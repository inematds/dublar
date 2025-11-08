# dublar.py
# Pipeline local de dublagem com etapas claras + sincronização opcional.
# Etapas:
# 1) Entrada/cheques
# 2) Extração de áudio
# 3) Transcrição (Whisper)
# 4) Tradução (M2M100)
# 5) Preparação de segmentos (split inteligente)
# 6) TTS (Bark ou Coqui) + (opcional) micro-fade
# 7) Sincronização por janela (fit/loose/none)
# 8) Concatenação
# 9) Pós-processo
# 10) Mux final + logs

import os, sys, json, csv, argparse, subprocess, shutil, re
from pathlib import Path

# -------------------- utilidades de shell e ffprobe --------------------
def sh(cmd, cwd=None):
    print(">>", " ".join(map(str, cmd)))
    subprocess.run(cmd, check=True, cwd=cwd)

def ensure_ffmpeg():
    if not shutil.which("ffmpeg"):
        print("ffmpeg não encontrado no PATH.")
        sys.exit(1)
    if not shutil.which("ffprobe"):
        print("ffprobe não encontrado no PATH (vem junto com ffmpeg).")
        sys.exit(1)

def ffprobe_duration(wav_path):
    try:
        out = subprocess.check_output([
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=nk=1:nw=1",
            str(wav_path)
        ], text=True).strip()
        return max(0.0, float(out))
    except Exception:
        return 0.0

def ts_stamp(t):
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")

# -------------------- etapa 3: transcrição --------------------
def transcribe_faster_whisper(wav_path, workdir, src_lang):
    print("\n=== ETAPA 3: Transcrição (Whisper) ===")
    from faster_whisper import WhisperModel
    model = WhisperModel("medium", device="auto")
    segments, info = model.transcribe(str(wav_path), language=src_lang, vad_filter=True)

    segs = []
    for s in segments:
        segs.append({
            "start": float(s.start),
            "end": float(s.end),
            "text": (s.text or "").strip()
        })

    srt_path = Path(workdir, "asr.srt")
    json_path = Path(workdir, "asr.json")
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, s in enumerate(segs, 1):
            f.write(f"{i}\n{ts_stamp(s['start'])} --> {ts_stamp(s['end'])}\n{s['text']}\n\n")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"language": src_lang, "segments": segs}, f, ensure_ascii=False, indent=2)

    print(f"Transcrito: {len(segs)} segmentos")
    return json_path, srt_path, segs

# -------------------- etapa 4: tradução --------------------
def translate_segments_m2m100(segs, src, tgt, workdir):
    print("\n=== ETAPA 4: Tradução (facebook/m2m100_418M) ===")
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    model_name = "facebook/m2m100_418M"
    tok = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

    src = (src or "en").lower()
    tgt = (tgt or "pt").lower()
    if hasattr(tok, "lang_code_to_id"):
        if src not in tok.lang_code_to_id: src = "en"
        if tgt not in tok.lang_code_to_id: tgt = "pt"

    out, batch, idxs = [], [], []
    max_batch = 8

    def flush():
        nonlocal out, batch, idxs
        if not batch:
            return
        tok.src_lang = src
        enc = tok(batch, return_tensors="pt", padding=True, truncation=True)
        gen = model.generate(
            **enc,
            forced_bos_token_id=tok.get_lang_id(tgt),
            max_new_tokens=200
        )
        texts = tok.batch_decode(gen, skip_special_tokens=True)
        for j, txt in enumerate(texts):
            i = idxs[j]
            item = dict(segs[i])
            item["text_trad"] = txt.strip()
            out.append(item)
        batch.clear()
        idxs.clear()

    for i, s in enumerate(segs):
        batch.append(s.get("text", ""))
        idxs.append(i)
        if len(batch) >= max_batch:
            flush()
    flush()

    srt_t = Path(workdir, "asr_trad.srt")
    json_t = Path(workdir, "asr_trad.json")
    with open(srt_t, "w", encoding="utf-8") as f:
        for i, s in enumerate(out, 1):
            f.write(f"{i}\n{ts_stamp(s['start'])} --> {ts_stamp(s['end'])}\n{s['text_trad']}\n\n")
    with open(json_t, "w", encoding="utf-8") as f:
        json.dump({"language": tgt, "segments": out}, f, ensure_ascii=False, indent=2)

    print(f"Traduzido: {len(out)} segmentos")
    return out, json_t, srt_t

# -------------------- etapa 5: preparação (split inteligente) --------------------
def split_long_segments(segments, maxdur):
    print("\n=== ETAPA 5: Preparação de segmentos (split inteligente) ===")
    if maxdur is None or maxdur <= 0:
        print("Split desativado.")
        return segments

    out = []
    for s in segments:
        start = s["start"]; end = s["end"]
        text = s.get("text_trad", "")
        dur = max(0.001, end - start)
        cps = max(len(text) / dur, 8.0) if len(text) > 0 else 12.0  # chars/seg aprox

        if dur <= maxdur or len(text.split()) < 16:
            out.append(s); continue

        parts = re.split(r'([\.!\?:;,\u2026])', text)  # mantém pontuação separada
        pieces = []
        buf = ""
        for chunk in parts:
            if chunk is None:
                continue
            cand = (buf + chunk).strip()
            est = len(cand) / cps
            if cand and est > maxdur and buf:
                pieces.append(buf)
                buf = chunk.strip()
            else:
                buf = cand
        if buf:
            pieces.append(buf)

        cur = start
        for i, piece in enumerate(pieces):
            est = len(piece) / cps
            nxt = cur + est
            # Garante que o último peça termine em 'end'
            if i == len(pieces) - 1:
                nxt = end
            out.append({"start": cur, "end": nxt, "text_trad": piece})
            cur = nxt

    print(f"Após split: {len(out)} segmentos")
    return out

# -------------------- etapa 6: TTS --------------------
def tts_bark(segments, workdir, text_temp=0.6, wave_temp=0.6, history_prompt=None):
    print("\n=== ETAPA 6: TTS (Bark) ===")
    from bark import generate_audio, SAMPLE_RATE
    from scipy.io.wavfile import write
    history = None
    if history_prompt:
        try:
            from bark.generation import load_history_prompt
            history = load_history_prompt(history_prompt)
        except Exception:
            history = history_prompt  # preset string

    seg_files = []
    tsv = Path(workdir, "segments.csv")
    with open(tsv, "w", encoding="utf-8", newline="") as fcsv:
        w = csv.writer(fcsv)
        w.writerow(["t_in", "t_out", "texto_trad", "file"])
        for i, s in enumerate(segments, 1):
            txt = s.get("text_trad", "")
            out = Path(workdir, f"seg_{i:04d}.wav")
            if not txt.strip():
                dur = max(0.05, s["end"] - s["start"])
                sh(["ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r={SAMPLE_RATE}:cl=mono", "-t", f"{dur:.3f}", out.name], cwd=workdir)
            else:
                audio = generate_audio(txt, text_temp=text_temp, waveform_temp=wave_temp, history_prompt=history)
                write(out, SAMPLE_RATE, audio)
            seg_files.append(out)
            w.writerow([s["start"], s["end"], txt, out.name])

    print(f"TTS Bark gerou: {len(seg_files)} arquivos")
    return seg_files, 24000  # SAMPLE_RATE

def tts_coqui(segments, workdir, tgt_lang, speaker=None):
    print("\n=== ETAPA 6: TTS (Coqui) ===")
    from TTS.api import TTS
    lang = (tgt_lang or "en").lower()
    if lang in ("pt", "pt-br", "pt_pt"):
        model_name = "tts_models/pt/cv/vits"
        sample_rate = 22050
    elif lang in ("en", "en-us", "en-gb"):
        model_name = "tts_models/en/ljspeech/tacotron2-DDC"
        sample_rate = 22050
    else:
        model_name = "tts_models/en/ljspeech/tacotron2-DDC"
        sample_rate = 22050

    tts = TTS(model_name, gpu=False)
    seg_files = []
    tsv = Path(workdir, "segments.csv")
    with open(tsv, "w", encoding="utf-8", newline="") as fcsv:
        w = csv.writer(fcsv)
        w.writerow(["t_in", "t_out", "texto_trad", "file"])
        for i, s in enumerate(segments, 1):
            txt = s.get("text_trad", "")
            out = Path(workdir, f"seg_{i:04d}.wav")
            if not txt.strip():
                dur = max(0.05, s["end"] - s["start"])
                sh(["ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r={sample_rate}:cl=mono", "-t", f"{dur:.3f}", out.name], cwd=workdir)
            else:
                if speaker:
                    try:
                        tts.tts_to_file(text=txt, file_path=str(out), speaker=speaker, language=tgt_lang)
                    except Exception:
                        tts.tts_to_file(text=txt, file_path=str(out))
                else:
                    tts.tts_to_file(text=txt, file_path=str(out))
            seg_files.append(out)
            w.writerow([s["start"], s["end"], txt, out.name])

    print(f"TTS Coqui gerou: {len(seg_files)} arquivos")
    return seg_files, sample_rate

# -------------------- etapa 7: sincronização --------------------
def atempo_chain(factor):
    chain = []
    f = float(factor)
    # encadear até cair em [0.5..2.0]
    while f < 0.5:
        chain.append("atempo=0.5"); f /= 0.5
    while f > 2.0:
        chain.append("atempo=2.0"); f /= 2.0
    chain.append(f"atempo={f:.6f}")
    return ",".join(chain)

def fit_segment_to_window(wav_path, target_dur, workdir, samplerate, tolerance, maxstretch):
    cur_dur = ffprobe_duration(Path(workdir, wav_path.name))
    if cur_dur <= 0.0:
        return wav_path
    ratio = target_dur / cur_dur
    # aplica somente se sair da tolerância
    if ratio < (1 - tolerance) or ratio > (1 + tolerance):
        ratio = max(min(ratio, maxstretch), 1.0 / maxstretch)
        filt = atempo_chain(ratio)
        fixed = Path(workdir, wav_path.name.replace(".wav", "_fit.wav"))
        sh(["ffmpeg", "-y", "-i", wav_path.name, "-af", filt, "-ar", str(samplerate), "-ac", "1", fixed.name], cwd=workdir)
        return fixed
    return wav_path

def micro_fade_inplace(wav_path, workdir):
    out = Path(workdir, wav_path.name.replace(".wav", "_xf.wav"))
    sh(["ffmpeg", "-y", "-i", wav_path.name, "-af", "afade=t=in:ss=0:d=0.02,afade=t=out:st=0.02:d=0.02", out.name], cwd=workdir)
    return out

# -------------------- etapa 8: concatenação --------------------
def concat_segments(seg_files, workdir, samplerate):
    print("\n=== ETAPA 8: Concatenação ===")
    lst = Path(workdir, "list.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for p in seg_files:
            f.write(f"file '{p.name}'\n")
    out = Path(workdir, "dub_raw.wav")
    sh([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", lst.name,
        "-c:a", "pcm_s16le",
        "-ar", str(samplerate), "-ac", "1",
        out.name
    ], cwd=workdir)
    return out

# -------------------- etapa 9: pós-processo --------------------
def postprocess_audio(wav_in, workdir, samplerate):
    print("\n=== ETAPA 9: Pós-processo de áudio ===")
    out = Path(workdir, "dub_final.wav")
    filters = "loudnorm=I=-16:TP=-1.5:LRA=11,afftdn=nf=-25,equalizer=f=6500:t=h:width=2000:g=-4"
    sh(["ffmpeg", "-y", "-i", wav_in.name, "-af", filters, "-ar", str(samplerate), "-ac", "1", out.name], cwd=workdir)
    return out

# -------------------- etapa 10: mux vídeo --------------------
def mux_video(video_in, wav_in, out_mp4, bitrate):
    print("\n=== ETAPA 10: Mux final (vídeo + dublagem) ===")
    sh([
        "ffmpeg", "-y",
        "-i", str(video_in),
        "-i", str(wav_in),
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", bitrate,
        str(out_mp4)
    ])

# -------------------- main --------------------
def main():
    print("=== ETAPA 1: Entrada/cheques ===")
    ap = argparse.ArgumentParser(description="Dublagem local com Whisper + M2M100 + Bark/Coqui (com sincronização opcional)")
    ap.add_argument("--in", dest="inp", required=True, help="vídeo de entrada, ex: video.mp4")
    ap.add_argument("--out", dest="out", default="video_dublado.mp4", help="arquivo MP4 de saída")
    ap.add_argument("--src", required=True, help="idioma origem, ex: en")
    ap.add_argument("--tgt", required=True, help="idioma destino, ex: pt")
    ap.add_argument("--tts", choices=["bark", "coqui"], default="bark", help="motor TTS")
    ap.add_argument("--voice", default=None, help="bark: history_prompt (.npz ou preset v2/pt_speaker_X). coqui: speaker (quando suportado).")
    ap.add_argument("--rate", type=int, default=24000, help="sample rate final (Hz)")
    ap.add_argument("--bitrate", default="192k", help="bitrate AAC (ex: 192k)")

    # novas flags de sincronização/prosódia
    ap.add_argument("--sync", choices=["none", "fit", "loose"], default="fit", help="ajuste de duração por segmento")
    ap.add_argument("--tolerance", type=float, default=0.15, help="tolerância de variação (ex: 0.15 = 15%)")
    ap.add_argument("--maxstretch", type=float, default=1.35, help="limite de stretching (ex: 1.35)")
    ap.add_argument("--maxdur", type=float, default=10.0, help="quebra segmentos acima desse tempo (s). 0 = desativa")
    ap.add_argument("--texttemp", type=float, default=0.6, help="Bark: temperatura de texto")
    ap.add_argument("--wavetemp", type=float, default=0.6, help="Bark: temperatura de waveform")
    ap.add_argument("--fade", type=int, default=1, help="aplica micro-fade in/out em cada segmento (1=sim, 0=não)")
    args = ap.parse_args()

    ensure_ffmpeg()
    workdir = Path("dub_work")
    workdir.mkdir(exist_ok=True)

    video_in = Path(args.inp).resolve()
    if not video_in.exists():
        print("Arquivo de entrada não encontrado:", video_in)
        sys.exit(1)

    # -------------------- etapa 2: extração de áudio --------------------
    print("\n=== ETAPA 2: Extração de áudio (ffmpeg) ===")
    audio_src = Path(workdir, "audio_src.wav")
    sh(["ffmpeg", "-y", "-i", str(video_in), "-vn", "-ac", "1", "-ar", "48000", "-c:a", "pcm_s16le", str(audio_src)])

    # 3) transcrever
    asr_json, asr_srt, segs = transcribe_faster_whisper(audio_src, workdir, args.src)

    # 4) traduzir
    segs_trad, trad_json, trad_srt = translate_segments_m2m100(segs, args.src, args.tgt, workdir)

    # 5) split inteligente
    segs_trad = split_long_segments(segs_trad, args.maxdur)

    # 6) TTS
    if args.tts == "bark":
        seg_files, sr_segs = tts_bark(segs_trad, workdir, text_temp=args.texttemp, wave_temp=args.wavetemp, history_prompt=args.voice)
    else:
        seg_files, sr_segs = tts_coqui(segs_trad, workdir, args.tgt, speaker=args.voice)

    # 6.1) micro-fade opcional
    if args.fade == 1:
        print("\n=== ETAPA 6.1: Micro-fade por segmento ===")
        seg_files = [micro_fade_inplace(p, workdir) for p in seg_files]

    # 7) sincronização por janela
    print("\n=== ETAPA 7: Sincronização por segmento ===")
    if args.sync in ("fit", "loose"):
        fixed_files = []
        for i, s in enumerate(segs_trad, 1):
            p = Path(workdir, f"seg_{i:04d}.wav")
            # caso tenha virado *_xf.wav ou *_fit.wav, escolha o mais recente pelo nome gerado
            # preferir o micro-fade quando ativo
            if args.fade == 1:
                xf = Path(workdir, f"seg_{i:04d}_xf.wav")
                if xf.exists():
                    p = xf
            target = max(0.05, s["end"] - s["start"])
            fixed = fit_segment_to_window(p, target, workdir, sr_segs, args.tolerance, args.maxstretch)
            fixed_files.append(fixed)
        seg_files = fixed_files
    else:
        print("Sincronização: desativada (none)")

    # 8) concatenação
    dub_raw = concat_segments(seg_files, workdir, sr_segs)

    # 9) pós-processo
    dub_final = postprocess_audio(dub_raw, workdir, args.rate)

    # 10) mux final
    out_mp4 = Path(args.out)
    mux_video(video_in, dub_final, out_mp4, args.bitrate)

    # logs
    logs = {
        "input_video": str(video_in),
        "output_video": str(out_mp4),
        "asr_json": str(asr_json),
        "asr_srt": str(asr_srt),
        "trad_json": str(trad_json),
        "trad_srt": str(trad_srt),
        "samples_dir": str(workdir),
        "tts": args.tts,
        "src": args.src,
        "tgt": args.tgt,
        "voice": args.voice,
        "sync": args.sync,
        "tolerance": args.tolerance,
        "maxstretch": args.maxstretch,
        "maxdur": args.maxdur,
        "texttemp": args.texttemp,
        "wavetemp": args.wavetemp,
        "fade": args.fade
    }
    with open(Path(workdir, "logs.json"), "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

    print("\nConcluído.")
    print("Saídas principais:")
    print(" -", out_mp4)
    print(" -", trad_srt)
    print(" -", Path(workdir, "logs.json"))
    print("Intermediários em:", workdir)

if __name__ == "__main__":
    main()

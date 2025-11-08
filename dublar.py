# dublar.py
# Pipeline local de dublagem com 4 modos de sync: none, fit, pad, smart.

import os, sys, json, csv, argparse, subprocess, shutil, re
from pathlib import Path

# ---------------- utilidades ----------------
def sh(cmd, cwd=None):
    print(">>", " ".join(map(str, cmd)))
    subprocess.run(cmd, check=True, cwd=cwd)

def ensure_ffmpeg():
    for bin in ("ffmpeg","ffprobe"):
        if not shutil.which(bin):
            print(f"{bin} não encontrado no PATH.")
            sys.exit(1)

def ffprobe_duration(path):
    try:
        out = subprocess.check_output([
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=nk=1:nw=1",
            str(path)
        ], text=True).strip()
        return max(0.0, float(out))
    except Exception:
        return 0.0

def ts_stamp(t):
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")

# ---------------- etapa 3: ASR ----------------
def transcribe_faster_whisper(wav_path, workdir, src_lang):
    print("\n=== ETAPA 3: Transcrição (Whisper) ===")
    from faster_whisper import WhisperModel
    import torch

    # faster-whisper com CTranslate2 tem problemas em GPU no Windows
    # Usamos CPU que é estável (ainda é rápido)
    import torch

    device = "cpu"  # Forçar CPU para Whisper (estável)
    compute_type = "int8"

    print(f"[INFO] Whisper usando: {device.upper()} (CTranslate2 mais estável em CPU)")
    if torch.cuda.is_available():
        print(f"[INFO] GPU disponível mas não usada pelo Whisper: {torch.cuda.get_device_name(0)}")
        print(f"[INFO] M2M100 e Bark usarão GPU normalmente")

    model = WhisperModel("medium", device=device, compute_type=compute_type)

    segments, _ = model.transcribe(
        str(wav_path),
        language=src_lang,
        vad_filter=True,
        beam_size=5,
        best_of=5,
        temperature=0.0
    )

    segs = []
    for s in segments:
        segs.append({"start": float(s.start), "end": float(s.end), "text": (s.text or "").strip()})

    srt_path = Path(workdir, "asr.srt")
    json_path = Path(workdir, "asr.json")
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, s in enumerate(segs, 1):
            f.write(f"{i}\n{ts_stamp(s['start'])} --> {ts_stamp(s['end'])}\n{s['text']}\n\n")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"language": src_lang, "segments": segs}, f, ensure_ascii=False, indent=2)
    print(f"Transcrito: {len(segs)} segmentos")
    return json_path, srt_path, segs

# ---------------- etapa 4: tradução ----------------
def translate_segments_m2m100(segs, src, tgt, workdir):
    print("\n=== ETAPA 4: Tradução (facebook/m2m100_418M) ===")
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    import torch

    model_name = "facebook/m2m100_418M"
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[GPU] M2M100 usando: {device.upper()}")

    tok = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(device)

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
        # Mover tensores para GPU se disponível
        enc = {k: v.to(device) for k, v in enc.items()}
        gen = model.generate(**enc, forced_bos_token_id=tok.get_lang_id(tgt), max_new_tokens=200)
        texts = tok.batch_decode(gen, skip_special_tokens=True)
        for j, txt in enumerate(texts):
            i = idxs[j]
            item = dict(segs[i])
            item["text_trad"] = txt.strip()
            out.append(item)
        batch.clear(); idxs.clear()

    for i, s in enumerate(segs):
        batch.append(s.get("text","")); idxs.append(i)
        if len(batch) >= max_batch: flush()
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

# ---------------- etapa 5: split ----------------
def split_long_segments(segments, maxdur):
    print("\n=== ETAPA 5: Split inteligente ===")
    if not maxdur or maxdur <= 0:
        print("Split desativado.")
        return segments

    out = []
    split_count = 0

    for seg_idx, s in enumerate(segments, 1):
        start, end = s["start"], s["end"]
        text = (s.get("text_trad") or "").strip()
        dur = max(0.001, end - start)

        # Não dividir se duração OK ou texto curto
        if dur <= maxdur or len(text.split()) < 16:
            out.append(s)
            continue

        print(f"[SPLIT] Segmento {seg_idx}: {start:.2f}s->{end:.2f}s ({dur:.2f}s, {len(text)} chars)")
        print(f"[SPLIT]   Texto: \"{text[:60]}...\"")

        # Dividir texto em pontuação
        parts = re.split(r'([\.!\?:;,\u2026])', text)
        cps = max(len(text)/dur, 8.0)

        def good(t):
            t2 = re.sub(r"\s+"," ", (t or "")).strip()
            return len(re.findall(r"[A-Za-zÀ-ÿ0-9]", t2)) >= 3

        # Reconstruir em pedaços lógicos
        buf = ""
        pieces = []
        for ch in parts:
            if ch is None: continue
            cand = (buf + ch).strip()
            est = len(cand)/cps if cand else 0
            if cand and est > maxdur and good(buf):
                pieces.append(buf.strip())
                buf = ch.strip()
            else:
                buf = cand
        if good(buf): pieces.append(buf.strip())

        if not pieces:
            out.append(s)
            continue

        # CORREÇÃO: Distribuir timestamps PROPORCIONALMENTE ao tamanho do texto
        total_chars = sum(len(p) for p in pieces)
        cur = start

        print(f"[SPLIT]   Dividindo em {len(pieces)} partes (total: {total_chars} chars):")

        for i, piece in enumerate(pieces):
            # Calcular duração proporcional ao tamanho do texto
            piece_ratio = len(piece) / total_chars
            piece_dur = dur * piece_ratio
            nxt = cur + piece_dur

            # Garantir que último segmento termina exatamente no end original
            if i == len(pieces)-1:
                nxt = end

            print(f"[SPLIT]     Parte {i+1}/{len(pieces)}: {cur:.2f}s->{nxt:.2f}s ({nxt-cur:.2f}s, {len(piece)} chars, {piece_ratio*100:.1f}%)")
            print(f"[SPLIT]       \"{piece[:50]}...\"")

            out.append({"start": cur, "end": nxt, "text_trad": piece})
            cur = nxt

        split_count += 1

    print(f"[SPLIT] Resultado: {len(out)} segmentos ({split_count} divididos, {len(segments)-split_count} mantidos)")
    return out

# ---------------- etapa 6: TTS ----------------
def tts_bark(segments, workdir, text_temp=0.6, wave_temp=0.6, history_prompt=None):
    print("\n=== ETAPA 6: TTS (Bark) ===")
    import os
    import torch

    # PATCH CRÍTICO: PyTorch 2.6 mudou torch.load para weights_only=True por padrão
    # Bark não é compatível, então precisamos patchear a função _load_model do Bark
    print(f"[INFO] Aplicando patch para PyTorch 2.6 + Bark...")

    import bark.generation as bark_gen
    _original_torch_load = torch.load

    def _patched_torch_load(f, map_location=None, *args, **kwargs):
        # Forçar weights_only=False para modelos Bark (são confiáveis)
        kwargs['weights_only'] = False
        return _original_torch_load(f, map_location=map_location, *args, **kwargs)

    # Substituir temporariamente torch.load
    torch.load = _patched_torch_load

    from bark import generate_audio, SAMPLE_RATE
    from scipy.io.wavfile import write

    # Configurar Bark para usar GPU
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[GPU] Bark usando: {device.upper()}")
    if device == "cuda":
        os.environ['SUNO_USE_SMALL_MODELS'] = '0'  # Usar modelos grandes em GPU
        os.environ['SUNO_OFFLOAD_CPU'] = '0'  # Não fazer offload para CPU
        print(f"[GPU] Modelos Bark carregados em GPU")

    history = None
    if history_prompt:
        try:
            from bark.generation import load_history_prompt
            history = load_history_prompt(history_prompt)
        except Exception:
            history = history_prompt

    seg_files = []
    tsv = Path(workdir, "segments.csv")
    with open(tsv, "w", encoding="utf-8", newline="") as fcsv:
        w = csv.writer(fcsv); w.writerow(["t_in","t_out","texto_trad","file"])
        for i, s in enumerate(segments, 1):
            txt = (s.get("text_trad") or "").strip()
            if len(re.findall(r"[A-Za-zÀ-ÿ0-9]", txt)) < 3:
                txt = "pausa curta"
            out = Path(workdir, f"seg_{i:04d}.wav")
            audio = generate_audio(txt, history_prompt=history, text_temp=text_temp, waveform_temp=wave_temp)
            write(out, SAMPLE_RATE, audio)
            seg_files.append(out); w.writerow([s["start"], s["end"], txt, out.name])

    # Restaurar torch.load original
    torch.load = _original_torch_load
    print(f"[INFO] torch.load restaurado")

    print(f"TTS Bark gerou: {len(seg_files)} arquivos")
    return seg_files, 24000

def tts_coqui(segments, workdir, tgt_lang, speaker=None):
    print("\n=== ETAPA 6: TTS (Coqui) ===")
    from TTS.api import TTS
    lang = (tgt_lang or "en").lower()
    if lang in ("pt","pt-br","pt_pt"):
        model_name = "tts_models/pt/cv/vits"; sample_rate = 22050
    else:
        model_name = "tts_models/en/ljspeech/tacotron2-DDC"; sample_rate = 22050

    tts = TTS(model_name, gpu=False)
    seg_files = []
    tsv = Path(workdir, "segments.csv")
    with open(tsv, "w", encoding="utf-8", newline="") as fcsv:
        w = csv.writer(fcsv); w.writerow(["t_in","t_out","texto_trad","file"])
        for i, s in enumerate(segments, 1):
            txt = (s.get("text_trad") or "").strip()
            if len(re.findall(r"[A-Za-zÀ-ÿ0-9]", txt)) < 3:
                txt = "pausa curta"
            out = Path(workdir, f"seg_{i:04d}.wav")
            if speaker:
                try:
                    tts.tts_to_file(text=txt, file_path=str(out), speaker=speaker, language=tgt_lang)
                except Exception:
                    tts.tts_to_file(text=txt, file_path=str(out))
            else:
                tts.tts_to_file(text=txt, file_path=str(out))
            seg_files.append(out); w.writerow([s["start"], s["end"], txt, out.name])
    print(f"TTS Coqui gerou: {len(seg_files)} arquivos")
    return seg_files, sample_rate

# ---------------- etapa 7: sync (none/fit/pad/smart) ----------------
def atempo_chain(factor):
    chain = []; f = float(factor)
    while f < 0.5: chain.append("atempo=0.5"); f /= 0.5
    while f > 2.0: chain.append("atempo=2.0"); f /= 2.0
    chain.append(f"atempo={f:.6f}")
    return ",".join(chain)

def safe_fade(in_path, out_path, workdir):
    # fade-in e fade-out simples (sem areverse que causa bugs de duração)
    sh(["ffmpeg","-y","-i", in_path.name,
        "-af","afade=t=in:d=0.01,afade=t=out:d=0.01",
        out_path.name], cwd=workdir)

def sync_fit(p, target, workdir, sr, tol, maxstretch):
    cur = ffprobe_duration(Path(workdir, p.name))
    ratio = target/cur if cur>0 else 1.0

    # Sempre comprimir/expandir quando ratio está fora da tolerância
    # Não retornar 'p' sem processar (isso causava áudios com duração errada)
    if cur<=0:
        return p

    # Limitar ratio ao maxstretch permitido
    ratio = max(min(ratio, maxstretch), 1.0/maxstretch)

    # Verificar se precisa ajuste (fora da tolerância)
    if abs(ratio - 1.0) < tol:
        print(f"    [FIT] Sem ajuste necessário (ratio={ratio:.3f}, tol={tol})")
        return p

    print(f"    [FIT] Ajustando: {cur:.2f}s → {target:.2f}s (ratio={ratio:.3f})")
    filt = atempo_chain(ratio)
    out = Path(workdir, p.name.replace(".wav","_fit.wav"))
    sh(["ffmpeg","-y","-i", p.name, "-af", filt, "-ar", str(sr), "-ac","1", out.name], cwd=workdir)
    return out

def sync_pad(p, target, workdir, sr):
    cur = ffprobe_duration(Path(workdir, p.name))
    if cur <= 0:
        return p
    if cur >= target:
        # corta no alvo, sem distorcer voz
        print(f"    [PAD] Cortando: {cur:.2f}s → {target:.2f}s")
        out = Path(workdir, p.name.replace(".wav","_pad.wav"))
        sh(["ffmpeg","-y","-i", p.name, "-af", f"atrim=duration={target:.6f}", "-ar", str(sr), "-ac","1", out.name], cwd=workdir)
        return out
    # adiciona silêncio até o alvo
    pad_dur = max(target - cur, 0.0)
    print(f"    [PAD] Adicionando silêncio: {cur:.2f}s + {pad_dur:.2f}s = {target:.2f}s")
    out = Path(workdir, p.name.replace(".wav","_pad.wav"))
    sh(["ffmpeg","-y","-i", p.name, "-af", f"apad=pad_dur={pad_dur:.6f},atrim=duration={target:.6f}",
        "-ar", str(sr), "-ac","1", out.name], cwd=workdir)
    return out

def sync_smart(p, target, workdir, sr, tol, maxstretch):
    cur = ffprobe_duration(Path(workdir, p.name))
    if cur <= 0: return p
    low = target*(1-tol); high = target*(1+tol)

    # Debug: mostrar valores para diagnóstico
    print(f"  [SYNC] Segmento: {p.name} | Alvo: {target:.2f}s | Atual: {cur:.2f}s | Range: [{low:.2f}s - {high:.2f}s]")

    if cur < low:
        print(f"  [SYNC] → Ação: PAD (áudio curto)")
        return sync_pad(p, target, workdir, sr)     # curto → completa silêncio
    elif cur > high:
        print(f"  [SYNC] → Ação: FIT (áudio longo, comprimir)")
        return sync_fit(p, target, workdir, sr, tol, maxstretch)  # longo → comprime
    else:
        print(f"  [SYNC] → Ação: OK (dentro da tolerância)")
        return p

# ---------------- etapa 8: concat ----------------
def concat_segments(seg_files, workdir, samplerate):
    print("\n=== ETAPA 8: Concatenação ===")
    lst = Path(workdir, "list.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for p in seg_files:
            f.write(f"file '{p.name}'\n")
    out = Path(workdir, "dub_raw.wav")
    sh(["ffmpeg","-y","-f","concat","-safe","0","-i", lst.name,
        "-c:a","pcm_s16le","-ar", str(samplerate),"-ac","1", out.name], cwd=workdir)
    return out

# ---------------- etapa 9: pós ----------------
def postprocess_audio(wav_in, workdir, samplerate):
    print("\n=== ETAPA 9: Pós-processo ===")
    out = Path(workdir, "dub_final.wav")
    # Filtros simplificados: apenas normalização de volume (removido afftdn e equalizer problemáticos)
    fx = "loudnorm=I=-14:TP=-1.5:LRA=11"
    sh(["ffmpeg","-y","-i", wav_in.name, "-af", fx, "-ar", str(samplerate), "-ac","1", out.name], cwd=workdir)
    return out

# ---------------- etapa 10: mux ----------------
def mux_video(video_in, wav_in, out_mp4, bitrate):
    print("\n=== ETAPA 10: Mux final ===")
    sh(["ffmpeg","-y","-i", str(video_in), "-i", str(wav_in),
        "-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a", bitrate, str(out_mp4)])

# ---------------- main ----------------
def main():
    print("=== ETAPA 1: Entrada/cheques ===")
    ap = argparse.ArgumentParser(description="Dublagem local com Whisper + M2M100 + Bark/Coqui")
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", dest="out", default="video_dublado.mp4")
    ap.add_argument("--src", required=True)
    ap.add_argument("--tgt", required=True)
    ap.add_argument("--tts", choices=["bark","coqui"], default="bark")
    ap.add_argument("--voice", default=None)
    ap.add_argument("--rate", type=int, default=24000)
    ap.add_argument("--bitrate", default="192k")

    ap.add_argument("--sync", choices=["none","fit","pad","smart"], default="smart")
    ap.add_argument("--tolerance", type=float, default=0.05)
    ap.add_argument("--maxstretch", type=float, default=1.3)
    ap.add_argument("--maxdur", type=float, default=10.0)
    ap.add_argument("--texttemp", type=float, default=0.6)
    ap.add_argument("--wavetemp", type=float, default=0.6)
    ap.add_argument("--fade", type=int, default=1)  # 1=sim, 0=não
    args = ap.parse_args()

    ensure_ffmpeg()
    workdir = Path("dub_work"); workdir.mkdir(exist_ok=True)

    video_in = Path(args.inp).resolve()
    if not video_in.exists():
        print("Arquivo de entrada não encontrado:", video_in); sys.exit(1)

    print("\n=== ETAPA 2: Extração de áudio ===")
    audio_src = Path(workdir, "audio_src.wav")
    sh(["ffmpeg","-y","-i", str(video_in), "-vn", "-ac","1","-ar","48000","-c:a","pcm_s16le", str(audio_src)])

    asr_json, asr_srt, segs = transcribe_faster_whisper(audio_src, workdir, args.src)
    segs_trad, trad_json, trad_srt = translate_segments_m2m100(segs, args.src, args.tgt, workdir)
    segs_trad = split_long_segments(segs_trad, args.maxdur)

    if args.tts == "bark":
        seg_files, sr_segs = tts_bark(segs_trad, workdir, text_temp=args.texttemp, wave_temp=args.wavetemp, history_prompt=args.voice)
    else:
        seg_files, sr_segs = tts_coqui(segs_trad, workdir, args.tgt, speaker=args.voice)

    if args.fade == 1:
        print("\n=== ETAPA 6.1: Micro-fade seguro ===")
        xf_files = []
        for i, _ in enumerate(segs_trad, 1):
            base = Path(workdir, f"seg_{i:04d}.wav")
            out = Path(workdir, f"seg_{i:04d}_xf.wav")
            safe_fade(base, out, workdir)
            xf_files.append(out)
        seg_files = xf_files

    print("\n=== ETAPA 7: Sincronização ===")
    fixed = []
    for i, s in enumerate(segs_trad, 1):
        target = max(0.05, s["end"] - s["start"])
        p = Path(workdir, f"seg_{i:04d}{'_xf' if args.fade==1 else ''}.wav")
        if args.sync == "none":
            fixed.append(p)
        elif args.sync == "fit":
            fixed.append(sync_fit(p, target, workdir, sr_segs, args.tolerance, args.maxstretch))
        elif args.sync == "pad":
            fixed.append(sync_pad(p, target, workdir, sr_segs))
        elif args.sync == "smart":
            fixed.append(sync_smart(p, target, workdir, sr_segs, args.tolerance, args.maxstretch))
    seg_files = fixed

    dub_raw = concat_segments(seg_files, workdir, sr_segs)
    dub_final = postprocess_audio(dub_raw, workdir, args.rate)
    out_mp4 = Path(args.out)
    mux_video(video_in, dub_final, out_mp4, args.bitrate)

    logs = {
        "input_video": str(video_in),
        "output_video": str(out_mp4),
        "asr_json": str(asr_json),
        "asr_srt": str(asr_srt),
        "trad_json": str(trad_json),
        "trad_srt": str(trad_srt),
        "samples_dir": str(workdir),
        "tts": args.tts, "src": args.src, "tgt": args.tgt, "voice": args.voice,
        "sync": args.sync, "tolerance": args.tolerance, "maxstretch": args.maxstretch,
        "maxdur": args.maxdur, "texttemp": args.texttemp, "wavetemp": args.wavetemp,
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

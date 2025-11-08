# dublar_sync_v2.py
# Pipeline de dublagem com MELHORIAS DE SINCRONIZAÇÃO AVANÇADAS
# Inclui: VAD, estimador de duração, densidade linguística, elastic sync, métricas

import os, sys, json, csv, argparse, subprocess, shutil, re, warnings
from pathlib import Path
import numpy as np

warnings.filterwarnings("ignore")

# ---------------- utilidades ----------------
def sh(cmd, cwd=None):
    print(">>", " ".join(map(str, cmd)))
    subprocess.run(cmd, check=True, cwd=cwd)

def make_silence_wav(workdir, idx, dur, sr):
    out = Path(workdir, f"sil_{idx:04d}.wav")
    sh([
        "ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r={sr}:cl=mono",
        "-t", f"{dur:.6f}",
        out.name
    ], cwd=workdir)
    return out

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

# ---------------- NOVO: Análise de densidade linguística ----------------
class LinguisticDensity:
    """Analisa densidade de caracteres/palavras por segundo entre idiomas"""

    # Fatores de expansão médios (relativo ao inglês)
    EXPANSION_FACTORS = {
        "pt": 1.20,  # Português 20% mais longo
        "pt-br": 1.20,
        "es": 1.15,  # Espanhol 15% mais longo
        "fr": 1.18,  # Francês 18% mais longo
        "de": 0.95,  # Alemão 5% mais curto
        "it": 1.12,  # Italiano 12% mais longo
        "en": 1.00,  # Inglês (baseline)
        "ja": 0.80,  # Japonês 20% mais curto
        "zh": 0.75,  # Chinês 25% mais curto
        "ru": 1.05,  # Russo 5% mais longo
    }

    @classmethod
    def get_expansion_factor(cls, src_lang, tgt_lang):
        """Retorna fator de expansão esperado"""
        src = cls.EXPANSION_FACTORS.get(src_lang.lower(), 1.0)
        tgt = cls.EXPANSION_FACTORS.get(tgt_lang.lower(), 1.0)
        return tgt / src

    @classmethod
    def estimate_duration(cls, text, reference_duration, src_lang, tgt_lang):
        """Estima duração da tradução baseada em expansão linguística"""
        factor = cls.get_expansion_factor(src_lang, tgt_lang)
        return reference_duration * factor

    @classmethod
    def calculate_cps(cls, text, duration):
        """Calcula caracteres por segundo"""
        chars = len(re.sub(r'\s+', '', text))
        return chars / max(duration, 0.1)

    @classmethod
    def calculate_wps(cls, text, duration):
        """Calcula palavras por segundo"""
        words = len(text.split())
        return words / max(duration, 0.1)

# ---------------- NOVO: VAD - Voice Activity Detection ----------------
def detect_speech_pauses(audio_path, min_silence_dur=0.3):
    """
    Detecta pausas naturais na fala usando análise de energia do áudio
    Retorna lista de (start, end) em segundos das pausas detectadas
    """
    try:
        import librosa
        # Carrega áudio
        y, sr = librosa.load(audio_path, sr=16000, mono=True)

        # Calcula energia RMS por frame
        frame_length = int(sr * 0.025)  # 25ms
        hop_length = int(sr * 0.010)    # 10ms

        rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]

        # Threshold adaptativo (percentil 20)
        threshold = np.percentile(rms, 20)

        # Detecta frames silenciosos
        silent_frames = rms < threshold

        # Converte frames para timestamps
        times = librosa.frames_to_time(np.arange(len(silent_frames)), sr=sr, hop_length=hop_length)

        # Agrupa silêncios consecutivos
        pauses = []
        in_pause = False
        pause_start = 0

        for i, (is_silent, time) in enumerate(zip(silent_frames, times)):
            if is_silent and not in_pause:
                pause_start = time
                in_pause = True
            elif not is_silent and in_pause:
                pause_dur = time - pause_start
                if pause_dur >= min_silence_dur:
                    pauses.append((pause_start, time))
                in_pause = False

        print(f"  Detectadas {len(pauses)} pausas naturais (>{min_silence_dur}s)")
        return pauses

    except ImportError:
        print("  [AVISO] librosa não instalado. VAD desabilitado.")
        print("  Instale com: pip install librosa")
        return []
    except Exception as e:
        print(f"  [AVISO] Erro no VAD: {e}")
        return []

# ---------------- NOVO: Estimador de duração pré-TTS ----------------
def estimate_tts_duration(text, lang="pt", base_wps=2.5):
    """
    Estima duração do TTS antes de gerar áudio
    base_wps: palavras por segundo (2-3 é conversacional normal)
    """
    # Remove pontuação e conta palavras
    words = len(text.split())

    # Ajuste por idioma
    speed_factors = {
        "pt": 1.0,
        "en": 1.1,   # Inglês tende a ser mais rápido
        "es": 0.95,  # Espanhol um pouco mais lento
        "fr": 0.90,  # Francês mais lento
    }

    factor = speed_factors.get(lang.lower(), 1.0)
    adjusted_wps = base_wps * factor

    # Duração base
    duration = words / adjusted_wps

    # Adiciona pausas por pontuação
    pauses = text.count('.') * 0.3 + text.count(',') * 0.15 + text.count('?') * 0.3 + text.count('!') * 0.3

    total = duration + pauses
    return max(total, 0.5)  # Mínimo 0.5s

# ---------------- etapa 3: ASR ----------------
def transcribe_faster_whisper(wav_path, workdir, src_lang):
    print("\n=== ETAPA 3: Transcrição (Whisper) ===")
    from faster_whisper import WhisperModel

    # Tenta GPU primeiro, se falhar usa CPU
    model = None
    try:
        print("Tentando usar GPU (CUDA)...")
        model = WhisperModel("medium", device="cuda", compute_type="float16")
        print("✓ GPU carregada, testando...")
        # Testa se realmente funciona
        test_segments, _ = model.transcribe(str(wav_path), language=src_lang, vad_filter=True)
        # Se chegou aqui, GPU funciona
        print("✓ GPU funcionando!")
        segments = test_segments
    except Exception as e:
        print(f"✗ GPU falhou: {str(e)[:100]}")
        print("Usando CPU (mais lento mas confiável)...")
        model = WhisperModel("medium", device="cpu", compute_type="int8")
        segments, _ = model.transcribe(str(wav_path), language=src_lang, vad_filter=True)

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
        gen = model.generate(**enc, forced_bos_token_id=tok.get_lang_id(tgt), max_new_tokens=200)
        texts = tok.batch_decode(gen, skip_special_tokens=True)
        for j, txt in enumerate(texts):
            i = idxs[j]
            item = dict(segs[i])
            item["text_trad"] = txt.strip()
            # NOVO: Adiciona métricas de densidade
            dur = item["end"] - item["start"]
            item["original_wps"] = LinguisticDensity.calculate_wps(item.get("text", ""), dur)
            item["trad_estimated_dur"] = estimate_tts_duration(txt.strip(), tgt)
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

# ---------------- MELHORADO: etapa 5: split inteligente com VAD ----------------
def split_long_segments_vad(segments, maxdur, audio_src_path=None):
    """
    Split inteligente melhorado que considera:
    - Pausas naturais detectadas por VAD
    - Pontuação
    - Densidade linguística
    """
    print("\n=== ETAPA 5: Split inteligente com VAD ===")
    if not maxdur or maxdur <= 0:
        print("Split desativado.")
        return segments

    # Detecta pausas naturais no áudio original
    pauses = []
    if audio_src_path and Path(audio_src_path).exists():
        print("Detectando pausas naturais no áudio...")
        pauses = detect_speech_pauses(audio_src_path, min_silence_dur=0.3)

    out = []
    for s in segments:
        start, end = s["start"], s["end"]
        text = (s.get("text_trad") or "").strip()
        dur = max(0.001, end - start)

        # Não divide se for curto ou poucas palavras
        if dur <= maxdur or len(text.split()) < 16:
            out.append(s)
            continue

        # Verifica se há pausas naturais neste segmento
        segment_pauses = [(p[0], p[1]) for p in pauses if start <= p[0] < end]

        # Se há pausas naturais, usa elas como pontos de divisão
        if segment_pauses:
            # Divide nos pontos de pausa
            parts_by_pause = []
            current_start = start

            for pause_start, pause_end in segment_pauses:
                if pause_start - current_start >= 1.0:  # Mínimo 1s por parte
                    parts_by_pause.append((current_start, pause_start))
                    current_start = pause_end

            # Adiciona última parte
            if end - current_start >= 0.5:
                parts_by_pause.append((current_start, end))

            if parts_by_pause:
                # Distribui texto proporcionalmente
                total_dur = sum(p[1] - p[0] for p in parts_by_pause)
                words = text.split()
                word_idx = 0

                for i, (p_start, p_end) in enumerate(parts_by_pause):
                    part_dur = p_end - p_start
                    proportion = part_dur / total_dur
                    num_words = max(1, int(len(words) * proportion))

                    if i == len(parts_by_pause) - 1:  # Última parte pega todas restantes
                        part_text = " ".join(words[word_idx:])
                    else:
                        part_text = " ".join(words[word_idx:word_idx + num_words])
                        word_idx += num_words

                    if part_text.strip():
                        out.append({
                            "start": p_start,
                            "end": p_end,
                            "text_trad": part_text.strip(),
                            "split_method": "vad"
                        })
                continue

        # Fallback: split por pontuação (método original)
        parts = re.split(r'([\.!\?:;,\u2026])', text)
        cps = max(len(text)/dur, 8.0)

        def good(t):
            t2 = re.sub(r"\s+"," ", (t or "")).strip()
            return len(re.findall(r"[A-Za-zÀ-ÿ0-9]", t2)) >= 3

        buf = ""; pieces = []
        for ch in parts:
            if ch is None: continue
            cand = (buf + ch).strip()
            est = len(cand)/cps if cand else 0
            if cand and est > maxdur and good(buf):
                pieces.append(buf.strip()); buf = ch.strip()
            else:
                buf = cand
        if good(buf): pieces.append(buf.strip())

        if not pieces:
            out.append(s)
            continue

        cur = start
        for i, piece in enumerate(pieces):
            est = max(0.5, len(piece)/cps)
            nxt = cur + est
            if i == len(pieces)-1: nxt = end
            out.append({
                "start": cur,
                "end": nxt,
                "text_trad": piece,
                "split_method": "punctuation"
            })
            cur = nxt

    print(f"Após split: {len(out)} segmentos (original: {len(segments)})")
    return out

# ---------------- etapa 6: TTS ----------------
def tts_bark(segments, workdir, text_temp=0.6, wave_temp=0.6, history_prompt=None):
    print("\n=== ETAPA 6: TTS (Bark) ===")
    import os
    # Força Bark a usar CPU para evitar erros de cuDNN
    os.environ["CUDA_VISIBLE_DEVICES"] = ""

    from bark import generate_audio, SAMPLE_RATE
    from scipy.io.wavfile import write

    print("Usando CPU para TTS (evita problemas de cuDNN)")

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
        w = csv.writer(fcsv)
        w.writerow(["idx", "t_in","t_out","texto_trad","file","estimated_dur","actual_dur"])
        for i, s in enumerate(segments, 1):
            txt = (s.get("text_trad") or "").strip()
            if len(re.findall(r"[A-Za-zÀ-ÿ0-9]", txt)) < 3:
                txt = "pausa curta"

            # NOVO: Estima duração antes de gerar
            estimated = s.get("trad_estimated_dur", estimate_tts_duration(txt, "pt"))

            out = Path(workdir, f"seg_{i:04d}.wav")
            audio = generate_audio(txt, history_prompt=history, text_temp=text_temp, waveform_temp=wave_temp)
            write(out, SAMPLE_RATE, audio)

            # NOVO: Mede duração real
            actual_dur = ffprobe_duration(out)

            seg_files.append(out)
            w.writerow([i, s["start"], s["end"], txt, out.name, f"{estimated:.3f}", f"{actual_dur:.3f}"])

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
        w = csv.writer(fcsv)
        w.writerow(["idx", "t_in","t_out","texto_trad","file","estimated_dur","actual_dur"])
        for i, s in enumerate(segments, 1):
            txt = (s.get("text_trad") or "").strip()
            if len(re.findall(r"[A-Za-zÀ-ÿ0-9]", txt)) < 3:
                txt = "pausa curta"

            estimated = s.get("trad_estimated_dur", estimate_tts_duration(txt, tgt_lang))

            out = Path(workdir, f"seg_{i:04d}.wav")
            if speaker:
                try:
                    tts.tts_to_file(text=txt, file_path=str(out), speaker=speaker, language=tgt_lang)
                except Exception:
                    tts.tts_to_file(text=txt, file_path=str(out))
            else:
                tts.tts_to_file(text=txt, file_path=str(out))

            actual_dur = ffprobe_duration(out)
            seg_files.append(out)
            w.writerow([i, s["start"], s["end"], txt, out.name, f"{estimated:.3f}", f"{actual_dur:.3f}"])

    print(f"TTS Coqui gerou: {len(seg_files)} arquivos")
    return seg_files, sample_rate

# ---------------- etapa 7: sync (none/fit/pad/smart/elastic) ----------------
def atempo_chain(factor):
    chain = []; f = float(factor)
    while f < 0.5: chain.append("atempo=0.5"); f /= 0.5
    while f > 2.0: chain.append("atempo=2.0"); f /= 2.0
    chain.append(f"atempo={f:.6f}")
    return ",".join(chain)

def safe_fade(in_path, out_path, workdir, fad=0.02):
    sh(["ffmpeg","-y","-i", in_path.name,
        "-af", f"afade=t=in:ss=0:d={fad},areverse,afade=t=in:ss=0:d={fad},areverse",
        out_path.name], cwd=workdir)

def sync_fit(p, target, workdir, sr, tol, maxstretch):
    cur = ffprobe_duration(Path(workdir, p.name))
    if cur <= 0:
        return p, 1.0

    diff = target - cur
    adiff = abs(diff)
    within_tol = (adiff <= (target * tol))

    if within_tol:
        out = Path(workdir, p.name.replace(".wav", "_fit.wav"))
        if diff >= 0:
            fchain = f"apad=pad_dur={diff:.6f},atrim=duration={target:.6f}"
        else:
            fchain = f"atrim=duration={target:.6f}"
        sh(["ffmpeg","-y","-i", p.name, "-af", fchain, "-ar", str(sr), "-ac","1", out.name], cwd=workdir)
        return out, 1.0

    ratio = (cur / target) if target > 0 else 1.0
    ratio = max(min(ratio, maxstretch), 1.0 / maxstretch)
    f_atempo = atempo_chain(ratio)
    out = Path(workdir, p.name.replace(".wav", "_fit.wav"))
    fchain = f"{f_atempo},atrim=duration={target:.6f}"
    sh(["ffmpeg","-y","-i", p.name, "-af", fchain, "-ar", str(sr), "-ac","1", out.name], cwd=workdir)
    return out, ratio

def sync_pad(p, target, workdir, sr):
    cur = ffprobe_duration(Path(workdir, p.name))
    if cur <= 0:
        return p, 1.0
    if cur >= target:
        out = Path(workdir, p.name.replace(".wav","_pad.wav"))
        sh(["ffmpeg","-y","-i", p.name, "-af", f"atrim=duration={target:.6f}", "-ar", str(sr), "-ac","1", out.name], cwd=workdir)
        return out, 1.0
    pad_dur = max(target - cur, 0.0)
    out = Path(workdir, p.name.replace(".wav","_pad.wav"))
    sh(["ffmpeg","-y","-i", p.name, "-af", f"apad=pad_dur={pad_dur:.6f},atrim=duration={target:.6f}",
        "-ar", str(sr), "-ac","1", out.name], cwd=workdir)
    return out, 1.0

def sync_smart(p, target, workdir, sr, tol, maxstretch):
    cur = ffprobe_duration(Path(workdir, p.name))
    if cur <= 0: return p, 1.0
    low = target*(1-tol); high = target*(1+tol)
    if cur < low:
        return sync_pad(p, target, workdir, sr)
    elif cur > high:
        return sync_fit(p, target, workdir, sr, tol, maxstretch)
    else:
        return p, 1.0

# ---------------- NOVO: Elastic Sync com redistribuição ----------------
def sync_elastic(segments_data, workdir, sr, tol=0.15, maxstretch=1.35):
    """
    Sincronização elástica que redistribui tempo entre segmentos adjacentes
    segments_data: lista de (path, target_duration, segment_info)
    """
    print("\n=== Modo ELASTIC: Redistribuindo tempo entre segmentos ===")

    # Mede durações reais
    actual_durations = []
    for path, target, seg in segments_data:
        actual = ffprobe_duration(Path(workdir, path.name))
        actual_durations.append(actual)

    # Calcula deslocamento acumulado
    cumulative_offset = 0
    adjusted_targets = []

    for i, (path, target, seg) in enumerate(segments_data):
        actual = actual_durations[i]
        diff = actual - target

        # Acumula deslocamento
        cumulative_offset += diff

        # Se deslocamento acumulado é grande, redistribui nos próximos segmentos
        if abs(cumulative_offset) > 0.5 and i < len(segments_data) - 1:
            # Distribui o offset nos próximos N segmentos
            lookahead = min(5, len(segments_data) - i - 1)
            compensation_per_seg = cumulative_offset / lookahead

            # Ajusta alvos futuros
            for j in range(i + 1, min(i + 1 + lookahead, len(segments_data))):
                segments_data[j] = (
                    segments_data[j][0],
                    segments_data[j][1] - compensation_per_seg,
                    segments_data[j][2]
                )

            cumulative_offset = 0

        adjusted_targets.append(target)

    # Aplica sync_fit com alvos ajustados
    results = []
    for i, (path, target, seg) in enumerate(segments_data):
        adjusted_path, ratio = sync_fit(path, target, workdir, sr, tol, maxstretch)
        results.append((adjusted_path, ratio, seg))

    print(f"Elastic sync aplicado em {len(results)} segmentos")
    return results

# ---------------- NOVO: Métricas de qualidade ----------------
def calculate_sync_metrics(segments_info):
    """
    Calcula métricas de qualidade da sincronização
    segments_info: lista de dicts com 'target', 'actual', 'ratio'
    """
    print("\n=== MÉTRICAS DE SINCRONIZAÇÃO ===")

    offsets = []
    ratios = []

    for seg in segments_info:
        offset = seg['actual'] - seg['target']
        offsets.append(offset)
        ratios.append(seg.get('ratio', 1.0))

    offsets = np.array(offsets)
    ratios = np.array(ratios)

    metrics = {
        "total_segments": len(segments_info),
        "avg_offset": float(np.mean(offsets)),
        "max_offset": float(np.max(np.abs(offsets))),
        "std_offset": float(np.std(offsets)),
        "avg_speed_ratio": float(np.mean(ratios)),
        "max_speed_ratio": float(np.max(ratios)),
        "segments_over_tolerance": int(np.sum(np.abs(offsets) > 0.5)),
        "segments_compressed": int(np.sum(ratios > 1.1)),
        "segments_expanded": int(np.sum(ratios < 0.9)),
    }

    print(f"  Total de segmentos: {metrics['total_segments']}")
    print(f"  Offset médio: {metrics['avg_offset']:.3f}s")
    print(f"  Offset máximo: {metrics['max_offset']:.3f}s")
    print(f"  Desvio padrão: {metrics['std_offset']:.3f}s")
    print(f"  Ratio de velocidade médio: {metrics['avg_speed_ratio']:.3f}x")
    print(f"  Segmentos fora da tolerância: {metrics['segments_over_tolerance']}")
    print(f"  Segmentos comprimidos (>1.1x): {metrics['segments_compressed']}")
    print(f"  Segmentos expandidos (<0.9x): {metrics['segments_expanded']}")

    return metrics

# ---------------- etapa 8: concat ----------------
def concat_segments(seg_files, workdir, samplerate, segs_trad=None, preserve_gaps=False, gap_min=0.20):
    print("\n=== ETAPA 8: Concatenação ===")
    lst = Path(workdir, "list.txt")
    files_for_concat = []

    if preserve_gaps and segs_trad is not None and len(segs_trad) == len(seg_files):
        for i, p in enumerate(seg_files):
            files_for_concat.append(p)
            if i < len(seg_files)-1:
                gap = max(0.0, segs_trad[i+1]["start"] - segs_trad[i]["end"])
                if gap >= gap_min:
                    sil = make_silence_wav(workdir, i+1, gap, samplerate)
                    files_for_concat.append(sil)
    else:
        files_for_concat = seg_files

    with open(lst, "w", encoding="utf-8") as f:
        for p in files_for_concat:
            f.write(f"file '{p.name}'\n")

    out = Path(workdir, "dub_raw.wav")
    sh([
        "ffmpeg","-y","-f","concat","-safe","0","-i", lst.name,
        "-c:a","pcm_s16le","-ar", str(samplerate),"-ac","1", out.name
    ], cwd=workdir)
    return out

# ---------------- etapa 9: pós ----------------
def postprocess_audio(wav_in, workdir, samplerate):
    print("\n=== ETAPA 9: Pós-processo ===")
    out = Path(workdir, "dub_final.wav")
    fx = "loudnorm=I=-16:TP=-1.5:LRA=11,afftdn=nf=-25,equalizer=f=6500:t=h:width=2000:g=-4"
    sh(["ffmpeg","-y","-i", wav_in.name, "-af", fx, "-ar", str(samplerate), "-ac","1", out.name], cwd=workdir)
    return out

# ---------------- etapa 10: mux ----------------
def mux_video(video_in, wav_in, out_mp4, bitrate):
    print("\n=== ETAPA 10: Mux final ===")
    sh(["ffmpeg","-y","-i", str(video_in), "-i", str(wav_in),
        "-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a", bitrate, str(out_mp4)])

# ---------------- main ----------------
def main():
    print("=== PIPELINE DE DUBLAGEM v2.0 - SINCRONIZAÇÃO MELHORADA ===")
    print("=== ETAPA 1: Entrada/cheques ===")
    ap = argparse.ArgumentParser(description="Dublagem com sincronização avançada")
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", dest="out", default=None)
    ap.add_argument("--src", required=True)
    ap.add_argument("--tgt", required=True)
    ap.add_argument("--tts", choices=["bark","coqui"], default="bark")
    ap.add_argument("--voice", default=None)
    ap.add_argument("--rate", type=int, default=24000)
    ap.add_argument("--bitrate", default="192k")

    ap.add_argument("--sync", choices=["none","fit","pad","smart","elastic"], default="smart")
    ap.add_argument("--tolerance", type=float, default=0.15)
    ap.add_argument("--maxstretch", type=float, default=1.35)
    ap.add_argument("--maxdur", type=float, default=10.0)
    ap.add_argument("--texttemp", type=float, default=0.6)
    ap.add_argument("--wavetemp", type=float, default=0.6)
    ap.add_argument("--fade", type=float, default=0.02)

    ap.add_argument("--preserve-gaps", action="store_true")
    ap.add_argument("--gap-min", type=float, default=0.20)
    ap.add_argument("--enable-vad", action="store_true", help="Ativa detecção de pausas naturais")

    args = ap.parse_args()

    ensure_ffmpeg()
    workdir = Path("dub_work"); workdir.mkdir(exist_ok=True)

    video_in = Path(args.inp).resolve()
    if not video_in.exists():
        print("Arquivo de entrada não encontrado:", video_in); sys.exit(1)

    outdir = Path("dublado")
    outdir.mkdir(exist_ok=True)
    out_mp4 = Path(args.out) if args.out else (outdir / video_in.name)

    print("\n=== ETAPA 2: Extração de áudio ===")
    audio_src = Path(workdir, "audio_src.wav")
    sh(["ffmpeg","-y","-i", str(video_in), "-vn", "-ac","1","-ar","48000","-c:a","pcm_s16le", str(audio_src)])

    # Etapas 3-5
    asr_json, asr_srt, segs = transcribe_faster_whisper(audio_src, workdir, args.src)
    segs_trad, trad_json, trad_srt = translate_segments_m2m100(segs, args.src, args.tgt, workdir)

    # Split com VAD se habilitado
    if args.enable_vad:
        segs_trad = split_long_segments_vad(segs_trad, args.maxdur, audio_src)
    else:
        # Usa função original simplificada
        segs_trad = split_long_segments_vad(segs_trad, args.maxdur, None)

    # Etapa 6: TTS
    if args.tts == "bark":
        seg_files, sr_segs = tts_bark(segs_trad, workdir, text_temp=args.texttemp, wave_temp=args.wavetemp, history_prompt=args.voice)
    else:
        seg_files, sr_segs = tts_coqui(segs_trad, workdir, args.tgt, speaker=args.voice)

    # Etapa 6.1: Fade
    if args.fade and args.fade > 0:
        print("\n=== ETAPA 6.1: Micro-fade ===")
        xf_files = []
        for i, _ in enumerate(segs_trad, 1):
            base = Path(workdir, f"seg_{i:04d}.wav")
            out = Path(workdir, f"seg_{i:04d}_xf.wav")
            safe_fade(base, out, workdir, args.fade)
            xf_files.append(out)
        seg_files = xf_files

    # Etapa 7: Sincronização
    print("\n=== ETAPA 7: Sincronização ===")
    fixed = []
    sync_info = []

    if args.sync == "elastic":
        # Prepara dados para elastic sync
        segments_data = []
        for i, s in enumerate(segs_trad, 1):
            target = max(0.05, s["end"] - s["start"])
            p = Path(workdir, f"seg_{i:04d}{'_xf' if (args.fade and args.fade > 0) else ''}.wav")
            segments_data.append((p, target, s))

        results = sync_elastic(segments_data, workdir, sr_segs, args.tolerance, args.maxstretch)
        for path, ratio, seg in results:
            fixed.append(path)
            sync_info.append({
                "target": seg["end"] - seg["start"],
                "actual": ffprobe_duration(path),
                "ratio": ratio
            })
    else:
        # Sync normal
        for i, s in enumerate(segs_trad, 1):
            target = max(0.05, s["end"] - s["start"])
            p = Path(workdir, f"seg_{i:04d}{'_xf' if (args.fade and args.fade > 0) else ''}.wav")

            if args.sync == "none":
                fixed.append(p)
                ratio = 1.0
            elif args.sync == "fit":
                synced, ratio = sync_fit(p, target, workdir, sr_segs, args.tolerance, args.maxstretch)
                fixed.append(synced)
            elif args.sync == "pad":
                synced, ratio = sync_pad(p, target, workdir, sr_segs)
                fixed.append(synced)
            elif args.sync == "smart":
                synced, ratio = sync_smart(p, target, workdir, sr_segs, args.tolerance, args.maxstretch)
                fixed.append(synced)

            sync_info.append({
                "target": target,
                "actual": ffprobe_duration(fixed[-1]),
                "ratio": ratio
            })

    seg_files = fixed

    # Calcula métricas
    metrics = calculate_sync_metrics(sync_info)

    # Etapas 8-10
    dub_raw = concat_segments(seg_files, workdir, sr_segs, segs_trad=segs_trad, preserve_gaps=args.preserve_gaps, gap_min=args.gap_min)
    dub_final = postprocess_audio(dub_raw, workdir, args.rate)
    mux_video(video_in, dub_final, out_mp4, args.bitrate)

    # Logs
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
        "fade": args.fade, "preserve_gaps": args.preserve_gaps, "gap_min": args.gap_min,
        "vad_enabled": args.enable_vad,
        "sync_metrics": metrics
    }
    with open(Path(workdir, "logs.json"), "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

    print("\n" + "="*60)
    print("CONCLUÍDO!")
    print("="*60)
    print(f"Vídeo dublado: {out_mp4}")
    print(f"Legendas: {trad_srt}")
    print(f"Logs e métricas: {Path(workdir, 'logs.json')}")
    print(f"Arquivos intermediários: {workdir}")
    print("="*60)

if __name__ == "__main__":
    main()

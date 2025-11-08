# dublar_tech_v2.py
# Pipeline de dublagem OTIMIZADO PARA CONTEÚDO TÉCNICO
# Inclui: glossário técnico, tradução consciente de comprimento, preservação de termos

import os, sys, json, csv, argparse, subprocess, shutil, re, warnings
from pathlib import Path
import numpy as np
from datetime import datetime

# Detecção automática de GPU/CUDA
# Se quiser forçar CPU, descomente a linha abaixo:
# os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

warnings.filterwarnings("ignore")

# ---------------- CHECKPOINT SYSTEM ----------------
def save_checkpoint(workdir, step_num, step_name):
    """Salva checkpoint da etapa concluída"""
    checkpoint_file = Path(workdir, "checkpoint.json")
    checkpoint = {
        "last_step": step_name,
        "last_step_num": step_num,
        "next_step": step_num + 1,
        "timestamp": datetime.now().isoformat()
    }
    with open(checkpoint_file, 'w', encoding='utf-8') as f:
        json.dump(checkpoint, f, indent=2, ensure_ascii=False)
    print(f"[CHECKPOINT] Etapa {step_num} salva: {step_name}")

# ---------------- GLOSSÁRIO TÉCNICO ----------------
TECH_GLOSSARY = {
    # Programação
    "string": "string",
    "array": "array",
    "function": "função",
    "method": "método",
    "class": "classe",
    "object": "objeto",
    "variable": "variável",
    "parameter": "parâmetro",
    "argument": "argumento",
    "return": "retornar",
    "loop": "loop",
    "if statement": "condicional if",
    "else": "else",
    "callback": "callback",
    "async": "async",
    "await": "await",
    "promise": "promise",
    "API": "API",
    "endpoint": "endpoint",
    "request": "requisição",
    "response": "resposta",
    "database": "banco de dados",
    "query": "query",
    "schema": "schema",
    "model": "modelo",
    "controller": "controller",
    "view": "view",
    "route": "rota",
    "middleware": "middleware",
    "framework": "framework",
    "library": "biblioteca",
    "package": "pacote",
    "module": "módulo",
    "import": "importar",
    "export": "exportar",
    "component": "componente",
    "props": "props",
    "state": "state",
    "hook": "hook",
    "render": "renderizar",
    "commit": "commit",
    "push": "push",
    "pull": "pull",
    "merge": "merge",
    "branch": "branch",
    "repository": "repositório",
    "git": "git",
    "debug": "debug",
    "console": "console",
    "terminal": "terminal",
    "command line": "linha de comando",
    "CLI": "CLI",
    "GUI": "GUI",
    "backend": "backend",
    "frontend": "frontend",
    "full stack": "full stack",
    "deployment": "deployment",
    "docker": "docker",
    "container": "container",
    "cloud": "nuvem",
    "Cloud Code": "Claude Code",  # Nome do produto
    "Claude Code": "Claude Code",  # Preserva nome
    "server": "servidor",
    "client": "cliente",
    "localhost": "localhost",
    "port": "porta",
    "HTTP": "HTTP",
    "HTTPS": "HTTPS",
    "REST": "REST",
    "JSON": "JSON",
    "XML": "XML",
    "HTML": "HTML",
    "CSS": "CSS",
    "JavaScript": "JavaScript",
    "Python": "Python",
    "TypeScript": "TypeScript",
    "React": "React",
    "Node": "Node",
    "npm": "npm",
    "yarn": "yarn",
    "webpack": "webpack",
    "babel": "babel",
    "lint": "lint",
    "test": "teste",
    "unit test": "teste unitário",
    "integration test": "teste de integração",
    "bug": "bug",
    "feature": "feature",
    "refactor": "refatorar",
    "code review": "code review",
    "pull request": "pull request",
    "issue": "issue",
    "ticket": "ticket",
    "sprint": "sprint",
    "agile": "ágil",
    "scrum": "scrum",
}

# Termos que NUNCA devem ser traduzidos
PRESERVE_TERMS = {
    "string", "array", "boolean", "null", "undefined", "true", "false",
    "const", "let", "var", "function", "class", "new", "return",
    "if", "else", "for", "while", "switch", "case", "break", "continue",
    "try", "catch", "finally", "throw", "async", "await", "promise",
    "console", "log", "error", "warn", "debug", "import", "export", "from",
    "default", "extends", "implements", "interface", "type", "enum",
    "public", "private", "protected", "static", "abstract",
    "git", "commit", "push", "pull", "merge", "branch", "checkout",
    "npm", "yarn", "pip", "docker", "kubernetes",
    "API", "REST", "HTTP", "HTTPS", "JSON", "XML", "HTML", "CSS",
    "localhost", "callback", "middleware", "endpoint", "props", "state", "hook",
    "Claude Code", "Cloud Code",  # Nomes de produtos
}

def protect_technical_terms(text):
    """Protege termos técnicos substituindo por placeholders"""
    protected = text
    replacements = {}

    # Protege termos técnicos (case insensitive mas preserva case)
    for i, term in enumerate(sorted(PRESERVE_TERMS, key=len, reverse=True)):
        # Busca termo como palavra completa (word boundary)
        pattern = r'\b' + re.escape(term) + r'\b'
        matches = list(re.finditer(pattern, protected, re.IGNORECASE))

        for match in reversed(matches):  # Reversed para não afetar índices
            original = match.group()
            placeholder = f"__TECH{i:03d}__"
            replacements[placeholder] = original
            protected = protected[:match.start()] + placeholder + protected[match.end():]

    return protected, replacements

def restore_technical_terms(text, replacements):
    """Restaura termos técnicos protegidos"""
    restored = text
    for placeholder, original in replacements.items():
        restored = restored.replace(placeholder, original)
    return restored

# ---------------- TRADUÇÃO COM CONTROLE DE COMPRIMENTO ----------------
def translate_with_length_control(text, src_lang, tgt_lang, target_duration, tokenizer, model):
    """
    Traduz tentando manter comprimento similar ao original
    """
    # Protege termos técnicos
    protected_text, replacements = protect_technical_terms(text)

    # Calcula comprimento alvo (com margem de 10%)
    src_words = len(text.split())
    expansion_factor = LinguisticDensity.get_expansion_factor(src_lang, tgt_lang)
    target_words = int(src_words * expansion_factor * 1.1)  # +10% margem

    # Traduz
    tokenizer.src_lang = src_lang
    # CORRIGIDO: Aumenta max_length para não truncar frases longas
    encoded = tokenizer(protected_text, return_tensors="pt", padding=True, truncation=True, max_length=1024)

    # Gera com controle de comprimento
    generated = model.generate(
        **encoded,
        forced_bos_token_id=tokenizer.get_lang_id(tgt_lang),
        # CORRIGIDO: Aumenta limite para não cortar traduções
        max_new_tokens=min(target_words + 100, 512),  # Permite traduções completas
        min_length=max(target_words - 20, 10),
        num_beams=5,  # Melhor qualidade
        length_penalty=0.8,  # CORRIGIDO: Reduz penalidade para permitir traduções completas
        no_repeat_ngram_size=3,
    )

    translation = tokenizer.batch_decode(generated, skip_special_tokens=True)[0]

    # Restaura termos técnicos
    translation = restore_technical_terms(translation, replacements)

    # Corrige palavras em inglês que vazaram (comum no M2M100)
    translation = fix_mixed_language(translation, tgt_lang)

    return translation.strip()

def fix_mixed_language(text, target_lang):
    """
    Detecta e corrige palavras em inglês que vazaram na tradução portuguesa
    """
    if target_lang != "pt":
        return text

    # Dicionário de correções comuns EN -> PT que o M2M100 erra
    common_fixes = {
        r'\bthis\b': 'este',
        r'\bthis video\b': 'este vídeo',
        r'\bthis code\b': 'este código',
        r'\bthis file\b': 'este arquivo',
        r'\bthis function\b': 'esta função',
        r'\bthat\b': 'isso',
        r'\bthese\b': 'estes',
        r'\bthose\b': 'aqueles',
        r'\bwhen you go\b': 'quando você vai',
        r'\byou can\b': 'você pode',
        r'\byou have\b': 'você tem',
        r'\bI will\b': 'eu vou',
        r'\bI am\b': 'eu estou',
        r'\bwe are\b': 'nós estamos',
        r'\bit is\b': 'é',
        r'\bthere is\b': 'há',
        r'\bthere are\b': 'há',
    }

    fixed = text
    for en_pattern, pt_replacement in common_fixes.items():
        fixed = re.sub(en_pattern, pt_replacement, fixed, flags=re.IGNORECASE)

    # Detecta palavras isoladas em inglês (heurística simples)
    # Se uma palavra começa com maiúscula em meio à frase em português, pode ser inglês vazado
    # Mas preserva termos técnicos e nomes próprios

    return fixed

def simplify_for_dubbing(text, max_words=None):
    """
    Simplifica texto para caber melhor na dublagem
    Remove palavras de enchimento mantendo significado
    """
    # Remove expressões verbosas comuns
    simplifications = {
        r'\bvocê sabe\b': '',
        r'\bbem,?\s*': '',
        r'\bentão,?\s*': '',
        r'\bassim,?\s*': '',
        r'\bbasicamente\b': '',
        r'\bnormalmente\b': '',
        r'\bgeralmente\b': '',
        r'\bna verdade\b': '',
        r'\bna realidade\b': '',
        r'\bpor exemplo\b': 'ex:',
        r'\bisso significa que\b': 'ou seja',
        r'\bo que eu quero dizer é\b': '',
        r'\beu acho que\b': '',
        r'\beu acredito que\b': '',
    }

    simplified = text
    for pattern, replacement in simplifications.items():
        simplified = re.sub(pattern, replacement, simplified, flags=re.IGNORECASE)

    # Remove espaços extras
    simplified = re.sub(r'\s+', ' ', simplified).strip()

    # Se ainda muito longo, remove mais
    if max_words and len(simplified.split()) > max_words:
        words = simplified.split()
        # Remove advérbios e adjetivos desnecessários
        essential_words = []
        skip_words = {'muito', 'realmente', 'bastante', 'bem', 'meio', 'um pouco'}
        for word in words:
            if word.lower() not in skip_words or len(essential_words) < 3:
                essential_words.append(word)
                if len(essential_words) >= max_words:
                    break
        simplified = ' '.join(essential_words)

    return simplified

# ---------------- Utilidades (mesmo código anterior) ----------------
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

class LinguisticDensity:
    EXPANSION_FACTORS = {
        "pt": 1.20, "pt-br": 1.20, "es": 1.15, "fr": 1.18,
        "de": 0.95, "it": 1.12, "en": 1.00, "ja": 0.80,
        "zh": 0.75, "ru": 1.05,
    }

    @classmethod
    def get_expansion_factor(cls, src_lang, tgt_lang):
        src = cls.EXPANSION_FACTORS.get(src_lang.lower(), 1.0)
        tgt = cls.EXPANSION_FACTORS.get(tgt_lang.lower(), 1.0)
        return tgt / src

    @classmethod
    def calculate_cps(cls, text, duration):
        chars = len(re.sub(r'\s+', '', text))
        return chars / max(duration, 0.1)

    @classmethod
    def calculate_wps(cls, text, duration):
        words = len(text.split())
        return words / max(duration, 0.1)

def detect_speech_pauses(audio_path, min_silence_dur=0.3):
    try:
        import librosa
        y, sr = librosa.load(audio_path, sr=16000, mono=True)
        frame_length = int(sr * 0.025)
        hop_length = int(sr * 0.010)
        rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
        threshold = np.percentile(rms, 20)
        silent_frames = rms < threshold
        times = librosa.frames_to_time(np.arange(len(silent_frames)), sr=sr, hop_length=hop_length)

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
        return []
    except Exception as e:
        print(f"  [AVISO] Erro no VAD: {e}")
        return []

def estimate_tts_duration(text, lang="pt", base_wps=2.5):
    words = len(text.split())
    speed_factors = {"pt": 1.0, "en": 1.1, "es": 0.95, "fr": 0.90}
    factor = speed_factors.get(lang.lower(), 1.0)
    adjusted_wps = base_wps * factor
    duration = words / adjusted_wps
    pauses = text.count('.') * 0.3 + text.count(',') * 0.15 + text.count('?') * 0.3 + text.count('!') * 0.3
    total = duration + pauses
    return max(total, 0.5)

# ---------------- ASR ----------------
def transcribe_faster_whisper(wav_path, workdir, src_lang):
    print("\n=== ETAPA 3: Transcrição (Whisper) ===")
    from faster_whisper import WhisperModel
    import torch

    # Estima duração do áudio
    audio_duration = ffprobe_duration(wav_path)
    estimated_segments = int(audio_duration / 3)  # ~1 segmento a cada 3 segundos
    estimated_time_min = int(audio_duration / 60)  # ~1min de processamento por 1min de áudio

    print(f"\n{'='*60}")
    print(f"  Duração do áudio: {int(audio_duration/60)}m {int(audio_duration%60)}s")
    print(f"  Segmentos estimados: ~{estimated_segments}")
    print(f"  Tempo estimado: ~{estimated_time_min} minuto(s)")
    print(f"{'='*60}\n")

    # Whisper: Força CPU (problema com cuBLAS 12 vs 11)
    # GPU será usada em Bark onde o ganho é maior (5-10x)
    print("Usando CPU para Whisper (evita incompatibilidade CUDA)...")
    print("  (GPU será usada no Bark TTS - onde o ganho é maior!)")
    device = "cpu"
    compute_type = "int8"
    use_vad = True

    print(f"Carregando modelo Whisper medium ({device.upper()})...")

    try:
        model = WhisperModel("medium", device=device, compute_type=compute_type)
        print("Transcrevendo áudio...")
        segments, info = model.transcribe(str(wav_path), language=src_lang, vad_filter=use_vad)
        print(f"[OK] Idioma detectado: {info.language} (confiança: {info.language_probability:.2f})")
    except Exception as e:
        print(f"ERRO na transcrição: {e}")
        raise

    segs = []
    print("\nProcessando segmentos...")
    seg_count = 0
    for s in segments:
        seg_count += 1
        segs.append({"start": float(s.start), "end": float(s.end), "text": (s.text or "").strip()})
        if seg_count % 10 == 0:
            print(f"  Processados {seg_count} segmentos...")

    print(f"\n{'='*60}")
    print(f"  [OK] TOTAL: {len(segs)} segmentos transcritos")
    print(f"  (Estimativa: {estimated_segments} | Real: {len(segs)})")
    print(f"{'='*60}")

    srt_path = Path(workdir, "asr.srt")
    json_path = Path(workdir, "asr.json")
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, s in enumerate(segs, 1):
            f.write(f"{i}\n{ts_stamp(s['start'])} --> {ts_stamp(s['end'])}\n{s['text']}\n\n")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"language": src_lang, "segments": segs}, f, ensure_ascii=False, indent=2)
    print(f"Transcrito: {len(segs)} segmentos")
    return json_path, srt_path, segs

# ---------------- TRADUÇÃO MELHORADA PARA CONTEÚDO TÉCNICO ----------------
def translate_segments_technical(segs, src, tgt, workdir, simplify=True):
    print("\n=== ETAPA 4: Tradução TÉCNICA com controle de comprimento ===")
    import time
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

    total_segments = len(segs)

    # Carrega modelo ANTES de mostrar estimativa
    print("\nCarregando modelo M2M100 (pode baixar ~2GB na primeira vez)...")
    model_name = "facebook/m2m100_418M"

    print("  - Carregando tokenizer...")
    tok = AutoTokenizer.from_pretrained(model_name)

    print("  - Carregando modelo de tradução...")
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

    print("[OK] Modelo carregado!\n")

    # AGORA mostra estimativa
    estimated_minutes = int(total_segments * 0.5 / 60)  # ~0.5s por segmento

    print(f"{'='*60}")
    print(f"  Total de segmentos: {total_segments}")
    print(f"  Tempo estimado: ~{estimated_minutes} minuto(s)")
    print(f"  (Apenas tradução, modelo já carregado)")
    print(f"{'='*60}\n")

    src = (src or "en").lower()
    tgt = (tgt or "pt").lower()
    if hasattr(tok, "lang_code_to_id"):
        if src not in tok.lang_code_to_id: src = "en"
        if tgt not in tok.lang_code_to_id: tgt = "pt"

    out = []

    print(f"  Modo técnico: preservando {len(PRESERVE_TERMS)} termos")
    print(f"  Simplificação: {'ATIVA' if simplify else 'DESATIVA'}")
    print(f"  Traduzindo {src} -> {tgt}...\n")

    start_time = time.time()

    for i, s in enumerate(segs):
        text = s.get("text", "").strip()
        dur = s["end"] - s["start"]

        # Traduz com controle de comprimento
        translation = translate_with_length_control(text, src, tgt, dur, tok, model)

        # Simplifica se necessário
        if simplify:
            # Calcula palavras máximas baseado na duração
            max_words = int((dur * 2.5) * 1.1)  # 2.5 palavras/seg + 10% margem
            translation = simplify_for_dubbing(translation, max_words)

        item = dict(s)
        item["text_trad"] = translation
        item["text_original"] = text
        item["original_wps"] = LinguisticDensity.calculate_wps(text, dur)
        item["trad_wps"] = LinguisticDensity.calculate_wps(translation, dur)
        item["trad_estimated_dur"] = estimate_tts_duration(translation, tgt)
        item["compression_ratio"] = len(translation.split()) / max(len(text.split()), 1)

        out.append(item)

        if (i + 1) % 10 == 0:
            elapsed = time.time() - start_time
            avg_speed = elapsed / (i + 1)
            remaining = (total_segments - i - 1) * avg_speed
            eta_sec = int(remaining)
            print(f"  Traduzidos {i+1}/{total_segments} ({(i+1)/total_segments*100:.1f}%) - ETA: {eta_sec}s")

    srt_t = Path(workdir, "asr_trad.srt")
    json_t = Path(workdir, "asr_trad.json")
    with open(srt_t, "w", encoding="utf-8") as f:
        for i, s in enumerate(out, 1):
            f.write(f"{i}\n{ts_stamp(s['start'])} --> {ts_stamp(s['end'])}\n{s['text_trad']}\n\n")
    with open(json_t, "w", encoding="utf-8") as f:
        json.dump({"language": tgt, "segments": out}, f, ensure_ascii=False, indent=2)

    # Estatísticas
    avg_compression = np.mean([s['compression_ratio'] for s in out])
    print(f"\nTraduzido: {len(out)} segmentos")
    print(f"Taxa de compressão média: {avg_compression:.2f}x")

    return out, json_t, srt_t

# [Resto do código igual ao dublar_sync_v2.py - split, TTS, sync, concat, etc.]
# Copiando funções necessárias...

def split_long_segments_vad(segments, maxdur, audio_src_path=None):
    print("\n=== ETAPA 5: Split inteligente com VAD ===")
    if not maxdur or maxdur <= 0:
        print("Split desativado.")
        return segments

    pauses = []
    if audio_src_path and Path(audio_src_path).exists():
        print("Detectando pausas naturais no áudio...")
        pauses = detect_speech_pauses(audio_src_path, min_silence_dur=0.3)

    out = []
    for s in segments:
        start, end = s["start"], s["end"]
        text = (s.get("text_trad") or "").strip()
        dur = max(0.001, end - start)

        if dur <= maxdur or len(text.split()) < 16:
            out.append(s)
            continue

        segment_pauses = [(p[0], p[1]) for p in pauses if start <= p[0] < end]

        if segment_pauses:
            parts_by_pause = []
            current_start = start

            for pause_start, pause_end in segment_pauses:
                if pause_start - current_start >= 1.0:
                    parts_by_pause.append((current_start, pause_start))
                    current_start = pause_end

            if end - current_start >= 0.5:
                parts_by_pause.append((current_start, end))

            if parts_by_pause:
                total_dur = sum(p[1] - p[0] for p in parts_by_pause)
                words = text.split()
                word_idx = 0

                for i, (p_start, p_end) in enumerate(parts_by_pause):
                    part_dur = p_end - p_start
                    proportion = part_dur / total_dur
                    num_words = max(1, int(len(words) * proportion))

                    if i == len(parts_by_pause) - 1:
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

def tts_bark(segments, workdir, text_temp=0.6, wave_temp=0.6, history_prompt=None):
    print("\n=== ETAPA 6: TTS (Bark) ===")
    import time
    import torch

    # Fix para PyTorch 2.6+ - monkey-patch torch.load para aceitar weights_only=False
    original_load = torch.load
    def patched_load(*args, **kwargs):
        kwargs['weights_only'] = False
        return original_load(*args, **kwargs)
    torch.load = patched_load

    from bark import generate_audio, SAMPLE_RATE
    from scipy.io.wavfile import write

    # Detecção automática de GPU/CPU
    use_gpu = torch.cuda.is_available()
    if use_gpu:
        print("GPU detectada! Usando CUDA para TTS (muito mais rápido)...")
        avg_time_per_segment = 1.5  # ~1.5s por segmento na GPU
    else:
        print("GPU não disponível, usando CPU (mais lento)...")
        avg_time_per_segment = 8  # ~8s por segmento na CPU

    # ESTIMATIVA DE TEMPO
    total_segments = len(segments)
    estimated_minutes = (total_segments * avg_time_per_segment) / 60

    print(f"\n{'='*60}")
    print(f"  AVISO: PROCESSO DEMORADO!")
    print(f"{'='*60}")
    print(f"  Total de segmentos: {total_segments}")
    print(f"  Tempo estimado: ~{int(estimated_minutes)} minutos")
    print(f"  (~{avg_time_per_segment}s por segmento em CPU)")
    print(f"{'='*60}")
    print("\nGerando áudio dos segmentos...\n")

    history = None
    if history_prompt:
        try:
            from bark.generation import load_history_prompt
            history = load_history_prompt(history_prompt)
        except Exception:
            history = history_prompt

    seg_files = []
    tsv = Path(workdir, "segments.csv")
    start_time = time.time()

    with open(tsv, "w", encoding="utf-8", newline="") as fcsv:
        w = csv.writer(fcsv)
        w.writerow(["idx", "t_in","t_out","texto_trad","file","estimated_dur","actual_dur","compression_ratio"])

        for i, s in enumerate(segments, 1):
            seg_start = time.time()

            txt = (s.get("text_trad") or "").strip()
            if len(re.findall(r"[A-Za-zÀ-ÿ0-9]", txt)) < 3:
                txt = "pausa curta"

            estimated = s.get("trad_estimated_dur", estimate_tts_duration(txt, "pt"))
            compression = s.get("compression_ratio", 1.0)

            out = Path(workdir, f"seg_{i:04d}.wav")
            audio = generate_audio(txt, history_prompt=history, text_temp=text_temp, waveform_temp=wave_temp)
            write(out, SAMPLE_RATE, audio)

            actual_dur = ffprobe_duration(out)
            seg_time = time.time() - seg_start

            seg_files.append(out)
            w.writerow([i, s["start"], s["end"], txt, out.name, f"{estimated:.3f}", f"{actual_dur:.3f}", f"{compression:.2f}"])

            # Progresso com ETA
            if i % 10 == 0 or i == total_segments:
                elapsed = time.time() - start_time
                avg_speed = elapsed / i
                remaining = (total_segments - i) * avg_speed
                eta_minutes = int(remaining / 60)
                eta_seconds = int(remaining % 60)

                print(f"  [{i}/{total_segments}] {(i/total_segments*100):.1f}% - "
                      f"ETA: {eta_minutes}m {eta_seconds}s - "
                      f"Último segmento: {seg_time:.1f}s")

    total_time = time.time() - start_time
    print(f"\n[OK] TTS Bark gerou: {len(seg_files)} arquivos em {int(total_time/60)}m {int(total_time%60)}s")
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
        w.writerow(["idx", "t_in","t_out","texto_trad","file","estimated_dur","actual_dur","compression_ratio"])
        for i, s in enumerate(segments, 1):
            txt = (s.get("text_trad") or "").strip()
            if len(re.findall(r"[A-Za-zÀ-ÿ0-9]", txt)) < 3:
                txt = "pausa curta"

            estimated = s.get("trad_estimated_dur", estimate_tts_duration(txt, tgt_lang))
            compression = s.get("compression_ratio", 1.0)

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
            w.writerow([i, s["start"], s["end"], txt, out.name, f"{estimated:.3f}", f"{actual_dur:.3f}", f"{compression:.2f}"])

    print(f"TTS Coqui gerou: {len(seg_files)} arquivos")
    return seg_files, sample_rate

# [Funções de sync do arquivo anterior]
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

def sync_elastic(segments_data, workdir, sr, tol=0.15, maxstretch=1.35):
    print("\n=== Modo ELASTIC: Redistribuindo tempo entre segmentos ===")

    actual_durations = []
    for path, target, seg in segments_data:
        actual = ffprobe_duration(Path(workdir, path.name))
        actual_durations.append(actual)

    cumulative_offset = 0
    adjusted_targets = []

    for i, (path, target, seg) in enumerate(segments_data):
        actual = actual_durations[i]
        diff = actual - target

        cumulative_offset += diff

        if abs(cumulative_offset) > 0.5 and i < len(segments_data) - 1:
            lookahead = min(5, len(segments_data) - i - 1)
            compensation_per_seg = cumulative_offset / lookahead

            for j in range(i + 1, min(i + 1 + lookahead, len(segments_data))):
                segments_data[j] = (
                    segments_data[j][0],
                    segments_data[j][1] - compensation_per_seg,
                    segments_data[j][2]
                )

            cumulative_offset = 0

        adjusted_targets.append(target)

    results = []
    for i, (path, target, seg) in enumerate(segments_data):
        adjusted_path, ratio = sync_fit(path, target, workdir, sr, tol, maxstretch)
        results.append((adjusted_path, ratio, seg))

    print(f"Elastic sync aplicado em {len(results)} segmentos")
    return results

def calculate_sync_metrics(segments_info):
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

def postprocess_audio(wav_in, workdir, samplerate):
    print("\n=== ETAPA 9: Pós-processo ===")
    out = Path(workdir, "dub_final.wav")
    fx = "loudnorm=I=-16:TP=-1.5:LRA=11,afftdn=nf=-25,equalizer=f=6500:t=h:width=2000:g=-4"
    sh(["ffmpeg","-y","-i", wav_in.name, "-af", fx, "-ar", str(samplerate), "-ac","1", out.name], cwd=workdir)
    return out

def mux_video(video_in, wav_in, out_mp4, bitrate):
    print("\n=== ETAPA 10: Mux final ===")
    sh(["ffmpeg","-y","-i", str(video_in), "-i", str(wav_in),
        "-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a", bitrate, str(out_mp4)])

# ---------------- MAIN ----------------
def main():
    print("="*70)
    print("  PIPELINE DE DUBLAGEM TÉCNICA v2.0")
    print("  Otimizado para vídeos de demonstração técnica e programação")
    print("="*70)
    print("\n=== ETAPA 1: Entrada/cheques ===")

    ap = argparse.ArgumentParser(description="Dublagem otimizada para conteúdo técnico")
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", dest="out", default=None)
    ap.add_argument("--src", required=True)
    ap.add_argument("--tgt", required=True)
    ap.add_argument("--tts", choices=["bark","coqui"], default="bark")
    ap.add_argument("--voice", default=None)
    ap.add_argument("--rate", type=int, default=24000)
    ap.add_argument("--bitrate", default="192k")

    ap.add_argument("--sync", choices=["none","fit","pad","smart","elastic"], default="smart")
    ap.add_argument("--tolerance", type=float, default=0.0)
    ap.add_argument("--maxstretch", type=float, default=2.0)
    ap.add_argument("--maxdur", type=float, default=10.0)
    ap.add_argument("--texttemp", type=float, default=0.6)
    ap.add_argument("--wavetemp", type=float, default=0.6)
    ap.add_argument("--fade", type=float, default=0.02)

    ap.add_argument("--preserve-gaps", action="store_true")
    ap.add_argument("--gap-min", type=float, default=0.20)
    ap.add_argument("--enable-vad", action="store_true")

    # NOVO: Opções para conteúdo técnico
    ap.add_argument("--no-simplify", action="store_true", help="Desativa simplificação automática")

    # Sistema de CHECKPOINT/RESUME
    ap.add_argument("--continue", dest="resume", action="store_true", help="Continua do último checkpoint salvo")

    args = ap.parse_args()

    ensure_ffmpeg()
    workdir = Path("dub_work"); workdir.mkdir(exist_ok=True)

    video_in = Path(args.inp).resolve()
    if not video_in.exists():
        print("Arquivo de entrada não encontrado:", video_in); sys.exit(1)

    outdir = Path("dublado")
    outdir.mkdir(exist_ok=True)
    out_mp4 = Path(args.out) if args.out else (outdir / video_in.name)

    # CHECKPOINT: Detecta qual etapa continuar
    checkpoint_file = Path(workdir, "checkpoint.json")
    start_from = 2  # Padrão: começa da etapa 2

    if args.resume and checkpoint_file.exists():
        import json
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            ckpt = json.load(f)
            start_from = ckpt.get("next_step", 2)
            print(f"\n{'='*60}")
            print(f"  MODO RESUME: Continuando da ETAPA {start_from}")
            print(f"  Última etapa completa: {ckpt.get('last_step', 'Nenhuma')}")
            print(f"{'='*60}\n")

    # ETAPA 2: Extração de áudio
    audio_src = Path(workdir, "audio_src.wav")
    if start_from <= 2:
        print("\n=== ETAPA 2: Extração de áudio ===")
        sh(["ffmpeg","-y","-i", str(video_in), "-vn", "-ac","1","-ar","48000","-c:a","pcm_s16le", str(audio_src)])
        save_checkpoint(workdir, 2, "Extração de áudio")
        start_from = 3
    else:
        print(f"\n[SKIP] ETAPA 2 já completa: {audio_src}")

    # ETAPA 3: Transcrição
    asr_json = Path(workdir, "asr.json")
    asr_srt = Path(workdir, "asr.srt")

    if start_from <= 3:
        asr_json, asr_srt, segs = transcribe_faster_whisper(audio_src, workdir, args.src)
        save_checkpoint(workdir, 3, "Transcrição")
        start_from = 4
    else:
        print(f"\n[SKIP] ETAPA 3 já completa: {asr_json}")
        # Recarrega segmentos do JSON
        import json
        with open(asr_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # O formato é {"language": "en", "segments": [...]}
            segs = data.get("segments", data) if isinstance(data, dict) else data

    # ETAPA 4: TRADUÇÃO TÉCNICA
    trad_json = Path(workdir, "asr_trad.json")
    trad_srt = Path(workdir, "asr_trad.srt")

    if start_from <= 4:
        segs_trad, trad_json, trad_srt = translate_segments_technical(
            segs, args.src, args.tgt, workdir,
            simplify=(not args.no_simplify)
        )
        save_checkpoint(workdir, 4, "Tradução")
        start_from = 5
    else:
        print(f"\n[SKIP] ETAPA 4 já completa: {trad_json}")
        with open(trad_json, 'r', encoding='utf-8') as f:
            segs_trad = json.load(f)

    # ETAPA 5: Split com VAD
    if start_from <= 5:
        if args.enable_vad:
            segs_trad = split_long_segments_vad(segs_trad, args.maxdur, audio_src)
        else:
            segs_trad = split_long_segments_vad(segs_trad, args.maxdur, None)
        save_checkpoint(workdir, 5, "Split de segmentos")
        start_from = 6
    else:
        print(f"\n[SKIP] ETAPA 5 já completa (split)")

    # ETAPA 6: TTS
    seg_1 = Path(workdir, "seg_0001.wav")
    if start_from <= 6:
        if args.tts == "bark":
            seg_files, sr_segs = tts_bark(segs_trad, workdir, text_temp=args.texttemp, wave_temp=args.wavetemp, history_prompt=args.voice)
        else:
            seg_files, sr_segs = tts_coqui(segs_trad, workdir, args.tgt, speaker=args.voice)
        save_checkpoint(workdir, 6, "TTS (geração de áudio)")
        start_from = 7
    else:
        print(f"\n[SKIP] ETAPA 6 já completa: {seg_1} e outros")
        # Recarrega seg_files
        seg_files = sorted(workdir.glob("seg_*.wav"))
        sr_segs = 24000 if args.tts == "bark" else 22050

    # Fade
    if args.fade and args.fade > 0:
        print("\n=== ETAPA 6.1: Micro-fade ===")
        xf_files = []
        for i, _ in enumerate(segs_trad, 1):
            base = Path(workdir, f"seg_{i:04d}.wav")
            out = Path(workdir, f"seg_{i:04d}_xf.wav")
            safe_fade(base, out, workdir, args.fade)
            xf_files.append(out)
        seg_files = xf_files

    # ETAPA 7: Sincronização
    sync_csv = Path(workdir, "segments.csv")
    if start_from <= 7:
        print("\n=== ETAPA 7: Sincronização ===")
        fixed = []
        sync_info = []

        if args.sync == "elastic":
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
        metrics = calculate_sync_metrics(sync_info)
        save_checkpoint(workdir, 7, "Sincronização")
        start_from = 8
    else:
        print(f"\n[SKIP] ETAPA 7 já completa (sincronização)")
        # Recarrega arquivos sincronizados
        fixed = sorted(workdir.glob("seg_*_sync.wav"))
        if not fixed:
            fixed = sorted(workdir.glob("seg_*.wav"))
        seg_files = fixed
        metrics = {}

    # ETAPA 8: Concatenação
    dub_raw = Path(workdir, "dub_raw.wav")
    if start_from <= 8:
        dub_raw = concat_segments(seg_files, workdir, sr_segs, segs_trad=segs_trad, preserve_gaps=args.preserve_gaps, gap_min=args.gap_min)
        save_checkpoint(workdir, 8, "Concatenação")
        start_from = 9
    else:
        print(f"\n[SKIP] ETAPA 8 já completa: {dub_raw}")

    # ETAPA 9: Pós-processamento
    dub_final = Path(workdir, "dub_final.wav")
    if start_from <= 9:
        dub_final = postprocess_audio(dub_raw, workdir, args.rate)
        save_checkpoint(workdir, 9, "Pós-processamento")
        start_from = 10
    else:
        print(f"\n[SKIP] ETAPA 9 já completa: {dub_final}")

    # ETAPA 10: Mux final
    if start_from <= 10:
        mux_video(video_in, dub_final, out_mp4, args.bitrate)
        save_checkpoint(workdir, 10, "Mux final - COMPLETO")
    else:
        print(f"\n[SKIP] ETAPA 10 já completa: {out_mp4}")

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
        "technical_mode": True,
        "simplify_enabled": not args.no_simplify,
        "sync_metrics": metrics
    }
    with open(Path(workdir, "logs.json"), "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

    print("\n" + "="*70)
    print("  CONCLUÍDO!")
    print("="*70)
    print(f"  Vídeo dublado: {out_mp4}")
    print(f"  Legendas: {trad_srt}")
    print(f"  Logs: {Path(workdir, 'logs.json')}")
    print(f"  Arquivos intermediários: {workdir}")
    print("="*70)

if __name__ == "__main__":
    main()

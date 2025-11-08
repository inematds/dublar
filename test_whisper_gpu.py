"""
Teste isolado do Whisper com GPU
Identifica exatamente onde está o problema
"""
import torch
from faster_whisper import WhisperModel
from pathlib import Path

print("="*60)
print("TESTE WHISPER GPU")
print("="*60)

# 1. Verifica CUDA
print("\n[1/5] Verificando CUDA...")
print(f"  PyTorch version: {torch.__version__}")
print(f"  CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"  CUDA version: {torch.version.cuda}")
    print(f"  GPU: {torch.cuda.get_device_name(0)}")

# 2. Carrega modelo
print("\n[2/5] Carregando modelo Whisper...")
try:
    model = WhisperModel("base", device="cuda", compute_type="float16")
    print("  [OK] Modelo carregado em GPU")
except Exception as e:
    print(f"  [ERRO] Falha ao carregar: {e}")
    print("\n  Tentando CPU...")
    model = WhisperModel("base", device="cpu", compute_type="int8")
    print("  [OK] Modelo carregado em CPU")

# 3. Verifica áudio
print("\n[3/5] Verificando áudio...")
audio_path = Path("dub_work/audio_src.wav")
if not audio_path.exists():
    print(f"  [ERRO] Arquivo não encontrado: {audio_path}")
    exit(1)
print(f"  [OK] Áudio encontrado: {audio_path}")

# 4. Testa transcrição SEM VAD
print("\n[4/5] Testando transcrição SEM VAD...")
try:
    segments, info = model.transcribe(str(audio_path), language="en", vad_filter=False)
    print(f"  [OK] Transcrição iniciada")
    print(f"  Idioma: {info.language} (confiança: {info.language_probability:.2f})")

    # Processa apenas os primeiros 3 segmentos
    print("\n  Processando primeiros 3 segmentos...")
    for i, s in enumerate(segments):
        print(f"    [{i+1}] {s.start:.2f}s - {s.end:.2f}s: {s.text[:50]}...")
        if i >= 2:
            break

    print("\n  [OK] Transcrição SEM VAD funcionou!")

except Exception as e:
    print(f"  [ERRO] Falha na transcrição: {e}")
    import traceback
    traceback.print_exc()

# 5. Testa transcrição COM VAD
print("\n[5/5] Testando transcrição COM VAD...")
try:
    model2 = WhisperModel("base", device="cuda", compute_type="float16")
    segments2, info2 = model2.transcribe(str(audio_path), language="en", vad_filter=True)
    print(f"  [OK] Transcrição iniciada")

    # Processa apenas os primeiros 3 segmentos
    print("\n  Processando primeiros 3 segmentos...")
    for i, s in enumerate(segments2):
        print(f"    [{i+1}] {s.start:.2f}s - {s.end:.2f}s: {s.text[:50]}...")
        if i >= 2:
            break

    print("\n  [OK] Transcrição COM VAD funcionou!")

except Exception as e:
    print(f"  [ERRO] Falha na transcrição COM VAD: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("TESTE CONCLUÍDO")
print("="*60)

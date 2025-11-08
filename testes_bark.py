# bark_pipeline.py
# Gera áudio com Bark ajustando temperaturas e faz pós-processo no ffmpeg.

from bark import generate_audio, SAMPLE_RATE
from scipy.io.wavfile import write
import subprocess, shutil, sys
import torch

# texto curto, com pausas e pontuação para melhorar naturalidade
TEXTO = (
    "Olá! Tudo bem? "
    "Este é um teste curto do Bark. "
    "Quero uma fala clara, natural e suave."
)

# temperaturas mais baixas reduzem metalização/ruído
TEXT_TEMP = 0.6
WAVE_TEMP = 0.6

RAW_WAV = "bark_raw.wav"
FINAL_WAV = "bark_final.wav"

print("torch:", torch.__version__, "cuda_ok:", torch.cuda.is_available())

# se quiser testar um preset de voz (se existir no cache), descomente:
# HISTORY_PROMPT = "v2/pt_speaker_6"
HISTORY_PROMPT = None

print("Gerando áudio com Bark...")
audio = generate_audio(
    TEXTO,
    text_temp=TEXT_TEMP,
    waveform_temp=WAVE_TEMP,
    history_prompt=HISTORY_PROMPT,
)
write(RAW_WAV, SAMPLE_RATE, audio)
print("OK ->", RAW_WAV)

# ffmpeg para normalizar loudness, reduzir chiado e suavizar agudos metálicos
ffmpeg = shutil.which("ffmpeg")
filters = 'loudnorm=I=-16:TP=-1.5:LRA=11,afftdn=nf=-25,equalizer=f=6500:t=h:width=2000:g=-4'

if ffmpeg:
    cmd = [
        ffmpeg, "-y",
        "-i", RAW_WAV,
        "-af", filters,
        FINAL_WAV
    ]
    print("Aplicando pós-processo no ffmpeg...")
    subprocess.run(cmd, check=True)
    print("OK ->", FINAL_WAV)
else:
    print("ffmpeg não encontrado. Rode manualmente:")
    print(f'ffmpeg -y -i {RAW_WAV} -af "{filters}" {FINAL_WAV}')

print("Concluído.")

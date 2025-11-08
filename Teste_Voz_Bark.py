from bark import generate_audio, SAMPLE_RATE
from scipy.io.wavfile import write

texto = "Olá, este é um teste de voz em português brasileiro."

presets = [f"v2/pt_speaker_{i}" for i in range(7)]

for preset in presets:
    print("Gerando com:", preset)
    audio = generate_audio(texto, history_prompt=preset)
    filename = f"test_{preset.replace('/', '_')}.wav"
    write(filename, SAMPLE_RATE, audio)
    print("  salvo:", filename)

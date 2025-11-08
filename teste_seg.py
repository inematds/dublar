from bark import generate_audio, SAMPLE_RATE
from scipy.io.wavfile import write

# texto de teste em português
texto = "Olá, este é um teste de voz com Bark em português."

# escolha de voz (pode trocar por v2/pt_speaker_0 .. v2/pt_speaker_6 ou seu .npz)
voz = "v2/pt_speaker_1"

# gera o áudio
audio_array = generate_audio(
    texto,
    history_prompt=voz,
    text_temp=0.6,
    waveform_temp=0.6
)

# salva em arquivo
write("seg_teste.wav", SAMPLE_RATE, audio_array)
print("Segmento gerado: seg_teste.wav")

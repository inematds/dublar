from bark import generate_audio, SAMPLE_RATE
from scipy.io.wavfile import write
import torch

print("torch:", torch.__version__, "cuda_ok:", torch.cuda.is_available())
audio = generate_audio("Olá! Este é um teste curto do Bark.")
write("bark_ok.wav", SAMPLE_RATE, audio)
print("OK -> bark_ok.wav")

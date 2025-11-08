from TTS.api import TTS

tts = TTS("tts_models/pt/cv/vits", gpu=False)  # modelo PT single-speaker
texto = "Olá, este é um teste pequeno com Coqui TTS em português."
tts.tts_to_file(text=texto, file_path="coqui_teste.wav")

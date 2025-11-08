from TTS.api import TTS

tts = TTS("tts_models/multilingual/multi-dataset/your_tts", gpu=False)

# escolha uma voz de PT exatamente como aparece na lista (inclui \n)
voz_pt = next(v for v in tts.speakers if "pt" in v)  # ex.: 'female-pt-4\n'
idioma = "pt-br"  # <- aqui está o ajuste

texto = "Olá, este é um teste pequeno com Coqui TTS em português."
tts.tts_to_file(text=texto, speaker=voz_pt, language=idioma, file_path="coqui_teste1.wav")
print("OK:", repr(voz_pt), idioma)

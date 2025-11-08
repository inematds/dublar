# Mapa Completo de Arquivos Gerados

## 📁 Estrutura de Pastas

```
voz_teste/
├── ccode-dia15.mp4           ← Vídeo original (entrada)
├── dublado/                  ← Pasta de saída
│   └── ccode-dia15.mp4       ← Vídeo dublado FINAL
└── dub_work/                 ← Pasta de trabalho (intermediários)
    ├── audio_src.wav         ← [ETAPA 2] Áudio extraído
    ├── asr.json              ← [ETAPA 3] Transcrição em JSON
    ├── asr.srt               ← [ETAPA 3] Legendas originais
    ├── asr_trad.json         ← [ETAPA 4] Tradução em JSON
    ├── asr_trad.srt          ← [ETAPA 4] Legendas traduzidas
    ├── segments.csv          ← [ETAPA 6] Info dos segmentos TTS
    ├── seg_0001.wav          ← [ETAPA 6] Segmento 1 TTS
    ├── seg_0002.wav          ← [ETAPA 6] Segmento 2 TTS
    ├── seg_XXXX.wav          ← [ETAPA 6] ... (um por segmento)
    ├── seg_0001_xf.wav       ← [ETAPA 6.1] Com fade (se --fade > 0)
    ├── seg_0001_xf_fit.wav   ← [ETAPA 7] Sincronizado (se sync ≠ none)
    ├── sil_0001.wav          ← [ETAPA 8] Silêncios (se --preserve-gaps)
    ├── list.txt              ← [ETAPA 8] Lista para concatenação
    ├── dub_raw.wav           ← [ETAPA 8] Áudio concatenado
    ├── dub_final.wav         ← [ETAPA 9] Áudio pós-processado
    └── logs.json             ← [FINAL] Logs completos + métricas
```

---

## 🔍 Detalhamento por Etapa

### ETAPA 1: Validação
**Arquivos:** Nenhum (apenas checks)
- Verifica se ffmpeg existe
- Verifica se vídeo de entrada existe

---

### ETAPA 2: Extração de Áudio
**Comando:** `ffmpeg -i video.mp4 -vn -ac 1 -ar 48000 audio_src.wav`

**Arquivos criados:**
```
dub_work/audio_src.wav   ← Áudio mono, 48kHz, PCM
```

**Como verificar:**
```bash
dir dub_work\audio_src.wav
```

---

### ETAPA 3: Transcrição (Whisper)
**Biblioteca:** faster-whisper

**Arquivos criados:**
```
dub_work/asr.json        ← Transcrição completa em JSON
dub_work/asr.srt         ← Legendas formato SRT
```

**Conteúdo esperado asr.json:**
```json
{
  "language": "en",
  "segments": [
    {"start": 0.0, "end": 3.5, "text": "Hello world"},
    {"start": 3.5, "end": 7.2, "text": "This is a test"}
  ]
}
```

**Como verificar:**
```bash
dir dub_work\asr.json
dir dub_work\asr.srt
type dub_work\asr.json
```

---

### ETAPA 4: Tradução (M2M100)
**Biblioteca:** transformers

**Arquivos criados:**
```
dub_work/asr_trad.json   ← Tradução em JSON
dub_work/asr_trad.srt    ← Legendas traduzidas
```

**Conteúdo esperado asr_trad.json:**
```json
{
  "language": "pt",
  "segments": [
    {
      "start": 0.0,
      "end": 3.5,
      "text": "Hello world",
      "text_trad": "Olá mundo",
      "original_wps": 2.5,
      "trad_estimated_dur": 1.2,
      "compression_ratio": 0.85
    }
  ]
}
```

**Como verificar:**
```bash
dir dub_work\asr_trad.json
dir dub_work\asr_trad.srt
type dub_work\asr_trad.json
```

---

### ETAPA 5: Split (Inteligente)
**Arquivos:** Nenhum (modifica dados em memória)
- Quebra segmentos longos em partes menores
- Resultado só é visível na próxima etapa

---

### ETAPA 6: TTS (Text-to-Speech)
**Biblioteca:** Bark ou Coqui TTS

**Arquivos criados:**
```
dub_work/segments.csv    ← Metadados de cada segmento
dub_work/seg_0001.wav    ← Áudio do segmento 1
dub_work/seg_0002.wav    ← Áudio do segmento 2
...
dub_work/seg_NNNN.wav    ← Áudio do segmento N
```

**Quantidade:** Um .wav por segmento traduzido (pode ser 50-200 arquivos)

**Conteúdo esperado segments.csv:**
```csv
idx,t_in,t_out,texto_trad,file,estimated_dur,actual_dur,compression_ratio
1,0.0,2.5,"Olá mundo",seg_0001.wav,1.234,1.189,0.85
2,2.5,5.0,"Vamos criar função",seg_0002.wav,2.100,2.050,0.90
```

**Como verificar:**
```bash
dir dub_work\seg_*.wav
dir dub_work\segments.csv
type dub_work\segments.csv
```

---

### ETAPA 6.1: Fade (Opcional)
**Quando:** Se `--fade > 0`

**Arquivos criados:**
```
dub_work/seg_0001_xf.wav    ← Segmento 1 com fade
dub_work/seg_0002_xf.wav    ← Segmento 2 com fade
...
```

**Como verificar:**
```bash
dir dub_work\seg_*_xf.wav
```

---

### ETAPA 7: Sincronização
**Quando:** Se `--sync` ≠ none

**Arquivos criados:**
```
dub_work/seg_0001_xf_fit.wav    ← Se sync=fit (ou _pad, _smart)
dub_work/seg_0002_xf_fit.wav
...
```

**Nomes variam:**
- `_fit.wav` se `--sync fit`
- `_pad.wav` se `--sync pad`
- `_fit.wav` se `--sync smart` ou `elastic` (usa fit internamente)

**Como verificar:**
```bash
dir dub_work\seg_*_fit.wav
dir dub_work\seg_*_pad.wav
```

---

### ETAPA 8: Concatenação
**Arquivos criados:**

```
dub_work/list.txt        ← Lista de arquivos para concat
dub_work/sil_0001.wav    ← Silêncios (se --preserve-gaps)
dub_work/sil_0002.wav
dub_work/dub_raw.wav     ← ÁUDIO CONCATENADO (importante!)
```

**Conteúdo esperado list.txt:**
```
file 'seg_0001_xf_fit.wav'
file 'sil_0001.wav'
file 'seg_0002_xf_fit.wav'
file 'sil_0002.wav'
...
```

**Como verificar:**
```bash
dir dub_work\list.txt
dir dub_work\dub_raw.wav
type dub_work\list.txt
```

---

### ETAPA 9: Pós-Processamento
**Arquivos criados:**
```
dub_work/dub_final.wav   ← ÁUDIO FINAL processado
```

**Processamento aplicado:**
- Normalização de volume (loudnorm)
- Redução de ruído (afftdn)
- Equalização (equalizer)

**Como verificar:**
```bash
dir dub_work\dub_final.wav
```

---

### ETAPA 10: Mux (Vídeo + Áudio)
**Arquivos criados:**
```
dublado/ccode-dia15.mp4  ← VÍDEO FINAL DUBLADO
```

**Comando:** `ffmpeg -i video.mp4 -i dub_final.wav -c:v copy -c:a aac output.mp4`

**Como verificar:**
```bash
dir dublado\ccode-dia15.mp4
```

---

### FINAL: Logs
**Arquivos criados:**
```
dub_work/logs.json       ← Logs completos com métricas
```

**Conteúdo:**
```json
{
  "input_video": "C:\\...\\ccode-dia15.mp4",
  "output_video": "C:\\...\\dublado\\ccode-dia15.mp4",
  "asr_json": "...",
  "sync_metrics": {
    "total_segments": 45,
    "avg_offset": -0.123,
    "max_offset": 0.847
  }
}
```

---

## ✅ Checklist de Verificação

Para diagnosticar onde o processo parou, verifique na ordem:

```bash
# ETAPA 2
dir dub_work\audio_src.wav

# ETAPA 3
dir dub_work\asr.json
dir dub_work\asr.srt

# ETAPA 4
dir dub_work\asr_trad.json
dir dub_work\asr_trad.srt

# ETAPA 6
dir dub_work\segments.csv
dir dub_work\seg_*.wav

# ETAPA 8
dir dub_work\dub_raw.wav

# ETAPA 9
dir dub_work\dub_final.wav

# ETAPA 10 (FINAL)
dir dublado\ccode-dia15.mp4
```

---

## 🐛 Diagnóstico Rápido

Execute:
```bash
dir dub_work
```

**Cenários:**

### Só tem `audio_src.wav`
→ Processo travou na **ETAPA 3 (Transcrição)**

### Tem `audio_src.wav` e `asr.json`/`asr.srt`
→ Processo travou na **ETAPA 4 (Tradução)**

### Tem até `asr_trad.json`/`asr_trad.srt`
→ Processo travou na **ETAPA 6 (TTS)**

### Tem `seg_*.wav` mas não tem `dub_raw.wav`
→ Processo travou na **ETAPA 8 (Concat)**

### Tem `dub_raw.wav` mas não tem `dub_final.wav`
→ Processo travou na **ETAPA 9 (Pós-processo)**

### Tem `dub_final.wav` mas vídeo não está em `dublado/`
→ Processo travou na **ETAPA 10 (Mux)**

---

## 🔍 Script de Diagnóstico

Execute este comando para ver status:
```bash
echo === DIAGNOSTICO ===
echo [ETAPA 2] Audio extraido:
if exist dub_work\audio_src.wav (echo OK) else (echo FALTANDO)
echo [ETAPA 3] Transcricao:
if exist dub_work\asr.json (echo OK) else (echo FALTANDO)
echo [ETAPA 4] Traducao:
if exist dub_work\asr_trad.json (echo OK) else (echo FALTANDO)
echo [ETAPA 6] TTS:
if exist dub_work\seg_0001.wav (echo OK) else (echo FALTANDO)
echo [ETAPA 8] Concat:
if exist dub_work\dub_raw.wav (echo OK) else (echo FALTANDO)
echo [ETAPA 9] Pos-processo:
if exist dub_work\dub_final.wav (echo OK) else (echo FALTANDO)
echo [ETAPA 10] Video final:
if exist dublado\ccode-dia15.mp4 (echo OK) else (echo FALTANDO)
```

---

## 📊 Tamanhos Esperados (vídeo de 7 min)

```
audio_src.wav      ~40 MB   (WAV 48kHz mono)
asr.json           ~5-10 KB
asr_trad.json      ~10-20 KB
seg_0001.wav       ~100-500 KB cada
segments.csv       ~10-50 KB
dub_raw.wav        ~40-60 MB
dub_final.wav      ~40-60 MB
ccode-dia15.mp4    ~140 MB (vídeo + áudio AAC)
```

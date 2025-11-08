# Como Usar o Dublar - Guia Rápido

## Uso Mais Simples (Padrões)

```batch
dublar video.mp4
```

**Isso irá automaticamente:**
- ✅ Dublar de **inglês** para **português**
- ✅ Usar **Bark TTS** (melhor qualidade)
- ✅ Voz: `v2/pt_speaker_1` (português)
- ✅ Sincronização **smart** (automática)
- ✅ Gerar: `video_dublado.mp4`
- ✅ Usar **GPU** automaticamente (se disponível)

---

## Personalizar Parâmetros

### Mudar Idiomas

```batch
# Inglês → Espanhol
dublar video.mp4 --src en --tgt es

# Português → Inglês
dublar video.mp4 --src pt --tgt en

# Francês → Português
dublar video.mp4 --src fr --tgt pt
```

### Mudar Motor TTS

```batch
# Coqui (mais rápido, menos VRAM)
dublar video.mp4 --tts coqui

# Bark (melhor qualidade, usa mais VRAM) - PADRÃO
dublar video.mp4 --tts bark
```

### Mudar Voz (Bark apenas)

```batch
# Voz masculina inglês
dublar video.mp4 --voice v2/en_speaker_6

# Voz feminina inglês
dublar video.mp4 --voice v2/en_speaker_9

# Voz portuguesa - PADRÃO
dublar video.mp4 --voice v2/pt_speaker_1
```

### Mudar Sincronização

```batch
# Smart (automático) - PADRÃO
dublar video.mp4 --sync smart

# Fit (ajustar duração exata)
dublar video.mp4 --sync fit

# Pad (adicionar silêncio)
dublar video.mp4 --sync pad

# None (sem ajuste)
dublar video.mp4 --sync none
```

### Arquivo de Saída Customizado

```batch
dublar video.mp4 --out meu_video_dublado.mp4
```

---

## Exemplos Práticos

### 1. Uso Padrão (EN→PT, Bark)
```batch
dublar ccode-dia15.mp4
```
Resultado: `video_dublado.mp4`

### 2. Inglês → Espanhol com Coqui
```batch
dublar ccode-dia15.mp4 --src en --tgt es --tts coqui --out video_espanhol.mp4
```

### 3. Português → Inglês com voz específica
```batch
dublar nei.mp4 --src pt --tgt en --voice v2/en_speaker_6 --out nei_english.mp4
```

### 4. Sincronização Perfeita
```batch
dublar video.mp4 --sync fit --tolerance 0.0 --maxstretch 1.5
```

### 5. Processar com Caminho Completo
```batch
dublar "C:\Videos\meu_video.mp4" --out "C:\Videos\dublado.mp4"
```

---

## Saída do Script

Quando você executa `dublar video.mp4`, verá:

```
========================================
   DUBLAR - Pipeline de Dublagem GPU
========================================

[CONFIG] Configuracao da Dublagem:
  Video........: C:\Users\...\video.mp4
  Idioma origem: en (en=ingles, pt=portugues, es=espanhol, etc.)
  Idioma alvo..: pt
  Motor TTS....: bark (bark=melhor qualidade, coqui=mais rapido)
  Voz..........: v2/pt_speaker_1
  Sincronizacao: smart (smart=automatico, fit=ajustar, pad=preencher)
  Tolerancia...: 0.0
  Max stretch..: 2.0
  Arquivo saida: video_dublado.mp4

[VENV] Ativando ambiente virtual...
[INFO] Python:
Python 3.13.5

[INFO] Verificando GPU...
GPU: NVIDIA GeForce RTX 4070 Laptop GPU

========================================
   Iniciando Pipeline de Dublagem
========================================

[EXEC] python dublar.py --in "video.mp4" --src en --tgt pt --tts bark ...

=== ETAPA 1: Entrada/cheques ===
=== ETAPA 2: Extração de áudio ===
=== ETAPA 3: Transcrição (Whisper) ===
[GPU] Whisper usando: CUDA
[GPU] GPU: NVIDIA GeForce RTX 4070 Laptop GPU
[GPU] VRAM disponível: 8.0 GB
...
```

---

## Parâmetros Disponíveis

| Parâmetro | Valores | Padrão | Descrição |
|-----------|---------|--------|-----------|
| `--src` | en, pt, es, fr, de, it, ja, ko, zh, etc. | `en` | Idioma do vídeo original |
| `--tgt` | en, pt, es, fr, de, it, ja, ko, zh, etc. | `pt` | Idioma da dublagem |
| `--tts` | `bark`, `coqui` | `bark` | Motor de síntese de voz |
| `--voice` | String (modelo TTS) | `v2/pt_speaker_1` | Voz específica (Bark) |
| `--sync` | `none`, `fit`, `pad`, `smart` | `smart` | Modo de sincronização |
| `--tolerance` | 0.0 - 1.0 | `0.0` | Tolerância de duração |
| `--maxstretch` | 1.0 - 3.0 | `2.0` | Máximo alongamento |
| `--out` | Nome do arquivo | `video_dublado.mp4` | Arquivo de saída |

---

## Códigos de Idioma

### Mais Comuns:
- `en` - Inglês
- `pt` - Português
- `es` - Espanhol
- `fr` - Francês
- `de` - Alemão
- `it` - Italiano
- `ja` - Japonês
- `ko` - Coreano
- `zh` - Chinês
- `ru` - Russo
- `ar` - Árabe

---

## Vozes do Bark

### Português:
- `v2/pt_speaker_0` até `v2/pt_speaker_9`

### Inglês:
- `v2/en_speaker_0` até `v2/en_speaker_9`

### Espanhol:
- `v2/es_speaker_0` até `v2/es_speaker_9`

### Outros idiomas:
- `v2/fr_speaker_X` (Francês)
- `v2/de_speaker_X` (Alemão)
- `v2/it_speaker_X` (Italiano)

---

## Dicas de Uso

### 1. Teste com Vídeo Curto
Sempre teste com um vídeo de 1-2 minutos antes de processar vídeos longos.

### 2. Escolha o TTS Certo
- **Bark**: Melhor qualidade, mais lento (~3x tempo real)
- **Coqui**: Mais rápido, boa qualidade (~1x tempo real)

### 3. Monitore a GPU
Em outro terminal:
```batch
nvidia-smi -l 1
```

### 4. Sincronização Smart
Use `--sync smart` para resultados equilibrados. Ajuste `tolerance` e `maxstretch` se necessário.

### 5. VRAM Insuficiente?
Se GPU ficar sem memória:
- Use `--tts coqui` (usa menos VRAM)
- Ou feche outros programas que usam GPU

---

## Solução de Problemas

### Script não executa, só mostra exemplos
Certifique-se de passar o nome do vídeo:
```batch
dublar video.mp4
```

### "Arquivo não encontrado"
Use caminho completo ou navegue até a pasta:
```batch
cd C:\Users\neima\projetosCC\voz_teste
dublar video.mp4
```

### "Python não encontrado"
O venv não foi ativado. Execute manualmente:
```batch
call venv\Scripts\activate.bat
python dublar.py --in video.mp4 --src en --tgt pt --tts bark
```

### GPU não está sendo usada
Verifique PyTorch CUDA:
```batch
python -c "import torch; print(torch.cuda.is_available())"
```
Se retornar `False`, reinstale PyTorch com CUDA (veja `INSTALACAO_GPU.md`)

---

## Comparação de Performance

### Vídeo de 10 minutos:

| Componente | CPU | GPU (RTX 4070) |
|------------|-----|----------------|
| Whisper | ~6 min | ~2 min |
| M2M100 | ~1 min | ~30s |
| Bark | ~60 min | ~20 min |
| **Total** | **~67 min** | **~22 min** |

**Ganho com GPU: ~3x mais rápido!**

---

## Arquivos Gerados

Após a execução, você terá:

```
voz_teste/
├── video_dublado.mp4          # Vídeo final dublado
└── dub_work/                  # Pasta de trabalho
    ├── audio_src.wav          # Áudio original extraído
    ├── asr.json               # Transcrição JSON
    ├── asr.srt                # Transcrição SRT
    ├── asr_trad.json          # Tradução JSON
    ├── asr_trad.srt           # Tradução SRT
    ├── segments.csv           # Segmentos de áudio
    ├── seg_0001.wav           # Áudio TTS segmento 1
    ├── seg_0002.wav           # Áudio TTS segmento 2
    ├── ...
    ├── dub_raw.wav            # Áudio dublado concatenado
    ├── dub_final.wav          # Áudio dublado processado
    └── logs.json              # Log completo da execução
```

---

## Referências Rápidas

- **INSTALACAO_GPU.md**: Instalação completa do CUDA/GPU
- **README_BAT.md**: Documentação detalhada dos scripts .bat
- **test_gpu.py**: Validar suporte GPU
- **dublar.py**: Script Python principal

---

**Criado em**: 2025-10-08
**Versão**: 1.0
**Uso mais simples**: `dublar video.mp4` (padrões: en→pt, bark, smart)

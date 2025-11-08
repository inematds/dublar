# Pipeline de Dublagem v2.0 - Sincronização Melhorada

## 🎯 O que há de novo?

Esta versão inclui **melhorias significativas na sincronização** entre tradução e dublagem:

### ✨ Novas Funcionalidades

1. **VAD (Voice Activity Detection)** - Detecta pausas naturais no áudio original
2. **Estimador de Duração pré-TTS** - Prevê duração antes de gerar áudio
3. **Análise de Densidade Linguística** - Considera expansão/contração entre idiomas
4. **Modo Elastic Sync** - Redistribui tempo entre segmentos adjacentes
5. **Métricas de Qualidade** - Dashboard com estatísticas de sincronização

---

## 📦 Instalação

### 1. Instalar dependências Python

```bash
pip install -r requirements.txt
```

### 2. Instalar FFmpeg

**Windows:**
- Baixe em: https://ffmpeg.org/download.html
- Adicione ao PATH do sistema

**Linux:**
```bash
sudo apt install ffmpeg
```

---

## 🚀 Uso Básico

### Exemplo simples (Inglês → Português)

```bash
python dublar_sync_v2.py --in video.mp4 --src en --tgt pt --sync smart
```

### Com todas as melhorias ativadas

```bash
python dublar_sync_v2.py \
  --in meu_video.mp4 \
  --src en \
  --tgt pt \
  --tts bark \
  --sync elastic \
  --enable-vad \
  --preserve-gaps \
  --tolerance 0.12 \
  --maxstretch 1.4
```

---

## 🎛️ Parâmetros

### Obrigatórios

| Parâmetro | Descrição | Exemplo |
|-----------|-----------|---------|
| `--in` | Vídeo de entrada | `--in video.mp4` |
| `--src` | Idioma original | `--src en` |
| `--tgt` | Idioma alvo | `--tgt pt` |

### Sincronização (NOVO!)

| Parâmetro | Descrição | Valores | Padrão |
|-----------|-----------|---------|--------|
| `--sync` | Modo de sincronização | `none`, `fit`, `pad`, `smart`, **`elastic`** | `smart` |
| `--enable-vad` | Ativa detecção de pausas naturais | flag | desativado |
| `--tolerance` | Tolerância de tempo (%) | 0.0-1.0 | `0.15` (15%) |
| `--maxstretch` | Máxima compressão/expansão | 1.0-2.0 | `1.35` (35%) |

### TTS

| Parâmetro | Descrição | Valores | Padrão |
|-----------|-----------|---------|--------|
| `--tts` | Engine de síntese de voz | `bark`, `coqui` | `bark` |
| `--voice` | Preset de voz | `v2/pt_speaker_0` | None |
| `--texttemp` | Temperatura de texto (Bark) | 0.0-1.0 | `0.6` |
| `--wavetemp` | Temperatura de onda (Bark) | 0.0-1.0 | `0.6` |

### Outros

| Parâmetro | Descrição | Padrão |
|-----------|-----------|--------|
| `--out` | Vídeo de saída | `dublado/{nome_original}` |
| `--maxdur` | Duração máxima por segmento (s) | `10.0` |
| `--preserve-gaps` | Preserva silêncios entre falas | desativado |
| `--gap-min` | Mínimo para inserir silêncio (s) | `0.20` |
| `--fade` | Duração do fade in/out (s) | `0.02` |
| `--rate` | Taxa de amostragem final | `24000` |
| `--bitrate` | Bitrate do áudio AAC | `192k` |

---

## 🔧 Modos de Sincronização

### `none` - Sem ajuste
- Gera áudio sem modificar velocidade
- Pode ficar dessincronizado

### `fit` - Ajuste por velocidade
- Acelera/desacelera para caber no tempo original
- Pode distorcer voz se diferença for grande

### `pad` - Ajuste por silêncio
- Adiciona silêncio ou corta excesso
- Mantém velocidade natural da voz

### `smart` ⭐ (Recomendado)
- Combina `fit` e `pad` inteligentemente
- Usa `pad` se diferença < tolerância
- Usa `fit` se diferença > tolerância

### `elastic` 🆕 (Avançado)
- **Redistribui tempo entre segmentos adjacentes**
- Compensa deslocamentos acumulados
- Melhor para diálogos rápidos e densos
- **Recomendado quando `--enable-vad` está ativo**

---

## 📊 Entendendo as Métricas

Após a execução, o sistema mostra métricas de qualidade:

```
=== MÉTRICAS DE SINCRONIZAÇÃO ===
  Total de segmentos: 45
  Offset médio: -0.123s           ← Atraso/adiantamento médio
  Offset máximo: 0.847s            ← Maior deslocamento
  Desvio padrão: 0.234s            ← Consistência (menor = melhor)
  Ratio de velocidade médio: 1.12x ← Compressão média
  Segmentos fora da tolerância: 3  ← Segmentos problemáticos
  Segmentos comprimidos (>1.1x): 8
  Segmentos expandidos (<0.9x): 2
```

**Interpretação:**
- **Offset médio próximo de 0** = boa sincronização global
- **Desvio padrão baixo** = sincronização consistente
- **Poucos segmentos fora da tolerância** = qualidade alta

---

## 📈 Densidade Linguística

O sistema agora considera que diferentes idiomas têm comprimentos diferentes:

| Idioma | Fator de Expansão (vs. Inglês) |
|--------|-------------------------------|
| Português | +20% |
| Espanhol | +15% |
| Francês | +18% |
| Alemão | -5% |
| Japonês | -20% |
| Chinês | -25% |

Isso permite **estimativas mais precisas** de duração antes de gerar o áudio.

---

## 🎤 VAD - Voice Activity Detection

Quando `--enable-vad` está ativo:

1. Analisa o áudio original
2. Detecta pausas naturais (respirações, silêncios dramáticos)
3. **Quebra segmentos nessas pausas** em vez de apenas por pontuação
4. Resultado: sincronização mais natural e orgânica

**Requer:** `librosa` instalado (`pip install librosa`)

---

## 🎬 Exemplos de Uso

### Dublagem rápida (padrões otimizados)
```bash
python dublar_sync_v2.py --in filme.mp4 --src en --tgt pt
```

### Máxima qualidade de sincronização
```bash
python dublar_sync_v2.py \
  --in serie_ep01.mp4 \
  --src en \
  --tgt pt \
  --sync elastic \
  --enable-vad \
  --tolerance 0.10 \
  --maxstretch 1.3 \
  --preserve-gaps
```

### Teste com voz específica (Bark)
```bash
python dublar_sync_v2.py \
  --in podcast.mp4 \
  --src en \
  --tgt pt \
  --tts bark \
  --voice v2/pt_speaker_3 \
  --texttemp 0.7 \
  --wavetemp 0.7
```

### Usando Coqui TTS
```bash
python dublar_sync_v2.py \
  --in tutorial.mp4 \
  --src en \
  --tgt pt \
  --tts coqui \
  --sync smart
```

---

## 📁 Arquivos Gerados

```
projeto/
├── dublado/
│   └── video.mp4              # Vídeo final dublado
├── dub_work/
│   ├── asr.json               # Transcrição original
│   ├── asr.srt                # Legendas originais
│   ├── asr_trad.json          # Tradução
│   ├── asr_trad.srt           # Legendas traduzidas
│   ├── segments.csv           # Info dos segmentos (COM MÉTRICAS!)
│   ├── seg_0001.wav           # Segmentos de áudio
│   ├── ...
│   ├── dub_final.wav          # Áudio processado final
│   └── logs.json              # Logs completos + MÉTRICAS
```

### 🆕 Novo formato do `segments.csv`

Agora inclui colunas extras para análise:

```csv
idx,t_in,t_out,texto_trad,file,estimated_dur,actual_dur
1,0.0,2.5,"Olá, mundo!",seg_0001.wav,1.234,1.189
```

- `estimated_dur`: duração estimada pré-TTS
- `actual_dur`: duração real gerada

---

## 🐛 Troubleshooting

### VAD não funciona
```bash
pip install librosa soundfile
```

### Erro "ffmpeg not found"
- Instale FFmpeg e adicione ao PATH

### Sincronização ruim mesmo com `elastic`
- Tente aumentar `--maxstretch` para 1.5
- Reduza `--tolerance` para 0.08
- Ative `--enable-vad`

### Voz muito rápida/lenta
- Ajuste `--maxstretch` (padrão 1.35)
- Use modo `smart` ou `elastic`

### Áudio cortado ou com pulos
- Ative `--preserve-gaps`
- Reduza `--gap-min` para 0.1

---

## 🔬 Comparação de Modos

| Situação | Modo Recomendado |
|----------|------------------|
| Narração lenta, poucas falas | `pad` |
| Diálogo rápido, muitas falas | `elastic` + `--enable-vad` |
| Documentário, ritmo moderado | `smart` |
| Teste rápido | `none` |
| Podcast, entrevista | `smart` ou `elastic` |

---

## 📝 Notas Importantes

1. **Primera execução é lenta** - modelos são baixados automaticamente
2. **GPU acelera muito** - especialmente Whisper e Bark
3. **Arquivos grandes** - considere dividir vídeos longos (>1h)
4. **Idiomas suportados**:
   - Whisper: ~100 idiomas
   - M2M100: ~100 idiomas
   - Bark: Português, Inglês, Espanhol, Francês, etc.

---

## 🤝 Contribuições

Sugestões de melhorias:
- Abra uma issue ou PR
- Reporte bugs com logs completos
- Compartilhe resultados e casos de uso

---

## 📄 Licença

Código fornecido como está. Use responsavelmente.

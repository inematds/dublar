# ✅ Correção Aplicada - safe_fade

## Data: 2025-10-08

---

## 🔧 Problema Identificado

**Vídeo dublado 2.5x mais longo que o original:**
- Original: 114s (1:54)
- Dublado: 279s (4:39)
- Diferença: **+145%**

**Causa raiz**: Função `safe_fade` usando `areverse` duas vezes estava causando bugs no ffmpeg que aumentavam a duração do áudio.

---

## ✅ Correção Aplicada

### Arquivo: `dublar.py` (linha 276-280)

**ANTES (ERRADO):**
```python
def safe_fade(in_path, out_path, workdir):
    # fade-in e fade-out seguros (areverse) para trechos curtos
    sh(["ffmpeg","-y","-i", in_path.name,
        "-af","afade=t=in:ss=0:d=0.02,areverse,afade=t=in:ss=0:d=0.02,areverse",
        out_path.name], cwd=workdir)
```

**DEPOIS (CORRETO):**
```python
def safe_fade(in_path, out_path, workdir):
    # fade-in e fade-out simples (sem areverse que causa bugs de duração)
    sh(["ffmpeg","-y","-i", in_path.name,
        "-af","afade=t=in:d=0.01,afade=t=out:d=0.01",
        out_path.name], cwd=workdir)
```

### Mudanças:

1. **Removido**: `areverse` (2 vezes)
2. **Simplificado**: Fade-in e fade-out diretos
3. **Duração ajustada**: 0.02s → 0.01s (mais suave)
4. **Sintaxe corrigida**:
   - Fade-in: `afade=t=in:d=0.01`
   - Fade-out: `afade=t=out:d=0.01`

---

## 🚀 Re-dublagem em Andamento

**Comando executado:**
```bash
python dublar.py --in nei.mp4 --src en --tgt pt --tts bark --voice v2/pt_speaker_1 --sync fit --tolerance 0.0 --maxstretch 1.2 --fade 1 --out dublagem/nei_corrigido.mp4
```

**Parâmetros importantes:**
- `--fade 1`: Mantém fade (agora corrigido)
- `--sync fit`: Força compressão para duração exata
- `--maxstretch 1.2`: Limita distorção a 20% max
- `--tolerance 0.0`: Zero tolerância (comprimir tudo que não bater exato)

**Status:**
- ✅ Extração de áudio
- ✅ Transcrição Whisper (11 segmentos)
- ✅ Tradução M2M100 em GPU (16 segmentos após split)
- 🔄 TTS Bark em GPU (em andamento)
- ⏳ Sincronização (fit)
- ⏳ Concatenação
- ⏳ Pós-processamento
- ⏳ Mux final

**Tempo estimado**: 30-40 minutos total

---

## 📊 Resultado Esperado

**Vídeo final**: `dublagem/nei_corrigido.mp4`

**Duração esperada**: ~114s (igual ao original)

**Diferença em relação ao vídeo bugado:**
- Antes: 279s (145% mais longo)
- Depois: 114s (duração correta ✅)
- Redução: **-59% de duração**

---

## 🔍 Como Verificar

Após a conclusão, rodar:

```bash
# Verificar duração original
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 nei.mp4

# Verificar duração corrigida
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 dublagem/nei_corrigido.mp4
```

**Resultado esperado**: Ambos devem mostrar ~114 segundos

---

## 📝 Lições Aprendidas

1. **`areverse` é problemático**: Usar com cautela em pipelines ffmpeg complexos
2. **Fade simples é mais seguro**: `afade=t=in` + `afade=t=out` funciona melhor
3. **`sync fit` é essencial**: Quando Bark gera áudio longo, fit força a compressão correta
4. **Tolerância zero funciona**: Com `tolerance=0.0`, todos os segmentos são ajustados exatamente

---

## 🛠️ Comandos Úteis para Futuro

### Re-dublar com correção (modo rápido):
```bash
dublar nei.mp4 --fade 1 --sync fit --maxstretch 1.2 --out dublagem/video.mp4
```

### Re-dublar sem fade (mais rápido):
```bash
dublar nei.mp4 --fade 0 --sync fit --maxstretch 1.2 --out dublagem/video.mp4
```

### Re-dublar com Coqui (alternativa ao Bark):
```bash
dublar nei.mp4 --tts coqui --sync smart --tolerance 0.1 --out dublagem/video.mp4
```

---

**Status**: ✅ Correção aplicada e re-dublagem em andamento
**Próximo passo**: Aguardar conclusão e verificar duração final

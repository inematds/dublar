# Guia de Instalação GPU - Dublar Pipeline

## Status da Instalação

✅ **INSTALAÇÃO CONCLUÍDA COM SUCESSO!**

Todos os componentes do pipeline dublar estão configurados para usar GPU NVIDIA.

---

## Hardware Detectado

- **GPU**: NVIDIA GeForce RTX 4070 Laptop GPU
- **VRAM**: 8 GB
- **Driver NVIDIA**: 556.29
- **CUDA Toolkit (Driver)**: 12.5

---

## Software Instalado

### 1. PyTorch com CUDA
- **Versão**: 2.6.0+cu124
- **CUDA Runtime**: 12.4
- **cuDNN**: 9.1.0
- **Status**: ✅ GPU Ativa

### 2. faster-whisper (Whisper ASR)
- **Versão**: 1.2.0
- **Backend**: CTranslate2 4.6.0
- **Compute Type**: float16 (GPU) / int8 (CPU)
- **Status**: ✅ GPU Ativa

### 3. Transformers (M2M100 Tradução)
- **Modelo**: facebook/m2m100_418M
- **Device**: cuda:0
- **Status**: ✅ GPU Ativa

### 4. Bark TTS
- **Versão**: 0.0.1a0 (suno-ai)
- **Dependências**: scipy, encodec, boto3
- **Status**: ✅ GPU Ativa

### 5. Componentes Auxiliares
- numpy 2.2.6
- scipy 1.16.2
- tqdm 4.67.1
- ffmpeg (sistema)

---

## Comandos de Instalação Executados

```bash
# 1. Desinstalar PyTorch CPU
pip uninstall -y torch torchvision torchaudio

# 2. Instalar PyTorch com CUDA 12.4
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# 3. Atualizar faster-whisper
pip install --upgrade faster-whisper

# 4. Instalar Bark TTS
pip install git+https://github.com/suno-ai/bark.git
```

**IMPORTANTE**: Não foi necessário instalar CUDA Toolkit separadamente! O PyTorch já inclui todas as bibliotecas CUDA necessárias (cuDNN, cuBLAS, etc.).

---

## Modificações no Código

### `dublar.py` - Alterações para GPU

#### 1. Whisper (Transcrição)
```python
# Antes:
model = WhisperModel("medium", device="auto")

# Depois:
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"[GPU] Whisper usando: {device.upper()}")
model = WhisperModel("medium", device=device, compute_type="float16" if device == "cuda" else "int8")
```

#### 2. M2M100 (Tradução)
```python
# Antes:
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

# Depois:
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"[GPU] M2M100 usando: {device.upper()}")
model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(device)

# E na geração:
enc = {k: v.to(device) for k, v in enc.items()}
```

#### 3. Bark (TTS)
```python
# Adicionado no início da função:
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"[GPU] Bark usando: {device.upper()}")
if device == "cuda":
    os.environ['SUNO_USE_SMALL_MODELS'] = '0'  # Modelos grandes em GPU
    os.environ['SUNO_OFFLOAD_CPU'] = '0'       # Não fazer offload
```

---

## Como Usar

### Execução Normal

```bash
python dublar.py --in video.mp4 --src en --tgt pt --tts bark --voice v2/pt_speaker_1 --sync smart --tolerance 0.0 --maxstretch 2.0
```

### Logs Esperados

Você verá mensagens indicando uso de GPU:

```
=== ETAPA 3: Transcrição (Whisper) ===
[GPU] Whisper usando: CUDA
[GPU] GPU: NVIDIA GeForce RTX 4070 Laptop GPU
[GPU] VRAM disponível: 8.0 GB

=== ETAPA 4: Tradução (facebook/m2m100_418M) ===
[GPU] M2M100 usando: CUDA

=== ETAPA 6: TTS (Bark) ===
[GPU] Bark usando: CUDA
[GPU] Modelos Bark carregados em GPU
```

### Teste de GPU

Para validar a instalação GPU:

```bash
python test_gpu.py
```

Resultado esperado:
```
======================================================================
  RESUMO DOS TESTES
======================================================================
  PyTorch             : ✓ PASSOU
  CTranslate2         : ✓ PASSOU
  faster-whisper      : ✓ PASSOU
  Transformers        : ✓ PASSOU
  Bark                : ✓ PASSOU
  Memória             : ✓ PASSOU

*** SUCESSO! Todos os componentes suportam GPU!
```

---

## Uso de VRAM (Estimado)

| Componente | VRAM | Tempo (10min vídeo) |
|------------|------|---------------------|
| Whisper medium | ~2 GB | ~2 min (GPU) vs ~6 min (CPU) |
| M2M100 418M | ~1.5 GB | ~30s (GPU) vs ~1 min (CPU) |
| Bark (completo) | ~3 GB | ~20 min (GPU) vs ~60 min (CPU) |
| **Total** | **~6.5 GB** | **~22 min** vs **~67 min** |

**Ganho de velocidade**: ~3x mais rápido com GPU!

---

## Solução de Problemas

### GPU não detectada

```bash
# Verificar CUDA
python -c "import torch; print(torch.cuda.is_available())"

# Se False, reinstalar PyTorch
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```

### Erro de VRAM insuficiente

```python
# Usar modelo Whisper menor:
model = WhisperModel("small", device="cuda")  # em vez de "medium"

# Ou processar em lotes menores (M2M100):
max_batch = 4  # reduzir de 8 para 4
```

### Bark lento mesmo em GPU

```bash
# Verificar se modelos grandes estão sendo usados
# No código dublar.py, confirmar:
os.environ['SUNO_USE_SMALL_MODELS'] = '0'  # 0 = modelos grandes (melhor qualidade)
os.environ['SUNO_OFFLOAD_CPU'] = '0'       # 0 = manter tudo em GPU
```

---

## Próximos Passos

1. **Testar com vídeo real**:
   ```bash
   python dublar.py --in seu_video.mp4 --src en --tgt pt --tts bark --sync smart
   ```

2. **Monitorar uso de GPU**:
   ```bash
   # Em outro terminal:
   nvidia-smi -l 1  # Atualiza a cada 1 segundo
   ```

3. **Ajustar parâmetros** conforme necessário:
   - `--maxdur`: Duração máxima de segmentos (padrão: 10s)
   - `--tolerance`: Tolerância de sincronização (padrão: 0.15)
   - `--maxstretch`: Máximo de alongamento de áudio (padrão: 1.35)

---

## Arquivos de Referência

- **dublar.py**: Pipeline principal (modificado para GPU)
- **test_gpu.py**: Script de validação GPU
- **FIX_CUDA.md**: Documentação anterior (CPU fallback)
- **README_TECH.md**: Documentação técnica geral

---

## Resumo

✅ PyTorch 2.6.0 + CUDA 12.4 instalado
✅ faster-whisper configurado para GPU
✅ Transformers usando GPU
✅ Bark TTS usando GPU
✅ Código dublar.py atualizado com logs
✅ Script de teste criado
✅ 8 GB VRAM suficiente para pipeline completo

**Tudo pronto para rodar o dublar em GPU!** 🚀

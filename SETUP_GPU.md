# Setup GPU - Passo a Passo

## ✅ O que você já tem:
- CUDA Toolkit instalado
- cuDNN v9.13 instalado em: `C:\Program Files\NVIDIA\CUDNN\v9.13\bin\13.0`
- Ambiente virtual Python configurado

## ❌ O que falta:
- PyTorch com suporte CUDA (atualmente está versão CPU)

---

## 🚀 INSTALAÇÃO SIMPLES (1 comando):

```bash
instalar_pytorch_gpu.bat
```

Isso vai:
1. Desinstalar PyTorch CPU
2. Instalar PyTorch CUDA
3. Testar GPU

**Tempo:** ~3-5 minutos

---

## 📋 Depois da instalação:

### Testar se GPU funciona:
```bash
ativar_gpu.bat
```

Deve mostrar:
```
CUDA disponível: True
GPU: NVIDIA GeForce [seu modelo]
```

### Dublar vídeo com GPU:
```bash
dublar.bat seu_video.mp4
```

O script **automaticamente**:
- ✅ Ativa ambiente virtual
- ✅ Adiciona cuDNN ao PATH
- ✅ Detecta e usa GPU se disponível
- ✅ Usa CPU se GPU não funcionar

---

## 🎯 Velocidade esperada:

### Vídeo de 7 minutos (~146 segmentos):

| Componente | CPU | GPU | Ganho |
|------------|-----|-----|-------|
| Whisper | ~7 min | ~2 min | **3.5x** |
| M2M100 | ~1 min | ~20s | **3x** |
| Bark TTS | ~19 min | ~4 min | **5x** |
| **TOTAL** | **~27 min** | **~6-7 min** | **4x** |

---

## 🔧 Se der erro:

### Erro: "CUDA disponível: False"
```bash
# Reinstale PyTorch GPU
instalar_pytorch_gpu.bat
```

### Erro: "Could not locate cudnn64_9.dll"
```bash
# O dublar.bat já adiciona automaticamente ao PATH
# Se ainda não funcionar, reinicie o computador
```

### Forçar CPU (se GPU der problema):
Edite `dublar_tech_v2.py` linha 12:
```python
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # Descomente esta linha
```

---

## ✅ CHECKLIST RÁPIDO:

- [ ] Instalei PyTorch GPU: `instalar_pytorch_gpu.bat`
- [ ] Testei GPU: `ativar_gpu.bat` → mostra "CUDA disponível: True"
- [ ] Dublei vídeo: `dublar.bat video.mp4`
- [ ] Vi mensagem "GPU detectada! Usando CUDA..."

---

## 📝 COMANDOS RESUMIDOS:

```bash
# 1. Instalar PyTorch GPU (apenas 1 vez)
instalar_pytorch_gpu.bat

# 2. Testar GPU (opcional)
ativar_gpu.bat

# 3. Dublar vídeo (GPU automática!)
dublar.bat seu_video.mp4

# 4. Continuar de onde parou (se der erro)
dublar.bat --continue seu_video.mp4
```

**Pronto! Agora é só rodar!** 🚀

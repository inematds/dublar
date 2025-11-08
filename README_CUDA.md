# Guia de Instalação do CUDA para Acelerar GPU

## ⚡ Por Que Instalar CUDA?

**Sem CUDA (CPU):**
- Vídeo de 15 min = ~30-45 min de processamento
- Funciona, mas lento

**Com CUDA (GPU):**
- Vídeo de 15 min = ~10-15 min de processamento
- **3x mais rápido!**

---

## 🎯 Instalação Guiada (Recomendada)

### Execute o script automático:

```bash
instalar_cuda.bat
```

O script irá:
1. ✅ Verificar se você tem GPU NVIDIA
2. ✅ Baixar CUDA Toolkit (ou guiar download manual)
3. ✅ Instalar CUDA
4. ✅ Configurar cuDNN
5. ✅ Reinstalar PyTorch com suporte GPU
6. ✅ Testar se funcionou

**Tempo total: 20-30 minutos**

---

## 📋 Instalação Manual (Detalhada)

Se preferir fazer manualmente ou se o script falhar:

### Passo 1: Verificar GPU NVIDIA

Abra o CMD e execute:
```bash
nvidia-smi
```

Deve mostrar sua placa NVIDIA. Se não aparecer:
- Instale drivers NVIDIA: https://www.nvidia.com/Download/index.aspx

---

### Passo 2: Baixar CUDA Toolkit 11.8

1. Acesse: https://developer.nvidia.com/cuda-11-8-0-download-archive

2. Selecione:
   - **Operating System:** Windows
   - **Architecture:** x86_64
   - **Version:** [sua versão do Windows]
   - **Installer Type:** exe (local) - **RECOMENDADO** (~3GB)

3. Baixe o arquivo `cuda_11.8.0_windows.exe`

---

### Passo 3: Instalar CUDA Toolkit

1. Execute o instalador baixado

2. Na tela de instalação, escolha:
   - **Express Installation** (Recomendado)
   - Ou **Custom** e marque:
     - ✅ CUDA Toolkit
     - ✅ CUDA Visual Studio Integration
     - ⬜ CUDA Samples (opcional)

3. Aguarde instalação (~10-15 min)

4. Verifique instalação:
```bash
nvcc --version
```

Deve mostrar: `Cuda compilation tools, release 11.8`

---

### Passo 4: Baixar cuDNN

1. Acesse: https://developer.nvidia.com/cudnn

2. Clique em **"Download cuDNN"**

3. **Faça login** (ou crie conta NVIDIA - grátis)

4. Baixe:
   - **cuDNN v8.9.x for CUDA 11.x**
   - Arquivo: `cudnn-windows-x86_64-8.x.x.xx_cuda11-archive.zip`

5. **Extraia o ZIP** para uma pasta temporária

---

### Passo 5: Instalar cuDNN

1. Abra a pasta extraída do cuDNN

2. Copie os arquivos para a pasta do CUDA:

**Estrutura do cuDNN extraído:**
```
cudnn-windows-x86_64-8.x.x/
  ├── bin/
  ├── include/
  └── lib/
```

**Copiar para CUDA (como ADMINISTRADOR):**

```
De: cudnn-windows-x86_64-8.x.x\bin\*.dll
Para: C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\bin\

De: cudnn-windows-x86_64-8.x.x\include\*.h
Para: C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\include\

De: cudnn-windows-x86_64-8.x.x\lib\x64\*.lib
Para: C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\lib\x64\
```

**Via CMD (como ADMINISTRADOR):**
```bash
xcopy "C:\caminho\para\cudnn\bin\*.dll" "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\bin\" /Y
xcopy "C:\caminho\para\cudnn\include\*.h" "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\include\" /Y
xcopy "C:\caminho\para\cudnn\lib\x64\*.lib" "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\lib\x64\" /Y
```

---

### Passo 6: Adicionar ao PATH do Windows (se necessário)

1. Pressione `Win + R`, digite `sysdm.cpl`, Enter

2. Aba **"Avançado"** → **"Variáveis de Ambiente"**

3. Em **"Variáveis do sistema"**, selecione **"Path"** → **"Editar"**

4. Adicione (se não existir):
   ```
   C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\bin
   C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\libnvvp
   ```

5. Clique **OK** em todas as janelas

6. **REINICIE o computador**

---

### Passo 7: Reinstalar PyTorch com CUDA

No seu ambiente virtual:

```bash
# Ativar ambiente
cd C:\Users\neima\projetosCC\voz_teste
venv\Scripts\activate

# Desinstalar PyTorch CPU
pip uninstall torch torchvision torchaudio

# Instalar PyTorch com CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

---

### Passo 8: Testar Instalação

```bash
python -c "import torch; print('CUDA disponível:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"
```

**Resultado esperado:**
```
CUDA disponível: True
GPU: NVIDIA GeForce RTX 3060 (ou seu modelo)
```

Se mostrar `False`, revise os passos ou execute `instalar_cuda.bat` novamente.

---

## 🧪 Testando com Dublagem

Execute:
```bash
dublar.bat ccode-dia15.mp4
```

Na etapa de transcrição, deve aparecer:
```
=== ETAPA 3: Transcrição (Whisper) ===
Tentando usar GPU (CUDA)...
✓ GPU carregada, testando...
✓ GPU funcionando!
```

**Se aparecer "GPU falhou"**, algo não foi instalado corretamente.

---

## 🔧 Troubleshooting

### Erro: "nvcc not found"
- Adicione ao PATH: `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\bin`
- Reinicie o computador

### Erro: "cudnn_ops64_9.dll not found"
- cuDNN não foi copiado corretamente
- Verifique se copiou os arquivos `.dll` para `CUDA\v11.8\bin\`

### PyTorch não detecta CUDA
```bash
# Reinstale PyTorch CUDA
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### "This application failed to start because no NVIDIA graphics driver is found"
- Instale/atualize drivers NVIDIA: https://www.nvidia.com/Download/index.aspx

---

## 📊 Comparação CPU vs GPU

| Operação | CPU | GPU (CUDA) | Speedup |
|----------|-----|------------|---------|
| Whisper (15 min vídeo) | ~30 min | ~8 min | **3.7x** |
| M2M100 (tradução) | ~2 min | ~1 min | **2x** |
| Bark TTS (15 min áudio) | ~90 min | ~30 min | **3x** |
| **TOTAL** | **~2h** | **~40 min** | **3x** |

---

## ✅ Checklist de Instalação

- [ ] GPU NVIDIA detectada (`nvidia-smi` funciona)
- [ ] CUDA Toolkit 11.8 instalado (`nvcc --version`)
- [ ] cuDNN 8.x copiado para pasta CUDA
- [ ] PATH do Windows atualizado
- [ ] Computador reiniciado
- [ ] PyTorch CUDA instalado (`pip list | grep torch`)
- [ ] Teste CUDA passou (`torch.cuda.is_available() = True`)
- [ ] Dublagem usa GPU (`✓ GPU funcionando!`)

---

## 🎯 Resumo

**Instalação Rápida (script automático):**
```bash
instalar_cuda.bat
```

**Instalação Manual:**
1. Baixar CUDA 11.8
2. Instalar CUDA
3. Baixar cuDNN 8.x
4. Copiar cuDNN para pasta CUDA
5. Reinstalar PyTorch com CUDA
6. Testar

**Tempo:** 20-30 minutos
**Benefício:** 3x mais rápido na dublagem
**Vale a pena?** Se você dubla 5+ vídeos/semana, SIM!

---

## 💡 Dica

Se a instalação parecer complexa, **use CPU!** O código já está configurado para funcionar perfeitamente em CPU. Só será mais lento, mas 100% funcional.

```bash
# Funciona sem CUDA, apenas mais lento
dublar.bat seu_video.mp4
```

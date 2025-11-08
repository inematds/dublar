# Scripts BAT - Dublar

Scripts Windows Batch para facilitar o uso do pipeline de dublagem.

---

## Arquivos Criados

### 1. `dublar.bat` (Principal)
Script completo que ativa o ambiente virtual e executa o dublar.py com parâmetros.

### 2. `dublar_global.bat` (Opcional)
Atalho global para usar `dublar` de qualquer pasta no Windows.

---

## Uso do `dublar.bat`

### Forma Mais Simples

```batch
dublar video.mp4
```

Isso irá:
- Dublar de **inglês (en)** para **português (pt)**
- Usar **Bark TTS** com voz `v2/pt_speaker_1`
- Sincronização **smart** (automática)
- Gerar `video_dublado.mp4`

### Com Parâmetros Personalizados

```batch
REM Mudar idiomas
dublar video.mp4 --src en --tgt es

REM Usar Coqui TTS em vez de Bark
dublar video.mp4 --tts coqui

REM Mudar voz do Bark
dublar video.mp4 --voice v2/en_speaker_6

REM Mudar sincronização
dublar video.mp4 --sync fit --tolerance 0.15 --maxstretch 1.5

REM Nome de arquivo de saída personalizado
dublar video.mp4 --out meu_video_dublado.mp4

REM Combinar vários parâmetros
dublar video.mp4 --src en --tgt pt --tts bark --voice v2/pt_speaker_1 --sync smart --out resultado.mp4
```

---

## Parâmetros Disponíveis

| Parâmetro | Valores | Padrão | Descrição |
|-----------|---------|--------|-----------|
| `--src` | en, pt, es, fr, de, etc. | `en` | Idioma do áudio original |
| `--tgt` | en, pt, es, fr, de, etc. | `pt` | Idioma da dublagem |
| `--tts` | `bark`, `coqui` | `bark` | Motor de síntese de voz |
| `--voice` | String (voz do TTS) | `v2/pt_speaker_1` | Voz específica (Bark) |
| `--sync` | `none`, `fit`, `pad`, `smart` | `smart` | Modo de sincronização |
| `--tolerance` | 0.0 - 1.0 | `0.0` | Tolerância de duração |
| `--maxstretch` | 1.0 - 3.0 | `2.0` | Máximo de alongamento |
| `--out` | Nome de arquivo | `video_dublado.mp4` | Arquivo de saída |

---

## Modos de Sincronização

### `none` - Sem sincronização
Áudio gerado sem ajuste de duração. Pode ficar dessincronizado.

### `fit` - Ajustar duração
Comprime ou alonga o áudio para caber exatamente no tempo original.

### `pad` - Adicionar silêncio
Adiciona silêncio no final se o áudio for mais curto.

### `smart` - Automático (Recomendado)
Combina `fit` e `pad` de forma inteligente:
- Se áudio gerado for muito curto → adiciona silêncio
- Se áudio gerado for muito longo → comprime

---

## Exemplos Práticos

### 1. Dublar vídeo do inglês para português (padrão)
```batch
dublar meu_video.mp4
```

### 2. Dublar do inglês para espanhol
```batch
dublar video.mp4 --src en --tgt es
```

### 3. Dublar vídeo em português para inglês com Coqui
```batch
dublar video_pt.mp4 --src pt --tgt en --tts coqui
```

### 4. Dublar com sincronização perfeita
```batch
dublar video.mp4 --sync fit --tolerance 0.0 --maxstretch 2.0
```

### 5. Dublar com voz específica do Bark
```batch
dublar video.mp4 --voice v2/en_speaker_6
```

### 6. Processar vídeo em outra pasta
```batch
dublar "C:\Videos\meu_video.mp4" --out "C:\Videos\dublado.mp4"
```

---

## Uso Global (Opcional)

Para usar `dublar` de qualquer pasta no Windows:

### Opção 1: Adicionar pasta ao PATH

1. Clique com botão direito em "Este Computador" → Propriedades
2. Configurações avançadas do sistema → Variáveis de ambiente
3. Em "Variáveis do sistema", encontre `Path` e clique em Editar
4. Clique em "Novo" e adicione:
   ```
   C:\Users\neima\projetosCC\voz_teste
   ```
5. Clique em OK em todas as janelas
6. Reinicie o terminal

Agora você pode usar:
```batch
dublar video.mp4
```
De qualquer pasta!

### Opção 2: Copiar dublar_global.bat para System32

```batch
REM Executar como Administrador
copy dublar_global.bat C:\Windows\System32\dublar.bat
```

Agora você pode usar `dublar` globalmente.

---

## O que o Script Faz

1. **Verifica arquivo de entrada**
   - Se não existir, mostra erro

2. **Processa parâmetros**
   - Usa padrões se não especificados
   - Permite sobrescrever qualquer parâmetro

3. **Ativa ambiente virtual**
   - Se `venv\Scripts\activate.bat` existir
   - Caso contrário, usa Python do sistema

4. **Verifica Python e GPU**
   - Mostra versão do Python
   - Detecta se GPU está disponível

5. **Executa dublar.py**
   - Com todos os parâmetros configurados
   - Mostra comandos sendo executados

6. **Verifica resultado**
   - Se sucesso: pergunta se quer abrir o vídeo
   - Se erro: mostra mensagem de erro

---

## Logs e Mensagens

### Durante a execução, você verá:

```
========================================
   DUBLAR - Pipeline de Dublagem GPU
========================================

[CONFIG] Video de entrada: C:\Users\...\video.mp4
[CONFIG] Idioma origem: en
[CONFIG] Idioma destino: pt
[CONFIG] Motor TTS: bark
[CONFIG] Voz: v2/pt_speaker_1
[CONFIG] Modo de sync: smart
[CONFIG] Tolerancia: 0.0
[CONFIG] Max stretch: 2.0
[CONFIG] Arquivo de saida: video_dublado.mp4

[VENV] Ativando ambiente virtual...
[INFO] Python:
Python 3.13.5

[INFO] Verificando GPU...
GPU: NVIDIA GeForce RTX 4070 Laptop GPU

========================================
   Iniciando Pipeline de Dublagem
========================================

[EXEC] python dublar.py --in "video.mp4" --src en --tgt pt ...

=== ETAPA 1: Entrada/cheques ===
=== ETAPA 2: Extração de áudio ===
=== ETAPA 3: Transcrição (Whisper) ===
[GPU] Whisper usando: CUDA
[GPU] GPU: NVIDIA GeForce RTX 4070 Laptop GPU
...
```

---

## Solução de Problemas

### Erro: "Python não encontrado"
```batch
REM Certifique-se que Python está no PATH
python --version

REM Se não estiver, instale Python ou ative o venv manualmente
call venv\Scripts\activate.bat
```

### Erro: "dublar.bat não é reconhecido"
```batch
REM Use o caminho completo
C:\Users\neima\projetosCC\voz_teste\dublar.bat video.mp4

REM Ou navegue até a pasta primeiro
cd C:\Users\neima\projetosCC\voz_teste
dublar video.mp4
```

### Erro: "GPU não disponível"
```batch
REM Verifique se PyTorch CUDA está instalado
python -c "import torch; print(torch.cuda.is_available())"

REM Se False, reinstale PyTorch com CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```

---

## Dicas de Uso

1. **Teste com vídeo curto primeiro**
   - Use um vídeo de 1-2 minutos para testar configurações

2. **Use sincronização `smart`**
   - É o modo mais equilibrado para a maioria dos casos

3. **Bark vs Coqui**
   - **Bark**: Mais natural, mais lento, usa mais VRAM
   - **Coqui**: Mais rápido, menos VRAM, qualidade boa

4. **Monitorar GPU**
   ```batch
   REM Em outro terminal
   nvidia-smi -l 1
   ```

5. **Parâmetros personalizados**
   - Experimente diferentes vozes do Bark
   - Ajuste `tolerance` e `maxstretch` conforme necessário

---

## Arquivo de Configuração (Futuro)

Você pode criar um arquivo `dublar.config` para definir padrões:

```ini
[DEFAULT]
SRC=en
TGT=pt
TTS=bark
VOICE=v2/pt_speaker_1
SYNC=smart
TOLERANCE=0.0
MAXSTRETCH=2.0
```

*Nota: Esta funcionalidade não está implementada ainda, mas pode ser adicionada.*

---

## Referências

- **dublar.py**: Script Python principal
- **INSTALACAO_GPU.md**: Guia de instalação GPU
- **test_gpu.py**: Script de teste GPU
- **FIX_CUDA.md**: Problemas comuns CUDA

---

## Atalhos Úteis

### Windows Terminal / PowerShell

Adicione ao seu perfil PowerShell (`$PROFILE`):

```powershell
function dublar {
    & "C:\Users\neima\projetosCC\voz_teste\dublar.bat" $args
}
```

Agora você pode usar:
```powershell
dublar video.mp4 --src en --tgt pt
```

### CMD

Crie um arquivo `dublar.cmd` em qualquer pasta do PATH:

```batch
@echo off
call "C:\Users\neima\projetosCC\voz_teste\dublar.bat" %*
```

---

**Criado em**: 2025-10-08
**Versão**: 1.0
**Autor**: Claude Code + Usuario

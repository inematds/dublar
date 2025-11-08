@echo off
echo ========================================
echo   INSTALACAO DO PIPELINE DE DUBLAGEM
echo ========================================
echo.

echo [1/5] Criando ambiente virtual...
python -m venv venv
if errorlevel 1 (
    echo ERRO: Nao foi possivel criar ambiente virtual
    echo Certifique-se de que Python esta instalado
    pause
    exit /b 1
)

echo [2/5] Ativando ambiente virtual...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERRO: Nao foi possivel ativar ambiente virtual
    pause
    exit /b 1
)

echo [3/5] Atualizando pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo AVISO: Falha ao atualizar pip, continuando...
)

echo [4/5] Instalando dependencias principais...
echo   - numpy, scipy...
pip install numpy scipy
if errorlevel 1 (
    echo ERRO: Falha ao instalar numpy/scipy
    pause
    exit /b 1
)

echo   - torch (CPU version - pode demorar)...
echo     NOTA: Instalando PyTorch 2.6+ (compatibilidade com Bark via monkey-patch)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
if errorlevel 1 (
    echo ERRO: Falha ao instalar torch
    pause
    exit /b 1
)

echo   - transformers, faster-whisper...
pip install transformers faster-whisper
if errorlevel 1 (
    echo ERRO: Falha ao instalar transformers/whisper
    pause
    exit /b 1
)

echo   - sentencepiece, protobuf (para M2M100)...
pip install sentencepiece protobuf sacremoses
if errorlevel 1 (
    echo AVISO: Falha ao instalar sentencepiece (traducao pode falhar)
)

echo [5/5] Instalando dependencias de audio/TTS...
echo   - bark, TTS...
pip install git+https://github.com/suno-ai/bark.git
pip install TTS
if errorlevel 1 (
    echo AVISO: Falha ao instalar bark/TTS, tentando alternativa...
    pip install bark-voice TTS
)

echo   - librosa, soundfile...
pip install librosa soundfile
if errorlevel 1 (
    echo AVISO: Falha ao instalar librosa (VAD nao funcionara)
)

echo   - pillow...
pip install Pillow

echo.
echo ========================================
echo   INSTALACAO CONCLUIDA!
echo ========================================
echo.
echo Ambiente virtual criado e dependencias instaladas.
echo.
echo Para dublar um video, use:
echo   dublar.bat seu_video.mp4
echo.
echo Ou manualmente:
echo   1. venv\Scripts\activate
echo   2. python dublar_tech_v2.py --in video.mp4 --src en --tgt pt --tts bark --voice v2/pt_speaker_1 --sync smart --tolerance 0.0 --maxstretch 2.0
echo.
pause

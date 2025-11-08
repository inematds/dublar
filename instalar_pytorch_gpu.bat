@echo off
echo ========================================
echo   INSTALAR PYTORCH COM CUDA
echo ========================================
echo.

REM Verifica se ambiente virtual existe
if not exist "venv\Scripts\activate.bat" (
    echo ERRO: Ambiente virtual nao encontrado!
    echo Execute primeiro: instalar.bat
    pause
    exit /b 1
)

echo IMPORTANTE:
echo   Este script vai SUBSTITUIR o PyTorch CPU pelo PyTorch CUDA
echo   Isso permite usar GPU para acelerar o processamento
echo.
echo Versao atual do PyTorch:
call venv\Scripts\activate.bat
python -c "import torch; print('  PyTorch:', torch.__version__); print('  CUDA disponivel:', torch.cuda.is_available())"
echo.

set /p CONFIRM="Deseja continuar? (S/N): "
if /i not "%CONFIRM%"=="S" (
    echo Instalacao cancelada.
    pause
    exit /b 0
)

echo.
echo [1/3] Desinstalando PyTorch CPU...
pip uninstall -y torch torchvision torchaudio

echo.
echo [2/3] Instalando PyTorch com CUDA 12.1 (~2GB)...
echo Isso pode demorar alguns minutos...
echo.

pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

if errorlevel 1 (
    echo.
    echo ERRO: Falha ao instalar PyTorch com CUDA
    echo.
    echo Tentando versao alternativa (CUDA 11.8)...
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

    if errorlevel 1 (
        echo ERRO: Falha na instalacao
        pause
        exit /b 1
    )
)

echo.
echo [3/3] Testando instalacao...
echo.

python -c "import torch; print('PyTorch versao:', torch.__version__); print('CUDA disponivel:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"

echo.
echo ========================================
echo   INSTALACAO CONCLUIDA!
echo ========================================
echo.

python -c "import torch; exit(0 if torch.cuda.is_available() else 1)" 2>nul
if errorlevel 1 (
    echo AVISO: CUDA ainda nao esta disponivel!
    echo.
    echo Possiveis causas:
    echo   1. CUDA Toolkit nao instalado
    echo   2. cuDNN nao instalado ou fora do PATH
    echo   3. Driver NVIDIA desatualizado
    echo.
    echo Execute: instalar_cuda.bat para instalar CUDA completo
    echo.
) else (
    echo GPU funcionando! Agora use:
    echo   ativar_gpu.bat
    echo   dublar.bat seu_video.mp4
    echo.
)

pause

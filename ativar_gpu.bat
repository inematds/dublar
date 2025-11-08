@echo off
echo ========================================
echo   ATIVANDO GPU/CUDA PARA DUBLAGEM
echo ========================================
echo.

REM Adiciona cuDNN ao PATH desta sessao
set PATH=%PATH%;C:\Program Files\NVIDIA\CUDNN\v9.13\bin\13.0

echo [1/3] cuDNN adicionado ao PATH
echo      C:\Program Files\NVIDIA\CUDNN\v9.13\bin\13.0
echo.

REM Verifica se ambiente virtual existe
if not exist "venv\Scripts\activate.bat" (
    echo ERRO: Ambiente virtual nao encontrado!
    echo Execute primeiro: instalar.bat
    pause
    exit /b 1
)

echo [2/3] Ativando ambiente virtual...
call venv\Scripts\activate.bat

echo [3/3] Testando GPU/CUDA...
echo.

python -c "import torch; print('PyTorch versao:', torch.__version__); print('CUDA disponivel:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'Nenhuma')"

echo.
echo ========================================
echo   GPU ATIVADA!
echo ========================================
echo.
echo Agora voce pode rodar:
echo   dublar.bat seu_video.mp4
echo.
echo NOTA: Esta janela deve permanecer aberta!
echo       O PATH so vale para esta sessao.
echo.

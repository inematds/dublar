@echo off
echo ========================================
echo   INSTALAR CUDA 11.8 COMPLETO
echo   Para compatibilidade com PyTorch
echo ========================================
echo.

echo Este script vai:
echo   1. Baixar CUDA Toolkit 11.8 (~3GB)
echo   2. Instalar bibliotecas necessarias (cuBLAS)
echo   3. Configurar PATH
echo.
echo IMPORTANTE: Pode demorar 15-20 minutos
echo.
pause

echo.
echo [1/3] Baixando CUDA Toolkit 11.8...
echo.

set INSTALLER=%TEMP%\cuda_11.8_installer.exe

powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Write-Host 'Baixando... (3GB, pode demorar)'; Invoke-WebRequest -Uri 'https://developer.download.nvidia.com/compute/cuda/11.8.0/local_installers/cuda_11.8.0_522.06_windows.exe' -OutFile '%INSTALLER%' -UseBasicParsing}"

if errorlevel 1 (
    echo.
    echo ERRO no download!
    echo.
    echo Baixe manualmente:
    echo   https://developer.nvidia.com/cuda-11-8-0-download-archive
    echo   Escolha: Windows ^> x86_64 ^> 11 ^> exe (local)
    echo.
    pause
    exit /b 1
)

echo.
echo [2/3] Executando instalador CUDA 11.8...
echo.
echo IMPORTANTE: Na instalacao, escolha CUSTOM e marque:
echo   [X] CUDA
echo   [X] Development
echo   [X] Runtime
echo   [ ] Driver (desmarque se ja tem driver atualizado)
echo.
pause

start /wait "" "%INSTALLER%"

echo.
echo [3/3] Testando instalacao...
echo.

REM Adiciona ao PATH temporario
set PATH=%PATH%;C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\bin

nvcc --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo AVISO: CUDA 11.8 instalado mas nao encontrado no PATH
    echo Reinicie o computador e teste novamente
    echo.
    pause
    exit /b 0
)

echo.
echo CUDA 11.8 instalado com sucesso:
nvcc --version

echo.
echo ========================================
echo   INSTALACAO CONCLUIDA!
echo ========================================
echo.
echo Proximos passos:
echo   1. REINICIE o computador
echo   2. Teste: python test_whisper_gpu.py
echo   3. Se funcionar: dublar.bat seu_video.mp4
echo.
pause

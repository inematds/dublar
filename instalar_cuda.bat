@echo off
echo ========================================
echo   INSTALADOR DE CUDA + cuDNN
echo   Para Aceleracao GPU
echo ========================================
echo.
echo Este script VAO GUIAR voce na instalacao do CUDA.
echo O processo completo leva ~20-30 minutos.
echo.
echo IMPORTANTE:
echo   - Voce precisa de uma placa NVIDIA compativel
echo   - Requer ~5GB de espaco em disco
echo   - Pode precisar reiniciar o computador
echo.
pause
echo.

REM ============================================
REM PASSO 1: Verificar placa NVIDIA
REM ============================================
echo [1/6] Verificando placa NVIDIA...
nvidia-smi >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERRO: Nenhuma placa NVIDIA detectada!
    echo.
    echo Este script e apenas para placas NVIDIA.
    echo Se voce tem placa NVIDIA, instale os drivers primeiro:
    echo   https://www.nvidia.com/Download/index.aspx
    echo.
    pause
    exit /b 1
)

echo GPU NVIDIA detectada:
nvidia-smi --query-gpu=name --format=csv,noheader
echo.
pause

REM ============================================
REM PASSO 2: Verificar se CUDA ja esta instalado
REM ============================================
echo [2/6] Verificando instalacao existente de CUDA...
nvcc --version >nul 2>&1
if not errorlevel 1 (
    echo.
    echo CUDA ja esta instalado:
    nvcc --version
    echo.
    echo Deseja reinstalar? (S/N)
    set /p REINSTALL=
    if /i not "%REINSTALL%"=="S" (
        echo Pulando instalacao do CUDA...
        goto STEP_CUDNN
    )
)
echo CUDA nao detectado, continuando instalacao...
echo.

REM ============================================
REM PASSO 3: Download CUDA Toolkit
REM ============================================
:STEP_CUDA
echo [3/6] Download do CUDA Toolkit 11.8
echo.
echo OPCAO 1: Download Automatico (Recomendado)
echo OPCAO 2: Download Manual
echo.
set /p DOWNLOAD_CHOICE="Escolha (1 ou 2): "

if "%DOWNLOAD_CHOICE%"=="1" (
    echo.
    echo Baixando CUDA 11.8 (~3GB, pode demorar)...
    echo Por favor aguarde...

    REM Usa PowerShell para download
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://developer.download.nvidia.com/compute/cuda/11.8.0/network_installers/cuda_11.8.0_windows_network.exe' -OutFile '%TEMP%\cuda_installer.exe'}"

    if errorlevel 1 (
        echo.
        echo ERRO: Falha no download automatico.
        echo Por favor, baixe manualmente em:
        echo   https://developer.nvidia.com/cuda-11-8-0-download-archive
        echo.
        pause
        exit /b 1
    )

    set CUDA_INSTALLER=%TEMP%\cuda_installer.exe
) else (
    echo.
    echo Por favor:
    echo   1. Abra: https://developer.nvidia.com/cuda-11-8-0-download-archive
    echo   2. Selecione: Windows ^> x86_64 ^> [sua versao] ^> exe (local)
    echo   3. Baixe o arquivo
    echo.
    echo Quando terminar o download, digite o caminho completo do arquivo:
    set /p CUDA_INSTALLER="Caminho: "

    if not exist "%CUDA_INSTALLER%" (
        echo ERRO: Arquivo nao encontrado!
        pause
        exit /b 1
    )
)

echo.
echo Executando instalador CUDA...
echo.
echo IMPORTANTE: Na instalacao, escolha:
echo   - Express Installation (Recomendado)
echo   - Ou Custom e marque: CUDA Toolkit + Visual Studio Integration
echo.
pause

start /wait "" "%CUDA_INSTALLER%"

echo.
echo Instalacao do CUDA concluida!
echo.
pause

REM ============================================
REM PASSO 4: Verificar instalacao CUDA
REM ============================================
echo [4/6] Verificando instalacao do CUDA...

REM Atualiza PATH temporariamente
set PATH=%PATH%;C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\bin

nvcc --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo AVISO: CUDA instalado mas nvcc nao encontrado no PATH.
    echo Tente reiniciar o computador e execute este script novamente.
    echo.
    pause
    exit /b 1
)

echo CUDA instalado com sucesso:
nvcc --version
echo.
pause

REM ============================================
REM PASSO 5: Download e instalacao cuDNN
REM ============================================
:STEP_CUDNN
echo [5/6] Instalacao do cuDNN
echo.
echo O cuDNN requer conta NVIDIA (gratis).
echo.
echo INSTRUCOES:
echo   1. Abra: https://developer.nvidia.com/cudnn
echo   2. Clique em "Download cuDNN"
echo   3. Faca login ou crie conta (gratis)
echo   4. Baixe: cuDNN v8.x.x for CUDA 11.x
echo   5. Extraia o arquivo ZIP baixado
echo.
pause

echo.
echo Digite o caminho da pasta EXTRAIDA do cuDNN:
echo Exemplo: C:\Users\seu_usuario\Downloads\cudnn-windows-x86_64-8.x.x
echo.
set /p CUDNN_PATH="Caminho da pasta cuDNN: "

if not exist "%CUDNN_PATH%\bin" (
    echo ERRO: Pasta invalida! Certifique-se de extrair o ZIP primeiro.
    echo A pasta deve conter: bin, include, lib
    pause
    exit /b 1
)

echo.
echo Copiando arquivos cuDNN para CUDA...

set CUDA_PATH=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8

xcopy "%CUDNN_PATH%\bin\*.dll" "%CUDA_PATH%\bin\" /Y /I
xcopy "%CUDNN_PATH%\include\*.h" "%CUDA_PATH%\include\" /Y /I
xcopy "%CUDNN_PATH%\lib\x64\*.lib" "%CUDA_PATH%\lib\x64\" /Y /I

if errorlevel 1 (
    echo.
    echo ERRO: Falha ao copiar arquivos.
    echo Execute este script como ADMINISTRADOR.
    echo.
    pause
    exit /b 1
)

echo cuDNN instalado com sucesso!
echo.
pause

REM ============================================
REM PASSO 6: Reinstalar PyTorch com CUDA
REM ============================================
echo [6/6] Reinstalando PyTorch com suporte CUDA...
echo.

REM Verifica se esta no ambiente virtual
if not exist "venv\Scripts\activate.bat" (
    echo ERRO: Ambiente virtual nao encontrado!
    echo Execute primeiro: instalar.bat
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo Desinstalando PyTorch CPU...
pip uninstall -y torch torchvision torchaudio

echo.
echo Instalando PyTorch com CUDA 11.8 (~2GB)...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

if errorlevel 1 (
    echo ERRO: Falha ao instalar PyTorch com CUDA
    pause
    exit /b 1
)

echo.
echo Testando CUDA no PyTorch...
python -c "import torch; print('CUDA disponivel:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"

echo.
echo ========================================
echo   INSTALACAO CONCLUIDA!
echo ========================================
echo.
echo PROXIMOS PASSOS:
echo   1. REINICIE o computador
echo   2. Execute: dublar.bat seu_video.mp4
echo   3. Verifique se aparece "GPU funcionando!"
echo.
echo Se ainda aparecer erro de GPU, execute novamente este script.
echo.
pause

@echo off
REM ========================================
REM  DUBLAR - Script de Dublagem com GPU
REM ========================================

setlocal enabledelayedexpansion

echo.
echo ========================================
echo    DUBLAR - Pipeline de Dublagem GPU
echo ========================================
echo.

REM Verificar se foi passado um arquivo de video
if "%~1"=="" (
    echo [ERRO] Nenhum video especificado!
    echo.
    echo Uso:
    echo   dublar video.mp4                    [usa padroes: en-^>pt, bark, smart]
    echo   dublar video.mp4 --src en --tgt es  [customizar parametros]
    echo.
    echo Padroes: --src en --tgt pt --tts bark --voice v2/pt_speaker_1 --sync smart
    echo.
    echo Parametros: --src, --tgt, --tts, --voice, --sync, --tolerance, --maxstretch, --out
    echo.
    exit /b 1
)

REM Verificar se o arquivo de video existe
if not exist "%~1" (
    echo [ERRO] Arquivo nao encontrado: %~1
    exit /b 1
)

REM Obter caminho completo e nome base do video
set "VIDEO=%~f1"
set "VIDEO_NAME=%~n1"
set "VIDEO_EXT=%~x1"
shift

REM Criar pasta dublado se nao existir
if not exist "%~dp0dublado\" mkdir "%~dp0dublado"

REM Parametros padrao
set "SRC=en"
set "TGT=pt"
set "TTS=bark"
set "VOICE=v2/pt_speaker_1"
set "SYNC=smart"
set "TOLERANCE=0.05"
set "MAXSTRETCH=1.3"
set "OUT=dublado\%VIDEO_NAME%%VIDEO_EXT%"

REM Processar argumentos adicionais
:parse_args
if "%~1"=="" goto end_parse

if /i "%~1"=="--src" (
    set "SRC=%~2"
    shift & shift
    goto parse_args
)
if /i "%~1"=="--tgt" (
    set "TGT=%~2"
    shift & shift
    goto parse_args
)
if /i "%~1"=="--tts" (
    set "TTS=%~2"
    shift & shift
    goto parse_args
)
if /i "%~1"=="--voice" (
    set "VOICE=%~2"
    shift & shift
    goto parse_args
)
if /i "%~1"=="--sync" (
    set "SYNC=%~2"
    shift & shift
    goto parse_args
)
if /i "%~1"=="--tolerance" (
    set "TOLERANCE=%~2"
    shift & shift
    goto parse_args
)
if /i "%~1"=="--maxstretch" (
    set "MAXSTRETCH=%~2"
    shift & shift
    goto parse_args
)
if /i "%~1"=="--out" (
    set "OUT=%~2"
    shift & shift
    goto parse_args
)

REM Argumento desconhecido
echo [AVISO] Argumento desconhecido: %~1
shift
goto parse_args

:end_parse

REM Mostrar configuracao
echo.
echo [CONFIG] Configuracao da Dublagem:
echo   Video........: %VIDEO%
echo   Idioma origem: %SRC% (en=ingles, pt=portugues, es=espanhol, etc.)
echo   Idioma alvo..: %TGT%
echo   Motor TTS....: %TTS% (bark=melhor qualidade, coqui=mais rapido)
if /i "%TTS%"=="bark" echo   Voz..........: %VOICE%
echo   Sincronizacao: %SYNC% (smart=automatico, fit=ajustar, pad=preencher)
echo   Tolerancia...: %TOLERANCE%
echo   Max stretch..: %MAXSTRETCH%
echo   Arquivo saida: %OUT%
echo.

REM Verificar se existe venv
if exist "%~dp0venv\Scripts\activate.bat" (
    echo [VENV] Ativando ambiente virtual...
    call "%~dp0venv\Scripts\activate.bat"
) else (
    echo [AVISO] Ambiente virtual nao encontrado, usando Python do sistema
)

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    exit /b 1
)

echo [INFO] Python:
python --version

REM Verificar CUDA
echo [INFO] Verificando GPU...
python -c "import torch; print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"CPU apenas\"}')" 2>nul
if errorlevel 1 (
    echo [AVISO] PyTorch nao instalado ou GPU nao disponivel
)

echo.
echo ========================================
echo    Iniciando Pipeline de Dublagem
echo ========================================
echo.

REM Construir comando
set "CMD=python "%~dp0dublar.py" --in "%VIDEO%" --src %SRC% --tgt %TGT% --tts %TTS% --sync %SYNC% --tolerance %TOLERANCE% --maxstretch %MAXSTRETCH% --out "%OUT%""

if /i "%TTS%"=="bark" (
    set "CMD=!CMD! --voice %VOICE%"
)

REM Executar
echo [EXEC] %CMD%
echo.
%CMD%

REM Verificar resultado
if errorlevel 1 (
    echo.
    echo ========================================
    echo    ERRO no processo de dublagem!
    echo ========================================
    exit /b 1
) else (
    echo.
    echo ========================================
    echo    Dublagem concluida com sucesso!
    echo ========================================
    echo.
    echo [OK] Arquivo de saida: %OUT%
    echo.
    if exist "%OUT%" (
        echo Deseja abrir o video? (S/N)
        set /p "OPEN=>>> "
        if /i "!OPEN!"=="S" (
            start "" "%OUT%"
        )
    )
)

endlocal

@echo off
REM ========================================
REM  DUBLAR GLOBAL - Atalho para dublar.bat
REM ========================================
REM
REM Este script permite usar 'dublar' de qualquer pasta.
REM
REM Instalacao:
REM 1. Copie este arquivo para uma pasta no PATH (ex: C:\Windows\System32)
REM 2. Ou adicione a pasta C:\Users\neima\projetosCC\voz_teste ao PATH do Windows
REM
REM Uso:
REM   dublar_global video.mp4
REM   dublar_global C:\Videos\video.mp4 --src en --tgt pt
REM ========================================

REM Caminho do projeto dublar
set "DUBLAR_PATH=C:\Users\neima\projetosCC\voz_teste"

REM Verificar se dublar.bat existe
if not exist "%DUBLAR_PATH%\dublar.bat" (
    echo [ERRO] dublar.bat nao encontrado em: %DUBLAR_PATH%
    echo.
    echo Por favor, ajuste a variavel DUBLAR_PATH neste script.
    exit /b 1
)

REM Chamar dublar.bat com todos os argumentos
call "%DUBLAR_PATH%\dublar.bat" %*

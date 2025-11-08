@echo off
echo ========================================
echo   DIAGNOSTICO DO PROCESSO DE DUBLAGEM
echo ========================================
echo.

if not exist "dub_work" (
    echo ERRO: Pasta dub_work nao existe!
    echo Execute primeiro: dublar.bat seu_video.mp4
    pause
    exit /b 1
)

echo Verificando arquivos criados em cada etapa...
echo.

REM ETAPA 2
echo [ETAPA 2] Extracao de audio:
if exist "dub_work\audio_src.wav" (
    echo   [OK] audio_src.wav encontrado
    for %%A in ("dub_work\audio_src.wav") do echo   Tamanho: %%~zA bytes
) else (
    echo   [FALTANDO] audio_src.wav
    echo   ^> Processo parou ANTES da extracao de audio
)
echo.

REM ETAPA 3
echo [ETAPA 3] Transcricao ^(Whisper^):
set ETAPA3_OK=0
if exist "dub_work\asr.json" (
    echo   [OK] asr.json encontrado
    set ETAPA3_OK=1
) else (
    echo   [FALTANDO] asr.json
)
if exist "dub_work\asr.srt" (
    echo   [OK] asr.srt encontrado
) else (
    echo   [FALTANDO] asr.srt
)
if %ETAPA3_OK%==0 (
    echo   ^> Processo parou na TRANSCRICAO
    echo   ^> Verifique erros de faster-whisper ou CUDA
)
echo.

REM ETAPA 4
echo [ETAPA 4] Traducao ^(M2M100^):
set ETAPA4_OK=0
if exist "dub_work\asr_trad.json" (
    echo   [OK] asr_trad.json encontrado
    set ETAPA4_OK=1
) else (
    echo   [FALTANDO] asr_trad.json
)
if exist "dub_work\asr_trad.srt" (
    echo   [OK] asr_trad.srt encontrado
) else (
    echo   [FALTANDO] asr_trad.srt
)
if %ETAPA4_OK%==0 if %ETAPA3_OK%==1 (
    echo   ^> Processo parou na TRADUCAO
    echo   ^> Verifique erros de transformers ou memoria RAM
)
echo.

REM ETAPA 6
echo [ETAPA 6] TTS ^(Text-to-Speech^):
set ETAPA6_OK=0
if exist "dub_work\seg_0001.wav" (
    echo   [OK] Segmentos TTS encontrados
    set ETAPA6_OK=1
    REM Conta quantos segmentos
    for /f %%A in ('dir /b "dub_work\seg_*.wav" 2^>nul ^| find /c /v ""') do echo   Total de segmentos: %%A
) else (
    echo   [FALTANDO] seg_*.wav
)
if exist "dub_work\segments.csv" (
    echo   [OK] segments.csv encontrado
) else (
    echo   [FALTANDO] segments.csv
)
if %ETAPA6_OK%==0 if %ETAPA4_OK%==1 (
    echo   ^> Processo parou no TTS
    echo   ^> Verifique erros de Bark/Coqui ou CUDA
)
echo.

REM ETAPA 8
echo [ETAPA 8] Concatenacao:
set ETAPA8_OK=0
if exist "dub_work\list.txt" (
    echo   [OK] list.txt encontrado
) else (
    echo   [FALTANDO] list.txt
)
if exist "dub_work\dub_raw.wav" (
    echo   [OK] dub_raw.wav encontrado
    for %%A in ("dub_work\dub_raw.wav") do echo   Tamanho: %%~zA bytes
    set ETAPA8_OK=1
) else (
    echo   [FALTANDO] dub_raw.wav
)
if %ETAPA8_OK%==0 if %ETAPA6_OK%==1 (
    echo   ^> Processo parou na CONCATENACAO
    echo   ^> Verifique erros de ffmpeg
)
echo.

REM ETAPA 9
echo [ETAPA 9] Pos-processamento:
set ETAPA9_OK=0
if exist "dub_work\dub_final.wav" (
    echo   [OK] dub_final.wav encontrado
    for %%A in ("dub_work\dub_final.wav") do echo   Tamanho: %%~zA bytes
    set ETAPA9_OK=1
) else (
    echo   [FALTANDO] dub_final.wav
)
if %ETAPA9_OK%==0 if %ETAPA8_OK%==1 (
    echo   ^> Processo parou no POS-PROCESSAMENTO
    echo   ^> Verifique erros de ffmpeg filters
)
echo.

REM ETAPA 10
echo [ETAPA 10] Video final:
set ETAPA10_OK=0
set VIDEO_FINAL=
for %%F in ("dublado\*.mp4") do (
    echo   [OK] %%~nxF encontrado
    for %%A in ("%%F") do echo   Tamanho: %%~zA bytes
    set ETAPA10_OK=1
    set VIDEO_FINAL=%%F
)
if %ETAPA10_OK%==0 (
    echo   [FALTANDO] Video final em dublado/
    if %ETAPA9_OK%==1 (
        echo   ^> Processo parou no MUX FINAL
        echo   ^> Verifique erros de ffmpeg mux
    )
) else (
    echo.
    echo ========================================
    echo   SUCESSO! Video dublado criado:
    echo   %VIDEO_FINAL%
    echo ========================================
)
echo.

REM Logs
echo [LOGS]:
if exist "dub_work\logs.json" (
    echo   [OK] logs.json encontrado
) else (
    echo   [FALTANDO] logs.json
)
echo.

REM Resumo
echo ========================================
echo   RESUMO
echo ========================================
if %ETAPA10_OK%==1 (
    echo Status: CONCLUIDO COM SUCESSO
    echo Proximo passo: Assista o video em dublado/
) else (
    echo Status: INCOMPLETO
    echo.
    if %ETAPA3_OK%==0 (
        echo Falhou em: ETAPA 3 - Transcricao
        echo Solucao: Verifique instalacao do faster-whisper
        echo   pip install faster-whisper
    ) else if %ETAPA4_OK%==0 (
        echo Falhou em: ETAPA 4 - Traducao
        echo Solucao: Verifique instalacao do transformers
        echo   pip install transformers
    ) else if %ETAPA6_OK%==0 (
        echo Falhou em: ETAPA 6 - TTS
        echo Solucao: Verifique instalacao do Bark/Coqui
        echo   pip install bark TTS
    ) else if %ETAPA8_OK%==0 (
        echo Falhou em: ETAPA 8 - Concatenacao
        echo Solucao: Verifique ffmpeg instalado
    ) else if %ETAPA9_OK%==0 (
        echo Falhou em: ETAPA 9 - Pos-processamento
        echo Solucao: Verifique ffmpeg filters
    ) else if %ETAPA10_OK%==0 (
        echo Falhou em: ETAPA 10 - Mux final
        echo Solucao: Verifique ffmpeg mux
    )
    echo.
    echo Execute novamente com output completo:
    echo   python dublar_tech_v2.py --in seu_video.mp4 --src en --tgt pt --tts bark --voice v2/pt_speaker_1 --sync smart
)
echo ========================================
echo.
pause

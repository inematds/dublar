@echo off
REM ========================================
REM  EXEMPLOS DE USO DO DUBLAR.BAT
REM ========================================

echo.
echo Este arquivo contem exemplos de uso do dublar.bat
echo NAO EXECUTE este arquivo! Copie os comandos que deseja usar.
echo.
pause
exit /b

REM ========================================
REM  EXEMPLOS BASICOS
REM ========================================

REM 1. Uso mais simples (ingles -> portugues, Bark, sync smart)
dublar video.mp4

REM 2. Especificar arquivo de saida
dublar video.mp4 --out meu_video_dublado.mp4

REM 3. Dublar de ingles para espanhol
dublar video.mp4 --src en --tgt es

REM 4. Dublar de portugues para ingles
dublar video_pt.mp4 --src pt --tgt en

REM ========================================
REM  TROCAR MOTOR TTS
REM ========================================

REM 5. Usar Coqui TTS em vez de Bark (mais rapido)
dublar video.mp4 --tts coqui

REM 6. Bark com voz especifica
dublar video.mp4 --tts bark --voice v2/en_speaker_6

REM ========================================
REM  AJUSTAR SINCRONIZACAO
REM ========================================

REM 7. Sincronizacao perfeita (fit)
dublar video.mp4 --sync fit

REM 8. Sem sincronizacao (pode desalinhar)
dublar video.mp4 --sync none

REM 9. Adicionar silencio apenas (pad)
dublar video.mp4 --sync pad

REM 10. Smart com parametros customizados
dublar video.mp4 --sync smart --tolerance 0.15 --maxstretch 1.5

REM ========================================
REM  EXEMPLOS COMPLETOS
REM ========================================

REM 11. Dublar video de ingles para portugues com Bark e sync perfeito
dublar video.mp4 --src en --tgt pt --tts bark --voice v2/pt_speaker_1 --sync smart --tolerance 0.0 --maxstretch 2.0 --out dublado.mp4

REM 12. Dublar com Coqui (mais rapido) de ingles para espanhol
dublar video.mp4 --src en --tgt es --tts coqui --sync smart --out video_es.mp4

REM 13. Processar video em outra pasta
dublar "C:\Videos\meu_video.mp4" --out "C:\Videos\dublado.mp4"

REM 14. Dublar varios idiomas
dublar video.mp4 --src en --tgt pt --out video_pt.mp4
dublar video.mp4 --src en --tgt es --out video_es.mp4
dublar video.mp4 --src en --tgt fr --out video_fr.mp4

REM ========================================
REM  DICAS
REM ========================================

REM - Use --tts coqui para processamento mais rapido
REM - Use --sync smart para melhor sincronizacao
REM - Teste com video curto (1-2 min) antes de videos longos
REM - Monitor GPU em outro terminal: nvidia-smi -l 1
REM - Logs sao salvos em dub_work/logs.json

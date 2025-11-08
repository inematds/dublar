#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TESTE RÁPIDO: Apenas concatena os WAV existentes e aplica pós-processamento NOVO
Usa os arquivos seg_*.wav já gerados pelo Bark
"""

import subprocess
from pathlib import Path
import json

print("=" * 70)
print("  TESTE RÁPIDO - Concatenar WAV + Pós-processo NOVO")
print("=" * 70)
print()

workdir = Path('dub_work')

# Verificar se existem arquivos seg_*.wav
seg_files = sorted(workdir.glob('seg_*.wav'))
seg_files = [f for f in seg_files if not ('_xf' in f.name or '_fit' in f.name or '_pad' in f.name)]

if not seg_files:
    print("ERRO: Nenhum arquivo seg_*.wav encontrado em dub_work/")
    print("Execute 'dublar nei.mp4' primeiro para gerar os arquivos TTS.")
    exit(1)

print(f"✅ Encontrados {len(seg_files)} arquivos seg_*.wav")
print()

# ============================================================================
# ETAPA 1: Criar lista de arquivos para concatenação
# ============================================================================
print("=" * 70)
print("ETAPA 1: Criando lista de concatenação")
print("=" * 70)
print()

list_file = workdir / 'test_list.txt'
with open(list_file, 'w', encoding='utf-8') as f:
    for seg in seg_files:
        f.write(f"file '{seg.name}'\n")

print(f"✅ Lista criada: {list_file}")
print(f"   Total: {len(seg_files)} arquivos")
print()

# ============================================================================
# ETAPA 2: Concatenar arquivos
# ============================================================================
print("=" * 70)
print("ETAPA 2: Concatenando arquivos WAV")
print("=" * 70)
print()

concat_out = workdir / 'test_concat.wav'
samplerate = 24000

cmd_concat = [
    "ffmpeg", "-y", "-f", "concat", "-safe", "0",
    "-i", str(list_file),
    "-c:a", "pcm_s16le", "-ar", str(samplerate), "-ac", "1",
    str(concat_out)
]

print(f"Comando: {' '.join(cmd_concat[:6])}...")
result = subprocess.run(cmd_concat, capture_output=True, text=True)

if result.returncode == 0:
    print(f"✅ Concatenado: {concat_out}")

    # Verificar duração
    try:
        dur_result = subprocess.check_output([
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=nw=1",
            str(concat_out)
        ], text=True).strip()
        duration = float(dur_result)
        print(f"   Duração: {duration:.2f}s")
    except:
        pass
else:
    print(f"❌ Erro ao concatenar")
    print(result.stderr[:500])
    exit(1)

print()

# ============================================================================
# ETAPA 3: Pós-processamento com filtros NOVOS (corrigidos)
# ============================================================================
print("=" * 70)
print("ETAPA 3: Pós-processamento (FILTROS NOVOS)")
print("=" * 70)
print()

# Filtros corrigidos (sem afftdn e equalizer)
fx_new = "loudnorm=I=-14:TP=-1.5:LRA=11"
final_out = workdir / 'test_final_CORRECTED.wav'

print(f"Filtros: {fx_new}")

cmd_post = [
    "ffmpeg", "-y", "-i", str(concat_out),
    "-af", fx_new,
    "-ar", str(samplerate), "-ac", "1",
    str(final_out)
]

print(f"Processando...")
result = subprocess.run(cmd_post, capture_output=True, text=True)

if result.returncode == 0:
    print(f"✅ Pós-processado: {final_out}")

    # Verificar duração
    try:
        dur_result = subprocess.check_output([
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=nw=1",
            str(final_out)
        ], text=True).strip()
        duration = float(dur_result)
        print(f"   Duração: {duration:.2f}s")
    except:
        pass
else:
    print(f"❌ Erro ao pós-processar")
    print(result.stderr[:500])
    exit(1)

print()

# ============================================================================
# ETAPA 4: Análise de volume
# ============================================================================
print("=" * 70)
print("ETAPA 4: Análise de Volume")
print("=" * 70)
print()

def analyze_volume(file_path, label):
    """Analisa volume de arquivo de áudio"""
    try:
        result = subprocess.run([
            "ffmpeg", "-i", str(file_path),
            "-af", "volumedetect",
            "-vn", "-f", "null", "-"
        ], capture_output=True, text=True, stderr=subprocess.STDOUT)

        output = result.stdout
        mean_vol = None
        max_vol = None

        for line in output.split('\n'):
            if 'mean_volume:' in line:
                mean_vol = line.split('mean_volume:')[1].split('dB')[0].strip()
            if 'max_volume:' in line:
                max_vol = line.split('max_volume:')[1].split('dB')[0].strip()

        if mean_vol and max_vol:
            mean_db = float(mean_vol)

            if mean_db < -50:
                status = "MUITO BAIXO (quase mudo)"
            elif mean_db < -30:
                status = "Baixo"
            elif mean_db < -20:
                status = "Normal"
            else:
                status = "Alto"

            print(f"{label}:")
            print(f"  Mean volume: {mean_vol} dB")
            print(f"  Max volume:  {max_vol} dB")
            print(f"  Status: {status}")
            return mean_db
    except Exception as e:
        print(f"{label}: Erro ao analisar - {e}")
    return None

# Comparar concatenado vs pós-processado
concat_vol = analyze_volume(concat_out, "Áudio concatenado (antes pós-processo)")
print()
final_vol = analyze_volume(final_out, "Áudio final (após pós-processo NOVO)")
print()

# ============================================================================
# ETAPA 5: Muxar com vídeo original
# ============================================================================
print("=" * 70)
print("ETAPA 5: Muxar com vídeo original")
print("=" * 70)
print()

# Procurar vídeo original
video_in = Path('nei.mp4')
if not video_in.exists():
    print("⚠️  nei.mp4 não encontrado na raiz, pulando mux")
    video_in = None
else:
    video_out = Path('test_VIDEO_CORRECTED.mp4')

    cmd_mux = [
        "ffmpeg", "-y",
        "-i", str(video_in),
        "-i", str(final_out),
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        str(video_out)
    ]

    print(f"Gerando vídeo de teste: {video_out}")
    result = subprocess.run(cmd_mux, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✅ Vídeo gerado: {video_out}")

        # Verificar duração e bitrate
        try:
            probe = subprocess.check_output([
                "ffprobe", "-v", "error",
                "-select_streams", "a:0",
                "-show_entries", "stream=bit_rate,duration",
                "-of", "default=nw=1",
                str(video_out)
            ], text=True)
            print(f"   Info áudio:")
            for line in probe.strip().split('\n'):
                if line:
                    print(f"     {line}")
        except:
            pass
    else:
        print(f"❌ Erro ao muxar vídeo")
        print(result.stderr[:300])

print()

# ============================================================================
# RESUMO
# ============================================================================
print("=" * 70)
print("RESUMO")
print("=" * 70)
print()

print("Arquivos gerados:")
print(f"  1. {concat_out}")
print(f"     Áudio concatenado (sem pós-processo)")
print()
print(f"  2. {final_out}")
print(f"     Áudio com pós-processo CORRIGIDO")
if video_in:
    print()
    print(f"  3. {video_out}")
    print(f"     Vídeo completo para teste")

print()
print("-" * 70)

if concat_vol is not None and final_vol is not None:
    diff = final_vol - concat_vol
    print(f"Volume:")
    print(f"  Antes pós-processo: {concat_vol:.1f} dB")
    print(f"  Após pós-processo:  {final_vol:.1f} dB")
    print(f"  Diferença:          {diff:+.1f} dB")
    print()

    if final_vol > -30:
        print("✅ Volume CORRETO (áudio deve estar audível)")
    elif final_vol > -50:
        print("⚠️  Volume ainda baixo, mas melhor que antes")
    else:
        print("❌ Volume ainda muito baixo (problema no áudio TTS original)")

print()
print("=" * 70)
print("TESTE PARA VALIDAR:")
print("=" * 70)
print()
print("1. Reproduzir áudio para verificar se está audível:")
if video_in:
    print(f"   ffplay {video_out}")
else:
    print(f"   ffplay {final_out}")
print()
print("2. Comparar com vídeo antigo (se existir):")
print("   ffplay video_dublado.mp4")
print()
print("3. Verificar duração (deve ser ~114s):")
if video_in:
    print(f"   ffprobe -v error -show_entries format=duration {video_out}")
print()

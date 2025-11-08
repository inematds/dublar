#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para testar a correção do pós-processamento de áudio
Aplica os filtros ANTIGOS e NOVOS no dub_raw.wav e compara
"""

import subprocess
from pathlib import Path

print("=" * 70)
print("  TESTE DE CORREÇÃO DO PÓS-PROCESSAMENTO DE ÁUDIO")
print("=" * 70)
print()

workdir = Path('dub_work')
raw_file = workdir / 'dub_raw.wav'

if not raw_file.exists():
    print(f"ERRO: {raw_file} não encontrado!")
    print("Execute 'dublar nei.mp4' primeiro para gerar os arquivos intermediários.")
    exit(1)

samplerate = 24000

# ============================================================================
# TESTE 1: Aplicar filtros ANTIGOS (problemáticos)
# ============================================================================
print("=" * 70)
print("TESTE 1: Pós-processamento ANTIGO (com afftdn + equalizer)")
print("=" * 70)
print()

fx_old = "loudnorm=I=-16:TP=-1.5:LRA=11,afftdn=nf=-25,equalizer=f=6500:t=h:width=2000:g=-4"
out_old = workdir / 'test_final_OLD.wav'

print(f"Filtros antigos: {fx_old}")
print(f"Processando...")

cmd_old = [
    "ffmpeg", "-y", "-i", str(raw_file),
    "-af", fx_old,
    "-ar", str(samplerate), "-ac", "1",
    str(out_old)
]

result = subprocess.run(cmd_old, capture_output=True, text=True)
if result.returncode == 0:
    print(f"✅ Gerado: {out_old}")
else:
    print(f"❌ Erro ao processar")
    print(result.stderr[:500])

print()

# ============================================================================
# TESTE 2: Aplicar filtros NOVOS (corrigidos)
# ============================================================================
print("=" * 70)
print("TESTE 2: Pós-processamento NOVO (apenas loudnorm)")
print("=" * 70)
print()

fx_new = "loudnorm=I=-14:TP=-1.5:LRA=11"
out_new = workdir / 'test_final_NEW.wav'

print(f"Filtros novos: {fx_new}")
print(f"Processando...")

cmd_new = [
    "ffmpeg", "-y", "-i", str(raw_file),
    "-af", fx_new,
    "-ar", str(samplerate), "-ac", "1",
    str(out_new)
]

result = subprocess.run(cmd_new, capture_output=True, text=True)
if result.returncode == 0:
    print(f"✅ Gerado: {out_new}")
else:
    print(f"❌ Erro ao processar")
    print(result.stderr[:500])

print()

# ============================================================================
# TESTE 3: Comparar volumes
# ============================================================================
print("=" * 70)
print("TESTE 3: Comparação de Volumes")
print("=" * 70)
print()

def analyze_volume(file_path):
    """Analisa volume de arquivo de áudio"""
    try:
        result = subprocess.run([
            "ffmpeg", "-i", str(file_path),
            "-af", "volumedetect",
            "-vn", "-f", "null", "-"
        ], capture_output=True, text=True, stderr=subprocess.STDOUT)

        output = result.stdout

        # Extrair valores
        mean_vol = None
        max_vol = None

        for line in output.split('\n'):
            if 'mean_volume:' in line:
                mean_vol = line.split('mean_volume:')[1].split('dB')[0].strip()
            if 'max_volume:' in line:
                max_vol = line.split('max_volume:')[1].split('dB')[0].strip()

        return mean_vol, max_vol
    except Exception as e:
        return None, None

# Comparar os 3 arquivos
files_to_compare = [
    ('dub_raw.wav (ORIGINAL)', raw_file),
    ('test_final_OLD.wav (FILTROS ANTIGOS)', out_old),
    ('test_final_NEW.wav (FILTROS NOVOS)', out_new),
]

print(f"{'Arquivo':<40} {'Mean Volume':<15} {'Max Volume':<15} {'Status':<20}")
print("-" * 90)

results = []

for name, file_path in files_to_compare:
    if file_path.exists():
        mean, max_v = analyze_volume(file_path)
        if mean and max_v:
            mean_db = float(mean)
            max_db = float(max_v)

            if mean_db < -50:
                status = "MUITO BAIXO ❌"
            elif mean_db < -30:
                status = "Baixo ⚠️"
            elif mean_db < -20:
                status = "Normal ✅"
            else:
                status = "Alto ✅"

            print(f"{name:<40} {mean} dB{' ':<8} {max_v} dB{' ':<8} {status}")
            results.append((name, mean_db, max_db))
        else:
            print(f"{name:<40} N/A             N/A             Erro na análise")
    else:
        print(f"{name:<40} N/A             N/A             Arquivo não existe")

print()

# ============================================================================
# RESUMO
# ============================================================================
print("=" * 70)
print("RESUMO DA ANÁLISE")
print("=" * 70)
print()

if len(results) >= 3:
    orig_mean = results[0][1]
    old_mean = results[1][1]
    new_mean = results[2][1]

    print(f"Volume médio (mean_volume):")
    print(f"  Original (raw):        {orig_mean:.1f} dB")
    print(f"  Após filtros ANTIGOS:  {old_mean:.1f} dB  (diferença: {old_mean - orig_mean:+.1f} dB)")
    print(f"  Após filtros NOVOS:    {new_mean:.1f} dB  (diferença: {new_mean - orig_mean:+.1f} dB)")
    print()

    if old_mean < -50:
        print("❌ Filtros ANTIGOS destruíram o áudio (< -50 dB)")
    else:
        print("⚠️  Filtros ANTIGOS reduziram volume mas não destruíram")

    print()

    if new_mean > old_mean:
        improvement = new_mean - old_mean
        print(f"✅ Filtros NOVOS melhoraram volume em {improvement:.1f} dB")
    else:
        print(f"⚠️  Filtros NOVOS não melhoraram (diferença: {new_mean - old_mean:.1f} dB)")

    print()

    if new_mean > -30:
        print("✅ Volume NOVO está em nível aceitável (> -30 dB)")
    elif new_mean > -50:
        print("⚠️  Volume NOVO ainda está baixo (-50 a -30 dB)")
    else:
        print("❌ Volume NOVO ainda está muito baixo (< -50 dB)")

print()
print("=" * 70)
print("ARQUIVOS GERADOS PARA TESTE MANUAL:")
print("=" * 70)
print()
print(f"  {out_old}")
print(f"  {out_new}")
print()
print("Você pode reproduzir esses arquivos para comparar:")
print(f"  ffplay {out_old}")
print(f"  ffplay {out_new}")
print()

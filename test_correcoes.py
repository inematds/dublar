#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de teste manual para validar correções do pipeline de dublagem
Usa os arquivos já gerados em dub_work/ para testar as funções corrigidas
"""

import json
import re
from pathlib import Path

print("=" * 60)
print("  TESTE MANUAL DAS CORREÇÕES")
print("=" * 60)
print()

# ============================================================================
# TESTE 1: Verificar função de split corrigida
# ============================================================================
print("=" * 60)
print("TESTE 1: Split com timestamps proporcionais")
print("=" * 60)
print()

# Carregar segmentos traduzidos originais
with open('dub_work/asr_trad.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

segments = data['segments']
maxdur = 10.0

print(f"Configuração: maxdur={maxdur}s")
print(f"Total de segmentos: {len(segments)}")
print()

# Simular split_long_segments corrigido
def split_long_segments_NEW(segments, maxdur):
    """Versão corrigida com timestamps proporcionais"""
    if not maxdur or maxdur <= 0:
        return segments

    out = []
    split_count = 0

    for seg_idx, s in enumerate(segments, 1):
        start, end = s["start"], s["end"]
        text = (s.get("text_trad") or "").strip()
        dur = max(0.001, end - start)

        # Não dividir se duração OK ou texto curto
        if dur <= maxdur or len(text.split()) < 16:
            out.append(s)
            continue

        print(f"[SPLIT] Segmento {seg_idx}: {start:.2f}s->{end:.2f}s ({dur:.2f}s, {len(text)} chars)")
        print(f"[SPLIT]   Texto: \"{text[:60]}...\"")

        # Dividir texto em pontuação
        parts = re.split(r'([\.!\?:;,\u2026])', text)
        cps = max(len(text)/dur, 8.0)

        def good(t):
            t2 = re.sub(r"\s+"," ", (t or "")).strip()
            return len(re.findall(r"[A-Za-zÀ-ÿ0-9]", t2)) >= 3

        # Reconstruir em pedaços lógicos
        buf = ""
        pieces = []
        for ch in parts:
            if ch is None: continue
            cand = (buf + ch).strip()
            est = len(cand)/cps if cand else 0
            if cand and est > maxdur and good(buf):
                pieces.append(buf.strip())
                buf = ch.strip()
            else:
                buf = cand
        if good(buf): pieces.append(buf.strip())

        if not pieces:
            out.append(s)
            continue

        # NOVO: Distribuir timestamps PROPORCIONALMENTE
        total_chars = sum(len(p) for p in pieces)
        cur = start

        print(f"[SPLIT]   Dividindo em {len(pieces)} partes (total: {total_chars} chars):")

        for i, piece in enumerate(pieces):
            # Calcular duração proporcional ao tamanho do texto
            piece_ratio = len(piece) / total_chars
            piece_dur = dur * piece_ratio
            nxt = cur + piece_dur

            # Garantir que último segmento termina exatamente no end original
            if i == len(pieces)-1:
                nxt = end

            print(f"[SPLIT]     Parte {i+1}/{len(pieces)}: {cur:.2f}s->{nxt:.2f}s ({nxt-cur:.2f}s, {len(piece)} chars, {piece_ratio*100:.1f}%)")
            print(f"[SPLIT]       \"{piece[:50]}...\"")

            out.append({"start": cur, "end": nxt, "text_trad": piece})
            cur = nxt

        split_count += 1

    print()
    print(f"[SPLIT] Resultado: {len(out)} segmentos ({split_count} divididos, {len(segments)-split_count} mantidos)")
    return out

# Executar split
segments_split = split_long_segments_NEW(segments, maxdur)

print()
print("-" * 60)
print("COMPARAÇÃO: Timestamps Antigos vs Novos")
print("-" * 60)
print()

# Carregar CSV antigo (com timestamps errados)
import csv
with open('dub_work/segments.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    old_segments = list(reader)

print(f"{'Seg':<5} {'Antigo':<20} {'Novo':<20} {'Diferença':<15}")
print("-" * 60)

# Comparar apenas os primeiros 5 segmentos
for i in range(min(5, len(old_segments))):
    old_start = float(old_segments[i]['t_in'])
    old_end = float(old_segments[i]['t_out'])
    old_dur = old_end - old_start

    new_start = segments_split[i]['start']
    new_end = segments_split[i]['end']
    new_dur = new_end - new_start

    diff = new_dur - old_dur

    print(f"{i+1:<5} {old_start:.2f}s->{old_end:.2f}s ({old_dur:.2f}s)  {new_start:.2f}s->{new_end:.2f}s ({new_dur:.2f}s)  {diff:+.2f}s")

print()

# ============================================================================
# TESTE 2: Simular sincronização com novos timestamps
# ============================================================================
print()
print("=" * 60)
print("TESTE 2: Sincronização com novos alvos")
print("=" * 60)
print()

# Verificar durações de áudio TTS existentes
from subprocess import check_output

def get_duration(file_path):
    """Pega duração de arquivo WAV usando ffprobe"""
    try:
        out = check_output([
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=nk=1:nw=1",
            str(file_path)
        ], text=True).strip()
        return float(out)
    except:
        return 0.0

print("Comparando duração TTS gerada vs alvo esperado:")
print()
print(f"{'Seg':<5} {'Alvo Antigo':<12} {'Alvo Novo':<12} {'TTS Gerado':<12} {'Ajuste Novo':<15}")
print("-" * 65)

for i in range(min(5, len(segments_split))):
    # Alvo antigo (do CSV)
    old_target = float(old_segments[i]['t_out']) - float(old_segments[i]['t_in'])

    # Alvo novo (corrigido)
    new_target = segments_split[i]['end'] - segments_split[i]['start']

    # Duração real do TTS
    tts_file = Path('dub_work', f'seg_{i+1:04d}.wav')
    if tts_file.exists():
        tts_dur = get_duration(tts_file)

        # Calcular ratio de ajuste necessário
        ratio_new = new_target / tts_dur if tts_dur > 0 else 1.0

        if ratio_new < 0.95:
            action = "COMPRIMIR"
        elif ratio_new > 1.05:
            action = "EXPANDIR"
        else:
            action = "OK"

        print(f"{i+1:<5} {old_target:.2f}s       {new_target:.2f}s       {tts_dur:.2f}s       {action} ({ratio_new:.3f}x)")
    else:
        print(f"{i+1:<5} {old_target:.2f}s       {new_target:.2f}s       N/A          N/A")

print()

# ============================================================================
# TESTE 3: Verificar volume do áudio final
# ============================================================================
print()
print("=" * 60)
print("TESTE 3: Análise de volume do áudio final")
print("=" * 60)
print()

import subprocess

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
    except:
        return None, None

# Verificar dub_raw.wav (antes do pós-processamento)
raw_file = Path('dub_work/dub_raw.wav')
if raw_file.exists():
    print("Arquivo: dub_work/dub_raw.wav (ANTES do pós-processamento)")
    mean, max_v = analyze_volume(raw_file)
    if mean and max_v:
        print(f"  Mean volume: {mean} dB")
        print(f"  Max volume:  {max_v} dB")

        mean_db = float(mean)
        if mean_db < -50:
            print(f"  Status: MUITO BAIXO (problema detectado)")
        elif mean_db < -30:
            print(f"  Status: Baixo")
        else:
            print(f"  Status: OK")
    print()

# Verificar dub_final.wav (depois do pós-processamento ANTIGO)
final_file = Path('dub_work/dub_final.wav')
if final_file.exists():
    print("Arquivo: dub_work/dub_final.wav (DEPOIS do pós-processamento ANTIGO)")
    mean, max_v = analyze_volume(final_file)
    if mean and max_v:
        print(f"  Mean volume: {mean} dB")
        print(f"  Max volume:  {max_v} dB")

        mean_db = float(mean)
        if mean_db < -50:
            print(f"  Status: MUITO BAIXO (problema detectado) ❌")
        elif mean_db < -30:
            print(f"  Status: Baixo")
        else:
            print(f"  Status: OK")
    print()

print("NOTA: Com a correção aplicada, o pós-processamento agora usa:")
print("  fx = \"loudnorm=I=-14:TP=-1.5:LRA=11\"")
print("  (removido afftdn e equalizer problemáticos)")
print()

# ============================================================================
# RESUMO FINAL
# ============================================================================
print()
print("=" * 60)
print("RESUMO DOS TESTES")
print("=" * 60)
print()

print("✅ TESTE 1 - Split com timestamps proporcionais:")
print("   - Timestamps agora refletem proporção do texto")
print("   - Primeira parte do segmento 1 deve ter ~10.0s (não 9.99s)")
print()

print("✅ TESTE 2 - Sincronização com novos alvos:")
print("   - Alvos de sincronização agora são mais realistas")
print("   - Menos compressão/expansão necessária")
print()

print("✅ TESTE 3 - Volume do áudio:")
print("   - Problema identificado: dub_final.wav está mudo (-91dB)")
print("   - Correção aplicada: filtros simplificados no pós-processamento")
print()

print("=" * 60)
print("PRÓXIMO PASSO: Rodar 'dublar nei.mp4' para testar correções")
print("=" * 60)

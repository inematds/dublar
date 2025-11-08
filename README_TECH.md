# Pipeline de Dublagem TÉCNICA v2.0

## 🎯 Otimizado para Vídeos de Demonstração Técnica

Esta versão é **especializada para conteúdo técnico** como:
- Tutoriais de programação
- Demonstrações de código
- Aulas de desenvolvimento
- Apresentações técnicas
- Code reviews

---

## ✨ Melhorias Específicas para Conteúdo Técnico

### 1. **Glossário de 100+ Termos Técnicos**
Preserva termos que NÃO devem ser traduzidos:
- `string`, `array`, `function`, `class`, `async`, `await`
- `git`, `commit`, `push`, `pull`, `branch`
- `npm`, `docker`, `API`, `JSON`, `HTTP`
- Nomes de linguagens, frameworks, bibliotecas

### 2. **Controle de Comprimento na Tradução**
- Analisa duração do segmento original
- Limita palavras na tradução para caber no tempo
- Evita traduções muito longas que causam dessincronia

### 3. **Simplificação Inteligente**
Remove palavras de enchimento mantendo clareza:
- "você sabe" → removido
- "basicamente" → removido
- "por exemplo" → "ex:"
- "o que eu quero dizer é" → removido

### 4. **Melhor Geração de Traduções**
- `num_beams=5`: tradução mais fluida
- `length_penalty=1.2`: penaliza traduções longas
- `no_repeat_ngram_size=3`: evita repetições

---

## 🚀 Seu Comando Atualizado

### Antes (dublar31.py):
```bash
python dublar31.py --in ccode-dia10.mp4 --src en --tgt pt --tts bark --voice v2/pt_speaker_1 --sync smart --tolerance 0.0 --maxstretch 2.0
```

### Agora (dublar_tech_v2.py):
```bash
python dublar_tech_v2.py --in ccode-dia10.mp4 --src en --tgt pt --tts bark --voice v2/pt_speaker_1 --sync smart --tolerance 0.0 --maxstretch 2.0
```

**É EXATAMENTE O MESMO COMANDO**, apenas muda o nome do arquivo!

---

## 🆕 Novas Opções Disponíveis

### Opção 1: Desativar simplificação (tradução literal completa)
```bash
python dublar_tech_v2.py --in ccode-dia10.mp4 --src en --tgt pt --tts bark --voice v2/pt_speaker_1 --sync smart --tolerance 0.0 --maxstretch 2.0 --no-simplify
```

### Opção 2: Usar modo elastic (melhor redistribuição)
```bash
python dublar_tech_v2.py --in ccode-dia10.mp4 --src en --tgt pt --tts bark --voice v2/pt_speaker_1 --sync elastic --tolerance 0.0 --maxstretch 2.0
```

### Opção 3: Ativar VAD (detectar pausas naturais)
```bash
python dublar_tech_v2.py --in ccode-dia10.mp4 --src en --tgt pt --tts bark --voice v2/pt_speaker_1 --sync smart --tolerance 0.0 --maxstretch 2.0 --enable-vad
```

### RECOMENDADO para demonstrações técnicas:
```bash
python dublar_tech_v2.py --in ccode-dia10.mp4 --src en --tgt pt --tts bark --voice v2/pt_speaker_1 --sync elastic --enable-vad --tolerance 0.0 --maxstretch 2.0
```

---

## 📊 O Que Você Ganha

### Antes (M2M100 puro):
```
Original: "Now we'll import the string module and create an array"
Tradução: "Agora vamos importar o módulo de cordas e criar um arranjo"
❌ Problema: "string" virou "cordas", "array" virou "arranjo"
```

### Depois (versão técnica):
```
Original: "Now we'll import the string module and create an array"
Tradução: "Agora vamos importar o módulo string e criar um array"
✅ Termos técnicos preservados!
```

---

## 🔧 Exemplos de Tradução Técnica

### Exemplo 1: Termos preservados
```
EN: "Let's use async/await with promises in JavaScript"
PT: "Vamos usar async/await com promises em JavaScript"
```

### Exemplo 2: Simplificação automática
```
Original tradução: "Bem, basicamente o que eu quero dizer é que você sabe, nós vamos fazer um loop"
Simplificado: "Vamos fazer um loop"
```

### Exemplo 3: Controle de comprimento
```
Segmento: 3.5 segundos
Original: 15 palavras
Tradução normal: 22 palavras (muito longo!)
Tradução otimizada: 17 palavras (cabe no tempo)
```

---

## 📈 Métricas Adicionais

O CSV agora inclui:
```csv
idx,t_in,t_out,texto_trad,file,estimated_dur,actual_dur,compression_ratio
1,0.0,2.5,"Vamos criar uma função",seg_0001.wav,1.234,1.189,0.85
```

- `compression_ratio`: 0.85 = tradução 15% mais curta (bom!)
- `compression_ratio`: 1.25 = tradução 25% mais longa (pode ser problema)

---

## 🎓 Glossário Completo

### Termos SEMPRE preservados:
```
string, array, boolean, null, undefined, true, false
const, let, var, function, class, return, async, await
git, commit, push, pull, merge, branch
npm, yarn, docker, API, JSON, HTTP, REST
console, log, import, export, callback, props, state
```

### Termos traduzidos corretamente:
```
function    → função
method      → método
variable    → variável
parameter   → parâmetro
loop        → loop (mantido)
database    → banco de dados
repository  → repositório
test        → teste
```

---

## 🛠️ Troubleshooting Específico

### "Termos ainda sendo traduzidos incorretamente"
- Adicione ao conjunto `PRESERVE_TERMS` no código (linha ~75)
- Ou use `--no-simplify` para tradução mais literal

### "Tradução muito curta/cortada"
```bash
--no-simplify  # Desativa simplificação automática
```

### "Tradução muito longa"
- O sistema já limita automaticamente
- Se ainda longo, aumente `--maxstretch` para 2.5

### "Perdi clareza com simplificação"
```bash
--no-simplify  # Mantém tradução completa
```

---

## 📋 Comparação: Normal vs. Técnica

| Aspecto | dublar_sync_v2.py | dublar_tech_v2.py |
|---------|-------------------|-------------------|
| Público | Geral | **Técnico/Programação** |
| Glossário técnico | ❌ | ✅ 100+ termos |
| Preservação de termos | ❌ | ✅ Automática |
| Controle de comprimento | ❌ | ✅ Baseado em duração |
| Simplificação | ❌ | ✅ Opcional |
| Qualidade tradução | Boa | **Melhor (beams=5)** |
| Métricas extras | Básicas | **+ compression_ratio** |

---

## 💡 Dicas para Melhores Resultados

### 1. **Use elastic sync para diálogos técnicos rápidos**
```bash
--sync elastic
```

### 2. **Ative VAD se houver muitas pausas**
```bash
--enable-vad
```

### 3. **Ajuste maxstretch baseado no ritmo**
- Narração lenta: `--maxstretch 1.3`
- Ritmo normal: `--maxstretch 2.0` (seu caso)
- Muito rápido: `--maxstretch 2.5`

### 4. **Teste vozes diferentes**
```bash
--voice v2/pt_speaker_0  # Voz feminina
--voice v2/pt_speaker_1  # Voz masculina 1
--voice v2/pt_speaker_2  # Voz masculina 2
--voice v2/pt_speaker_3  # Voz grave
```

---

## 🔍 Analisando Resultados

Após execução, confira:

1. **`dub_work/asr_trad.json`** - Veja se termos técnicos foram preservados
2. **`dub_work/segments.csv`** - Confira compression_ratio de cada segmento
3. **`dub_work/logs.json`** - Métricas completas de sincronização

### Exemplo de análise:
```json
{
  "compression_ratio": 0.92,  // ✅ Bom! 8% mais curto
  "text_original": "Let's create a new async function",
  "text_trad": "Vamos criar uma nova função async"
}
```

---

## 🎬 Workflow Recomendado

1. **Primeira execução (teste rápido)**
```bash
python dublar_tech_v2.py --in video.mp4 --src en --tgt pt --tts bark --voice v2/pt_speaker_1 --sync smart --tolerance 0.0 --maxstretch 2.0
```

2. **Confira resultados**
- Assista o vídeo dublado
- Verifique `segments.csv` para ver compression_ratio
- Leia `asr_trad.srt` para checar tradução

3. **Ajuste fino (se necessário)**
```bash
# Se tradução muito simplificada:
--no-simplify

# Se ainda dessincronia:
--sync elastic --enable-vad

# Se voz muito rápida:
--maxstretch 1.5
```

---

## 📝 Customização do Glossário

Para adicionar seus próprios termos:

1. Abra `dublar_tech_v2.py`
2. Localize `PRESERVE_TERMS` (linha ~75)
3. Adicione termos:
```python
PRESERVE_TERMS = {
    # ... termos existentes ...
    "react", "vue", "angular",  # Seus frameworks
    "redux", "hooks",           # Suas libs
    "typescript",               # Suas linguagens
}
```

---

## ✅ Checklist de Qualidade

Após dublar, confira:

- [ ] Termos técnicos preservados (string, array, etc.)
- [ ] Nomes de funções/variáveis não traduzidos
- [ ] Sincronização aceitável (offset médio < 0.3s)
- [ ] Voz natural (sem acelerações extremas)
- [ ] Áudio limpo (sem pulos ou cortes)
- [ ] Legendas corretas

---

## 🎯 Resumo

Para seus vídeos de demonstração técnica:

**Comando básico (igual ao anterior, só muda o arquivo):**
```bash
python dublar_tech_v2.py --in ccode-dia10.mp4 --src en --tgt pt --tts bark --voice v2/pt_speaker_1 --sync smart --tolerance 0.0 --maxstretch 2.0
```

**Ganhos automáticos:**
✅ Preserva termos técnicos
✅ Tradução mais curta (cabe no tempo)
✅ Remove palavras de enchimento
✅ Melhor qualidade de tradução
✅ Métricas detalhadas

**Sem precisar mudar NADA no comando!**

# Prompt — Phase 4A supplement: Cynic sub-type tagging (v1.0)

**Model:** claude-haiku-4-5-20251001  
**Temperature:** 0.1  
**Max output tokens:** 200  
**Use prompt cache:** yes

Supervisor carry-forward 2026-05-21: re-classify each existing Cynical-Reactive
candidate quote into one of three sub-types so the memo can lead with the
defining institutional cynicism, use personal-tragedy quotes sparingly, and
exclude gambling/off-topic corpus-edge quotes.

This step does NOT extract new quotes. It only tags existing ones.

---

## System prompt

Você está classificando citações de um cluster "cynical-reactive" de
investidores brasileiros no Reddit. Cada citação foi extraída de um post
específico; você recebe a citação e o texto do post para contexto.

Sua tarefa: atribuir UM sub-tipo a cada citação, escolhendo entre as quatro
categorias abaixo. Use o CONTEXTO do post inteiro para julgar — a citação
isoladamente pode ser ambígua.

CATEGORIAS:

1. **`institutional_cynicism`** — postura cínica/irônica/desconfiada direcionada
   ao SISTEMA FINANCEIRO: gurus de mercado, influenciadores, corretoras,
   bancos, governo, "hustle culture", promessas de enriquecimento fácil,
   manipulação de mercado, esquemas duvidosos. Esta é a postura *definidora*
   do cluster cynical-reactive. Exemplos do padrão:
   - "Não confio em assessor que ganha comissão"
   - "Mais um curso de 'fique rico em 30 dias'"
   - "Invista R$1.000 e depois de 1 mês pegue seus R$1.000 de volta!" (zombando
     de promessas vazias)
   - Crítica a Ferri, Primo, gurus do mercado
   - Crítica ao Banco Central, governo, instituições

2. **`personal_crisis`** — narrativa de TRAGÉDIA PESSOAL/FAMILIAR financeira:
   perda concreta de dinheiro próprio ou da família, casa vendida, pai que
   ignorou conselhos, mãe sem casa, dívida acumulada, score crashou, etc.
   Quotes vívidas mas que não capturam a postura *definidora* do cluster —
   são a "cauda dramática". Use com cuidado e respeito; pessoas em sofrimento
   real. Exemplos do padrão:
   - "Mendigo digital"
   - "vendeu a casa da mãe e trapeu ela em um apartamento financiado"
   - "Score caiu de 800 para 400"
   - "Perdi tudo no tigrinho"
   - Pai/irmão/amigo perdendo dinheiro e narrador impotente

3. **`gambling_offtopic`** — citações cuja fonte é jogo de azar / apostas
   esportivas / "tigrinho" / slots online / esquemas claramente fora do escopo
   de investimento. Estes são corpus-edge — entraram no cluster porque a
   postura linguística é similar, mas não representam investidores. EXCLUIR
   dos candidatos do memo. Exemplos do padrão:
   - "perdi no tigrinho"
   - "nunca mais aposto em jogo"
   - "casa de apostas me roubou"
   - "esse robô do PIX"

4. **`other`** — não se encaixa claramente em 1–3. Use com parcimônia; tente
   classificar em 1, 2 ou 3 primeiro.

CRITÉRIO DE DECISÃO:
- Se a citação E o contexto do post mostram crítica/desconfiança ao sistema
  financeiro como tema central → `institutional_cynicism`.
- Se a citação E o contexto mostram tragédia financeira pessoal/familiar como
  tema central → `personal_crisis`.
- Se a citação OU o contexto envolvem jogos de azar / apostas esportivas /
  slots / esquemas de PIX-rico → `gambling_offtopic` (regra de exclusão).
- Se uma citação é institucional-cínica mas o thread também menciona perda
  pessoal, classifique pela *temática dominante* da citação isolada, não do
  thread inteiro.

FORMATO DE SAÍDA — APENAS JSON:

```json
{
  "subtype": "institutional_cynicism" | "personal_crisis" | "gambling_offtopic" | "other",
  "rationale_en": "<one short English sentence (≤20 words) explaining the choice>"
}
```

---

## User-message template

```
CITAÇÃO A CLASSIFICAR:
"{quote_text}"

CONTEXTO DO POST DE ORIGEM (para desambiguar):
<<<
{unit_text}
>>>

Classifique a citação em um sub-tipo. Apenas JSON.
```

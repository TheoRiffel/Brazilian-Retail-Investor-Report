# Phase 1 Summary — Open Coding & Attribute Schema Design

**Date:** 2026-05-20  
**Status: READY FOR SUPERVISOR REVIEW**  
**Phase 2 is blocked until supervisor approves the schema.**

---

## 1. Pipeline Summary

| Task | Description | Result |
|------|-------------|--------|
| 1 | Build eligible author-thread units | 15,883 r/investimentos + 36,322 r/farialimabets = 52,205 total |
| 2 | Stratified mini-sample (50 per cell) | **300 threads** across 6 cells |
| 3 | Open coding via Claude Haiku 4.5 | **300/300 coded, 0 failures** |
| 4 | Schema synthesis via Claude Sonnet 4.6 | **14-field schema** produced |
| 5 | Programmatic sanity checks | **7/7 checks passed** |

**Phase 1 LLM cost:** $1.69 total (Task 3: $0.97, Task 4: $0.31, retries: $0.31)  
**Tokens:** 448,230 input / 151,947 output

---

## 2. Sample Composition (Task 2)

| Cell | Subreddit | Window | Eligible | Sampled | Mean unit len (chars) | Mean comments |
|------|-----------|--------|----------|---------|----------------------|---------------|
| investimentos_WA | r/investimentos | 2020-06 – 2021-06 | 3,326 | 50 | 1,956 | 18 |
| investimentos_WB | r/investimentos | 2022-01 – 2023-01 | 3,597 | 50 | 1,824 | 22 |
| investimentos_WC | r/investimentos | 2024-01 – 2024-12 | 8,960 | 50 | 1,687 | 13 |
| farialimabets_WA | r/farialimabets | 2020-06 – 2021-06 | 2,663 | 50 | 1,007 | 13 |
| farialimabets_WB | r/farialimabets | 2022-01 – 2023-01 | 11,853 | 50 | 874 | 20 |
| farialimabets_WC | r/farialimabets | 2024-01 – 2024-12 | 21,806 | 50 | 1,070 | 43 |
| **Total** | | | **52,205** | **300** | | |

**Sampling strategy (per cell):** 15 top-quartile by num_comments + 15 mid-tier (p10–median) + 20 uniform random; seed=42.

**Notable:** r/farialimabets unit texts are shorter (~900–1070 chars) because many are link posts with top-10 comments rather than long selftexts. r/investimentos threads are richer in body text (~1700–1960 chars). WC farialimabets has the highest engagement (43 mean comments) reflecting platform growth.

---

## 3. Top Dimensions Emerging from Open Coding (Task 3)

1861 free-text dimension entries across 300 threads. Ranked by estimated mention frequency (from schema synthesis justificativas):

| Rank | Dimension (emergent label) | Estimated mentions | Notes |
|------|---------------------------|-------------------|-------|
| 1 | Sofisticação técnica financeira | ~300 (near-universal) | Anchors all other dimensions |
| 2 | Estado emocional predominante | ~200 | Dominant in farialimabets; cynicism as defense mechanism |
| 3 | Tolerância a risco | ~180 | Often diverges from declared preference |
| 4 | Fonte primária de informação | ~160 | YouTube influencers vs. first-principles reading |
| 5 | Estratégia de investimento principal | ~150 | Dividends/buy-hold most common in investimentos |
| 6 | Objetivo financeiro primário | ~140 | IF/aposentadoria vs. reserva vs. renda passiva |
| 7 | Fase de acumulação patrimonial | ~120 | Wide range: R$50 de estagiário to R$7M em imóvel |
| 8 | Ceticismo institucional | ~120 | Strong in farialimabets; present across both subs |
| 9 | Relação com instituições financeiras | ~100 | Bancão vs. corretora migration |
| 10 | Exposição a cripto e especulação | ~100 | Includes day trade, NFTs, apostas |
| 11 | Relação com Selic / renda fixa | ~90 | Brazil-specific anchor; attitude not just knowledge |
| 12 | Vínculo empregatício e renda | ~80 | CLT vs. PJ is fiscally consequential |
| 13 | Perfil tributário e fiscal | ~80 | DARF, carnê-leão, isenção 20k, PGBL/VGBL |
| 14 | Relação com imóvel e herança | ~60 | Transition from illiquid real estate is a distinct trigger |

---

## 4. Proposed Schema (Task 4)

**Schema version:** 1.0  
**Fields:** 14  
**Discarded dimensions:** 7 (see Section 6)

| # | name | tipo | valores (summary) | desconhecido? |
|---|------|------|-------------------|---------------|
| 1 | `sofisticacao_tecnica` | ordinal 1–5 | 1=desconhece básico … 5=nível institucional/automação | não |
| 2 | `fase_acumulacao` | categorical | pre_inicio / acumulacao_inicial / acumulacao_ativa / consolidacao / distribuicao_renda_passiva / preservacao_patrimonial | sim |
| 3 | `estrategia_principal` | categorical | renda_fixa_conservadora / dividendos_buy_hold / growth_valorizacao / especulacao_curto_prazo / investimento_exterior / imobiliario_direto_ou_fii / sem_estrategia_definida | sim |
| 4 | `tolerancia_risco_declarada_ou_inferida` | ordinal 1–5 | 1=evita qualquer volatilidade … 5=all-in especulativo | não |
| 5 | `relacao_com_selic_e_renda_fixa` | categorical | ancora_principal / reserva_e_transicao / obstaculo_a_superar / indiferente_ou_desconhece / otimizador_ativo | sim |
| 6 | `perfil_tributario_e_fiscal` | categorical | desconhece_ou_ignora / conformidade_basica / otimizador_fiscal / cross_border_ou_pj / evasao_ou_zona_cinzenta | sim |
| 7 | `relacao_com_imovel_e_heranca` | categorical | sem_exposicao_ou_irrelevante / imovel_como_moradia_apenas / imovel_como_investimento_ativo / planejamento_sucessorio_relevante / transicao_imovel_para_financeiro | sim |
| 8 | `relacao_com_instituicoes_financeiras` | categorical | dependente_de_bancao / migrando_para_corretora / multiplaforma_ativo / desconfiado_de_todos / diy_sem_intermediario | sim |
| 9 | `estado_emocional_predominante` | categorical | ansioso_ou_inseguro / confiante_ou_assertivo / frustrado_ou_resignado / euforico_ou_impulsivo / cinico_ou_ironico / curioso_ou_exploratorio / equilibrado_ou_neutro | sim |
| 10 | `fonte_primaria_de_informacao` | categorical | comunidade_online_forum / influenciadores_youtube_instagram / assessor_ou_profissional / analise_propria_e_fontes_primarias / familia_ou_rede_proxima / sem_fonte_estruturada | sim |
| 11 | `vinculo_empregaticio_e_renda` | categorical | clt_empregado / servidor_publico / pj_autonomo_mei / empresario_socio / renda_exterior_ou_remoto_internacional / sem_renda_ou_dependente / aposentado_ou_rentista | sim |
| 12 | `objetivo_financeiro_primario` | categorical | reserva_de_emergencia / compra_de_imovel / aposentadoria_independencia_financeira / renda_passiva_imediata / acumulacao_sem_objetivo_claro / educacao_ou_projeto_especifico / sucessao_ou_doacao_familiar | sim |
| 13 | `ceticismo_institucional` | ordinal 1–5 | 1=confia plenamente … 5=ceticismo radical/evasão legítima | não |
| 14 | `exposicao_a_cripto_e_especulacao` | ordinal 1–5 | 1=nenhuma/rejeita … 5=all-in shitcoins/cassino | sim |

Full schema with anchors and justificativas: `data/interim/phase1_proposed_schema.json`

---

## 5. Sanity Check Results (Task 5)

7/7 checks passed:

| Check | Result | Value |
|-------|--------|-------|
| field_count (8–15) | ✓ PASS | 14 fields |
| required_keys present on all fields | ✓ PASS | no issues |
| no_duplicate_names | ✓ PASS | no duplicates |
| has_emotional_field | ✓ PASS | `estado_emocional_predominante` |
| has_capital_field | ✓ PASS | `fase_acumulacao` (patrimônio/capital) |
| has_goal_field | ✓ PASS | `objetivo_financeiro_primario` |
| has_brazil_specific_field | ✓ PASS | `relacao_com_selic_e_renda_fixa`, `perfil_tributario_e_fiscal` |

---

## 6. Discarded Dimensions

| Name | Reason |
|------|--------|
| horizonte_temporal_declarado | Redundant with fase_acumulacao + objetivo_financeiro_primario |
| capital_absoluto | Rarely explicit; noisy as continuous; captured by fase_acumulacao |
| uso_de_previdencia_privada | <30 mentions; absorbed by perfil_tributario_e_fiscal + objetivo |
| genero_e_composicao_familiar | Low extractability; contextual only; not LLM-reliable |
| engajamento_politico | Topic not person attribute; collinear with ceticismo_institucional |
| orientacao_educativa_ou_mentor | <20 mentions; captured by sofisticacao_tecnica + ceticismo |
| uso_de_alavancagem | Subset of exposicao_a_cripto_e_especulacao + tolerancia_risco |

---

## 7. Researcher Notes (from LLM schema synthesis)

> **TENSÕES PRINCIPAIS:**
>
> **(1) sofisticacao_tecnica vs ceticismo_institucional:** há correlação positiva moderada (quem sabe mais tende a desconfiar mais), mas existem iniciantes altamente céticos (desconfiança emocional sem base técnica) e especialistas confiantes em assessores. Manter separados é correto mas o LLM pode confundir ao extrair — recomendar exemplos de calibração no prompt de extração.
>
> **(2) estado_emocional_predominante** é o campo mais subjetivo e o mais rico: `cinico_ou_ironico` domina o r/farialimabets e pode mascarar ansiedade real (humor como mecanismo de defesa). Instruir o LLM a priorizar comportamento descrito sobre tom superficial.
>
> **(3) estrategia_principal e objetivo_financeiro_primario** têm sobreposição parcial (quem quer renda passiva tende a usar dividendos/FIIs), mas são dimensões ortogonais: objetivo captura "para quê" e estratégia captura "como". Manter separados é essencial para clustering.
>
> **(4) Viés de seleção do corpus:** r/farialimabets é dominado por ceticismo alto, humor e especulação; r/investimentos tem perfis mais sérios e iniciantes. Recomendo criar variável de metadado `subreddit_origem` fora do esquema de atributos de pessoa para controlar esse viés no clustering.
>
> **(5) relacao_com_imovel_e_heranca** pode ter baixa extratibilidade em postagens curtas — marcar como opcional com desconhecido permitido foi a decisão correta.
>
> **(6) identidade_de_grupo** (farialimer, boglehead, bastteriano, holder) foi fundida em fonte_primaria_de_informacao + estrategia_principal para evitar proliferação. Supervisor deve avaliar se identidade de comunidade merece campo próprio em v1.1.
>
> **(7) exposicao_a_cripto_e_especulacao mantida separada de tolerancia_risco** deliberadamente: há investidores conservadores em ações com 5% em Bitcoin (tolerância 2, exposição 2) e day traders de ações sem cripto (tolerância 5, exposição 1). A separação é empiricamente justificada pelo corpus.

---

## 8. Sample Threads with Full Coding Output

### Thread 1 — r/investimentos WC (2024), exploratory

**Thread ID:** 1arim50  
**Unit text (first 600 chars):**
```
IA de investimento

existe alguma inteligência artificial de investimento? mesmo que ela só simule e não que dê dicas de investimento

--- Top comments ---
[score 10] Urubu do pix é uma ótima IA de incestimento
[score 9] Estudo IA há muito anos e eu não faria isso. O ponto forte da IA hoje é aprender com dados passados para prever/gerar/simular o futuro. Sabemos que isso não é uma boa ideia no mundo dos investimentos.
[score 7] Vixi tem um monte, já tinha um monte de robo-advisors faz uns 20 anos, agora virou qse tudo ai-advisors...
```

**Open coding output:**
```json
{
  "situacao_resumida": "Investidor iniciante ou curioso que busca conhecer se existem ferramentas de IA para simular ou auxiliar investimentos, sem necessariamente esperar recomendações diretas.",
  "dimensoes_observadas": [
    "Nível de sofisticação técnica baixo a médio — pergunta sobre IA de forma genérica, sem conhecimento prévio de robo-advisors",
    "Postura exploratória e cautelosa — quer simular antes de agir, não quer conselhos diretos",
    "Ceticismo moderado — questiona a viabilidade de IA em investimentos, mas está aberto a aprender",
    "Foco em educação/compreensão — parece querer entender a ferramenta antes de usar",
    "Baixa exposição a produtos financeiros tecnológicos — desconhecimento de robo-advisors existentes há 20 anos"
  ],
  "dor_principal": "Incerteza sobre se existem ferramentas de IA confiáveis para investimento e dúvida sobre a viabilidade de usar IA nesse contexto.",
  "tema_principal": "Busca por ferramentas de IA para investimento",
  "notas": "Os comentários revelam tensão entre a existência real de robo-advisors/AI-advisors e o ceticismo sobre sua eficácia. A pessoa parece estar em fase de descoberta."
}
```

---

### Thread 2 — r/farialimabets WB (2022–2023), cynical/humor

**Thread ID:** upjxur  
**Unit text (first 600 chars):**
```
Minha esposa fez uma música depois da nossa briga por causa das NFTs

[link post]

--- Top comments ---
[score 10] Cheirinho de incell
[score 9] Erro juvenil…. Aqui em casa a minha não faz ideia do tamanho do meu LOSS.
[score 8] Aqui ninguém tá de brincadeira, casar é o maior LOSS possível.
[score 7] Kkkkkk casei, multipliquei minha renda em 4x no meio tempo e ainda acho que quando era solteiro eu tinha mais dinheiro.
```

**Open coding output:**
```json
{
  "situacao_resumida": "Um investidor casado que teve uma briga com sua esposa sobre investimentos em NFTs, e ela respondeu criando uma música sobre o assunto. A postagem parece ser mais uma brincadeira/desabafo humorístico sobre conflitos conjugais relacionados a decisões financeiras de risco.",
  "dimensoes_observadas": [
    "Tolerância a risco elevada — investe em NFTs, ativo de alta volatilidade e especulativo",
    "Sofisticação técnica moderada — conhece NFTs mas pode estar em fase inicial de aprendizado",
    "Dinâmica conjugal tensa em relação a decisões financeiras — esposa desaprova ou questiona investimentos",
    "Postura emocional leve/humorística — transforma conflito em piada, busca validação com humor",
    "Visão de casamento como 'perda financeira' — perspectiva cínica sobre impacto econômico do matrimônio",
    "Comunidade de pares com valores similares — busca validação em fórum de investidores que compartilham frustração com cônjuges"
  ],
  "dor_principal": "Conflito conjugal sobre decisões de investimento de risco, com sensação de que o casamento limita liberdade financeira e oportunidades especulativas.",
  "tema_principal": "Conflito conjugal e NFTs",
  "notas": "A postagem é leve/humorística mas revela tensão real. Há também cinismo sobre casamento como 'loss' financeiro. A dinâmica sugere que a esposa representa a voz da aversão ao risco/segurança."
}
```

---

### Thread 3 — r/investimentos WC (2024), early-stage with dor

**Thread ID:** 1akbstl  
**Unit text (first 600 chars):**
```
Qualquer centavo conta?

Oi galera, me ajudem aqui por favor, tenho meu salário de estagiário, meu pai é autônomo e as vezes recebe pagamento via pix e coloca na minha conta por preguiça de mexer na conta dele e minha mãe recebe dinheiro de alguns primos para comprar remédios para minha tia que precisa. Com isso costumo ficar com uns 3k na conta parado por alguns dias todo mês, é possível investir em algo rápido tipo CDB ou poupança de cartão para ganhar algo durante esse tempo ou nem vale a pena o esforço por sei lá, 20 centavos provavelmente?
```

**Open coding output:**
```json
{
  "situacao_resumida": "Estagiário que recebe salário próprio e ocasionalmente guarda dinheiro de terceiros em sua conta, acumulando cerca de 3k parados alguns dias por mês, questionando se vale a pena investir esse valor temporário em produtos de renda fixa.",
  "dimensoes_observadas": [
    "Capital muito reduzido e temporário (3k em períodos curtos)",
    "Renda instável e compartilhada (salário de estagiário + depósitos de familiares)",
    "Baixa sofisticação financeira (questiona se 'centavos' valem a pena, desconhece custos de transação e impostos)",
    "Mentalidade de aproveitar 'tudo' mesmo que mínimo (otimismo ingênuo sobre pequenos ganhos)",
    "Situação financeira familiar complexa (pai autônomo, mãe gerenciando dinheiro de terceiros para medicamentos)",
    "Falta de clareza sobre liquidez necessária (não considera que o dinheiro pode ser sacado a qualquer momento)",
    "Postura pragmática mas inexperiente (busca solução rápida sem entender implicações)"
  ],
  "dor_principal": "Sensação de desperdício ao deixar dinheiro parado sem render, mesmo que o ganho seja mínimo.",
  "tema_principal": "Micro-investimento com capital temporário",
  "notas": "A comunidade foi bastante crítica, apontando que o risco operacional supera em muito o ganho potencial. Há também uma questão implícita de compliance (justificar movimentações)."
}
```

---

## 9. Supervisor Review Checklist

Before approving for Phase 2, please review:

- [ ] **Schema completeness:** Are there important dimensions you expected that are missing?
- [ ] **Granularity:** Is the ordinal 1–5 scale appropriate for `sofisticacao_tecnica`, `tolerancia_risco`, `ceticismo_institucional`, `exposicao_a_cripto`? Or should any be collapsed to 3-point?
- [ ] **LLM extractability:** For Phase 2, each field will be extracted via a single LLM call per thread. Flag any fields that seem hard to infer from Reddit posts.
- [ ] **`identidade_de_grupo`:** The LLM noted this was discarded (farialimer, boglehead, bastteriano). Should it be reinstated as a v1.1 field?
- [ ] **`subreddit_origem`:** LLM recommends adding this as a metadata field (not an attribute) in the Phase 2 dataset to control corpus bias. Agree?
- [ ] **`relacao_com_imovel_e_heranca`:** Low extractability in short posts. Keep with `permite_desconhecido=true`, or remove?
- [ ] **`perfil_tributario_e_fiscal` value `evasao_ou_zona_cinzenta`:** Present in ~15 notes. Ethically appropriate to code this in Phase 2? Confirm.
- [ ] **Cost acceptance:** Phase 2 (extracting 14 fields × 300 threads) will be ~$X. Approve budget?

**→ Awaiting supervisor review before proceeding to Phase 2.**

# Phase 2 Calibration Report

**Date:** 2026-05-20  
**Status: AWAITING SUPERVISOR REVIEW — do not proceed to full extraction**

---

## 1. Parse Success & Cost

| Metric | Value |
|--------|-------|
| Threads attempted | 102 |
| Parse successes | 102 (100.0%) |
| Parse failures | 0 |
| Total input tokens | 667,052 |
| Total output tokens | 28,707 |
| Estimated cost (calibration) | $0.8106 |
| Model | claude-haiku-4-5-20251001 |
| Temperature | 0.1 |

---

## 2. Field Value Distributions

### 2a. Ordinal Fields (value counts)

**ceticismo_institucional**

| Value | Count | % |
|-------|-------|---|
| 1 | 8 | 7.8% |
| 2 | 38 | 37.3% |
| 3 | 37 | 36.3% |
| 4 | 18 | 17.6% |
| 5 | 1 | 1.0% |

**confianca_extracao**

| Value | Count | % |
|-------|-------|---|
| 1 | 14 | 13.7% |
| 2 | 26 | 25.5% |
| 3 | 41 | 40.2% |
| 4 | 21 | 20.6% |

**exposicao_a_cripto_e_especulacao**

| Value | Count | % |
|-------|-------|---|
| 1 | 73 | 71.6% |
| 2 | 8 | 7.8% |
| 3 | 5 | 4.9% |
| 4 | 6 | 5.9% |
| 5 | 9 | 8.8% |
| desconhecido | 1 | 1.0% |

**identidade_comunitaria**

| Value | Count | % |
|-------|-------|---|
| 1 | 43 | 42.2% |
| 2 | 17 | 16.7% |
| 3 | 17 | 16.7% |
| 4 | 20 | 19.6% |
| 5 | 5 | 4.9% |

**sofisticacao_tecnica**

| Value | Count | % |
|-------|-------|---|
| 1 | 35 | 34.3% |
| 2 | 45 | 44.1% |
| 3 | 22 | 21.6% |

**tolerancia_risco_declarada_ou_inferida**

| Value | Count | % |
|-------|-------|---|
| 1 | 15 | 14.7% |
| 2 | 40 | 39.2% |
| 3 | 21 | 20.6% |
| 4 | 11 | 10.8% |
| 5 | 15 | 14.7% |

### 2b. Categorical Fields (value counts)

**fase_acumulacao**

| Value | Count | % |
|-------|-------|---|
| desconhecido | 32 | 31.4% |
| acumulacao_ativa | 25 | 24.5% |
| pre_inicio | 19 | 18.6% |
| acumulacao_inicial | 16 | 15.7% |
| consolidacao | 10 | 9.8% |

**estrategia_principal**

| Value | Count | % |
|-------|-------|---|
| desconhecido | 25 | 24.5% |
| sem_estrategia_definida | 23 | 22.5% |
| especulacao_curto_prazo | 17 | 16.7% |
| dividendos_buy_hold | 13 | 12.7% |
| renda_fixa_conservadora | 10 | 9.8% |
| growth_valorizacao | 5 | 4.9% |
| investimento_exterior | 4 | 3.9% |
| imobiliario_direto_ou_fii | 4 | 3.9% |
| acumulacao_sem_objetivo_claro | 1 | 1.0% |

**relacao_com_selic_e_renda_fixa**

| Value | Count | % |
|-------|-------|---|
| desconhecido | 75 | 73.5% |
| ancora_principal | 8 | 7.8% |
| indiferente_ou_desconhece | 7 | 6.9% |
| obstaculo_a_superar | 5 | 4.9% |
| reserva_e_transicao | 4 | 3.9% |
| otimizador_ativo | 3 | 2.9% |

**perfil_tributario_e_fiscal**

| Value | Count | % |
|-------|-------|---|
| desconhecido | 72 | 70.6% |
| desconhece_ou_ignora | 14 | 13.7% |
| conformidade_basica | 11 | 10.8% |
| evasao_ou_zona_cinzenta | 3 | 2.9% |
| otimizador_fiscal | 2 | 2.0% |

**relacao_com_imovel_e_heranca**

| Value | Count | % |
|-------|-------|---|
| desconhecido | 94 | 92.2% |
| imovel_como_investimento_ativo | 6 | 5.9% |
| planejamento_sucessorio_relevante | 1 | 1.0% |
| imovel_como_moradia_apenas | 1 | 1.0% |

**relacao_com_instituicoes_financeiras**

| Value | Count | % |
|-------|-------|---|
| desconhecido | 68 | 66.7% |
| migrando_para_corretora | 14 | 13.7% |
| dependente_de_bancao | 8 | 7.8% |
| desconfiado_de_todos | 7 | 6.9% |
| multiplaforma_ativo | 3 | 2.9% |
| diy_sem_intermediario | 2 | 2.0% |

**estado_emocional_predominante**

| Value | Count | % |
|-------|-------|---|
| curioso_ou_exploratorio | 28 | 27.5% |
| cinico_ou_ironico | 21 | 20.6% |
| ansioso_ou_inseguro | 19 | 18.6% |
| euforico_ou_impulsivo | 15 | 14.7% |
| frustrado_ou_resignado | 13 | 12.7% |
| equilibrado_ou_neutro | 3 | 2.9% |
| desconhecido | 3 | 2.9% |

**fonte_primaria_de_informacao**

| Value | Count | % |
|-------|-------|---|
| comunidade_online_forum | 85 | 83.3% |
| analise_propria_e_fontes_primarias | 6 | 5.9% |
| sem_fonte_estruturada | 5 | 4.9% |
| influenciadores_youtube_instagram | 3 | 2.9% |
| desconhecido | 3 | 2.9% |

**vinculo_empregaticio_e_renda**

| Value | Count | % |
|-------|-------|---|
| desconhecido | 84 | 82.4% |
| clt_empregado | 8 | 7.8% |
| pj_autonomo_mei | 4 | 3.9% |
| sem_renda_ou_dependente | 3 | 2.9% |
| empresario_socio | 2 | 2.0% |
| renda_exterior_ou_remoto_internacional | 1 | 1.0% |

**objetivo_financeiro_primario**

| Value | Count | % |
|-------|-------|---|
| desconhecido | 44 | 43.1% |
| acumulacao_sem_objetivo_claro | 42 | 41.2% |
| renda_passiva_imediata | 7 | 6.9% |
| reserva_de_emergencia | 6 | 5.9% |
| aposentadoria_independencia_financeira | 3 | 2.9% |

---

## 3. Desconhecido Rate by Field & Subreddit

Fields with >70% desconhecido rate flagged with ⚠️ (pre-registered threshold).

| Field | Overall % desconh | r/investimentos % | r/farialimabets % | Flag |
|-------|-------------------|-------------------|-------------------|------|
| fase_acumulacao | 31.4% | 11.8% | 51.0% |  |
| estrategia_principal | 24.5% | 13.7% | 35.3% |  |
| relacao_com_selic_e_renda_fixa | 73.5% | 62.7% | 84.3% | ⚠️ >70% |
| perfil_tributario_e_fiscal | 70.6% | 58.8% | 82.4% | ⚠️ >70% |
| relacao_com_imovel_e_heranca | 92.2% | 88.2% | 96.1% | ⚠️ >70% |
| relacao_com_instituicoes_financeiras | 66.7% | 54.9% | 78.4% |  |
| estado_emocional_predominante | 2.9% | 0.0% | 5.9% |  |
| fonte_primaria_de_informacao | 2.9% | 0.0% | 5.9% |  |
| vinculo_empregaticio_e_renda | 82.4% | 82.4% | 82.4% | ⚠️ >70% |
| objetivo_financeiro_primario | 43.1% | 21.6% | 64.7% |  |
| identidade_comunitaria | 0.0% | 0.0% | 0.0% |  |
| tolerancia_risco_declarada_ou_inferida | 0.0% | 0.0% | 0.0% |  |
| exposicao_a_cripto_e_especulacao | 1.0% | 0.0% | 2.0% |  |
| ceticismo_institucional | 0.0% | 0.0% | 0.0% |  |
| sofisticacao_tecnica | 0.0% | 0.0% | 0.0% |  |

---

## 4. Emotional Distribution by Subreddit

Key calibration check: does r/farialimabets show emotional variety, not just cinico_ou_ironico collapse?

**r/investimentos** (n=51)

| Emotion | Count | % |
|---------|-------|---|
| curioso_ou_exploratorio | 24 | 47.1% |
| ansioso_ou_inseguro | 14 | 27.5% |
| frustrado_ou_resignado | 6 | 11.8% |
| equilibrado_ou_neutro | 3 | 5.9% |
| cinico_ou_ironico | 2 | 3.9% |
| euforico_ou_impulsivo | 2 | 3.9% |

**r/farialimabets** (n=51)

| Emotion | Count | % |
|---------|-------|---|
| cinico_ou_ironico | 19 | 37.3% |
| euforico_ou_impulsivo | 13 | 25.5% |
| frustrado_ou_resignado | 7 | 13.7% |
| ansioso_ou_inseguro | 5 | 9.8% |
| curioso_ou_exploratorio | 4 | 7.8% |
| desconhecido | 3 | 5.9% |

---

## 5. Self-Confidence Distribution (confianca_extracao)

| Score | Count | % |
|-------|-------|---|
| 1 | 14 | 13.7% |
| 2 | 26 | 25.5% |
| 3 | 41 | 40.2% |
| 4 | 21 | 20.6% |

Mean confidence: 2.68  Median: 3.0

---

## 6. Ten Full Extraction Outputs (for manual review)

Includes at least 2 r/farialimabets threads for humor-masking verification.

### Example 1 — l6j4v4 (farialimabets_A)

**unit_text (first 600 chars):**
```
Único filme possível pra hoje

[link post]

--- Top comments ---
[score 4] Quero saber quem vai fazer o The Game Short
[score 3] Não é bem fundo imobiliário, mas tua lógica tá no caminho certo.

 Eles viram que os fundos baseados no mercado imobiliário e nas hipotecas eram um castelo de cartas cheio de fraude na montagem de produtos criados por bancos, em aprovação de empréstimos sem conferir créditos e nas precificações. E tava começando a dar sinais que ia desmoronar. 

Então eles abriram posição de short contra os fundos, que funciona da mesma forma que short contra ações. Quando o mercado 
```

**Extracted attributes:**
```json
{
  "sofisticacao_tecnica": 2,
  "fase_acumulacao": "desconhecido",
  "estrategia_principal": "desconhecido",
  "tolerancia_risco_declarada_ou_inferida": 2,
  "relacao_com_selic_e_renda_fixa": "desconhecido",
  "perfil_tributario_e_fiscal": "desconhecido",
  "relacao_com_imovel_e_heranca": "desconhecido",
  "relacao_com_instituicoes_financeiras": "desconhecido",
  "estado_emocional_predominante": "curioso_ou_exploratorio",
  "fonte_primaria_de_informacao": "comunidade_online_forum",
  "vinculo_empregaticio_e_renda": "desconhecido",
  "objetivo_financeiro_primario": "desconhecido",
  "ceticismo_institucional": 3,
  "exposicao_a_cripto_e_especulacao": 1,
  "identidade_comunitaria": 1,
  "confianca_extracao": 2
}
```

### Example 2 — kufitd (farialimabets_A)

**unit_text (first 600 chars):**
```
Vou ter que abrir conta lá fora pra perder dinheiro com isso? Não tem nem uma BDR?

[link post]

--- Top comments ---
[score 2] os gringos também tão comprando call de VALE.... Particularmente vou half in em NIO com todos meus dolares
[score 2] [Mais um pouco sobre ela ](https://www.bbc.com/portuguese/internacional-54462250)
[score 2] Abre uma conta na Avenue e já era. Desvantagem só é que não tem opções
[score 2] Baniram esse cara no r/wallstreetbets , parece que ele só queria levantar o preço disso aí.

https://www.reddit.com/r/wallstreetbets/comments/kuhibq/wallstreetsbets_getting_infiltrat
```

**Extracted attributes:**
```json
{
  "sofisticacao_tecnica": 2,
  "fase_acumulacao": "desconhecido",
  "estrategia_principal": "especulacao_curto_prazo",
  "tolerancia_risco_declarada_ou_inferida": 4,
  "relacao_com_selic_e_renda_fixa": "desconhecido",
  "perfil_tributario_e_fiscal": "desconhecido",
  "relacao_com_imovel_e_heranca": "desconhecido",
  "relacao_com_instituicoes_financeiras": "migrando_para_corretora",
  "estado_emocional_predominante": "cinico_ou_ironico",
  "fonte_primaria_de_informacao": "comunidade_online_forum",
  "vinculo_empregaticio_e_renda": "desconhecido",
  "objetivo_financeiro_primario": "desconhecido",
  "ceticismo_institucional": 3,
  "exposicao_a_cripto_e_especulacao": 3,
  "identidade_comunitaria": 4,
  "confianca_extracao": 2
}
```

### Example 3 — l8ssfd (farialimabets_A)

**unit_text (first 600 chars):**
```
Difíceis verdades

[link post]

--- Top comments ---
[score 21] O jogo não foi feito para gente ganhar.
[score 8] Desculpa q sinceridade, mas antes desse episódio com o wallstreetbets, não havia esse povo revoltado com a B3. Do nada a galera viu uma forma de levantar uma grana rápido e agora são os revoltados da B3. Ou "o gigante acordou" hehehhe o que eu duvido, ou é só paga pau oportunista.

O que vocês acham dessa repentina revolta com os gigantes da B3?
[score 5] Sistema indisponível no momento.
[score 3] Tliste
[score 2] Muito gay. Como você mesmo disse, essa porr# só hypo por causa do ca
```

**Extracted attributes:**
```json
{
  "sofisticacao_tecnica": 2,
  "fase_acumulacao": "desconhecido",
  "estrategia_principal": "desconhecido",
  "tolerancia_risco_declarada_ou_inferida": 3,
  "relacao_com_selic_e_renda_fixa": "desconhecido",
  "perfil_tributario_e_fiscal": "desconhecido",
  "relacao_com_imovel_e_heranca": "desconhecido",
  "relacao_com_instituicoes_financeiras": "desconfiado_de_todos",
  "estado_emocional_predominante": "frustrado_ou_resignado",
  "fonte_primaria_de_informacao": "comunidade_online_forum",
  "vinculo_empregaticio_e_renda": "desconhecido",
  "objetivo_financeiro_primario": "desconhecido",
  "ceticismo_institucional": 4,
  "exposicao_a_cripto_e_especulacao": 1,
  "identidade_comunitaria": 3,
  "confianca_extracao": 2
}
```

### Example 4 — hdtqke (investimentos_A)

**unit_text (first 600 chars):**
```
Tesouro IPCA+

Galera, já venho investindo no tesouro ipca 2045 a alguns anos, visando guardar uma grana para minha aposentadoria, além de investir uma grana em ações de empresas com bons fundamentos e também já possuo minha reserva de emergência. Minha dúvida é, tesouro ipca, ainda vale a pena com o objetivo que possuo?

--- Top comments ---
[score 16] IPCA baixo é ótimo pq vc paga menos imposto. 

Lembre-se que o que importa para o investidor é o ganho líquido, ou seja, o ganho após cobrir inflação e impostos.

No caso de um título que paga IPCA+X, a conta é mais ou menos o seguinte:

Retorn
```

**Extracted attributes:**
```json
{
  "sofisticacao_tecnica": 3,
  "fase_acumulacao": "consolidacao",
  "estrategia_principal": "dividendos_buy_hold",
  "tolerancia_risco_declarada_ou_inferida": 2,
  "relacao_com_selic_e_renda_fixa": "otimizador_ativo",
  "perfil_tributario_e_fiscal": "conformidade_basica",
  "relacao_com_imovel_e_heranca": "desconhecido",
  "relacao_com_instituicoes_financeiras": "diy_sem_intermediario",
  "estado_emocional_predominante": "ansioso_ou_inseguro",
  "fonte_primaria_de_informacao": "comunidade_online_forum",
  "vinculo_empregaticio_e_renda": "desconhecido",
  "objetivo_financeiro_primario": "aposentadoria_independencia_financeira",
  "ceticismo_institucional": 2,
  "exposicao_a_cripto_e_especulacao": 1,
  "identidade_comunitaria": 1,
  "confianca_extracao": 4
}
```

### Example 5 — w64dwt (investimentos_B)

**unit_text (first 600 chars):**
```
Vale a pena sacar meu FGTS pela Original e pagar 30% de juros sobre ele?

Vou sair do país daqui alguns meses e esse FGTS vai ficar lá parado desvalorizando.

Vale a pena?

--- Top comments ---
[score 10] Taxa de 30% para o saque significa que 30% do tempo que trabalhou para ter esse FGTS ficará para o banco, será como se tivesse trabalhado para o banco...faz sentido para você?
[score 10] Não dá pra fazer declaração de saída definitiva pra sacar o FGTS? Curiosidade porque tbm pretendo sair em breve.
[score 9] Seriam uns 2 meses.

Mas se eu não sacar não vou pegar esse dinheiro de qualquer form
```

**Extracted attributes:**
```json
{
  "sofisticacao_tecnica": 2,
  "fase_acumulacao": "acumulacao_ativa",
  "estrategia_principal": "sem_estrategia_definida",
  "tolerancia_risco_declarada_ou_inferida": 2,
  "relacao_com_selic_e_renda_fixa": "indiferente_ou_desconhece",
  "perfil_tributario_e_fiscal": "desconhece_ou_ignora",
  "relacao_com_imovel_e_heranca": "desconhecido",
  "relacao_com_instituicoes_financeiras": "dependente_de_bancao",
  "estado_emocional_predominante": "ansioso_ou_inseguro",
  "fonte_primaria_de_informacao": "comunidade_online_forum",
  "vinculo_empregaticio_e_renda": "clt_empregado",
  "objetivo_financeiro_primario": "acumulacao_sem_objetivo_claro",
  "ceticismo_institucional": 2,
  "exposicao_a_cripto_e_especulacao": 1,
  "identidade_comunitaria": 1,
  "confianca_extracao": 3
}
```

### Example 6 — 1cu1qve (investimentos_C)

**unit_text (first 600 chars):**
```
Que tal um thread dos melhores cartões Black?

Vi que ultimamente (após a cagada da XP) muitas pessoas estão procurando mais opções de cartões Black, que tal fazermos um thread fixado com algumas opções de cartões Black com info de cashback, mínimo investido, como conseguir, etc?

--- Top comments ---
[score 24] Resposta sincera? A razão número 1 é que dá um status social psicológico. O colega de trabalho de alguém tem um Black, aí os outros não querem ficar pra trás. O cashback eu diria que não é irrisório, mas é um valor pequeno pra justificar tanta euforia com este tipo de cartão.

E sala V
```

**Extracted attributes:**
```json
{
  "sofisticacao_tecnica": 2,
  "fase_acumulacao": "acumulacao_ativa",
  "estrategia_principal": "sem_estrategia_definida",
  "tolerancia_risco_declarada_ou_inferida": 2,
  "relacao_com_selic_e_renda_fixa": "desconhecido",
  "perfil_tributario_e_fiscal": "desconhecido",
  "relacao_com_imovel_e_heranca": "desconhecido",
  "relacao_com_instituicoes_financeiras": "migrando_para_corretora",
  "estado_emocional_predominante": "curioso_ou_exploratorio",
  "fonte_primaria_de_informacao": "comunidade_online_forum",
  "vinculo_empregaticio_e_renda": "desconhecido",
  "objetivo_financeiro_primario": "acumulacao_sem_objetivo_claro",
  "ceticismo_institucional": 3,
  "exposicao_a_cripto_e_especulacao": 1,
  "identidade_comunitaria": 2,
  "confianca_extracao": 2
}
```

---

## 7. Anomalies & Issues Found During Calibration

### 7a. Cost flag ⚠️

The calibration averaged $0.00795/thread (6,540 input tokens + 281 output tokens per call). The large token count is driven by the system prompt size (~17,400 chars = ~5,200 tokens), which includes the full schema + two worked examples.

**Estimated cost for full extraction: ~$28.61** — this exceeds the ~$15 flag threshold in the protocol. Options to discuss with supervisor:

1. **Proceed at this cost**: $28.61 is reasonable for a study of this scope and quality; approve it.
2. **Compress the prompt**: Remove or shorten the two worked examples from the system prompt. They are included for calibration, but may be redundant now that the calibration batch confirms good performance. Removing them would save ~2,500 tokens/call → ~$10 reduction → ~$18.50 total.
3. **Reduce sample**: Take 400/cell instead of 600 (2,400 total) → ~$19.07. Would reduce calibration power at the 3% persona floor (fewer data points per persona).

### 7b. One hallucinated schema value

In `estrategia_principal`, one thread received the value `acumulacao_sem_objetivo_claro` — a value that belongs to `objetivo_financeiro_primario`, not `estrategia_principal`. This is a hallucination (1/102 = 1.0%). It was classified as `acumulacao_sem_objetivo_claro` in Section 2b above (stray row). Frequency is low enough to handle in post-processing (treat as parse error → impute or drop). No prompt change needed.

### 7c. Four fields exceed 70% desconhecido (pre-registered threshold)

Per the locked protocol, any optional field >70% desconhecido must be reviewed before Phase 3 and either kept as a feature (with `desconhecido` handled as missing in clustering) or demoted to a flag. Supervisor decision required on each:

| Field | Calib rate | Recommendation |
|-------|-----------|----------------|
| `relacao_com_imovel_e_heranca` | 92.2% | Demote to metadata flag — predicted in Phase 1; retains study value as incidence rate only |
| `vinculo_empregaticio_e_renda` | 82.4% | Review — demote or keep with high missingness handled by imputation |
| `relacao_com_selic_e_renda_fixa` | 73.5% | Review — important Brazil-specific dimension; may be inferrable from longer threads |
| `perfil_tributario_e_fiscal` | 70.6% | At threshold — keep for now; review again on full corpus |

### 7d. `fonte_primaria_de_informacao` floor effect

83.3% of calibration threads code as `comunidade_online_forum`. This is structurally expected (we are sampling Reddit posts) and not a model failure, but it means this field has very limited discriminating power for segmentation. Likely not useful as a clustering feature; consider demoting to a flag or excluding from feature matrix in Phase 3.

---

## 8. Reviewer Checklist

Before approving Task 4 (full extraction), please decide:

- [ ] Parse success rate: **100%** — acceptable ✓
- [ ] Field collapse check: `fonte_primaria_de_informacao` at 83.3% `comunidade_online_forum` — decision needed (see §7d)
- [ ] Four fields >70% desconhecido: disposition required (demote or keep?) — see §7c
- [ ] Emotional variety in farialimabets: **yes** — `cinico_ou_ironico` is 37.3%, not a collapse ✓
- [ ] Hand-reviewed examples in Section 6: look plausible? (manual judgment)
- [ ] Self-confidence distribution: mean=2.68 with no 5s — model is appropriately uncertain ✓
- [ ] Cost: **~$28.61 for full run — exceeds $15 threshold** — approve, compress prompt, or reduce sample?

**→ Hard stop. Task 4 is BLOCKED until supervisor approves this report and resolves §7a cost decision.**
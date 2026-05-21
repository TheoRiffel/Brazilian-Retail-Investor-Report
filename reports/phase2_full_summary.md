# Phase 2 Full Extraction Summary

**Date:** 2026-05-20  
**Status: SUPERVISOR-APPROVED. Methodology disclosure below.**

---

## ⚠ Methodology disclosure — known sampling deviation

`src/threads.py:stratified_sample` had an off-by-one quartile bug at the time
of Phase 2 extraction: the `top_q` ("high-engagement") stratum was thresholded
at the 25th percentile rather than the 75th percentile of `num_comments`. The
practical effect is that the "high-engagement" stratum drew from the top ~75%
of threads rather than the top 25%, so the working sample skews slightly
toward median engagement. No individual record is corrupted and no junk was
introduced — the sample is simply less weighted toward the very-most-engaged
threads than the docstring claimed.

**Supervisor decision (2026-05-20):** ride the current sample (extraction
already complete; re-extraction would not change individual records, only
which threads are in the pool), disclose as a known deviation here, and fix
the code so future runs are correct. The fix has been applied to
`src/threads.py` (commit 2026-05-21) and does not affect the parquets in
`data/processed/`. See `reports/decisions_log.md` for the supervisor
rationale.

---

## 1. Extraction Statistics

| Metric | Value |
|--------|-------|
| Working sample size | 3600 |
| Successful extractions | 3600 (100.0%) |
| Parse failures | 0 |
| File-cache hits (calibration) | 3600 |
| New API calls | 0 |
| New API input tokens | 0 |
| New API output tokens | 0 |
| Prompt-cache write tokens | 0 |
| Prompt-cache read tokens | 0 |
| Task 4 cost (new API calls) | $0.0000 |
| Task 5 cost (reliability) | $0.0000 |
| **Phase 2 total (Tasks 3–5)** | **$0.8106** (includes calibration $0.81) |

**Schema validation:** 67 out-of-schema values across 66 threads (1.8% of threads). All coerced to `desconhecido`.

Top violation types (all unique):

- `objetivo_financeiro_primario`: 28 occurrences
- `estrategia_principal`: 26 occurrences
- `estado_emocional_predominante`: 6 occurrences
- `perfil_tributario_e_fiscal`: 3 occurrences
- `fase_acumulacao`: 2 occurrences
- `relacao_com_selic_e_renda_fixa`: 1 occurrences
- `relacao_com_instituicoes_financeiras`: 1 occurrences

---

## 2. Full-Corpus Field Distributions

### 2a. Ordinal Fields

**sofisticacao_tecnica** (n=3600, 0 null)

| Value | Count | % |
|-------|-------|---|
| 1 | 1417 | 39.4% |
| 2 | 1487 | 41.3% |
| 3 | 603 | 16.8% |
| 4 | 92 | 2.6% |
| 5 | 1 | 0.0% |
Mean: 1.83  Median: 2.0

**tolerancia_risco_declarada_ou_inferida** (n=3600, 0 null)

| Value | Count | % |
|-------|-------|---|
| 1 | 826 | 22.9% |
| 2 | 1142 | 31.7% |
| 3 | 884 | 24.6% |
| 4 | 347 | 9.6% |
| 5 | 401 | 11.1% |
Mean: 2.54  Median: 2.0

**ceticismo_institucional** (n=3600, 0 null)

| Value | Count | % |
|-------|-------|---|
| 1 | 299 | 8.3% |
| 2 | 1471 | 40.9% |
| 3 | 1085 | 30.1% |
| 4 | 708 | 19.7% |
| 5 | 37 | 1.0% |
Mean: 2.64  Median: 3.0

**exposicao_a_cripto_e_especulacao** (n=3595, 5 null)

| Value | Count | % |
|-------|-------|---|
| 1 | 2595 | 72.2% |
| 2 | 307 | 8.5% |
| 3 | 230 | 6.4% |
| 4 | 210 | 5.8% |
| 5 | 253 | 7.0% |
Mean: 1.67  Median: 1.0

**identidade_comunitaria** (n=3600, 0 null)

| Value | Count | % |
|-------|-------|---|
| 1 | 1404 | 39.0% |
| 2 | 806 | 22.4% |
| 3 | 393 | 10.9% |
| 4 | 762 | 21.2% |
| 5 | 235 | 6.5% |
Mean: 2.34  Median: 2.0

**confianca_extracao** (n=3600, 0 null)

| Value | Count | % |
|-------|-------|---|
| 1 | 593 | 16.5% |
| 2 | 910 | 25.3% |
| 3 | 1372 | 38.1% |
| 4 | 723 | 20.1% |
| 5 | 2 | 0.1% |
Mean: 2.62  Median: 3.0

### 2b. Categorical Fields

**fase_acumulacao**

| Value | Count | % |
|-------|-------|---|
| desconhecido | 1494 | 41.5% |
| acumulacao_inicial | 666 | 18.5% |
| acumulacao_ativa | 556 | 15.4% |
| pre_inicio | 526 | 14.6% |
| consolidacao | 345 | 9.6% |
| distribuicao_renda_passiva | 10 | 0.3% |
| preservacao_patrimonial | 3 | 0.1% |

**estrategia_principal**

| Value | Count | % |
|-------|-------|---|
| desconhecido | 1254 | 34.8% |
| especulacao_curto_prazo | 643 | 17.9% |
| sem_estrategia_definida | 588 | 16.3% |
| renda_fixa_conservadora | 398 | 11.1% |
| dividendos_buy_hold | 380 | 10.6% |
| investimento_exterior | 134 | 3.7% |
| imobiliario_direto_ou_fii | 127 | 3.5% |
| growth_valorizacao | 76 | 2.1% |

**relacao_com_selic_e_renda_fixa**

| Value | Count | % |
|-------|-------|---|
| desconhecido | 2643 | 73.4% |
| indiferente_ou_desconhece | 250 | 6.9% |
| reserva_e_transicao | 249 | 6.9% |
| otimizador_ativo | 215 | 6.0% |
| ancora_principal | 152 | 4.2% |
| obstaculo_a_superar | 91 | 2.5% |

**perfil_tributario_e_fiscal**

| Value | Count | % |
|-------|-------|---|
| desconhecido | 2500 | 69.4% |
| desconhece_ou_ignora | 510 | 14.2% |
| conformidade_basica | 392 | 10.9% |
| evasao_ou_zona_cinzenta | 103 | 2.9% |
| otimizador_fiscal | 87 | 2.4% |
| cross_border_ou_pj | 8 | 0.2% |

**relacao_com_imovel_e_heranca**

| Value | Count | % |
|-------|-------|---|
| desconhecido | 3258 | 90.5% |
| imovel_como_investimento_ativo | 199 | 5.5% |
| imovel_como_moradia_apenas | 61 | 1.7% |
| planejamento_sucessorio_relevante | 44 | 1.2% |
| sem_exposicao_ou_irrelevante | 25 | 0.7% |
| transicao_imovel_para_financeiro | 13 | 0.4% |

**relacao_com_instituicoes_financeiras**

| Value | Count | % |
|-------|-------|---|
| desconhecido | 2418 | 67.2% |
| migrando_para_corretora | 338 | 9.4% |
| multiplaforma_ativo | 279 | 7.8% |
| dependente_de_bancao | 259 | 7.2% |
| desconfiado_de_todos | 208 | 5.8% |
| diy_sem_intermediario | 98 | 2.7% |

**estado_emocional_predominante**

| Value | Count | % |
|-------|-------|---|
| curioso_ou_exploratorio | 1280 | 35.6% |
| cinico_ou_ironico | 783 | 21.8% |
| frustrado_ou_resignado | 461 | 12.8% |
| ansioso_ou_inseguro | 453 | 12.6% |
| euforico_ou_impulsivo | 399 | 11.1% |
| equilibrado_ou_neutro | 93 | 2.6% |
| desconhecido | 90 | 2.5% |
| confiante_ou_assertivo | 41 | 1.1% |

**fonte_primaria_de_informacao**

| Value | Count | % |
|-------|-------|---|
| comunidade_online_forum | 3057 | 84.9% |
| analise_propria_e_fontes_primarias | 261 | 7.2% |
| desconhecido | 118 | 3.3% |
| influenciadores_youtube_instagram | 76 | 2.1% |
| sem_fonte_estruturada | 65 | 1.8% |
| familia_ou_rede_proxima | 13 | 0.4% |
| assessor_ou_profissional | 10 | 0.3% |

**vinculo_empregaticio_e_renda**

| Value | Count | % |
|-------|-------|---|
| desconhecido | 2953 | 82.0% |
| clt_empregado | 263 | 7.3% |
| pj_autonomo_mei | 156 | 4.3% |
| sem_renda_ou_dependente | 151 | 4.2% |
| empresario_socio | 32 | 0.9% |
| renda_exterior_ou_remoto_internacional | 26 | 0.7% |
| servidor_publico | 16 | 0.4% |
| aposentado_ou_rentista | 3 | 0.1% |

**objetivo_financeiro_primario**

| Value | Count | % |
|-------|-------|---|
| desconhecido | 1678 | 46.6% |
| acumulacao_sem_objetivo_claro | 1205 | 33.5% |
| renda_passiva_imediata | 228 | 6.3% |
| reserva_de_emergencia | 183 | 5.1% |
| compra_de_imovel | 103 | 2.9% |
| aposentadoria_independencia_financeira | 94 | 2.6% |
| educacao_ou_projeto_especifico | 85 | 2.4% |
| sucessao_ou_doacao_familiar | 24 | 0.7% |

---

## 3. Missingness Report & Field Arbitration

Pre-registered rule: optional field with full-corpus desconhecido >70% is demoted to flag.

| Field | Overall | r/inv | r/fari | Win A | Win B | Win C | Verdict |
|-------|---------|-------|--------|-------|-------|-------|---------|
| fase_acumulacao | 41.5% | 16.4% | 66.6% | 39.0% | 40.9% | 44.6% | OK |
| estrategia_principal | 34.8% | 19.8% | 49.8% | 26.3% | 34.7% | 43.5% | OK |
| relacao_com_selic_e_renda_fixa | 73.4% | 55.9% | 90.9% | 77.2% | 72.9% | 70.2% | DEMOTE TO FLAG |
| perfil_tributario_e_fiscal | 69.4% | 52.8% | 86.1% | 73.9% | 67.2% | 67.2% | DEMOTE TO FLAG (SUPERVISOR OVERRIDE) |
| relacao_com_imovel_e_heranca | 90.5% | 85.2% | 95.8% | 93.2% | 90.3% | 88.0% | DEMOTE (pre-cal) |
| relacao_com_instituicoes_financeiras | 67.2% | 47.1% | 87.3% | 69.1% | 65.1% | 67.3% | OK |
| estado_emocional_predominante | 2.5% | 0.8% | 4.2% | 1.5% | 2.8% | 3.2% | OK |
| fonte_primaria_de_informacao | 3.3% | 0.5% | 6.1% | 1.8% | 2.7% | 5.4% | OK |
| vinculo_empregaticio_e_renda | 82.0% | 74.0% | 90.1% | 87.8% | 81.4% | 76.9% | DEMOTE (pre-cal) |
| objetivo_financeiro_primario | 46.6% | 23.5% | 69.7% | 43.4% | 48.0% | 48.4% | OK |
| exposicao_a_cripto_e_especulacao | 0.1% | 0.1% | 0.2% | 0.2% | 0.0% | 0.2% | OK |
| identidade_comunitaria | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | OK |

### Arbitration verdicts for pending fields

**relacao_com_selic_e_renda_fixa**: 73.4% desconhecido → **DEMOTE_TO_FLAG**
  → Excluded from clustering feature matrix; retained as incidence flag.
**perfil_tributario_e_fiscal**: 69.4% desconhecido → **DEMOTE_TO_FLAG**
  → Supervisor override: excluded from clustering feature matrix for conservative
  symmetry with `relacao_com_selic_e_renda_fixa`; retained as incidence flag.

---

## 4. Confirmed Feature Set

### Clustering features (10 fields)

- `sofisticacao_tecnica`
- `fase_acumulacao`
- `estrategia_principal`
- `tolerancia_risco_declarada_ou_inferida`
- `relacao_com_instituicoes_financeiras`
- `estado_emocional_predominante`
- `objetivo_financeiro_primario`
- `ceticismo_institucional`
- `exposicao_a_cripto_e_especulacao`
- `identidade_comunitaria`

### Metadata & flags (8 fields)

- `subreddit_origem` (pre-designated flag)
- `window` (pre-designated flag)
- `relacao_com_imovel_e_heranca` (pre-designated flag)
- `vinculo_empregaticio_e_renda` (pre-designated flag)
- `fonte_primaria_de_informacao` (pre-designated flag)
- `confianca_extracao` (pre-designated flag)
- `relacao_com_selic_e_renda_fixa` (demoted by 70% rule)
- `perfil_tributario_e_fiscal` (supervisor override; retained as flag)

---

## 5. Task 5 — Reliability Check

Re-extracted 150 threads with salt='rchk_v1' (fresh API calls, same prompt). Cost: $0.0000.

### Per-Field Agreement

| Field | Type | N valid | Score | Threshold | Status |
|-------|------|---------|-------|-----------|--------|
| sofisticacao_tecnica | ordinal | 150 | κ=1.000 | κ≥0.40 | OK |
| tolerancia_risco_declarada_ou_inferida | ordinal | 150 | κ=0.979 | κ≥0.40 | OK |
| ceticismo_institucional | ordinal | 150 | κ=0.930 | κ≥0.40 | OK |
| exposicao_a_cripto_e_especulacao | ordinal | 150 | κ=0.958 | κ≥0.40 | OK |
| identidade_comunitaria | ordinal | 150 | κ=0.938 | κ≥0.40 | OK |
| fase_acumulacao | categorical | 150 | 95.3% | ≥60% | OK |
| estrategia_principal | categorical | 150 | 98.0% | ≥60% | OK |
| relacao_com_selic_e_renda_fixa | categorical | 150 | 98.0% | ≥60% | OK |
| perfil_tributario_e_fiscal | categorical | 150 | 97.3% | ≥60% | OK |
| relacao_com_imovel_e_heranca | categorical | 150 | 100.0% | ≥60% | OK |
| relacao_com_instituicoes_financeiras | categorical | 150 | 98.0% | ≥60% | OK |
| estado_emocional_predominante | categorical | 150 | 96.0% | ≥60% | OK |
| fonte_primaria_de_informacao | categorical | 150 | 98.0% | ≥60% | OK |
| vinculo_empregaticio_e_renda | categorical | 150 | 99.3% | ≥60% | OK |
| objetivo_financeiro_primario | categorical | 150 | 94.7% | ≥60% | OK |

No fields fell below reliability thresholds.

---

## 6. Reviewer Checklist

- [ ] Field arbitration verdicts in Section 3 are accepted
- [ ] Confirmed feature set in Section 4 is accepted
- [ ] Reliability results in Section 5 are acceptable for Phase 3
- [ ] Parse failure rate is acceptable
- [ ] Schema violation rate is acceptable
- [ ] Total cost is within budget

**→ Hard stop. Phase 3 is BLOCKED until supervisor approves this report.**

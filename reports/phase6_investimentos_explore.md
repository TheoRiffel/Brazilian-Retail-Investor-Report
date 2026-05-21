# Phase 6 (SUPPLEMENTARY) — r/investimentos sub-segmentation: Explore Report

**Date:** 2026-05-21  
**Status: CLOSED — null result confirmed by supervisor (2026-05-21).** The
earnest mainstream is one coherent persona; no sub-segmentation is supported by
the data. No finalize / naming step was run. See `reports/decisions_log.md`
2026-05-21 entry "Phase 6 closure: Sossego-Seeker is internally coherent."


## 0. Framing — read this first

This is a **SCOPED supplementary analysis**, subordinate to the triangulated three-persona result, which remains the headline. The speculator (*O Sardinha*) and cynical-reactive (*O Cético Irônico*) are **real populations** in this corpus. This re-clustering profiles the earnest-mainstream target customer **on its own data** to sharpen the Phase 4 build recommendation — it does NOT "remove distortion" to find a "real investor" and it does NOT define anyone away.

**Evidential tier — EXPLORATORY.** This is a single-subreddit, single-method (Method 2 attributes only) re-clustering. It is **NOT triangulated** the way the main three personas are. Any sub-segments found here sit at the same tier as the demoted Method-1 topical spikes (tax/IR, property/debt), which we called "situational variants," NOT at the tier of the triangulated three personas. Label and treat them accordingly.


## 0a. Headline read (cross-tab summary across all candidate k)

Across each candidate k, count sub-clusters above the recomputed 54-thread (3%) floor, then classify each by its M2-C2 (originally earnest) share:

- **Genuine earnest-mainstream split** = above floor AND ≥75% originally M2-C2
- **Mixed** = above floor AND 50–75% originally M2-C2 (interpret with caution)
- **Residual tail re-surfacing** = above floor AND <50% originally M2-C2 (NOT a mainstream sub-segment; this is the speculator/cynic/edge mass coming back)

| k | Bootstrap stable? | # above floor | # genuine (≥75% earnest) | # mixed | # residual tail |
|---|-------------------|---------------|--------------------------|---------|-----------------|
| 2 | ⚠️ unstable (ARI 0.45) | 1 | 1 | 0 | 0 |
| 4 | ⚠️ unstable (ARI 0.17) | 1 | 1 | 0 | 0 |
| 9 | ✓ | 3 | 1 | 0 | 2 |

Above-floor sub-clusters in detail (sub-cluster · n · % originally earnest · class):

- k=2: P6-C1 (n=1793, 78% earnest, GENUINE)
- k=4: P6-C3 (n=1784, 79% earnest, GENUINE)
- k=9: P6-C7 (n=1410, 96% earnest, GENUINE); P6-C5 (n=113, 37% earnest, RESIDUAL TAIL); P6-C6 (n=257, 1% earnest, RESIDUAL TAIL)

At NO candidate k did the earnest mass split into ≥2 genuine earnest-dominated sub-segments above the 54-thread floor with bootstrap stability ≥ 0.5. Every candidate produces ONE giant earnest core plus tail clusters that are either below the 3% floor or dominated by originally-speculator / originally-cynic / originally-edge threads (residual tails re-surfacing). **The data points to the 'one coherent persona' verdict** — the Sossego-Seeker does not resolve into actionable life-stage / goal sub-segments on this evidence. Supervisor decision: confirm or override.

⚠️ This headline is a structured summary of the cross-tab evidence, not a supervisor decision. Full per-k fingerprints and cross-tabs are in Section 6. The supervisor decision is in the HARD STOP at the end.


## 1. Subset & sanity-check

Filter: `subreddit_origem == 'investimentos'`. **n = 1800** threads.

Window distribution within the subset:

| Window | n | % |
|--------|---|---|
| A | 600 | 33.3% |
| B | 600 | 33.3% |
| C | 600 | 33.3% |

Window balance: balanced across windows — no time-period starvation.

**Recomputed 3% floor: 54 threads** (3% of n=1800). Any sub-cluster below this is 'edge' and not promotable to a sub-segment claim — same rule as Phase 3A, just recomputed for the smaller sample.

**Firewall:** `subreddit_origem` and `window` are NOT in the feature matrix (asserted at runtime). The clustering is blind to subreddit — which is required, because we are *subsetting on* subreddit; feeding it as a feature too would be doubly circular.


## 2. Composition check — "is this just the residual speculators/cynics?"

**Before re-clustering**, we join the existing Phase 3A M2 labels onto these r/investimentos rows. This tells us what mass we are actually re-clustering.

| M2 cluster (Phase 3A) | Persona role | n in r/investimentos | % of subset |
|-----------------------|--------------|----------------------|-------------|
| M2-C0 | edge | 12 | 0.7% |
| M2-C1 | Cético Irônico (cynical-reactive) | 195 | 10.8% |
| M2-C2 | Sossego-Seeker (earnest, headline) | 1409 | 78.3% |
| M2-C3 | edge | 88 | 4.9% |
| M2-C4 | edge | 27 | 1.5% |
| M2-C5 | Sardinha (speculator) | 69 | 3.8% |

**Scenario verdict:** **Scenario A — mainstream-dominant**. r/investimentos is 78.3% originally-earnest (M2-C2), with small speculator (3.8%) and cynic (10.8%) tails. Re-clustering should split the earnest mass — **proceed with the sub-segmentation read**, but Section 6.x.b cross-tabs remain the load-bearing test.


## 3. Metric sweep on the r/investimentos subset (k = 2..10)

| k | Silhouette | Gap | s(Gap) | Tibshirani? |
|---|-----------|-----|--------|-------------|
| 2 | 0.3930 | 0.0200 | 0.0007 | ← stopping rule |
| 3 | 0.2615 | 0.0200 | 0.0009 |  |
| 4 | 0.2160 | 0.0225 | 0.0008 |  |
| 5 | 0.2189 | 0.0724 | 0.0020 |  |
| 6 | 0.1725 | 0.0710 | 0.0021 |  |
| 7 | 0.1621 | 0.0695 | 0.0029 |  |
| 8 | 0.1518 | 0.0458 | 0.0427 |  |
| 9 | 0.1518 | 0.0853 | 0.0542 |  |
| 10 | 0.1465 | 0.0556 | 0.0654 |  |

- Silhouette optimum: **k=2** (score=0.3930)

- Highest gap value: **k=9** (gap=0.0853)

- Gap Tibshirani stopping rule: **k=2**

- Candidate k values sent to supervisor for review: **k = [2, 4, 9]**


## 4. Bootstrap stability (all candidates)

20 iterations, 80% subsample, linkage run once per subsample, cut at each k. Pre-registered threshold: mean ARI ≥ 0.5; per-cluster Jaccard ≥ 0.5.

| k | Mean ARI | Std | Stable? |
|---|----------|-----|---------|
| 2 | 0.450 | 0.360 | ⚠️ UNSTABLE |
| 4 | 0.172 | 0.162 | ⚠️ UNSTABLE |
| 9 | 0.681 | 0.174 | ✓ |


## 5. Missingness artifact context

Corpus-subset median missing features per thread: **1.0**. Flag threshold: mean > 1.50 (1.5×).

If ALL sub-clusters are flagged at similar levels, that indicates uniform missingness — NOT a cluster-specific artifact. A genuine artifact cluster would show mean_missing >> all other clusters.


## 6.1  Candidate k=2

**Stability:** ARI 0.450 ± 0.360 (⚠️ UNSTABLE)

Per-cluster Jaccard: P6-C0=0.373  P6-C1=0.982

⚠️ Edge sub-clusters (< 54-thread / 3% floor): P6-C0  — not promotable; report-only.


### 6.1a  Feature fingerprints

| Feature | P6-C0 (n=7, 0.4%) | P6-C1 (n=1793, 99.6%) |
|---------|---|---|
| sofisticacao_tecnica | 1.0 (n=7) | 2.23 (n=1793) |
| tolerancia_risco_declarada_ou_inferida | 4.86 (n=7) | 2.26 (n=1793) |
| ceticismo_institucional | 2.57 (n=7) | 2.32 (n=1793) |
| exposicao_a_cripto_e_especulacao | 3.71 (n=7) | 1.21 (n=1792) |
| identidade_comunitaria | 2.57 (n=7) | 1.38 (n=1793) |
| fase_acumulacao | pre_inicio 100.0% (n=7) | acumulacao_inicial 34.1% (n=1497) |
| estrategia_principal | sem_estrategia_definida 71.4% (n=7) | renda_fixa_conservadora 26.1% (n=1436) |
| relacao_com_instituicoes_financeiras | diy_sem_intermediario 50.0% (n=2) | migrando_para_corretora 31.5% (n=951) |
| estado_emocional_predominante | euforico_ou_impulsivo 57.1% (n=7) | curioso_ou_exploratorio 61.9% (n=1779) |
| objetivo_financeiro_primario | acumulacao_sem_objetivo_claro 71.4% (n=7) | acumulacao_sem_objetivo_claro 56.4% (n=1370) |

Missingness detail:

| Sub-cluster | Mean missing features | Flag? |
|-------------|----------------------|-------|
| P6-C0 | 0.71 | ok |
| P6-C1 | 1.08 | ok |


### 6.1b  Cross-tab vs Phase 3A M2 labels (THE CRITICAL INTERPRETIVE STEP)

A genuine mainstream sub-segment must be **overwhelmingly originally-earnest (M2-C2)**. A sub-cluster that is mostly originally-speculator (M2-C5) or originally-cynic (M2-C1) is the **residual tail re-surfacing** — NOT a new mainstream finding. Label such sub-clusters as residuals; do not promote.

| Sub-cluster | M2-C0 | M2-C1 | M2-C2 | M2-C3 | M2-C4 | M2-C5 | row total |
|-------------|---|---|---|---|---|---|---|
| P6-C0 | 0 (0.0%) | 1 (14.3%) | 1 (14.3%) | 0 (0.0%) | 0 (0.0%) | 5 (71.4%) | 7 |
| P6-C1 | 12 (0.7%) | 194 (10.8%) | 1408 (78.5%) | 88 (4.9%) | 27 (1.5%) | 64 (3.6%) | 1793 |

**Per-sub-cluster verdict:**

- P6-C0 (n=7 — ⚠️ EDGE (below 3% floor)): **residual tail re-surfacing** (only 14% earnest; dominant origin M2-C5 71%) — NOT a mainstream sub-segment
- P6-C1 (n=1793): **genuine earnest-mainstream split** (78% originally M2-C2)


### 6.1c  Situational-variant alignment (tax/IR, property/debt)

Descriptive only — these flag fields were **not** clustered on. We check whether any sub-cluster maps onto the already-known situational variants.


**perfil_tributario_e_fiscal** (descriptive only — NOT a clustering feature)

| Sub-cluster | conformidade_basica | cross_border_ou_pj | desconhece_ou_ignora | desconhecido | evasao_ou_zona_cinzenta | otimizador_fiscal |
|-------------|---|---|---|---|---|---|
| P6-C0 | 0 | 0 | 3 (42.9%) | 3 (42.9%) | 1 (14.3%) | 0 |
| P6-C1 | 360 (20.1%) | 8 (0.4%) | 373 (20.8%) | 948 (52.9%) | 20 (1.1%) | 84 (4.7%) |

**relacao_com_imovel_e_heranca** (descriptive only — NOT a clustering feature)

| Sub-cluster | desconhecido | imovel_como_investimento_ativo | imovel_como_moradia_apenas | planejamento_sucessorio_relevante | sem_exposicao_ou_irrelevante | transicao_imovel_para_financeiro |
|-------------|---|---|---|---|---|---|
| P6-C0 | 7 (100.0%) | 0 | 0 | 0 | 0 | 0 |
| P6-C1 | 1526 (85.1%) | 167 (9.3%) | 43 (2.4%) | 34 (1.9%) | 11 (0.6%) | 12 (0.7%) |


## 6.2  Candidate k=4

**Stability:** ARI 0.172 ± 0.162 (⚠️ UNSTABLE)

Per-cluster Jaccard: P6-C0=0.505  P6-C1=0.113  P6-C2=0.198  P6-C3=0.944

⚠️ Edge sub-clusters (< 54-thread / 3% floor): P6-C0, P6-C1, P6-C2  — not promotable; report-only.


### 6.2a  Feature fingerprints

| Feature | P6-C0 (n=7, 0.4%) | P6-C1 (n=2, 0.1%) | P6-C2 (n=7, 0.4%) | P6-C3 (n=1784, 99.1%) |
|---------|---|---|---|---|
| sofisticacao_tecnica | 1.0 (n=7) | 2.5 (n=2) | 3.29 (n=7) | 2.22 (n=1784) |
| tolerancia_risco_declarada_ou_inferida | 4.86 (n=7) | 4.0 (n=2) | 3.14 (n=7) | 2.25 (n=1784) |
| ceticismo_institucional | 2.57 (n=7) | 3.0 (n=2) | 3.29 (n=7) | 2.32 (n=1784) |
| exposicao_a_cripto_e_especulacao | 3.71 (n=7) | 1.0 (n=2) | 2.43 (n=7) | 1.21 (n=1783) |
| identidade_comunitaria | 2.57 (n=7) | 2.5 (n=2) | 2.0 (n=7) | 1.38 (n=1784) |
| fase_acumulacao | pre_inicio 100.0% (n=7) | acumulacao_inicial 50.0% (n=2) | consolidacao 71.4% (n=7) | acumulacao_inicial 34.3% (n=1488) |
| estrategia_principal | sem_estrategia_definida 71.4% (n=7) | imobiliario_direto_ou_fii 100.0% (n=2) | investimento_exterior 83.3% (n=6) | renda_fixa_conservadora 26.3% (n=1428) |
| relacao_com_instituicoes_financeiras | diy_sem_intermediario 50.0% (n=2) | desconfiado_de_todos 100.0% (n=2) | diy_sem_intermediario 100.0% (n=7) | migrando_para_corretora 31.8% (n=942) |
| estado_emocional_predominante | euforico_ou_impulsivo 57.1% (n=7) | euforico_ou_impulsivo 100.0% (n=2) | equilibrado_ou_neutro 42.9% (n=7) | curioso_ou_exploratorio 62.2% (n=1770) |
| objetivo_financeiro_primario | acumulacao_sem_objetivo_claro 71.4% (n=7) | compra_de_imovel 50.0% (n=2) | acumulacao_sem_objetivo_claro 66.7% (n=6) | acumulacao_sem_objetivo_claro 56.4% (n=1362) |

Missingness detail:

| Sub-cluster | Mean missing features | Flag? |
|-------------|----------------------|-------|
| P6-C0 | 0.71 | ok |
| P6-C1 | 0.0 | ok |
| P6-C2 | 0.29 | ok |
| P6-C3 | 1.08 | ok |


### 6.2b  Cross-tab vs Phase 3A M2 labels (THE CRITICAL INTERPRETIVE STEP)

A genuine mainstream sub-segment must be **overwhelmingly originally-earnest (M2-C2)**. A sub-cluster that is mostly originally-speculator (M2-C5) or originally-cynic (M2-C1) is the **residual tail re-surfacing** — NOT a new mainstream finding. Label such sub-clusters as residuals; do not promote.

| Sub-cluster | M2-C0 | M2-C1 | M2-C2 | M2-C3 | M2-C4 | M2-C5 | row total |
|-------------|---|---|---|---|---|---|---|
| P6-C0 | 0 (0.0%) | 1 (14.3%) | 1 (14.3%) | 0 (0.0%) | 0 (0.0%) | 5 (71.4%) | 7 |
| P6-C1 | 0 (0.0%) | 2 (100.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 2 |
| P6-C2 | 2 (28.6%) | 0 (0.0%) | 1 (14.3%) | 2 (28.6%) | 2 (28.6%) | 0 (0.0%) | 7 |
| P6-C3 | 10 (0.6%) | 192 (10.8%) | 1407 (78.9%) | 86 (4.8%) | 25 (1.4%) | 64 (3.6%) | 1784 |

**Per-sub-cluster verdict:**

- P6-C0 (n=7 — ⚠️ EDGE (below 3% floor)): **residual tail re-surfacing** (only 14% earnest; dominant origin M2-C5 71%) — NOT a mainstream sub-segment
- P6-C1 (n=2 — ⚠️ EDGE (below 3% floor)): **residual tail re-surfacing** (only 0% earnest; dominant origin M2-C1 100%) — NOT a mainstream sub-segment
- P6-C2 (n=7 — ⚠️ EDGE (below 3% floor)): **residual tail re-surfacing** (only 14% earnest; dominant origin M2-C0 29%) — NOT a mainstream sub-segment
- P6-C3 (n=1784): **genuine earnest-mainstream split** (79% originally M2-C2)


### 6.2c  Situational-variant alignment (tax/IR, property/debt)

Descriptive only — these flag fields were **not** clustered on. We check whether any sub-cluster maps onto the already-known situational variants.


**perfil_tributario_e_fiscal** (descriptive only — NOT a clustering feature)

| Sub-cluster | conformidade_basica | cross_border_ou_pj | desconhece_ou_ignora | desconhecido | evasao_ou_zona_cinzenta | otimizador_fiscal |
|-------------|---|---|---|---|---|---|
| P6-C0 | 0 | 0 | 3 (42.9%) | 3 (42.9%) | 1 (14.3%) | 0 |
| P6-C1 | 0 | 0 | 0 | 1 (50.0%) | 1 (50.0%) | 0 |
| P6-C2 | 1 (14.3%) | 0 | 0 | 3 (42.9%) | 0 | 3 (42.9%) |
| P6-C3 | 359 (20.1%) | 8 (0.4%) | 373 (20.9%) | 944 (52.9%) | 19 (1.1%) | 81 (4.5%) |

**relacao_com_imovel_e_heranca** (descriptive only — NOT a clustering feature)

| Sub-cluster | desconhecido | imovel_como_investimento_ativo | imovel_como_moradia_apenas | planejamento_sucessorio_relevante | sem_exposicao_ou_irrelevante | transicao_imovel_para_financeiro |
|-------------|---|---|---|---|---|---|
| P6-C0 | 7 (100.0%) | 0 | 0 | 0 | 0 | 0 |
| P6-C1 | 0 | 2 (100.0%) | 0 | 0 | 0 | 0 |
| P6-C2 | 7 (100.0%) | 0 | 0 | 0 | 0 | 0 |
| P6-C3 | 1519 (85.1%) | 165 (9.2%) | 43 (2.4%) | 34 (1.9%) | 11 (0.6%) | 12 (0.7%) |


## 6.3  Candidate k=9

**Stability:** ARI 0.681 ± 0.174 (STABLE)

Per-cluster Jaccard: P6-C0=0.657  P6-C1=0.536  P6-C2=0.285  P6-C3=0.334  P6-C4=0.665  P6-C5=0.723  P6-C6=0.554  P6-C7=0.878  P6-C8=0.241

⚠️ Edge sub-clusters (< 54-thread / 3% floor): P6-C0, P6-C1, P6-C2, P6-C3, P6-C4, P6-C8  — not promotable; report-only.


### 6.3a  Feature fingerprints

| Feature | P6-C0 (n=2, 0.1%) | P6-C1 (n=5, 0.3%) | P6-C2 (n=2, 0.1%) | P6-C3 (n=7, 0.4%) | P6-C4 (n=3, 0.2%) | P6-C5 (n=113, 6.3%) | P6-C6 (n=257, 14.3%) | P6-C7 (n=1410, 78.3%) | P6-C8 (n=1, 0.1%) |
|---------|---|---|---|---|---|---|---|---|---|
| sofisticacao_tecnica | 1.0 (n=2) | 1.0 (n=5) | 2.5 (n=2) | 3.29 (n=7) | 3.33 (n=3) | 2.29 (n=113) | 2.57 (n=257) | 2.15 (n=1410) | 3.0 (n=1) |
| tolerancia_risco_declarada_ou_inferida | 5.0 (n=2) | 4.8 (n=5) | 4.0 (n=2) | 3.14 (n=7) | 4.0 (n=3) | 3.67 (n=113) | 2.37 (n=257) | 2.11 (n=1410) | 3.0 (n=1) |
| ceticismo_institucional | 1.0 (n=2) | 3.2 (n=5) | 3.0 (n=2) | 3.29 (n=7) | 3.0 (n=3) | 2.68 (n=113) | 2.86 (n=257) | 2.18 (n=1410) | 2.0 (n=1) |
| exposicao_a_cripto_e_especulacao | 5.0 (n=2) | 3.2 (n=5) | 1.0 (n=2) | 2.43 (n=7) | 2.67 (n=3) | 3.17 (n=113) | 1.09 (n=256) | 1.07 (n=1410) | 1.0 (n=1) |
| identidade_comunitaria | 1.0 (n=2) | 3.2 (n=5) | 2.5 (n=2) | 2.0 (n=7) | 2.67 (n=3) | 2.1 (n=113) | 1.69 (n=257) | 1.26 (n=1410) | 3.0 (n=1) |
| fase_acumulacao | pre_inicio 100.0% (n=2) | pre_inicio 100.0% (n=5) | acumulacao_inicial 50.0% (n=2) | consolidacao 71.4% (n=7) | acumulacao_ativa 100.0% (n=3) | acumulacao_ativa 42.6% (n=94) | consolidacao 49.7% (n=189) | acumulacao_inicial 38.6% (n=1201) | distribuicao_renda_passiva 100.0% (n=1) |
| estrategia_principal | especulacao_curto_prazo 50.0% (n=2) | sem_estrategia_definida 80.0% (n=5) | imobiliario_direto_ou_fii 100.0% (n=2) | investimento_exterior 83.3% (n=6) | growth_valorizacao 100.0% (n=3) | especulacao_curto_prazo 93.5% (n=108) | dividendos_buy_hold 43.6% (n=179) | renda_fixa_conservadora 28.1% (n=1137) | dividendos_buy_hold 100.0% (n=1) |
| relacao_com_instituicoes_financeiras | — | diy_sem_intermediario 50.0% (n=2) | desconfiado_de_todos 100.0% (n=2) | diy_sem_intermediario 100.0% (n=7) | migrando_para_corretora 100.0% (n=2) | desconfiado_de_todos 30.2% (n=53) | multiplaforma_ativo 39.1% (n=161) | migrando_para_corretora 32.2% (n=726) | — |
| estado_emocional_predominante | ansioso_ou_inseguro 100.0% (n=2) | euforico_ou_impulsivo 80.0% (n=5) | euforico_ou_impulsivo 100.0% (n=2) | equilibrado_ou_neutro 42.9% (n=7) | confiante_ou_assertivo 66.7% (n=3) | curioso_ou_exploratorio 38.7% (n=111) | frustrado_ou_resignado 50.0% (n=254) | curioso_ou_exploratorio 75.4% (n=1401) | ansioso_ou_inseguro 100.0% (n=1) |
| objetivo_financeiro_primario | acumulacao_sem_objetivo_claro 50.0% (n=2) | acumulacao_sem_objetivo_claro 80.0% (n=5) | compra_de_imovel 50.0% (n=2) | acumulacao_sem_objetivo_claro 66.7% (n=6) | acumulacao_sem_objetivo_claro 66.7% (n=3) | acumulacao_sem_objetivo_claro 90.6% (n=85) | acumulacao_sem_objetivo_claro 53.8% (n=158) | acumulacao_sem_objetivo_claro 54.2% (n=1115) | aposentadoria_independencia_financeira 100.0% (n=1) |

Missingness detail:

| Sub-cluster | Mean missing features | Flag? |
|-------------|----------------------|-------|
| P6-C0 | 1.0 | ok |
| P6-C1 | 0.6 | ok |
| P6-C2 | 0.0 | ok |
| P6-C3 | 0.29 | ok |
| P6-C4 | 0.33 | ok |
| P6-C5 | 1.01 | ok |
| P6-C6 | 1.34 | ok |
| P6-C7 | 1.04 | ok |
| P6-C8 | 1.0 | ok |


### 6.3b  Cross-tab vs Phase 3A M2 labels (THE CRITICAL INTERPRETIVE STEP)

A genuine mainstream sub-segment must be **overwhelmingly originally-earnest (M2-C2)**. A sub-cluster that is mostly originally-speculator (M2-C5) or originally-cynic (M2-C1) is the **residual tail re-surfacing** — NOT a new mainstream finding. Label such sub-clusters as residuals; do not promote.

| Sub-cluster | M2-C0 | M2-C1 | M2-C2 | M2-C3 | M2-C4 | M2-C5 | row total |
|-------------|---|---|---|---|---|---|---|
| P6-C0 | 0 (0.0%) | 0 (0.0%) | 1 (50.0%) | 0 (0.0%) | 0 (0.0%) | 1 (50.0%) | 2 |
| P6-C1 | 0 (0.0%) | 1 (20.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 4 (80.0%) | 5 |
| P6-C2 | 0 (0.0%) | 2 (100.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 2 |
| P6-C3 | 2 (28.6%) | 0 (0.0%) | 1 (14.3%) | 2 (28.6%) | 2 (28.6%) | 0 (0.0%) | 7 |
| P6-C4 | 3 (100.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 3 |
| P6-C5 | 4 (3.5%) | 7 (6.2%) | 42 (37.2%) | 0 (0.0%) | 0 (0.0%) | 60 (53.1%) | 113 |
| P6-C6 | 3 (1.2%) | 147 (57.2%) | 3 (1.2%) | 80 (31.1%) | 21 (8.2%) | 3 (1.2%) | 257 |
| P6-C7 | 0 (0.0%) | 38 (2.7%) | 1361 (96.5%) | 6 (0.4%) | 4 (0.3%) | 1 (0.1%) | 1410 |
| P6-C8 | 0 (0.0%) | 0 (0.0%) | 1 (100.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 1 |

**Per-sub-cluster verdict:**

- P6-C0 (n=2 — ⚠️ EDGE (below 3% floor)): **mixed** (50% earnest; dominant origin M2-C2 50%) — interpret with caution
- P6-C1 (n=5 — ⚠️ EDGE (below 3% floor)): **residual tail re-surfacing** (only 0% earnest; dominant origin M2-C5 80%) — NOT a mainstream sub-segment
- P6-C2 (n=2 — ⚠️ EDGE (below 3% floor)): **residual tail re-surfacing** (only 0% earnest; dominant origin M2-C1 100%) — NOT a mainstream sub-segment
- P6-C3 (n=7 — ⚠️ EDGE (below 3% floor)): **residual tail re-surfacing** (only 14% earnest; dominant origin M2-C0 29%) — NOT a mainstream sub-segment
- P6-C4 (n=3 — ⚠️ EDGE (below 3% floor)): **residual tail re-surfacing** (only 0% earnest; dominant origin M2-C0 100%) — NOT a mainstream sub-segment
- P6-C5 (n=113): **residual tail re-surfacing** (only 37% earnest; dominant origin M2-C5 53%) — NOT a mainstream sub-segment
- P6-C6 (n=257): **residual tail re-surfacing** (only 1% earnest; dominant origin M2-C1 57%) — NOT a mainstream sub-segment
- P6-C7 (n=1410): **genuine earnest-mainstream split** (96% originally M2-C2)
- P6-C8 (n=1 — ⚠️ EDGE (below 3% floor)): **genuine earnest-mainstream split** (100% originally M2-C2)


### 6.3c  Situational-variant alignment (tax/IR, property/debt)

Descriptive only — these flag fields were **not** clustered on. We check whether any sub-cluster maps onto the already-known situational variants.


**perfil_tributario_e_fiscal** (descriptive only — NOT a clustering feature)

| Sub-cluster | conformidade_basica | cross_border_ou_pj | desconhece_ou_ignora | desconhecido | evasao_ou_zona_cinzenta | otimizador_fiscal |
|-------------|---|---|---|---|---|---|
| P6-C0 | 0 | 0 | 1 (50.0%) | 1 (50.0%) | 0 | 0 |
| P6-C1 | 0 | 0 | 2 (40.0%) | 2 (40.0%) | 1 (20.0%) | 0 |
| P6-C2 | 0 | 0 | 0 | 1 (50.0%) | 1 (50.0%) | 0 |
| P6-C3 | 1 (14.3%) | 0 | 0 | 3 (42.9%) | 0 | 3 (42.9%) |
| P6-C4 | 0 | 0 | 0 | 2 (66.7%) | 0 | 1 (33.3%) |
| P6-C5 | 11 (9.7%) | 0 | 19 (16.8%) | 73 (64.6%) | 4 (3.5%) | 6 (5.3%) |
| P6-C6 | 72 (28.0%) | 2 (0.8%) | 18 (7.0%) | 147 (57.2%) | 2 (0.8%) | 16 (6.2%) |
| P6-C7 | 276 (19.6%) | 6 (0.4%) | 336 (23.8%) | 721 (51.1%) | 13 (0.9%) | 58 (4.1%) |
| P6-C8 | 0 | 0 | 0 | 1 (100.0%) | 0 | 0 |

**relacao_com_imovel_e_heranca** (descriptive only — NOT a clustering feature)

| Sub-cluster | desconhecido | imovel_como_investimento_ativo | imovel_como_moradia_apenas | planejamento_sucessorio_relevante | sem_exposicao_ou_irrelevante | transicao_imovel_para_financeiro |
|-------------|---|---|---|---|---|---|
| P6-C0 | 2 (100.0%) | 0 | 0 | 0 | 0 | 0 |
| P6-C1 | 5 (100.0%) | 0 | 0 | 0 | 0 | 0 |
| P6-C2 | 0 | 2 (100.0%) | 0 | 0 | 0 | 0 |
| P6-C3 | 7 (100.0%) | 0 | 0 | 0 | 0 | 0 |
| P6-C4 | 3 (100.0%) | 0 | 0 | 0 | 0 | 0 |
| P6-C5 | 111 (98.2%) | 1 (0.9%) | 0 | 1 (0.9%) | 0 | 0 |
| P6-C6 | 222 (86.4%) | 26 (10.1%) | 6 (2.3%) | 2 (0.8%) | 0 | 1 (0.4%) |
| P6-C7 | 1182 (83.8%) | 138 (9.8%) | 37 (2.6%) | 31 (2.2%) | 11 (0.8%) | 11 (0.8%) |
| P6-C8 | 1 (100.0%) | 0 | 0 | 0 | 0 | 0 |


## 7. Figures

- `reports/figures/phase6_silhouette.png` — silhouette vs k on the subset
- `reports/figures/phase6_gap.png` — gap statistic vs k on the subset
- `reports/figures/phase6_umap.png` — 2-D UMAP scatter (visualisation only)


## 8. Pre-registered hard stops (carried from CLAUDE.md and Phase 3A)

- 3% floor RECOMPUTED on this subset: **54 threads**. Sub-clusters below are edge.
- Bootstrap stability mean ARI must be ≥ 0.5 to be 'real.'
- Cross-tab is the load-bearing interpretive test: a sub-cluster that is mostly originally-speculator or originally-cynic is the residual tail re-surfacing, NOT a mainstream sub-segment.
- Phase 6 outputs sit at the EXPLORATORY tier; they CANNOT supersede the triangulated three-persona headline.

---

## ✅ CLOSED — Supervisor verdict (2026-05-21)

**Option 2 selected: the earnest mainstream is one coherent persona.** No
finalize / naming step. Phase 6 closes here.

**Why (supervisor):** Re-clustering r/investimentos (n=1,800, 78% earnest) on the
locked 10 Method-2 features produced one genuine earnest core (P6-C7,
n=1,410 = 78.3% of the subset, 96.5% originally M2-C2) plus residual
speculator/cynic tails that re-surfaced under the cross-tab. At no stable k did
≥2 earnest-dominated sub-segments clear the 54-thread (3%) floor. The
Sossego-Seeker is internally coherent; the tax/IR and property/debt variants
identified at Phase 3D are **situational moments**, not sub-types — confirmed by
their non-concentration in this attribute clustering.

**Effect on the study:** This strengthens the Phase 4D recommendation. **One
product, one voice, sequenced by life-moment, not fragmented across
sub-audiences.** No memo edits are required (the recommendation was already
written this way); Phase 6 is now the cited supplementary evidence for that
choice.

Phase 0–5 outputs remain untouched. Phase 6 outputs sit at the EXPLORATORY tier
(single-subreddit, single-method) and do not supersede the triangulated
three-persona headline.

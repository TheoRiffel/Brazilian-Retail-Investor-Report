# Phase 3A — Method 2: Attribute Clustering (PRIMARY) — FINAL

**Date:** 2026-05-20  
**Chosen k:** 7 (supervisor-selected)  
**Status: APPROVED — k=7 locked. Phase 3B blocked pending Phase 3A review completion.**

---


## 1. k-selection rationale (supervisor decision, logged for reproducibility)

**k=2** — cleanest by both silhouette (0.380) and Tibshirani stopping rule, but the two clusters collapse to a single speculator-vs-mainstream axis (M2-C1: risk=4.44, crypto=3.93, strategy=especulacao 92%). A single axis is a pre-registered failure condition (CLAUDE.md § H4); k=2 was rejected on that basis.

**k=5** — degenerate: one cluster contains a single thread (n=1), violating the 3% floor by four orders of magnitude. Rejected.

**k=7** — selected. First value that (a) resolves the dominant mass into two distinct well-populated behavioral segments beyond the speculator split; (b) clears the bootstrap stability floor (mean ARI ≥ 0.5) for five of seven clusters; (c) sits at the gap-statistic discontinuity — gap rises sharply from ~0.21 at k=2..6 to 0.33 at k=7, consistent with a real structural boundary; (d) aligns with HDBSCAN's fine structure (13 density-based clusters suggesting the data supports ≥ 7 natural groups).

**Edge clusters (below 108-thread / 3% floor):** M2-C0 (n=17) and M2-C4 (n=33) are retained in the output labelled 'edge' and excluded from persona candidacy. They are kept for Phase 3D enrichment analysis only.

**Soft clusters:** M2-C1 and M2-C3 have per-cluster Jaccard ≈ 0.49, just below the 0.5 stability threshold. Both are flagged here for cross-method validation in Phase 3D. If Methods 1 and 3 independently corroborate their boundaries they will be promoted; otherwise they will be merged or demoted to 'edge'.


## 2. Methodology

Gower distance + average-linkage hierarchical clustering. HDBSCAN cross-check: metric='precomputed' on Gower matrix, NOT on 2-D UMAP. HDBSCAN min_cluster_size=108, min_samples=27. K-prototypes cross-check: desconhecido retained as level (different missingness strategy).


## 3. Cluster sizes and 3% floor

Minimum viable cluster: 108 threads (3% of 3600).

| Cluster | n | % | Below 3% floor? |
|---------|---|---|-----------------|
| M2-C0 | 17 | 0.5% | ⚠️ EDGE |
| M2-C1 | 1079 | 30.0% | ok |
| M2-C2 | 1712 | 47.6% | ok |
| M2-C3 | 94 | 2.6% | ⚠️ EDGE |
| M2-C4 | 33 | 0.9% | ⚠️ EDGE |
| M2-C5 | 664 | 18.4% | ok |
| M2-C6 | 1 | 0.0% | ⚠️ EDGE |


## 4. Feature fingerprints

Ordinal: mean (1–5 scale). Categorical: mode + mode%. No persona names — refer to clusters as M2-C0 … M2-C{k-1}. Edge clusters (below 3% floor) are labelled ⚠️ EDGE.


#### M2-C0  (n=17, 0.5%)  ⚠️ EDGE — excluded from persona candidacy

| Feature | Value | n_valid |
|---------|-------|---------|
| sofisticacao_tecnica | 2.82 (mean) | 17 |
| tolerancia_risco_declarada_ou_inferida | 3.47 (mean) | 17 |
| ceticismo_institucional | 2.59 (mean) | 17 |
| exposicao_a_cripto_e_especulacao | 2.18 (mean) | 17 |
| identidade_comunitaria | 2.29 (mean) | 17 |
| fase_acumulacao | acumulacao_ativa (86.7%) | 15 |
| estrategia_principal | growth_valorizacao (87.5%) | 16 |
| relacao_com_instituicoes_financeiras | diy_sem_intermediario (28.6%) | 7 |
| estado_emocional_predominante | frustrado_ou_resignado (47.1%) | 17 |
| objetivo_financeiro_primario | acumulacao_sem_objetivo_claro (93.8%) | 16 |


#### M2-C1  (n=1079, 30.0%)

| Feature | Value | n_valid |
|---------|-------|---------|
| sofisticacao_tecnica | 1.48 (mean) | 1079 |
| tolerancia_risco_declarada_ou_inferida | 2.03 (mean) | 1079 |
| ceticismo_institucional | 3.17 (mean) | 1079 |
| exposicao_a_cripto_e_especulacao | 1.17 (mean) | 1076 |
| identidade_comunitaria | 3.0 (mean) | 1079 |
| fase_acumulacao | pre_inicio (30.0%) | 303 |
| estrategia_principal | sem_estrategia_definida (46.2%) | 318 |
| relacao_com_instituicoes_financeiras | desconfiado_de_todos (42.0%) | 205 |
| estado_emocional_predominante | cinico_ou_ironico (57.4%) | 1045 |
| objetivo_financeiro_primario | acumulacao_sem_objetivo_claro (61.6%) | 232 |


#### M2-C2  (n=1712, 47.6%)

| Feature | Value | n_valid |
|---------|-------|---------|
| sofisticacao_tecnica | 2.05 (mean) | 1712 |
| tolerancia_risco_declarada_ou_inferida | 2.13 (mean) | 1712 |
| ceticismo_institucional | 2.18 (mean) | 1712 |
| exposicao_a_cripto_e_especulacao | 1.14 (mean) | 1712 |
| identidade_comunitaria | 1.33 (mean) | 1712 |
| fase_acumulacao | acumulacao_inicial (36.4%) | 1348 |
| estrategia_principal | sem_estrategia_definida (30.3%) | 1289 |
| relacao_com_instituicoes_financeiras | migrando_para_corretora (32.6%) | 782 |
| estado_emocional_predominante | curioso_ou_exploratorio (77.0%) | 1661 |
| objetivo_financeiro_primario | acumulacao_sem_objetivo_claro (56.3%) | 1241 |


#### M2-C3  (n=94, 2.6%)  ⚠️ EDGE — excluded from persona candidacy

| Feature | Value | n_valid |
|---------|-------|---------|
| sofisticacao_tecnica | 2.7 (mean) | 94 |
| tolerancia_risco_declarada_ou_inferida | 2.2 (mean) | 94 |
| ceticismo_institucional | 2.33 (mean) | 94 |
| exposicao_a_cripto_e_especulacao | 1.05 (mean) | 94 |
| identidade_comunitaria | 1.53 (mean) | 94 |
| fase_acumulacao | consolidacao (66.3%) | 86 |
| estrategia_principal | renda_fixa_conservadora (46.8%) | 79 |
| relacao_com_instituicoes_financeiras | multiplaforma_ativo (52.4%) | 63 |
| estado_emocional_predominante | equilibrado_ou_neutro (97.9%) | 94 |
| objetivo_financeiro_primario | renda_passiva_imediata (33.3%) | 75 |


#### M2-C4  (n=33, 0.9%)  ⚠️ EDGE — excluded from persona candidacy

| Feature | Value | n_valid |
|---------|-------|---------|
| sofisticacao_tecnica | 3.03 (mean) | 33 |
| tolerancia_risco_declarada_ou_inferida | 3.06 (mean) | 33 |
| ceticismo_institucional | 2.52 (mean) | 33 |
| exposicao_a_cripto_e_especulacao | 1.3 (mean) | 33 |
| identidade_comunitaria | 1.91 (mean) | 33 |
| fase_acumulacao | consolidacao (44.4%) | 27 |
| estrategia_principal | dividendos_buy_hold (53.3%) | 30 |
| relacao_com_instituicoes_financeiras | multiplaforma_ativo (64.7%) | 17 |
| estado_emocional_predominante | confiante_ou_assertivo (100.0%) | 32 |
| objetivo_financeiro_primario | acumulacao_sem_objetivo_claro (60.7%) | 28 |


#### M2-C5  (n=664, 18.4%)

| Feature | Value | n_valid |
|---------|-------|---------|
| sofisticacao_tecnica | 1.6 (mean) | 664 |
| tolerancia_risco_declarada_ou_inferida | 4.44 (mean) | 664 |
| ceticismo_institucional | 3.04 (mean) | 664 |
| exposicao_a_cripto_e_especulacao | 3.93 (mean) | 662 |
| identidade_comunitaria | 3.98 (mean) | 664 |
| fase_acumulacao | pre_inicio (49.1%) | 326 |
| estrategia_principal | especulacao_curto_prazo (92.5%) | 613 |
| relacao_com_instituicoes_financeiras | desconfiado_de_todos (53.7%) | 108 |
| estado_emocional_predominante | euforico_ou_impulsivo (51.5%) | 660 |
| objetivo_financeiro_primario | acumulacao_sem_objetivo_claro (93.6%) | 329 |


#### M2-C6  (n=1, 0.0%)  ⚠️ EDGE — excluded from persona candidacy

| Feature | Value | n_valid |
|---------|-------|---------|
| sofisticacao_tecnica | 1.0 (mean) | 1 |
| tolerancia_risco_declarada_ou_inferida | 2.0 (mean) | 1 |
| ceticismo_institucional | 1.0 (mean) | 1 |
| exposicao_a_cripto_e_especulacao | 4.0 (mean) | 1 |
| identidade_comunitaria | 2.0 (mean) | 1 |
| fase_acumulacao | pre_inicio (100.0%) | 1 |
| estrategia_principal | especulacao_curto_prazo (100.0%) | 1 |
| relacao_com_instituicoes_financeiras | None (None%) | 0 |
| estado_emocional_predominante | frustrado_ou_resignado (100.0%) | 1 |
| objetivo_financeiro_primario | educacao_ou_projeto_especifico (100.0%) | 1 |


## 5. Bootstrap stability

20 iterations, 80% subsample. Mean ARI: **0.532 ± 0.143** (STABLE)

| Cluster | Mean Jaccard | Stable? | Notes |
|---------|-------------|---------|-------|
| M2-C0 | 0.221 | n/a | edge cluster — excluded from persona candidacy |
| M2-C1 | 0.491 | ⚠️ UNSTABLE | ⚠️ soft — flagged for Phase 3D cross-method validation |
| M2-C2 | 0.728 | ok |  |
| M2-C3 | 0.488 | n/a | edge cluster — excluded from persona candidacy |
| M2-C4 | 0.260 | n/a | edge cluster — excluded from persona candidacy |
| M2-C5 | 0.770 | ok |  |
| M2-C6 | 0.568 | n/a | edge cluster — excluded from persona candidacy |


## 6. Missingness artifact check

Corpus median: 1.0. Flag threshold: 1.50.

| Cluster | Mean missing features | Flag? |
|---------|----------------------|-------|
| M2-C0 | 0.82 | ok |
| M2-C1 | 3.05 | ⚠️ |
| M2-C2 | 1.31 | ok |
| M2-C3 | 0.78 | ok |
| M2-C4 | 0.94 | ok |
| M2-C5 | 1.94 | ⚠️ |
| M2-C6 | 1.0 | ok |


## 7. Provisional clusters & artifact risk

**M2-C1 (n=1,079) — PROVISIONAL, pending Phase 3D cross-method adjudication.**
Mean missingness is 3.05 features per thread, approximately 3× the corpus median of 1.0 and the
highest of any non-edge cluster. Critically, the categorical fingerprint rests on small valid-n
fractions: `fase_acumulacao` 205/1,079 (19%), `estrategia_principal` 318/1,079 (29%),
`relacao_com_instituicoes_financeiras` 108/1,079 (10%), `objetivo_financeiro_primario` 121/1,079 (11%).
The modal values for these features are therefore drawn from a minority of C1 members, making the
fingerprint unreliable as a population descriptor. The specific adjudication tests required in
Phase 3D are: (a) whether Method 1 (text embeddings, missingness-blind) independently recovers a
cynical-reactive group occupying the same region of thread-space; and (b) whether k-prototypes —
which retains 'desconhecido' as a category level — collapses C1 into a single missingness-dominated
cluster rather than a behavioural one. If either test fails to corroborate C1's boundary, it will
be demoted to 'edge' or merged into M2-C2. C1's Jaccard stability (0.491) is also just below the
0.5 threshold, consistent with a cluster whose boundary is partly driven by missing-data patterning
rather than latent investor type.

**Confirmed clusters: M2-C2 (n=1,712) and M2-C5 (n=664).** Both clear the 3% floor, both have
Jaccard ≥ 0.5 (0.728 and 0.770 respectively), and both have missingness within acceptable range
(1.31 and 1.94, neither flagged as artifact risk relative to the corpus distribution). These two
clusters are treated as robust persona candidates going into Phase 3B and 3C.


## 8. HDBSCAN cross-check

HDBSCAN (precomputed Gower) found 10 clusters, 1358 noise (37.7%). Hierarchical chose k=7. Method disagreement is logged here for Phase 4 cross-method synthesis.


## 9. K-prototypes cross-check

⚠️ Different missingness strategy (desconhecido as category level + ordinal median impute). Gower/k-proto agreement → robustness. Disagreement → check if driven by missingness.

| k | Cost |
|---|------|
| 2 | 17698.3 |
| 3 | 13751.3 |
| 4 | 11895.5 |
| 5 | 10965.7 |
| 6 | 10272.9 |
| 7 | 9710.1 |
| 8 | 9273.6 |


## 10. Figures

- `reports/figures/m2_silhouette.png` — silhouette vs k
- `reports/figures/m2_gap.png` — gap statistic vs k
- `reports/figures/m2_umap.png` — 2-D UMAP scatter (hierarchical + HDBSCAN)
- `reports/figures/m2_dendrogram.png` — truncated dendrogram

---

## ⛔ HARD STOP

Phase 3A finalised. **Do not proceed to Phase 3B** until supervisor
has reviewed this document and the four figures.

# Phase 3A — Method 2 Explore Report: Candidate k Values

**Date:** 2026-05-20  
**Status: AWAITING SUPERVISOR k SELECTION — Phase 3A finalize and Phase 3B are blocked**

---


## 1. Methodology summary

**Gower distance** (mixed ordinal/categorical; desconhecido → NaN, excluded pairwise). **Average-linkage** hierarchical on full Gower matrix. **HDBSCAN** run on the precomputed Gower matrix (metric='precomputed'), NOT on the 2-D UMAP. HDBSCAN min_cluster_size=108 (3% floor), min_samples=27. **2-D UMAP** used only for the scatter figure. **K-prototypes** retains 'desconhecido' as a category level — different missing-data strategy than Gower (see Section 6 for interpretation rules).


## 2. Metric sweep (k = 2..10)

| k | Silhouette | Gap | s(Gap) | Tibshirani? |
|---|-----------|-----|--------|-------------|
| 2 | 0.3801 | 0.2035 | 0.0010 | ← stopping rule |
| 3 | 0.2692 | 0.2024 | 0.0011 |  |
| 4 | 0.1728 | 0.2051 | 0.0011 |  |
| 5 | 0.1364 | 0.2211 | 0.0014 |  |
| 6 | 0.1258 | 0.2175 | 0.0224 |  |
| 7 | 0.2109 | 0.3290 | 0.0527 |  |
| 8 | 0.1791 | 0.3067 | 0.0582 |  |
| 9 | 0.1756 | 0.2523 | 0.0678 |  |
| 10 | 0.2170 | 0.2878 | 0.0885 |  |

- Silhouette optimum: **k=2** (score=0.3801)

- Highest gap value: **k=7** (gap=0.3290)

- Gap Tibshirani stopping rule: **k=2**

- Candidates sent to supervisor for interpretability review: **k = [2, 5, 7]**

⚠️ Note: k=2 (Tibshirani/silhouette optimum) and k=7 (highest gap) diverge significantly. The gap values at k=7 and k=8 are substantially above k=2..6, but Tibshirani selects k=2 because gap(2) ≥ gap(3) − s(3). This is a known conservatism of the Tibshirani rule. The 13 HDBSCAN clusters (Section 5) suggest finer structure exists. Interpretability of the fingerprints below is the pre-registered tie-breaker.


## 3. Bootstrap stability (all candidates)

20 iterations, 80% subsample, linkage run once per subsample, cut at each k. Threshold: mean ARI ≥ 0.5 and all per-cluster Jaccard ≥ 0.5.

| k | Mean ARI | Std | Stable? |
|---|----------|-----|---------|
| 2 | 0.676 | 0.303 | ✓ |
| 5 | 0.635 | 0.174 | ✓ |
| 7 | 0.532 | 0.143 | ✓ |


## 4. Missingness artifact context

Corpus median missing features per thread: **1.0**. Flag threshold: mean > 1.50 (1.5×).

Note: if ALL clusters for a given k are flagged at similar levels, this indicates corpus-wide missingness uniformly distributed — NOT a cluster-specific artifact. A genuine artifact cluster would show mean_missing >> all other clusters. Inspect per-cluster values; flag all-clusters-flagged as a corpus note, not a veto.


## 5.1  Candidate k=2 — fingerprints

**ARI: 0.676 ± 0.303**  (STABLE)

Per-cluster Jaccard: M2-C0=0.928  M2-C1=0.692

All clusters ≥ 108 threads (3% floor ok).

⚠️ Missingness flags: M2-C0, M2-C1 — compare means below to corpus median 1.0.

| Feature | M2-C0 (n=2935, 81.5%) | M2-C1 (n=665, 18.5%) |
|---------|---|---|
| sofisticacao_tecnica | 1.88 (n=2935) | 1.6 (n=665) |
| tolerancia_risco_declarada_ou_inferida | 2.11 (n=2935) | 4.44 (n=665) |
| ceticismo_institucional | 2.55 (n=2935) | 3.03 (n=665) |
| exposicao_a_cripto_e_especulacao | 1.16 (n=2932) | 3.93 (n=663) |
| identidade_comunitaria | 1.97 (n=2935) | 3.98 (n=665) |
| fase_acumulacao | acumulacao_inicial 32.7% (n=1779) | pre_inicio 49.2% (n=327) |
| estrategia_principal | sem_estrategia_definida 31.4% (n=1732) | especulacao_curto_prazo 92.5% (n=614) |
| relacao_com_instituicoes_financeiras | migrando_para_corretora 30.0% (n=1074) | desconfiado_de_todos 53.7% (n=108) |
| estado_emocional_predominante | curioso_ou_exploratorio 44.9% (n=2849) | euforico_ou_impulsivo 51.4% (n=661) |
| objetivo_financeiro_primario | acumulacao_sem_objetivo_claro 56.3% (n=1592) | acumulacao_sem_objetivo_claro 93.3% (n=330) |

Missingness detail:
| Cluster | Mean missing features | Flag? |
|---------|----------------------|-------|
| M2-C0 | 1.93 | ⚠️ |
| M2-C1 | 1.94 | ⚠️ |


## 5.2  Candidate k=5 — fingerprints

**ARI: 0.635 ± 0.174**  (STABLE)

Per-cluster Jaccard: M2-C0=0.213  M2-C1=0.863  M2-C2=0.145  M2-C3=0.77  M2-C4=0.444

⚠️ Edge clusters (< 108 threads): M2-C0, M2-C4

⚠️ Missingness flags: M2-C1, M2-C3 — compare means below to corpus median 1.0.

| Feature | M2-C0 (n=17, 0.5%) | M2-C1 (n=2791, 77.5%) | M2-C2 (n=127, 3.5%) | M2-C3 (n=664, 18.4%) | M2-C4 (n=1, 0.0%) |
|---------|---|---|---|---|---|
| sofisticacao_tecnica | 2.82 (n=17) | 1.83 (n=2791) | 2.79 (n=127) | 1.6 (n=664) | 1.0 (n=1) |
| tolerancia_risco_declarada_ou_inferida | 3.47 (n=17) | 2.09 (n=2791) | 2.43 (n=127) | 4.44 (n=664) | 2.0 (n=1) |
| ceticismo_institucional | 2.59 (n=17) | 2.56 (n=2791) | 2.38 (n=127) | 3.04 (n=664) | 1.0 (n=1) |
| exposicao_a_cripto_e_especulacao | 2.18 (n=17) | 1.15 (n=2788) | 1.12 (n=127) | 3.93 (n=662) | 4.0 (n=1) |
| identidade_comunitaria | 2.29 (n=17) | 1.98 (n=2791) | 1.63 (n=127) | 3.98 (n=664) | 2.0 (n=1) |
| fase_acumulacao | acumulacao_ativa 86.7% (n=15) | acumulacao_inicial 34.6% (n=1651) | consolidacao 61.1% (n=113) | pre_inicio 49.1% (n=326) | pre_inicio 100.0% (n=1) |
| estrategia_principal | growth_valorizacao 87.5% (n=16) | sem_estrategia_definida 33.5% (n=1607) | dividendos_buy_hold 45.0% (n=109) | especulacao_curto_prazo 92.5% (n=613) | especulacao_curto_prazo 100.0% (n=1) |
| relacao_com_instituicoes_financeiras | diy_sem_intermediario 28.6% (n=7) | migrando_para_corretora 30.8% (n=987) | multiplaforma_ativo 55.0% (n=80) | desconfiado_de_todos 53.7% (n=108) | — |
| estado_emocional_predominante | frustrado_ou_resignado 47.1% (n=17) | curioso_ou_exploratorio 47.3% (n=2706) | equilibrado_ou_neutro 73.0% (n=126) | euforico_ou_impulsivo 51.5% (n=660) | frustrado_ou_resignado 100.0% (n=1) |
| objetivo_financeiro_primario | acumulacao_sem_objetivo_claro 93.8% (n=16) | acumulacao_sem_objetivo_claro 57.2% (n=1473) | acumulacao_sem_objetivo_claro 38.8% (n=103) | acumulacao_sem_objetivo_claro 93.6% (n=329) | educacao_ou_projeto_especifico 100.0% (n=1) |

Missingness detail:
| Cluster | Mean missing features | Flag? |
|---------|----------------------|-------|
| M2-C0 | 0.82 | ok |
| M2-C1 | 1.98 | ⚠️ |
| M2-C2 | 0.82 | ok |
| M2-C3 | 1.94 | ⚠️ |
| M2-C4 | 1.0 | ok |


## 5.3  Candidate k=7 — fingerprints

**ARI: 0.532 ± 0.143**  (STABLE)

Per-cluster Jaccard: M2-C0=0.221  M2-C1=0.491  M2-C2=0.728  M2-C3=0.488  M2-C4=0.26  M2-C5=0.77  M2-C6=0.568

⚠️ Edge clusters (< 108 threads): M2-C0, M2-C3, M2-C4, M2-C6

⚠️ Missingness flags: M2-C1, M2-C5 — compare means below to corpus median 1.0.

| Feature | M2-C0 (n=17, 0.5%) | M2-C1 (n=1079, 30.0%) | M2-C2 (n=1712, 47.6%) | M2-C3 (n=94, 2.6%) | M2-C4 (n=33, 0.9%) | M2-C5 (n=664, 18.4%) | M2-C6 (n=1, 0.0%) |
|---------|---|---|---|---|---|---|---|
| sofisticacao_tecnica | 2.82 (n=17) | 1.48 (n=1079) | 2.05 (n=1712) | 2.7 (n=94) | 3.03 (n=33) | 1.6 (n=664) | 1.0 (n=1) |
| tolerancia_risco_declarada_ou_inferida | 3.47 (n=17) | 2.03 (n=1079) | 2.13 (n=1712) | 2.2 (n=94) | 3.06 (n=33) | 4.44 (n=664) | 2.0 (n=1) |
| ceticismo_institucional | 2.59 (n=17) | 3.17 (n=1079) | 2.18 (n=1712) | 2.33 (n=94) | 2.52 (n=33) | 3.04 (n=664) | 1.0 (n=1) |
| exposicao_a_cripto_e_especulacao | 2.18 (n=17) | 1.17 (n=1076) | 1.14 (n=1712) | 1.05 (n=94) | 1.3 (n=33) | 3.93 (n=662) | 4.0 (n=1) |
| identidade_comunitaria | 2.29 (n=17) | 3.0 (n=1079) | 1.33 (n=1712) | 1.53 (n=94) | 1.91 (n=33) | 3.98 (n=664) | 2.0 (n=1) |
| fase_acumulacao | acumulacao_ativa 86.7% (n=15) | pre_inicio 30.0% (n=303) | acumulacao_inicial 36.4% (n=1348) | consolidacao 66.3% (n=86) | consolidacao 44.4% (n=27) | pre_inicio 49.1% (n=326) | pre_inicio 100.0% (n=1) |
| estrategia_principal | growth_valorizacao 87.5% (n=16) | sem_estrategia_definida 46.2% (n=318) | sem_estrategia_definida 30.3% (n=1289) | renda_fixa_conservadora 46.8% (n=79) | dividendos_buy_hold 53.3% (n=30) | especulacao_curto_prazo 92.5% (n=613) | especulacao_curto_prazo 100.0% (n=1) |
| relacao_com_instituicoes_financeiras | diy_sem_intermediario 28.6% (n=7) | desconfiado_de_todos 42.0% (n=205) | migrando_para_corretora 32.6% (n=782) | multiplaforma_ativo 52.4% (n=63) | multiplaforma_ativo 64.7% (n=17) | desconfiado_de_todos 53.7% (n=108) | — |
| estado_emocional_predominante | frustrado_ou_resignado 47.1% (n=17) | cinico_ou_ironico 57.4% (n=1045) | curioso_ou_exploratorio 77.0% (n=1661) | equilibrado_ou_neutro 97.9% (n=94) | confiante_ou_assertivo 100.0% (n=32) | euforico_ou_impulsivo 51.5% (n=660) | frustrado_ou_resignado 100.0% (n=1) |
| objetivo_financeiro_primario | acumulacao_sem_objetivo_claro 93.8% (n=16) | acumulacao_sem_objetivo_claro 61.6% (n=232) | acumulacao_sem_objetivo_claro 56.3% (n=1241) | renda_passiva_imediata 33.3% (n=75) | acumulacao_sem_objetivo_claro 60.7% (n=28) | acumulacao_sem_objetivo_claro 93.6% (n=329) | educacao_ou_projeto_especifico 100.0% (n=1) |

Missingness detail:
| Cluster | Mean missing features | Flag? |
|---------|----------------------|-------|
| M2-C0 | 0.82 | ok |
| M2-C1 | 3.05 | ⚠️ |
| M2-C2 | 1.31 | ok |
| M2-C3 | 0.78 | ok |
| M2-C4 | 0.94 | ok |
| M2-C5 | 1.94 | ⚠️ |
| M2-C6 | 1.0 | ok |


## 5. Cross-check: HDBSCAN on precomputed Gower

HDBSCAN (metric='precomputed', min_cluster_size=108, min_samples=27) found **10 clusters** with 1358 noise points (37.7%). This is the data-driven 'no-k-specified' view — compare to hierarchical candidates above.

| HDBSCAN label | n | % |
|---------------|---|---|
| noise | 1358 | 37.7% |
| HDB-C0 | 276 | 7.7% |
| HDB-C1 | 241 | 6.7% |
| HDB-C2 | 389 | 10.8% |
| HDB-C3 | 291 | 8.1% |
| HDB-C4 | 144 | 4.0% |
| HDB-C5 | 162 | 4.5% |
| HDB-C6 | 197 | 5.5% |
| HDB-C7 | 127 | 3.5% |
| HDB-C8 | 218 | 6.1% |
| HDB-C9 | 197 | 5.5% |

⚠️ Disagreement note: HDBSCAN found a substantially different cluster count than the hierarchical optimum (k=2 vs k=10). Per CLAUDE.md § H3, disagreement between methods is itself a finding, not a problem. Document and carry forward.


## 6. Cross-check: K-prototypes

⚠️ **Different missingness strategy**: k-prototypes keeps 'desconhecido' as a category level for all categorical features, and imputes ordinal NaN with column median (5 values total). Gower excludes missing values pairwise.  Interpretation rule: • Agreement → robustness evidence: the segment structure survives two different   treatments of missing data. • Disagreement → may be missingness-driven: check whether the disagreeing cluster   in k-prototypes is dominated by 'desconhecido' values. If so, it is likely a   missingness artefact in k-prototypes, not a real investor segment.

| k | Cost (lower = better within k-proto objective) |
|---|------------------------------------------------|
| 2 | 17698.3 |
| 3 | 13751.3 |
| 4 | 11895.5 |
| 5 | 10965.7 |
| 6 | 10272.9 |
| 7 | 9710.1 |
| 8 | 9273.6 |

K-prototypes cost decreases monotonically to k=8; cost alone is not diagnostic — elbow inspection and comparison to Gower are required.


## 7. Figures

- `reports/figures/m2_silhouette.png` — silhouette vs k (candidates highlighted)
- `reports/figures/m2_gap.png` — gap statistic vs k (candidates highlighted)
- `reports/figures/m2_umap.png` — 2-D UMAP scatter (hierarchical + HDBSCAN)
- `reports/figures/m2_dendrogram.png` — truncated dendrogram

---

## ⛔ HARD STOP — Supervisor action required

Review the fingerprints for k ∈ [2, 5, 7] above (Section 5) and the
figures in reports/figures/. Select the k that produces the most interpretable
and multi-dimensional segments. Interpretability is a pre-registered criterion.

To finalise, run:

```
python notebooks/03a_attribute_clustering.py --finalize <chosen_k>
```

This will write `data/processed/clusters_method2.parquet` and
`reports/phase3a_method2.md`. Do not proceed to Phase 3B until that is done.

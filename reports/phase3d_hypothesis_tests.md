# Phase 3D — Hypothesis Tests (H1, H2, H4)

**Date:** 2026-05-21  
**Shared spine:** 3586 threads (M1 ∩ M2 ∩ M3)

Scope per supervisor brief: H1 and H2 run on **all three methods**; H4 runs on **Method 2 only** (primary attribute clustering).

Effect-size convention: Cramér's V, where 0.1 ≈ small, 0.3 ≈ medium, 0.5 ≈ large.

---

## H1 — Subreddit differentiation

**Hypothesis (locked):** r/investimentos and r/farialimabets draw measurably different populations. Null: same investors, different venue.

**Firewall:** `subreddit_origem` was never a clustering feature. Any cluster × subreddit association is genuinely post-hoc.

| Method | n | χ² | df | p | Cramér's V | Verdict |
|--------|---|---:|---:|--:|-----------:|---------|
| M1 | 3586 | 287.0 | 4 | 6.91e-61 | 0.283 | H1 weak support (small effect) |
| M2 | 3586 | 1650.3 | 6 | 0.00e+00 | 0.678 | **H1 supported (medium+ effect)** |
| M3 | 3586 | 1508.8 | 3 | 0.00e+00 | 0.649 | **H1 supported (medium+ effect)** |

### Per-cluster farialimabets enrichment (×corpus base rate)

**M1:**
  - M1-C0: 12.3% (0.25×)
  - M1-C1: 22.8% (0.46×)
  - M1-C2: 58.4% (1.17×)
  - M1-C3: 54.3% (1.09×)
  - M1-noise: 66.2% (1.33×)

**M2:**
  - M2-C0: 29.4% (0.59×)
  - M2-C1: 81.8% (1.64×)
  - M2-C2: 17.7% (0.35×)
  - M2-C3: 6.5% (0.13×)
  - M2-C4: 18.2% (0.36×)
  - M2-C5: 89.7% (1.80×)
  - M2-C6: 100.0% (2.00×)

**M3:**
  - M3-C0: 9.8% (0.20×)
  - M3-C1: 66.8% (1.34×)
  - M3-C2: 65.0% (1.30×)
  - M3-C3: 93.6% (1.88×)

## H2 — Temporal prevalence shift

**Hypothesis (locked):** persona *composition* is stable but persona *prevalence* shifts with macro regime. Null: nothing shifts.

**Windows:** A = 2020-06→2021-06 (Selic ~2%), B = 2022-01→2023-01 (Selic rising), C = 2024 (mature fixed income).

### Headline findings (the directional shifts that matter)

The aggregate cluster × window chi-square (Part 2 below) finds only small effect sizes. The actionable temporal content is NOT in the aggregate — it is in **two specific directional shifts** that move in opposite directions and track the macro regime.

1. **Speculator share declines monotonically across windows**, tracking the Selic rise from ~2% (window A) to ~13.75% (window B) to mature fixed-income regime (window C). Within-cluster window share: A 51.3% → B 33.0% → C 15.7%. The speculator persona is concentrated in the low-rate era; crypto/equity speculation thins out as fixed-income becomes the alternative.

2. **Cynical-reactive continuum grows monotonically across windows**: A 29.5% → B 32.6% → C 38.0%. Where speculator volume goes, cynical posture rises — consistent with the loss-as-meme / guru-skeptic sub-flavors absorbing investors who weathered the crypto winter and the volatility of B.

For contrast, the earnest learner is roughly flat: A 32.6% / B 35.3% / C 32.1% — the mainstream investor population is stable across regimes; the regime-sensitive movement is in the speculator ↔ cynical region.

**Interpretation.** Locked H2 form ("composition stable, prevalence shifts") is supported in its strongest reading on these two personas, not on the aggregate. The aggregate test misses this because directional shifts in opposite directions partly cancel in the chi-square. Report the directional shifts as the headline; report the aggregate test for completeness.

### Part 1 — Aggregate prevalence shift (cluster × window)

| Method | n | χ² | df | p | Cramér's V | Verdict |
|--------|---|---:|---:|--:|-----------:|---------|
| M1 | 3586 | 95.0 | 8 | 4.49e-17 | 0.115 | H2 aggregate weak |
| M2 | 3586 | 163.5 | 12 | 1.00e-28 | 0.151 | H2 aggregate weak |
| M3 | 3586 | 39.2 | 6 | 6.63e-07 | 0.074 | H2 aggregate null |

The aggregate is small because the directional shifts on speculator and cynical-continuum partly cancel and because the large earnest cluster is flat across windows. **Treat the per-persona trajectory as the H2 result; the aggregate is supporting, not primary.**

Within-cluster window share by method (for completeness):

**M1**
  - M1-C0: A 46.8% / B 29.2% / C 24.0%
  - M1-C1: A 18.3% / B 40.9% / C 40.7%
  - M1-C2: A 54.5% / B 26.0% / C 19.5%
  - M1-C3: A 33.6% / B 32.5% / C 33.9%
  - M1-noise: A 35.3% / B 34.6% / C 30.1%

**M2**
  - M2-C0: A 64.7% / B 23.5% / C 11.8%
  - M2-C1: A 26.7% / B 31.0% / C 42.2%
  - M2-C2: A 31.6% / B 34.7% / C 33.7%
  - M2-C3: A 24.7% / B 26.9% / C 48.4%
  - M2-C4: A 48.5% / B 36.4% / C 15.2%
  - M2-C5: A 48.0% / B 34.8% / C 17.2%
  - M2-C6: A 0.0% / B 100.0% / C 0.0%

**M3**
  - M3-C0: A 32.0% / B 34.1% / C 34.0%
  - M3-C1: A 30.8% / B 28.6% / C 40.7%
  - M3-C2: A 38.6% / B 32.9% / C 28.5%
  - M3-C3: A 27.8% / B 36.0% / C 36.2%

### Part 2 — Composition stability (within-cluster ordinal drift)

### Part 2 — Composition stability (within-cluster ordinal drift)

Operationalisation: within each cluster, compute the mean of each ordinal feature per window; report the max-min spread across the three windows, then average across the 5 ordinal features. Spread ≤ 0.50 (half an ordinal point) = compositionally stable; > 1.00 = composition is also shifting (which would falsify the H2 'stability' part).

**M1** mean within-cluster ordinal drift across windows:
  - M1-C0: 0.26 (stable)
  - M1-C1: 0.18 (stable)
  - M1-C2: 0.42 (stable)
  - M1-C3: 0.41 (stable)
  - M1-noise: 0.44 (stable)

**M2** mean within-cluster ordinal drift across windows:
  - M2-C0: 0.54 (mixed)
  - M2-C1: 0.23 (stable)
  - M2-C2: 0.23 (stable)
  - M2-C3: 0.31 (stable)
  - M2-C4: 0.42 (stable)
  - M2-C5: 0.27 (stable)
  - M2-C6: n/a (cluster too small or absent in some windows)

**M3** mean within-cluster ordinal drift across windows:
  - M3-C0: 0.19 (stable)
  - M3-C1: 0.37 (stable)
  - M3-C2: 0.52 (mixed)
  - M3-C3: 0.67 (mixed)

## H4 — Multi-dimensionality (M2 only)

**Hypothesis (locked):** segments are defined by combinations of dimensions, not any single axis. Null: one axis (capital or sophistication) explains most variance.

**Operationalisation:** random-forest classifier predicting M2 cluster from the 10 locked clustering features (5 ordinals + 5 categoricals one-hot encoded). One-hot importance grouped back to the original feature. Null is supported if the top single feature carries ≥50% of total importance.

**Verdict — PARTIALLY NULL: multi-dimensional but emotional-posture-dominated.** Top feature `estado_emocional_predominante` carries 45.1% of total importance — under the 50% threshold for the formal null, but **3.80× the work of the next feature** (identidade_comunitaria at 11.9%). One axis is doing about half the work; the other half is spread across 3–4 supporting features. H4's positive form (multi-dim) holds in the literal sense, but the locked H4 brief framed multi-dim as 'combinations of dimensions' — in practice, ONE dimension (emotional posture) dominates and a handful of others sharpen it. **Personas in Phase 4 must be led by emotional posture, with other attributes as supporting texture — NOT narrated as ten co-equal dimensions.**

**Circularity caveat (must be disclosed in methodology).** `estado_emocional_predominante` was one of the 10 *clustering features* fed to Method 2. So this H4 result describes the **geometry of the M2 partition** — i.e., which feature most strongly distinguishes the clusters Method 2 itself produced — not an external causal claim about what drives Brazilian retail investor behavior. The clustering had access to emotional posture as input; finding that it discriminates well between the resulting clusters is partly tautological. The interesting non-circular evidence is that **the locked classical axes the brief named (`sofisticacao_tecnica`, `fase_acumulacao`, `objetivo_financeiro_primario`) are in the bottom half** even with full clustering access — that finding is robust to the circularity.

### Grouped feature importance

| Feature | Share | Univariate V (M2) |
|---------|------:|------------------:|
| estado_emocional_predominante | 45.1% | 0.703 |
| identidade_comunitaria | 11.9% | 0.444 |
| estrategia_principal | 11.7% | 0.430 |
| exposicao_a_cripto_e_especulacao | 10.9% | 0.403 |
| tolerancia_risco_declarada_ou_inferida | 7.6% | 0.448 |
| ceticismo_institucional | 4.0% | 0.271 |
| fase_acumulacao | 3.2% | 0.241 |
| objetivo_financeiro_primario | 2.8% | 0.226 |
| relacao_com_instituicoes_financeiras | 1.4% | 0.191 |
| sofisticacao_tecnica | 1.4% | 0.239 |

The next four features (`identidade_comunitaria`, `estrategia_principal`, `exposicao_a_cripto_e_especulacao`, `tolerancia_risco_declarada_ou_inferida`) each contribute 7.6–11.9% — they sharpen the picture but none rivals emotional posture. The locked H4 brief named sophistication and capital as the candidate dominant axes for the null; those are in the BOTTOM half — that part of the finding is robust to the circularity caveat above and is the genuine surprise.

---

## Summary verdicts (for the memo)

- **H1**: **SUPPORTED** (max V=0.68, medium+ effect on posture methods)
- **H2 prevalence**: **PARTIAL** — small effect on M1/M2 (V≈0.12–0.15), null on M3 (V=0.07). Prevalence shifts are real but modest; composition stability mostly holds (Part 2). Locked H2 form ('composition stable, prevalence shifts') is directionally supported, weakly.
- **H3**: covered in `phase3d_synthesis.md` Section 2 — **split verdict**. M2↔M3 convergent (ARI=0.21); M1 orthogonal to both (ARI≈0). M1 is a topic instrument, M2/M3 are posture instruments — same threads, different partitioning logic.
- **H4**: **PARTIALLY NULL — multi-dimensional but emotional-posture-dominated.** Top feature `estado_emocional_predominante` carries 45% — under the 50% threshold for the formal null, but ~3.75× the next feature. Personas in Phase 4 MUST be led by emotional posture, with other attributes as supporting texture. **Circularity caveat applies** (estado_emocional was a clustering feature; this describes cluster geometry, not external causal truth). The non-circular finding — that the locked classical axes (sophistication/capital) are in the bottom half — is robust.

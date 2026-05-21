# Phase 3D — Cross-Method Synthesis (candidate evidence)

**Date:** 2026-05-21  
**Status: SUPERVISOR-APPROVED with carry-forwards (2026-05-21). Phase 4 BLOCKED until brief issued.**

Approval notes (4 carry-forwards locked in `reports/decisions_log.md`): (1) H4 relabelled PARTIALLY NULL + posture-dominated + circularity caveat; (2) H2 headline is the two directional shifts (speculator↓, cynical↑), not the weak aggregate; (3) counting convention — Phase 4 uses M2 partition as mutually-exclusive backbone for stated proportions, M3/M1 characterize but don't re-count; (4) topical subsets demoted from candidate personas to earnest-learner sub-themes (single-method evidence).

---

## 1. Scope and inputs

Shared spine: **3586 threads** present in all three methods (M1 HDBSCAN, M2 attribute k-medoids, M3 LLM-hierarchical k-medoids). 14 threads dropped where M3 summarisation failed (already disclosed in Phase 3C).

Phase 3D is the **analytical convergence phase**: it tests H1/H2/H3/H4 and produces evidence rows for Phase 4. It does NOT name personas — that is Phase 4's job. Persona language here is descriptive shorthand.

Hypothesis tests live in `phase3d_hypothesis_tests.md` (this report links to numbers; that report carries the full statistical tables).

## 2. Cross-method convergence (H3)

**Pairwise ARI** (Adjusted Rand Index — 0 random, 1 perfect):

| Pair | ARI |
|------|-----|
| M1 × M2 | -0.003 |
| M1 × M3 | -0.009 |
| M2 × M3 | 0.212 |

**Interpretation — H3 split verdict.** M2 and M3 converge meaningfully (ARI 0.212): two independent algorithms operating on different inputs (structured attributes vs. holistic LLM summaries) agree on coarse structure while disagreeing on fine splits. That is **H3's predicted positive form**.

M1 (HDBSCAN on raw embeddings), by contrast, is **essentially orthogonal** to both posture methods (ARI ≈ 0 with M2 *and* M3). This is NOT a failure — it is a finding. M1's clusters are topical density spikes (tax/IR, property/debt, crypto) sitting inside a giant mainstream bucket; M2 and M3 split the corpus along posture axes that cut across topics. Same threads, different partitioning logic, near-zero rand agreement at the *global* partition level.

The right way to read M1's contribution is in the cross-tab overrepresentation table (Phase 3C Section 10), not in ARI. M1-C2 (crypto) is 2.06× overrepresented in the M3 speculator cluster; M1-C0 (tax/IR) is 1.9× overrepresented in the M3 earnest cluster — strong *local* signals invisible to global ARI because the bulk of M1 lives in one giant cluster.

See `reports/figures/phase3d_ari_matrix.png` for the matrix; per-method cross-tabs are in `phase3c_method3.md` Sections 9–10.

## 3. Method-robust cores (co-cluster table)

Triples (M1, M2, M3) with at least 30 threads on the shared spine (~0.8% of corpus floor for the triple — not the 3% persona floor).

| M1 | M2 | M3 | n | % corpus | farialimabets share | farialimabets overrep | top examples |
|----|----|----|---|---------:|--------------------:|----------------------:|--------------|
| M1-C3 | M2-C2 | M3-C0 | 690 | 19.2% | 5.4% | 0.11× | isrrdx; i1rnpd; j5hmst |
| M1-C3 | M2-C1 | M3-C3 | 302 | 8.4% | 97.4% | 1.95× | iadcs2; lghsfv; hsxo4r |
| M1-C3 | M2-C2 | M3-C2 | 292 | 8.1% | 37.7% | 0.76× | lahp9c; i0ocgq; hlg10i |
| M1-C3 | M2-C5 | M3-C2 | 269 | 7.5% | 92.6% | 1.86× | l79h3l; nceg2t; jxreqa |
| M1-C3 | M2-C1 | M3-C2 | 233 | 6.5% | 85.0% | 1.70× | lcs829; jbonc0; nmypd1 |
| M1-C1 | M2-C2 | M3-C0 | 229 | 6.4% | 6.1% | 0.12× | n0gwny; lz3uw9; k83yam |
| M1-C3 | M2-C1 | M3-C1 | 190 | 5.3% | 86.3% | 1.73× | ka90a2; nublzn; mt2lsw |
| M1-C3 | M2-C5 | M3-C3 | 138 | 3.8% | 98.6% | 1.98× | tf9epl; 1el62zq; n007kv |
| M1-C0 | M2-C2 | M3-C0 | 87 | 2.4% | 8.0% | 0.16× | l0g9m6; mq8iqc; lzutc1 |
| M1-C3 | M2-C2 | M3-C1 | 82 | 2.3% | 30.5% | 0.61× | k6olwt; lpxrs0; lp4un6 |
| M1-C2 | M2-C5 | M3-C2 | 73 | 2.0% | 67.1% | 1.35× | o0f467; nczoq9; n7vezh |
| M1-noise | M2-C2 | M3-C0 | 65 | 1.8% | 15.4% | 0.31× | ly1vfn; maw74d; nhsurw |
| M1-C1 | M2-C2 | M3-C2 | 60 | 1.7% | 26.7% | 0.53× | o7ekox; jhb9q4; lmqq0k |
| M1-noise | M2-C1 | M3-C3 | 59 | 1.6% | 94.9% | 1.90× | umze6k; ugezdu; 1b1aycr |
| M1-C3 | M2-C1 | M3-C0 | 53 | 1.5% | 35.8% | 0.72× | k1t5yg; lp8t19; jkps7v |
| M1-C3 | M2-C3 | M3-C0 | 52 | 1.5% | 5.8% | 0.12× | ntptv1; ma046q; oacz2y |
| M1-noise | M2-C2 | M3-C2 | 49 | 1.4% | 40.8% | 0.82× | jl6jyw; iaasq3; mm4y5p |
| M1-noise | M2-C1 | M3-C2 | 49 | 1.4% | 89.8% | 1.80× | mvga9d; vqn2et; 10hybre |
| M1-C3 | M2-C2 | M3-C3 | 40 | 1.1% | 82.5% | 1.65× | j70u7k; gz5twz; vuarrm |
| M1-C1 | M2-C1 | M3-C0 | 40 | 1.1% | 22.5% | 0.45× | nzvnzo; jvcids; jfqdpp |
| M1-C1 | M2-C1 | M3-C2 | 38 | 1.1% | 47.4% | 0.95× | vynqk6; zi6qhg; sxzmef |
| M1-noise | M2-C5 | M3-C2 | 37 | 1.0% | 89.2% | 1.79× | t66pof; 1etvujm; 1ekpu2w |
| M1-noise | M2-C1 | M3-C1 | 35 | 1.0% | 85.7% | 1.72× | leb9wc; k77vjk; l1maqn |
| M1-C3 | M2-C5 | M3-C1 | 32 | 0.9% | 96.9% | 1.94× | ncchod; nbvp16; luqi2j |
| M1-C1 | M2-C1 | M3-C3 | 30 | 0.8% | 76.7% | 1.54× | zf74vc; sa9ysg; 1gjupbm |

Triples with farialimabets overrepresentation ≥1.5× sit in the speculator/cynical region (the part of the corpus where farialimabets dominates). Triples with overrepresentation <0.7× are earnest-learner / topical territory dominated by r/investimentos.

## 4. Candidate persona rows (NOT final personas)

Phase 4 names and narrates personas. Phase 3D supplies the evidence rows. The cynical region is ONE row, flagged fuzzy (supervisor verdict 2026-05-21, `reports/decisions_log.md`).

**Counting convention:** crisp rows use the INTERSECTION of partner clusters (M2 ∩ M3, high-confidence convergent core). The fuzzy cynical row uses the UNION (M2-C1 ∪ M3-C1 ∪ M3-C3), honouring the supervisor verdict that the posture is real but the boundaries shift between methods. Topical subsets use (M1 ∩ M3-C0). The two crisp rows + the fuzzy row are not mutually exclusive (some threads sit in both crisp earnest and cynical via different methods).

| Label (descriptive) | Status | n | % | ≥3% floor? | investimentos / farialimabets | flb overrep | window mix | example threads |
|--------------------|--------|---|---|------------|------------------------------|------------:|------------|------------------|
| Earnest learner (mainstream) | crisp | 1089 | 30.4% | ✓ | 93.5% / 6.5% | 0.13× | A 32.6% / B 35.3% / C 32.1% | n0gwny, isrrdx, i1rnpd |
| Speculator / crypto-adjacent | crisp | 394 | 11.0% | ✓ | 13.5% / 86.5% | 1.73× | A 51.3% / B 33.0% / C 15.7% | o0f467, l79h3l, nceg2t |
| Cynical-reactive continuum (fuzzy) | fuzzy | 1511 | 42.1% | ✓ | 21.2% / 78.8% | 1.58× | A 29.5% / B 32.6% / C 38.0% | k6olwt, jigrgj, lpxrs0 |
| Earnest sub-theme: tax/IR | sub_theme | 109 | 3.0% | ✓ | 91.7% / 8.3% | 0.17× | A 47.7% / B 28.4% / C 23.9% | l0g9m6, mq8iqc, lzutc1 |
| Earnest sub-theme: property/banking-debt | sub_theme | 295 | 8.2% | ✓ | 91.2% / 8.8% | 0.18× | A 19.7% / B 37.3% / C 43.1% | n0gwny, lz3uw9, k83yam |

### 4.1 Defining attribute profile per candidate

**Earnest learner (mainstream)** (crisp, n=1089)
- Ordinal means (1–5): ceticismo_institucional=2.13, exposicao_a_cripto_e_especulacao=1.10, identidade_comunitaria=1.26, sofisticacao_tecnica=2.18, tolerancia_risco_declarada_ou_inferida=2.12
- Categorical modes: fase_acumulacao: acumulacao_inicial (32.6%); estrategia_principal: renda_fixa_conservadora (24.9%); relacao_com_instituicoes_financeiras: desconhecido (46.1%); estado_emocional_predominante: curioso_ou_exploratorio (78.7%); objetivo_financeiro_primario: acumulacao_sem_objetivo_claro (42.7%)

**Speculator / crypto-adjacent** (crisp, n=394)
- Ordinal means (1–5): ceticismo_institucional=2.87, exposicao_a_cripto_e_especulacao=3.99, identidade_comunitaria=3.85, sofisticacao_tecnica=1.59, tolerancia_risco_declarada_ou_inferida=4.44
- Categorical modes: fase_acumulacao: desconhecido (45.9%); estrategia_principal: especulacao_curto_prazo (87.8%); relacao_com_instituicoes_financeiras: desconhecido (83.2%); estado_emocional_predominante: euforico_ou_impulsivo (62.7%); objetivo_financeiro_primario: acumulacao_sem_objetivo_claro (52.5%)

**Cynical-reactive continuum (fuzzy)** (fuzzy, n=1511)
- Note: Continuum-end posture per supervisor verdict 2026-05-21. M3 subdivides into C1 (guru-skeptic core) and C3 (loss-as-meme).
- Ordinal means (1–5): ceticismo_institucional=3.09, exposicao_a_cripto_e_especulacao=1.60, identidade_comunitaria=3.01, sofisticacao_tecnica=1.57, tolerancia_risco_declarada_ou_inferida=2.43
- Categorical modes: fase_acumulacao: desconhecido (67.2%); estrategia_principal: desconhecido (58.8%); relacao_com_instituicoes_financeiras: desconhecido (80.1%); estado_emocional_predominante: cinico_ou_ironico (46.4%); objetivo_financeiro_primario: desconhecido (72.9%)

**Earnest sub-theme: tax/IR** (sub_theme, n=109)
- Note: Single-method evidence (M1 only); collapsed into earnest persona by M2 and M3. Demoted from persona to sub-theme by supervisor 2026-05-21. Use as pain/need texture for the earnest persona in Phase 4; do NOT list as a separate persona row.
- Ordinal means (1–5): ceticismo_institucional=2.29, exposicao_a_cripto_e_especulacao=1.35, identidade_comunitaria=1.34, sofisticacao_tecnica=2.42, tolerancia_risco_declarada_ou_inferida=2.39
- Categorical modes: fase_acumulacao: acumulacao_ativa (40.4%); estrategia_principal: dividendos_buy_hold (35.8%); relacao_com_instituicoes_financeiras: desconhecido (45.0%); estado_emocional_predominante: curioso_ou_exploratorio (66.1%); objetivo_financeiro_primario: acumulacao_sem_objetivo_claro (47.7%)

**Earnest sub-theme: property/banking-debt** (sub_theme, n=295)
- Note: Single-method evidence (M1 only); collapsed into earnest persona by M2 and M3. Demoted from persona to sub-theme by supervisor 2026-05-21. Use as pain/need texture for the earnest persona in Phase 4; do NOT list as a separate persona row.
- Ordinal means (1–5): ceticismo_institucional=2.35, exposicao_a_cripto_e_especulacao=1.04, identidade_comunitaria=1.29, sofisticacao_tecnica=2.18, tolerancia_risco_declarada_ou_inferida=2.12
- Categorical modes: fase_acumulacao: consolidacao (28.5%); estrategia_principal: imobiliario_direto_ou_fii (25.8%); relacao_com_instituicoes_financeiras: migrando_para_corretora (28.1%); estado_emocional_predominante: curioso_ou_exploratorio (48.5%); objetivo_financeiro_primario: acumulacao_sem_objetivo_claro (34.6%)

## 5. What Phase 4 inherits

### 5.1 Persona structure to carry forward

- **Two crisp convergent personas** (earnest learner; speculator/crypto-adjacent), each backed by all three methods.
- **One fuzzy cynical-reactive continuum** — real posture, soft boundaries; do NOT narrate as a single tight persona.
- **Topical subsets are sub-themes, NOT personas.** Tax/IR and property/banking-debt are situational variants *within* the earnest-learner persona, useful as pain/need texture in Phase 4's pains section. Their independent existence is **single-method evidence** (Method 1 topical density spikes that M2 and M3 collapse). Do not list them as separate persona rows in the memo.

### 5.2 Hypothesis-test carry-forwards

- **H1 SUPPORTED** on posture methods (M2 V=0.68, M3 V=0.65). Subreddit segmentation is a real signal; document the firewall.
- **H2 — two specific directional shifts are the headline**, not the weak aggregate chi-square: **speculator share declines monotonically A→B→C (~51%→33%→16%)** tracking the Selic rise; **cynical-reactive continuum grows A→C (~29.5%→38.0%)**. The aggregate test is reported but is not the actionable temporal content.
- **H3 SPLIT** — M2↔M3 convergent (ARI=0.21); M1 orthogonal at the global partition level but locally informative via overrepresentation. M1 = topic instrument; M2/M3 = posture instruments.
- **H4 PARTIALLY NULL — multi-dimensional but emotional-posture-dominated**. Emotional posture carries ~45% of importance vs. ~12% for the next feature (~3.75× ratio). **Phase 4 personas MUST be led by emotional posture**, with other attributes as supporting texture — NOT narrated as ten co-equal dimensions. Circularity caveat applies (see `phase3d_hypothesis_tests.md` H4 section).


### 5.3 Counting convention — Phase 4 MUST read this before drafting

The candidate rows in Section 4 use **different denominators** by construction: crisp rows are method INTERSECTIONS (M2 ∩ M3); the fuzzy cynical row is a UNION (M2-C1 ∪ M3-C1 ∪ M3-C3). They overlap. The earnest-crisp row (n=1089) and the cynical-union row (n=1511) sum to more than the corpus when added naively. **These are evidence rows, not a partition.**

**Phase 4 instruction.** For any stated persona proportion in the memo, use the **M2 partition as the mutually-exclusive backbone** (M2-C0..C6 cover all 3600 threads with no overlap). M3 and M1 are characterizing instruments: use them to *describe* personas (which M2-C2 threads are also M3-C0? which M2-C1 threads are M3-C3 loss-as-memes?) but NOT to re-count them. A partner reading "30% earnest + 11% speculator + 42% cynical + 8% property-debt = 91%" would be misled — those numbers come from overlapping definitions. Use M2 share (M2-C2 = 47.6% earnest, M2-C5 = 18.4% speculator, M2-C1 = 30.0% cynical, etc.) as the canonical proportions.

## 6. Figures

- `reports/figures/phase3d_ari_matrix.png` — pairwise ARI
- `reports/figures/phase3d_h1_subreddit_by_cluster.png` — H1 visual
- `reports/figures/phase3d_h2_window_by_cluster.png` — H2 visual
- `reports/figures/phase3d_h4_feature_importance.png` — H4 visual

---

## ⛔ HARD STOP

Phase 3D is supervisor-approved with the four carry-forwards above. Phase 4 remains BLOCKED until the supervisor issues the Phase 4 brief. Do not begin persona naming, memo drafting, or any synthesis writing before the brief lands.

# Decisions Log

Tracks supervisor overrides and out-of-band decisions that deviate from pre-registered
rules. Each entry records what changed, why, and what the default rule would have done.

---

## 2026-05-20 — perfil_tributario_e_fiscal demoted to FLAG (Phase 2)

**Decision:** `perfil_tributario_e_fiscal` moved from clustering feature to metadata/flag.

**Default rule outcome:** The pre-registered 70% missingness threshold would have
*included* this field as a clustering feature (69.4% desconhecido, just under threshold).

**Override rationale (supervisor):**
- `relacao_com_selic_e_renda_fixa` was demoted at 73.4% by the pre-registered rule.
- Both fields are Brazil-specific, high-missingness, and structurally similar in what
  they capture (country-specific financial context not visible from posts alone).
- Treating a 69.4% and 73.4% field asymmetrically based on a 3.4-percentage-point
  difference in rate would be spurious precision. Conservative direction is preferred.
- The pre-registered rule is a decision boundary, not a guarantee of feature quality.
  At ~70%, either verdict is defensible; the supervisor chose the conservative one.

**Effect on study:**
- Clustering feature matrix: 10 fields (was 11).
- Metadata/flags: 8 fields (was 7).
- Field is retained in the extracted parquet and can be used for post-hoc analysis
  (e.g., cross-tabulating tax-posture distribution across clusters).
- No re-extraction required; the data is unchanged.

**Affected files:**
- `data/processed/clustering_features.json` — updated (supervisor_overrides block added)
- `reports/phase2_full_summary.md` — sections 3 and 4 corrected
- `reports/cost_log.md` — override logged

**Not affected:**
- `data/processed/extracted_attributes.parquet` — data unchanged
- Any extraction scripts — no re-run

---

## 2026-05-21 — Phase 3C clustering method changed from HDBSCAN+UMAP to k-medoids (PAM)

**Decision:** Replace the HDBSCAN+UMAP pipeline in Phase 3C (Method 3) with k-medoids
(PAM) on cosine distance of the raw 768-D mpnet embeddings.

**What HDBSCAN+UMAP produced:**
- HDBSCAN on raw 768-D cosine distances: 0 clusters / 100% noise at all tested
  min_samples (5, 10, 15, 27). The embedding space is a continuum — no density
  structure that HDBSCAN can exploit.
- UMAP (n_components=20, n_neighbors=15, min_dist=0.0, metric=cosine) then
  collapsed the data into three equilateral-triangle manifolds.
- HDBSCAN on the UMAP-20D output: ARI=1.000 across all 20 bootstraps, 0 noise,
  cluster separation ratios 14–50×. These are signatures of UMAP topology collapse,
  not genuine density structure.
- Only one genuine cluster existed: the crypto/speculator group (n≈178, 98.3%
  crypto keyword match), which is a true density spike. The other two
  "clusters" were UMAP artifacts splitting the continuous bulk population.

**Default rule outcome:** The pre-registered Phase 3C brief specified HDBSCAN+UMAP
(simplified Kura-style pipeline). The degenerate clustering was a methodological
failure, not a finding about the data.

**Override rationale (supervisor):**
- The raw 768-D mpnet space has no density structure. HDBSCAN is appropriate for
  spaces with density variation; it is not appropriate here.
- UMAP manufacturing artificial structure is a documented failure mode on
  manifolds with low intrinsic dimensionality.
- k-medoids (PAM) on cosine distance is the correct tool for partitioning a
  continuum at a supervisor-chosen k. It makes no density assumption, works
  directly on the distance matrix, and produces k representative medoids.
- Supervisor runs k=4,5,6,7 in an explore step (same discipline as Phase 3A)
  and selects k based on silhouette + interpretability.

**Effect on study:**
- Phase 3C produced a degenerate 3-cluster result (UMAP artifact) that was
  discarded. The explore re-run with k-medoids is the official Phase 3C result.
- The embedding (m3_emb_mpnet.npy, shape (3538+, 768)) is unchanged and healthy:
  median pairwise cosine similarity 0.607, no NaN, good diversity.
- The UMAP cache files (m3_umap_20d.npy, m3_umap_2d.npy) are retained but:
  - m3_umap_20d.npy is no longer used for clustering (DEPRECATED).
  - m3_umap_2d.npy is used for cosmetic scatter plots only (NOT clustering input).
- The old clusters_method3.parquet (degenerate 3-cluster result) is overwritten
  by the --finalize step.
- Bootstrap ARI=1.000 from the old run is NOT reported as a finding; it is an
  artifact of the UMAP manifold collapse. The methodology appendix will note it.

**Affected files:**
- `notebooks/03c_llm_hierarchical.py` — rewritten: HDBSCAN+UMAP → k-medoids PAM.
  New modes: --repair-failures (zero-cost JSON repair), --cluster (explore k=4..7),
  --finalize <k> (full analysis at chosen k).
- `reports/phase3c_method3.md` — overwritten by each run.
- `data/processed/clusters_method3.parquet` — to be overwritten by --finalize.

**Not affected:**
- `data/interim/m3_emb_mpnet.npy` — embedding unchanged (healthy).
- `data/interim/phase3c_summaries.jsonl` — summaries unchanged.
- All Phase 3A and Phase 3B outputs — unaffected.

---

## 2026-05-21 — Phase 3C k=4 selected by supervisor (k-medoids explore)

**Decision:** k=4 chosen for Phase 3C Method 3 k-medoids partition.

**Silhouette context:** All candidate silhouette scores were ~0.05–0.08 (k=4..7).
Low silhouette confirms the raw 768-D embedding space is a continuum — there is no
density structure. This is consistent with the HDBSCAN finding (0 clusters in raw
space). Silhouette on a continuum partition reflects partition quality, not cluster
existence; it cannot be used to select k the same way as on data with genuine clusters.

**Override rationale (supervisor):** k selected on interpretability, not silhouette.
k=4 cleanly separates:
- One earnest-learner cluster (C0): anxious, validation-seeking, methodical.
- Three flavors of a cynical-reactive family (C1/C2/C3): irony-masking-frustration,
  guru-skepticism, loss-as-meme. All above the 3% floor.
- The crypto/speculator outcropping persists within the structure.
Higher k (5,6,7) further subdivides the cynical continuum without revealing new types;
silhouette drops from k=4 to k=6, confirming no new structure is gained.

**Effect on study:**
- Phase 3C will produce k=4 M3 clusters: M3-C0 through M3-C3.
- Predicted correspondence (to be confirmed by finalize adjudication):
  M3-C0 (earnest-learner) ↔ M2-C2; cynical-family (M3-C1/C2/C3) ↔ M2-C1;
  speculator signal ↔ M2-C5 (distributed across M3 or concentrated).
- Low silhouette is REPORTED HONESTLY in the methodology: these are
  supervisor-interpretability partitions of a continuum, not density clusters.
  The crypto group (n≈178 from HDBSCAN diagnosis) is a genuine density spike;
  the remaining three partitions are cuts along the cynical-reactive axis.

**Affected files:**
- `data/processed/clusters_method3.parquet` — to be written by --finalize 4.
- `reports/phase3c_method3.md` — to be written by --finalize 4.

---

## 2026-05-21 — M2-C1 (cynical-reactive) verdict: real posture, fuzzy boundaries

**Decision:** M2-C1 is **corroborated as a real cynical-reactive posture** by Methods 2
and 3, but **NOT promoted to "confirmed crisp cluster"**. It is carried into Phase 3D
as a **continuum-end posture with fuzzy boundaries**, not as a discrete segment.

**Default rule outcome:** The Phase 3A adjudication framework defined the M2-C1
test as decisive: if Method 3 recovered M2-C1 as a single concentrated cluster, it
would be promoted from "provisional" (per Phase 3A) to "confirmed crisp cluster."
If dispersed below the 40% concentration threshold, it would remain provisional.

**Adjudication outcome (Section 8 of phase3c_method3.md):**
- Top M3 partner of M2-C1: **M3-C3** at 36.4% — below the 40% threshold (formally DISPERSED).
- BUT M2-C1 is overrepresented in **both** M3 cynical clusters:
  - M3-C3 (loss-as-meme): **2.0×** overrepresentation.
  - M3-C1 (cynical core): **1.91×** overrepresentation.
- M2-C1 is **underrepresented in the earnest M3-C0** (117/1073 = 10.9% vs. 37.2% base rate).
- I.e., Methods 2 and 3 *independently agree* the cynical-reactive posture is real and
  distinct from the earnest learner; they *disagree* on whether it is one cluster or two.

**Override rationale (supervisor):**
- The formal binary verdict ("CONCENTRATED" vs. "DISPERSED" at 40%) is too coarse for
  this case. A literal reading would say M2-C1 is DISPERSED and downgrade it. That
  reading misses the actual signal: M2-C1 is *consistently and asymmetrically* present
  in M3's cynical region, not scattered randomly.
- Method 3 subdivides M2-C1 into two cynical sub-flavors (guru-skepticism / loss-meme)
  rather than dissolving it. The dispersion is *substructure*, not noise.
- However, the absence of a 1:1 crisp partner cluster in Method 3 is itself informative:
  the cynical posture sits on a continuum rather than forming a tight density region.
  Calling it a "crisp cluster" would overstate the convergence evidence.
- Final verdict: **real posture, fuzzy boundaries.** Treat as a continuum-end, not a
  discrete segment. This is fully consistent with the locked H3 hypothesis (methods
  converge on coarse segmentation, disagree on fine splits — that is a finding, not
  a problem to hide).

**Effect on study:**
- Phase 3D synthesis will report the cynical-reactive posture as a **confirmed dimension**
  (the *posture* exists across methods) but not as a **confirmed segment** (the *boundary*
  shifts between methods).
- Persona naming for the cynical region will acknowledge internal heterogeneity rather
  than collapsing M3-C1 + M3-C3 into a single "cynical persona" without qualification.
- The earnest-learner cluster (M2-C2/M3-C0) and speculator cluster (M2-C5/M3-C2/M1-C2)
  remain the two crisp, fully-convergent segments. The cynical region is the
  hypothesis-generating territory where Phase 3D method-comparison will be most valuable.
- Memo language must be calibrated: "two convergent personas + a cynical-reactive
  continuum" is honest; "three crisp personas" would overstate.

**Affected files:**
- `reports/phase3c_method3.md` — status header and HARD STOP section updated to record
  the approval and the M2-C1 verdict.
- `data/processed/clusters_method3.parquet` — unchanged (k=4 labels stand).
- Phase 3D synthesis (to come) must honor this verdict in persona definitions.

**Not affected:**
- All Phase 3A/3B/3C outputs and parquets — unchanged.
- M2-C2 and M2-C5 verdicts (both confirmed crisp clusters per Sections 7 and 8).

---

## 2026-05-21 — Memo wedge = IR over paralysis (product judgment supplementing data)

**Decision:** The Phase 4D memo (`reports/memo.md`) recommends the **integrated
IR-preparation tool** as the wedge product, rather than a product addressing
the Sossego-Seeker's most central pain (decision paralysis / pre-decision
validation). This is product judgment supplementing the data; logging here so
the choice is auditable.

**What the data alone would recommend.** Phase 4C documented three Sossego-
Seeker pains in priority order: Pain 1 = idle capital + decision paralysis;
Pain 2 = first-time IR declaration anxiety; Pain 3 = property-purchase
complexity. Paralysis is the most central pain by every quantitative criterion
— it is the persona's defining behavioral signature, it is what the supervisor-
locked sossego/paralysis quotes most directly express, and the H4 finding
(emotional posture as the dominant clustering axis, 45% importance) reinforces
that *certainty* is what the user lacks. A literal "central pain → product"
reading of Phase 4C would have us build for paralysis.

**Why the memo overrides that and recommends IR.** Paralysis is the deeper
pain but the *fuzzier* one — what the user wants ("personalized validation,
yes-this-fits-you reassurance") is a service-design problem with ambiguous
data inputs and no clear v1 shape. The IR pain, by contrast, is **specific,
annual, high-stakes, evidenced, and addressable in a single shippable
product**. Three concrete product-judgment criteria favor IR as the wedge:

1. **Buildability** — IR has clear data inputs (`informes-de-rendimentos`),
   clear outputs (a pre-filled declaration), and a clear deadline (the April
   filing window). Paralysis-as-product is a service offering with no obvious
   minimum shippable unit.
2. **Specificity** — annual moment beats always-on need for product
   measurement and user acquisition.
3. **Trust-earning sequence** — start where the gap is concrete; expand to
   the fuzzier paralysis territory once credibility is established. The memo
   makes this wedge → expansion sequence explicit.

**Defensibility (logged explicitly per supervisor 2026-05-21):** cross-
institution reconciliation is the natural moat because no single broker has
an incentive to build it. The trust earned at the high-stakes annual moment
opens the expansion to year-round validation that single-broker products
cannot replicate. This claim sits in the memo and is auditable.

**Validation requirement (logged explicitly per supervisor 2026-05-21):** the
IR pain is documented in 2020–2024 corpus threads. Broker / B3 IR-automation
may have advanced since. The memo includes a "Validate first" instruction to
desk-check the top brokers and Receita's IR program before committing build.
This is a 2026 present-tense market check, NOT a corpus claim — flagged in
the memo and again here.

**Effect on study:**
- Memo recommendation = IR wedge + paralysis-validation expansion path.
- Phase 4C remains the canonical pain documentation; the IR-over-paralysis
  product call lives in the memo + this log entry, not in 4C.
- Cético Irônico re-framed in the memo as "win later via earned credibility,"
  not dismissed.
- Sample-bias caveat ("Reddit-active investors, hypothesis-generating, not
  demographic truth") on the memo's first paragraph per the locked Phase 1
  rule.

**Affected files:**
- `reports/memo.md` — final deliverable.
- This log entry — auditable disclosure that product judgment supplemented
  data in choosing the wedge.

**Not affected:**
- `reports/phase4c_pains_needs.md` — pain priority order unchanged
  (paralysis Pain 1; IR Pain 2; property Pain 3). The memo's wedge choice is
  noted as product judgment, not a re-priortization of pains.
- All other Phase 4 outputs.

---

## 2026-05-21 — threads.py stratified_sample bug fix applied (Phase 5 packaging)

**Decision:** Apply the quartile-threshold fix to `src/threads.py:stratified_sample`
as part of the Phase 5 final-assembly step. The supervisor decision to ride the
existing extraction sample (rather than re-extract) remains in force; the fix is
strictly for forward reproducibility.

**What changed.** `top_q` threshold corrected from `scores[len // 4]`
(25th percentile — the bug) to `scores[len * 3 // 4]` (75th percentile —
the intended top quartile). Variable renamed `q25 → q75`. A reproducibility
note was added to the function docstring, pointing to
`reports/phase2_full_summary.md` for the deviation disclosure.

**Default rule outcome.** Without this fix, future runs of
`stratified_sample` would silently reproduce the bug. The locked methodology
appendix would document a deviation that the code does not exhibit.

**Effect on study.**
- `data/processed/working_sample.jsonl` — UNCHANGED. The Phase 2 extraction
  sample stays exactly as analysed throughout Phases 3 and 4.
- `data/processed/extracted_attributes.parquet` — UNCHANGED.
- `reports/phase2_full_summary.md` — methodology disclosure block added at
  the top.
- Future re-runs of `stratified_sample` will produce a CORRECT top-quartile
  sample. If someone re-extracts from scratch they will get a different (and
  cleaner) sample than the one this study used; the deviation disclosure
  makes that visible.

**Affected files:**
- `src/threads.py` — function fix + docstring note.
- `reports/phase2_full_summary.md` — disclosure block.
- This log entry — auditable record of the fix landing in repo.

**Not affected:**
- All Phase 3 / Phase 4 outputs, parquets, and reports. The deviation flows
  through the methodology appendix; it does not retroactively change the
  analysis sample.

---

## 2026-05-21 — Phase 3D approved with four carry-forwards (supervisor review)

**Decision:** Phase 3D (cross-method synthesis + H1/H2/H4 hypothesis tests) approved.
Phase 4 remains BLOCKED until the supervisor issues the Phase 4 brief. Four
carry-forwards are locked here and propagated into `phase3d_synthesis.md` and
`phase3d_hypothesis_tests.md`.

### Carry-forward 1 — H4 verdict relabelled

**Old verdict (Claude's first draft):** "BORDERLINE multi-dim" / "H4 null NOT
supported." That framing treated the 50% threshold as a sharp binary and missed
the asymmetric importance distribution.

**Supervisor verdict:** **PARTIALLY NULL — multi-dimensional but emotional-
posture-dominated.** Top feature `estado_emocional_predominante` carries 45.1% of
RF importance versus 11.9% for the next feature (`identidade_comunitaria`) — a
3.80× ratio. One axis is doing about half the work; the remainder is spread across
3–4 supporting features.

**Required disclosure — circularity caveat:** `estado_emocional_predominante` was
itself one of the 10 clustering features fed to Method 2. The H4 test therefore
describes the *geometry* of the M2 partition (which feature most strongly
discriminates the clusters M2 produced), NOT an external causal claim about what
drives Brazilian retail investor behavior. The non-circular finding — that the
classical axes the H4 brief named (sophistication, fase_acumulacao, objetivo) sit
in the bottom half of importance even with full clustering access — IS robust.

**Phase 4 implication (binding):** Personas MUST be led by emotional posture, with
other attributes as supporting texture. Personas MUST NOT be narrated as if all
ten clustering features matter equally. The circularity caveat must appear in the
methodology appendix.

### Carry-forward 2 — H2 headline is the two directional shifts, not the aggregate

**Old framing:** "H2 PARTIAL — small effect sizes (V≈0.07–0.15)." Honest as far as
the aggregate chi-square goes, but missed the actionable directional content.

**Supervisor verdict:** The aggregate test is reported for completeness but is NOT
the headline. The two real H2 findings are:

1. **Speculator share declines monotonically A→B→C: ~51% → ~33% → ~16%** — tracks
   the Selic rise from ~2% (window A) to ~13.75% (window B) to mature fixed-
   income regime (window C). Crypto/equity speculation thins out as fixed-income
   becomes the alternative.
2. **Cynical-reactive continuum grows A→C: ~29.5% → ~38.0%** — opposite-direction
   trajectory consistent with loss-as-meme and guru-skeptic sub-flavors absorbing
   investors who weathered the crypto winter and the volatility of window B.

These two shifts move in opposite directions, which is *why* the aggregate
chi-square is muted — they partly cancel. The locked H2 form ("composition stable,
prevalence shifts") holds in its strongest reading on these two personas.

**Phase 4 implication (binding):** The temporal section of the memo leads with
these two directional shifts. The weak aggregate chi-square is reported in the
methodology, NOT in the memo headline.

### Carry-forward 3 — Counting convention for Phase 4 (M2 partition as backbone)

**Issue:** Phase 3D's candidate persona rows use heterogeneous denominators by
construction. Crisp rows are method INTERSECTIONS (M2 ∩ M3); the fuzzy cynical
row is a UNION (M2-C1 ∪ M3-C1 ∪ M3-C3). They overlap. Adding the candidate-row
percentages as if they partition the corpus would mislead the reader.

**Supervisor instruction (binding for Phase 4):** Use the **M2 partition as the
mutually-exclusive backbone** for any stated persona proportion in the memo
(M2-C0..C6 cover all 3600 threads with no overlap). M3 and M1 are *characterizing*
instruments — use them to describe personas (e.g., "which M2-C2 threads are also
M3-C0 cynical-flavored?") but NOT to re-count personas. Canonical proportions in
the memo come from M2 share (M2-C2 = 47.6% earnest, M2-C5 = 18.4% speculator,
M2-C1 = 30.0% cynical, etc.).

**Rationale:** A partner reading "30% earnest + 11% speculator + 42% cynical + 8%
property-debt = 91%" would be misled — those numbers come from overlapping
definitions. The M2 partition gives a single clean denominator while honoring the
H3 finding that M2 and M3 converge on coarse structure.

### Carry-forward 4 — Topical subsets are sub-themes, not personas

**Old framing:** Tax/IR (n=109) and property/banking-debt (n=295) appeared as
"topical" candidate persona rows. Both clear the 3% floor by member count.

**Supervisor verdict:** Both are **demoted to earnest-learner sub-themes**, not
standalone personas. Their independent existence is single-method evidence (M1
topical density spikes that M2 and M3 collapse into the earnest cluster). They
fail the Phase-1 locked rule that "Cluster validity requires all three: 3%
threshold, bootstrap stability, AND interpretable across methods" — the third
condition is not met.

**Phase 4 implication (binding):** Carry tax/IR and property/banking-debt as
**texture for the earnest persona's pains/needs section** — useful colour for
what the earnest learner is asking about — NOT as separate persona rows in the
memo's persona table.

### Status

- `reports/phase3d_synthesis.md` — Status header + Sections 4/5 reflect the
  four carry-forwards. Candidate persona table labels topical rows as
  "Earnest sub-theme: …" with status `sub_theme`.
- `reports/phase3d_hypothesis_tests.md` — H4 verdict, H2 headline, summary
  verdict block all updated.
- `notebooks/03d_phase3d_synthesis.py` — script regenerates the above
  deterministically; re-runs preserve the carry-forwards.
- `data/processed/phase3d_results.json` — machine-readable snapshot refreshed.

**Phase 4 stays BLOCKED until the supervisor issues the Phase 4 brief. Do not
begin persona naming, memo drafting, or any synthesis writing before the brief
lands.**

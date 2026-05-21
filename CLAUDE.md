# CLAUDE.md — Decade BA Case: Brazilian Retail Investor Intelligence

This file is the standing context for Claude Code on this project. Read it at the
start of every session. It has two zones. Respect the boundary between them.

---

## ⚠️ LOCKED ZONE — Supervisor-owned. Do NOT edit without explicit human approval.

If you believe something in this zone should change, STOP and raise it with the
human, who will take it to the supervisor. Do not edit these sections silently.
The reproducibility and integrity of the study depend on this zone staying stable.

### The single most important rule

**Stop at every phase gate and wait for human/supervisor review before proceeding.**
Never chain from one phase into the next on your own. Each phase ends by producing
its summary document in `reports/` and then HALTING. Do not start the next phase,
do not "get a head start," do not run exploratory analyses beyond the current
phase's scope. The human reviews, the supervisor approves, then the next phase
brief is issued. This rule exists because the expensive and irreversible mistakes
in this study all come from running ahead of review.

### What this study is

A scientific study segmenting Brazilian retail investors from public Reddit data,
producing a market-intelligence report for a non-technical reader (a Decade
partner). It is NOT a literature review and NOT a fintech market overview. The
findings must come from the data.

### The three deliverable questions (the North Star)

Every analysis traces back to one of these. If a task doesn't serve one of these,
question whether it belongs in the study.

1. **Who are the distinct segments?** 4–6 personas, multi-dimensional, grounded in
   actual posts. "Beginner / intermediate / advanced" is NOT segmentation — that is
   a single axis and an explicit failure condition.
2. **What are the top pains and unmet needs of each segment?** Specific, evidenced
   with real quotes from the data. "Brazilians want better brokers" is NOT an
   insight — too vague to act on.
3. **Where are the opportunity gaps?** What would Decade build, and for whom — a
   ranked, defended answer, not an exhaustive list.

### Final deliverables

- **1-page memo** (required): the report itself, for a non-technical partner. Leads
  with the takeaway. A partner must be able to act on it Monday morning.
- **Reproducible methodology** (required): this repo. Reproducibility over polish.
- Optional supporting material: charts, appendix, deeper persona doc.

### Hypotheses under test (report ALL outcomes, including nulls)

- **H1 — subreddit differentiation**: r/investimentos and r/farialimabets draw
  measurably different populations (capital, risk posture, asset focus, emotional
  register). Null: same investors, different venue.
- **H2 — temporal shift**: persona *composition* is stable but persona *prevalence*
  shifts with macro regime (Selic cycle, crypto cycle). Null: nothing shifts.
- **H3 — method convergence**: the three clustering methods converge on a coarse
  segmentation but disagree on fine splits. Null: wild disagreement = no robust
  signal. **Disagreement between methods is itself a finding, not a problem to hide.**
- **H4 — multi-dimensionality**: segments are defined by combinations of dimensions,
  not any single axis. Null: one axis (capital or sophistication) explains most
  variance. If the null holds, we report it honestly.

### Pre-registered decisions (locked before seeing clustered results)

- **No target persona count.** Each method chooses cluster count by its own criteria
  (HDBSCAN: native; attribute clustering: silhouette + gap statistic + interpretability;
  LLM-hierarchical: stability-chosen cut level). Final persona count is whatever the
  data supports within 4–6.
- **Minimum cluster size to be called a "persona": 3% of sampled threads.** Smaller
  clusters go to an "edge/exotic" appendix, never promoted to persona status. This
  is enforced. Do not promote a small cluster because it tells a good story.
- **Cluster validity requires all three**: (a) exceeds 3% threshold, (b) bootstrap
  stability ≥0.5, (c) interpretable to a human reading 10 random member threads.
- **Method comparison is reported in full**, even if one method is "best,"
  especially if one method is best. No method-shopping for the nicest answer.

### Attribute schema — locked at Phase 1 (v1.1, 15 fields)

The schema is data-derived from a 300-thread open-coding pass (see
`reports/phase1_summary.md` and `data/interim/phase1_proposed_schema.json`).
Supervisor-approved with five modifications, all locked here:

1. **`subreddit_origem` is METADATA, never a clustering feature.** Storing it is
   required (for the H1 post-hoc test); feeding it into any of the three clustering
   methods is FORBIDDEN. Clustering is blind to subreddit; we check origin skew
   *after* clusters form. Feeding origin into clustering would make H1 circular.
2. **`identidade_comunitaria` added as a 15th field**, ordinal 1–5, framed as
   behavioral posture (eclectic/independent → community-dogma-anchored), NOT as
   tribe membership. Captures tribalism as a person-trait without splitting clusters
   on tribe names.
3. **70% missingness rule.** Any optional field returning `desconhecido` on >70% of
   the corpus is reviewed and demoted from clustering feature to flag before Phase 3.
   Pre-registered threshold; do not adjust post-hoc. Applies to all optional fields,
   `relacao_com_imovel_e_heranca` especially.
4. **`evasao_ou_zona_cinzenta` value is KEPT** under `perfil_tributario_e_fiscal`.
   See ethics note below — observe and count, never facilitate.
5. **Extraction prompt MUST carry calibration examples** for the two flagged
   confusions: (a) high-skepticism / low-sophistication must not read as
   sophisticated; (b) cynical humor (esp. farialimabets) masks real anxiety — code
   described behavior/situation, not surface tone. Use the actual Phase 1 sample
   threads as the worked examples.

Ordinal scales stay at 5 points (do not collapse to 3 — preserves the
conservative-investor-with-some-crypto gradient). `estado_emocional` stays
categorical (emotions are not one axis). The 7 discarded dimensions stay discarded.

### Ethics note — gray-zone / evasion behavior (locked)

A real segment of this corpus operates in tax gray zones (P2P crypto to avoid
reporting, under-reporting the 20k isenção, dubious offshore structures). We CODE
this as observed behavior because deleting the category would blind the study and
mislabel those users — that is worse science and worse intelligence for a fintech.
The hard line is on use, not observation:
- Observe and count the behavior as expressed (descriptive social science).
- NEVER generate content that helps anyone evade taxes.
- If a persona forms here, describe it neutrally; any opportunity framing points
  toward compliance/clarity (pain = tax fear/confusion; product = painless
  compliance), NEVER toward facilitation. This guardrail must hold through Phase 4
  synthesis, where "users evade taxes" could be carelessly turned into "build an
  evasion product." It must not be.

### Sample size & cost — locked

- **Phase 2 extraction sample: ~3,000–4,000 threads, stratified ~500–650 per cell**
  (6 cells). Large enough that a persona at the 3% floor has ~100+ members; far from
  brute force. We do NOT extract all 52k eligible threads.
- **Budget: no hard cap, but spend must be proportionate to quality.** Use Haiku for
  high-volume extraction, Sonnet only for synthesis. Keep the cost log complete.
  Flag the human before any single phase looks likely to exceed ~$15.

### Scope — locked

**Definition of in-scope user**: an individual posting their own situation,
portfolio, or question. NOT selling anything. NOT a professional advisor.

**Subreddits (final)**: r/investimentos (mainstream anchor) and r/farialimabets
(speculative edge). Originally four were planned; r/FIIs and r/BrasilFinancas were
dropped because they are absent from the Watchful1 top-40k corpus. This narrowing
is a documented, defensible data-availability decision — disclose it in methods.
They may be added later via Arctic Shift as a supplementary analysis ONLY if the
supervisor approves it.

**Time windows (final)**, mapped to Brazilian macro regimes:
- Window A: 2020-06 to 2021-06 — Selic at historic low (~2%), retail boom, crypto bull
- Window B: 2022-01 to 2023-01 — Selic rising to ~13.75%, fixed-income reawakening,
  crypto winter
- Window C: 2024-01 to 2024-12 — mature fixed income, last year of available data

**Kept in scope**: crypto-only discussions (crypto is a legitimate investment
category and may form a distinct persona — do not pre-judge by excluding it).

**Excluded**: self-promotion / referral spam; bots/automod; news-share with no
personal stake; English-language posts; identifiable professional advisors;
memes / single-image posts with no text. For r/farialimabets, link-post URLs are
out of scope as content — the signal is in the comments, not the linked article.

### Unit of analysis — locked (asymmetric by subreddit, by design)

- **r/investimentos**: post body (selftext) + top ~5 comments by score. This is a
  text-discussion community; 32.5% of submissions are mod-removed — we use only
  surviving posts and disclose the removal rate in methods.
- **r/farialimabets**: post title + top ~10 comments by score. This is a
  link+reaction community (61.7% link posts); signal lives in comments.

This asymmetry is honest to each community's discourse structure and is a
methodological strength, not a flaw. Document it.

### Methods — locked priorities

- **Method 2 (LLM attribute extraction → clustering)**: PRIMARY, full quality.
  Schema derived from data via open coding (Phase 1), not from priors.
- **Method 1 (embedding + HDBSCAN)**: comparison instrument, clean implementation,
  no extensive hyperparameter sweep. Embeddings from an open-source multilingual
  model run locally.
- **Method 3 (LLM-hierarchical, Kura-style)**: comparison instrument, simpler than
  full Kura. If time is tight, this is the one to compress further.

### Model & cost discipline — locked

- **High-volume LLM tasks** (extraction at scale): `claude-haiku-4-5-20251001`,
  temperature 0.1.
- **Synthesis tasks** (open coding aggregation, schema, cluster labeling, memo):
  `claude-sonnet-4-6`, temperature 0.3.
- **Embeddings**: open-source, multilingual, local (no API cost).
- **All LLM calls go through the cached, resumable client.** Cache hits cost $0 and
  must still be logged as `cached: true`. Every call — cached or not — is logged to
  `reports/cost_log.md`. This is the audit trail; keep it complete.
- Keep costs reasonably low while maintaining quality. Flag the human before any
  single phase is likely to exceed a few dollars.

### Failure modes to actively guard against

- **Persona pollution**: narrating clusters into confident personas before stability
  supports it. Keep persona confidence proportional to cluster stability.
- **Schema-as-prior leakage**: the attribute schema biases everything. It must be
  data-derived and reviewed by the supervisor before scale extraction.
- **The "interesting outlier" trap**: small juicy clusters are usually unreliable.
  Enforce the 3% threshold.
- **Method-shopping**: never pick the method whose answer reads best. Report all.
- **Ignoring null results**: a failed hypothesis is a finding. Report it.
- **Sample-bias creep**: Reddit ≠ Brazilian retail investors at large. Reddit users
  skew young, urban, male, online. Every persona name and pain claim must be phrased
  to honor this scope: these are "Reddit-expressed personas," hypothesis-generating,
  NOT demographic ground truth. Sample bias must be on page 1 of the memo.
- **Quote integrity**: memo quotes must be real, attributable, and not cherry-picked.
  Surface 5+ candidate quotes per persona; selection happens transparently.

### What this study can and cannot conclude

CAN: what segments exist among Reddit-posting BR retail investors; their stated
needs/pains/behaviors; where the three methods agree (high confidence) and disagree
(interesting); how segment prevalence shifts across windows; whether subreddits draw
distinct populations.

CANNOT: anything about BR retail investors who don't post on Reddit (the majority);
causation (only correlation with macro cycles); real-population segment sizes (only
relative prevalence within Reddit discourse).

### Data provenance — locked

- Source: Watchful1 separated-subreddit dump, Academic Torrents, info hash
  `1614740ac8c94505e4ecb9d88be8bed7b6afddd4`, coverage 2005-06 to 2024-12.
- Format: per-subreddit zstandard-compressed ndjson.
- Fresh scraping is NOT used unless the human explicitly flags for it.
- Cite the source in the methodology appendix.

### Reproducibility rules — locked

- Treat `data/raw/` as READ-ONLY. Never modify or write to it.
- All random seeds = 42.
- All prompts live as versioned files in `prompts/`, never inline in notebooks.
- Intermediate outputs to `data/interim/`; final processed data to `data/processed/`;
  all reports/figures to `reports/`.
- Every phase produces a summary doc in `reports/` and then HALTS for review.

---

## 🔧 LIVING ZONE — Executor-maintained. Update this as the repo evolves.

Claude Code: keep this section accurate as the codebase grows. These are living
facts about how the repo works, not standing orders. Update freely, but do not
let updates here contradict the LOCKED zone above.

### Project status

- [x] Phase 0 — Data survey & provenance (complete; see `reports/phase0_summary.md`)
- [x] Phase 1 — Open coding & attribute schema design (complete; schema v1.1 locked,
      15 fields; see `reports/phase1_summary.md`)
- [x] Phase 2 — Full sampling & attribute extraction at scale (complete; $10.61,
      reliability κ≥0.93 all fields, 10 clustering features locked; see
      `reports/phase2_full_summary.md` and `reports/decisions_log.md`)
- [x] Phase 3A — Method 2 attribute clustering (COMPLETE, supervisor-approved;
      k=7 supervisor-selected; `data/processed/clusters_method2.parquet`;
      see `reports/phase3a_method2.md` and `reports/phase3a_explore.md`)
- [x] Phase 3B — Method 1 embedding + HDBSCAN (COMPLETE, supervisor-approved; 4 clusters,
      ARI=0.623, UMAP-dependency finding; `data/processed/clusters_method1.parquet`;
      see `reports/phase3b_method1.md`)
- [x] Phase 3C — Method 3 LLM-hierarchical (COMPLETE, SUPERVISOR-APPROVED 2026-05-21;
      k=4 medoids, sil=0.079, bootstrap ARI=0.618±0.264, ARI(M3,M2)=0.212;
      4 clusters: C0 earnest-learner (37%), C1 cynical-reactive (12%),
      C2 speculator/market-watcher (33%), C3 loss-as-meme (18%);
      M2-C1 verdict: "real posture, fuzzy boundaries" — continuum-end, NOT crisp cluster;
      `data/processed/clusters_method3.parquet`; see `reports/phase3c_method3.md`
      and `reports/decisions_log.md`)
- [x] Phase 3D — Cross-method comparison & hypothesis tests (COMPLETE, SUPERVISOR-APPROVED
      2026-05-21 with four carry-forwards; ARI M2×M3=0.212, M1 orthogonal (≈0) to both —
      split H3 verdict; H1 SUPPORTED on posture (M2 V=0.68, M3 V=0.65); H2 headline is
      two directional shifts (speculator 51→33→16%, cynical 29.5→38% A→C) not the weak
      aggregate; H4 PARTIALLY NULL — posture-dominated (estado_emocional 45%, 3.8× next
      feature) with circularity caveat; 3 candidate persona rows (2 crisp convergent +
      1 fuzzy cynical) + 2 demoted topical sub-themes; Phase 4 binding rules: personas
      led by emotional posture, M2 partition as counting backbone, topical subsets as
      texture not personas; see `reports/phase3d_synthesis.md`,
      `reports/phase3d_hypothesis_tests.md`, and `reports/decisions_log.md`)
- [x] Phase 4A — Persona quote bank (v1.1 SUPERVISOR-APPROVED 2026-05-21 with locked 15-quote selection;
      v1.0 = 375 quotes from 147 threads, 5 targets; v1.1 carry-forwards:
      (a) earnest pool supplemented with 25 new M3-C0 medoid-nearest + M1-C3 ∩ M2-C2 ∩ M3-C0
      threads via targeted paralysis/sossego/self_doubt prompt — yielded 65 new quotes incl.
      the ipn9s4 "sossego" line, wa7bjf R$400k paralysis, 1g6jgt7 "verdadeiro leigo" medoid;
      (b) cynic pool re-classified by sub-type: 36 institutional_cynicism (lead), 23
      personal_crisis (sparingly), 6 gambling_offtopic (EXCLUDED from memo), 15 other.
      Final 15-quote selection locked by supervisor 2026-05-21 (verbatim corpus forms,
      incl. unaccented "Sindrome" and colloquial "Investa"). Total cost $0.61 Haiku;
      see `reports/phase4a_quote_bank.md`, `data/processed/persona_quotes.jsonl`,
      `prompts/04a_*.md`)
- [x] Phase 4B — Persona narration (COMPLETE 2026-05-21, APPROVED WITH 1 EDIT;
      3 persona profiles in `reports/phase4b_personas.md` using supervisor-locked
      15-quote selection: Earnest Learner "Em Busca de Sossego" (47.6% M2, stable A→C,
      confirmed all 3 methods); Speculator "O Sardinha" (18.4%, 51→33→16% A→C declining,
      confirmed); Cynical-Reactive "O Cético Irônico" (30.0%, 29.5→38% A→C growing,
      real posture / fuzzy boundaries); plus situational-variant note for tax/IR and
      property/debt as earnest sub-themes (held for 4C). Word counts 259/282/319/109 vs
      ~200-250 target — cynical over due to required carry-forward framing.)
- [x] Phase 4C — Pains & needs (COMPLETE 2026-05-21, SUPERVISOR-APPROVED;
      `reports/phase4c_pains_needs.md`; Sossego-Seeker 3 pains (paralysis, IR, property)
      well-evidenced; Sardinha 2 pains (whiplash, structural-outgunned) + mandatory
      wellbeing flag; Cético Irônico 3 pains (exclusion, distrust, tax/legitimacy
      ethics-bound) + lower-confidence flag + ethics guardrail. All pains traced to
      locked quotes / fingerprints / hypothesis findings.)
- [x] Phase 4D — Memo (FINAL 2026-05-21, APPROVED WITH 3 EDITS + DECISION LOG;
      `reports/memo.md` — 650 words. v2 edits: (1) defensibility/moat sentence added
      (cross-institution reconciliation as natural moat); (2) "Validate first" note
      flagging IR pain is documented 2020–2024 and requires 2026 desk-check;
      (3) Cético reframed as "win later via earned credibility." Decision log entry
      added disclosing IR-wedge chosen partly for buildability over the more-central-
      but-fuzzier paralysis pain — product judgment supplementing data. See
      `reports/decisions_log.md` 2026-05-21 entry "Memo wedge = IR over paralysis".)
- [x] Phase 5 — Final assembly & handoff (COMPLETE 2026-05-21; comprehensive
      `README.md` written (navigation map, three findings, reproducibility,
      methodology disclosures, $28.68 cost summary); `src/threads.py` stratified-sample
      quartile bug fixed + disclosure block added to `reports/phase2_full_summary.md`;
      every appendix link in `reports/memo.md` verified to resolve; all phases marked
      complete. Study END-TO-END CLOSED.)
- [x] Phase 6 (SUPPLEMENTARY — COMPLETE 2026-05-21, SUPERVISOR-CONFIRMED null result)
      — r/investimentos-only sub-segmentation of the earnest mainstream. Verdict:
      **the earnest mainstream is one coherent persona; it does NOT resolve into
      sub-segments.** Re-clustering n=1,800 (78.3% originally M2-C2 earnest) on the
      locked 10 Method-2 features produced ONE genuine earnest core at every
      candidate k (P6-C7 at k=9: n=1,410, 96.5% originally-earnest). At no stable k
      did ≥2 earnest-dominated sub-segments clear the recomputed 54-thread floor
      with bootstrap ARI ≥ 0.5; the other above-floor groups at k=9 were the
      residual speculator and cynic/tax-edge tails re-surfacing, NOT mainstream
      sub-splits. Tax/IR and property/debt confirmed as **situational moments**,
      not sub-types. **Strengthens the Phase 4D recommendation: one product, one
      voice, sequenced by life-moment, not fragmented across sub-audiences.** No
      memo edits required. Evidential tier remains EXPLORATORY (single-subreddit,
      single-method) — does NOT supersede the triangulated three-persona headline,
      corroborates it. No finalize / naming run. See
      `reports/phase6_investimentos_explore.md` and `reports/decisions_log.md`
      2026-05-21 entry "Phase 6 closure: Sossego-Seeker is internally coherent."

### Environment

- Platform: WSL2, Python 3.x, 16 GB RAM (can be reallocated higher if needed).
- Always STREAM the .zst files; never load a full corpus into memory.
- Anthropic API key in env var `ANTHROPIC_API_KEY`.

### Directory map

<!-- TODO (executor): fill in the real tree after Phase 1 establishes the skeleton -->
```
decade-ba-case/
├── CLAUDE.md
├── README.md
├── requirements.txt
├── data/
│   ├── raw/          # downloaded .zst (READ-ONLY, gitignored)
│   ├── interim/      # filtered, threaded, caches, intermediate artifacts
│   └── processed/    # final sampled dataset
├── notebooks/        # one per phase: 00_..., 01_..., etc.
├── src/              # reusable modules (llm_client, threads, ...)
├── prompts/          # versioned LLM prompts
└── reports/          # summaries, figures, cost_log.md, final memo
```

### How to run

- Setup: `pip install -r requirements.txt`
- Phase 3A explore: `python notebooks/03a_attribute_clustering.py`
- Phase 3A finalize: `python notebooks/03a_attribute_clustering.py --finalize <k>`
- Phase 3B: `python notebooks/03b_embedding_clustering.py`
- Phase 3C repair failures: `python notebooks/03c_llm_hierarchical.py --repair-failures`
- Phase 3C explore (k=4..7): `python notebooks/03c_llm_hierarchical.py --cluster`
- Phase 3C finalize: `python notebooks/03c_llm_hierarchical.py --finalize <k>`

### Key modules

<!-- TODO (executor): document src/ modules and their interfaces as written -->
- `src/llm_client.py` — cached, resumable, cost-logging Anthropic wrapper.
  Cache keyed by (model, prompt_hash, input_hash) in `data/interim/llm_cache/`.
- `src/threads.py` — builds AuthorThread units (asymmetric per subreddit; see LOCKED).

### Cost log

- Lives at `reports/cost_log.md`. Columns: date | phase | task | model |
  input_tokens | output_tokens | est_cost_usd | notes.
- Log EVERY call including cache hits (cost 0, note `cached: true`).

### Data quirks discovered (append as found)

- r/investimentos: 32.5% submissions mod-removed; surviving corpus is curated.
- r/farialimabets: 61.7% link posts; dormant until mid-2020 then exploded.
- Link-id reconstruction works: ~62.6% (investimentos) / ~82.3% (farialimabets)
  of submissions have retrievable comments.
- langdetect flags ~8% as en/es — likely false positives on short PT finance text;
  use PT-stopword + accent heuristics, not langdetect alone, as the hard filter.

### Phase 2 outcomes & known deviations (must be disclosed in methodology)

- **KNOWN BUG — inverted quartile in `stratified_sample` (threads.py).** `top_q` used
  `num_comments >= scores[len//4]` (25th pctile) instead of `>= scores[len*3//4]`
  (75th pctile), so the "high-engagement" stratum drew from the top ~75% rather than
  top 25%. Effect: the working sample skews slightly toward median engagement; no
  individual record is corrupted, no junk introduced. SUPERVISOR DECISION: ride the
  current sample (extraction already complete), DISCLOSE as a known sampling
  deviation in the methodology appendix, and FIX the code for reproducibility. The
  fix must NOT trigger a re-extraction; it only corrects the repo for future runs.
- **Extraction reliability is high**: all 15 fields κ≥0.93 (ordinal) or ≥94.7%
  agreement (categorical) on a 150-thread re-extraction. Personas are not LLM-noise
  artifacts. `sofisticacao_tecnica` κ=1.000.
- **Cost**: Phase 2 total $10.61 (prompt caching cut Task 4 from ~$28 to $9.41;
  21.76M cache-read tokens vs 6,048 cache-write — auditable in cost_log.md).
- **Schema violations 1.8%**, concentrated in `objetivo`↔`estrategia` (those two
  adjacent fields bleed; residual ~0.7% each coerced to desconhecido). Documented.
- **First H1 signal**: farialimabets is 2–3× more `desconhecido` than investimentos
  across every person-defining field — a behavioral difference (react/joke vs.
  describe-situation), not a bug. Phase 3 MUST guard against a cluster that is really
  just "farialimabets threads we couldn't read" (missingness-pattern artifact).
- **Large goalless population**: ~46.6% objetivo desconhecido + ~33.5% explicitly
  `acumulacao_sem_objetivo_claro`. The explicit-goalless slice is a real candidate
  persona; the unknown slice is partly thin-thread noise — do not over-read it.

### SUPERVISOR OVERRIDE — feature set (logged; see reports/decisions_log.md)

The pre-registered 70% missingness rule split two ~70%-missing Brazil-specific fields
onto opposite sides by a 4-point rounding accident. Supervisor demoted BOTH for
symmetry (conservative direction). FINAL feature/flag split for ALL Phase 3 methods:

- **CLUSTERING FEATURES (10)**: sofisticacao_tecnica, fase_acumulacao,
  estrategia_principal, tolerancia_risco_declarada_ou_inferida,
  relacao_com_instituicoes_financeiras, estado_emocional_predominante,
  objetivo_financeiro_primario, ceticismo_institucional,
  exposicao_a_cripto_e_especulacao, identidade_comunitaria.
- **FLAGS — never clustered, used for enrichment + H1/H2 tests (8)**:
  subreddit_origem, window, relacao_com_selic_e_renda_fixa,
  perfil_tributario_e_fiscal, relacao_com_imovel_e_heranca,
  vinculo_empregaticio_e_renda, fonte_primaria_de_informacao, confianca_extracao.

`subreddit_origem` and `window` remain METADATA-ONLY (the H1/H2 firewall): never a
clustering feature; checked only AFTER clusters form.

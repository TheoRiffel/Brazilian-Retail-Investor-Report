# Decade BA Case — Brazilian Retail Investor Reddit Study

A scientific segmentation study of Brazilian retail investors posting on Reddit
between 2020 and 2024. Produces a partner-facing investment-thesis memo backed
by three independent clustering methods, hypothesis tests on a pre-registered
H1–H4 set, and a fully reproducible pipeline.

## Start here

**→ [`reports/memo.md`](reports/memo.md)** — the one-page deliverable. Reads in
3 minutes; states who the segments are, what to build, and for whom.

If you only have 60 seconds, the headline:

> Brazilian retail investors on Reddit divide into three posture-led personas
> — **Em Busca de Sossego** (47.6%), **O Sardinha** (18.4%), **O Cético
> Irônico** (30.0%). Decade should build an **integrated income-tax (IR)
> preparation tool for the Sossego-Seeker** as a wedge into a broader
> pre-decision-validation product. Sample is Reddit-active investors;
> hypothesis-generating, not demographic truth.

## The three findings (executive summary)

1. **Posture, not capital, segments this population.** Three independent
   clustering methods converge: the dominant axis (emotional-posture) carries
   roughly 3.8× the weight of the next feature, and the classical
   "beginner / intermediate / advanced" dimensions sit in the bottom half.
   Any segmentation that ignores posture misses the signal.
2. **Two crisp personas + one fuzzy continuum.** The Sossego-Seeker (the
   anxious mainstream learner) and O Sardinha (the euphoric speculator) are
   recovered by all three methods. O Cético Irônico (the ironic skeptic) is
   real but soft-edged — recovered by the two posture-reading methods,
   dispersed by the topic method. Carried as a continuum, not a crisp
   segment.
3. **The macro cycle is doing segmentation work.** As Selic rose, the
   speculator persona shrank monotonically (51% → 16% across windows
   A → B → C); the cynical-reactive posture grew in the opposite direction
   (29.5% → 38%). The Sossego-Seeker is stable across the cycle and grows
   alongside fixed-income relevance.

## Navigation map — which report answers what

| Question | Report |
|---|---|
| **What should we build, and for whom?** | [`reports/memo.md`](reports/memo.md) |
| **Who are the three personas in detail?** | [`reports/phase4b_personas.md`](reports/phase4b_personas.md) |
| **What specifically hurts each persona?** | [`reports/phase4c_pains_needs.md`](reports/phase4c_pains_needs.md) |
| **What do real users actually say?** (verbatim quote bank) | [`reports/phase4a_quote_bank.md`](reports/phase4a_quote_bank.md) |
| **How were the three methods compared? H1–H4 results?** | [`reports/phase3d_synthesis.md`](reports/phase3d_synthesis.md), [`reports/phase3d_hypothesis_tests.md`](reports/phase3d_hypothesis_tests.md) |
| **Method 2 — attribute clustering** | [`reports/phase3a_method2.md`](reports/phase3a_method2.md), [`reports/phase3a_explore.md`](reports/phase3a_explore.md) |
| **Method 1 — embedding + HDBSCAN** | [`reports/phase3b_method1.md`](reports/phase3b_method1.md) |
| **Method 3 — LLM-hierarchical k-medoids** | [`reports/phase3c_method3.md`](reports/phase3c_method3.md), [`reports/phase3c_brief.md`](reports/phase3c_brief.md) |
| **Attribute schema (15 fields) — how it was derived** | [`reports/phase1_summary.md`](reports/phase1_summary.md) |
| **Extraction stats, reliability, sampling caveats** | [`reports/phase2_full_summary.md`](reports/phase2_full_summary.md) |
| **Calibration round (pre-extraction)** | [`reports/phase2_calibration.md`](reports/phase2_calibration.md) |
| **Data inventory, quality scan, window feasibility** | [`reports/phase0_summary.md`](reports/phase0_summary.md) |
| **Every supervisor override and out-of-band decision** | [`reports/decisions_log.md`](reports/decisions_log.md) |
| **Every LLM call ever made (with cost + cache state)** | [`reports/cost_log.md`](reports/cost_log.md) |
| **Standing instructions / locked study rules** | [`CLAUDE.md`](CLAUDE.md) |

## Method, in one paragraph

Three independent clustering methods over a stratified sample of ~3,600 Reddit
threads (r/investimentos + r/farialimabets, three macro windows). **Method 2
(primary)** extracts a 15-field attribute schema (Phase 1 open-coded, locked
before scale extraction) per thread via Haiku 4.5, then runs k-medoids on Gower
distance over 10 clustering features. **Method 1** runs HDBSCAN on
multilingual mpnet embeddings. **Method 3** generates LLM holistic summaries
of each thread and clusters their mpnet embeddings via k-medoids PAM.
Cluster validity = (a) ≥3% of sample, (b) bootstrap stability, (c)
human-interpretable; all three methods report results in full, with
disagreement reported as a finding rather than hidden. Hypothesis tests H1–H4
are pre-registered, run on all three partitions where appropriate, and report
nulls honestly. See [`reports/phase3d_synthesis.md`](reports/phase3d_synthesis.md)
for the cross-method comparison.

## Reproduce from raw data

The pipeline is reproducible end-to-end from the raw Watchful1 .zst files.

**Environment.**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...   # required for any Haiku/Sonnet call
```

**Random seeds.** All non-determinism is seeded to `42` (sampling,
clustering, bootstrap, UMAP/HDBSCAN). The seeds are inline in the relevant
notebook constants.

**Pipeline order — run notebooks `00 → 04` in this sequence:**

| # | Notebook | Phase | What it does |
|---|---|---|---|
| 1 | `notebooks/00_phase0_data_survey.ipynb` | 0 | Inventory the .zst files; quality scan; window feasibility check |
| 2 | `notebooks/01_phase1_open_coding.ipynb` | 1 | 300-thread open coding → derive the 15-field attribute schema |
| 3 | `notebooks/02_phase2_sampling.py` | 2 | Stratified sample of ~3,600 threads across 6 cells (subreddit × window) |
| 4 | `notebooks/02b_phase2_extraction.py` | 2 | Haiku attribute extraction with prompt caching + reliability re-extraction |
| 5 | `notebooks/03a_attribute_clustering.py` | 3A | Method 2 — Gower k-medoids on the 10 clustering features (explore + finalize) |
| 6 | `notebooks/03b_embedding_clustering.py` + `03b_method1b_instruct.py` | 3B | Method 1 — multilingual mpnet embeddings + HDBSCAN |
| 7 | `notebooks/03c_llm_hierarchical.py` | 3C | Method 3 — Haiku per-thread summaries → embed → k-medoids PAM |
| 8 | `notebooks/03d_phase3d_synthesis.py` | 3D | Cross-method ARI + H1/H2/H4 hypothesis tests + candidate persona rows |
| 9 | `notebooks/04a_quote_mining.py` + `04a_quote_mining_supplement.py` | 4A | Per-persona verbatim quote extraction + supervisor-revision supplement |
|10 | `reports/phase4b_personas.md` (manual narration; uses locked quote selection) | 4B | Persona profiles |
|11 | `reports/phase4c_pains_needs.md` (manual narration) | 4C | Pains and unmet needs per persona |
|12 | `reports/memo.md` (manual narration) | 4D | The one-page partner-facing deliverable |

**Prompts** live as versioned files in [`prompts/`](prompts/) — never inline
in notebooks. The relevant files: `01_open_coding.md`, `02_schema_synthesis.md`,
`03_attribute_extraction.md` (extraction prompt with the calibration examples),
`04_thread_summary.md` (Method 3 summaries), `04a_quote_extraction.md`,
`04a_earnest_supplement.md`, `04a_cynic_subtype_tagging.md`.

**LLM client.** All API calls go through
[`src/llm_client.py`](src/llm_client.py) which provides:
- file-based caching keyed on `(model, system, user_text, salt)` — repeated
  runs cost $0 once cached;
- Anthropic server-side prompt caching (`use_prompt_cache=True`) for the
  high-volume extraction prompts;
- automatic cost logging to `reports/cost_log.md` on every call (cache hits
  included, marked `cached: true`).

**Cost-log audit.** Every LLM call ever made, with input/output tokens and
estimated cost, lives in [`reports/cost_log.md`](reports/cost_log.md). The
log is append-only and cache-aware.

## Cost summary

| Phase | API calls | Input tokens | Output tokens | Cost |
|---|---:|---:|---:|---:|
| Phase 0 (data survey, no API) | 16 | 0 | 0 | $0.00 |
| Phase 1 (open coding) | 302 | 448k | 152k | $1.69 |
| Phase 2 (extraction) | 3,852 | 2.93M | 1.08M | $10.61 |
| Phase 3C (LLM thread summaries) | 4,207 | 4.40M | 2.27M | $15.76 |
| Phase 4A (quote mining + cynic subtypes) | 252 | 426k | 38k | $0.61 |
| **Total** | **8,629** | **8.20M** | **3.54M** | **$28.68** |

**~$29 of LLM spend buys three triangulated clustering methods over ~3,600
threads, hypothesis tests on a pre-registered H1–H4 set, an attribute schema
derived from data (not priors), a verbatim quote bank, and full
reproducibility from raw .zst files.** Phase 2 extraction was the largest
single cost; Anthropic prompt-caching cut it from a projected $28 to $9.41
(see `reports/decisions_log.md`).

## Project status

| Phase | Status | Output |
|---|---|---|
| Phase 0 — data survey | complete | `reports/phase0_summary.md` |
| Phase 1 — open coding + schema | complete | `reports/phase1_summary.md` |
| Phase 2 — extraction | complete | `reports/phase2_full_summary.md` |
| Phase 3A — Method 2 attribute clustering | complete | `reports/phase3a_method2.md` |
| Phase 3B — Method 1 embedding + HDBSCAN | complete | `reports/phase3b_method1.md` |
| Phase 3C — Method 3 LLM-hierarchical | complete | `reports/phase3c_method3.md` |
| Phase 3D — cross-method synthesis + H1/H2/H4 | complete | `reports/phase3d_synthesis.md`, `phase3d_hypothesis_tests.md` |
| Phase 4A — quote bank | complete | `reports/phase4a_quote_bank.md` |
| Phase 4B — persona profiles | complete | `reports/phase4b_personas.md` |
| Phase 4C — pains & unmet needs | complete | `reports/phase4c_pains_needs.md` |
| Phase 4D — memo | complete | `reports/memo.md` |
| Phase 5 — packaging & handoff | complete | this README + repo state |

## Methodology disclosures

- **Stratified-sampling bug in `src/threads.py` (Phase 2).** The `top_q`
  "high-engagement" stratum was thresholded at the 25th percentile rather
  than the 75th percentile, so the working sample skews slightly toward
  median engagement. No record corrupted; no junk introduced. Supervisor
  decided to ride the existing extraction; the code is fixed for future
  runs. See `reports/phase2_full_summary.md` for the disclosure and
  `reports/decisions_log.md` for the rationale.
- **`subreddit_origem` is metadata, never a clustering feature.** The H1
  firewall is structural and respected throughout. Any cluster × subreddit
  signal is genuinely post-hoc.
- **`evasao_ou_zona_cinzenta` is observed and counted, never facilitated.**
  Tax gray-zone behavior is part of the corpus; the locked CLAUDE.md ethics
  rule (observe and count, never facilitate) is honored through to the memo.
- **H4 has a circularity caveat.** The dominant clustering feature
  (`estado_emocional_predominante`) was itself a clustering input, so the
  H4 finding describes M2 partition *geometry*, not external causal truth.
  The non-circular finding — that the classical sophistication/capital axes
  are in the bottom half — is robust. See
  `reports/phase3d_hypothesis_tests.md` H4 section.
- **Cynical-reactive persona is fuzzy.** Real posture, soft boundaries.
  Carried as a continuum, not a crisp segment. See `reports/decisions_log.md`
  2026-05-21 M2-C1 verdict.
- **The IR-wedge product call is product judgment supplementing data.** The
  Phase 4C pain priority order puts paralysis-validation as Pain 1 and IR
  as Pain 2; the memo's wedge selection prioritizes buildability and
  trust-earning sequence. See `reports/decisions_log.md` 2026-05-21
  "Memo wedge = IR over paralysis".

## What this study can and cannot conclude

**Can:** the segments that exist among Reddit-posting Brazilian retail
investors, their stated needs/pains/behaviors, where the three methods
agree (high confidence) and disagree (interesting), how segment prevalence
shifts across macro windows, whether subreddits draw measurably different
populations (they do).

**Cannot:** anything about Brazilian retail investors who don't post on
Reddit (the majority); causation (only correlation with macro cycles);
real-population segment sizes (only relative prevalence within Reddit
discourse). Sample bias must be on page 1 of any derivative artifact.

## Data provenance & scope

| Field | Value |
|---|---|
| Source | Watchful1 separated-subreddit dump |
| Distribution | Academic Torrents (info hash `1614740ac8c94505e4ecb9d88be8bed7b6afddd4`) |
| Coverage | 2005-06 to 2024-12 |
| Format | Zstandard-compressed newline-delimited JSON |
| Subreddits used | r/investimentos, r/farialimabets |
| Windows | A: 2020-06→2021-06 (Selic ~2%); B: 2022-01→2023-01 (Selic rising to ~13.75%); C: 2024-01→2024-12 (mature fixed income) |

**Scoping note.** The original design referenced four subreddits (added
r/FIIs and r/BrasilFinancas); the latter two were not present in the
Watchful1 top-40k corpus, so the scope was narrowed to two subreddits —
a documented, defensible data-availability decision.

## Repo layout

```
decade-ba-case/
├── README.md             ← you are here
├── CLAUDE.md             ← locked study rules + executor-maintained status
├── requirements.txt
├── data/
│   ├── raw/              ← .zst files (READ-ONLY, gitignored)
│   ├── interim/          ← filtered threads, caches, intermediates
│   └── processed/        ← parquets, final sampled dataset, persona_quotes.jsonl
├── notebooks/            ← 00→04, the pipeline
├── src/
│   ├── llm_client.py     ← cached, cost-logged Anthropic wrapper
│   └── threads.py        ← AuthorThread unit assembly + stratified sampling
├── prompts/              ← versioned prompts (never inline)
└── reports/              ← all summaries, figures, the memo, cost+decisions logs
```

## License & attribution

This is an internal study deliverable. Cite the Watchful1 dump (Academic
Torrents) for data provenance. The Reddit content is public-record posting;
quotes carry their original `thread_id` for traceback.

# Phase 3C Brief — Method 3: LLM-Hierarchical Clustering (Kura-style)

**Issued:** 2026-05-20  
**Status: APPROVED TO PROCEED** — Phase 3B supervisor review complete.  
**Blocked phases:** 3D (cross-method comparison) remains blocked until 3C is reviewed.

---

## Supervisor readings carried into Phase 3C

From the Phase 3B review, four decisions govern how 3C is run and what it must answer:

1. **M2-C1 remains PROVISIONAL.** The automated promotion recommendation from Section 11.3 of the Phase 3B report is overruled. The 72.6% concentration of M2-C1 threads in M1-C3 is not evidence of a coherent group — M1-C3 is the 67.8%-base-rate catch-all. The null is: M2-C1 threads land in M1-C3 simply because everything does. Method 3 is the decisive adjudication test. If Method 3 independently recovers a cynical/ironic/goalless-without-clear-anxiety group from the text alone, M2-C1 is promoted. If Method 3 dissolves it into the mainstream mass, M2-C1 is demoted to edge.

2. **Three Method 1 signals to probe.** Method 1's topic separation identified three groups not legible from attributes alone: (a) the **property/banking/debt** cluster (M1-C1: bank switching, mortgage math, credit-card debt), (b) the **tax/IR** cluster (M1-C0: DARF, declaration, IR on FIIs/ações), (c) the **partial speculator recovery** (M1-C2: crypto-heavy, euphoric or cynical, short-termist). Method 3 — which reads full thread context with longer window — must check whether holistic LLM summaries find these topic-defined groups or dissolve them into broader posture clusters. Report the outcome explicitly.

3. **Method 1's 512-token truncation finding goes in the methodology appendix**, documented as a finding, not a failure: topic-level separation is possible within 512 tokens; posture and tone separation requires longer context or explicit attribute extraction. Method 3 uses the LLM's context window (no truncation to 512) and will test whether the posture signals become visible.

4. **UMAP-dependency finding** (M1: 0 clusters without UMAP) goes in the methodology appendix. It does not affect Method 3's design.

---

## What Method 3 is (simplified Kura-style, defined here)

Full Kura (Broomé 2024) runs a bottom-up hierarchical merge of LLM-generated cluster descriptions. The compressed version used here has three stages:

**Stage 1 — Thread summarization (Haiku).** For each of the 3,600 threads, generate a compact investor-type profile (≤120 words). The prompt asks: what is this person's financial situation, what do they care about, and what is their emotional register? The prompt does NOT show the attribute schema — this stage must be schema-blind to avoid schema-as-prior contamination. Summaries are the only input to Stages 2 and 3.

**Stage 2 — Batch type discovery (Haiku).** Divide the 3,600 summaries into batches of 60. For each batch, ask the LLM to identify 2–6 recurring investor types and assign each summary to one type. Record the type label and a 2-sentence type description for each batch. This produces ~60 batch-level typologies.

**Stage 3 — Consolidation and assignment (Sonnet).** Feed all ~60 batch-level typology descriptions to Sonnet in a single call (they are short). Ask it to merge overlapping types into a final candidate set of 4–8 types, with names and defining characteristics. Then, for each thread summary (Haiku, batched), assign to one of the consolidated types. This produces the final per-thread M3 label.

**Stability run.** Repeat Stages 2–3 once more with a different random shuffle of the summaries. Compute ARI between run-1 and run-2 labels. Report mean ARI as the Method 3 stability estimate. If ARI < 0.3, note instability explicitly; do not suppress it.

---

## Algorithm specification (for implementation)

### Inputs

- `data/processed/working_sample.jsonl` — thread text (field: `text`, `thread_id`, `subreddit`, `window`)
- `data/processed/clusters_method2.parquet` — M2 labels (join key: `thread_id`) — for adjudication only, never as input to Stage 1/2/3
- `data/processed/clusters_method1.parquet` — M1 labels (join key: `thread_id`) — same

### Model assignment

| Stage | Model | Temperature | Notes |
|-------|-------|-------------|-------|
| Stage 1: summarization | `claude-haiku-4-5-20251001` | 0.1 | per-thread; cache system prompt |
| Stage 2: batch type discovery | `claude-haiku-4-5-20251001` | 0.3 | per-batch; slightly higher temp for diversity |
| Stage 3: consolidation | `claude-sonnet-4-6` | 0.3 | one call per run |
| Stage 3: assignment | `claude-haiku-4-5-20251001` | 0.1 | per-thread; cache system+consolidated-types prompt |

### Prompt files (create these in `prompts/`)

All prompts live as versioned files. Do not inline them in the notebook.

- `prompts/m3_stage1_summary.txt` — thread → investor-type summary (schema-blind)
- `prompts/m3_stage2_batch_types.txt` — batch of summaries → type list with descriptions
- `prompts/m3_stage3_consolidate.txt` — batch typologies → merged final type set
- `prompts/m3_stage3_assign.txt` — summary + consolidated types → type assignment

### Stage 1 prompt guidance

The Stage 1 prompt must not reproduce or reference the 15-field attribute schema. It should ask three natural-language questions about the thread:

1. What is this person's financial situation (approximate capital stage, what they hold or want to hold)?
2. What is their primary concern or question (what do they want to know or do)?
3. What is their emotional register in this post (anxious, curious, cynical, euphoric, matter-of-fact, etc.)?

Output as structured prose (not JSON). Cap at 120 words. Include the thread_id as a header so outputs are parseable.

### Stage 2 prompt guidance

Input: 60 investor-type summaries (one paragraph each). Ask: "Reading these investor profiles, what distinct types of Brazilian retail investors do you see? Identify 2–6 recurring types. For each type, give: a short name (3–5 words), a 2-sentence description of defining traits, and a list of which profile IDs belong to this type." Output as structured text parseable into (type_name, description, [ids]).

### Stage 3 consolidation prompt guidance

Input: all batch-level type descriptions (names + 2-sentence descriptions only, not the IDs). Ask: "These type descriptions come from 60 independent batches of investor profiles. Merge overlapping types. Produce a final set of 4–8 investor types that covers the full range. For each type: a short name, a 3-sentence description of defining traits and differentiators." Output as structured text.

### Stage 3 assignment prompt guidance

Input: one summary + the full consolidated type set. Ask: "Which of the following investor types best describes this person? Choose exactly one. If none fits well, choose the closest and flag it." Output: type_name, confidence (HIGH/MED/LOW), optional flag.

### Caching

Stage 1: cache the system prompt (it is the same for all 3,600 calls). Stage 3 assignment: cache the system prompt + consolidated type definitions (they are fixed after consolidation).

### Outputs

- `data/interim/m3_summaries.jsonl` — thread_id + Stage 1 summary (intermediate)
- `data/interim/m3_batch_types_run1.jsonl` and `_run2.jsonl` — Stage 2 batch outputs
- `data/interim/m3_consolidated_types_run1.json` and `_run2.json` — Stage 3 consolidated type set
- `data/processed/clusters_method3.parquet` — final per-thread labels (thread_id, m3_label_run1, m3_label_run2, confidence, flag)
- `reports/phase3c_method3.md` — the output report (produced by the script)
- `reports/figures/m3_*.png` — figures

---

## Report structure (`reports/phase3c_method3.md`)

The output script must produce this report. Match the Phase 3A/3B structure.

### Required sections

1. **Methodology** — stages, models, temperatures, batch sizes, prompt files used, seed.
2. **Run 1 cluster summary** — type names, sizes, % of corpus, below-3%-floor flags.
3. **Run 2 cluster summary** — same format.
4. **Stability: ARI(run1, run2)** — report the number. If < 0.3 flag as unstable.
5. **Cluster profiles** — for each run-1 type above the 3% floor: the consolidated type description, top-5 exemplar thread IDs with truncated text (300 chars), missingness artifact check (join M2 attributes; flag if mean_missing > 1.5).
6. **Adjudication — four questions** (see below). Each answered with cross-tab + entropy + interpretation.
7. **M3 × M2 cross-tabulation** — full matrix.
8. **M3 × M1 cross-tabulation** — full matrix.
9. **Consolidated type descriptions** — the full text of the final type set from Stage 3, verbatim.
10. **Cost log entries** — all LLM calls, tokens, est. cost; also write to `reports/cost_log.md`.
11. **Hard stop** and status line.

---

## Adjudication questions (answer all four in Section 6 of the report)

These are the pre-specified tests for Phase 3C. Answer each with: (a) the cross-tab numbers, (b) the entropy of the relevant M2/M1 cluster across M3 types, (c) a plain-language verdict.

### Q1 — M2-C1 (cynical-reactive): does Method 3 find it independently?

M2-C1 profile: low sophistication (1.48), low crypto (1.17), high cynicism/irony (57.4% cinico_ou_ironico), high missingness (3.05 per thread), high institutional skepticism (3.17), frequently goalless (61.6% acumulacao_sem_objetivo_claro).

For each M3 type, compute the fraction of its members that are M2-C1. If one M3 type has M2-C1 concentration substantially above 30% (M2-C1's base rate) and is characterized by cynical/ironic language in the consolidated description, interpret as corroboration. If M2-C1 threads scatter uniformly across M3 types, interpret as disconfirmation. The supervisor decision applies: if disconfirmation, M2-C1 is demoted to edge in Phase 3D; if corroboration, it is promoted.

### Q2 — M1-C1 signal (property/banking/debt): does Method 3 find it?

M1-C1 profile: bank switching, mortgage math, credit-card debt, institution navigation. n=465. Exemplar text: discussions of financiamento imobiliário, cartão de crédito, corretora vs. banco, dívida. If M3 produces a type whose exemplars overlap heavily with M1-C1 and whose description references property, banking, or debt contexts, the signal survives the truncation-free test. Cross-tab M3 × M1-C1.

### Q3 — M1-C0 signal (tax/IR): does Method 3 find it?

M1-C0 profile: IR declaration, DARF, FII taxation, cartão-de-crédito IR. n=154, unstable (Jaccard 0.132). The instability could reflect small n or a genuinely narrow topic. If M3 finds a type centered on taxation/compliance, note it. If the topic disperses (IR questions land inside a broader "anxious beginner" or "earnest learner" type), that is also a valid finding — document it.

### Q4 — M1-C2 / M2-C5 signal (speculator/crypto): does Method 3 recover it?

Both prior methods found this group clearly (M2-C5 Jaccard=0.770; M1-C2 stable). If Method 3 does NOT produce a crypto-speculator type, that is a red flag about Stage 2–3 sensitivity. Expected outcome: yes, Method 3 finds it. If not found, investigate whether the Stage 1 summaries are suppressing the crypto signal.

---

## Cost estimate and flag threshold

| Stage | Threads | Model | Est. input tokens | Est. output tokens | Est. cost |
|-------|---------|-------|-------------------|--------------------|-----------|
| Stage 1: summarize (×1) | 3,600 | Haiku | ~5.4M (w/ caching ~1.1M non-cached) | ~540K | ~$3.0 |
| Stage 2: batch types (×2 runs) | 60 batches × 2 | Haiku | ~720K | ~180K | ~$0.9 |
| Stage 3: consolidate (×2 runs) | 2 | Sonnet | ~40K | ~4K | ~$0.3 |
| Stage 3: assign (×2 runs) | 7,200 | Haiku | ~3.6M (w/ caching ~0.4M non-cached) | ~360K | ~$1.8 |
| **Total** | | | | | **~$6.0** |

This is a rough estimate assuming ~60% cache hit on Stage 1 and ~90% cache hit on Stage 3 assignment (type definitions are fixed). Actual cost may vary ±50%. **Flag the human before proceeding if any single stage looks like it will exceed $8 before completion.** Total phase budget ceiling: $15 (shared with all Phase 3 work; $10.61 spent in Phase 2; remain mindful).

Log every call — cached or not — in `reports/cost_log.md`.

---

## Implementation notes

- Use `src/llm_client.py` (the cached, resumable client) for all calls.
- Stage 1 is the longest operation. Implement with progress logging every 100 threads.
- The batch-type Stage 2 output is semi-structured text. Parse defensively: if the LLM returns malformed output for a batch, log the batch ID and skip it (don't crash).
- Stage 3 consolidation is a single Sonnet call. If it returns fewer than 4 or more than 8 types, re-prompt once with the constraint made explicit. If still out of range, accept the result and document it.
- The assignment prompt includes confidence (HIGH/MED/LOW) and a flag for poor-fit cases. Tabulate flag rates per cluster — a type with >20% flagged assignments may be poorly defined.
- All random seeds = 42. Batch shuffle seed = 42 (run 1) and 43 (run 2) to create the stability variation.

---

## What this phase does NOT do

- Does not name personas. Types get short descriptive labels from Stage 3 (e.g., "cautious fixed-income accumulator"), not polished persona names. Those come in Phase 4.
- Does not determine which method wins. That is Phase 3D.
- Does not run H1 or H2 tests. Those require all three methods complete.
- Does not touch `data/raw/`. Ever.

---

## Hard stop

Phase 3C ends when `reports/phase3c_method3.md` is complete and the four adjudication questions are answered. The script must print a clear HALT message and not proceed to any Phase 3D work. Phase 3D is blocked until the supervisor reviews this report.

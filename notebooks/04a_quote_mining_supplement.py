#!/usr/bin/env python3
"""
Phase 4A supplement — supervisor carry-forwards 2026-05-21.

Two operations:
  (1) Targeted earnest-learner re-pull: ~25 new threads from M3-C0 medoid
      neighbourhood + M1-C3 ∩ M2-C2 ∩ M3-C0 triple, with a prompt steered
      toward paralysis / sossego / self_doubt.
  (2) Cynic sub-type tagging: re-classify each existing M2-C1 candidate quote
      as institutional_cynicism / personal_crisis / gambling_offtopic / other,
      using the source post as context.

Then regenerates `reports/phase4a_quote_bank.md` with:
  - supplemented earnest pool (original + supplement, ranked together)
  - cynic pool grouped by sub-type (institutional_cynicism first, personal_crisis
    sparingly, gambling_offtopic excluded)
  - other targets (speculator, both sub-themes) unchanged.

Outputs:
  - data/processed/persona_quotes.jsonl     (augmented in place)
  - reports/phase4a_quote_bank.md           (regenerated)
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
INTERIM = ROOT / "data" / "interim"
PROMPTS = ROOT / "prompts"
REPORTS = ROOT / "reports"

sys.path.insert(0, str(ROOT))
from src.llm_client import async_call  # noqa: E402

CONFIANCA_MIN = 3
UNIT_TEXT_CAP_CHARS = 8000
CONCURRENCY = 8
MODEL = "claude-haiku-4-5-20251001"
TEMP = 0.1
PHASE = "4A"

# How many new earnest threads to extract from
N_NEW_EARNEST_THREADS = 25

# M3-C0 medoid thread per Phase 3C report
M3_C0_MEDOID_TID = "1g6jgt7"


# ---------------------------------------------------------------------------
# Prompt loading
# ---------------------------------------------------------------------------


def load_prompt(path: Path) -> tuple[str, str]:
    raw = path.read_text()
    sys_match = re.search(
        r"## System prompt\n\n(.*?)\n---\n\n## User-message template",
        raw,
        re.DOTALL,
    )
    user_match = re.search(
        r"## User-message template\n\n```\n(.*?)\n```",
        raw,
        re.DOTALL,
    )
    if not sys_match or not user_match:
        raise RuntimeError(f"Could not parse {path.name}")
    return sys_match.group(1).strip(), user_match.group(1).strip()


# ---------------------------------------------------------------------------
# Earnest supplement: select new threads
# ---------------------------------------------------------------------------


def select_new_earnest_threads(existing_threads: set[str]) -> pd.DataFrame:
    m1 = pd.read_parquet(PROC / "clusters_method1.parquet")[
        ["thread_id", "cluster_label"]
    ].rename(columns={"cluster_label": "M1"})
    m2 = pd.read_parquet(PROC / "clusters_method2.parquet")[
        ["thread_id", "cluster_label", "dist_to_medoid", "silhouette_sample"]
    ].rename(columns={"cluster_label": "M2"})
    m3 = pd.read_parquet(PROC / "clusters_method3.parquet")[
        ["thread_id", "subreddit", "window", "cluster_label"]
    ].rename(columns={"cluster_label": "M3"})
    attr = pd.read_parquet(PROC / "extracted_attributes.parquet")[
        ["thread_id", "confianca_extracao"]
    ]
    working = pd.read_json(PROC / "working_sample.jsonl", lines=True)[
        ["thread_id", "unit_text"]
    ]

    df = (
        m3.merge(m1, on="thread_id", how="left")
        .merge(m2, on="thread_id", how="left")
        .merge(attr, on="thread_id", how="left")
        .merge(working, on="thread_id", how="left")
    )

    # Pool 1 — M3-C0 medoid-nearest by cosine distance (mpnet, L2-normalised).
    emb = np.load(INTERIM / "m3_emb_mpnet.npy")
    if emb.shape[0] != len(m3):
        raise RuntimeError("Embedding rows do not align with M3 parquet")
    medoid_idx = m3.index[m3.thread_id == M3_C0_MEDOID_TID].tolist()[0]
    medoid_vec = emb[medoid_idx]
    # L2-normalised → cosine distance = 1 - dot product
    dists = 1.0 - (emb @ medoid_vec)
    df["dist_to_m3c0_medoid"] = dists

    # Pool 1 candidates: in M3-C0, confianca>=3, unit_text not null, NOT already mined
    pool1 = df[
        (df.M3 == "M3-C0")
        & (df.confianca_extracao >= CONFIANCA_MIN)
        & df.unit_text.notna()
        & (~df.thread_id.isin(existing_threads))
    ].sort_values(
        ["dist_to_m3c0_medoid", "confianca_extracao", "thread_id"],
        ascending=[True, False, True],
    )
    print(f"Pool 1 (M3-C0 medoid-nearest, excluding existing): {len(pool1)} candidates")

    # Pool 2 — M1-C3 ∩ M2-C2 ∩ M3-C0 convergent core
    pool2 = df[
        (df.M1 == "M1-C3")
        & (df.M2 == "M2-C2")
        & (df.M3 == "M3-C0")
        & (df.confianca_extracao >= CONFIANCA_MIN)
        & df.unit_text.notna()
        & (~df.thread_id.isin(existing_threads))
    ].sort_values(
        ["dist_to_medoid", "silhouette_sample", "confianca_extracao", "thread_id"],
        ascending=[True, False, False, True],
    )
    print(f"Pool 2 (M1-C3 ∩ M2-C2 ∩ M3-C0 triple, excluding existing): {len(pool2)} candidates")

    # Take half from each pool, dedup, cap at N_NEW_EARNEST_THREADS total
    half = N_NEW_EARNEST_THREADS // 2 + 1
    pool1_top = pool1.head(half)
    pool2_top = pool2.head(half)
    combined = pd.concat([pool1_top, pool2_top]).drop_duplicates("thread_id")
    combined = combined.head(N_NEW_EARNEST_THREADS).reset_index(drop=True)
    # tag provenance
    combined["source_pool"] = combined.thread_id.apply(
        lambda tid: "m3c0_medoid_nearest"
        if tid in set(pool1_top.thread_id)
        else "triple_m1c3_m2c2_m3c0"
    )
    print(
        f"Selected {len(combined)} unique new threads "
        f"({(combined.source_pool == 'm3c0_medoid_nearest').sum()} from Pool 1, "
        f"{(combined.source_pool == 'triple_m1c3_m2c2_m3c0').sum()} from Pool 2)"
    )
    return combined


# ---------------------------------------------------------------------------
# Async Haiku calls
# ---------------------------------------------------------------------------


def truncate(s: str) -> str:
    if not isinstance(s, str):
        return ""
    if len(s) <= UNIT_TEXT_CAP_CHARS:
        return s
    return s[:UNIT_TEXT_CAP_CHARS] + "\n[...texto truncado para extração...]"


def parse_json(raw: str) -> dict:
    s = raw.strip()
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*", "", s)
        s = re.sub(r"\s*```\s*$", "", s)
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", s, re.DOTALL)
        if not m:
            return {}
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            return {}


def post_block(unit_text: str) -> str:
    return unit_text.split("--- Top comments ---", 1)[0] if isinstance(unit_text, str) else ""


def verbatim_check(quote_text: str, source: str) -> bool:
    norm = lambda s: re.sub(r"\s+", " ", s).strip()
    return norm(quote_text) in norm(source)


async def extract_earnest_quotes(
    sem: asyncio.Semaphore,
    system_prompt: str,
    user_template: str,
    thread_id: str,
    unit_text: str,
) -> dict:
    user_text = user_template.format(unit_text=truncate(unit_text))
    async with sem:
        result = await async_call(
            system=system_prompt,
            user_text=user_text,
            model=MODEL,
            temperature=TEMP,
            max_tokens=700,
            phase=PHASE,
            task="quote_extraction_earnest_supplement",
            notes=f"thread={thread_id}",
            use_prompt_cache=True,
        )
    return {
        "thread_id": thread_id,
        "raw_response": result["text"],
        "from_cache": result["from_cache"],
    }


async def classify_cynic_quote(
    sem: asyncio.Semaphore,
    system_prompt: str,
    user_template: str,
    quote_idx: int,
    quote_text: str,
    unit_text: str,
) -> dict:
    user_text = user_template.format(
        quote_text=quote_text, unit_text=truncate(unit_text)
    )
    # Salt the cache key with the quote_idx so identical quote-texts (rare but
    # possible if the same line appears in two threads) get classified per-instance.
    async with sem:
        result = await async_call(
            system=system_prompt,
            user_text=user_text,
            model=MODEL,
            temperature=TEMP,
            max_tokens=200,
            phase=PHASE,
            task="cynic_subtype_tagging",
            notes=f"quote_idx={quote_idx}",
            use_prompt_cache=True,
            salt=str(quote_idx),
        )
    parsed = parse_json(result["text"])
    return {
        "quote_idx": quote_idx,
        "subtype": parsed.get("subtype", "other"),
        "rationale_en": parsed.get("rationale_en", ""),
        "from_cache": result["from_cache"],
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main():
    # --- Load existing quotes -------------------------------------------------
    existing: list[dict] = []
    with open(PROC / "persona_quotes.jsonl", encoding="utf-8") as f:
        for line in f:
            existing.append(json.loads(line))
    existing_earnest_tids = {
        q["thread_id"] for q in existing if q["target_key"] == "earnest_learner"
    }
    print(f"Existing quotes: {len(existing)}")
    print(f"Existing earnest threads: {len(existing_earnest_tids)}")

    # working_sample lookup for cynic context
    ws_lookup: dict[str, str] = {}
    with open(PROC / "working_sample.jsonl", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            ws_lookup[rec["thread_id"]] = rec.get("unit_text", "")

    # =========================================================================
    # Operation 1 — earnest supplement extraction
    # =========================================================================
    earnest_sys, earnest_user = load_prompt(PROMPTS / "04a_earnest_supplement.md")
    new_earnest = select_new_earnest_threads(existing_earnest_tids)

    sem = asyncio.Semaphore(CONCURRENCY)
    print(f"\nRunning earnest supplement extraction on {len(new_earnest)} threads...")
    extract_tasks = [
        extract_earnest_quotes(
            sem, earnest_sys, earnest_user, r.thread_id, r.unit_text
        )
        for r in new_earnest.itertuples()
    ]
    extract_results = await asyncio.gather(*extract_tasks)
    cache_hits = sum(1 for r in extract_results if r["from_cache"])
    print(f"Earnest extraction cache hits: {cache_hits}/{len(extract_results)}")

    # build new quote records
    new_quotes: list[dict] = []
    for raw_res, row in zip(extract_results, new_earnest.itertuples()):
        parsed = parse_json(raw_res["raw_response"])
        quotes = parsed.get("quotes", []) if isinstance(parsed, dict) else []
        pb = post_block(row.unit_text)
        for q in quotes:
            text = (q.get("text", "") or "").strip()
            qtype = (q.get("type", "") or "").strip()
            gloss = (q.get("gloss_en", "") or "").strip()
            if not text:
                continue
            wc = len(text.split())
            new_quotes.append(
                {
                    "target_key": "earnest_learner_supplement",
                    "target_label": "Earnest Learner (supplement)",
                    "target_kind": "persona_supplement",
                    "method": "M3+M2+M1 triple",
                    "cluster_label": "M2-C2 / M3-C0",
                    "thread_id": row.thread_id,
                    "subreddit": row.subreddit,
                    "window": row.window,
                    "selection_score": float(row.dist_to_m3c0_medoid),
                    "source_pool": row.source_pool,
                    "type": qtype,
                    "text_pt": text,
                    "gloss_en": gloss,
                    "word_count": wc,
                    "verbatim_match": verbatim_check(text, pb),
                    "over_25_words": wc > 25,
                }
            )

    print(f"New earnest quotes extracted: {len(new_quotes)}")
    new_verbatim = sum(1 for q in new_quotes if q["verbatim_match"])
    print(f"  verbatim-OK: {new_verbatim}/{len(new_quotes)}")

    # =========================================================================
    # Operation 2 — cynic sub-type tagging
    # =========================================================================
    cynic_sys, cynic_user = load_prompt(PROMPTS / "04a_cynic_subtype_tagging.md")
    cynic_quotes_idxs = [
        (i, q) for i, q in enumerate(existing) if q["target_key"] == "cynical_reactive"
    ]
    print(f"\nClassifying {len(cynic_quotes_idxs)} cynic quotes by sub-type...")

    classify_tasks = [
        classify_cynic_quote(
            sem,
            cynic_sys,
            cynic_user,
            quote_idx=i,
            quote_text=q["text_pt"],
            unit_text=ws_lookup.get(q["thread_id"], ""),
        )
        for i, q in cynic_quotes_idxs
    ]
    classify_results = await asyncio.gather(*classify_tasks)
    cache_hits_c = sum(1 for r in classify_results if r["from_cache"])
    print(f"Cynic classification cache hits: {cache_hits_c}/{len(classify_results)}")

    # Apply subtype to existing quotes
    for res in classify_results:
        existing[res["quote_idx"]]["cynic_subtype"] = res["subtype"]
        existing[res["quote_idx"]]["cynic_subtype_rationale_en"] = res["rationale_en"]

    # Diagnostics on sub-type distribution
    subtype_counts: dict[str, int] = defaultdict(int)
    for i, q in cynic_quotes_idxs:
        subtype_counts[existing[i].get("cynic_subtype", "?")] += 1
    print("Cynic sub-type distribution:")
    for k, v in sorted(subtype_counts.items(), key=lambda kv: -kv[1]):
        print(f"  {k}: {v}")

    # =========================================================================
    # Write augmented JSONL
    # =========================================================================
    all_quotes = existing + new_quotes
    with open(PROC / "persona_quotes.jsonl", "w", encoding="utf-8") as f:
        for q in all_quotes:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")
    print(f"\nWrote {len(all_quotes)} total quotes to persona_quotes.jsonl")

    # =========================================================================
    # Regenerate phase4a_quote_bank.md
    # =========================================================================
    write_bank(all_quotes)


# ---------------------------------------------------------------------------
# Bank report writer (supersedes the original in 04a_quote_mining.py once
# supplementation has run)
# ---------------------------------------------------------------------------


# Target ordering for the report; speculator and sub-themes unchanged from 4A
SECTION_ORDER = [
    ("earnest_learner_combined", "Earnest Learner", "M2-C2 (M3-C0 supplement)", "persona"),
    ("speculator", "Speculator", "M2-C5", "persona"),
    ("cynical_reactive", "Cynical-Reactive", "M2-C1", "persona"),
    ("earnest_subtheme_tax", "Earnest sub-theme: tax/IR", "M1-C0", "sub_theme"),
    (
        "earnest_subtheme_property",
        "Earnest sub-theme: property/banking-debt",
        "M1-C1",
        "sub_theme",
    ),
]


def write_bank(all_quotes: list[dict]):
    # group quotes by display section
    by_section: dict[str, list[dict]] = defaultdict(list)
    for q in all_quotes:
        tk = q["target_key"]
        if tk in ("earnest_learner", "earnest_learner_supplement"):
            by_section["earnest_learner_combined"].append(q)
        else:
            by_section[tk].append(q)

    lines: list[str] = []
    lines.append("# Phase 4A — Persona Quote Bank (candidates)")
    lines.append("")
    lines.append("**Date:** 2026-05-21  ")
    lines.append(
        "**Status:** AWAITING SUPERVISOR FINAL SELECTION — Phase 4B persona narration BLOCKED"
    )
    lines.append("")
    lines.append(
        "**Revision history:**  \n"
        "- _v1.0 (initial):_ 375 candidate quotes from 147 threads across 5 targets.  \n"
        "- _v1.1 (supervisor carry-forwards):_ Earnest pool supplemented with M3-C0 "
        "medoid-nearest + M1-C3 ∩ M2-C2 ∩ M3-C0 triple, steered toward paralysis / "
        "sossego / self-doubt. Cynical-Reactive pool re-grouped by sub-type — "
        "`institutional_cynicism` (defining), `personal_crisis` (sparingly), "
        "`gambling_offtopic` (excluded from memo). Speculator and both sub-themes "
        "unchanged."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## How to read this file")
    lines.append("")
    lines.append(
        "Each section is one persona or sub-theme. Quotes are pulled VERBATIM "
        "from the original post body (not comments) of high-confidence cluster "
        "exemplars. Order: verbatim-matched first, then ranked by cluster-core "
        "proximity / quote length."
    )
    lines.append("")
    lines.append("**Each row carries:**")
    lines.append("")
    lines.append(
        "- `thread_id`, `subreddit`, `window` — provenance.  \n"
        "- `type` — quote function (posture / pain / system / paralysis / sossego / self_doubt / cynicism sub-type).  \n"
        "- **Portuguese text** — verbatim. Typos, slang, casing, abbreviations preserved.  \n"
        "- *English gloss* — orientation only; the memo uses the Portuguese with explanatory caption.  \n"
        "- ⚠ flags: `non-verbatim` (Haiku reached into comments — discard); `over-25w` (longer than the cap)."
    )
    lines.append("")
    lines.append(
        "**Hard rules for supervisor selection.** Discard any `⚠ non-verbatim` "
        "quote. For Cynical-Reactive, lead with `institutional_cynicism`; use "
        "`personal_crisis` quotes sparingly and respectfully; DO NOT pull from "
        "`gambling_offtopic` (corpus-edge). Aim for ~5 final quotes per persona "
        "spanning posture / pain / system."
    )
    lines.append("")

    # diagnostics
    lines.append("## Selection diagnostics")
    lines.append("")
    lines.append("| Section | candidate quotes | verbatim-OK | over-25w |")
    lines.append("|---------|-----------------:|------------:|---------:|")
    for sec_key, sec_label, sec_cluster, sec_kind in SECTION_ORDER:
        qs = by_section.get(sec_key, [])
        n = len(qs)
        n_ok = sum(1 for q in qs if q["verbatim_match"])
        n_long = sum(1 for q in qs if q["over_25_words"])
        lines.append(f"| {sec_label} ({sec_cluster}) | {n} | {n_ok} | {n_long} |")
    lines.append("")
    # cynic sub-type sub-table
    cynic_qs = by_section.get("cynical_reactive", [])
    if cynic_qs:
        lines.append("**Cynical-Reactive sub-type breakdown:**")
        lines.append("")
        lines.append("| Sub-type | quotes | verbatim-OK | use in memo? |")
        lines.append("|----------|-------:|------------:|--------------|")
        subtypes = ["institutional_cynicism", "personal_crisis", "gambling_offtopic", "other"]
        use_label = {
            "institutional_cynicism": "lead — defining posture",
            "personal_crisis": "sparingly + respectfully",
            "gambling_offtopic": "EXCLUDE — corpus-edge",
            "other": "case-by-case",
        }
        for st in subtypes:
            qs = [q for q in cynic_qs if q.get("cynic_subtype") == st]
            n = len(qs)
            n_ok = sum(1 for q in qs if q["verbatim_match"])
            if n:
                lines.append(f"| `{st}` | {n} | {n_ok} | {use_label[st]} |")
        lines.append("")
    lines.append("---")
    lines.append("")

    for sec_key, sec_label, sec_cluster, sec_kind in SECTION_ORDER:
        qs = by_section.get(sec_key, [])
        if not qs:
            continue
        lines.append(f"## {sec_label} — `{sec_cluster}` ({sec_kind})")
        lines.append("")

        if sec_key == "earnest_learner_combined":
            _render_earnest(qs, lines)
        elif sec_key == "cynical_reactive":
            _render_cynic(qs, lines)
        else:
            _render_generic(qs, lines)

        lines.append("---")
        lines.append("")

    lines.append("## ⛔ HARD STOP")
    lines.append("")
    lines.append(
        "Phase 4A v1.1 is a supervisor-revised quote bank. Phase 4B (persona "
        "narration) BLOCKED until the supervisor selects the final ~5 quotes "
        "per persona. Do NOT begin persona names, narratives, or memo drafting "
        "before the selection arrives."
    )
    lines.append("")

    (REPORTS / "phase4a_quote_bank.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORTS / 'phase4a_quote_bank.md'}")


def _rank_key(q: dict) -> tuple:
    return (
        not q.get("verbatim_match", False),
        q.get("over_25_words", False),
        q.get("word_count", 99),
    )


def _render_quote(q: dict, lines: list[str], type_tag: str | None = None):
    flags = []
    if not q.get("verbatim_match"):
        flags.append("⚠ non-verbatim")
    if q.get("over_25_words"):
        flags.append("⚠ over-25w")
    flag_str = f" — {' / '.join(flags)}" if flags else ""
    src = q.get("source_pool")
    src_str = f", pool={src}" if src else ""
    type_str = f", type=`{q['type']}`" if type_tag is None else f", type=`{type_tag}`"
    lines.append(
        f"- **`{q['thread_id']}`** ({q['subreddit']}, window {q['window']}{src_str}{type_str}){flag_str}  "
    )
    lines.append(f"  > {q['text_pt']}  ")
    if q.get("gloss_en"):
        lines.append(f"  *{q['gloss_en']}*  ")
    lines.append("")


def _render_earnest(qs: list[dict], lines: list[str]):
    n_total = len(qs)
    n_supp = sum(1 for q in qs if q["target_key"] == "earnest_learner_supplement")
    lines.append(
        f"_{n_total} total candidate quotes (orig {n_total - n_supp} + supplement {n_supp}). "
        f"Supplement priorities: **paralysis**, **sossego**, **self_doubt** — surfacing first._"
    )
    lines.append("")

    priority_types = ["paralysis", "sossego", "self_doubt"]
    other_types = ["pain", "posture", "system"]
    headings = {
        "paralysis": "decision paralysis (PRIORITY — supplement target)",
        "sossego": "sossego / peace-of-mind craving (PRIORITY — supplement target)",
        "self_doubt": "self-doubt / 'estou fazendo certo?' (PRIORITY — supplement target)",
        "posture": "posture (other)",
        "pain": "pain (other)",
        "system": "system (other)",
    }
    cap_per_block = {
        "paralysis": 8,
        "sossego": 5,
        "self_doubt": 5,
        "posture": 6,
        "pain": 6,
        "system": 4,
    }
    for tp in priority_types + other_types:
        group = sorted([q for q in qs if q.get("type") == tp], key=_rank_key)
        if not group:
            continue
        lines.append(f"### {headings[tp]}")
        lines.append("")
        for q in group[: cap_per_block[tp]]:
            _render_quote(q, lines)


def _render_cynic(qs: list[dict], lines: list[str]):
    by_subtype: dict[str, list[dict]] = defaultdict(list)
    for q in qs:
        st = q.get("cynic_subtype", "other")
        by_subtype[st].append(q)

    subtype_labels = {
        "institutional_cynicism": (
            "institutional / guru cynicism (LEAD — this is the defining posture)"
        ),
        "personal_crisis": (
            "personal financial crisis / family tragedy (use SPARINGLY and respectfully — dramatic tail, not center)"
        ),
        "gambling_offtopic": (
            "gambling / off-topic (EXCLUDED from memo candidates — corpus-edge, not persona-core)"
        ),
        "other": ("other / ambiguous"),
    }
    cap_per_subtype = {
        "institutional_cynicism": 14,
        "personal_crisis": 6,
        "gambling_offtopic": 5,
        "other": 4,
    }
    for st in ["institutional_cynicism", "personal_crisis", "gambling_offtopic", "other"]:
        group = sorted(by_subtype.get(st, []), key=_rank_key)
        if not group:
            continue
        lines.append(f"### {subtype_labels[st]}")
        lines.append("")
        for q in group[: cap_per_subtype[st]]:
            # show rationale only on ambiguous classifications
            _render_quote(q, lines)
            if st == "other" and q.get("cynic_subtype_rationale_en"):
                lines.append(f"  _(classifier note: {q['cynic_subtype_rationale_en']})_  ")
                lines.append("")


def _render_generic(qs: list[dict], lines: list[str]):
    n_total = len(qs)
    lines.append(f"_{n_total} total candidate quotes; showing top 20 after ranking._")
    lines.append("")
    qs_sorted = sorted(qs, key=_rank_key)[:20]
    for qtype in ("posture", "pain", "system"):
        group = [q for q in qs_sorted if q.get("type") == qtype]
        if not group:
            continue
        lines.append(f"### {qtype}")
        lines.append("")
        for q in group:
            _render_quote(q, lines)
    # other types (defensive)
    other = [
        q for q in qs_sorted if q.get("type") not in ("posture", "pain", "system")
    ]
    if other:
        lines.append("### other (unknown type — supervisor review)")
        lines.append("")
        for q in other:
            _render_quote(q, lines)


if __name__ == "__main__":
    asyncio.run(main())

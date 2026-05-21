#!/usr/bin/env python3
"""
Phase 4A — Quote mining for persona grounding.

For each of the three personas (M2 canonical clusters) plus the two earnest-
learner sub-themes (M1 topical clusters), pull the 30 most representative
exemplars and ask Haiku to extract up to 3 verbatim quotes per thread.

Outputs:
- data/processed/persona_quotes.jsonl  — every candidate quote with cluster tags
- reports/phase4a_quote_bank.md        — 15-20 candidate quotes per cluster
- prompts/04a_quote_extraction.md      — versioned prompt (already exists)

HARD STOP after writing. Supervisor selects the final quotes.
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
PROMPTS = ROOT / "prompts"
REPORTS = ROOT / "reports"

sys.path.insert(0, str(ROOT))
from src.llm_client import async_call  # noqa: E402

SEED = 42
N_PER_CLUSTER = 30
CONFIANCA_MIN = 3
UNIT_TEXT_CAP_CHARS = 8000     # safety cap; most threads <2k
CONCURRENCY = 8                # parallel Haiku calls
MODEL = "claude-haiku-4-5-20251001"
TEMP = 0.1
MAX_TOK = 600
PHASE = "4A"
TASK = "quote_extraction"

# canonical persona / sub-theme registry
TARGETS = [
    {
        "key": "earnest_learner",
        "label": "Earnest Learner",
        "method": "M2",
        "cluster_label": "M2-C2",
        "selection": "dist_to_medoid",  # ascending
        "kind": "persona",
    },
    {
        "key": "speculator",
        "label": "Speculator",
        "method": "M2",
        "cluster_label": "M2-C5",
        "selection": "dist_to_medoid",
        "kind": "persona",
    },
    {
        "key": "cynical_reactive",
        "label": "Cynical-Reactive",
        "method": "M2",
        "cluster_label": "M2-C1",
        "selection": "dist_to_medoid",
        "kind": "persona",
    },
    {
        "key": "earnest_subtheme_tax",
        "label": "Earnest sub-theme: tax/IR",
        "method": "M1",
        "cluster_label": "M1-C0",
        "selection": "membership_prob",  # descending
        "kind": "sub_theme",
    },
    {
        "key": "earnest_subtheme_property",
        "label": "Earnest sub-theme: property/banking-debt",
        "method": "M1",
        "cluster_label": "M1-C1",
        "selection": "membership_prob",
        "kind": "sub_theme",
    },
]


# ---------------------------------------------------------------------------
# Selection
# ---------------------------------------------------------------------------


def load_prompt() -> tuple[str, str]:
    """Return (system_prompt, user_template)."""
    raw = (PROMPTS / "04a_quote_extraction.md").read_text()
    # Pull system prompt (between '## System prompt' and '---' separator).
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
        raise RuntimeError("Could not parse prompts/04a_quote_extraction.md")
    return sys_match.group(1).strip(), user_match.group(1).strip()


def build_selection() -> pd.DataFrame:
    """
    For each target, select N_PER_CLUSTER threads with confianca>=3, ordered
    by the per-target selection criterion. Returns one row per (target, thread).
    """
    m1 = pd.read_parquet(PROC / "clusters_method1.parquet")
    m2 = pd.read_parquet(PROC / "clusters_method2.parquet")
    attr = pd.read_parquet(PROC / "extracted_attributes.parquet")[
        ["thread_id", "confianca_extracao", "subreddit_origem", "window"]
    ]

    # working_sample has the raw unit_text — keyed by thread_id
    working = pd.read_json(PROC / "working_sample.jsonl", lines=True)[
        ["thread_id", "unit_text"]
    ]

    rows: list[dict] = []
    for t in TARGETS:
        if t["method"] == "M2":
            # M2-C2 has 203 threads tied at dist=0 (categorical attribute
            # fingerprint matches the medoid exactly). Break ties by silhouette
            # desc (more distinctly THIS cluster than its neighbours), then
            # confianca desc, then thread_id asc for full reproducibility.
            base = m2.merge(attr, on="thread_id", how="left").merge(
                working, on="thread_id", how="left"
            )
            sub = base[
                (base.cluster_label == t["cluster_label"])
                & (base.confianca_extracao >= CONFIANCA_MIN)
                & base.unit_text.notna()
            ].sort_values(
                ["dist_to_medoid", "silhouette_sample", "confianca_extracao", "thread_id"],
                ascending=[True, False, False, True],
            )
        else:  # M1
            # M1-C0/C1 have many threads tied at membership_prob=1.0; break by
            # confianca desc then thread_id asc.
            base = m1.merge(attr, on="thread_id", how="left").merge(
                working, on="thread_id", how="left"
            )
            sub = base[
                (base.cluster_label == t["cluster_label"])
                & (base.confianca_extracao >= CONFIANCA_MIN)
                & base.unit_text.notna()
            ].sort_values(
                ["membership_prob", "confianca_extracao", "thread_id"],
                ascending=[False, False, True],
            )
        sub = sub.head(N_PER_CLUSTER)
        for _, r in sub.iterrows():
            rows.append(
                {
                    "target_key": t["key"],
                    "target_label": t["label"],
                    "target_kind": t["kind"],
                    "method": t["method"],
                    "cluster_label": t["cluster_label"],
                    "thread_id": r.thread_id,
                    "subreddit": r.subreddit_origem,
                    "window": r.window,
                    "confianca_extracao": int(r.confianca_extracao),
                    "selection_score": float(
                        r.dist_to_medoid if t["method"] == "M2" else r.membership_prob
                    ),
                    "unit_text": r.unit_text,
                }
            )

    selection = pd.DataFrame(rows)
    print(
        f"Selection: {len(selection)} (target, thread) pairs across "
        f"{selection.thread_id.nunique()} unique threads"
    )
    return selection


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------


def truncate_text(s: str) -> str:
    if len(s) <= UNIT_TEXT_CAP_CHARS:
        return s
    # cap but preserve the post body (which is at the top)
    return s[:UNIT_TEXT_CAP_CHARS] + "\n[...texto truncado para extração...]"


async def extract_one(
    semaphore: asyncio.Semaphore,
    system_prompt: str,
    user_template: str,
    thread_id: str,
    unit_text: str,
) -> dict:
    user_text = user_template.format(unit_text=truncate_text(unit_text))
    async with semaphore:
        result = await async_call(
            system=system_prompt,
            user_text=user_text,
            model=MODEL,
            temperature=TEMP,
            max_tokens=MAX_TOK,
            phase=PHASE,
            task=TASK,
            notes=f"thread={thread_id}",
            use_prompt_cache=True,
        )
    return {"thread_id": thread_id, "raw_response": result["text"], "from_cache": result["from_cache"]}


def parse_quotes(raw: str) -> list[dict]:
    """Robust JSON extraction (model occasionally wraps in fences)."""
    s = raw.strip()
    # strip code fences
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*", "", s)
        s = re.sub(r"\s*```\s*$", "", s)
    try:
        obj = json.loads(s)
    except json.JSONDecodeError:
        # try to recover an object substring
        m = re.search(r"\{.*\}", s, re.DOTALL)
        if not m:
            return []
        try:
            obj = json.loads(m.group(0))
        except json.JSONDecodeError:
            return []
    if isinstance(obj, dict) and isinstance(obj.get("quotes"), list):
        return obj["quotes"]
    return []


def post_block_only(unit_text: str) -> str:
    """Original-post block only (before the '--- Top comments ---' marker)."""
    return unit_text.split("--- Top comments ---", 1)[0]


def verbatim_check(quote_text: str, post_block: str) -> bool:
    """
    Whitespace-tolerant substring check. We collapse runs of whitespace on both
    sides so that the model's normalisation of inline whitespace doesn't trigger
    false negatives — but otherwise we require an exact match (preserves typos,
    case, accents, punctuation).
    """
    norm = lambda s: re.sub(r"\s+", " ", s).strip()
    return norm(quote_text) in norm(post_block)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def run():
    system_prompt, user_template = load_prompt()
    selection = build_selection()

    # extract once per unique thread; tags come from the selection rows
    unique_threads = (
        selection[["thread_id", "unit_text"]]
        .drop_duplicates("thread_id")
        .reset_index(drop=True)
    )
    print(f"Calling Haiku for {len(unique_threads)} unique threads...")

    sem = asyncio.Semaphore(CONCURRENCY)
    tasks = [
        extract_one(sem, system_prompt, user_template, r.thread_id, r.unit_text)
        for r in unique_threads.itertuples()
    ]
    raw_results = await asyncio.gather(*tasks)

    cache_hits = sum(1 for r in raw_results if r["from_cache"])
    print(f"Cache hits: {cache_hits}/{len(raw_results)}")

    # Build quote records: cross unique extractions with the (possibly multiple)
    # cluster tags each thread received in the selection.
    by_thread = {r["thread_id"]: r["raw_response"] for r in raw_results}
    quotes_out: list[dict] = []
    for _, r in selection.iterrows():
        raw = by_thread.get(r.thread_id, "")
        quotes = parse_quotes(raw)
        post_block = post_block_only(r.unit_text)
        for q in quotes:
            text = q.get("text", "").strip()
            qtype = q.get("type", "").strip()
            gloss = q.get("gloss_en", "").strip()
            if not text:
                continue
            word_count = len(text.split())
            quotes_out.append(
                {
                    "target_key": r.target_key,
                    "target_label": r.target_label,
                    "target_kind": r.target_kind,
                    "method": r.method,
                    "cluster_label": r.cluster_label,
                    "thread_id": r.thread_id,
                    "subreddit": r.subreddit,
                    "window": r.window,
                    "selection_score": r.selection_score,
                    "type": qtype,
                    "text_pt": text,
                    "gloss_en": gloss,
                    "word_count": word_count,
                    "verbatim_match": verbatim_check(text, post_block),
                    "over_25_words": word_count > 25,
                }
            )

    # Write JSONL
    out_jsonl = PROC / "persona_quotes.jsonl"
    with open(out_jsonl, "w", encoding="utf-8") as f:
        for q in quotes_out:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")
    print(f"Wrote {len(quotes_out)} candidate quotes to {out_jsonl}")

    # Diagnostics
    diag: dict[str, dict] = defaultdict(lambda: {"n_threads": 0, "n_quotes": 0, "verbatim_ok": 0, "over_25": 0})
    for q in quotes_out:
        d = diag[q["target_key"]]
        d["n_quotes"] += 1
        if q["verbatim_match"]:
            d["verbatim_ok"] += 1
        if q["over_25_words"]:
            d["over_25"] += 1
    for tk in {q["target_key"] for q in quotes_out}:
        diag[tk]["n_threads"] = (
            selection[selection.target_key == tk].thread_id.nunique()
        )

    print("\nDiagnostics per target:")
    for t in TARGETS:
        d = diag[t["key"]]
        if d["n_quotes"]:
            pct_ok = d["verbatim_ok"] / d["n_quotes"] * 100
        else:
            pct_ok = 0.0
        print(
            f"  {t['key']}: threads={d['n_threads']}, quotes={d['n_quotes']}, "
            f"verbatim_ok={d['verbatim_ok']} ({pct_ok:.0f}%), "
            f"over_25w={d['over_25']}"
        )

    # Markdown report
    write_quote_bank(quotes_out, selection)


def write_quote_bank(quotes_out: list[dict], selection: pd.DataFrame):
    by_target: dict[str, list[dict]] = defaultdict(list)
    for q in quotes_out:
        by_target[q["target_key"]].append(q)

    # rank quotes within each target: verbatim match first, then lower
    # selection_score (closer to medoid / higher membership), then shorter
    def rank_key(q):
        return (
            not q["verbatim_match"],   # True (=non-verbatim) sorts last
            q["over_25_words"],
            q["selection_score"]
            if q["method"] == "M2"
            else -q["selection_score"],
            q["word_count"],
        )

    lines: list[str] = []
    lines.append("# Phase 4A — Persona Quote Bank (candidates)")
    lines.append("")
    lines.append("**Date:** 2026-05-21  ")
    lines.append("**Status:** AWAITING SUPERVISOR SELECTION — Phase 4B persona narration is BLOCKED")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## How to read this file")
    lines.append("")
    lines.append(
        "Each section is one persona or sub-theme. Per section I show up to 20 "
        "candidate quotes that Haiku 4.5 pulled VERBATIM from the post body of "
        "the 30 closest-to-medoid threads (M2) or 30 highest-membership_prob "
        "threads (M1), filtered to `confianca_extracao ≥ 3`. Order: verbatim-"
        "matched first, then ranked by closeness to medoid / cluster core."
    )
    lines.append("")
    lines.append("**Each row carries:**")
    lines.append("")
    lines.append(
        "- `thread_id` — link the quote back to the original post.\n"
        "- `subreddit` / `window` — provenance.\n"
        "- `type` — `posture` (emotional stance), `pain` (concrete frustration), "
        "or `system` (relation to financial system / institutions / community).\n"
        "- **Portuguese text** — verbatim. Typos, slang, casing, and abbreviations "
        "are preserved on purpose. A sanitised paraphrase would lose the signal.\n"
        "- *English gloss* — one-line summary; never use this in the memo, use "
        "the Portuguese with an explanatory caption.\n"
        "- ⚠ flags: `non-verbatim` (Haiku rewrote or hallucinated — flagged but "
        "kept for transparency); `over-25w` (longer than the 25-word cap)."
    )
    lines.append("")
    lines.append(
        "**Hard rule for the supervisor selection step.** Discard any quote "
        "flagged `non-verbatim`. Treat `over-25w` as low-priority but not "
        "auto-reject. Aim for ~5 final quotes per persona spanning posture / "
        "pain / system."
    )
    lines.append("")

    lines.append("## Selection diagnostics")
    lines.append("")
    lines.append("| Target | threads | candidate quotes | verbatim-OK | over-25w |")
    lines.append("|--------|--------:|-----------------:|------------:|---------:|")
    for t in TARGETS:
        qs = by_target.get(t["key"], [])
        n_threads = selection[selection.target_key == t["key"]].thread_id.nunique()
        n_q = len(qs)
        n_ok = sum(1 for q in qs if q["verbatim_match"])
        n_long = sum(1 for q in qs if q["over_25_words"])
        lines.append(
            f"| {t['label']} ({t['cluster_label']}) | {n_threads} | {n_q} | "
            f"{n_ok} | {n_long} |"
        )
    lines.append("")

    lines.append("---")
    lines.append("")

    for t in TARGETS:
        qs = by_target.get(t["key"], [])
        qs_sorted = sorted(qs, key=rank_key)[:20]  # cap at 20 per target
        lines.append(f"## {t['label']} — `{t['cluster_label']}` ({t['kind']})")
        lines.append("")
        n_total = len(qs)
        lines.append(
            f"_{n_total} total candidate quotes from this cluster; showing top {len(qs_sorted)} after ranking._"
        )
        lines.append("")
        # group by type for skimming
        for qtype in ("posture", "pain", "system"):
            group = [q for q in qs_sorted if q["type"] == qtype]
            if not group:
                continue
            lines.append(f"### {qtype}")
            lines.append("")
            for q in group:
                flags = []
                if not q["verbatim_match"]:
                    flags.append("⚠ non-verbatim")
                if q["over_25_words"]:
                    flags.append("⚠ over-25w")
                flag_str = f" — {' / '.join(flags)}" if flags else ""
                lines.append(
                    f"- **`{q['thread_id']}`** "
                    f"({q['subreddit']}, window {q['window']}){flag_str}  "
                )
                lines.append(f"  > {q['text_pt']}  ")
                lines.append(f"  *{q['gloss_en']}*  ")
                lines.append("")
        # Also include any "other" type (in case model invents a category)
        other = [q for q in qs_sorted if q["type"] not in ("posture", "pain", "system")]
        if other:
            lines.append("### other (unknown type — supervisor review)")
            lines.append("")
            for q in other:
                lines.append(
                    f"- **`{q['thread_id']}`** "
                    f"({q['subreddit']}, window {q['window']}, type={q['type']!r})  "
                )
                lines.append(f"  > {q['text_pt']}  ")
                lines.append(f"  *{q['gloss_en']}*  ")
                lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("## ⛔ HARD STOP")
    lines.append("")
    lines.append(
        "Phase 4A is a quote bank, not a persona narration. Do NOT begin persona "
        "naming, persona narratives, or memo drafting until the supervisor has "
        "selected the final ~5 quotes per persona."
    )
    lines.append("")

    out_md = REPORTS / "phase4a_quote_bank.md"
    out_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_md}")


if __name__ == "__main__":
    asyncio.run(run())

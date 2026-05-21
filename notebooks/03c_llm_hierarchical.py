#!/usr/bin/env python3
"""
Phase 3C: Method 3 — LLM-Hierarchical Clustering (comparison instrument)

Run modes:

  python notebooks/03c_llm_hierarchical.py
      → Task 1: summarise all 3,600 threads with Haiku.
        Saves data/interim/phase3c_summaries.jsonl and
        reports/phase3c_summary_sample.md, then HARD STOPS.

  python notebooks/03c_llm_hierarchical.py --repair-failures
      → Reads failed records, loads their full cached API responses,
        applies JSON-quote repair, and appends fixed records to summaries.jsonl.
        Zero API cost. Run before --cluster if there are parse errors.

  python notebooks/03c_llm_hierarchical.py --cluster
      → Task 2 EXPLORE: embed summaries → k-medoids for k=4..7 →
        silhouette scores + fingerprints → HARD STOP for supervisor k-selection.
        Does NOT run adjudication; that waits for k to be chosen.

  python notebooks/03c_llm_hierarchical.py --finalize <k>
      → Task 2 FINALIZE: re-run k-medoids at supervisor-selected k,
        bootstrap stability, adjudication, cross-tabs, parquet output, full report.

NOTE: HDBSCAN+UMAP pipeline was abandoned. Raw 768-D mpnet space has no density
structure (HDBSCAN finds 0 clusters / 100% noise at min_samples≥15). UMAP collapsed
data into an equilateral-triangle topology artifact (ARI=1.0, 0 noise).
k-medoids (PAM) on cosine distance is used instead to partition the continuum at
a supervisor-chosen k. See reports/decisions_log.md for the full entry.
"""

import asyncio
import json
import re
import random
import sys
import warnings
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import adjusted_rand_score

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import llm_client

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE       = Path(__file__).resolve().parent.parent
DATA_PROC  = BASE / "data" / "processed"
DATA_INT   = BASE / "data" / "interim"
REPORTS    = BASE / "reports"
FIGURES    = REPORTS / "figures"
PROMPTS    = BASE / "prompts"
FIGURES.mkdir(parents=True, exist_ok=True)

SAMPLE_OUT     = DATA_INT / "phase3c_summaries.jsonl"
CLUSTERS_OUT   = DATA_PROC / "clusters_method3.parquet"
REPORT_SAMPLE  = REPORTS / "phase3c_summary_sample.md"
REPORT_CLUSTER = REPORTS / "phase3c_method3.md"

EMB_CACHE    = DATA_INT / "m3_emb_mpnet.npy"
UMAP2D_CACHE = DATA_INT / "m3_umap_2d.npy"

# ── Constants ─────────────────────────────────────────────────────────────────
SEED           = 42
N_TOTAL        = 3600
MIN_SIZE       = int(N_TOTAL * 0.03)   # 108 — 3% floor
SAMPLE_N       = 20
MODEL          = "claude-haiku-4-5-20251001"
TEMPERATURE    = 0.1
MAX_TOKENS     = 800
MAX_TOKENS_RETRY = 1000
RETRY_SALT     = "retry1"
RETRY_SALT_2   = "retry2"  # for --retry-failures with modified prompt

K_CANDIDATES   = [4, 5, 6, 7]
N_RESTARTS     = 5     # k-medoids restarts per k
MAX_ITER_PAM   = 100
BOOT_B         = 20
BOOT_FRAC      = 0.80
EXEMPLARS_N    = 10
SNIPPET_CHARS  = 300

EMBED_MODEL    = "paraphrase-multilingual-mpnet-base-v2"

SUMMARY_FIELDS = [
    "perfil_em_uma_frase", "situacao_financeira", "postura_emocional",
    "relacao_com_o_sistema", "o_que_ela_realmente_quer",
    "dor_principal", "sinal_distintivo",
]
EMBED_FIELDS   = ["perfil_em_uma_frase", "postura_emocional", "sinal_distintivo"]

ORDINAL_FEATURES = [
    "sofisticacao_tecnica", "tolerancia_risco_declarada_ou_inferida",
    "ceticismo_institucional", "exposicao_a_cripto_e_especulacao",
    "identidade_comunitaria",
]
CATEGORICAL_FEATURES = [
    "fase_acumulacao", "estrategia_principal",
    "relacao_com_instituicoes_financeiras", "estado_emocional_predominante",
    "objetivo_financeiro_primario",
]


def log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Shared helpers
# ═══════════════════════════════════════════════════════════════════════════════

def load_prompt() -> tuple[str, str]:
    text = (PROMPTS / "04_thread_summary.md").read_text()
    parts = text.split("--- USER ---")
    system = parts[0].replace("--- SYSTEM ---", "").strip()
    user_tpl = parts[1].strip()
    return system, user_tpl


def load_threads() -> list[dict]:
    threads = []
    with open(DATA_PROC / "working_sample.jsonl") as f:
        for line in f:
            threads.append(json.loads(line))
    return threads


def load_existing_summaries() -> dict[str, dict]:
    """Returns {thread_id: latest_ok_summary_dict} for successfully-parsed threads."""
    if not SAMPLE_OUT.exists():
        return {}
    done = {}
    with open(SAMPLE_OUT) as f:
        for line in f:
            rec = json.loads(line)
            if not rec.get("parse_error"):
                done[rec["thread_id"]] = rec  # later records override earlier ones
    return done


def load_failed_ids() -> set[str]:
    """Returns thread_ids that have a parse_error record and no later successful record."""
    if not SAMPLE_OUT.exists():
        return set()
    has_ok  = set()
    has_err = set()
    with open(SAMPLE_OUT) as f:
        for line in f:
            rec = json.loads(line)
            if rec.get("parse_error"):
                has_err.add(rec["thread_id"])
            else:
                has_ok.add(rec["thread_id"])
    return has_err - has_ok


# ═══════════════════════════════════════════════════════════════════════════════
# Task 1 — Summarise all threads
# ═══════════════════════════════════════════════════════════════════════════════

def _repair_unescaped_quotes(text: str) -> str:
    """
    State-machine repair: escape unescaped double-quotes inside JSON string values.

    Walks char-by-char. When inside a JSON string, a closing `"` is recognised by
    what follows it: `,`, `}`, `]`, `:`, or another `"` (the latter would be
    closing then opening the next string). Anything else → unescaped internal quote
    → emit `\"` instead.

    Handles `\\` escapes correctly (a `"` after `\\` is already escaped, skip it).
    """
    result  = []
    i       = 0
    n       = len(text)
    in_str  = False
    skip    = False

    while i < n:
        ch = text[i]

        if skip:
            result.append(ch)
            skip = False
            i += 1
            continue

        if ch == '\\' and in_str:
            result.append(ch)
            skip = True  # next char is escaped; pass through
            i += 1
            continue

        if ch == '"':
            if not in_str:
                in_str = True
                result.append(ch)
            else:
                # Determine if this closes the string or is an internal quote.
                # Peek past optional whitespace to find the next significant char.
                j = i + 1
                while j < n and text[j] in ' \t\n\r':
                    j += 1
                next_sig = text[j] if j < n else ''
                if next_sig in (',', '}', ']', ':', '"', ''):
                    in_str = False
                    result.append(ch)
                else:
                    result.append('\\')
                    result.append(ch)
        else:
            result.append(ch)

        i += 1

    return ''.join(result)


def parse_summary(text: str) -> tuple[dict | None, str | None]:
    """
    Parse the Haiku JSON response.
    1. Strip markdown fences.
    2. Try direct json.loads.
    3. If that fails, try _repair_unescaped_quotes then json.loads again.
    Returns (summary_dict, None) on success, (None, error_msg) on failure.
    """
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(
            l for l in lines if not l.startswith("```")
        ).strip()

    # First try direct parse
    try:
        d = json.loads(text)
        missing = [f for f in SUMMARY_FIELDS if f not in d]
        if missing:
            return None, f"missing_fields:{','.join(missing)}"
        return d, None
    except json.JSONDecodeError:
        pass

    # Repair pass: escape unescaped internal quotes
    repaired = _repair_unescaped_quotes(text)
    try:
        d = json.loads(repaired)
        missing = [f for f in SUMMARY_FIELDS if f not in d]
        if missing:
            return None, f"missing_fields:{','.join(missing)}"
        return d, None
    except json.JSONDecodeError as e:
        return None, f"json_error:{e}"


CONCURRENCY = 10   # max simultaneous Haiku requests


async def _summarise_async(threads: list[dict]) -> None:
    """
    Async inner loop: up to CONCURRENCY simultaneous requests.
    Previously-failed threads are retried with RETRY_SALT + MAX_TOKENS_RETRY.
    File writes and counters are protected by a shared asyncio.Lock.
    """
    system, user_tpl = load_prompt()
    existing   = load_existing_summaries()
    failed_ids = load_failed_ids()
    log(f"Already summarised (ok): {len(existing)}/{N_TOTAL}")
    log(f"Previously failed (will retry at {MAX_TOKENS_RETRY} tokens): {len(failed_ids)}")

    todo = [t for t in threads if t["thread_id"] not in existing]
    log(f"Remaining: {len(todo)} | concurrency cap: {CONCURRENCY}")

    if not todo:
        log("All summaries already generated — skipping API calls.")
        return

    sem      = asyncio.Semaphore(CONCURRENCY)
    file_lck = asyncio.Lock()
    counters = {"n_ok": len(existing), "n_err": 0, "cost": 0.0, "done": 0}
    parse_errors: list[dict] = []

    async def process(thread: dict) -> None:
        tid      = thread["thread_id"]
        is_retry = tid in failed_ids
        user_msg = user_tpl.replace("{unit_text}", thread["unit_text"])

        async with sem:
            result = await llm_client.async_call(
                system           = system,
                user_text        = user_msg,
                model            = MODEL,
                temperature      = TEMPERATURE,
                max_tokens       = MAX_TOKENS_RETRY if is_retry else MAX_TOKENS,
                phase            = "3C",
                task             = "thread_summary_retry" if is_retry else "thread_summary",
                notes            = f"tid={tid}",
                use_prompt_cache = True,
                salt             = RETRY_SALT if is_retry else "",
            )

        summary, err = parse_summary(result["text"])
        rec = {
            "thread_id":   tid,
            "subreddit":   thread["subreddit"],
            "window":      thread["window"],
            "from_cache":  result["from_cache"],
            "parse_error": err,
        }
        if summary:
            rec.update(summary)
        else:
            rec["raw_text"] = result["text"][:500]
            parse_errors.append({"thread_id": tid, "error": err})

        async with file_lck:
            with open(SAMPLE_OUT, "a") as out_f:
                out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            if summary:
                counters["n_ok"] += 1
            else:
                counters["n_err"] += 1
            if not result["from_cache"]:
                counters["cost"] += result["cost"]
            counters["done"] += 1
            done = counters["done"]
            if done % 100 == 0 or done == len(todo):
                log(f"  Progress: {done}/{len(todo)} | "
                    f"ok={counters['n_ok']} err={counters['n_err']} | "
                    f"cost so far=${counters['cost']:.4f}")

    await asyncio.gather(*[process(t) for t in todo])

    log(f"Summarisation complete: {counters['n_ok']} ok, {counters['n_err']} parse errors, "
        f"task-1 API cost=${counters['cost']:.4f}")
    if parse_errors:
        log(f"Parse errors (first 5): {parse_errors[:5]}")


def run_summarise(threads: list[dict]) -> None:
    asyncio.run(_summarise_async(threads))


def write_summary_sample() -> None:
    """Sample 20 summaries stratified by subreddit+window for supervisor review."""
    rng = random.Random(SEED)
    records = []
    with open(SAMPLE_OUT) as f:
        for line in f:
            rec = json.loads(line)
            if not rec.get("parse_error"):
                records.append(rec)

    log(f"Total usable summaries for sampling: {len(records)}")

    from collections import defaultdict
    groups = defaultdict(list)
    for r in records:
        groups[(r["subreddit"], r["window"])].append(r)

    sampled = []
    per_cell = max(1, SAMPLE_N // len(groups))
    for key, grp in sorted(groups.items()):
        sampled.extend(rng.sample(grp, min(per_cell, len(grp))))
    remaining = [r for r in records if r not in sampled]
    rng.shuffle(remaining)
    sampled.extend(remaining[:max(0, SAMPLE_N - len(sampled))])
    sampled = sampled[:SAMPLE_N]
    rng.shuffle(sampled)

    lines = [
        "# Phase 3C — Summary Sample (checkpoint for supervisor review)\n",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d')}  ",
        f"**Total summaries generated:** {len(records)}/{N_TOTAL}  ",
        "**Status: AWAITING SUPERVISOR REVIEW — do not proceed to --cluster**\n",
        "---\n",
        "Review these 20 summaries for quality before approving Task 2 (clustering).\n",
        "Check: Does the model capture WHO the person is (not just what they asked)?",
        "Does it distinguish irony from anxiety? Is `sinal_distintivo` specific?",
        "Is `desconhecido` used appropriately (not overused)?\n",
        "---\n",
    ]

    for idx, r in enumerate(sampled, 1):
        lines.append(f"### Sample {idx} — `{r['thread_id']}` "
                     f"(r/{r['subreddit']}, window {r['window']})\n")
        for field in SUMMARY_FIELDS:
            val = r.get(field, "—")
            lines.append(f"**{field}:** {val}  ")
        lines.append("\n---\n")

    REPORT_SAMPLE.write_text("\n".join(lines), encoding="utf-8")
    log(f"Summary sample written → {REPORT_SAMPLE}")


def task1_repair_failures() -> None:
    """
    Zero-API-cost repair pass.
    For each thread with a parse_error and no later valid record:
      1. Reconstruct the file-cache key (checking both salt="" and RETRY_SALT).
      2. Load the full cached API response.
      3. Apply parse_summary (which now includes the repair pass).
      4. If parseable, append a valid record to summaries.jsonl.
    Reports how many were fixed vs. still unrecoverable.
    """
    system, user_tpl = load_prompt()
    threads_by_id = {t["thread_id"]: t for t in load_threads()}

    failed_ids = load_failed_ids()
    log(f"Unique failed thread_ids to repair: {len(failed_ids)}")
    if not failed_ids:
        log("Nothing to repair.")
        return

    fixed = 0
    still_failed = []

    with open(SAMPLE_OUT, "a") as out_f:
        for tid in sorted(failed_ids):
            thread = threads_by_id.get(tid)
            if not thread:
                log(f"  {tid}: not found in working_sample.jsonl — skip")
                still_failed.append(tid)
                continue

            user_msg = user_tpl.replace("{unit_text}", thread["unit_text"])

            # Try both salts (first-pass and retry1)
            cached = None
            for salt in ("", RETRY_SALT):
                key    = llm_client._cache_key(MODEL, system, user_msg, salt=salt)
                cached = llm_client._load_cache(key)
                if cached:
                    break

            if not cached:
                log(f"  {tid}: no file-cache entry found — skip")
                still_failed.append(tid)
                continue

            summary, err = parse_summary(cached["text"])
            if summary:
                rec = {
                    "thread_id":   tid,
                    "subreddit":   thread["subreddit"],
                    "window":      thread["window"],
                    "from_cache":  True,
                    "parse_error": None,
                }
                rec.update(summary)
                out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                fixed += 1
            else:
                log(f"  {tid}: repair failed — {err}")
                still_failed.append(tid)

    log(f"Repair complete: {fixed} fixed, {len(still_failed)} still failed")
    if still_failed:
        log(f"  Still failed (dropping from corpus): {still_failed[:10]}")

    # Report updated count
    n_ok = len(load_existing_summaries())
    log(f"Total valid summaries now: {n_ok}/{N_TOTAL}")


def task1_summarise() -> None:
    log("=== Phase 3C Task 1: Thread Summarisation ===")
    threads = load_threads()
    run_summarise(threads)
    write_summary_sample()

    n_ok = n_err = 0
    with open(SAMPLE_OUT) as f:
        for line in f:
            rec = json.loads(line)
            if rec.get("parse_error"):
                n_err += 1
            else:
                n_ok += 1

    log("")
    log("═" * 60)
    log("TASK 1 COMPLETE — HARD STOP")
    log(f"  Summaries: {n_ok} ok, {n_err} parse error lines")
    log(f"  Output: {SAMPLE_OUT}")
    log(f"  Sample: {REPORT_SAMPLE}")
    log("")
    log("  Supervisor: review reports/phase3c_summary_sample.md")
    log("  If parse errors remain, run:")
    log("    python notebooks/03c_llm_hierarchical.py --repair-failures")
    log("  Then, to proceed to clustering:")
    log("    python notebooks/03c_llm_hierarchical.py --cluster")
    log("═" * 60)


# ═══════════════════════════════════════════════════════════════════════════════
# Non-financial content detection
# ═══════════════════════════════════════════════════════════════════════════════

_RE_SINAL_NONFINANCIAL = re.compile(
    r'não (?:é |um |demonstra )?investidor'
    r'|sem (?:perfil de )?investidor'
    r'|incluído no corpus'
    r'|não (?:investe|possui investimentos|demonstra interesse em investir)'
    r'|sem contexto (?:financeiro|de investimento|pessoal de investimento)',
    re.IGNORECASE | re.UNICODE,
)

_RE_QUER_NONFINANCIAL = re.compile(
    r'validação (?:social|de (?:escolha|comportamento|decisão))'
    r'|pertencimento (?:a grupo|à comunidade|ao grupo)'
    r'|reconhecimento (?:como|social|de)'
    r'|(?:validação|aprovação) de (?:um )?comportamento'
    r'|aceitação (?:social|do grupo|da comunidade)'
    r'|entreter|conteúdo (?:viral|absurdo|humorístico)'
    r'|parceiros? (?:sexuais?|românticos?)|sexo (?:sem|pago|fácil)'
    r'|matches? (?:no|do) tinder|tinder|aplicativo de (?:namoro|relacionamento)'
    r'|rejeição (?:romântica|sexual|no tinder)',
    re.IGNORECASE | re.UNICODE,
)

_RE_QUER_FINANCIAL = re.compile(
    r'invest|poupan|rendimento|retorno (?:financeiro|do capital|sobre)'
    r'|renda (?:passiva|fixa|variável)|patrimônio|carteira (?:de investimento)?'
    r'|ação|fii\b|cdb\b|tesouro|dividendo|cdi\b|capital (?:inicial|guardado|investido)'
    r'|aposentador|previdência|independência financeira|reserva de emergência'
    r'|aporte|diversificar|alocar|comprar (?:ativo|imóvel|ação|fundo)'
    r'|liberdade financeira|ganho financeiro',
    re.IGNORECASE | re.UNICODE,
)


def detect_nonfinancial(full_dicts: list[dict]) -> list[bool]:
    flags = []
    for rec in full_dicts:
        sinal = str(rec.get("sinal_distintivo", ""))
        quer  = str(rec.get("o_que_ela_realmente_quer", ""))
        by_sinal = bool(_RE_SINAL_NONFINANCIAL.search(sinal))
        by_quer  = (bool(_RE_QUER_NONFINANCIAL.search(quer))
                    and not bool(_RE_QUER_FINANCIAL.search(quer)))
        flags.append(by_sinal or by_quer)
    return flags


def nonfinancial_report(labels: np.ndarray, thread_ids: list[str],
                        subreddits: list[str],
                        is_nonfinancial: list[bool]) -> dict:
    nf    = np.array(is_nonfinancial, dtype=bool)
    total = len(labels)
    overall_rate = round(100 * nf.sum() / total, 1)

    sub_arr = np.array(subreddits)
    by_sub  = {}
    for sub in sorted(set(subreddits)):
        mask = sub_arr == sub
        rate = round(100 * nf[mask].sum() / mask.sum(), 1)
        by_sub[sub] = {"n": int(mask.sum()), "n_nf": int(nf[mask].sum()),
                       "rate_pct": rate}

    per_cluster = {}
    for c in sorted(set(labels)):
        mask  = labels == c
        n_c   = int(mask.sum())
        n_nf  = int(nf[mask].sum())
        rate  = round(100 * n_nf / n_c, 1) if n_c else 0.0
        label = f"M3-C{c}"
        per_cluster[label] = {
            "n": n_c, "n_nf": n_nf, "rate_pct": rate,
            "artifact_flag": rate > 40,
        }

    return {
        "overall_rate_pct": overall_rate,
        "n_total":          total,
        "n_nf_total":       int(nf.sum()),
        "by_subreddit":     by_sub,
        "per_cluster":      per_cluster,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Data loading for Task 2
# ═══════════════════════════════════════════════════════════════════════════════

def load_summaries() -> tuple[list[str], list[str], list[str], list[str], list[dict]]:
    """
    Load usable summaries (latest valid record per thread_id).
    Returns (thread_ids, subreddits, windows, embed_texts, full_dicts).
    """
    seen: dict[str, dict] = {}
    with open(SAMPLE_OUT) as f:
        for line in f:
            rec = json.loads(line)
            if not rec.get("parse_error"):
                seen[rec["thread_id"]] = rec  # later records override earlier

    tids, subreddits, windows, embed_txts, full_dicts = [], [], [], [], []
    for rec in seen.values():
        combined = " | ".join(
            str(rec.get(field, "desconhecido")) for field in EMBED_FIELDS
        )
        tids.append(rec["thread_id"])
        subreddits.append(rec["subreddit"])
        windows.append(rec["window"])
        embed_txts.append(combined)
        full_dicts.append(rec)
    return tids, subreddits, windows, embed_txts, full_dicts


def count_unique_failures() -> int:
    """Count thread_ids that have a parse_error and no valid record."""
    return len(load_failed_ids())


# ═══════════════════════════════════════════════════════════════════════════════
# Embedding
# ═══════════════════════════════════════════════════════════════════════════════

def embed_texts(texts: list[str]) -> np.ndarray:
    """Encode texts with mpnet (L2-normalised). Invalidates cache on count mismatch."""
    if EMB_CACHE.exists():
        cached_emb = np.load(EMB_CACHE)
        if cached_emb.shape[0] == len(texts):
            log(f"  Loading cached embeddings {cached_emb.shape}")
            return cached_emb
        log(f"  Cache stale ({cached_emb.shape[0]} vs {len(texts)}) — re-embedding")

    from sentence_transformers import SentenceTransformer
    log(f"  Loading model {EMBED_MODEL} …")
    model = SentenceTransformer(EMBED_MODEL)
    log(f"  Encoding {len(texts)} texts …")
    emb = model.encode(
        texts,
        batch_size=64,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    np.save(EMB_CACHE, emb)
    log(f"  Embeddings saved → {EMB_CACHE}  shape={emb.shape}")
    return emb


# ═══════════════════════════════════════════════════════════════════════════════
# UMAP — visualisation only (NOT used for clustering)
# ═══════════════════════════════════════════════════════════════════════════════

def umap_reduce_2d(emb: np.ndarray) -> np.ndarray:
    """2-D UMAP for scatter plots only. NOT used as clustering input."""
    if UMAP2D_CACHE.exists():
        cached = np.load(UMAP2D_CACHE)
        if cached.shape[0] == emb.shape[0]:
            log(f"  Loading cached 2-D UMAP {cached.shape}")
            return cached
        log("  2-D UMAP cache stale — re-computing")

    import umap as umap_lib
    log("  Computing 2-D UMAP for visualisation (this is cosmetic only) …")
    reducer = umap_lib.UMAP(
        n_components=2, metric="cosine",
        n_neighbors=15, min_dist=0.1,
        random_state=SEED, n_jobs=1,
    )
    reduced = reducer.fit_transform(emb)
    np.save(UMAP2D_CACHE, reduced)
    log(f"  2-D UMAP done → {UMAP2D_CACHE}")
    return reduced


# ═══════════════════════════════════════════════════════════════════════════════
# k-medoids (PAM) — vectorised implementation
# ═══════════════════════════════════════════════════════════════════════════════

def _kmedoids_single(dist_matrix: np.ndarray, k: int, seed: int) -> tuple[np.ndarray, list[int], float]:
    """
    Single-restart PAM k-medoids on a precomputed distance matrix.
    Returns (labels_0indexed, medoid_point_indices, total_cost).

    Vectorised SWAP phase: for each current medoid m_j, computes the cost
    change for every possible swap m_j → x_h in one matrix operation.
    Convergence is O(n² * k) per iteration, typically 5–20 iterations.
    """
    rng = np.random.default_rng(seed)
    n   = dist_matrix.shape[0]

    # k-medoids++ initialisation (distance-proportional seeding)
    first = int(rng.integers(n))
    medoids = [first]
    for _ in range(k - 1):
        min_d = dist_matrix[:, medoids].min(axis=1)
        prob  = min_d / (min_d.sum() + 1e-12)
        medoids.append(int(rng.choice(n, p=prob)))
    # Deduplicate and fill if needed
    medoids = list(dict.fromkeys(medoids))
    while len(medoids) < k:
        cand = int(rng.integers(n))
        if cand not in medoids:
            medoids.append(cand)
    medoids = sorted(medoids[:k])

    def assign(meds: list[int]):
        D       = dist_matrix[:, meds]          # (n, k) distances to medoids
        sorted2 = np.argsort(D, axis=1)[:, :2]
        labels  = sorted2[:, 0]                 # cluster index 0..k-1
        d1      = D[np.arange(n), sorted2[:, 0]]
        d2      = D[np.arange(n), sorted2[:, 1]] if k > 1 else np.full(n, np.inf)
        return labels, d1, d2, float(d1.sum())

    labels, d1, d2, cost = assign(medoids)
    medoid_set = set(medoids)

    for _it in range(MAX_ITER_PAM):
        best_gain = 1e-9
        best_swap = None

        # Compute once per sweep (non_med and d_to_h are constant across j within a sweep)
        non_med = np.array([i for i in range(n) if i not in medoid_set])
        d_to_h  = dist_matrix[np.ix_(np.arange(n), non_med)]  # (n, |H|)

        for j_idx, m_j in enumerate(medoids):
            in_j  = labels == j_idx        # bool mask: in cluster j
            out_j = ~in_j                  # bool mask: not in cluster j

            # In-cluster contribution: d1[i] - min(d_to_h[i], d2[i])
            in_gain = (d1[in_j, np.newaxis]
                       - np.minimum(d_to_h[in_j, :], d2[in_j, np.newaxis]))

            # Out-cluster contribution: max(0, d1[i] - d_to_h[i])
            out_gain = np.maximum(0.0, d1[out_j, np.newaxis] - d_to_h[out_j, :])

            total_gain = in_gain.sum(axis=0) + out_gain.sum(axis=0)   # (|H|,)
            best_h_local = int(total_gain.argmax())
            if total_gain[best_h_local] > best_gain:
                best_gain = float(total_gain[best_h_local])
                best_swap = (j_idx, int(non_med[best_h_local]))

        if best_swap is None:
            break

        j_idx, h = best_swap
        medoids[j_idx] = h
        medoid_set = set(medoids)
        labels, d1, d2, cost = assign(medoids)

    return labels, sorted(medoids), cost


def kmedoids(dist_matrix: np.ndarray, k: int,
             n_restarts: int = N_RESTARTS) -> tuple[np.ndarray, list[int], float]:
    """
    k-medoids with multiple random restarts. Returns best (lowest cost) result.
    """
    rng      = np.random.default_rng(SEED)
    best_labels, best_meds, best_cost = None, None, np.inf
    for r in range(n_restarts):
        seed = int(rng.integers(1 << 31))
        lbl, meds, cost = _kmedoids_single(dist_matrix, k, seed=seed)
        log(f"    restart {r+1}/{n_restarts}: cost={cost:.2f}")
        if cost < best_cost:
            best_labels, best_meds, best_cost = lbl, meds, cost
    return best_labels, best_meds, best_cost


def silhouette_cosine(labels: np.ndarray, cos_dist: np.ndarray) -> float:
    """Silhouette score using the precomputed cosine distance matrix."""
    from sklearn.metrics import silhouette_score
    # Silhouette is undefined for k=1 or all-same labels
    if len(set(labels)) < 2:
        return float('nan')
    return float(silhouette_score(cos_dist, labels, metric="precomputed"))


def bootstrap_stability_kmedoids(cos_dist: np.ndarray, orig_labels: np.ndarray,
                                  k: int) -> dict:
    """Bootstrap ARI stability for k-medoids (replaces HDBSCAN bootstrap)."""
    rng  = np.random.default_rng(SEED)
    n    = len(orig_labels)
    aris, cj = [], {c: [] for c in range(k)}

    for b in range(BOOT_B):
        sub = np.sort(rng.choice(n, size=int(n * BOOT_FRAC), replace=False))
        sub_dist = cos_dist[np.ix_(sub, sub)]
        boot_labels, _, _ = kmedoids(sub_dist, k, n_restarts=2)
        orig_s = orig_labels[sub]
        ari = adjusted_rand_score(orig_s, boot_labels)
        aris.append(ari)
        for c in range(k):
            orig_m = set(np.where(orig_s == c)[0])
            if not orig_m:
                continue
            best_j = 0.0
            for c2 in set(boot_labels):
                bm    = set(np.where(boot_labels == c2)[0])
                union = len(orig_m | bm)
                if union > 0:
                    best_j = max(best_j, len(orig_m & bm) / union)
            cj[c].append(best_j)
        log(f"  Bootstrap {b+1}/{BOOT_B}: ARI={ari:.3f}")

    return {
        "mean_ari": round(float(np.mean(aris)), 3),
        "std_ari":  round(float(np.std(aris)), 3),
        "per_cluster_jaccard": {
            c: round(float(np.mean(v)), 3) if v else 0.0
            for c, v in cj.items()
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Exemplars
# ═══════════════════════════════════════════════════════════════════════════════

def cluster_exemplars_kmedoids(emb: np.ndarray, labels: np.ndarray,
                                medoids: list[int],
                                full_dicts: list[dict]) -> dict:
    """
    For each cluster: medoid first, then nearest neighbours to the medoid,
    up to EXEMPLARS_N total.
    """
    exemplars = {}
    for j, m in enumerate(medoids):
        members = np.where(labels == j)[0]
        # Cosine distance from medoid to cluster members (emb is L2-normalised)
        sims  = emb[members] @ emb[m]
        dists = 1.0 - sims
        # Sort by distance, but ensure medoid is first
        order = np.argsort(dists)
        top_n = min(EXEMPLARS_N, len(members))
        top_idx = members[order[:top_n]]
        exemplars[j] = [
            {
                "thread_id":              full_dicts[i]["thread_id"],
                "cosine_dist_to_medoid":  round(float(1.0 - emb[i] @ emb[m]), 4),
                "is_medoid":              int(i) == m,
                "perfil":  str(full_dicts[i].get("perfil_em_uma_frase", ""))[:SNIPPET_CHARS],
                "postura": str(full_dicts[i].get("postura_emocional",   ""))[:SNIPPET_CHARS],
                "sinal":   str(full_dicts[i].get("sinal_distintivo",    ""))[:SNIPPET_CHARS],
                "dor":     str(full_dicts[i].get("dor_principal",       ""))[:SNIPPET_CHARS],
            }
            for i in top_idx
        ]
    return exemplars


# ═══════════════════════════════════════════════════════════════════════════════
# Missingness profiles (post-hoc, M2 attributes)
# ═══════════════════════════════════════════════════════════════════════════════

def missingness_profiles(labels: np.ndarray, thread_ids: list[str],
                         attr_df: pd.DataFrame) -> tuple[dict, float]:
    aligned = attr_df.set_index("thread_id")
    miss_counts = (
        aligned[CATEGORICAL_FEATURES].apply(
            lambda col: col == "desconhecido").sum(axis=1)
        + aligned[ORDINAL_FEATURES].isna().sum(axis=1)
    )
    corpus_median = miss_counts.median()
    profiles = {}
    for c in sorted(set(labels)):
        members = [thread_ids[i] for i in np.where(labels == c)[0]]
        sub     = miss_counts.reindex(members).dropna()
        mean_m  = round(float(sub.mean()), 2) if len(sub) else 0.0
        profiles[int(c)] = {
            "mean_missing": mean_m,
            "artifact_flag": mean_m > 1.5 * corpus_median,
        }
    return profiles, corpus_median


# ═══════════════════════════════════════════════════════════════════════════════
# Cross-tabs and adjudication (used in finalize only)
# ═══════════════════════════════════════════════════════════════════════════════

def build_crosstabs(labels: np.ndarray, thread_ids: list[str],
                    m2_df: pd.DataFrame,
                    m1_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    m2_map     = dict(zip(m2_df["thread_id"], m2_df["cluster_label"]))
    m1_map     = dict(zip(m1_df["thread_id"], m1_df["m1_label"]))
    m3_lbls    = [f"M3-C{c}" for c in labels]
    m2_aligned = [m2_map.get(tid, "M2-unknown") for tid in thread_ids]
    m1_aligned = [m1_map.get(tid, "M1-unknown") for tid in thread_ids]
    ct_m2 = pd.crosstab(pd.Categorical(m3_lbls), pd.Categorical(m2_aligned))
    ct_m1 = pd.crosstab(pd.Categorical(m3_lbls), pd.Categorical(m1_aligned))
    return ct_m2, ct_m1


def adjudication(labels: np.ndarray, thread_ids: list[str],
                 m2_df: pd.DataFrame, m1_df: pd.DataFrame) -> dict:
    """
    Five pre-specified adjudication tests (run in finalize only).
    M2 targets: M2-C1 (cynical-reactive), M2-C2 (earnest learner), M2-C5 (speculator).
    M1 signals: M1-C1 (property/banking/debt), M1-C0 (tax/IR).
    """
    from scipy.stats import entropy as scipy_entropy
    from collections import Counter

    m2_map = dict(zip(m2_df["thread_id"], m2_df["cluster_label"]))
    m1_map = dict(zip(m1_df["thread_id"], m1_df["m1_label"]))

    results = {}
    for test_name, ref_label, ref_map, base_rate_pct, concentrate_threshold in [
        ("M2-C1 (cynical-reactive — decisive test)", "M2-C1", m2_map, 30.0, 40),
        ("M2-C2 (earnest learner)",                  "M2-C2", m2_map, 47.6, 55),
        ("M2-C5 (speculator)",                       "M2-C5", m2_map, 18.4, 30),
        ("M1-C1 (property/banking/debt)",             "M1-C1", m1_map, 12.9, 25),
        ("M1-C0 (tax/IR)",                            "M1-C0", m1_map,  4.3, 15),
    ]:
        ref_tids  = {tid for tid, lbl in ref_map.items() if lbl == ref_label}
        m3_of_ref = [labels[i] for i, tid in enumerate(thread_ids) if tid in ref_tids]
        n_ref = len(m3_of_ref)
        if n_ref == 0:
            results[test_name] = {"n_ref": 0, "note": "no threads found"}
            continue

        dist        = Counter(m3_of_ref)
        top_m3, top_n = dist.most_common(1)[0]
        counts      = np.array([dist[c] for c in sorted(dist)])
        probs       = counts / counts.sum()
        ent         = float(scipy_entropy(probs, base=2))
        pct_in_top  = round(100 * top_n / n_ref, 1)
        concentrated = pct_in_top >= concentrate_threshold

        # Compute overrepresentation: cluster share vs. base rate
        n_total = len(labels)
        n_in_top_cluster = int((labels == top_m3).sum())
        cluster_share_pct = round(100 * n_in_top_cluster / n_total, 1)
        overrep = round(pct_in_top / cluster_share_pct, 2) if cluster_share_pct > 0 else None

        results[test_name] = {
            "n_ref":                 n_ref,
            "top_m3_cluster":        f"M3-C{top_m3}",
            "pct_in_top":            pct_in_top,
            "top_cluster_share_pct": cluster_share_pct,
            "overrepresentation":    overrep,
            "concentrate_threshold": concentrate_threshold,
            "concentrated":          concentrated,
            "entropy":               round(ent, 3),
            "base_rate_pct":         base_rate_pct,
            "distribution":          {f"M3-C{c}": int(v) for c, v in sorted(dist.items())},
        }
    return results


def compute_m3_m2_ari(labels: np.ndarray, thread_ids: list[str],
                      m2_df: pd.DataFrame) -> dict:
    """
    ARI between M3 partition and M2 partition on the threads that exist in both.
    Returns n_shared, ari, and per-M3-cluster modal M2 label.
    """
    m2_map   = dict(zip(m2_df["thread_id"], m2_df["cluster_label"]))
    shared_m3, shared_m2 = [], []
    for i, tid in enumerate(thread_ids):
        if tid in m2_map:
            shared_m3.append(int(labels[i]))
            shared_m2.append(m2_map[tid])

    n_shared = len(shared_m3)
    if n_shared < 2:
        return {"n_shared": n_shared, "ari": None}

    # Map M2 string labels to ints for ARI
    uniq_m2  = sorted(set(shared_m2))
    m2_int   = {lbl: idx for idx, lbl in enumerate(uniq_m2)}
    shared_m2_int = [m2_int[l] for l in shared_m2]

    ari = float(adjusted_rand_score(shared_m3, shared_m2_int))
    return {"n_shared": n_shared, "ari": round(ari, 4)}


def m3_cluster_correspondence(labels: np.ndarray, thread_ids: list[str],
                               k: int, m2_df: pd.DataFrame,
                               m1_df: pd.DataFrame) -> list[dict]:
    """
    For each M3 cluster: find the M2 and M1 clusters most overrepresented within it.
    Overrepresentation = (share of M2-Cx in M3-Cc) / (base rate of M2-Cx in corpus).
    This is the M3→M2/M1 direction of the adjudication: which M2 cluster does each
    M3 cluster most resemble?
    """
    m2_map = dict(zip(m2_df["thread_id"], m2_df["cluster_label"]))
    m1_map = dict(zip(m1_df["thread_id"], m1_df["m1_label"]))
    n_total = len(thread_ids)

    # Corpus base rates for each M2 and M1 cluster
    m2_all = [m2_map.get(tid, "M2-unknown") for tid in thread_ids]
    m1_all = [m1_map.get(tid, "M1-unknown") for tid in thread_ids]

    from collections import Counter
    m2_base = {k2: v / n_total for k2, v in Counter(m2_all).items()}
    m1_base = {k1: v / n_total for k1, v in Counter(m1_all).items()}

    correspondence = []
    for c in range(k):
        members_idx = np.where(labels == c)[0]
        n_c = len(members_idx)
        m2_in_c = [m2_all[i] for i in members_idx]
        m1_in_c = [m1_all[i] for i in members_idx]

        # M2 overrepresentation per cluster
        m2_overrep = {}
        for lbl, cnt in Counter(m2_in_c).items():
            share  = cnt / n_c
            base   = m2_base.get(lbl, 1e-6)
            m2_overrep[lbl] = round(share / base, 2)

        # M1 overrepresentation per cluster
        m1_overrep = {}
        for lbl, cnt in Counter(m1_in_c).items():
            share  = cnt / n_c
            base   = m1_base.get(lbl, 1e-6)
            m1_overrep[lbl] = round(share / base, 2)

        best_m2 = max(m2_overrep, key=m2_overrep.get) if m2_overrep else "—"
        best_m1 = max(m1_overrep, key=m1_overrep.get) if m1_overrep else "—"

        correspondence.append({
            "m3_cluster":       f"M3-C{c}",
            "n":                n_c,
            "best_m2":          best_m2,
            "best_m2_overrep":  m2_overrep.get(best_m2, 0),
            "best_m1":          best_m1,
            "best_m1_overrep":  m1_overrep.get(best_m1, 0),
            "m2_overrep_full":  dict(sorted(m2_overrep.items())),
            "m1_overrep_full":  dict(sorted(m1_overrep.items())),
        })

    return correspondence


# ═══════════════════════════════════════════════════════════════════════════════
# Plots
# ═══════════════════════════════════════════════════════════════════════════════

def plot_kmedoids_explore(umap2d: np.ndarray, all_labels: dict[int, np.ndarray],
                          all_sil: dict[int, float]) -> None:
    """2×2 grid of UMAP scatter plots, one per k candidate."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 11))
    axes_flat  = axes.flatten()
    palette    = sns.color_palette("tab10", 10)

    for idx, k in enumerate(K_CANDIDATES):
        ax     = axes_flat[idx]
        labels = all_labels[k]
        sil    = all_sil[k]
        for c in sorted(set(labels)):
            m     = labels == c
            color = palette[c % 10]
            ax.scatter(umap2d[m, 0], umap2d[m, 1], c=[color],
                       s=3, alpha=0.5, label=f"C{c} (n={m.sum()})")
        ax.set_title(f"k={k}  silhouette={sil:.3f}", fontsize=10)
        ax.set_xlabel("UMAP-1"); ax.set_ylabel("UMAP-2")
        ax.legend(markerscale=3, fontsize=6, loc="upper right")

    fig.suptitle("Phase 3C — Method 3: k-medoids explore (UMAP 2-D, cosmetic only)",
                 fontsize=11)
    plt.tight_layout()
    fig.savefig(FIGURES / "m3_kmedoids_explore.png", dpi=150)
    plt.close(fig)
    log("  Saved m3_kmedoids_explore.png")


def plot_kmedoids_final(umap2d: np.ndarray, labels: np.ndarray, k: int) -> None:
    fig, ax  = plt.subplots(figsize=(10, 8))
    palette  = sns.color_palette("tab10", k)
    for c in range(k):
        m = labels == c
        ax.scatter(umap2d[m, 0], umap2d[m, 1], c=[palette[c]],
                   s=4, alpha=0.5, label=f"M3-C{c} (n={m.sum()})")
    ax.set_title(f"Phase 3C — k-medoids k={k} (UMAP 2-D, cosmetic)")
    ax.set_xlabel("UMAP-1"); ax.set_ylabel("UMAP-2")
    ax.legend(markerscale=3, fontsize=7)
    plt.tight_layout()
    fig.savefig(FIGURES / f"m3_kmedoids_k{k}.png", dpi=150)
    plt.close(fig)
    log(f"  Saved m3_kmedoids_k{k}.png")


def plot_crosstab(ct: pd.DataFrame, filename: str, title: str) -> None:
    fig, ax = plt.subplots(
        figsize=(max(8, len(ct.columns)), max(5, len(ct.index))))
    sns.heatmap(ct, annot=True, fmt="d", cmap="Blues", ax=ax,
                linewidths=0.5, linecolor="grey")
    ax.set_title(title)
    plt.tight_layout()
    fig.savefig(FIGURES / filename, dpi=150)
    plt.close(fig)
    log(f"  Saved {filename}")


# ═══════════════════════════════════════════════════════════════════════════════
# Reports
# ═══════════════════════════════════════════════════════════════════════════════

def write_explore_report(n_usable: int, n_parse_error: int, emb_shape: tuple,
                         all_labels: dict[int, np.ndarray],
                         all_medoids: dict[int, list[int]],
                         all_sil: dict[int, float],
                         all_exemplars: dict[int, dict],
                         full_dicts: list[dict]) -> None:
    """
    Explore report: silhouette scores + fingerprints for k=4..7.
    Does NOT select k — supervisor does that.
    """
    L = []

    def h(t, lv=2): L.append(f"\n{'#'*lv} {t}\n")
    def p(*parts):  L.append(" ".join(parts)); L.append("")

    L.append("# Phase 3C — Method 3: k-medoids Explore (k=4..7)\n")
    L.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}  ")
    L.append("**Status: ⛔ HARD STOP — supervisor must select k before finalize**\n")
    L.append("---\n")

    h("1. Methodology note")
    p("**Clustering method:** k-medoids (PAM) on cosine distance. NOT HDBSCAN+UMAP.",
      "HDBSCAN on raw 768-D cosine distances found 0 clusters (100% noise at min_samples≥15).",
      "UMAP manufactured an equilateral-triangle topology artifact (ARI=1.0, 0 noise,",
      "separation ratio 14–50×). See reports/decisions_log.md for the full diagnosis.")
    p(f"**Embedding:** {EMBED_MODEL}, {emb_shape[1]}-dim, L2-normalised.",
      f"Fields: perfil_em_uma_frase | postura_emocional | sinal_distintivo.")
    p(f"**Usable summaries:** {n_usable}/{N_TOTAL}. Unique parse failures (dropped): {n_parse_error}.")
    p(f"**k-medoids restarts per k:** {N_RESTARTS}. Best (lowest cost) restart reported.")
    p("**2-D UMAP is cosmetic only** — used for scatter plots, not for clustering.")

    h("2. Silhouette scores and cluster sizes")
    L.append("| k | Silhouette (cosine) | Cluster sizes | Notes |")
    L.append("|---|--------------------|-----------|----|")
    for k in K_CANDIDATES:
        sizes = " / ".join(
            f"C{c}={int((all_labels[k]==c).sum())}"
            for c in sorted(set(all_labels[k]))
        )
        below_floor = [c for c in set(all_labels[k]) if (all_labels[k]==c).sum() < MIN_SIZE]
        note = f"⚠️ C{below_floor} < 3% floor" if below_floor else "ok"
        L.append(f"| {k} | {all_sil[k]:.4f} | {sizes} | {note} |")
    L.append("")
    p(f"Minimum viable cluster size: {MIN_SIZE} (3% of {N_TOTAL}).",
      "Clusters below floor cannot be promoted to persona status.")

    h("3. Cluster fingerprints (5 exemplars each)")
    p("Exemplars = nearest neighbours to the cluster medoid (cosine distance).",
      "First exemplar is the medoid itself (is_medoid=True).",
      "Fields shown are Haiku-generated summaries, NOT raw thread text.")

    for k in K_CANDIDATES:
        h(f"k = {k}  (silhouette = {all_sil[k]:.4f})", lv=3)
        exemplars = all_exemplars[k]
        for c in sorted(exemplars.keys()):
            n_c  = int((all_labels[k] == c).sum())
            pct  = round(n_c / N_TOTAL * 100, 1)
            flag = "  ⚠️ EDGE (<3% floor)" if n_c < MIN_SIZE else ""
            h(f"C{c}  (n={n_c}, {pct}%){flag}", lv=4)
            for ex in exemplars[c][:5]:
                medoid_tag = " **[medoid]**" if ex.get("is_medoid") else ""
                L.append(f"**{ex['thread_id']}** "
                         f"(d={ex['cosine_dist_to_medoid']}){medoid_tag}")
                L.append(f"> Perfil: {ex['perfil']}  ")
                L.append(f"> Postura: {ex['postura']}  ")
                L.append(f"> Sinal: {ex['sinal']}  ")
                L.append(f"> Dor: {ex['dor']}  ")
                L.append("")

    h("4. Figure")
    L.append("- `reports/figures/m3_kmedoids_explore.png` — 2×2 UMAP scatter, one panel per k")
    L.append("")

    L.append("---\n")
    L.append("## ⛔ HARD STOP — k-selection required\n")
    L.append("Review silhouette scores and exemplar fingerprints above.")
    L.append("Select k (from 4, 5, 6, 7) based on interpretability + silhouette.")
    L.append("Then run:")
    L.append("```")
    L.append("python notebooks/03c_llm_hierarchical.py --finalize <k>")
    L.append("```")
    L.append("The finalize run will compute bootstrap stability, adjudication,")
    L.append("cross-tabulations, and produce the final parquet + full report.")

    REPORT_CLUSTER.write_text("\n".join(L), encoding="utf-8")
    log(f"Explore report written → {REPORT_CLUSTER}")


def write_finalize_report(k: int, n_usable: int, n_parse_error: int,
                          emb_shape: tuple, labels: np.ndarray, medoids: list[int],
                          sil: float, boot: dict, miss: dict, corpus_median: float,
                          exemplars: dict, ct_m2: pd.DataFrame, ct_m1: pd.DataFrame,
                          adj: dict, nf_report: dict,
                          ari_m2: dict, correspondence: list[dict]) -> None:
    L = []

    def h(t, lv=2): L.append(f"\n{'#'*lv} {t}\n")
    def p(*parts):  L.append(" ".join(parts)); L.append("")

    L.append(f"# Phase 3C — Method 3: LLM-Hierarchical Clustering (k={k} finalized)\n")
    L.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}  ")
    L.append("**Status: AWAITING SUPERVISOR REVIEW — Phase 3D is blocked**\n")
    L.append("---\n")

    h("1. Methodology")
    p("**Method:** k-medoids (PAM) on cosine distance of mpnet embeddings.",
      f"k={k} selected by supervisor from candidates k=4..7 (interpretability, not silhouette).",
      "HDBSCAN+UMAP pipeline abandoned — see reports/decisions_log.md.")
    p(f"**Embedding:** {EMBED_MODEL}, {emb_shape[1]}-dim, L2-normalised.",
      "Concatenation: perfil_em_uma_frase | postura_emocional | sinal_distintivo.")
    p(f"**Usable summaries:** {n_usable}/{N_TOTAL}.",
      f"Parse failures dropped: {n_parse_error} (0.4% of corpus — see decisions_log.md).")
    p(f"**k-medoids restarts:** {N_RESTARTS}. Silhouette score (cosine): {sil:.4f}.",
      "Low silhouette (~0.05–0.08 range across all k) confirms continuum — no density structure.",
      "k selected on interpretability; silhouette used as tie-breaker only.")

    h("2. Cluster summary")
    L.append(f"Minimum viable cluster: {MIN_SIZE} threads (3% of {N_TOTAL}).\n")
    L.append("| Cluster | n | % | Below 3% floor? |")
    L.append("|---------|---|---|-----------------|")
    for c in range(k):
        n_c  = int((labels == c).sum())
        pct  = round(n_c / N_TOTAL * 100, 1)
        flag = "⚠️ EDGE" if n_c < MIN_SIZE else "ok"
        L.append(f"| M3-C{c} | {n_c} | {pct}% | {flag} |")
    L.append("")

    h("3. Bootstrap stability")
    p("**Interpretation:** k-medoids on a continuum yields modest ARI — these are",
      "supervisor-interpretability partitions, not density clusters. Low ARI is",
      "expected and is reported honestly. ARI=1.0 from the old UMAP run was a",
      "topology artifact, NOT a real stability signal.")
    L.append(f"**Mean ARI: {boot['mean_ari']} ± {boot['std_ari']}**"
             f" ({'STABLE ≥0.5' if boot['mean_ari'] >= 0.5 else 'MODEST <0.5 (expected for continuum)'})\n")
    L.append("| Cluster | Mean Jaccard | Stable? |")
    L.append("|---------|-------------|---------|")
    for c, j in boot["per_cluster_jaccard"].items():
        stable = "ok ≥0.5" if j >= 0.5 else "modest <0.5"
        L.append(f"| M3-C{c} | {j} | {stable} |")
    L.append("")

    h("4. Missingness artifact check")
    p(f"Corpus median missing fields = {corpus_median}. Artifact flag: >{round(1.5 * corpus_median, 2)}.")
    L.append("| Cluster | Mean missing features | Flag? |")
    L.append("|---------|----------------------|-------|")
    for c, mp in miss.items():
        flag = "⚠️ ARTIFACT RISK" if mp["artifact_flag"] else "ok"
        L.append(f"| M3-C{c} | {mp['mean_missing']} | {flag} |")
    L.append("")

    h("5. Cluster exemplars (10 nearest to medoid)")
    p("First exemplar in each cluster is the medoid itself.",
      "Fields are Haiku-generated summaries — not raw thread text.")
    for c in sorted(exemplars.keys()):
        n_c  = int((labels == c).sum())
        pct  = round(n_c / N_TOTAL * 100, 1)
        flag = "  ⚠️ EDGE" if n_c < MIN_SIZE else ""
        h(f"M3-C{c}  (n={n_c}, {pct}%){flag}", lv=4)
        for ex in exemplars[c]:
            medoid_tag = " **[medoid]**" if ex.get("is_medoid") else ""
            L.append(f"**{ex['thread_id']}**"
                     f" (d={ex['cosine_dist_to_medoid']}){medoid_tag}")
            L.append(f"> **Perfil:** {ex['perfil']}  ")
            L.append(f"> **Postura:** {ex['postura']}  ")
            L.append(f"> **Sinal:** {ex['sinal']}  ")
            L.append(f"> **Dor:** {ex['dor']}  ")
            L.append("")

    h("6. Non-financial content rate per cluster")
    p(f"Overall non-financial rate: **{nf_report['overall_rate_pct']}%** "
      f"({nf_report['n_nf_total']}/{nf_report['n_total']} threads). "
      "Clusters >40% non-financial are corpus-artifact candidates.")
    L.append("\n**By subreddit:**\n")
    for sub, sv in sorted(nf_report["by_subreddit"].items()):
        L.append(f"  r/{sub}: {sv['n_nf']}/{sv['n']} = {sv['rate_pct']}%")
    L.append("")
    L.append("| Cluster | n | n non-financial | rate % | Flag? |")
    L.append("|---------|---|-----------------|--------|-------|")
    for lbl, cv in sorted(nf_report["per_cluster"].items()):
        flag = "⚠️ ARTIFACT (>40%)" if cv["artifact_flag"] else "ok"
        L.append(f"| {lbl} | {cv['n']} | {cv['n_nf']} | {cv['rate_pct']}% | {flag} |")
    L.append("")

    h("7. M3–M2 ARI and cluster correspondence")
    p("**ARI (M3 k=4 vs M2 k=7) on shared threads:** actual agreement between the two",
      "independent clusterings. Computed on threads present in both parquets.",
      "ARI=0 means no agreement beyond chance; ARI=1 means perfect agreement.",
      "For independent methods with different k, modest ARI (~0.1–0.3) is a positive signal.")
    ari_val = ari_m2.get("ari")
    n_shared = ari_m2.get("n_shared", 0)
    if ari_val is not None:
        L.append(f"**ARI(M3, M2) = {ari_val:.4f}** on {n_shared} shared threads.\n")
    else:
        L.append("**ARI: insufficient shared threads.**\n")

    p("**M3→M2 correspondence table** (which M2 cluster is most overrepresented in each M3 cluster?).",
      "Overrepresentation = (share of M2-Cx within M3-Cc) / (corpus base rate of M2-Cx).",
      ">1.5× = meaningful signal. Supervisor's predicted mapping shown for comparison.")
    L.append("| M3 cluster | n | Best M2 match | Overrep | Best M1 match | Overrep |")
    L.append("|------------|---|---------------|---------|---------------|---------|")
    for row in correspondence:
        L.append(f"| {row['m3_cluster']} | {row['n']} "
                 f"| {row['best_m2']} | {row['best_m2_overrep']}× "
                 f"| {row['best_m1']} | {row['best_m1_overrep']}× |")
    L.append("")
    p("Full M2 overrepresentation per M3 cluster:")
    for row in correspondence:
        overreps = ", ".join(
            f"{lbl}:{v}×" for lbl, v in sorted(
                row["m2_overrep_full"].items(), key=lambda x: -x[1])
            if v > 0.5
        )
        L.append(f"  {row['m3_cluster']}: {overreps}")
    L.append("")

    h("8. Adjudication — five pre-specified tests (M2→M3 direction)")
    p("Complement to Section 7: for each M2/M1 reference cluster, where do its",
      "threads land in M3? Overrepresentation = pct_in_top / cluster_base_rate.",
      ">1.5× and concentrated = methods independently recover the same group.")
    for test_name, res in adj.items():
        h(f"  {test_name}", lv=4)
        if "note" in res:
            p(f"⚠️ {res['note']}")
            continue
        p(f"Reference threads: {res['n_ref']}. Base rate: {res['base_rate_pct']}%.",
          f"Top M3 cluster: **{res['top_m3_cluster']}** ({res['pct_in_top']}% of ref threads).",
          f"That cluster's corpus share: {res['top_cluster_share_pct']}%. "
          f"Overrepresentation: **{res['overrepresentation']}×**.",
          f"Entropy: {res['entropy']}. Threshold: {res['concentrate_threshold']}%.")
        L.append("Distribution:")
        for m3_c, cnt in sorted(res["distribution"].items()):
            L.append(f"  {m3_c}: {cnt}")
        L.append("")
        if res["concentrated"]:
            verdict = (f"✓ CONCENTRATED — {res['overrepresentation']}× overrepresented in "
                       f"{res['top_m3_cluster']} ({res['pct_in_top']}% ≥ {res['concentrate_threshold']}%)")
        else:
            verdict = f"— DISPERSED ({res['pct_in_top']}% < {res['concentrate_threshold']}% threshold)"
        p(f"**Verdict:** {verdict}")

    h("9. M3 × M2 cross-tabulation")
    L.append(ct_m2.to_markdown())
    L.append("")

    h("10. M3 × M1 cross-tabulation")
    L.append(ct_m1.to_markdown())
    L.append("")

    h("11. Figures")
    L.append(f"- `reports/figures/m3_kmedoids_k{k}.png` — 2-D UMAP coloured by M3 clusters")
    L.append("- `reports/figures/m3_crosstab_m2.png` — M3 × M2 heatmap")
    L.append("- `reports/figures/m3_crosstab_m1.png` — M3 × M1 heatmap")
    L.append("")

    L.append("---\n")
    L.append("## ⛔ HARD STOP\n")
    L.append("Phase 3C complete. Do not proceed to Phase 3D until supervisor review.\n")
    L.append("Key review questions:")
    L.append("1. Does the M3→M2 correspondence (Section 7) confirm the predicted mapping?")
    L.append("   - M3 earnest-learner cluster ↔ M2-C2?")
    L.append("   - M3 cynical-reactive cluster(s) ↔ M2-C1?")
    L.append("   - M3 speculator/crypto cluster ↔ M2-C5?")
    L.append("2. Does the M3×M1 cross-tab confirm the speculator cluster aligns with M1-C2 (crypto)?")
    L.append("3. Are any clusters flagged as missingness or non-financial artifacts?")
    L.append("4. Is bootstrap stability acceptable given the continuum-partition context?")

    REPORT_CLUSTER.write_text("\n".join(L), encoding="utf-8")
    log(f"Finalize report written → {REPORT_CLUSTER}")


# ═══════════════════════════════════════════════════════════════════════════════
# Main entry points
# ═══════════════════════════════════════════════════════════════════════════════

def task2_cluster() -> None:
    """
    Task 2 EXPLORE: k-medoids for k=4..7 on cosine distance.
    Produces silhouette scores + exemplar fingerprints, then HARD STOPS.
    Does NOT run adjudication or save parquet — that is done in --finalize <k>.
    """
    log("=== Phase 3C Task 2 EXPLORE: k-medoids (k=4..7) ===")
    log("HDBSCAN+UMAP pipeline was abandoned — see decisions_log.md")

    if not SAMPLE_OUT.exists():
        log("ERROR: summaries not found. Run Task 1 first.")
        sys.exit(1)

    log("Loading summaries …")
    tids, subreddits, windows, embed_txts, full_dicts = load_summaries()
    n_usable      = len(tids)
    n_parse_error = count_unique_failures()
    log(f"  {n_usable} usable summaries ({n_parse_error} unique parse failures dropped)")

    log("Embedding …")
    emb = embed_texts(embed_txts)

    log("Computing cosine distance matrix …")
    # emb is L2-normalised → cosine_dist = 1 - dot(a,b)
    cos_sim  = emb @ emb.T
    cos_dist = np.clip(1.0 - cos_sim, 0.0, 2.0).astype(np.float32)
    log(f"  Distance matrix shape: {cos_dist.shape}")

    log("Running k-medoids for k=4..7 …")
    all_labels  : dict[int, np.ndarray] = {}
    all_medoids : dict[int, list[int]]  = {}
    all_sil     : dict[int, float]      = {}
    all_exemplars: dict[int, dict]       = {}

    for k in K_CANDIDATES:
        log(f"  k={k} …")
        labels, medoids, cost = kmedoids(cos_dist, k)
        sil = silhouette_cosine(labels, cos_dist)
        log(f"  k={k}: cost={cost:.2f}, silhouette={sil:.4f}")

        sizes = {c: int((labels == c).sum()) for c in range(k)}
        log(f"  Cluster sizes: {sizes}")

        exemplars = cluster_exemplars_kmedoids(emb, labels, medoids, full_dicts)
        all_labels[k]   = labels
        all_medoids[k]  = medoids
        all_sil[k]      = sil
        all_exemplars[k] = exemplars

    log("UMAP 2-D for visualisation …")
    umap2d = umap_reduce_2d(emb)

    log("Plotting …")
    plot_kmedoids_explore(umap2d, all_labels, all_sil)

    log("Writing explore report …")
    write_explore_report(
        n_usable      = n_usable,
        n_parse_error = n_parse_error,
        emb_shape     = emb.shape,
        all_labels    = all_labels,
        all_medoids   = all_medoids,
        all_sil       = all_sil,
        all_exemplars  = all_exemplars,
        full_dicts    = full_dicts,
    )

    log("")
    log("═" * 60)
    log("EXPLORE COMPLETE — HARD STOP")
    log(f"  Silhouette scores: "
        + ", ".join(f"k={k}:{all_sil[k]:.4f}" for k in K_CANDIDATES))
    log(f"  Report: {REPORT_CLUSTER}")
    log(f"  Figure: {FIGURES / 'm3_kmedoids_explore.png'}")
    log("")
    log("  Supervisor: review fingerprints and select k.")
    log("  Then run:")
    log("    python notebooks/03c_llm_hierarchical.py --finalize <k>")
    log("═" * 60)


def task2_finalize(k: int) -> None:
    """
    Task 2 FINALIZE: full analysis at supervisor-selected k.
    Runs k-medoids at chosen k, bootstrap stability, adjudication,
    cross-tabs, saves parquet, writes full report.
    """
    log(f"=== Phase 3C Task 2 FINALIZE: k-medoids k={k} ===")

    if not SAMPLE_OUT.exists():
        log("ERROR: summaries not found.")
        sys.exit(1)

    log("Loading summaries …")
    tids, subreddits, windows, embed_txts, full_dicts = load_summaries()
    n_usable      = len(tids)
    n_parse_error = count_unique_failures()
    log(f"  {n_usable} usable summaries")

    log("Embedding …")
    emb = embed_texts(embed_txts)

    log("Computing cosine distance matrix …")
    cos_sim  = emb @ emb.T
    cos_dist = np.clip(1.0 - cos_sim, 0.0, 2.0).astype(np.float32)

    log(f"Running k-medoids k={k} (final) …")
    labels, medoids, cost = kmedoids(cos_dist, k)
    sil = silhouette_cosine(labels, cos_dist)
    log(f"  cost={cost:.2f}, silhouette={sil:.4f}")
    for c in range(k):
        n_c = int((labels == c).sum())
        log(f"  M3-C{c}: n={n_c} ({round(n_c/N_TOTAL*100,1)}%)")

    log("Bootstrap stability …")
    boot = bootstrap_stability_kmedoids(cos_dist, labels, k)
    log(f"  Mean ARI: {boot['mean_ari']} ± {boot['std_ari']}")

    log("Loading M2 and M1 labels …")
    m2_df = pd.read_parquet(DATA_PROC / "clusters_method2.parquet")[
        ["thread_id", "cluster_label"]]
    m1_df = pd.read_parquet(DATA_PROC / "clusters_method1.parquet")[
        ["thread_id", "cluster_label"]].rename(columns={"cluster_label": "m1_label"})

    log("Loading M2 attributes for missingness check …")
    attr_df = pd.read_parquet(DATA_PROC / "extracted_attributes.parquet")

    log("Missingness profiles …")
    miss, corpus_median = missingness_profiles(labels, tids, attr_df)

    log("Exemplars …")
    exemplars = cluster_exemplars_kmedoids(emb, labels, medoids, full_dicts)

    log("Non-financial content detection …")
    is_nf  = detect_nonfinancial(full_dicts)
    nf_rep = nonfinancial_report(labels, tids, subreddits, is_nf)
    log(f"  Overall: {nf_rep['overall_rate_pct']}% "
        f"({nf_rep['n_nf_total']}/{nf_rep['n_total']})")

    log("Cross-tabulations …")
    ct_m2, ct_m1 = build_crosstabs(labels, tids, m2_df, m1_df)

    log("Adjudication (M2→M3 direction) …")
    adj = adjudication(labels, tids, m2_df, m1_df)

    log("M3→M2 ARI and correspondence (M3→M2 direction) …")
    ari_m2       = compute_m3_m2_ari(labels, tids, m2_df)
    correspondence = m3_cluster_correspondence(labels, tids, k, m2_df, m1_df)
    log(f"  ARI(M3, M2) = {ari_m2.get('ari')} on {ari_m2.get('n_shared')} shared threads")
    for row in correspondence:
        log(f"  {row['m3_cluster']}: best_m2={row['best_m2']} ({row['best_m2_overrep']}×) "
            f"| best_m1={row['best_m1']} ({row['best_m1_overrep']}×)")

    log("UMAP 2-D …")
    umap2d = umap_reduce_2d(emb)

    log("Plots …")
    plot_kmedoids_final(umap2d, labels, k)
    plot_crosstab(ct_m2, "m3_crosstab_m2.png",
                  f"Method 3 × Method 2 cluster cross-tabulation (k={k})")
    plot_crosstab(ct_m1, "m3_crosstab_m1.png",
                  f"Method 3 × Method 1 cluster cross-tabulation (k={k})")

    log("Saving clusters parquet …")
    out_df = pd.DataFrame({
        "thread_id":     tids,
        "subreddit":     subreddits,
        "window":        windows,
        "cluster_label": [f"M3-C{c}" for c in labels],
        "cluster_int":   labels.tolist(),
    })
    out_df.to_parquet(CLUSTERS_OUT, index=False)
    log(f"  Saved → {CLUSTERS_OUT}")

    log("Writing finalize report …")
    write_finalize_report(
        k=k, n_usable=n_usable, n_parse_error=n_parse_error,
        emb_shape=emb.shape, labels=labels, medoids=medoids, sil=sil,
        boot=boot, miss=miss, corpus_median=corpus_median,
        exemplars=exemplars, ct_m2=ct_m2, ct_m1=ct_m1,
        adj=adj, nf_report=nf_rep,
        ari_m2=ari_m2, correspondence=correspondence,
    )

    log("")
    log("═" * 60)
    log(f"TASK 2 FINALIZE COMPLETE — HARD STOP")
    log(f"  k={k}, bootstrap ARI={boot['mean_ari']}±{boot['std_ari']}, sil={sil:.4f}")
    log(f"  ARI(M3 vs M2) = {ari_m2.get('ari')} on {ari_m2.get('n_shared')} shared threads")
    log(f"  Clusters: {CLUSTERS_OUT}")
    log(f"  Report:   {REPORT_CLUSTER}")
    log("  Do NOT proceed to Phase 3D until supervisor review.")
    log("═" * 60)


if __name__ == "__main__":
    if "--cluster" in sys.argv:
        task2_cluster()
    elif "--finalize" in sys.argv:
        idx = sys.argv.index("--finalize")
        if idx + 1 >= len(sys.argv):
            log("ERROR: --finalize requires k argument. E.g., --finalize 5")
            sys.exit(1)
        k = int(sys.argv[idx + 1])
        if k not in K_CANDIDATES:
            log(f"ERROR: k must be one of {K_CANDIDATES}")
            sys.exit(1)
        task2_finalize(k)
    elif "--repair-failures" in sys.argv:
        task1_repair_failures()
    else:
        task1_summarise()

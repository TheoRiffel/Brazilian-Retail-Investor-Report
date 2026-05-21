#!/usr/bin/env python3
"""
Phase 3B — Method 1b: e5-large-instruct with 4k context window
Supplementary re-run using intfloat/multilingual-e5-large-instruct.

Key differences from Method 1 (03b_embedding_clustering.py):
  - Model: intfloat/multilingual-e5-large-instruct
  - Task-instruction prefix (4096-token context window)
  - GPU device, batch_size=16
  - No mpnet secondary, no cosine-distance cross-check
  - Labels: M1b-C prefix
  - Section 0 compares with Phase 3B (Method 1) results

All utility functions reused from 03b_embedding_clustering.py unchanged.
Outputs MUST NOT overwrite any Phase 3B files.

Outputs:
  data/processed/clusters_method1b.parquet
  reports/phase3b_method1b.md
  reports/figures/m1b_*.png
"""

import sys
import importlib.util
import warnings
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import adjusted_rand_score

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE      = Path(__file__).resolve().parent.parent
DATA_PROC = BASE / "data" / "processed"
DATA_INT  = BASE / "data" / "interim"
REPORTS   = BASE / "reports"
FIGURES   = REPORTS / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)

# ── Import utility functions from Phase 3B script ─────────────────────────────
_spec = importlib.util.spec_from_file_location(
    "m1_utils", Path(__file__).parent / "03b_embedding_clustering.py"
)
_m1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m1)

# Re-export all shared utilities under their original names
umap_reduce         = _m1.umap_reduce
umap_2d             = _m1.umap_2d
run_hdbscan         = _m1.run_hdbscan
hdbscan_sweep       = _m1.hdbscan_sweep
choose_min_samples  = _m1.choose_min_samples
bootstrap_stability = _m1.bootstrap_stability
cluster_exemplars   = _m1.cluster_exemplars
attribute_profiles  = _m1.attribute_profiles
cross_tab           = _m1.cross_tab
compute_adjudication = _m1.compute_adjudication
plot_umap_clusters  = _m1.plot_umap_clusters
plot_crosstab       = _m1.plot_crosstab

# ── Constants ─────────────────────────────────────────────────────────────────
SEED            = 42
N_TOTAL         = 3600
MIN_SIZE        = int(N_TOTAL * 0.03)        # 108 — 3% floor
TEXT_CAP        = 6000
UMAP_COMPONENTS = 20
UMAP_NEIGHBORS  = 15
MIN_SAMPLES_OPTIONS = [5, 10, 15, 27]
BOOT_B          = 20
BOOT_FRAC       = 0.80
EXEMPLARS_N     = 10

MODEL_INSTRUCT = "intfloat/multilingual-e5-large-instruct"
INSTRUCT_PREFIX = (
    "Instruct: Represent this Brazilian retail investor Reddit post "
    "for clustering by investor profile and behavior\nQuery: "
)

ORDINAL_FEATURES    = _m1.ORDINAL_FEATURES
CATEGORICAL_FEATURES = _m1.CATEGORICAL_FEATURES


def log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Instruct embedding (new — not in Phase 3B)
# ═══════════════════════════════════════════════════════════════════════════════

def embed_texts_instruct(
    texts: list[str],
    cache_path: Path,
    batch_size: int = 16,
) -> tuple[np.ndarray, dict]:
    """
    Encode texts with e5-large-instruct.
    Uses task-instruction prefix; sets max_seq_length=4096.
    """
    if cache_path.exists():
        log(f"  Loading cached embeddings from {cache_path.name}")
        emb = np.load(cache_path)
        return emb, {"model": MODEL_INSTRUCT, "from_cache": True, "shape": emb.shape}

    log(f"  Loading model {MODEL_INSTRUCT} …")
    from sentence_transformers import SentenceTransformer
    import torch

    device = "cuda" if torch.cuda.is_available() else "cpu"
    log(f"  CUDA available: {torch.cuda.is_available()}  device: {device}")
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        vram_gb  = torch.cuda.get_device_properties(0).total_memory / 1e9
        log(f"  GPU: {gpu_name}  VRAM: {vram_gb:.2f} GB")
        if vram_gb > 10:
            batch_size = 32
            log(f"  VRAM > 10 GB → using batch_size=32")

    model = SentenceTransformer(MODEL_INSTRUCT, device=device)
    model.max_seq_length = 4096
    actual_max = model.max_seq_length
    log(f"  max_seq_length set to 4096, confirmed: {actual_max}")

    input_texts = [INSTRUCT_PREFIX + t[:TEXT_CAP] for t in texts]

    tokenizer = model.tokenizer
    tok_lens  = [len(tokenizer(t, truncation=False)["input_ids"]) for t in input_texts[:200]]
    p95_toks  = int(np.percentile(tok_lens, 95))
    p50_toks  = int(np.percentile(tok_lens, 50))
    n_over_512 = sum(1 for l in tok_lens if l > 512)
    log(f"  Token length (sample 200) — p50: {p50_toks}  p95: {p95_toks}  "
        f"over-512: {n_over_512} ({n_over_512/200*100:.0f}%)")
    log(f"  Model max_seq_length={actual_max}: texts over 4096 tokens will be truncated.")

    import time; t0 = time.time()
    log(f"  Encoding {len(input_texts)} texts (batch_size={batch_size}, device={device}) …")
    emb = model.encode(
        input_texts,
        batch_size=batch_size,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    elapsed = time.time() - t0
    log(f"  Done in {elapsed:.1f}s. Shape: {emb.shape}")

    np.save(cache_path, emb)
    log(f"  Cached → {cache_path}")

    meta = {
        "model":          MODEL_INSTRUCT,
        "from_cache":     False,
        "shape":          emb.shape,
        "max_seq_length": actual_max,
        "p50_tokens":     p50_toks,
        "p95_tokens":     p95_toks,
        "n_over_512":     n_over_512,
        "encode_seconds": round(elapsed, 1),
        "device":         device,
        "batch_size":     batch_size,
    }
    return emb, meta


# ═══════════════════════════════════════════════════════════════════════════════
# Figure helpers specific to Method 1b
# ═══════════════════════════════════════════════════════════════════════════════

def plot_m1b_vs_m1(
    umap2d:      np.ndarray,
    labels_m1b:  np.ndarray,
    labels_m1:   np.ndarray,
) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    palette   = sns.color_palette("tab20", 20)
    for lbl_arr, title, ax in [
        (labels_m1b, f"Method 1b — e5-large-instruct clusters", axes[0]),
        (labels_m1,  f"Method 1 — e5-large clusters",           axes[1]),
    ]:
        for c in sorted(set(lbl_arr)):
            m     = lbl_arr == c
            color = "lightgrey" if c == -1 else palette[c % 20]
            label = "noise" if c == -1 else f"C{c} (n={m.sum()})"
            ax.scatter(umap2d[m, 0], umap2d[m, 1], c=[color], s=4, alpha=0.5, label=label)
        ax.set_title(title)
        ax.set_xlabel("UMAP-1 (e5-large 2D, Phase 3B projection)")
        ax.legend(markerscale=3, fontsize=7, ncol=2)
    fig.suptitle("Method 1b vs Method 1 — same 2-D UMAP projection (e5-large)")
    plt.tight_layout()
    fig.savefig(FIGURES / "m1b_vs_m1.png", dpi=150)
    plt.close(fig)
    log("  Saved m1b_vs_m1.png")


# ═══════════════════════════════════════════════════════════════════════════════
# Report
# ═══════════════════════════════════════════════════════════════════════════════

def write_report(
    emb_meta:     dict,
    sweep_results: dict,
    chosen_ms:    int,
    labels_m1b:   np.ndarray,
    probs_m1b:    np.ndarray,
    labels_m1:    np.ndarray | None,
    ari_m1b_m1:   float | None,
    boot_res:     dict,
    profiles:     dict,
    exemplars:    dict,
    ct:           pd.DataFrame,
    adjudication: dict,
    adj_m1:       dict | None,
) -> None:
    L = []

    def h(t, lv=2): L.append(f"\n{'#'*lv} {t}\n")
    def p(*parts):  L.append(" ".join(str(x) for x in parts)); L.append("")

    n_clusters = len(set(labels_m1b)) - (1 if -1 in labels_m1b else 0)
    n_noise    = int((labels_m1b == -1).sum())
    noise_pct  = round(n_noise / N_TOTAL * 100, 1)

    L.append("# Phase 3B — Method 1b: e5-large-instruct (4k context) — Supplementary\n")
    L.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}  ")
    L.append("**Status: AWAITING SUPERVISOR REVIEW**\n")
    L.append("---\n")

    # ── Section 0: Comparison with Method 1 ─────────────────────────────────
    h("0. Comparison with Method 1 (e5-large, 512-token)")
    p("This section summarises how Method 1b (e5-large-instruct, 4k context) differs from",
      "the Phase 3B standard run (e5-large, 512-token).")

    p(f"**Method 1b:** {n_clusters} clusters, {n_noise} noise ({noise_pct}%),",
      f"min_samples={chosen_ms} (sweep-chosen).")

    if labels_m1 is not None:
        n_m1  = len(set(labels_m1)) - (1 if -1 in labels_m1 else 0)
        nn_m1 = int((labels_m1 == -1).sum())
        p(f"**Method 1:**  {n_m1} clusters, {nn_m1} noise ({nn_m1/N_TOTAL*100:.1f}%),",
          f"min_samples=15 (Phase 3B chosen).")
        if ari_m1b_m1 is not None:
            p(f"**ARI(Method 1b, Method 1) = {ari_m1b_m1:.3f}**")
            if ari_m1b_m1 >= 0.7:
                p("ARI ≥ 0.7: strong agreement. The instruct model recovers essentially",
                  "the same cluster structure. The 4k context window does not materially",
                  "change segmentation versus the 512-token baseline.")
            elif ari_m1b_m1 >= 0.4:
                p("ARI 0.4–0.7: moderate agreement. Method 1b finds a similar coarse",
                  "structure but splits or merges some boundaries. The longer context may",
                  "capture more within-thread discourse structure.")
            else:
                p("⚠️ ARI < 0.4: low agreement. Method 1b finds substantially different",
                  "cluster assignments. Differences are likely due to the instruct prefix",
                  "and/or longer effective context changing embedding geometry.")

    p("**Adjudication comparison (M2-C1 provisional cluster):**")
    if adj_m1 is not None and "M2-C1" in adjudication:
        m1b_c1 = adjudication["M2-C1"]
        m1_c1  = adj_m1.get("M2-C1", {})
        p(f"- Method 1b:  M2-C1 → top_m1b={m1b_c1.get('top_m1','?')}",
          f"({m1b_c1.get('top_pct',0):.1f}%),",
          f"entropy={m1b_c1.get('entropy','?')},",
          f"concentrated={m1b_c1.get('concentrated',False)}")
        p(f"- Method 1:   M2-C1 → top_m1={m1_c1.get('top_m1','?')}",
          f"({m1_c1.get('top_pct',0):.1f}%),",
          f"entropy={m1_c1.get('entropy','?')},",
          f"concentrated={m1_c1.get('concentrated',False)}")
        m1b_conc = m1b_c1.get("concentrated", False)
        m1_conc  = m1_c1.get("concentrated", False)
        if m1b_conc and m1_conc:
            p("Both methods find M2-C1 concentrated: converging evidence that M2-C1 is",
              "a real behavioral cluster. Supports promotion to confirmed in Phase 3D.")
        elif not m1b_conc and not m1_conc:
            p("Neither method finds M2-C1 concentrated: M2-C1 is diffuse in embedding",
              "space regardless of context window. Supports maintaining provisional flag.")
        else:
            p(f"Methods disagree on M2-C1 concentration (M1b: {m1b_conc}, M1: {m1_conc}).",
              "Adjudication is inconclusive. Report both outcomes in Phase 3D.")
    else:
        p("(Method 1 adjudication data unavailable for comparison.)")

    # ── Section 1: Methodology ────────────────────────────────────────────────
    h("1. Methodology")
    p("**Independent of Method 2.** Text embeddings only; blind to subreddit, window,",
      "extracted attributes, and Method 2 cluster labels.")
    p(f"**Model:** `{MODEL_INSTRUCT}`",
      f"  Dimensions: {emb_meta['shape'][1]}.",
      f"  Pooling: mean (SentenceTransformer default).",
      f"  Prefix: task-instruction format (see below).",
      f"  max_seq_length set to 4096 (confirmed: {emb_meta.get('max_seq_length', 4096)}).",
      f"  Encode time: {emb_meta.get('encode_seconds', 'cached')}s.",
      f"  Device: {emb_meta.get('device', 'cached')}.")
    p(f"**Task instruction prefix:**")
    L.append(f"```\n{INSTRUCT_PREFIX}\n```\n")
    p(f"**Token length (sample of 200 texts):**",
      f"p50={emb_meta.get('p50_tokens', '?')}, p95={emb_meta.get('p95_tokens', '?')}.",
      f"Texts over 512 tokens: {emb_meta.get('n_over_512', '?')} of 200",
      f"({emb_meta.get('n_over_512', 0)/2:.0f}% of sample).",
      "These texts benefit from the 4k window; the 512-token model would truncate them.")
    p(f"**UMAP denoising:** cosine metric, n_components={UMAP_COMPONENTS},",
      f"n_neighbors={UMAP_NEIGHBORS}, min_dist=0.0.",
      "2-D UMAP uses the Phase 3B e5-large 2D projection for visual comparison.",
      "(Method 1b does NOT generate its own 2D UMAP — this avoids projection distortion",
      "when comparing visually to Method 1.)")
    p(f"**HDBSCAN:** min_cluster_size={MIN_SIZE}, min_samples={chosen_ms} (sweep-chosen).")
    p("**No mpnet secondary.** No cosine-distance cross-check.",
      "This script is a targeted re-run focused on the instruct model benefit;",
      "secondary checks are reported in Phase 3B.")

    # ── Section 2: min_samples sweep ─────────────────────────────────────────
    h("2. HDBSCAN min_samples sweep (instruct model, UMAP-20d)")
    L.append("| min_samples | n_clusters | n_noise | noise_pct | Chosen? |")
    L.append("|------------|-----------|---------|-----------|---------|")
    for ms, r in sorted(sweep_results.items()):
        mark = "← chosen" if ms == chosen_ms else ""
        L.append(f"| {ms} | {r['n_clusters']} | {r['n_noise']} | {r['noise_pct']}% | {mark} |")
    L.append("")

    # ── Section 3: Cluster summary ────────────────────────────────────────────
    h("3. Cluster summary (e5-large-instruct, UMAP+HDBSCAN)")
    L.append(f"⚠️ **Noise: {n_noise} threads ({noise_pct}%) excluded from all analyses below.**\n")
    L.append("| Cluster | n | % | Below 3% floor? |")
    L.append("|---------|---|---|-----------------|")
    sizes = pd.Series(labels_m1b).value_counts().sort_index()
    for c, cnt in sizes.items():
        if c == -1:
            L.append(f"| noise | {cnt} | {cnt/N_TOTAL*100:.1f}% | n/a |")
        else:
            edge = "⚠️ EDGE" if cnt < MIN_SIZE else "ok"
            L.append(f"| M1b-C{c} | {cnt} | {cnt/N_TOTAL*100:.1f}% | {edge} |")
    L.append("")

    # ── Section 4: Bootstrap stability ───────────────────────────────────────
    h("4. Bootstrap stability (instruct model, UMAP+HDBSCAN)")
    p(f"20 iterations, 80% subsample. UMAP NOT re-run per bootstrap.",
      f"Noise excluded from ARI computation.")
    p(f"**Mean ARI: {boot_res['mean_ari']:.3f} ± {boot_res['std_ari']:.3f}**",
      f"({'STABLE' if boot_res['mean_ari'] >= 0.5 else '⚠️ UNSTABLE'})")
    L.append("| Cluster | Mean Jaccard | Stable? |")
    L.append("|---------|-------------|---------|")
    for c, j in sorted(boot_res["per_cluster_jaccard"].items()):
        flag = "ok" if j >= 0.5 else "⚠️ UNSTABLE"
        L.append(f"| M1b-C{c} | {j:.3f} | {flag} |")
    L.append("")

    # ── Section 5: Missingness artifact check ────────────────────────────────
    h("5. Missingness artifact check")
    p("Mean desconhecido/NaN count per thread (M2 attributes) per M1b cluster.",
      "Corpus median = 1.0. Flag if mean > 1.50.")
    L.append("| Cluster | Mean missing features | Flag? |")
    L.append("|---------|----------------------|-------|")
    for c, prof in sorted(profiles.items()):
        mm   = prof["mean_missing"]
        flag = "⚠️ ARTIFACT RISK" if mm > 1.5 else "ok"
        L.append(f"| M1b-C{c} | {mm} | {flag} |")
    L.append("")

    # ── Section 6: Attribute profiles ────────────────────────────────────────
    h("6. Attribute profiles (M2 attributes joined back; NOT used in clustering)")
    for c, prof in sorted(profiles.items()):
        h(f"M1b-C{c}  (n={prof['n']})", lv=4)
        L.append(f"Mean missingness: {prof['mean_missing']}\n")
        L.append("| Feature | Value |")
        L.append("|---------|-------|")
        for col in ORDINAL_FEATURES:
            L.append(f"| {col} | {prof.get(col, '—')} (mean) |")
        for col in CATEGORICAL_FEATURES:
            modes = prof.get(col, [])
            val   = "  /  ".join(f"{v} ({n})" for v, n in modes) if modes else "—"
            L.append(f"| {col} | {val} |")
        L.append("")

    # ── Section 7: Exemplars ─────────────────────────────────────────────────
    h("7. Exemplars (10 nearest to cluster centroid, instruct embeddings)")
    p("Cosine similarity computed on e5-large-instruct embeddings.")
    for c, ex_list in sorted(exemplars.items()):
        h(f"M1b-C{c} exemplars", lv=4)
        for ex in ex_list:
            L.append(f"**{ex['thread_id']}** (sim={ex['cosine_sim']})")
            L.append(f"> {ex['snippet']}")
            L.append("")
        L.append("")

    # ── Section 8: Cross-tab M1b × M2 ────────────────────────────────────────
    h("8. Cross-tabulation M1b × M2")
    L.append(ct.to_markdown())
    L.append("")

    # ── Section 9: Adjudication ───────────────────────────────────────────────
    h("9. Adjudication — does Method 1b corroborate Method 2 structure?")
    for m2_tgt, label, note in [
        ("M2-C5", "speculator: high-crypto, euphoric, short-term", "11.1"),
        ("M2-C2", "earnest-learner: curious, exploratory",         "11.2"),
        ("M2-C1", "PROVISIONAL — cynical-reactive",                "11.3"),
    ]:
        adj = adjudication.get(m2_tgt, {})
        h(f"9.{note[-1]}  {m2_tgt} ({label})", lv=4)
        p(f"{m2_tgt} threads: {adj.get('total', 0)}.",
          f"Top M1b cluster: {adj.get('top_m1', '?')} ({adj.get('top_pct', 0):.1f}%).",
          f"Entropy: {adj.get('entropy', '?')}.")
        if adj.get("concentrated", False):
            p(f"✓ {m2_tgt} concentrated in one M1b cluster — Method 1b corroborates.")
        else:
            p(f"⚠️ {m2_tgt} diffuse across M1b clusters — no strong corroboration.")

    # ── Section 10: Figures ───────────────────────────────────────────────────
    h("10. Figures")
    for fn, desc in [
        ("m1b_umap.png",     "2-D UMAP (Phase 3B projection) coloured by M1b clusters"),
        ("m1b_vs_m1.png",    "M1b vs M1 cluster assignments on same 2-D UMAP"),
        ("m1b_crosstab.png", "M1b × M2 cross-tabulation heatmap"),
    ]:
        L.append(f"- `reports/figures/{fn}` — {desc}")
    L.append("")

    L.append("---\n")
    L.append("## ⛔ HARD STOP\n")
    L.append(
        "Method 1b complete. **Do not proceed to Phase 3D** until supervisor has\n"
        "reviewed this document, the comparison in Section 0, and the adjudication\n"
        "results in Section 9. The M2-C1 adjudication outcome from both Method 1\n"
        "and Method 1b should be considered together before changing provisional status.\n"
    )

    out = REPORTS / "phase3b_method1b.md"
    out.write_text("\n".join(L), encoding="utf-8")
    log(f"  Saved {out}")


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    rng = np.random.default_rng(SEED)

    # ── Load texts ────────────────────────────────────────────────────────────
    log("Loading extracted attributes …")
    attr_df    = pd.read_parquet(DATA_PROC / "extracted_attributes.parquet")
    thread_ids = attr_df["thread_id"].tolist()
    texts      = [str(t)[:TEXT_CAP] for t in attr_df["unit_text"].tolist()]
    log(f"  {len(texts)} threads loaded.")

    # ── Embed (instruct model) ─────────────────────────────────────────────────
    log("=== METHOD 1b: e5-large-instruct ===")
    emb_m1b, meta_m1b = embed_texts_instruct(
        texts,
        cache_path=DATA_INT / "embeddings_e5large_instruct.npy",
    )

    # ── UMAP denoising (instruct) ─────────────────────────────────────────────
    log("UMAP denoising (instruct, 20 components) …")
    umap20_m1b = umap_reduce(
        emb_m1b, UMAP_COMPONENTS, "cosine",
        cache_path=DATA_INT / "umap20_e5instruct.npy",
    )

    # ── Load Phase 3B 2D UMAP for visual comparison ───────────────────────────
    umap2d_path = DATA_INT / "umap2d_e5large.npy"
    umap2d_m1   = np.load(umap2d_path) if umap2d_path.exists() else None
    if umap2d_m1 is None:
        log("⚠️  Phase 3B 2D UMAP not found; running new 2D UMAP for M1b visualization.")
        umap2d_m1 = umap_2d(emb_m1b, "cosine",
                             cache_path=DATA_INT / "umap2d_e5instruct.npy")

    # ── HDBSCAN sweep ─────────────────────────────────────────────────────────
    log("HDBSCAN min_samples sweep (instruct UMAP-20d) …")
    sweep = hdbscan_sweep(umap20_m1b, metric="euclidean")
    chosen_ms = choose_min_samples(sweep)
    log(f"Chosen min_samples: {chosen_ms}")

    # ── Primary clustering ─────────────────────────────────────────────────────
    log(f"Primary HDBSCAN (instruct, UMAP-20d, min_samples={chosen_ms}) …")
    labels_m1b, probs_m1b = run_hdbscan(umap20_m1b, MIN_SIZE, chosen_ms, "euclidean")
    n_clust = len(set(labels_m1b)) - (1 if -1 in labels_m1b else 0)
    n_noise = int((labels_m1b == -1).sum())
    log(f"  Result: {n_clust} clusters, {n_noise} noise ({n_noise/N_TOTAL*100:.1f}%)")

    # ── Load Phase 3B labels for comparison ──────────────────────────────────
    m1_df      = None
    labels_m1  = None
    adj_m1     = None
    ari_m1b_m1 = None

    m1_parquet = DATA_PROC / "clusters_method1.parquet"
    if m1_parquet.exists():
        m1_df     = pd.read_parquet(m1_parquet)
        id_to_m1  = dict(zip(m1_df["thread_id"], m1_df["cluster_int"]))
        labels_m1 = np.array([id_to_m1.get(tid, -1) for tid in thread_ids])
        valid     = (labels_m1b != -1) & (labels_m1 != -1)
        if valid.sum() > 10:
            ari_m1b_m1 = round(adjusted_rand_score(labels_m1b[valid], labels_m1[valid]), 3)
        log(f"ARI(M1b, M1) = {ari_m1b_m1}")

        m2_df_for_adj = pd.read_parquet(DATA_PROC / "clusters_method2.parquet")
        adj_m1 = compute_adjudication(labels_m1, thread_ids, m2_df_for_adj,
                                      ["M2-C1", "M2-C2", "M2-C5"])
    else:
        log("  Phase 3B parquet not found; skipping M1 comparison.")

    # ── Bootstrap stability ───────────────────────────────────────────────────
    log(f"Bootstrap stability ({BOOT_B} iterations, {int(BOOT_FRAC*100)}% subsample) …")
    boot_res = bootstrap_stability(
        umap20_m1b, labels_m1b, chosen_ms, "euclidean", BOOT_B, BOOT_FRAC, rng
    )
    log(f"  Mean ARI: {boot_res['mean_ari']:.3f} ± {boot_res['std_ari']:.3f}")

    # ── Attribute profiles ────────────────────────────────────────────────────
    log("Computing attribute profiles …")
    profiles = attribute_profiles(labels_m1b, thread_ids, attr_df)

    # ── Exemplars ─────────────────────────────────────────────────────────────
    log("Computing cluster exemplars (instruct embeddings) …")
    exemplars = cluster_exemplars(emb_m1b, labels_m1b, texts, thread_ids)

    # ── Cross-tab M1b × M2 ────────────────────────────────────────────────────
    log("Building M1b × M2 cross-tabulation …")
    m2_df = pd.read_parquet(DATA_PROC / "clusters_method2.parquet")

    # Rename labels to M1b-C prefix before cross-tab
    labels_m1b_str = np.array([f"M1b-C{c}" if c != -1 else "M1b-noise" for c in labels_m1b])
    m2_map     = dict(zip(m2_df["thread_id"], m2_df["cluster_label"]))
    m2_aligned = np.array([m2_map.get(tid, "M2-unknown") for tid in thread_ids])
    ct = pd.crosstab(pd.Categorical(labels_m1b_str), pd.Categorical(m2_aligned))

    # ── Adjudication ──────────────────────────────────────────────────────────
    log("Computing adjudication statistics …")
    adjudication = compute_adjudication(
        labels_m1b, thread_ids, m2_df, ["M2-C1", "M2-C2", "M2-C5"]
    )
    # Rename top_m1 to top_m1b in display
    for res in adjudication.values():
        if "top_m1" in res:
            res["top_m1"] = res["top_m1"].replace("M1-C", "M1b-C")

    for tgt, res in adjudication.items():
        log(f"  {tgt}: top_m1b={res.get('top_m1','?')} ({res.get('top_pct',0):.1f}%)  "
            f"entropy={res.get('entropy','?')}  concentrated={res.get('concentrated',False)}")

    # ── Figures ───────────────────────────────────────────────────────────────
    log("Generating figures …")
    plot_umap_clusters(
        umap2d_m1, labels_m1b,
        f"Method 1b — e5-large-instruct UMAP+HDBSCAN  "
        f"(k={n_clust}, noise={n_noise/N_TOTAL*100:.1f}%)",
        "m1b_umap.png", n_noise / N_TOTAL * 100,
    )
    if labels_m1 is not None:
        plot_m1b_vs_m1(umap2d_m1, labels_m1b, labels_m1)

    # Crosstab figure using M1b labels (numeric → the cross_tab function uses m1_labels directly)
    fig, ax = plt.subplots(figsize=(max(8, len(ct.columns)), max(5, len(ct.index))))
    sns.heatmap(ct, annot=True, fmt="d", cmap="Blues", ax=ax,
                linewidths=0.5, linecolor="grey")
    ax.set_title("Method 1b × Method 2 cluster cross-tabulation")
    ax.set_xlabel("Method 2 cluster")
    ax.set_ylabel("Method 1b cluster")
    plt.tight_layout()
    fig.savefig(FIGURES / "m1b_crosstab.png", dpi=150)
    plt.close(fig)
    log("  Saved m1b_crosstab.png")

    # ── Save parquet ──────────────────────────────────────────────────────────
    out_df = pd.DataFrame({
        "thread_id":       thread_ids,
        "cluster_label":   [f"M1b-C{c}" if c != -1 else "M1b-noise" for c in labels_m1b],
        "cluster_int":     labels_m1b,
        "membership_prob": probs_m1b.round(4),
    })
    out_path = DATA_PROC / "clusters_method1b.parquet"
    out_df.to_parquet(out_path, index=False)
    log(f"Saved {out_path}")

    # ── Report ────────────────────────────────────────────────────────────────
    log("Writing report …")
    write_report(
        emb_meta=meta_m1b,
        sweep_results=sweep,
        chosen_ms=chosen_ms,
        labels_m1b=labels_m1b,
        probs_m1b=probs_m1b,
        labels_m1=labels_m1,
        ari_m1b_m1=ari_m1b_m1,
        boot_res=boot_res,
        profiles=profiles,
        exemplars=exemplars,
        ct=ct,
        adjudication=adjudication,
        adj_m1=adj_m1,
    )

    # ── Summary ───────────────────────────────────────────────────────────────
    log("=" * 60)
    log("METHOD 1b (e5-large-instruct) COMPLETE")
    sizes = pd.Series(labels_m1b).value_counts().sort_index()
    for c, cnt in sizes.items():
        log(f"  {'noise' if c==-1 else f'M1b-C{c}'}: {cnt} ({cnt/N_TOTAL*100:.1f}%)")
    log(f"  Mean ARI stability: {boot_res['mean_ari']:.3f}")
    if ari_m1b_m1 is not None:
        log(f"  ARI(M1b, M1): {ari_m1b_m1:.3f}")
    log(f"  M2-C1 adjudication: concentrated={adjudication.get('M2-C1',{}).get('concentrated','?')}")
    log(f"  Parquet: {out_path}")
    log(f"  Report: {REPORTS / 'phase3b_method1b.md'}")
    log("⛔ HARD STOP — awaiting supervisor review")
    log("=" * 60)


if __name__ == "__main__":
    main()

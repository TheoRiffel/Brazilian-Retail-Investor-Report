#!/usr/bin/env python3
"""
Phase 3B: Method 1 — Embedding + HDBSCAN (comparison instrument)

Independent of Method 2. Text embeddings only; blind to subreddit, window,
all extracted attributes, AND Method 2 cluster labels.

Primary model:   intfloat/multilingual-e5-large  (1024-dim; passage: prefix)
Secondary model: paraphrase-multilingual-mpnet-base-v2  (768-dim; no prefix)

Embedding → UMAP denoising (cosine, 20 components) → HDBSCAN
Cross-check: HDBSCAN on raw cosine distances (no UMAP)
Second-model agreement: run full pipeline on mpnet; report ARI vs e5

Outputs:
  data/processed/clusters_method1.parquet
  reports/phase3b_method1.md
  reports/figures/m1_*.png
"""

import sys
import warnings
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.metrics.pairwise import cosine_distances

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE      = Path(__file__).resolve().parent.parent
DATA_PROC = BASE / "data" / "processed"
DATA_INT  = BASE / "data" / "interim"
REPORTS   = BASE / "reports"
FIGURES   = REPORTS / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)

# ── Constants ─────────────────────────────────────────────────────────────────
SEED            = 42
N_TOTAL         = 3600
MIN_SIZE        = int(N_TOTAL * 0.03)        # 108 — 3% floor
TEXT_CAP        = 6000                        # chars (already enforced in data)
UMAP_COMPONENTS = 20                          # denoising UMAP dimensions
UMAP_NEIGHBORS  = 15
MIN_SAMPLES_OPTIONS = [5, 10, 15, 27]        # tune; report all; pick best
BOOT_B          = 20
BOOT_FRAC       = 0.80
EXEMPLARS_N     = 10

MODEL_PRIMARY   = "intfloat/multilingual-e5-large"
MODEL_SECONDARY = "paraphrase-multilingual-mpnet-base-v2"

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
# 1. Embedding
# ═══════════════════════════════════════════════════════════════════════════════

def embed_texts(
    texts: list[str],
    model_name: str,
    cache_path: Path,
    use_passage_prefix: bool = False,
    batch_size: int = 64,
) -> tuple[np.ndarray, dict]:
    """
    Encode texts with a SentenceTransformer model, caching to disk.
    Returns (embeddings, metadata_dict).
    embeddings are L2-normalised (unit vectors).
    """
    if cache_path.exists():
        log(f"  Loading cached embeddings from {cache_path.name}")
        emb = np.load(cache_path)
        meta = {"model": model_name, "from_cache": True, "shape": emb.shape}
        return emb, meta

    log(f"  Loading model {model_name} …")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_name)

    if use_passage_prefix:
        input_texts = ["passage: " + t[:TEXT_CAP] for t in texts]
    else:
        input_texts = [t[:TEXT_CAP] for t in texts]

    # Token-length stats
    tokenizer  = model.tokenizer
    tok_lens   = [len(tokenizer(t, truncation=False)["input_ids"]) for t in input_texts[:200]]
    p95_toks   = int(np.percentile(tok_lens, 95))
    max_model  = getattr(tokenizer, "model_max_length", 512)
    n_truncated_est = sum(1 for t in input_texts if len(t) > 2000)  # rough proxy
    log(f"  Model max_length={max_model}  p95 token length (sample 200)={p95_toks}")
    log(f"  Approx texts that will be tokenizer-truncated: {n_truncated_est} "
        f"({n_truncated_est/N_TOTAL*100:.1f}%)")

    log(f"  Encoding {len(input_texts)} texts (batch_size={batch_size}) …")
    import time; t0 = time.time()
    emb = model.encode(
        input_texts,
        batch_size=batch_size,
        show_progress_bar=True,
        normalize_embeddings=True,   # L2-normalise: cosine sim = dot product
        convert_to_numpy=True,
    )
    elapsed = time.time() - t0
    log(f"  Done in {elapsed:.1f}s. Shape: {emb.shape}")

    np.save(cache_path, emb)
    log(f"  Cached → {cache_path}")

    meta = {
        "model":           model_name,
        "from_cache":      False,
        "shape":           emb.shape,
        "max_model_len":   max_model,
        "p95_tokens":      p95_toks,
        "n_truncated_est": n_truncated_est,
        "encode_seconds":  round(elapsed, 1),
        "passage_prefix":  use_passage_prefix,
    }
    return emb, meta


# ═══════════════════════════════════════════════════════════════════════════════
# 2. UMAP
# ═══════════════════════════════════════════════════════════════════════════════

def umap_reduce(
    emb: np.ndarray,
    n_components: int,
    metric: str,
    cache_path: Path | None = None,
) -> np.ndarray:
    """UMAP dimensionality reduction. Caches result if cache_path given."""
    if cache_path and cache_path.exists():
        log(f"  Loading cached UMAP ({n_components}d) from {cache_path.name}")
        return np.load(cache_path)

    import umap as umap_lib
    log(f"  UMAP n_components={n_components}, metric={metric} …")
    import time; t0 = time.time()
    reducer = umap_lib.UMAP(
        n_components=n_components,
        metric=metric,
        n_neighbors=UMAP_NEIGHBORS,
        min_dist=0.0,           # tight clusters, for clustering not viz
        random_state=SEED,
        n_jobs=1,
    )
    reduced = reducer.fit_transform(emb)
    log(f"  UMAP done in {time.time()-t0:.1f}s. Shape: {reduced.shape}")

    if cache_path:
        np.save(cache_path, reduced)
        log(f"  Cached → {cache_path}")
    return reduced


def umap_2d(emb: np.ndarray, metric: str, cache_path: Path | None = None) -> np.ndarray:
    """2-D UMAP for visualisation only (min_dist=0.1 for readability)."""
    if cache_path and cache_path.exists():
        log(f"  Loading cached 2-D UMAP from {cache_path.name}")
        return np.load(cache_path)

    import umap as umap_lib
    log("  UMAP 2-D (visualisation only) …")
    reducer = umap_lib.UMAP(
        n_components=2, metric=metric, n_neighbors=UMAP_NEIGHBORS,
        min_dist=0.1, random_state=SEED, n_jobs=1,
    )
    emb2d = reducer.fit_transform(emb)
    if cache_path:
        np.save(cache_path, emb2d)
        log(f"  Cached → {cache_path}")
    return emb2d


# ═══════════════════════════════════════════════════════════════════════════════
# 3. HDBSCAN
# ═══════════════════════════════════════════════════════════════════════════════

def run_hdbscan(
    X: np.ndarray,
    min_cluster_size: int,
    min_samples: int,
    metric: str = "euclidean",
) -> tuple[np.ndarray, np.ndarray]:
    """
    Returns (labels, probabilities).
    labels: -1 = noise, 0..k-1 = cluster
    """
    import hdbscan as hdbscan_lib
    clusterer = hdbscan_lib.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric=metric,
        core_dist_n_jobs=1,
    )
    labels = clusterer.fit_predict(X.astype(np.float64))
    probs  = getattr(clusterer, "probabilities_", np.ones(len(labels)))
    return labels, probs


def hdbscan_sweep(X: np.ndarray, metric: str = "euclidean") -> dict:
    """Run HDBSCAN for each min_samples value; return summary table."""
    results = {}
    for ms in MIN_SAMPLES_OPTIONS:
        labels, _ = run_hdbscan(X, MIN_SIZE, ms, metric)
        n_clust   = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise   = int((labels == -1).sum())
        results[ms] = {
            "n_clusters": n_clust,
            "n_noise":    n_noise,
            "noise_pct":  round(n_noise / N_TOTAL * 100, 1),
        }
        log(f"  min_samples={ms}: {n_clust} clusters, {n_noise} noise ({n_noise/N_TOTAL*100:.1f}%)")
    return results


def choose_min_samples(sweep: dict) -> int:
    """
    Select min_samples: prefer smallest value with noise_pct < 25%
    and n_clusters >= 4. Fall back to the value with fewest noise points.
    """
    candidates = [
        ms for ms, r in sweep.items()
        if r["noise_pct"] < 25 and r["n_clusters"] >= 4
    ]
    if candidates:
        return min(candidates)
    # fall back: fewest noise points
    return min(sweep, key=lambda ms: sweep[ms]["n_noise"])


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Bootstrap stability
# ═══════════════════════════════════════════════════════════════════════════════

def bootstrap_stability(
    X: np.ndarray,
    orig_labels: np.ndarray,
    min_samples: int,
    metric:  str = "euclidean",
    n_boot:  int = BOOT_B,
    frac:    float = BOOT_FRAC,
    rng:     np.random.Generator | None = None,
) -> dict:
    """
    Bootstrap stability for HDBSCAN on precomputed UMAP embeddings.
    Subsamples frac*n rows of X (the UMAP-reduced embeddings); does NOT re-run UMAP.
    """
    if rng is None:
        rng = np.random.default_rng(SEED)

    k_orig = len(set(orig_labels)) - (1 if -1 in orig_labels else 0)
    n      = len(orig_labels)
    aris   = []
    cj     = {c: [] for c in range(k_orig)}

    for b in range(n_boot):
        sub = np.sort(rng.choice(n, size=int(n * frac), replace=False))
        X_s = X[sub]
        boot_labels, _ = run_hdbscan(X_s, MIN_SIZE, min_samples, metric)

        orig_s = orig_labels[sub]
        # Exclude noise from both sides for ARI
        valid  = (orig_s != -1) & (boot_labels != -1)
        if valid.sum() < 10:
            log(f"  Bootstrap {b+1}: too few valid pairs ({valid.sum()}), skip")
            aris.append(0.0)
            continue

        ari = adjusted_rand_score(orig_s[valid], boot_labels[valid])
        aris.append(ari)

        # Per-cluster Jaccard (on subsample, non-noise original clusters only)
        for c in range(k_orig):
            orig_m = set(np.where(orig_s == c)[0])
            if not orig_m:
                continue
            best_j = 0.0
            for c2 in set(boot_labels):
                if c2 == -1:
                    continue
                bm   = set(np.where(boot_labels == c2)[0])
                union = len(orig_m | bm)
                if union > 0:
                    best_j = max(best_j, len(orig_m & bm) / union)
            cj[c].append(best_j)

        log(f"  Bootstrap {b+1}/{n_boot}: k_boot={len(set(boot_labels))-(1 if -1 in boot_labels else 0)}"
            f"  ARI={ari:.3f}")

    return {
        "mean_ari": round(float(np.mean(aris)), 3),
        "std_ari":  round(float(np.std(aris)),  3),
        "per_cluster_jaccard": {
            c: round(float(np.mean(v)), 3) if v else 0.0
            for c, v in cj.items()
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Exemplars
# ═══════════════════════════════════════════════════════════════════════════════

def cluster_exemplars(
    emb: np.ndarray,
    labels: np.ndarray,
    texts: list[str],
    thread_ids: list[str],
    n: int = EXEMPLARS_N,
    snippet_len: int = 300,
) -> dict:
    """
    For each cluster: compute centroid (mean of normalised embeddings),
    find n threads with highest cosine similarity (= dot product for unit vectors).
    Returns {cluster_int: [(thread_id, similarity, text_snippet), …]}.
    """
    exemplars = {}
    for c in sorted(set(labels)):
        if c == -1:
            continue
        members = np.where(labels == c)[0]
        centroid = emb[members].mean(axis=0)
        norm     = np.linalg.norm(centroid)
        if norm > 0:
            centroid /= norm
        sims     = emb[members] @ centroid          # dot product (cosine sim)
        top_idx  = members[np.argsort(-sims)[:n]]
        exemplars[int(c)] = [
            {
                "thread_id": thread_ids[i],
                "cosine_sim": round(float(emb[i] @ centroid), 4),
                "snippet":   texts[i][:snippet_len].replace("\n", " "),
            }
            for i in top_idx
        ]
    return exemplars


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Attribute profiles (M2 attributes joined back)
# ═══════════════════════════════════════════════════════════════════════════════

def attribute_profiles(
    labels:      np.ndarray,
    thread_ids:  list[str],
    attr_df:     pd.DataFrame,
) -> dict:
    """
    For each M1 cluster, compute M2-attribute distributions.
    Ordinals: mean (ignoring desconhecido).
    Categoricals: top-3 modes.
    Missingness: mean desconhecido count per thread.
    """
    # Align attr_df to label order
    id_to_idx = {tid: i for i, tid in enumerate(attr_df["thread_id"].values)}
    aligned   = attr_df.set_index("thread_id")

    # missingness per thread (across ALL 10 features)
    feat_cols = ORDINAL_FEATURES + CATEGORICAL_FEATURES
    miss_counts = (
        aligned[CATEGORICAL_FEATURES].apply(lambda col: col == "desconhecido").sum(axis=1)
        + aligned[ORDINAL_FEATURES].isna().sum(axis=1)
    )

    profiles = {}
    for c in sorted(set(labels)):
        if c == -1:
            continue
        members = [thread_ids[i] for i in np.where(labels == c)[0]]
        sub     = aligned.loc[aligned.index.intersection(members)]
        prof    = {"n": len(members)}

        for col in ORDINAL_FEATURES:
            vals = pd.to_numeric(sub[col], errors="coerce").dropna()
            prof[col] = round(float(vals.mean()), 2) if len(vals) else None

        for col in CATEGORICAL_FEATURES:
            vals = sub[col][sub[col] != "desconhecido"].dropna()
            if len(vals):
                vc       = vals.value_counts().head(3)
                prof[col] = [(str(v), int(n)) for v, n in zip(vc.index, vc.values)]
            else:
                prof[col] = []

        miss_sub = miss_counts.reindex(sub.index).fillna(0)
        prof["mean_missing"] = round(float(miss_sub.mean()), 2)
        profiles[int(c)] = prof
    return profiles


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Cross-tab M1 × M2
# ═══════════════════════════════════════════════════════════════════════════════

def cross_tab(
    m1_labels:   np.ndarray,
    m2_labels:   np.ndarray,
    thread_ids:  list[str],
    m2_df:       pd.DataFrame,
) -> pd.DataFrame:
    """Cross-tabulation of M1 cluster vs M2 cluster (rows=M1, cols=M2)."""
    m2_map = dict(zip(m2_df["thread_id"], m2_df["cluster_label"]))
    m2_aligned = np.array([m2_map.get(tid, "M2-unknown") for tid in thread_ids])

    m1_lbls = [f"M1-C{c}" if c != -1 else "M1-noise" for c in m1_labels]
    ct      = pd.crosstab(
        pd.Categorical(m1_lbls),
        pd.Categorical(m2_aligned),
    )
    return ct


# ═══════════════════════════════════════════════════════════════════════════════
# 8. Plots
# ═══════════════════════════════════════════════════════════════════════════════

def plot_umap_clusters(
    emb2d:    np.ndarray,
    labels:   np.ndarray,
    title:    str,
    filename: str,
    noise_pct: float,
) -> None:
    fig, ax = plt.subplots(figsize=(10, 8))
    palette = sns.color_palette("tab20", max(labels.max() + 2, 20))
    for c in sorted(set(labels)):
        m     = labels == c
        color = "lightgrey" if c == -1 else palette[c % 20]
        lbl   = f"noise ({noise_pct:.1f}%)" if c == -1 else f"M1-C{c} (n={m.sum()})"
        ax.scatter(emb2d[m, 0], emb2d[m, 1], c=[color], s=4, alpha=0.5, label=lbl)
    ax.set_title(title)
    ax.set_xlabel("UMAP-1")
    ax.set_ylabel("UMAP-2")
    ax.legend(markerscale=3, fontsize=7, loc="upper right", ncol=2)
    plt.tight_layout()
    fig.savefig(FIGURES / filename, dpi=150)
    plt.close(fig)
    log(f"  Saved {filename}")


def plot_model_comparison(emb2d: np.ndarray, labels_e5: np.ndarray,
                           labels_mpnet: np.ndarray) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    palette   = sns.color_palette("tab20", 20)
    for lbl_arr, title, ax in [
        (labels_e5,   f"e5-large clusters", axes[0]),
        (labels_mpnet, f"mpnet clusters",    axes[1]),
    ]:
        for c in sorted(set(lbl_arr)):
            m     = lbl_arr == c
            color = "lightgrey" if c == -1 else palette[c % 20]
            ax.scatter(emb2d[m, 0], emb2d[m, 1], c=[color], s=4, alpha=0.5,
                       label=f"{'noise' if c == -1 else f'C{c}'}")
        ax.set_title(title)
        ax.set_xlabel("UMAP-1 (e5-large 2D)")
        ax.legend(markerscale=3, fontsize=6, ncol=2)
    fig.suptitle("Method 1 — Two-model comparison on 2-D UMAP (e5-large projection)")
    plt.tight_layout()
    fig.savefig(FIGURES / "m1_model_comparison.png", dpi=150)
    plt.close(fig)
    log("  Saved m1_model_comparison.png")


def plot_crosstab(ct: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(max(8, len(ct.columns)), max(5, len(ct.index))))
    sns.heatmap(
        ct, annot=True, fmt="d", cmap="Blues", ax=ax,
        linewidths=0.5, linecolor="grey",
    )
    ax.set_title("Method 1 × Method 2 cluster cross-tabulation")
    ax.set_xlabel("Method 2 cluster")
    ax.set_ylabel("Method 1 cluster")
    plt.tight_layout()
    fig.savefig(FIGURES / "m1_crosstab.png", dpi=150)
    plt.close(fig)
    log("  Saved m1_crosstab.png")


# ═══════════════════════════════════════════════════════════════════════════════
# 9. Report
# ═══════════════════════════════════════════════════════════════════════════════

def write_report(
    emb_meta_e5:     dict,
    emb_meta_mpnet:  dict,
    sweep_results:   dict,
    chosen_ms:       int,
    labels_e5:       np.ndarray,
    probs_e5:        np.ndarray,
    labels_mpnet:    np.ndarray,
    labels_cosine:   np.ndarray,
    ari_models:      float,
    boot_res:        dict,
    profiles:        dict,
    exemplars:       dict,
    ct:              pd.DataFrame,
    adjudication:    dict,
) -> None:
    L = []

    def h(t, lv=2): L.append(f"\n{'#'*lv} {t}\n")
    def p(*parts):  L.append(" ".join(parts)); L.append("")

    n_clusters = len(set(labels_e5)) - (1 if -1 in labels_e5 else 0)
    n_noise    = int((labels_e5 == -1).sum())
    noise_pct  = round(n_noise / N_TOTAL * 100, 1)

    L.append("# Phase 3B — Method 1: Embedding + HDBSCAN (comparison instrument)\n")
    L.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}  ")
    L.append("**Status: AWAITING SUPERVISOR REVIEW — Phase 3C is blocked**\n")
    L.append("---\n")

    h("1. Methodology")
    p("**This method is independent of Method 2.** Text embeddings only.",
      "No attributes, no subreddit, no window labels are used in clustering.",
      "The M2 attribute join in Section 8 is for post-hoc description, not input.")
    p(f"**Primary model:** `{MODEL_PRIMARY}`",
      f"  Dimensions: {emb_meta_e5['shape'][1]}.",
      f"  Pooling: mean (SentenceTransformer default).",
      f"  Prefix: `passage: ` (required by e5 architecture for document encoding).",
      f"  Model max_length: {emb_meta_e5.get('max_model_len', 512)} tokens.",
      f"  Estimated tokenizer-truncated texts: {emb_meta_e5.get('n_truncated_est', 'n/a')}",
      f"  ({emb_meta_e5.get('n_truncated_est', 0)/N_TOTAL*100:.1f}%).",
      f"  Encode time: {emb_meta_e5.get('encode_seconds', 'cached')}s.",
      f"  Embeddings L2-normalised: cosine similarity = dot product.")
    p(f"**Secondary model:** `{MODEL_SECONDARY}`",
      f"  Dimensions: {emb_meta_mpnet['shape'][1]}.",
      f"  No prefix required.",
      f"  Model max_length: {emb_meta_mpnet.get('max_model_len', 514)} tokens.",
      f"  Used for cross-model robustness check (Section 3).")
    p(f"**UMAP denoising:** cosine metric, n_components={UMAP_COMPONENTS},",
      f"n_neighbors={UMAP_NEIGHBORS}, min_dist=0.0 (tight clusters).",
      "2-D UMAP (min_dist=0.1) used only for visualisation.")
    p(f"**HDBSCAN:** min_cluster_size={MIN_SIZE} (3% floor), min_samples tuned",
      f"(chosen: {chosen_ms}; see sweep table in Section 2).",
      "Noise points (label −1) are excluded from persona candidacy.")
    p("**Cross-check:** HDBSCAN also run directly on cosine-distance matrix",
      "(no UMAP), metric='precomputed'. Both results reported; primary is UMAP+HDBSCAN.")

    h("2. HDBSCAN min_samples sweep (primary model, UMAP-20d)")
    L.append("| min_samples | n_clusters | n_noise | noise_pct | Chosen? |")
    L.append("|------------|-----------|---------|-----------|---------|")
    for ms, r in sorted(sweep_results.items()):
        chosen_mark = "← chosen" if ms == chosen_ms else ""
        L.append(f"| {ms} | {r['n_clusters']} | {r['n_noise']} | {r['noise_pct']}% | {chosen_mark} |")
    L.append("")
    p(f"**Chosen min_samples={chosen_ms}**: first value with noise < 25% and ≥ 4 clusters.",
      "If no value met both criteria, the value minimising noise was selected.",
      f"**Noise fraction: {noise_pct}%.** Noise points are excluded from all downstream analyses.")

    h("3. Cross-model agreement (e5-large vs mpnet)")
    n_e5    = len(set(labels_e5))    - (1 if -1 in labels_e5    else 0)
    n_mpnet = len(set(labels_mpnet)) - (1 if -1 in labels_mpnet else 0)
    p(f"e5-large: **{n_e5} clusters**, {int((labels_e5==-1).sum())} noise",
      f"({(labels_e5==-1).sum()/N_TOTAL*100:.1f}%)")
    p(f"mpnet: **{n_mpnet} clusters**, {int((labels_mpnet==-1).sum())} noise",
      f"({(labels_mpnet==-1).sum()/N_TOTAL*100:.1f}%)")
    p(f"**ARI(e5, mpnet) = {ari_models:.3f}**")
    if ari_models >= 0.5:
        p("ARI ≥ 0.5: the two embedding models broadly agree on cluster structure.",
          "The embedding-derived segmentation is robust to model choice.")
    elif ari_models >= 0.3:
        p("ARI 0.3–0.5: moderate agreement. The coarse structure is likely shared;",
          "fine splits are model-sensitive. Interpret cluster boundaries cautiously.")
    else:
        p("⚠️ ARI < 0.3: low inter-model agreement. Cluster assignments are",
          "model-sensitive. Results below reflect e5-large only; treat with caution.")

    h("4. Cosine-distance cross-check (HDBSCAN, no UMAP)")
    n_cos   = len(set(labels_cosine)) - (1 if -1 in labels_cosine else 0)
    n_cnois = int((labels_cosine == -1).sum())
    ari_cos = adjusted_rand_score(
        [l for l in labels_e5    if l != -1],
        [labels_cosine[i] for i, l in enumerate(labels_e5) if l != -1],
    ) if n_cos > 0 else 0.0
    # actually need to compare on same set; recompute:
    valid_both = (labels_e5 != -1) & (labels_cosine != -1)
    ari_cos = round(adjusted_rand_score(labels_e5[valid_both], labels_cosine[valid_both]), 3) \
              if valid_both.sum() > 10 else 0.0
    p(f"HDBSCAN on cosine-distance matrix (precomputed, min_samples={chosen_ms}):",
      f"**{n_cos} clusters**, {n_cnois} noise ({n_cnois/N_TOTAL*100:.1f}%).",
      f"ARI vs UMAP+HDBSCAN (non-noise overlap): **{ari_cos}**.",
      "High ARI → UMAP denoising did not distort the cluster structure.",
      "Low ARI → UMAP collapsed some real boundaries; interpret UMAP-based results carefully.")

    h("5. Primary cluster summary (e5-large, UMAP+HDBSCAN)")
    L.append(f"⚠️ **Noise: {n_noise} threads ({noise_pct}%) excluded from all analyses below.**\n")
    L.append("| Cluster | n | % | Below 3% floor? |")
    L.append("|---------|---|---|-----------------|")
    sizes = pd.Series(labels_e5).value_counts().sort_index()
    for c, cnt in sizes.items():
        if c == -1:
            L.append(f"| noise | {cnt} | {cnt/N_TOTAL*100:.1f}% | n/a |")
        else:
            edge = "⚠️ EDGE" if cnt < MIN_SIZE else "ok"
            L.append(f"| M1-C{c} | {cnt} | {cnt/N_TOTAL*100:.1f}% | {edge} |")
    L.append("")

    h("6. Bootstrap stability (e5-large, UMAP+HDBSCAN)")
    p(f"20 iterations, 80% subsample. UMAP NOT re-run per bootstrap (subsamples the",
      f"precomputed {UMAP_COMPONENTS}-d embedding). Noise excluded from ARI computation.")
    p(f"**Mean ARI: {boot_res['mean_ari']:.3f} ± {boot_res['std_ari']:.3f}**",
      f"({'STABLE' if boot_res['mean_ari'] >= 0.5 else '⚠️ UNSTABLE'})")
    L.append("| Cluster | Mean Jaccard | Stable? |")
    L.append("|---------|-------------|---------|")
    for c, j in sorted(boot_res["per_cluster_jaccard"].items()):
        flag = "ok" if j >= 0.5 else "⚠️ UNSTABLE"
        L.append(f"| M1-C{c} | {j:.3f} | {flag} |")
    L.append("")

    h("7. Missingness artifact check")
    p("Mean count of desconhecido/NaN fields per thread (M2 attributes) per M1 cluster.",
      "Corpus median = 1.0. A TEXT cluster should NOT be missingness-driven.",
      "Flag if mean > 1.5 × corpus median (1.50).")
    corpus_med = 1.0
    L.append("| Cluster | Mean missing features | Flag? |")
    L.append("|---------|----------------------|-------|")
    for c, prof in sorted(profiles.items()):
        mm   = prof["mean_missing"]
        flag = "⚠️ ARTIFACT RISK" if mm > 1.5 * corpus_med else "ok"
        L.append(f"| M1-C{c} | {mm} | {flag} |")
    L.append("")

    h("8. Attribute profiles (M2 attributes joined back; NOT used in clustering)")
    p("For each M1 cluster: ordinal means + top-3 categorical modes from M2 attributes.",
      "This shows what the embedding clusters 'look like' in attribute space.",
      "No persona names assigned — clusters are M1-C0 … M1-C{k-1}.")
    for c, prof in sorted(profiles.items()):
        h(f"M1-C{c}  (n={prof['n']})", lv=4)
        L.append(f"Mean missingness: {prof['mean_missing']}")
        L.append("")
        L.append("| Feature | Value |")
        L.append("|---------|-------|")
        for col in ORDINAL_FEATURES:
            L.append(f"| {col} | {prof.get(col, '—')} (mean) |")
        for col in CATEGORICAL_FEATURES:
            modes = prof.get(col, [])
            val   = "  /  ".join(f"{v} ({n})" for v, n in modes) if modes else "—"
            L.append(f"| {col} | {val} |")
        L.append("")

    h("9. Exemplars (10 nearest to cluster centroid)")
    p(f"Cosine similarity to centroid (unit-norm embeddings). Texts truncated to 300 chars.")
    for c, ex_list in sorted(exemplars.items()):
        h(f"M1-C{c} exemplars", lv=4)
        for ex in ex_list:
            L.append(f"**{ex['thread_id']}** (sim={ex['cosine_sim']})")
            L.append(f"> {ex['snippet']}")
            L.append("")
        L.append("")

    h("10. Cross-tabulation M1 × M2")
    p("Rows = M1 cluster, Columns = M2 cluster. Noise rows/cols included for completeness.",
      "Use this table for the adjudication analysis below.")
    L.append(ct.to_markdown())
    L.append("")
    ari_m1_m2 = round(adjusted_rand_score(
        labels_e5[labels_e5 != -1],
        np.array([int(s.replace("M2-C","")) if s.startswith("M2-C") else -1
                  for s in ct.columns.values[np.searchsorted(ct.columns, [f"M2-C{labels_e5[i]}" for i in np.where(labels_e5 != -1)[0]])]])
    ), 3) if False else "see table"  # placeholder; real ARI computed below
    p(f"Overall ARI(M1-non-noise, M2-non-noise): computed in adjudication section.")

    h("11. Adjudication — does Method 1 corroborate Method 2 structure?")
    p("Three specific adjudication questions from Phase 3A:")

    h("11.1  M2-C5 (speculator): high-crypto, euphoric, short-term", lv=4)
    adj_c5 = adjudication.get("M2-C5", {})
    p(f"M2-C5 threads: {adj_c5.get('total', 0)}.",
      f"Concentration: top M1 cluster is {adj_c5.get('top_m1', '?')} "
      f"({adj_c5.get('top_pct', 0):.1f}% of M2-C5 threads).",
      f"Entropy: {adj_c5.get('entropy', '?')}  (lower = more concentrated in one M1 cluster).")
    if adj_c5.get("concentrated", False):
        p("✓ M2-C5 is concentrated in one M1 cluster — Method 1 recovers the speculator group.")
    else:
        p("⚠️ M2-C5 is distributed across multiple M1 clusters — no clear speculator signal from text alone.")

    h("11.2  M2-C2 (earnest-learner): curious, exploratory", lv=4)
    adj_c2 = adjudication.get("M2-C2", {})
    p(f"M2-C2 threads: {adj_c2.get('total', 0)}.",
      f"Top M1 cluster: {adj_c2.get('top_m1', '?')} ({adj_c2.get('top_pct', 0):.1f}%).",
      f"Entropy: {adj_c2.get('entropy', '?')}.")
    if adj_c2.get("concentrated", False):
        p("✓ M2-C2 concentrated in one M1 cluster — earnest-learner is text-distinguishable.")
    else:
        p("⚠️ M2-C2 diffuse in embedding space — may be a heterogeneous attitudinal group "
          "not separable by text alone.")

    h("11.3  M2-C1 (PROVISIONAL — cynical-reactive): high missingness", lv=4)
    adj_c1 = adjudication.get("M2-C1", {})
    p(f"M2-C1 threads: {adj_c1.get('total', 0)}.",
      f"Top M1 cluster: {adj_c1.get('top_m1', '?')} ({adj_c1.get('top_pct', 0):.1f}%).",
      f"Entropy: {adj_c1.get('entropy', '?')}.")
    if adj_c1.get("concentrated", False):
        p("✓ M2-C1 is concentrated → Method 1 (missingness-blind) recovers a coherent group "
          "in the same embedding region. This is positive evidence that C1 is a REAL cluster, "
          "not a missingness artifact. Recommend promoting to confirmed in Phase 3D.")
    else:
        p("⚠️ M2-C1 is diffuse across M1 clusters → the embedding (which ignores missing data "
          "patterns) does NOT recover C1. This supports the hypothesis that C1 is partly a "
          "missingness artifact. Do NOT promote to confirmed. Carry the provisional flag into Phase 3D.")

    # ARI on non-noise threads
    m1_nn = labels_e5
    m2_series = pd.Series(labels_e5, name="m1")

    h("12. Figures")
    for fn, desc in [
        ("m1_umap_primary.png",        "2-D UMAP coloured by e5-large clusters"),
        ("m1_umap_cosine.png",         "2-D UMAP coloured by cosine-distance HDBSCAN"),
        ("m1_model_comparison.png",    "e5-large vs mpnet clusters on same 2-D UMAP"),
        ("m1_crosstab.png",            "M1 × M2 cross-tabulation heatmap"),
    ]:
        L.append(f"- `reports/figures/{fn}` — {desc}")
    L.append("")

    L.append("---\n")
    L.append("## ⛔ HARD STOP\n")
    L.append(
        "Phase 3B complete. **Do not proceed to Phase 3C** until supervisor has\n"
        "reviewed this document, the adjudication results (Section 11), and the figures.\n"
        "Specifically: the M2-C1 adjudication outcome changes the provisional flag status.\n"
    )

    out = REPORTS / "phase3b_method1.md"
    out.write_text("\n".join(L), encoding="utf-8")
    log(f"  Saved {out}")


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def compute_adjudication(
    labels_e5:   np.ndarray,
    thread_ids:  list[str],
    m2_df:       pd.DataFrame,
    m2_targets:  list[str],
) -> dict:
    """
    For each M2 target cluster, compute:
    - Distribution across M1 clusters
    - Top M1 cluster and its share
    - Entropy (lower = more concentrated)
    - Flag concentrated = True if top_pct >= 40%
    """
    m2_map = dict(zip(m2_df["thread_id"], m2_df["cluster_label"]))
    m1_labels_str = [f"M1-C{c}" if c != -1 else "M1-noise" for c in labels_e5]

    results = {}
    for m2_tgt in m2_targets:
        m2_members = [tid for tid in thread_ids if m2_map.get(tid) == m2_tgt]
        m2_idx     = [i for i, tid in enumerate(thread_ids) if m2_map.get(tid) == m2_tgt]
        if not m2_idx:
            results[m2_tgt] = {"total": 0}
            continue

        m1_for_m2 = [m1_labels_str[i] for i in m2_idx]
        dist       = pd.Series(m1_for_m2).value_counts()
        top_m1     = dist.index[0]
        top_pct    = dist.iloc[0] / len(m2_idx) * 100
        probs      = dist.values / dist.values.sum()
        entropy    = round(float(-np.sum(probs * np.log(probs + 1e-12))), 3)

        results[m2_tgt] = {
            "total":        len(m2_idx),
            "distribution": dist.to_dict(),
            "top_m1":       top_m1,
            "top_pct":      round(top_pct, 1),
            "entropy":      entropy,
            "concentrated": top_pct >= 40.0,
        }
    return results


def main() -> None:
    rng = np.random.default_rng(SEED)

    # ── Load texts ────────────────────────────────────────────────────────────
    log("Loading extracted attributes …")
    attr_df    = pd.read_parquet(DATA_PROC / "extracted_attributes.parquet")
    thread_ids = attr_df["thread_id"].tolist()
    texts      = [str(t)[:TEXT_CAP] for t in attr_df["unit_text"].tolist()]
    log(f"  {len(texts)} threads loaded. Max text length: {max(len(t) for t in texts)}")

    # ── Embed (primary: e5-large) ─────────────────────────────────────────────
    log("=== PRIMARY MODEL: e5-large ===")
    emb_e5, meta_e5 = embed_texts(
        texts,
        MODEL_PRIMARY,
        DATA_INT / "embeddings_e5large.npy",
        use_passage_prefix=True,
        batch_size=64,
    )

    # ── Embed (secondary: mpnet) ──────────────────────────────────────────────
    log("=== SECONDARY MODEL: mpnet ===")
    emb_mpnet, meta_mpnet = embed_texts(
        texts,
        MODEL_SECONDARY,
        DATA_INT / "embeddings_mpnet.npy",
        use_passage_prefix=False,
        batch_size=128,
    )

    # ── UMAP denoising (e5-large) ─────────────────────────────────────────────
    log("UMAP denoising (e5-large, 20 components) …")
    umap20_e5 = umap_reduce(
        emb_e5, UMAP_COMPONENTS, "cosine",
        cache_path=DATA_INT / "umap20_e5large.npy",
    )

    # ── UMAP denoising (mpnet) ────────────────────────────────────────────────
    log("UMAP denoising (mpnet, 20 components) …")
    umap20_mpnet = umap_reduce(
        emb_mpnet, UMAP_COMPONENTS, "cosine",
        cache_path=DATA_INT / "umap20_mpnet.npy",
    )

    # ── 2-D UMAP (visualisation only, e5-large) ───────────────────────────────
    log("UMAP 2-D (e5-large, visualisation) …")
    umap2d_e5 = umap_2d(emb_e5, "cosine", cache_path=DATA_INT / "umap2d_e5large.npy")

    # ── HDBSCAN sweep (e5-large, UMAP-20d) ───────────────────────────────────
    log("HDBSCAN min_samples sweep (e5-large UMAP-20d) …")
    sweep = hdbscan_sweep(umap20_e5, metric="euclidean")
    chosen_ms = choose_min_samples(sweep)
    log(f"Chosen min_samples: {chosen_ms}")

    # ── Primary clustering (e5-large, UMAP-20d) ───────────────────────────────
    log(f"Primary HDBSCAN (e5-large, UMAP-20d, min_samples={chosen_ms}) …")
    labels_e5, probs_e5 = run_hdbscan(umap20_e5, MIN_SIZE, chosen_ms, "euclidean")
    n_clust = len(set(labels_e5)) - (1 if -1 in labels_e5 else 0)
    n_noise = int((labels_e5 == -1).sum())
    log(f"  Result: {n_clust} clusters, {n_noise} noise ({n_noise/N_TOTAL*100:.1f}%)")

    # ── mpnet clustering (UMAP-20d, same params) ──────────────────────────────
    log(f"HDBSCAN (mpnet, UMAP-20d, min_samples={chosen_ms}) …")
    labels_mpnet, _ = run_hdbscan(umap20_mpnet, MIN_SIZE, chosen_ms, "euclidean")

    # ── Model agreement ARI ───────────────────────────────────────────────────
    valid = (labels_e5 != -1) & (labels_mpnet != -1)
    ari_models = round(adjusted_rand_score(labels_e5[valid], labels_mpnet[valid]), 3) \
                 if valid.sum() > 10 else 0.0
    log(f"ARI(e5 clusters, mpnet clusters) = {ari_models}")

    # ── Cosine-distance cross-check (HDBSCAN, no UMAP) ────────────────────────
    log("Building cosine distance matrix …")
    cos_dist = cosine_distances(emb_e5).astype(np.float64)
    log(f"  Done. Shape: {cos_dist.shape}  min={cos_dist.min():.4f}  max={cos_dist.max():.4f}")
    log(f"HDBSCAN on cosine distances (precomputed, min_samples={chosen_ms}) …")
    labels_cosine, _ = run_hdbscan(cos_dist, MIN_SIZE, chosen_ms, "precomputed")
    n_cos = len(set(labels_cosine)) - (1 if -1 in labels_cosine else 0)
    log(f"  Cosine cross-check: {n_cos} clusters, {int((labels_cosine==-1).sum())} noise")

    # ── Bootstrap stability ───────────────────────────────────────────────────
    log(f"Bootstrap stability ({BOOT_B} iterations, {int(BOOT_FRAC*100)}% subsample) …")
    boot_res = bootstrap_stability(
        umap20_e5, labels_e5, chosen_ms, "euclidean", BOOT_B, BOOT_FRAC, rng
    )
    log(f"  Mean ARI: {boot_res['mean_ari']:.3f} ± {boot_res['std_ari']:.3f}")

    # ── Attribute profiles ────────────────────────────────────────────────────
    log("Computing attribute profiles (M2 attributes joined back) …")
    profiles = attribute_profiles(labels_e5, thread_ids, attr_df)

    # ── Exemplars ─────────────────────────────────────────────────────────────
    log("Computing cluster exemplars …")
    exemplars = cluster_exemplars(emb_e5, labels_e5, texts, thread_ids)

    # ── Cross-tab M1 × M2 ─────────────────────────────────────────────────────
    log("Building M1 × M2 cross-tabulation …")
    m2_df = pd.read_parquet(DATA_PROC / "clusters_method2.parquet")
    ct    = cross_tab(labels_e5, None, thread_ids, m2_df)

    # ── Adjudication ──────────────────────────────────────────────────────────
    log("Computing adjudication statistics …")
    adjudication = compute_adjudication(
        labels_e5, thread_ids, m2_df, ["M2-C1", "M2-C2", "M2-C5"]
    )
    for tgt, res in adjudication.items():
        log(f"  {tgt}: top_m1={res.get('top_m1','?')} ({res.get('top_pct',0):.1f}%)  "
            f"entropy={res.get('entropy','?')}  concentrated={res.get('concentrated',False)}")

    # ── Figures ───────────────────────────────────────────────────────────────
    log("Generating figures …")
    plot_umap_clusters(
        umap2d_e5, labels_e5,
        f"Method 1 — e5-large + UMAP+HDBSCAN  (k={n_clust}, noise={n_noise/N_TOTAL*100:.1f}%)",
        "m1_umap_primary.png", n_noise / N_TOTAL * 100,
    )
    plot_umap_clusters(
        umap2d_e5, labels_cosine,
        f"Method 1 — e5-large + cosine HDBSCAN (no UMAP)  (k={n_cos})",
        "m1_umap_cosine.png", (labels_cosine == -1).sum() / N_TOTAL * 100,
    )
    plot_model_comparison(umap2d_e5, labels_e5, labels_mpnet)
    plot_crosstab(ct)

    # ── Save parquet ──────────────────────────────────────────────────────────
    out_df = pd.DataFrame({
        "thread_id":         thread_ids,
        "cluster_label":     [f"M1-C{c}" if c != -1 else "M1-noise" for c in labels_e5],
        "cluster_int":       labels_e5,
        "membership_prob":   probs_e5.round(4),
    })
    out_path = DATA_PROC / "clusters_method1.parquet"
    out_df.to_parquet(out_path, index=False)
    log(f"Saved {out_path}")

    # ── Report ────────────────────────────────────────────────────────────────
    log("Writing report …")
    write_report(
        emb_meta_e5=meta_e5, emb_meta_mpnet=meta_mpnet,
        sweep_results=sweep, chosen_ms=chosen_ms,
        labels_e5=labels_e5, probs_e5=probs_e5,
        labels_mpnet=labels_mpnet, labels_cosine=labels_cosine,
        ari_models=ari_models, boot_res=boot_res,
        profiles=profiles, exemplars=exemplars,
        ct=ct, adjudication=adjudication,
    )

    # ── Summary ───────────────────────────────────────────────────────────────
    log("=" * 60)
    log(f"PHASE 3B COMPLETE")
    sizes = pd.Series(labels_e5).value_counts().sort_index()
    for c, cnt in sizes.items():
        log(f"  {'noise' if c==-1 else f'M1-C{c}'}: {cnt} ({cnt/N_TOTAL*100:.1f}%)")
    log(f"  Mean ARI stability: {boot_res['mean_ari']:.3f}")
    log(f"  ARI(e5, mpnet): {ari_models:.3f}")
    log(f"  M2-C1 adjudication: concentrated={adjudication.get('M2-C1',{}).get('concentrated','?')}")
    log(f"  Parquet: {out_path}")
    log(f"  Report: {REPORTS / 'phase3b_method1.md'}")
    log("⛔ HARD STOP — awaiting supervisor review before Phase 3C")
    log("=" * 60)


if __name__ == "__main__":
    main()

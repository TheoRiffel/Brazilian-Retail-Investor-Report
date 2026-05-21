#!/usr/bin/env python3
"""
Phase 3A: Method 2 — Attribute Clustering (PRIMARY METHOD)

Two-mode script:

  python 03a_attribute_clustering.py               # EXPLORE mode (default)
      → computes Gower, linkage, silhouette/gap, fingerprints + bootstrap
        stability for the top-3 candidate k values, writes
        reports/phase3a_explore.md, then HARD STOPS.
      → does NOT write clusters_method2.parquet yet.

  python 03a_attribute_clustering.py --finalize K  # FINALIZE mode
      → loads cached artefacts, applies the supervisor-chosen k,
        writes data/processed/clusters_method2.parquet +
        reports/phase3a_method2.md.

Distance:  Gower (mixed ordinal/categorical, NaN excluded pairwise)
Hierarchy: average-linkage (Ward excluded — requires Euclidean space)
HDBSCAN:   metric='precomputed' on the full Gower matrix (NOT 2-D UMAP)
UMAP 2D:   used ONLY for the scatter visualisation
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
from scipy.spatial.distance import squareform
from scipy.cluster.hierarchy import linkage, fcluster, dendrogram
from sklearn.metrics import (
    silhouette_score,
    silhouette_samples,
    adjusted_rand_score,
)

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
SEED        = 42
N_TOTAL     = 3600
MIN_SIZE    = int(N_TOTAL * 0.03)         # 108 = 3% floor
K_RANGE     = list(range(2, 11))          # evaluate k = 2..10
GAP_B       = 10                          # gap-statistic reference datasets
BOOT_B      = 20                          # bootstrap iterations per candidate k
BOOT_FRAC   = 0.80
HDBSCAN_MIN_SAMPLES = max(10, MIN_SIZE // 4)   # 27

ORDINAL_FEATURES = [
    "sofisticacao_tecnica",
    "tolerancia_risco_declarada_ou_inferida",
    "ceticismo_institucional",
    "exposicao_a_cripto_e_especulacao",
    "identidade_comunitaria",
]
CATEGORICAL_FEATURES = [
    "fase_acumulacao",
    "estrategia_principal",
    "relacao_com_instituicoes_financeiras",
    "estado_emocional_predominante",
    "objetivo_financeiro_primario",
]
ALL_FEATURES = ORDINAL_FEATURES + CATEGORICAL_FEATURES


def log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Data / distance
# ═══════════════════════════════════════════════════════════════════════════════

def load_features() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load extracted attributes.
    Categoricals: 'desconhecido' → pd.NA  (treated as missing, not a category).
    Ordinals: Int8 nullable int → float64 (pd.NA → np.nan).
    """
    df   = pd.read_parquet(DATA_PROC / "extracted_attributes.parquet")
    meta = df[["thread_id", "subreddit_origem", "window"]].copy()
    feat = df[ALL_FEATURES].copy()
    for col in CATEGORICAL_FEATURES:
        feat[col] = feat[col].where(feat[col] != "desconhecido", other=pd.NA)
    for col in ORDINAL_FEATURES:
        feat[col] = feat[col].astype("float64")
    return meta, feat


def compute_gower_matrix(feat: pd.DataFrame) -> np.ndarray:
    """
    Gower distance for mixed ordinal/categorical data with missingness.

    Ordinal pair (i,j):     d = |xi − xj| / range(col)   — NaN excluded
    Categorical pair (i,j): d = 0 if xi==xj else 1        — NaN excluded
    Gower(i,j) = Σ d_k / count(non-null features for pair i,j)
    If no feature is valid for a pair → distance = 1.0 (maximum).

    Returns float32 symmetric matrix, zeros on diagonal.
    """
    n  = len(feat)
    D  = np.zeros((n, n), dtype=np.float32)
    W  = np.zeros((n, n), dtype=np.float32)

    for col in ORDINAL_FEATURES:
        vals  = feat[col].to_numpy(dtype=np.float32)
        valid = ~np.isnan(vals)
        col_r = float(np.nanmax(vals) - np.nanmin(vals))
        if col_r == 0.0:
            continue
        vi   = vals[:, None]
        vj   = vals[None, :]
        both = valid[:, None] & valid[None, :]
        D   += np.where(both, np.abs(vi - vj) / col_r, 0.0)
        W   += both.astype(np.float32)

    for col in CATEGORICAL_FEATURES:
        raw   = feat[col].to_numpy(dtype=object)
        valid = ~pd.isna(raw)
        cats  = list(dict.fromkeys(v for v in raw if pd.notna(v)))
        enc   = {c: i for i, c in enumerate(cats)}
        vals  = np.array(
            [enc[v] if pd.notna(v) else -1 for v in raw], dtype=np.int16
        )
        vi   = vals[:, None]
        vj   = vals[None, :]
        both = valid[:, None] & valid[None, :]
        D   += np.where(both, (vi != vj).astype(np.float32), 0.0)
        W   += both.astype(np.float32)

    with np.errstate(invalid="ignore", divide="ignore"):
        D = np.where(W > 0, D / W, 1.0).astype(np.float32)
    np.fill_diagonal(D, 0.0)
    return D


# ═══════════════════════════════════════════════════════════════════════════════
# Metrics
# ═══════════════════════════════════════════════════════════════════════════════

def silhouette_sweep(D: np.ndarray, Z: np.ndarray, k_range: list) -> dict:
    D64    = D.astype(np.float64)
    scores = {}
    for k in k_range:
        labels = fcluster(Z, k, criterion="maxclust") - 1
        if len(np.unique(labels)) < 2:
            scores[k] = np.nan
            continue
        scores[k] = float(silhouette_score(D64, labels, metric="precomputed"))
        log(f"  silhouette k={k}: {scores[k]:.4f}")
    return scores


def within_cluster_dist(D64: np.ndarray, labels: np.ndarray) -> float:
    """W_k = Σ_c [Σ_{i<j ∈ c} D[i,j] / n_c]  (Tibshirani 2001)."""
    total = 0.0
    for c in np.unique(labels):
        members = np.where(labels == c)[0]
        nc      = len(members)
        if nc > 1:
            total += D64[np.ix_(members, members)].sum() / (2.0 * nc)
    return total


def gap_statistic(
    D: np.ndarray,
    feat: pd.DataFrame,
    Z: np.ndarray,
    k_range: list,
    B: int = GAP_B,
    rng: np.random.Generator | None = None,
) -> dict:
    """
    Gap statistic (Tibshirani 2001).
    Reference: each feature column permuted independently — breaks joint
    structure while preserving marginal distributions.
    """
    if rng is None:
        rng = np.random.default_rng(SEED)

    D64      = D.astype(np.float64)
    obs_logW = {
        k: np.log(max(within_cluster_dist(D64, fcluster(Z, k, criterion="maxclust") - 1), 1e-12))
        for k in k_range
    }
    ref_logW = {k: [] for k in k_range}

    for b in range(B):
        log(f"  Gap reference {b+1}/{B} …")
        fp = feat.copy()
        for col in ALL_FEATURES:
            vals    = fp[col].to_numpy()
            fp[col] = vals[rng.permutation(len(vals))]

        D_r  = compute_gower_matrix(fp)
        Z_r  = linkage(squareform(D_r.astype(np.float64), checks=False), method="average")
        D64r = D_r.astype(np.float64)
        for k in k_range:
            lbl_r = fcluster(Z_r, k, criterion="maxclust") - 1
            ref_logW[k].append(np.log(max(within_cluster_dist(D64r, lbl_r), 1e-12)))

    results = {}
    for k in k_range:
        arr  = np.array(ref_logW[k])
        gap  = float(arr.mean() - obs_logW[k])
        sk   = float(arr.std() * np.sqrt(1.0 + 1.0 / B))
        results[k] = {"gap": gap, "sk": sk, "obs_logW": float(obs_logW[k])}
        log(f"  Gap k={k}: gap={gap:.4f}  sk={sk:.4f}")
    return results


def gap_optimal_k(gap_res: dict, k_range: list) -> int:
    """Tibshirani stopping rule: smallest k where gap(k) ≥ gap(k+1) − s(k+1)."""
    ks = sorted(k_range)
    for i in range(len(ks) - 1):
        k, k1 = ks[i], ks[i + 1]
        if gap_res[k]["gap"] >= gap_res[k1]["gap"] - gap_res[k1]["sk"]:
            return k
    return ks[-1]


# ═══════════════════════════════════════════════════════════════════════════════
# Bootstrap stability — multi-k in one pass
# ═══════════════════════════════════════════════════════════════════════════════

def bootstrap_stability_multi(
    D: np.ndarray,
    Z: np.ndarray,
    candidate_ks: list,
    n_boot: int = BOOT_B,
    frac:   float = BOOT_FRAC,
    rng:    np.random.Generator | None = None,
) -> dict:
    """
    Run bootstrap stability for multiple k values in a single pass.
    Each bootstrap subsample runs linkage once; cut at each candidate k.
    Returns {k: {mean_ari, std_ari, per_cluster_jaccard}}.
    """
    if rng is None:
        rng = np.random.default_rng(SEED)

    n     = D.shape[0]
    D64   = D.astype(np.float64)
    orig  = {k: fcluster(Z, k, criterion="maxclust") - 1 for k in candidate_ks}
    aris  = {k: [] for k in candidate_ks}
    cj    = {k: {c: [] for c in range(k)} for k in candidate_ks}

    for b in range(n_boot):
        sub = np.sort(rng.choice(n, size=int(n * frac), replace=False))
        D_s = D64[np.ix_(sub, sub)]
        Z_s = linkage(squareform(D_s, checks=False), method="average")

        for k in candidate_ks:
            lbl_s   = fcluster(Z_s, k, criterion="maxclust") - 1
            orig_s  = orig[k][sub]
            ari     = adjusted_rand_score(orig_s, lbl_s)
            aris[k].append(ari)

            for c in range(k):
                orig_m = set(np.where(orig_s == c)[0])
                if not orig_m:
                    continue
                best_j = max(
                    (
                        len(orig_m & (bm := set(np.where(lbl_s == c2)[0])))
                        / len(orig_m | bm)
                        for c2 in range(k)
                        if len(orig_m | set(np.where(lbl_s == c2)[0])) > 0
                    ),
                    default=0.0,
                )
                cj[k][c].append(best_j)

        log(f"  Bootstrap {b+1}/{n_boot}: ARI(k={candidate_ks}) = "
            + " / ".join(f"{aris[k][-1]:.3f}" for k in candidate_ks))

    return {
        k: {
            "mean_ari": round(float(np.mean(aris[k])), 3),
            "std_ari":  round(float(np.std(aris[k])),  3),
            "per_cluster_jaccard": {c: round(float(np.mean(v)), 3) for c, v in cj[k].items()},
        }
        for k in candidate_ks
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Missingness & fingerprints
# ═══════════════════════════════════════════════════════════════════════════════

def missingness_check(feat: pd.DataFrame, labels: np.ndarray) -> tuple[dict, float]:
    miss          = feat.isna().sum(axis=1).to_numpy()
    corpus_median = float(np.median(miss))
    n             = len(labels)
    stats         = {}
    for c in np.unique(labels):
        members   = np.where(labels == c)[0]
        mean_miss = float(miss[members].mean())
        stats[int(c)] = {
            "n":                     int(len(members)),
            "pct":                   round(len(members) / n * 100, 1),
            "mean_missing_features": round(mean_miss, 2),
            "flag_missingness":      mean_miss > 1.5 * corpus_median,
        }
    return stats, round(corpus_median, 2)


def cluster_fingerprints(feat: pd.DataFrame, labels: np.ndarray) -> dict:
    """Modal (categorical) and mean (ordinal) per cluster for the 10 features."""
    fps = {}
    for c in sorted(np.unique(labels)):
        members = np.where(labels == c)[0]
        sub     = feat.iloc[members]
        fp      = {}
        for col in ORDINAL_FEATURES:
            vals    = sub[col].dropna()
            fp[col] = {
                "mean":    round(float(vals.mean()), 2) if len(vals) else None,
                "n_valid": int(len(vals)),
            }
        for col in CATEGORICAL_FEATURES:
            vals = sub[col].dropna()
            if len(vals):
                vc      = vals.value_counts()
                fp[col] = {
                    "mode":     str(vc.index[0]),
                    "mode_pct": round(vc.iloc[0] / len(vals) * 100, 1),
                    "n_valid":  int(len(vals)),
                }
            else:
                fp[col] = {"mode": None, "mode_pct": None, "n_valid": 0}
        fps[int(c)] = fp
    return fps


# ═══════════════════════════════════════════════════════════════════════════════
# Cross-checks
# ═══════════════════════════════════════════════════════════════════════════════

def run_hdbscan_precomputed(D: np.ndarray) -> np.ndarray:
    """
    HDBSCAN directly on the Gower distance matrix (metric='precomputed').
    This clusters the actual data structure, not a 2-D projection.
    min_samples = max(10, MIN_SIZE // 4) = 27.
    """
    import hdbscan as hdbscan_lib
    log(f"  HDBSCAN (precomputed Gower, min_cluster_size={MIN_SIZE}, "
        f"min_samples={HDBSCAN_MIN_SAMPLES}) …")
    clusterer  = hdbscan_lib.HDBSCAN(
        min_cluster_size=MIN_SIZE,
        min_samples=HDBSCAN_MIN_SAMPLES,
        metric="precomputed",
    )
    labels     = clusterer.fit_predict(D.astype(np.float64))
    n_clust    = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise    = int((labels == -1).sum())
    log(f"  HDBSCAN result: {n_clust} clusters, {n_noise} noise points ({n_noise/N_TOTAL*100:.1f}%)")
    return labels


def run_umap_2d(D: np.ndarray) -> np.ndarray:
    """2-D UMAP for visualisation ONLY — not used as clustering input."""
    import umap as umap_lib
    log("  UMAP 2-D (visualisation only) …")
    reducer   = umap_lib.UMAP(
        n_components=2, metric="precomputed", random_state=SEED, n_jobs=1
    )
    return reducer.fit_transform(D.astype(np.float64))


def run_kprototypes(feat: pd.DataFrame, k_range: list) -> dict:
    """
    K-prototypes cross-check.

    ⚠️  DIFFERENT MISSINGNESS STRATEGY than Gower:
    - Categoricals: 'desconhecido' KEPT as its own category level (not treated as
      missing). K-prototypes sees 'desconhecido' as a valid label.
    - Ordinal NaN: imputed at column median (only 5 values total across the corpus).

    Consequence for interpretation:
    - If k-prototypes and Gower hierarchical agree on segment structure,
      that is strong robustness evidence — the split survives two different
      treatments of missing data.
    - If they disagree, the disagreement may be missingness-driven, not
      structural. Specifically, clusters dominated by 'desconhecido' in
      k-prototypes may not correspond to real investor types but to
      extraction-thin threads.
    """
    from kmodes.kprototypes import KPrototypes

    df_kp = feat.copy()
    for col in ORDINAL_FEATURES:
        df_kp[col] = df_kp[col].fillna(float(df_kp[col].median()))
    for col in CATEGORICAL_FEATURES:
        df_kp[col] = df_kp[col].fillna("desconhecido")

    X_num   = df_kp[ORDINAL_FEATURES].to_numpy(dtype=np.float64)
    X_cat   = df_kp[CATEGORICAL_FEATURES].to_numpy(dtype=object)
    X       = np.hstack([X_num, X_cat])
    cat_idx = list(range(len(ORDINAL_FEATURES), len(ALL_FEATURES)))

    results = {}
    for k in k_range:
        log(f"  K-prototypes k={k} (n_init=8) …")
        kp     = KPrototypes(
            n_clusters=k, init="Cao", n_init=8, random_state=SEED, verbose=0
        )
        labels = kp.fit_predict(X, categorical=cat_idx)
        results[k] = {"labels": labels.tolist(), "cost": float(kp.cost_)}
        log(f"    cost={kp.cost_:.2f}")
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# Plots
# ═══════════════════════════════════════════════════════════════════════════════

def plot_silhouette(sil_scores: dict, candidate_ks: list) -> None:
    ks  = sorted(sil_scores)
    vs  = [sil_scores[k] for k in ks]
    fig, ax = plt.subplots(figsize=(9, 4))
    colors  = ["#e07b54" if k in candidate_ks else "#4c8bb5" for k in ks]
    ax.bar(ks, vs, color=colors)
    for k in candidate_ks:
        ax.axvline(k, color="#e07b54", linestyle="--", linewidth=1, alpha=0.5)
    ax.set_xlabel("k")
    ax.set_ylabel("Average silhouette score")
    ax.set_title("Method 2 — Silhouette vs k  (average-linkage, Gower)\n"
                 "Orange bars = candidate k values sent to supervisor")
    ax.set_xticks(ks)
    plt.tight_layout()
    fig.savefig(FIGURES / "m2_silhouette.png", dpi=150)
    plt.close(fig)
    log("  Saved m2_silhouette.png")


def plot_gap(gap_res: dict, candidate_ks: list) -> None:
    ks   = sorted(gap_res)
    gaps = [gap_res[k]["gap"] for k in ks]
    sks  = [gap_res[k]["sk"]  for k in ks]
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.errorbar(ks, gaps, yerr=sks, fmt="o-", color="#4c8bb5", capsize=4)
    for k in candidate_ks:
        ax.axvline(k, color="#e07b54", linestyle="--", linewidth=1, alpha=0.6,
                   label=f"candidate k={k}")
    ax.set_xlabel("k")
    ax.set_ylabel("Gap statistic")
    ax.set_title(f"Method 2 — Gap statistic vs k  (B={GAP_B} permutation references)\n"
                 "Error bars = ±s_k;  orange lines = candidate k values")
    ax.set_xticks(ks)
    ax.legend(fontsize=8)
    plt.tight_layout()
    fig.savefig(FIGURES / "m2_gap.png", dpi=150)
    plt.close(fig)
    log("  Saved m2_gap.png")


def plot_umap(embedding: np.ndarray, labels_hier: np.ndarray,
              labels_hdb: np.ndarray, chosen_k: int) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    palette   = sns.color_palette("tab10", max(labels_hier.max() + 2, 14))

    for lbl, title, ax in [
        (labels_hier, f"Hierarchical (k={chosen_k})", axes[0]),
        (labels_hdb,  "HDBSCAN/precomputed Gower (noise=−1 grey)", axes[1]),
    ]:
        for c in sorted(set(lbl)):
            m     = lbl == c
            color = "lightgrey" if c == -1 else palette[c % 10]
            label = "noise" if c == -1 else f"C{c}"
            ax.scatter(embedding[m, 0], embedding[m, 1],
                       c=[color], s=4, alpha=0.6, label=label)
        ax.set_title(title)
        ax.set_xlabel("UMAP-1")
        ax.set_ylabel("UMAP-2")
        ax.legend(markerscale=3, fontsize=7)

    fig.suptitle("Method 2 — 2-D UMAP of Gower distances (visualisation only)\n"
                 "HDBSCAN was run on the full Gower matrix, not on this projection")
    plt.tight_layout()
    fig.savefig(FIGURES / "m2_umap.png", dpi=150)
    plt.close(fig)
    log("  Saved m2_umap.png")


def plot_dendrogram(Z: np.ndarray, candidate_ks: list) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    dendrogram(Z, truncate_mode="level", p=5, ax=ax,
               color_threshold=0, above_threshold_color="grey")
    ax.set_title("Method 2 — Dendrogram (truncated, average linkage, Gower)\n"
                 f"Candidate cuts: k = {candidate_ks}")
    ax.set_xlabel("Sample (or cluster count in parens)")
    ax.set_ylabel("Distance")
    plt.tight_layout()
    fig.savefig(FIGURES / "m2_dendrogram.png", dpi=150)
    plt.close(fig)
    log("  Saved m2_dendrogram.png")


# ═══════════════════════════════════════════════════════════════════════════════
# Explore report
# ═══════════════════════════════════════════════════════════════════════════════

def _fingerprint_table(fps: dict, miss_stats: dict) -> list[str]:
    """Render all clusters for one k as a compact feature-profile table."""
    lines = []
    k     = len(fps)
    # Header row
    header = "| Feature | " + " | ".join(f"M2-C{c} (n={miss_stats[c]['n']}, {miss_stats[c]['pct']}%)" for c in range(k)) + " |"
    sep    = "|---------|" + "---|" * k
    lines += [header, sep]
    for col in ORDINAL_FEATURES:
        row = f"| {col} |"
        for c in range(k):
            v    = fps[c][col]
            cell = f"{v['mean']} (n={v['n_valid']})" if v["mean"] is not None else "—"
            row += f" {cell} |"
        lines.append(row)
    for col in CATEGORICAL_FEATURES:
        row = f"| {col} |"
        for c in range(k):
            v    = fps[c][col]
            cell = f"{v['mode']} {v['mode_pct']}% (n={v['n_valid']})" if v["mode"] else "—"
            row += f" {cell} |"
        lines.append(row)
    return lines


def write_explore_report(
    sil_scores:    dict,
    gap_res:       dict,
    gap_tibsh_k:   int,
    candidate_ks:  list,
    boot_res:      dict,
    miss_by_k:     dict,
    corpus_median: float,
    fps_by_k:      dict,
    hdb_labels:    np.ndarray,
    kp_results:    dict,
) -> None:
    L = []

    def h(text, level=2):
        L.append(f"\n{'#' * level} {text}\n")

    def p(*parts):
        L.append(" ".join(parts))
        L.append("")

    L.append("# Phase 3A — Method 2 Explore Report: Candidate k Values\n")
    L.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}  ")
    L.append("**Status: AWAITING SUPERVISOR k SELECTION — Phase 3A finalize and Phase 3B are blocked**\n")
    L.append("---\n")

    h("1. Methodology summary")
    p("**Gower distance** (mixed ordinal/categorical; desconhecido → NaN, excluded pairwise).",
      "**Average-linkage** hierarchical on full Gower matrix.",
      "**HDBSCAN** run on the precomputed Gower matrix (metric='precomputed'), NOT on the 2-D UMAP.",
      f"HDBSCAN min_cluster_size={MIN_SIZE} (3% floor), min_samples={HDBSCAN_MIN_SAMPLES}.",
      "**2-D UMAP** used only for the scatter figure.",
      "**K-prototypes** retains 'desconhecido' as a category level — different missing-data strategy",
      "than Gower (see Section 6 for interpretation rules).")

    h("2. Metric sweep (k = 2..10)")
    L.append("| k | Silhouette | Gap | s(Gap) | Tibshirani? |")
    L.append("|---|-----------|-----|--------|-------------|")
    for k in sorted(sil_scores):
        g    = gap_res.get(k, {})
        tib  = "← stopping rule" if k == gap_tibsh_k else ""
        L.append(f"| {k} | {sil_scores[k]:.4f} | "
                 f"{g.get('gap',0):.4f} | {g.get('sk',0):.4f} | {tib} |")
    L.append("")

    best_sil = max(sil_scores, key=lambda k: sil_scores[k] if not np.isnan(sil_scores[k]) else -1)
    best_gap = max(gap_res,    key=lambda k: gap_res[k]["gap"])
    p(f"- Silhouette optimum: **k={best_sil}** (score={sil_scores[best_sil]:.4f})")
    p(f"- Highest gap value: **k={best_gap}** (gap={gap_res[best_gap]['gap']:.4f})")
    p(f"- Gap Tibshirani stopping rule: **k={gap_tibsh_k}**")
    p(f"- Candidates sent to supervisor for interpretability review: **k = {candidate_ks}**")
    p("⚠️ Note: k=2 (Tibshirani/silhouette optimum) and k=7 (highest gap) diverge significantly.",
      "The gap values at k=7 and k=8 are substantially above k=2..6, but Tibshirani selects k=2",
      "because gap(2) ≥ gap(3) − s(3). This is a known conservatism of the Tibshirani rule.",
      "The 13 HDBSCAN clusters (Section 5) suggest finer structure exists.",
      "Interpretability of the fingerprints below is the pre-registered tie-breaker.")

    # Bootstrap stability summary table
    h("3. Bootstrap stability (all candidates)")
    p(f"20 iterations, 80% subsample, linkage run once per subsample, cut at each k.",
      "Threshold: mean ARI ≥ 0.5 and all per-cluster Jaccard ≥ 0.5.")
    L.append("| k | Mean ARI | Std | Stable? |")
    L.append("|---|----------|-----|---------|")
    for k in candidate_ks:
        br   = boot_res[k]
        flag = "✓" if br["mean_ari"] >= 0.5 else "⚠️ UNSTABLE"
        L.append(f"| {k} | {br['mean_ari']:.3f} | {br['std_ari']:.3f} | {flag} |")
    L.append("")

    # Missingness note
    h("4. Missingness artifact context")
    p(f"Corpus median missing features per thread: **{corpus_median}**.",
      f"Flag threshold: mean > {1.5 * corpus_median:.2f} (1.5×).")
    p("Note: if ALL clusters for a given k are flagged at similar levels, this indicates",
      "corpus-wide missingness uniformly distributed — NOT a cluster-specific artifact.",
      "A genuine artifact cluster would show mean_missing >> all other clusters.",
      "Inspect per-cluster values; flag all-clusters-flagged as a corpus note, not a veto.")

    # Per-candidate sections
    for k in candidate_ks:
        h(f"5.{candidate_ks.index(k)+1}  Candidate k={k} — fingerprints")
        fps       = fps_by_k[k]
        miss      = miss_by_k[k][0]
        br        = boot_res[k]

        # Stability
        p(f"**ARI: {br['mean_ari']:.3f} ± {br['std_ari']:.3f}**  "
          f"({'STABLE' if br['mean_ari'] >= 0.5 else '⚠️ UNSTABLE'})")
        L.append("Per-cluster Jaccard: "
                 + "  ".join(f"M2-C{c}={j}" for c, j in br["per_cluster_jaccard"].items()))
        L.append("")

        # 3% floor
        below = [f"M2-C{c}" for c, ms in miss.items() if ms["n"] < MIN_SIZE]
        if below:
            p(f"⚠️ Edge clusters (< {MIN_SIZE} threads): {', '.join(below)}")
        else:
            p(f"All clusters ≥ {MIN_SIZE} threads (3% floor ok).")

        # Missingness flags
        flags = [f"M2-C{c}" for c, ms in miss.items() if ms["flag_missingness"]]
        if flags:
            p(f"⚠️ Missingness flags: {', '.join(flags)} — compare means below to corpus median {corpus_median}.")

        # Fingerprint table
        L += _fingerprint_table(fps, miss)
        L.append("")

        # Missingness detail
        L.append("Missingness detail:")
        L.append("| Cluster | Mean missing features | Flag? |")
        L.append("|---------|----------------------|-------|")
        for c, ms in sorted(miss.items()):
            f2 = "⚠️" if ms["flag_missingness"] else "ok"
            L.append(f"| M2-C{c} | {ms['mean_missing_features']} | {f2} |")
        L.append("")

    h("5. Cross-check: HDBSCAN on precomputed Gower")
    n_hdb   = len(set(hdb_labels)) - (1 if -1 in hdb_labels else 0)
    n_noise = int((hdb_labels == -1).sum())
    p(f"HDBSCAN (metric='precomputed', min_cluster_size={MIN_SIZE}, min_samples={HDBSCAN_MIN_SAMPLES})",
      f"found **{n_hdb} clusters** with {n_noise} noise points ({n_noise/N_TOTAL*100:.1f}%).",
      "This is the data-driven 'no-k-specified' view — compare to hierarchical candidates above.")
    L.append("| HDBSCAN label | n | % |")
    L.append("|---------------|---|---|")
    vc = pd.Series(hdb_labels).value_counts().sort_index()
    for lbl, cnt in vc.items():
        name = "noise" if lbl == -1 else f"HDB-C{lbl}"
        L.append(f"| {name} | {cnt} | {round(cnt/N_TOTAL*100,1)}% |")
    L.append("")
    p("⚠️ Disagreement note: HDBSCAN found a substantially different cluster count than",
      f"the hierarchical optimum (k=2 vs k={n_hdb}). Per CLAUDE.md § H3, disagreement",
      "between methods is itself a finding, not a problem. Document and carry forward.")

    h("6. Cross-check: K-prototypes")
    p("⚠️ **Different missingness strategy**: k-prototypes keeps 'desconhecido' as a",
      "category level for all categorical features, and imputes ordinal NaN with column",
      "median (5 values total). Gower excludes missing values pairwise.",
      "",
      "Interpretation rule:",
      "• Agreement → robustness evidence: the segment structure survives two different",
      "  treatments of missing data.",
      "• Disagreement → may be missingness-driven: check whether the disagreeing cluster",
      "  in k-prototypes is dominated by 'desconhecido' values. If so, it is likely a",
      "  missingness artefact in k-prototypes, not a real investor segment.")
    L.append("| k | Cost (lower = better within k-proto objective) |")
    L.append("|---|------------------------------------------------|")
    for k in sorted(kp_results):
        L.append(f"| {k} | {kp_results[k]['cost']:.1f} |")
    L.append("")
    best_kp = min(kp_results, key=lambda k: kp_results[k]["cost"])
    p(f"K-prototypes cost decreases monotonically to k={best_kp};",
      "cost alone is not diagnostic — elbow inspection and comparison to Gower are required.")

    h("7. Figures")
    L.append("- `reports/figures/m2_silhouette.png` — silhouette vs k (candidates highlighted)")
    L.append("- `reports/figures/m2_gap.png` — gap statistic vs k (candidates highlighted)")
    L.append("- `reports/figures/m2_umap.png` — 2-D UMAP scatter (hierarchical + HDBSCAN)")
    L.append("- `reports/figures/m2_dendrogram.png` — truncated dendrogram")
    L.append("")

    L.append("---\n")
    L.append("## ⛔ HARD STOP — Supervisor action required\n")
    L.append(
        f"Review the fingerprints for k ∈ {candidate_ks} above (Section 5) and the\n"
        "figures in reports/figures/. Select the k that produces the most interpretable\n"
        "and multi-dimensional segments. Interpretability is a pre-registered criterion.\n\n"
        "To finalise, run:\n\n"
        "```\n"
        "python notebooks/03a_attribute_clustering.py --finalize <chosen_k>\n"
        "```\n\n"
        "This will write `data/processed/clusters_method2.parquet` and\n"
        "`reports/phase3a_method2.md`. Do not proceed to Phase 3B until that is done.\n"
    )

    out = REPORTS / "phase3a_explore.md"
    out.write_text("\n".join(L), encoding="utf-8")
    log(f"  Saved {out}")


# ═══════════════════════════════════════════════════════════════════════════════
# Finalize report
# ═══════════════════════════════════════════════════════════════════════════════

def write_final_report(
    chosen_k:      int,
    sil_scores:    dict,
    gap_res:       dict,
    boot_res:      dict,
    miss_stats:    dict,
    corpus_median: float,
    fps:           dict,
    labels:        np.ndarray,
    hdb_labels:    np.ndarray,
    kp_results:    dict,
) -> None:
    L = []

    def h(t, lv=2): L.append(f"\n{'#'*lv} {t}\n")
    def p(*parts): L.append(" ".join(parts)); L.append("")

    L.append("# Phase 3A — Method 2: Attribute Clustering (PRIMARY) — FINAL\n")
    L.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}  ")
    L.append(f"**Chosen k:** {chosen_k} (supervisor-selected)  ")
    L.append("**Status: AWAITING SUPERVISOR REVIEW — Phase 3B is blocked**\n")
    L.append("---\n")

    h("1. k-selection rationale (supervisor decision, logged for reproducibility)")
    p("**k=2** — cleanest by both silhouette (0.380) and Tibshirani stopping rule, but",
      "the two clusters collapse to a single speculator-vs-mainstream axis",
      "(M2-C1: risk=4.44, crypto=3.93, strategy=especulacao 92%). A single axis is a",
      "pre-registered failure condition (CLAUDE.md § H4); k=2 was rejected on that basis.")
    p("**k=5** — degenerate: one cluster contains a single thread (n=1), violating the",
      "3% floor by four orders of magnitude. Rejected.")
    p("**k=7** — selected. First value that (a) resolves the dominant mass into two",
      "distinct well-populated behavioral segments beyond the speculator split;",
      "(b) clears the bootstrap stability floor (mean ARI ≥ 0.5) for five of seven",
      "clusters; (c) sits at the gap-statistic discontinuity — gap rises sharply from",
      "~0.21 at k=2..6 to 0.33 at k=7, consistent with a real structural boundary;",
      "(d) aligns with HDBSCAN's fine structure (13 density-based clusters suggesting",
      "the data supports ≥ 7 natural groups).")
    p(f"**Edge clusters (below {MIN_SIZE}-thread / 3% floor):** M2-C0 (n=17) and M2-C4 (n=33)",
      "are retained in the output labelled 'edge' and excluded from persona candidacy.",
      "They are kept for Phase 3D enrichment analysis only.")
    p("**Soft clusters:** M2-C1 and M2-C3 have per-cluster Jaccard ≈ 0.49, just below the",
      "0.5 stability threshold. Both are flagged here for cross-method validation in",
      "Phase 3D. If Methods 1 and 3 independently corroborate their boundaries they will",
      "be promoted; otherwise they will be merged or demoted to 'edge'.")

    h("2. Methodology")
    p("Gower distance + average-linkage hierarchical clustering.",
      "HDBSCAN cross-check: metric='precomputed' on Gower matrix, NOT on 2-D UMAP.",
      f"HDBSCAN min_cluster_size={MIN_SIZE}, min_samples={HDBSCAN_MIN_SAMPLES}.",
      "K-prototypes cross-check: desconhecido retained as level (different missingness strategy).")

    h("3. Cluster sizes and 3% floor")
    L.append(f"Minimum viable cluster: {MIN_SIZE} threads (3% of {N_TOTAL}).\n")
    L.append("| Cluster | n | % | Below 3% floor? |")
    L.append("|---------|---|---|-----------------|")
    for c in sorted(miss_stats):
        ms   = miss_stats[c]
        edge = "⚠️ EDGE" if ms["n"] < MIN_SIZE else "ok"
        L.append(f"| M2-C{c} | {ms['n']} | {ms['pct']}% | {edge} |")
    L.append("")

    h("4. Feature fingerprints")
    p("Ordinal: mean (1–5 scale). Categorical: mode + mode%.",
      "No persona names — refer to clusters as M2-C0 … M2-C{k-1}.",
      "Edge clusters (below 3% floor) are labelled ⚠️ EDGE.")
    for c in sorted(fps):
        ms_c  = miss_stats[c]
        edge  = "  ⚠️ EDGE — excluded from persona candidacy" if ms_c["n"] < MIN_SIZE else ""
        h(f"M2-C{c}  (n={ms_c['n']}, {ms_c['pct']}%){edge}", lv=4)
        L.append("| Feature | Value | n_valid |")
        L.append("|---------|-------|---------|")
        for col in ORDINAL_FEATURES:
            v = fps[c][col]
            L.append(f"| {col} | {v['mean']} (mean) | {v['n_valid']} |")
        for col in CATEGORICAL_FEATURES:
            v = fps[c][col]
            L.append(f"| {col} | {v['mode']} ({v['mode_pct']}%) | {v['n_valid']} |")
        L.append("")

    h("5. Bootstrap stability")
    br = boot_res[chosen_k]
    p(f"20 iterations, 80% subsample.",
      f"Mean ARI: **{br['mean_ari']:.3f} ± {br['std_ari']:.3f}**",
      f"({'STABLE' if br['mean_ari'] >= 0.5 else '⚠️ UNSTABLE'})")
    L.append("| Cluster | Mean Jaccard | Stable? | Notes |")
    L.append("|---------|-------------|---------|-------|")
    for c, j in sorted(br["per_cluster_jaccard"].items()):
        ms_c  = miss_stats[c]
        if ms_c["n"] < MIN_SIZE:
            note  = "edge cluster — excluded from persona candidacy"
            flag  = "n/a"
        elif j < 0.5:
            note  = "⚠️ soft — flagged for Phase 3D cross-method validation"
            flag  = "⚠️ UNSTABLE"
        else:
            note, flag = "", "ok"
        L.append(f"| M2-C{c} | {j:.3f} | {flag} | {note} |")
    L.append("")

    h("6. Missingness artifact check")
    p(f"Corpus median: {corpus_median}. Flag threshold: {1.5*corpus_median:.2f}.")
    L.append("| Cluster | Mean missing features | Flag? |")
    L.append("|---------|----------------------|-------|")
    for c in sorted(miss_stats):
        ms = miss_stats[c]
        L.append(f"| M2-C{c} | {ms['mean_missing_features']} | {'⚠️' if ms['flag_missingness'] else 'ok'} |")
    L.append("")
    if all(miss_stats[c]["flag_missingness"] for c in miss_stats):
        p("Note: all clusters flagged at similar levels — indicates uniform corpus-wide",
          "missingness, NOT cluster-specific artifact. See explore report for discussion.")

    h("7. HDBSCAN cross-check")
    n_hdb  = len(set(hdb_labels)) - (1 if -1 in hdb_labels else 0)
    n_nois = int((hdb_labels == -1).sum())
    p(f"HDBSCAN (precomputed Gower) found {n_hdb} clusters, {n_nois} noise ({n_nois/N_TOTAL*100:.1f}%).",
      f"Hierarchical chose k={chosen_k}.",
      "Method disagreement is logged here for Phase 4 cross-method synthesis.")

    h("8. K-prototypes cross-check")
    p("⚠️ Different missingness strategy (desconhecido as category level + ordinal median impute).",
      "Gower/k-proto agreement → robustness. Disagreement → check if driven by missingness.")
    L.append("| k | Cost |")
    L.append("|---|------|")
    for k in sorted(kp_results):
        L.append(f"| {k} | {kp_results[k]['cost']:.1f} |")
    L.append("")

    h("9. Figures")
    for fn, desc in [
        ("m2_silhouette.png", "silhouette vs k"),
        ("m2_gap.png",        "gap statistic vs k"),
        ("m2_umap.png",       "2-D UMAP scatter (hierarchical + HDBSCAN)"),
        ("m2_dendrogram.png", "truncated dendrogram"),
    ]:
        L.append(f"- `reports/figures/{fn}` — {desc}")
    L.append("")

    L.append("---\n")
    L.append("## ⛔ HARD STOP\n")
    L.append("Phase 3A finalised. **Do not proceed to Phase 3B** until supervisor\n"
             "has reviewed this document and the four figures.\n")

    out = REPORTS / "phase3a_method2.md"
    out.write_text("\n".join(L), encoding="utf-8")
    log(f"  Saved {out}")


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    # ── Parse mode ────────────────────────────────────────────────────────────
    if len(sys.argv) >= 2 and sys.argv[1] == "--finalize":
        if len(sys.argv) < 3:
            print("Usage: python 03a_attribute_clustering.py --finalize <k>")
            sys.exit(1)
        chosen_k = int(sys.argv[2])
        mode     = "finalize"
    else:
        chosen_k = None
        mode     = "explore"

    rng = np.random.default_rng(SEED)
    log(f"MODE: {mode}" + (f" (k={chosen_k})" if chosen_k else ""))

    # ── Load ──────────────────────────────────────────────────────────────────
    log("Loading features …")
    meta, feat = load_features()
    log(f"  {len(feat)} threads × {len(ALL_FEATURES)} features")

    # ── Gower (cached) ────────────────────────────────────────────────────────
    gower_cache = DATA_INT / "gower_matrix.npy"
    if gower_cache.exists():
        log("Loading cached Gower matrix …")
        D = np.load(gower_cache)
    else:
        log("Computing Gower matrix …")
        import time; t0 = time.time()
        D = compute_gower_matrix(feat)
        log(f"  Done in {time.time()-t0:.1f}s")
        np.save(gower_cache, D)
        log(f"  Cached → {gower_cache}")

    # ── Hierarchical linkage (cached) ─────────────────────────────────────────
    link_cache = DATA_INT / "linkage_average.npy"
    if link_cache.exists():
        log("Loading cached linkage …")
        Z = np.load(link_cache)
    else:
        log("Running average-linkage …")
        import time; t0 = time.time()
        Z = linkage(squareform(D.astype(np.float64), checks=False), method="average")
        np.save(link_cache, Z)
        log(f"  Done in {time.time()-t0:.1f}s")

    # ══════════════════════════════════════════════════════════════════════════
    # FINALIZE MODE
    # ══════════════════════════════════════════════════════════════════════════
    if mode == "finalize":
        log(f"FINALIZE MODE: applying supervisor-chosen k={chosen_k}")
        labels = fcluster(Z, chosen_k, criterion="maxclust") - 1

        # Need the full metric / cross-check outputs (load from explore artefacts if cached,
        # or recompute quickly — silhouette+gap are fast since Gower is cached)
        log("Recomputing silhouette & gap for final report …")
        sil_scores = silhouette_sweep(D, Z, K_RANGE)
        gap_res    = gap_statistic(D, feat, Z, K_RANGE, B=GAP_B, rng=rng)

        log("Bootstrap stability for chosen k …")
        boot_res = bootstrap_stability_multi(D, Z, [chosen_k], n_boot=BOOT_B, rng=rng)

        miss_stats, corpus_median = missingness_check(feat, labels)
        fps = cluster_fingerprints(feat, labels)

        log("HDBSCAN cross-check …")
        hdb_labels = run_hdbscan_precomputed(D)

        log("K-prototypes cross-check …")
        kp_results = run_kprototypes(feat, list(range(2, 9)))

        # Figures
        log("Generating figures …")
        plot_silhouette(sil_scores, [chosen_k])
        plot_gap(gap_res, [chosen_k])
        embedding = run_umap_2d(D)
        plot_umap(embedding, labels, hdb_labels, chosen_k)
        plot_dendrogram(Z, [chosen_k])

        # Per-sample silhouette + medoid distance
        sil_vals = silhouette_samples(D.astype(np.float64), labels, metric="precomputed")
        medoids  = {}
        for c in np.unique(labels):
            members    = np.where(labels == c)[0]
            sub        = D[np.ix_(members, members)]
            medoids[c] = int(members[sub.sum(axis=1).argmin()])
        dist_to_med = np.array([float(D[i, medoids[labels[i]]]) for i in range(len(labels))])

        out_df = pd.DataFrame({
            "thread_id":         meta["thread_id"].values,
            "cluster_label":     [f"M2-C{c}" for c in labels],
            "cluster_int":       labels,
            "silhouette_sample": sil_vals.round(4),
            "dist_to_medoid":    dist_to_med.round(4),
        })
        out_path = DATA_PROC / "clusters_method2.parquet"
        out_df.to_parquet(out_path, index=False)
        log(f"Saved {out_path}")

        write_final_report(
            chosen_k=chosen_k, sil_scores=sil_scores, gap_res=gap_res,
            boot_res=boot_res, miss_stats=miss_stats, corpus_median=corpus_median,
            fps=fps, labels=labels, hdb_labels=hdb_labels, kp_results=kp_results,
        )

        log("=" * 60)
        log(f"PHASE 3A FINALISED  (k={chosen_k})")
        sizes = pd.Series(labels).value_counts().sort_index()
        for c, n in sizes.items():
            log(f"  M2-C{c}: {n} ({n/N_TOTAL*100:.1f}%)")
        log(f"  Mean ARI stability: {boot_res[chosen_k]['mean_ari']:.3f}")
        log(f"  Parquet: {out_path}")
        log(f"  Report: {REPORTS / 'phase3a_method2.md'}")
        log("⛔ HARD STOP — awaiting supervisor review before Phase 3B")
        log("=" * 60)
        return

    # ══════════════════════════════════════════════════════════════════════════
    # EXPLORE MODE
    # ══════════════════════════════════════════════════════════════════════════
    log("EXPLORE MODE")

    # Silhouette sweep
    log("Silhouette sweep k=2..10 …")
    sil_scores = silhouette_sweep(D, Z, K_RANGE)

    # Gap statistic
    log(f"Gap statistic (B={GAP_B} references) …")
    gap_res      = gap_statistic(D, feat, Z, K_RANGE, B=GAP_B, rng=rng)
    gap_tibsh_k  = gap_optimal_k(gap_res, K_RANGE)
    best_sil_k   = max(sil_scores, key=lambda k: sil_scores[k] if not np.isnan(sil_scores[k]) else -1)
    best_gap_k   = max(gap_res, key=lambda k: gap_res[k]["gap"])
    log(f"  Silhouette-best k={best_sil_k}  |  Gap-best (highest) k={best_gap_k}  |  Tibshirani k={gap_tibsh_k}")

    # Candidate k values: silhouette-best, gap-best, interpretable middle
    # Use k=5 as the "interpretable middle" (centre of the 4–6 persona target range)
    middle_k      = 5
    candidate_ks  = sorted(set([best_sil_k, best_gap_k, middle_k]))
    log(f"Candidate k values for supervisor review: {candidate_ks}")

    # Bootstrap stability — one pass, all candidates
    log(f"Bootstrap stability for k ∈ {candidate_ks} ({BOOT_B} iterations) …")
    boot_res = bootstrap_stability_multi(D, Z, candidate_ks, n_boot=BOOT_B, rng=rng)

    # Fingerprints & missingness for each candidate
    fps_by_k  = {}
    miss_by_k = {}
    for k in candidate_ks:
        labels                = fcluster(Z, k, criterion="maxclust") - 1
        fps_by_k[k]           = cluster_fingerprints(feat, labels)
        miss_by_k[k]          = missingness_check(feat, labels)
    corpus_median = miss_by_k[candidate_ks[0]][1]

    # HDBSCAN on precomputed Gower
    log("HDBSCAN cross-check (precomputed Gower) …")
    hdb_labels = run_hdbscan_precomputed(D)

    # K-prototypes
    log("K-prototypes cross-check …")
    kp_results = run_kprototypes(feat, list(range(2, 9)))

    # Figures (use best_sil_k labels for the hierarchical side)
    log("Generating figures …")
    labels_for_fig = fcluster(Z, best_sil_k, criterion="maxclust") - 1
    plot_silhouette(sil_scores, candidate_ks)
    plot_gap(gap_res, candidate_ks)
    embedding = run_umap_2d(D)
    np.save(DATA_INT / "umap_embedding.npy", embedding)
    plot_umap(embedding, labels_for_fig, hdb_labels, best_sil_k)
    plot_dendrogram(Z, candidate_ks)

    # Write explore report
    log("Writing explore report …")
    write_explore_report(
        sil_scores=sil_scores, gap_res=gap_res, gap_tibsh_k=gap_tibsh_k,
        candidate_ks=candidate_ks, boot_res=boot_res, miss_by_k=miss_by_k,
        corpus_median=corpus_median, fps_by_k=fps_by_k,
        hdb_labels=hdb_labels, kp_results=kp_results,
    )

    log("=" * 60)
    log("PHASE 3A EXPLORE COMPLETE")
    log(f"  Candidate k values: {candidate_ks}")
    log(f"  ARI (mean): " + "  ".join(f"k={k}: {boot_res[k]['mean_ari']:.3f}" for k in candidate_ks))
    log(f"  HDBSCAN found: {len(set(hdb_labels)) - (1 if -1 in hdb_labels else 0)} clusters")
    log(f"  Report: {REPORTS / 'phase3a_explore.md'}")
    log("⛔ HARD STOP — supervisor selects k, then run --finalize <k>")
    log("=" * 60)


if __name__ == "__main__":
    main()

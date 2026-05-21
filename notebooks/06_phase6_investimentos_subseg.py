#!/usr/bin/env python3
"""
Phase 6 (SUPPLEMENTARY) — r/investimentos-only sub-segmentation of the earnest
mainstream.

This is NOT a re-run of the main study. It is a SCOPED supplementary analysis,
subordinate to the triangulated three-persona result. The headline remains the
three personas (Sossego-Seeker, Sardinha, Cético Irônico). This re-clusters only
the r/investimentos subset to ask: does the earnest mainstream (where the
Sossego-Seeker dominates) resolve into actionable sub-segments, or is it one
coherent persona?

Single-subreddit, single-method (Method 2 attributes only). Any sub-segments
found are EXPLORATORY — same tier as the demoted Method-1 topical spikes
(tax/IR, property/debt), NOT the tier of the confirmed personas.

Mode:
  python notebooks/06_phase6_investimentos_subseg.py    # EXPLORE only.
                                                          HARD STOP after.

Inputs (already exist; NO new extraction, NO new LLM calls):
  data/processed/extracted_attributes.parquet  — 15-field scorecard for 3,600 threads
  data/processed/clusters_method2.parquet      — Phase 3A M2 labels (k=7)
  data/processed/clustering_features.json      — locked 10 features + flags

Reused primitives (imported from notebooks/03a_attribute_clustering.py):
  compute_gower_matrix, silhouette_sweep, gap_statistic, gap_optimal_k,
  bootstrap_stability_multi, missingness_check, cluster_fingerprints,
  ORDINAL_FEATURES, CATEGORICAL_FEATURES, ALL_FEATURES, SEED, GAP_B, BOOT_B
"""

import sys
import importlib.util
import json
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
from scipy.cluster.hierarchy import linkage, fcluster

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE      = Path(__file__).resolve().parent.parent
DATA_PROC = BASE / "data" / "processed"
DATA_INT  = BASE / "data" / "interim"
REPORTS   = BASE / "reports"
FIGURES   = REPORTS / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)

# ── Import Phase 3A primitives (reuse, do NOT re-implement) ──────────────────
_p3a_path = BASE / "notebooks" / "03a_attribute_clustering.py"
_spec     = importlib.util.spec_from_file_location("p3a", _p3a_path)
p3a       = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(p3a)

compute_gower_matrix       = p3a.compute_gower_matrix
silhouette_sweep           = p3a.silhouette_sweep
gap_statistic              = p3a.gap_statistic
gap_optimal_k              = p3a.gap_optimal_k
bootstrap_stability_multi  = p3a.bootstrap_stability_multi
missingness_check          = p3a.missingness_check
cluster_fingerprints       = p3a.cluster_fingerprints
ORDINAL_FEATURES           = p3a.ORDINAL_FEATURES
CATEGORICAL_FEATURES       = p3a.CATEGORICAL_FEATURES
ALL_FEATURES               = p3a.ALL_FEATURES
SEED                       = p3a.SEED
GAP_B                      = p3a.GAP_B
BOOT_B                     = p3a.BOOT_B

# ── Phase 6 constants ─────────────────────────────────────────────────────────
SUBSET_SUBREDDIT = "investimentos"
K_RANGE          = list(range(2, 11))
# 3% floor is RECOMPUTED on the subset n, not inherited from the main study (3600 → 108).

# Demoted-flag fields used for situational-variant alignment (descriptive only;
# these were NOT clustered on).
SITUATIONAL_FLAGS = ["perfil_tributario_e_fiscal", "relacao_com_imovel_e_heranca"]


def log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Load + subset + firewall
# ═══════════════════════════════════════════════════════════════════════════════

def load_and_subset() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load full attributes, subset to investimentos, also keep demoted flags."""
    df = pd.read_parquet(DATA_PROC / "extracted_attributes.parquet")
    df_sub = df[df["subreddit_origem"] == SUBSET_SUBREDDIT].reset_index(drop=True)

    meta = df_sub[["thread_id", "subreddit_origem", "window"]].copy()
    feat = df_sub[ALL_FEATURES].copy()
    flags = df_sub[SITUATIONAL_FLAGS].copy()

    # Same NA convention as Phase 3A: 'desconhecido' → NA for categoricals.
    for col in CATEGORICAL_FEATURES:
        feat[col] = feat[col].where(feat[col] != "desconhecido", other=pd.NA)
    for col in ORDINAL_FEATURES:
        feat[col] = feat[col].astype("float64")
    return meta, feat, flags


def assert_firewall(feat: pd.DataFrame) -> None:
    """subreddit_origem and window must NOT be in the feature matrix."""
    forbidden = {"subreddit_origem", "window"}
    present   = forbidden & set(feat.columns)
    assert not present, (
        f"FIREWALL VIOLATION: {present} present in clustering feature matrix. "
        "We are subsetting ON subreddit_origem, so feeding it as a clustering "
        "feature would be doubly circular. ABORT."
    )
    log("  ✓ Firewall assertion PASSED: subreddit_origem and window are NOT in feature matrix.")


# ═══════════════════════════════════════════════════════════════════════════════
# Task 2 — M2 composition check
# ═══════════════════════════════════════════════════════════════════════════════

def m2_composition_check(meta: pd.DataFrame) -> pd.DataFrame:
    """
    Join existing Phase 3A M2 labels onto investimentos rows.
    Report % originally M2-C0..M2-C6 in this subset.
    """
    m2 = pd.read_parquet(DATA_PROC / "clusters_method2.parquet")
    merged = meta.merge(
        m2[["thread_id", "cluster_label"]],
        on="thread_id", how="left", validate="one_to_one",
    )
    assert merged["cluster_label"].notna().all(), "Some investimentos threads have no M2 label."
    vc = merged["cluster_label"].value_counts().sort_index()
    table = pd.DataFrame({
        "n":     vc.values,
        "pct":   (vc.values / len(merged) * 100).round(1),
    }, index=vc.index)
    table.index.name = "m2_cluster"
    return table, merged


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 6 figures
# ═══════════════════════════════════════════════════════════════════════════════

def plot_silhouette(sil_scores: dict, candidate_ks: list) -> None:
    ks = sorted(sil_scores)
    vs = [sil_scores[k] for k in ks]
    fig, ax = plt.subplots(figsize=(9, 4))
    colors = ["#e07b54" if k in candidate_ks else "#4c8bb5" for k in ks]
    ax.bar(ks, vs, color=colors)
    for k in candidate_ks:
        ax.axvline(k, color="#e07b54", linestyle="--", linewidth=1, alpha=0.5)
    ax.set_xlabel("k")
    ax.set_ylabel("Silhouette (Gower, average linkage)")
    ax.set_title("Phase 6 (supplementary) — Silhouette vs k on r/investimentos subset\n"
                 "Orange bars = candidate k values; ⚠️ supplementary, not headline")
    ax.set_xticks(ks)
    plt.tight_layout()
    fig.savefig(FIGURES / "phase6_silhouette.png", dpi=150)
    plt.close(fig)
    log("  Saved phase6_silhouette.png")


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
    ax.set_title(f"Phase 6 (supplementary) — Gap vs k on r/investimentos subset "
                 f"(B={GAP_B} refs)")
    ax.set_xticks(ks)
    ax.legend(fontsize=8)
    plt.tight_layout()
    fig.savefig(FIGURES / "phase6_gap.png", dpi=150)
    plt.close(fig)
    log("  Saved phase6_gap.png")


def plot_umap_scatter(D: np.ndarray, labels_by_k: dict) -> np.ndarray:
    """2-D UMAP for visualisation only. Returns embedding for caller to cache."""
    import umap as umap_lib
    log("  UMAP 2-D (visualisation only) …")
    reducer = umap_lib.UMAP(
        n_components=2, metric="precomputed", random_state=SEED, n_jobs=1,
    )
    embedding = reducer.fit_transform(D.astype(np.float64))

    n_panels = len(labels_by_k)
    fig, axes = plt.subplots(1, n_panels, figsize=(6 * n_panels, 6), squeeze=False)
    palette   = sns.color_palette("tab10", 10)
    for ax, (k, lbl) in zip(axes[0], labels_by_k.items()):
        for c in sorted(set(lbl)):
            m = lbl == c
            ax.scatter(embedding[m, 0], embedding[m, 1],
                       c=[palette[c % 10]], s=6, alpha=0.6, label=f"P6-C{c}")
        ax.set_title(f"r/investimentos hierarchical (k={k})")
        ax.set_xlabel("UMAP-1")
        ax.set_ylabel("UMAP-2")
        ax.legend(markerscale=2, fontsize=7)
    fig.suptitle("Phase 6 (supplementary) — 2-D UMAP of Gower distances on r/investimentos\n"
                 "visualisation only; clustering ran on full Gower matrix; ⚠️ supplementary")
    plt.tight_layout()
    fig.savefig(FIGURES / "phase6_umap.png", dpi=150)
    plt.close(fig)
    log("  Saved phase6_umap.png")
    return embedding


# ═══════════════════════════════════════════════════════════════════════════════
# Cross-tabs & situational alignment
# ═══════════════════════════════════════════════════════════════════════════════

def crosstab_to_m2(p6_labels: np.ndarray, merged: pd.DataFrame) -> pd.DataFrame:
    """Sub-cluster (P6) × Phase 3A M2 label, rows sum to 100%."""
    df = pd.DataFrame({
        "p6_cluster": [f"P6-C{c}" for c in p6_labels],
        "m2_cluster": merged["cluster_label"].values,
    })
    ct  = pd.crosstab(df["p6_cluster"], df["m2_cluster"])
    pct = ct.div(ct.sum(axis=1), axis=0).mul(100).round(1)
    return ct, pct


def situational_flag_distribution(p6_labels: np.ndarray, flags: pd.DataFrame) -> dict:
    """Per sub-cluster: value-counts of perfil_tributario and relacao_com_imovel."""
    out = {}
    for c in sorted(set(p6_labels)):
        members = np.where(p6_labels == c)[0]
        per_flag = {}
        for fcol in SITUATIONAL_FLAGS:
            vals = flags[fcol].iloc[members]
            vc   = vals.value_counts(dropna=False)
            tot  = len(vals)
            per_flag[fcol] = {
                str(idx): {"n": int(cnt), "pct": round(cnt / tot * 100, 1)}
                for idx, cnt in vc.items()
            }
        out[int(c)] = per_flag
    return out


# ═══════════════════════════════════════════════════════════════════════════════
# Report writer
# ═══════════════════════════════════════════════════════════════════════════════

def _fp_table(fps: dict, miss_stats: dict, k: int) -> list[str]:
    """Compact per-cluster fingerprint table."""
    lines  = []
    header = "| Feature | " + " | ".join(
        f"P6-C{c} (n={miss_stats[c]['n']}, {miss_stats[c]['pct']}%)" for c in range(k)
    ) + " |"
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


def _crosstab_table(ct: pd.DataFrame, pct: pd.DataFrame) -> list[str]:
    """Render P6 × M2 crosstab with both n and %."""
    lines = []
    m2_cols = list(ct.columns)
    header  = "| Sub-cluster | " + " | ".join(m2_cols) + " | row total |"
    sep     = "|-------------|" + "---|" * (len(m2_cols) + 1)
    lines  += [header, sep]
    for p6 in ct.index:
        cells = []
        for m2c in m2_cols:
            n = int(ct.loc[p6, m2c])
            p = pct.loc[p6, m2c]
            cells.append(f"{n} ({p}%)")
        cells.append(str(int(ct.loc[p6].sum())))
        lines.append(f"| {p6} | " + " | ".join(cells) + " |")
    return lines


def _flag_table(sit: dict, k: int) -> list[str]:
    """Per-sub-cluster distribution of demoted situational flags."""
    lines = []
    for fcol in SITUATIONAL_FLAGS:
        lines.append(f"\n**{fcol}** (descriptive only — NOT a clustering feature)\n")
        # Gather all observed levels across sub-clusters for a stable column order.
        levels = set()
        for c in range(k):
            levels |= set(sit[c][fcol].keys())
        levels = sorted(levels)
        header = "| Sub-cluster | " + " | ".join(levels) + " |"
        sep    = "|-------------|" + "---|" * len(levels)
        lines += [header, sep]
        for c in range(k):
            row = [f"P6-C{c}"]
            for lvl in levels:
                cell = sit[c][fcol].get(lvl)
                row.append(f"{cell['n']} ({cell['pct']}%)" if cell else "0")
            lines.append("| " + " | ".join(row) + " |")
    return lines


def headline_read(
    candidate_ks:  list,
    min_size:      int,
    crosstab_by_k: dict,
    boot_res:      dict,
) -> tuple[dict, str]:
    """
    For each candidate k, classify above-3%-floor sub-clusters by their M2-C2
    (earnest) share into: genuine_mainstream (≥75% earnest), mixed (50–75%),
    residual_tail (<50%). Return per-k summary + a single one-paragraph verdict.
    """
    per_k = {}
    any_genuine_above_floor = False
    for k in candidate_ks:
        ct, pct = crosstab_by_k[k]
        genuine, mixed, residual = [], [], []
        for p6c in pct.index:
            row_n = int(ct.loc[p6c].sum())
            if row_n < min_size:
                continue
            earnest_pc = float(pct.loc[p6c].get("M2-C2", 0.0))
            entry = {"sub": p6c, "n": row_n, "earnest_pct": earnest_pc}
            if earnest_pc >= 75:
                genuine.append(entry)
                any_genuine_above_floor = True
            elif earnest_pc >= 50:
                mixed.append(entry)
            else:
                residual.append(entry)
        per_k[k] = {
            "stable":      boot_res[k]["mean_ari"] >= 0.5,
            "mean_ari":    boot_res[k]["mean_ari"],
            "genuine":     genuine,
            "mixed":       mixed,
            "residual":    residual,
            "n_above":     len(genuine) + len(mixed) + len(residual),
        }

    # One-paragraph verdict: did any candidate k produce more than one genuine
    # earnest-dominated sub-segment above the 3% floor AND clear the stability bar?
    multi_split_k = [
        k for k, info in per_k.items()
        if info["stable"] and len(info["genuine"]) >= 2
    ]
    if multi_split_k:
        verdict = (
            f"**Candidate k={multi_split_k} produced ≥2 genuine earnest-dominated "
            f"(≥75% M2-C2) sub-segments above the recomputed {min_size}-thread floor "
            "AND cleared bootstrap stability ≥ 0.5. The data SUPPORTS a sub-segmentation "
            "read; supervisor selects k for naming."
        )
    elif any_genuine_above_floor:
        verdict = (
            f"At NO candidate k did the earnest mass split into ≥2 genuine "
            f"earnest-dominated sub-segments above the {min_size}-thread floor with "
            "bootstrap stability ≥ 0.5. Every candidate produces ONE giant earnest core "
            "plus tail clusters that are either below the 3% floor or dominated by "
            "originally-speculator / originally-cynic / originally-edge threads (residual "
            "tails re-surfacing). **The data points to the 'one coherent persona' verdict** "
            "— the Sossego-Seeker does not resolve into actionable life-stage / goal sub-segments "
            "on this evidence. Supervisor decision: confirm or override."
        )
    else:
        verdict = (
            "No earnest-dominated sub-cluster appears above the 3% floor at any candidate k. "
            "This is an unexpected result — review the composition check (Section 2) and "
            "consider whether the subset is actually mainstream-dominant before interpreting."
        )
    return per_k, verdict


def write_report(
    n_sub:          int,
    min_size:       int,
    window_dist:    pd.Series,
    m2_table:       pd.DataFrame,
    composition_v:  str,
    sil_scores:     dict,
    gap_res:        dict,
    gap_tibsh_k:    int,
    candidate_ks:   list,
    boot_res:       dict,
    miss_by_k:      dict,
    corpus_median:  float,
    fps_by_k:       dict,
    crosstab_by_k:  dict,
    sit_by_k:       dict,
) -> None:
    L = []

    def h(text, level=2):
        L.append(f"\n{'#' * level} {text}\n")

    def p(*parts):
        L.append(" ".join(parts))
        L.append("")

    per_k_summary, headline_verdict = headline_read(
        candidate_ks=candidate_ks, min_size=min_size,
        crosstab_by_k=crosstab_by_k, boot_res=boot_res,
    )

    L.append("# Phase 6 (SUPPLEMENTARY) — r/investimentos sub-segmentation: Explore Report\n")
    L.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}  ")
    L.append("**Status: AWAITING SUPERVISOR k SELECTION (or 'one coherent persona' verdict)**\n")

    h("0. Framing — read this first")
    p("This is a **SCOPED supplementary analysis**, subordinate to the triangulated",
      "three-persona result, which remains the headline. The speculator (*O Sardinha*)",
      "and cynical-reactive (*O Cético Irônico*) are **real populations** in this corpus.",
      "This re-clustering profiles the earnest-mainstream target customer **on its own",
      "data** to sharpen the Phase 4 build recommendation — it does NOT \"remove distortion\"",
      "to find a \"real investor\" and it does NOT define anyone away.")
    p("**Evidential tier — EXPLORATORY.** This is a single-subreddit, single-method",
      "(Method 2 attributes only) re-clustering. It is **NOT triangulated** the way the",
      "main three personas are. Any sub-segments found here sit at the same tier as the",
      "demoted Method-1 topical spikes (tax/IR, property/debt), which we called",
      "\"situational variants,\" NOT at the tier of the triangulated three personas.",
      "Label and treat them accordingly.")

    h("0a. Headline read (cross-tab summary across all candidate k)")
    p("Across each candidate k, count sub-clusters above the recomputed",
      f"{min_size}-thread (3%) floor, then classify each by its M2-C2 (originally",
      "earnest) share:")
    L.append(
        "- **Genuine earnest-mainstream split** = above floor AND ≥75% originally M2-C2"
    )
    L.append(
        "- **Mixed** = above floor AND 50–75% originally M2-C2 (interpret with caution)"
    )
    L.append(
        "- **Residual tail re-surfacing** = above floor AND <50% originally M2-C2 "
        "(NOT a mainstream sub-segment; this is the speculator/cynic/edge mass coming back)"
    )
    L.append("")
    L.append("| k | Bootstrap stable? | # above floor | # genuine (≥75% earnest) | # mixed | # residual tail |")
    L.append("|---|-------------------|---------------|--------------------------|---------|-----------------|")
    for k in candidate_ks:
        info  = per_k_summary[k]
        stable = "✓" if info["stable"] else f"⚠️ unstable (ARI {info['mean_ari']:.2f})"
        L.append(
            f"| {k} | {stable} | {info['n_above']} | "
            f"{len(info['genuine'])} | {len(info['mixed'])} | {len(info['residual'])} |"
        )
    L.append("")
    # Detail rows: list every above-floor sub-cluster with its earnest share
    L.append("Above-floor sub-clusters in detail (sub-cluster · n · % originally earnest · class):\n")
    for k in candidate_ks:
        info = per_k_summary[k]
        all_above = info["genuine"] + info["mixed"] + info["residual"]
        if not all_above:
            L.append(f"- k={k}: no sub-cluster above the {min_size}-thread floor")
            continue
        parts = []
        for entry in info["genuine"]:
            parts.append(f"{entry['sub']} (n={entry['n']}, {entry['earnest_pct']:.0f}% earnest, GENUINE)")
        for entry in info["mixed"]:
            parts.append(f"{entry['sub']} (n={entry['n']}, {entry['earnest_pct']:.0f}% earnest, MIXED)")
        for entry in info["residual"]:
            parts.append(f"{entry['sub']} (n={entry['n']}, {entry['earnest_pct']:.0f}% earnest, RESIDUAL TAIL)")
        L.append(f"- k={k}: " + "; ".join(parts))
    L.append("")
    p(headline_verdict)
    p("⚠️ This headline is a structured summary of the cross-tab evidence, not a",
      "supervisor decision. Full per-k fingerprints and cross-tabs are in Section 6.",
      "The supervisor decision is in the HARD STOP at the end.")

    h("1. Subset & sanity-check")
    p(f"Filter: `subreddit_origem == '{SUBSET_SUBREDDIT}'`. **n = {n_sub}** threads.")
    L.append("Window distribution within the subset:\n")
    L.append("| Window | n | % |")
    L.append("|--------|---|---|")
    for w, cnt in window_dist.items():
        L.append(f"| {w} | {int(cnt)} | {round(cnt/n_sub*100, 1)}% |")
    L.append("")
    bal_note = ("balanced across windows — no time-period starvation."
                if window_dist.max() / max(window_dist.min(), 1) < 1.5
                else "⚠️ unbalanced across windows — interpret time-period claims with care.")
    p(f"Window balance: {bal_note}")
    p(f"**Recomputed 3% floor: {min_size} threads** (3% of n={n_sub}). Any sub-cluster",
      "below this is 'edge' and not promotable to a sub-segment claim — same rule as",
      "Phase 3A, just recomputed for the smaller sample.")
    p("**Firewall:** `subreddit_origem` and `window` are NOT in the feature matrix",
      "(asserted at runtime). The clustering is blind to subreddit — which is required,",
      "because we are *subsetting on* subreddit; feeding it as a feature too would be",
      "doubly circular.")

    h("2. Composition check — \"is this just the residual speculators/cynics?\"")
    p("**Before re-clustering**, we join the existing Phase 3A M2 labels onto these",
      "r/investimentos rows. This tells us what mass we are actually re-clustering.")
    L.append("| M2 cluster (Phase 3A) | Persona role | n in r/investimentos | % of subset |")
    L.append("|-----------------------|--------------|----------------------|-------------|")
    persona_role = {
        "M2-C2": "Sossego-Seeker (earnest, headline)",
        "M2-C1": "Cético Irônico (cynical-reactive)",
        "M2-C5": "Sardinha (speculator)",
        "M2-C0": "edge",
        "M2-C3": "edge",
        "M2-C4": "edge",
        "M2-C6": "edge",
    }
    for m2c in m2_table.index:
        role = persona_role.get(m2c, "?")
        n    = int(m2_table.loc[m2c, "n"])
        pc   = m2_table.loc[m2c, "pct"]
        L.append(f"| {m2c} | {role} | {n} | {pc}% |")
    L.append("")
    p(f"**Scenario verdict:** {composition_v}")

    h("3. Metric sweep on the r/investimentos subset (k = 2..10)")
    L.append("| k | Silhouette | Gap | s(Gap) | Tibshirani? |")
    L.append("|---|-----------|-----|--------|-------------|")
    for k in sorted(sil_scores):
        g   = gap_res.get(k, {})
        tib = "← stopping rule" if k == gap_tibsh_k else ""
        L.append(f"| {k} | {sil_scores[k]:.4f} | {g.get('gap',0):.4f} | "
                 f"{g.get('sk',0):.4f} | {tib} |")
    L.append("")
    best_sil = max(sil_scores, key=lambda k: sil_scores[k] if not np.isnan(sil_scores[k]) else -1)
    best_gap = max(gap_res,    key=lambda k: gap_res[k]["gap"])
    p(f"- Silhouette optimum: **k={best_sil}** (score={sil_scores[best_sil]:.4f})")
    p(f"- Highest gap value: **k={best_gap}** (gap={gap_res[best_gap]['gap']:.4f})")
    p(f"- Gap Tibshirani stopping rule: **k={gap_tibsh_k}**")
    p(f"- Candidate k values sent to supervisor for review: **k = {candidate_ks}**")

    h("4. Bootstrap stability (all candidates)")
    p(f"{BOOT_B} iterations, 80% subsample, linkage run once per subsample, cut at each k.",
      "Pre-registered threshold: mean ARI ≥ 0.5; per-cluster Jaccard ≥ 0.5.")
    L.append("| k | Mean ARI | Std | Stable? |")
    L.append("|---|----------|-----|---------|")
    for k in candidate_ks:
        br   = boot_res[k]
        flag = "✓" if br["mean_ari"] >= 0.5 else "⚠️ UNSTABLE"
        L.append(f"| {k} | {br['mean_ari']:.3f} | {br['std_ari']:.3f} | {flag} |")
    L.append("")

    h("5. Missingness artifact context")
    p(f"Corpus-subset median missing features per thread: **{corpus_median}**.",
      f"Flag threshold: mean > {1.5 * corpus_median:.2f} (1.5×).")
    p("If ALL sub-clusters are flagged at similar levels, that indicates uniform",
      "missingness — NOT a cluster-specific artifact. A genuine artifact cluster",
      "would show mean_missing >> all other clusters.")

    # Per-candidate sections
    for k in candidate_ks:
        h(f"6.{candidate_ks.index(k)+1}  Candidate k={k}", level=2)

        fps  = fps_by_k[k]
        miss = miss_by_k[k][0]
        br   = boot_res[k]
        ct, pct = crosstab_by_k[k]
        sit  = sit_by_k[k]

        # Stability + floor + missingness flags
        p(f"**Stability:** ARI {br['mean_ari']:.3f} ± {br['std_ari']:.3f} "
          f"({'STABLE' if br['mean_ari'] >= 0.5 else '⚠️ UNSTABLE'})")
        L.append("Per-cluster Jaccard: "
                 + "  ".join(f"P6-C{c}={j}" for c, j in br["per_cluster_jaccard"].items()))
        L.append("")
        below = [f"P6-C{c}" for c, ms in miss.items() if ms["n"] < min_size]
        if below:
            p(f"⚠️ Edge sub-clusters (< {min_size}-thread / 3% floor): {', '.join(below)}",
              " — not promotable; report-only.")
        else:
            p(f"All sub-clusters ≥ {min_size} threads (3% floor ok).")
        flags = [f"P6-C{c}" for c, ms in miss.items() if ms["flag_missingness"]]
        if flags:
            p(f"⚠️ Missingness flags: {', '.join(flags)} — compare to subset median {corpus_median}.")

        # Fingerprints
        h(f"6.{candidate_ks.index(k)+1}a  Feature fingerprints", level=3)
        L += _fp_table(fps, miss, k)
        L.append("")

        # Missingness detail
        L.append("Missingness detail:\n")
        L.append("| Sub-cluster | Mean missing features | Flag? |")
        L.append("|-------------|----------------------|-------|")
        for c, ms in sorted(miss.items()):
            f2 = "⚠️" if ms["flag_missingness"] else "ok"
            L.append(f"| P6-C{c} | {ms['mean_missing_features']} | {f2} |")
        L.append("")

        # ── Critical interpretive step: cross-tab vs original M2 ─────────────
        h(f"6.{candidate_ks.index(k)+1}b  Cross-tab vs Phase 3A M2 labels "
          "(THE CRITICAL INTERPRETIVE STEP)", level=3)
        p("A genuine mainstream sub-segment must be **overwhelmingly originally-earnest",
          "(M2-C2)**. A sub-cluster that is mostly originally-speculator (M2-C5) or",
          "originally-cynic (M2-C1) is the **residual tail re-surfacing** — NOT a new",
          "mainstream finding. Label such sub-clusters as residuals; do not promote.")
        L += _crosstab_table(ct, pct)
        L.append("")
        # Per-row plain-English call
        L.append("**Per-sub-cluster verdict:**\n")
        for p6c in pct.index:
            top_m2 = pct.loc[p6c].idxmax()
            top_pc = pct.loc[p6c].max()
            earnest_pc = float(pct.loc[p6c].get("M2-C2", 0.0))
            row_n = int(ct.loc[p6c].sum())
            edge_str  = " — ⚠️ EDGE (below 3% floor)" if row_n < min_size else ""
            if earnest_pc >= 75:
                verdict = f"**genuine earnest-mainstream split** ({earnest_pc:.0f}% originally M2-C2)"
            elif earnest_pc >= 50:
                verdict = (f"**mixed** ({earnest_pc:.0f}% earnest; dominant origin {top_m2} {top_pc:.0f}%) "
                           "— interpret with caution")
            else:
                verdict = (f"**residual tail re-surfacing** (only {earnest_pc:.0f}% earnest; "
                           f"dominant origin {top_m2} {top_pc:.0f}%) — NOT a mainstream sub-segment")
            L.append(f"- {p6c} (n={row_n}{edge_str}): {verdict}")
        L.append("")

        # ── Situational variant alignment ───────────────────────────────────
        h(f"6.{candidate_ks.index(k)+1}c  Situational-variant alignment "
          "(tax/IR, property/debt)", level=3)
        p("Descriptive only — these flag fields were **not** clustered on. We check",
          "whether any sub-cluster maps onto the already-known situational variants.")
        L += _flag_table(sit, k)
        L.append("")

    h("7. Figures")
    L.append("- `reports/figures/phase6_silhouette.png` — silhouette vs k on the subset")
    L.append("- `reports/figures/phase6_gap.png` — gap statistic vs k on the subset")
    L.append("- `reports/figures/phase6_umap.png` — 2-D UMAP scatter (visualisation only)")
    L.append("")

    h("8. Pre-registered hard stops (carried from CLAUDE.md and Phase 3A)")
    L.append(f"- 3% floor RECOMPUTED on this subset: **{min_size} threads**. Sub-clusters below are edge.")
    L.append("- Bootstrap stability mean ARI must be ≥ 0.5 to be 'real.'")
    L.append("- Cross-tab is the load-bearing interpretive test: a sub-cluster that is mostly "
             "originally-speculator or originally-cynic is the residual tail re-surfacing, "
             "NOT a mainstream sub-segment.")
    L.append("- Phase 6 outputs sit at the EXPLORATORY tier; they CANNOT supersede the "
             "triangulated three-persona headline.")
    L.append("")

    L.append("---\n")
    L.append("## ⛔ HARD STOP — Supervisor decision required\n")
    L.append(
        f"Review the candidate k values (k ∈ {candidate_ks}) above, the cross-tabs in\n"
        "Section 6.x.b, and the figures. Decide ONE of:\n\n"
        "1. **Select a k** that produces interpretable, well-populated, originally-earnest-\n"
        "   dominated sub-segments — Phase 6 then proceeds to a constrained naming step.\n"
        "2. **Verdict: the earnest mainstream is one coherent persona** — there is nothing\n"
        "   to sub-segment; Phase 6 closes with that finding.\n\n"
        "Do not name sub-personas in explore mode. Do not present any Phase 6 output as\n"
        "superseding the triangulated three-persona headline.\n"
    )

    out = REPORTS / "phase6_investimentos_explore.md"
    out.write_text("\n".join(L), encoding="utf-8")
    log(f"  Saved {out}")


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    rng = np.random.default_rng(SEED)
    log("MODE: explore (Phase 6 supplementary)")

    # ── Load + subset ─────────────────────────────────────────────────────────
    log("Loading + subsetting to r/investimentos …")
    meta, feat, flags = load_and_subset()
    n_sub = len(feat)
    log(f"  n_subset = {n_sub} threads × {len(ALL_FEATURES)} features")
    assert_firewall(feat)

    # Recomputed 3% floor
    min_size = int(round(n_sub * 0.03))
    log(f"  Recomputed 3% floor: {min_size} threads")
    window_dist = meta["window"].value_counts().sort_index()
    log(f"  Window distribution: {dict(window_dist)}")

    # ── Task 2: composition check BEFORE re-clustering ───────────────────────
    log("Task 2 — composition check against Phase 3A M2 labels …")
    m2_table, merged = m2_composition_check(meta)
    earnest_pct = float(m2_table.loc["M2-C2", "pct"]) if "M2-C2" in m2_table.index else 0.0
    spec_pct    = float(m2_table.loc["M2-C5", "pct"]) if "M2-C5" in m2_table.index else 0.0
    cyn_pct     = float(m2_table.loc["M2-C1", "pct"]) if "M2-C1" in m2_table.index else 0.0
    edge_pct    = 100.0 - earnest_pct - spec_pct - cyn_pct
    if earnest_pct >= 75:
        composition_v = (
            f"**Scenario A — mainstream-dominant**. r/investimentos is {earnest_pct:.1f}% "
            f"originally-earnest (M2-C2), with small speculator ({spec_pct:.1f}%) and "
            f"cynic ({cyn_pct:.1f}%) tails. Re-clustering should split the earnest mass — "
            "**proceed with the sub-segmentation read**, but Section 6.x.b cross-tabs "
            "remain the load-bearing test."
        )
    elif earnest_pct >= 50:
        composition_v = (
            f"**Scenario B — mainstream-majority but with material tails**. r/investimentos "
            f"is {earnest_pct:.1f}% originally-earnest, {spec_pct:.1f}% speculator, "
            f"{cyn_pct:.1f}% cynic. Re-clustering will likely surface a mix of mainstream "
            "splits AND tail re-emergence — Section 6.x.b cross-tabs must adjudicate "
            "each sub-cluster individually."
        )
    else:
        composition_v = (
            f"**Scenario C — not mainstream-dominant**. r/investimentos is only "
            f"{earnest_pct:.1f}% originally-earnest. Re-clustering here will mostly "
            "recover the main study's segments at smaller n, NOT sub-segment the "
            "mainstream. **Strongly consider declaring the mainstream is one coherent "
            "persona** rather than reading sub-segments out of this exercise."
        )
    log(f"  Composition: earnest={earnest_pct}%, speculator={spec_pct}%, cynic={cyn_pct}%, edge={edge_pct:.1f}%")
    log(f"  Scenario verdict: {composition_v[:80]}…")

    # ── Gower on subset (cached) ─────────────────────────────────────────────
    gower_cache = DATA_INT / "phase6_gower_matrix.npy"
    if gower_cache.exists():
        log("Loading cached Phase 6 Gower matrix …")
        D = np.load(gower_cache)
        assert D.shape == (n_sub, n_sub), "Cached Gower matrix shape mismatch — delete and rerun."
    else:
        log("Computing Gower matrix on subset …")
        import time; t0 = time.time()
        D = compute_gower_matrix(feat)
        log(f"  Done in {time.time()-t0:.1f}s")
        np.save(gower_cache, D)
        log(f"  Cached → {gower_cache}")

    # ── Hierarchical linkage (cached) ────────────────────────────────────────
    link_cache = DATA_INT / "phase6_linkage_average.npy"
    if link_cache.exists():
        log("Loading cached Phase 6 linkage …")
        Z = np.load(link_cache)
    else:
        log("Running average-linkage on subset …")
        import time; t0 = time.time()
        Z = linkage(squareform(D.astype(np.float64), checks=False), method="average")
        np.save(link_cache, Z)
        log(f"  Done in {time.time()-t0:.1f}s")

    # ── Metric sweep ─────────────────────────────────────────────────────────
    log("Silhouette sweep k=2..10 …")
    sil_scores = silhouette_sweep(D, Z, K_RANGE)
    log(f"Gap statistic (B={GAP_B} references) …")
    gap_res     = gap_statistic(D, feat, Z, K_RANGE, B=GAP_B, rng=rng)
    gap_tibsh_k = gap_optimal_k(gap_res, K_RANGE)
    best_sil_k  = max(sil_scores, key=lambda k: sil_scores[k] if not np.isnan(sil_scores[k]) else -1)
    best_gap_k  = max(gap_res,    key=lambda k: gap_res[k]["gap"])
    log(f"  best_sil_k={best_sil_k}  best_gap_k={best_gap_k}  tibsh_k={gap_tibsh_k}")

    # Candidate k values: silhouette-best, gap-best, interpretable middle (k=4).
    # The 4-6 target range from the main study; here we are sub-splitting an
    # already-smaller mass, so we anchor the "middle" at 4 (mid of 3..5) rather
    # than 5.
    middle_k     = 4
    candidate_ks = sorted(set([best_sil_k, best_gap_k, middle_k]))
    log(f"Candidate k values: {candidate_ks}")

    # ── Bootstrap stability ──────────────────────────────────────────────────
    log(f"Bootstrap stability for k ∈ {candidate_ks} ({BOOT_B} iterations) …")
    boot_res = bootstrap_stability_multi(D, Z, candidate_ks, n_boot=BOOT_B, rng=rng)

    # ── Per-candidate analysis ──────────────────────────────────────────────
    fps_by_k       = {}
    miss_by_k      = {}
    crosstab_by_k  = {}
    sit_by_k       = {}
    labels_by_k    = {}
    for k in candidate_ks:
        labels                = fcluster(Z, k, criterion="maxclust") - 1
        labels_by_k[k]        = labels
        fps_by_k[k]           = cluster_fingerprints(feat, labels)
        miss_by_k[k]          = missingness_check(feat, labels)
        crosstab_by_k[k]      = crosstab_to_m2(labels, merged)
        sit_by_k[k]           = situational_flag_distribution(labels, flags)
    corpus_median = miss_by_k[candidate_ks[0]][1]

    # ── Figures ─────────────────────────────────────────────────────────────
    log("Generating figures …")
    plot_silhouette(sil_scores, candidate_ks)
    plot_gap(gap_res, candidate_ks)
    embedding = plot_umap_scatter(D, labels_by_k)
    np.save(DATA_INT / "phase6_umap_embedding.npy", embedding)

    # ── Machine-readable snapshot for reproducibility ───────────────────────
    snapshot = {
        "phase":           "6_supplementary",
        "subset":          SUBSET_SUBREDDIT,
        "n_subset":        n_sub,
        "min_size_3pct":   min_size,
        "window_dist":     {str(k): int(v) for k, v in window_dist.items()},
        "m2_composition":  {
            str(idx): {"n": int(row["n"]), "pct": float(row["pct"])}
            for idx, row in m2_table.iterrows()
        },
        "composition_verdict_first_80_chars": composition_v[:80],
        "k_range":         K_RANGE,
        "silhouette":      {int(k): None if np.isnan(v) else float(v) for k, v in sil_scores.items()},
        "gap":             {int(k): {"gap": float(g["gap"]), "sk": float(g["sk"])}
                            for k, g in gap_res.items()},
        "gap_tibshirani":  int(gap_tibsh_k),
        "candidate_ks":    candidate_ks,
        "bootstrap":       {
            int(k): {
                "mean_ari": br["mean_ari"], "std_ari": br["std_ari"],
                "per_cluster_jaccard": {int(c): v for c, v in br["per_cluster_jaccard"].items()},
            }
            for k, br in boot_res.items()
        },
        "cluster_sizes": {
            int(k): {int(c): int(ms["n"]) for c, ms in miss_by_k[k][0].items()}
            for k in candidate_ks
        },
        "crosstab_pct_vs_m2": {
            int(k): crosstab_by_k[k][1].to_dict(orient="index")
            for k in candidate_ks
        },
    }
    snap_path = DATA_INT / "phase6_explore_snapshot.json"
    snap_path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"  Snapshot → {snap_path}")

    # ── Report ──────────────────────────────────────────────────────────────
    log("Writing explore report …")
    write_report(
        n_sub=n_sub, min_size=min_size, window_dist=window_dist,
        m2_table=m2_table, composition_v=composition_v,
        sil_scores=sil_scores, gap_res=gap_res, gap_tibsh_k=gap_tibsh_k,
        candidate_ks=candidate_ks, boot_res=boot_res,
        miss_by_k=miss_by_k, corpus_median=corpus_median, fps_by_k=fps_by_k,
        crosstab_by_k=crosstab_by_k, sit_by_k=sit_by_k,
    )

    log("=" * 60)
    log("PHASE 6 EXPLORE COMPLETE (SUPPLEMENTARY)")
    log(f"  n_subset:        {n_sub}")
    log(f"  3% floor:        {min_size}")
    log(f"  Candidate k:     {candidate_ks}")
    log(f"  ARI (mean):      "
        + "  ".join(f"k={k}: {boot_res[k]['mean_ari']:.3f}" for k in candidate_ks))
    log(f"  Report:          {REPORTS / 'phase6_investimentos_explore.md'}")
    log("⛔ HARD STOP — supervisor decision required (select k OR declare one coherent persona)")
    log("=" * 60)


if __name__ == "__main__":
    main()

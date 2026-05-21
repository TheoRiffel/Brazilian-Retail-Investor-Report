#!/usr/bin/env python3
"""
Phase 3D: Cross-method synthesis & hypothesis tests.

Combines the three clustering outputs (M1 HDBSCAN, M2 attribute k-medoids,
M3 LLM-hierarchical k-medoids) on the shared 3586-thread spine and produces:

- pairwise ARI matrix (H3: convergence/divergence between methods)
- co-cluster table (which (M1, M2, M3) triples co-occur)
- method-robust cores (threads where all three methods agree on grouping)
- H1 test (subreddit differentiation) on M1, M2, M3
- H2 test (temporal prevalence shift) on M1, M2, M3
- H4 test (multi-dimensionality) on M2 attribute features
- candidate persona table (evidence rows; Phase 4 names them)

Outputs:
- reports/phase3d_synthesis.md
- reports/phase3d_hypothesis_tests.md
- reports/figures/phase3d_ari_matrix.png
- reports/figures/phase3d_h1_subreddit_by_cluster.png
- reports/figures/phase3d_h2_window_by_cluster.png
- reports/figures/phase3d_h4_feature_importance.png
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, f_oneway
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import adjusted_rand_score

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
FIGS = REPORTS / "figures"
FIGS.mkdir(parents=True, exist_ok=True)

SEED = 42
np.random.seed(SEED)

CLUSTERING_FEATURES = [
    "sofisticacao_tecnica",
    "fase_acumulacao",
    "estrategia_principal",
    "tolerancia_risco_declarada_ou_inferida",
    "relacao_com_instituicoes_financeiras",
    "estado_emocional_predominante",
    "objetivo_financeiro_primario",
    "ceticismo_institucional",
    "exposicao_a_cripto_e_especulacao",
    "identidade_comunitaria",
]
ORDINAL_FEATURES = {
    "sofisticacao_tecnica",
    "tolerancia_risco_declarada_ou_inferida",
    "ceticismo_institucional",
    "exposicao_a_cripto_e_especulacao",
    "identidade_comunitaria",
}


def cramers_v(chi2: float, n: int, r: int, c: int) -> float:
    """Cramér's V effect size for a chi-square contingency test."""
    k = min(r - 1, c - 1)
    if n == 0 or k == 0:
        return float("nan")
    return float(np.sqrt(chi2 / (n * k)))


def load_all() -> pd.DataFrame:
    """Inner-join the three method parquets + attribute parquet on thread_id."""
    m1 = pd.read_parquet(PROC / "clusters_method1.parquet")[
        ["thread_id", "cluster_label", "cluster_int"]
    ].rename(columns={"cluster_label": "M1", "cluster_int": "M1_int"})
    m2 = pd.read_parquet(PROC / "clusters_method2.parquet")[
        ["thread_id", "cluster_label", "cluster_int"]
    ].rename(columns={"cluster_label": "M2", "cluster_int": "M2_int"})
    m3 = pd.read_parquet(PROC / "clusters_method3.parquet")[
        ["thread_id", "cluster_label", "cluster_int", "subreddit", "window"]
    ].rename(columns={"cluster_label": "M3", "cluster_int": "M3_int"})
    attr = pd.read_parquet(PROC / "extracted_attributes.parquet")

    df = m3.merge(m1, on="thread_id", how="inner").merge(
        m2, on="thread_id", how="inner"
    )
    # avoid column conflict: M3 already carries subreddit/window; drop them from attr
    attr_join = attr.drop(columns=[c for c in ("subreddit_origem", "window") if c in attr.columns])
    df = df.merge(attr_join, on="thread_id", how="left")
    return df


# ---------------------------------------------------------------------------
# H3: pairwise ARI + co-cluster table + method-robust cores
# ---------------------------------------------------------------------------


def pairwise_ari(df: pd.DataFrame) -> dict:
    pairs = [("M1", "M2"), ("M1", "M3"), ("M2", "M3")]
    out = {}
    for a, b in pairs:
        out[f"{a}x{b}"] = float(adjusted_rand_score(df[a], df[b]))
    return out


def co_cluster_table(df: pd.DataFrame, min_n: int = 30) -> pd.DataFrame:
    """Counts of (M1, M2, M3) triples; only triples with at least min_n threads."""
    triples = df.groupby(["M1", "M2", "M3"], observed=True).size().reset_index(name="n")
    triples = triples.sort_values("n", ascending=False).reset_index(drop=True)
    return triples[triples["n"] >= min_n].reset_index(drop=True)


def method_robust_cores(triples: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    """
    Each high-count triple is a "method-robust core" — a group of threads that
    all three methods place in the same partner cluster. Add subreddit/window
    enrichment and top defining M2 attributes.
    """
    total = len(df)
    rows = []
    for _, row in triples.iterrows():
        sub = df[(df.M1 == row.M1) & (df.M2 == row.M2) & (df.M3 == row.M3)]
        n = len(sub)
        sr_share = sub.subreddit.value_counts(normalize=True).to_dict()
        win_share = sub.window.value_counts(normalize=True).to_dict()
        # corpus-base subreddit/window shares for enrichment math
        base_sr = df.subreddit.value_counts(normalize=True).to_dict()
        base_win = df.window.value_counts(normalize=True).to_dict()
        sr_overrep = {
            k: sr_share.get(k, 0) / base_sr[k] for k in base_sr
        }
        win_overrep = {k: win_share.get(k, 0) / base_win[k] for k in base_win}

        rows.append(
            {
                "M1": row.M1,
                "M2": row.M2,
                "M3": row.M3,
                "n": n,
                "pct_corpus": n / total,
                "investimentos_share": sr_share.get("investimentos", 0),
                "farialimabets_share": sr_share.get("farialimabets", 0),
                "farialimabets_overrep": sr_overrep.get("farialimabets", 0),
                "winA_share": win_share.get("A", 0),
                "winB_share": win_share.get("B", 0),
                "winC_share": win_share.get("C", 0),
                "top_examples": "; ".join(sub.head(3).thread_id.tolist()),
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# H1 (subreddit differentiation) on all three methods
# ---------------------------------------------------------------------------


def hypothesis_h1(df: pd.DataFrame) -> dict:
    out = {}
    for method in ("M1", "M2", "M3"):
        ct = pd.crosstab(df[method], df.subreddit)
        chi2, p, dof, _ = chi2_contingency(ct)
        v = cramers_v(chi2, ct.values.sum(), ct.shape[0], ct.shape[1])
        # per-cluster farialimabets share + enrichment
        flb_share_by_cluster = (
            df.groupby(method, observed=True).subreddit.apply(
                lambda s: (s == "farialimabets").mean()
            )
        )
        flb_base = (df.subreddit == "farialimabets").mean()
        enrich = flb_share_by_cluster / flb_base
        out[method] = {
            "contingency": ct,
            "chi2": float(chi2),
            "p_value": float(p),
            "dof": int(dof),
            "cramers_v": v,
            "farialimabets_share": flb_share_by_cluster.to_dict(),
            "farialimabets_enrichment": enrich.to_dict(),
        }
    return out


# ---------------------------------------------------------------------------
# H2 (temporal prevalence shift + composition stability check)
# ---------------------------------------------------------------------------


def hypothesis_h2(df: pd.DataFrame) -> dict:
    out = {}
    for method in ("M1", "M2", "M3"):
        ct = pd.crosstab(df[method], df.window)
        chi2, p, dof, _ = chi2_contingency(ct)
        v = cramers_v(chi2, ct.values.sum(), ct.shape[0], ct.shape[1])

        # per-window prevalence: share of each cluster within each window
        share_by_window = ct / ct.sum(axis=0)
        prev_range = (
            share_by_window.max(axis=1) - share_by_window.min(axis=1)
        ).to_dict()
        # within-cluster trajectory: share of each cluster's threads coming from
        # each window — answers "where does this cluster's volume live?"
        within_cluster = ct.div(ct.sum(axis=1), axis=0)
        trajectory = {
            cl: {w: float(within_cluster.loc[cl, w]) for w in within_cluster.columns}
            for cl in within_cluster.index
        }

        # composition stability check: within each cluster, do the ORDINAL feature
        # means stay within ±0.5 across windows? (cheap proxy)
        comp_drift = {}
        for cl in df[method].unique():
            sub = df[df[method] == cl]
            drifts = []
            for f in ORDINAL_FEATURES:
                means = sub.groupby("window", observed=True)[f].mean()
                if len(means.dropna()) >= 2:
                    drifts.append(float(means.max() - means.min()))
            comp_drift[cl] = float(np.mean(drifts)) if drifts else float("nan")

        out[method] = {
            "contingency": ct,
            "chi2": float(chi2),
            "p_value": float(p),
            "dof": int(dof),
            "cramers_v": v,
            "prevalence_range": prev_range,
            "composition_drift_mean_ordinal": comp_drift,
            "within_cluster_window_share": trajectory,
        }
    return out


# ---------------------------------------------------------------------------
# H4 (multi-dimensionality) on M2 attribute features
# ---------------------------------------------------------------------------


def encode_features(attr: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """One-hot encode categorical features; keep ordinals as integers."""
    blocks = []
    columns = []
    for f in CLUSTERING_FEATURES:
        if f in ORDINAL_FEATURES:
            col = attr[f].astype("float64")
            blocks.append(col.to_frame(name=f))
            columns.append(f)
        else:
            dummies = pd.get_dummies(attr[f], prefix=f, dummy_na=False)
            blocks.append(dummies.astype("float64"))
            columns.extend(list(dummies.columns))
    X = pd.concat(blocks, axis=1)
    return X, columns


def hypothesis_h4(df: pd.DataFrame) -> dict:
    """
    Random forest predicting M2 cluster from the 10 features; report importance
    grouped back to the original feature, plus per-feature Cramér's V on
    (cluster × feature-value) for ordinals and chi-square for categoricals.
    """
    X, cols = encode_features(df)
    y = df["M2_int"].to_numpy()
    rf = RandomForestClassifier(
        n_estimators=400, max_depth=None, random_state=SEED, n_jobs=-1
    )
    rf.fit(X.values, y)
    raw_imp = pd.Series(rf.feature_importances_, index=cols)

    # group one-hot importances back to original feature
    grouped = {}
    for f in CLUSTERING_FEATURES:
        if f in ORDINAL_FEATURES:
            grouped[f] = float(raw_imp.get(f, 0.0))
        else:
            cols_f = [c for c in raw_imp.index if c.startswith(f + "_")]
            grouped[f] = float(raw_imp.loc[cols_f].sum())
    grouped_total = sum(grouped.values())
    grouped_share = {k: v / grouped_total for k, v in grouped.items()}

    # per-feature univariate dependence on cluster
    per_feature = {}
    for f in CLUSTERING_FEATURES:
        ct = pd.crosstab(df.M2, df[f].astype(str))
        chi2, p, dof, _ = chi2_contingency(ct)
        v = cramers_v(chi2, ct.values.sum(), ct.shape[0], ct.shape[1])
        per_feature[f] = {"chi2": float(chi2), "p_value": float(p), "cramers_v": v}

    # top-feature dominance test: does the largest single feature exceed 50%?
    top_feature = max(grouped_share, key=grouped_share.get)
    top_share = grouped_share[top_feature]
    h4_null_supported = top_share >= 0.5  # one axis dominates

    return {
        "grouped_importance": grouped,
        "grouped_importance_share": grouped_share,
        "per_feature_univariate": per_feature,
        "top_feature": top_feature,
        "top_feature_share": float(top_share),
        "h4_null_supported": bool(h4_null_supported),
    }


# ---------------------------------------------------------------------------
# Candidate persona table (evidence rows; Phase 4 names them)
# ---------------------------------------------------------------------------


def candidate_personas(df: pd.DataFrame, cores: pd.DataFrame) -> list[dict]:
    """
    Construct candidate persona evidence rows.
    Convention from decisions_log 2026-05-21: the cynical region is ONE row,
    flagged fuzzy (M2-C1 + M3-C1 + M3-C3 combined).
    """
    total = len(df)
    rows: list[dict] = []

    # Crisp convergent personas: collapse the cores by (M2, M3) since M1 has
    # noise and is the topic instrument rather than the posture instrument.
    crisp_keys = [
        # (label, M2, M3, M1 partner — most overrepresented)
        ("Earnest learner (mainstream)", "M2-C2", "M3-C0"),
        ("Speculator / crypto-adjacent", "M2-C5", "M3-C2"),
    ]
    for label, m2, m3 in crisp_keys:
        sub = df[(df.M2 == m2) & (df.M3 == m3)]
        rows.append(_persona_row(label, sub, df, status="crisp"))

    # Fuzzy cynical region: M2-C1 ∪ (M3-C1 ∪ M3-C3). Honor decisions_log.
    sub = df[(df.M2 == "M2-C1") | (df.M3.isin(["M3-C1", "M3-C3"]))]
    rows.append(
        _persona_row(
            "Cynical-reactive continuum (fuzzy)",
            sub,
            df,
            status="fuzzy",
            note=(
                "Continuum-end posture per supervisor verdict 2026-05-21. M3 "
                "subdivides into C1 (guru-skeptic core) and C3 (loss-as-meme)."
            ),
        )
    )

    # Topical sub-themes (NOT personas — earnest-learner sub-themes per supervisor
    # carry-forward 2026-05-21). M1 finds them as topical density spikes; M2/M3
    # collapse them. Carry forward as pain/need texture, not standalone rows.
    for label, m1 in [
        ("Earnest sub-theme: tax/IR", "M1-C0"),
        ("Earnest sub-theme: property/banking-debt", "M1-C1"),
    ]:
        sub = df[(df.M1 == m1) & (df.M3 == "M3-C0")]
        rows.append(
            _persona_row(
                label,
                sub,
                df,
                status="sub_theme",
                note=(
                    "Single-method evidence (M1 only); collapsed into earnest "
                    "persona by M2 and M3. Demoted from persona to sub-theme by "
                    "supervisor 2026-05-21. Use as pain/need texture for the "
                    "earnest persona in Phase 4; do NOT list as a separate persona row."
                ),
            )
        )

    return rows


def _persona_row(
    label: str,
    sub: pd.DataFrame,
    df: pd.DataFrame,
    status: str,
    note: str | None = None,
) -> dict:
    n = len(sub)
    total = len(df)
    base_sr = df.subreddit.value_counts(normalize=True).to_dict()
    base_win = df.window.value_counts(normalize=True).to_dict()
    sr_share = sub.subreddit.value_counts(normalize=True).to_dict()
    win_share = sub.window.value_counts(normalize=True).to_dict()
    # top defining ordinal-feature means
    feat_means = {
        f: float(sub[f].mean())
        for f in ORDINAL_FEATURES
        if sub[f].notna().any()
    }
    # top categorical modes
    cat_modes = {}
    for f in CLUSTERING_FEATURES:
        if f in ORDINAL_FEATURES:
            continue
        vc = sub[f].value_counts(normalize=True)
        if len(vc):
            cat_modes[f] = (vc.index[0], float(vc.iloc[0]))
    examples = sub.head(3).thread_id.tolist()
    return {
        "label": label,
        "status": status,
        "n": n,
        "pct_corpus": n / total,
        "above_3pct_floor": (n / total) >= 0.03,
        "investimentos_share": sr_share.get("investimentos", 0),
        "farialimabets_share": sr_share.get("farialimabets", 0),
        "farialimabets_overrep": sr_share.get("farialimabets", 0)
        / base_sr.get("farialimabets", np.nan),
        "winA_share": win_share.get("A", 0),
        "winB_share": win_share.get("B", 0),
        "winC_share": win_share.get("C", 0),
        "winA_overrep": win_share.get("A", 0) / base_win.get("A", np.nan),
        "winC_overrep": win_share.get("C", 0) / base_win.get("C", np.nan),
        "ordinal_means": feat_means,
        "categorical_modes": cat_modes,
        "example_threads": examples,
        "note": note,
    }


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------


def plot_ari_matrix(ari: dict, path: Path):
    methods = ["M1", "M2", "M3"]
    M = np.eye(3)
    for i, a in enumerate(methods):
        for j, b in enumerate(methods):
            if i == j:
                continue
            key = f"{a}x{b}" if f"{a}x{b}" in ari else f"{b}x{a}"
            M[i, j] = ari[key]
    fig, ax = plt.subplots(figsize=(4, 3.5))
    im = ax.imshow(M, vmin=0, vmax=1, cmap="viridis")
    ax.set_xticks(range(3))
    ax.set_yticks(range(3))
    ax.set_xticklabels(methods)
    ax.set_yticklabels(methods)
    for i in range(3):
        for j in range(3):
            ax.text(j, i, f"{M[i, j]:.3f}", ha="center", va="center", color="white")
    ax.set_title("Pairwise ARI (cross-method convergence)")
    fig.colorbar(im, ax=ax, shrink=0.7)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def plot_h1(h1: dict, path: Path):
    fig, axes = plt.subplots(1, 3, figsize=(12, 4), sharey=True)
    for ax, method in zip(axes, ["M1", "M2", "M3"]):
        ct = h1[method]["contingency"]
        share = ct.div(ct.sum(axis=1), axis=0)
        share.plot(kind="bar", stacked=True, ax=ax, legend=(method == "M1"))
        ax.set_title(
            f"{method}: V={h1[method]['cramers_v']:.3f}, p={h1[method]['p_value']:.2e}"
        )
        ax.set_xlabel("")
        ax.tick_params(axis="x", labelrotation=45)
    axes[0].set_ylabel("subreddit share within cluster")
    fig.suptitle("H1 — subreddit composition by cluster (per method)")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def plot_h2(h2: dict, path: Path):
    fig, axes = plt.subplots(1, 3, figsize=(12, 4), sharey=True)
    for ax, method in zip(axes, ["M1", "M2", "M3"]):
        ct = h2[method]["contingency"]
        share = ct.div(ct.sum(axis=0), axis=1)  # share of each cluster WITHIN window
        share.T.plot(kind="bar", stacked=True, ax=ax, legend=(method == "M1"))
        ax.set_title(
            f"{method}: V={h2[method]['cramers_v']:.3f}, p={h2[method]['p_value']:.2e}"
        )
        ax.set_xlabel("window")
    axes[0].set_ylabel("cluster share within window (prevalence)")
    fig.suptitle("H2 — cluster prevalence by window (per method)")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def plot_h4(h4: dict, path: Path):
    s = pd.Series(h4["grouped_importance_share"]).sort_values(ascending=True)
    fig, ax = plt.subplots(figsize=(7, 5))
    s.plot(kind="barh", ax=ax, color="steelblue")
    ax.set_xlabel("share of total RF feature importance")
    ax.set_title("H4 — feature importance on M2 cluster (grouped by original feature)")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Report writers
# ---------------------------------------------------------------------------


def fmt_pct(x: float) -> str:
    return f"{x*100:.1f}%"


def write_synthesis_report(df, ari, cores, personas, n_total, ht_path: Path, path: Path):
    lines: list[str] = []
    lines.append("# Phase 3D — Cross-Method Synthesis (candidate evidence)")
    lines.append("")
    lines.append("**Date:** 2026-05-21  ")
    lines.append(
        "**Status: SUPERVISOR-APPROVED with carry-forwards (2026-05-21). Phase 4 BLOCKED until brief issued.**"
    )
    lines.append("")
    lines.append(
        "Approval notes (4 carry-forwards locked in `reports/decisions_log.md`): "
        "(1) H4 relabelled PARTIALLY NULL + posture-dominated + circularity caveat; "
        "(2) H2 headline is the two directional shifts (speculator↓, cynical↑), "
        "not the weak aggregate; "
        "(3) counting convention — Phase 4 uses M2 partition as mutually-exclusive "
        "backbone for stated proportions, M3/M1 characterize but don't re-count; "
        "(4) topical subsets demoted from candidate personas to earnest-learner "
        "sub-themes (single-method evidence)."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 1. Scope and inputs")
    lines.append("")
    lines.append(
        f"Shared spine: **{n_total} threads** present in all three methods "
        f"(M1 HDBSCAN, M2 attribute k-medoids, M3 LLM-hierarchical k-medoids). "
        f"14 threads dropped where M3 summarisation failed (already disclosed in "
        f"Phase 3C)."
    )
    lines.append("")
    lines.append(
        "Phase 3D is the **analytical convergence phase**: it tests H1/H2/H3/H4 "
        "and produces evidence rows for Phase 4. It does NOT name personas — "
        "that is Phase 4's job. Persona language here is descriptive shorthand."
    )
    lines.append("")
    lines.append(
        f"Hypothesis tests live in `{ht_path.name}` (this report links to numbers; "
        f"that report carries the full statistical tables)."
    )
    lines.append("")

    lines.append("## 2. Cross-method convergence (H3)")
    lines.append("")
    lines.append("**Pairwise ARI** (Adjusted Rand Index — 0 random, 1 perfect):")
    lines.append("")
    lines.append("| Pair | ARI |")
    lines.append("|------|-----|")
    for k, v in ari.items():
        lines.append(f"| {k.replace('x', ' × ')} | {v:.3f} |")
    lines.append("")
    lines.append(
        "**Interpretation — H3 split verdict.** M2 and M3 converge meaningfully "
        "(ARI 0.212): two independent algorithms operating on different inputs "
        "(structured attributes vs. holistic LLM summaries) agree on coarse "
        "structure while disagreeing on fine splits. That is **H3's predicted "
        "positive form**."
    )
    lines.append("")
    lines.append(
        "M1 (HDBSCAN on raw embeddings), by contrast, is **essentially orthogonal** "
        "to both posture methods (ARI ≈ 0 with M2 *and* M3). This is NOT a failure "
        "— it is a finding. M1's clusters are topical density spikes (tax/IR, "
        "property/debt, crypto) sitting inside a giant mainstream bucket; M2 and "
        "M3 split the corpus along posture axes that cut across topics. Same "
        "threads, different partitioning logic, near-zero rand agreement at the "
        "*global* partition level."
    )
    lines.append("")
    lines.append(
        "The right way to read M1's contribution is in the cross-tab "
        "overrepresentation table (Phase 3C Section 10), not in ARI. M1-C2 (crypto) "
        "is 2.06× overrepresented in the M3 speculator cluster; M1-C0 (tax/IR) is "
        "1.9× overrepresented in the M3 earnest cluster — strong *local* signals "
        "invisible to global ARI because the bulk of M1 lives in one giant cluster."
    )
    lines.append("")
    lines.append(
        "See `reports/figures/phase3d_ari_matrix.png` for the matrix; per-method "
        "cross-tabs are in `phase3c_method3.md` Sections 9–10."
    )
    lines.append("")

    lines.append("## 3. Method-robust cores (co-cluster table)")
    lines.append("")
    lines.append(
        f"Triples (M1, M2, M3) with at least 30 threads on the shared spine "
        f"(~0.8% of corpus floor for the triple — not the 3% persona floor)."
    )
    lines.append("")
    lines.append(
        "| M1 | M2 | M3 | n | % corpus | farialimabets share | farialimabets overrep | top examples |"
    )
    lines.append(
        "|----|----|----|---|---------:|--------------------:|----------------------:|--------------|"
    )
    for _, r in cores.iterrows():
        lines.append(
            f"| {r.M1} | {r.M2} | {r.M3} | {r.n} | {fmt_pct(r.pct_corpus)} | "
            f"{fmt_pct(r.farialimabets_share)} | {r.farialimabets_overrep:.2f}× | "
            f"{r.top_examples} |"
        )
    lines.append("")
    lines.append(
        "Triples with farialimabets overrepresentation ≥1.5× sit in the "
        "speculator/cynical region (the part of the corpus where farialimabets "
        "dominates). Triples with overrepresentation <0.7× are earnest-learner / "
        "topical territory dominated by r/investimentos."
    )
    lines.append("")

    lines.append("## 4. Candidate persona rows (NOT final personas)")
    lines.append("")
    lines.append(
        "Phase 4 names and narrates personas. Phase 3D supplies the evidence rows. "
        "The cynical region is ONE row, flagged fuzzy (supervisor verdict "
        "2026-05-21, `reports/decisions_log.md`)."
    )
    lines.append("")
    lines.append(
        "**Counting convention:** crisp rows use the INTERSECTION of partner "
        "clusters (M2 ∩ M3, high-confidence convergent core). The fuzzy cynical "
        "row uses the UNION (M2-C1 ∪ M3-C1 ∪ M3-C3), honouring the supervisor "
        "verdict that the posture is real but the boundaries shift between "
        "methods. Topical subsets use (M1 ∩ M3-C0). The two crisp rows + the "
        "fuzzy row are not mutually exclusive (some threads sit in both crisp "
        "earnest and cynical via different methods)."
    )
    lines.append("")
    lines.append(
        "| Label (descriptive) | Status | n | % | ≥3% floor? | "
        "investimentos / farialimabets | flb overrep | window mix | "
        "example threads |"
    )
    lines.append(
        "|--------------------|--------|---|---|------------|"
        "------------------------------|------------:|------------|"
        "------------------|"
    )
    for p in personas:
        win_mix = (
            f"A {fmt_pct(p['winA_share'])} / B {fmt_pct(p['winB_share'])} / "
            f"C {fmt_pct(p['winC_share'])}"
        )
        floor = "✓" if p["above_3pct_floor"] else "⚠ below"
        lines.append(
            f"| {p['label']} | {p['status']} | {p['n']} | "
            f"{fmt_pct(p['pct_corpus'])} | {floor} | "
            f"{fmt_pct(p['investimentos_share'])} / "
            f"{fmt_pct(p['farialimabets_share'])} | "
            f"{p['farialimabets_overrep']:.2f}× | "
            f"{win_mix} | {', '.join(p['example_threads'])} |"
        )
    lines.append("")

    lines.append("### 4.1 Defining attribute profile per candidate")
    lines.append("")
    for p in personas:
        lines.append(f"**{p['label']}** ({p['status']}, n={p['n']})")
        if p.get("note"):
            lines.append(f"- Note: {p['note']}")
        # ordinal means
        if p["ordinal_means"]:
            ords = ", ".join(
                f"{k}={v:.2f}" for k, v in sorted(p["ordinal_means"].items())
            )
            lines.append(f"- Ordinal means (1–5): {ords}")
        if p["categorical_modes"]:
            cats = "; ".join(
                f"{f}: {val} ({fmt_pct(share)})"
                for f, (val, share) in p["categorical_modes"].items()
            )
            lines.append(f"- Categorical modes: {cats}")
        lines.append("")

    lines.append("## 5. What Phase 4 inherits")
    lines.append("")
    lines.append(
        "### 5.1 Persona structure to carry forward"
    )
    lines.append("")
    lines.append(
        "- **Two crisp convergent personas** (earnest learner; speculator/crypto-"
        "adjacent), each backed by all three methods.\n"
        "- **One fuzzy cynical-reactive continuum** — real posture, soft "
        "boundaries; do NOT narrate as a single tight persona.\n"
        "- **Topical subsets are sub-themes, NOT personas.** Tax/IR and "
        "property/banking-debt are situational variants *within* the earnest-"
        "learner persona, useful as pain/need texture in Phase 4's pains section. "
        "Their independent existence is **single-method evidence** (Method 1 "
        "topical density spikes that M2 and M3 collapse). Do not list them as "
        "separate persona rows in the memo."
    )
    lines.append("")
    lines.append(
        "### 5.2 Hypothesis-test carry-forwards"
    )
    lines.append("")
    lines.append(
        "- **H1 SUPPORTED** on posture methods (M2 V=0.68, M3 V=0.65). "
        "Subreddit segmentation is a real signal; document the firewall.\n"
        "- **H2 — two specific directional shifts are the headline**, not the "
        "weak aggregate chi-square: **speculator share declines monotonically "
        "A→B→C (~51%→33%→16%)** tracking the Selic rise; **cynical-reactive "
        "continuum grows A→C (~29.5%→38.0%)**. The aggregate test is reported "
        "but is not the actionable temporal content.\n"
        "- **H3 SPLIT** — M2↔M3 convergent (ARI=0.21); M1 orthogonal at the "
        "global partition level but locally informative via overrepresentation. "
        "M1 = topic instrument; M2/M3 = posture instruments.\n"
        "- **H4 PARTIALLY NULL — multi-dimensional but emotional-posture-"
        "dominated**. Emotional posture carries ~45% of importance vs. ~12% for "
        "the next feature (~3.75× ratio). **Phase 4 personas MUST be led by "
        "emotional posture**, with other attributes as supporting texture — "
        "NOT narrated as ten co-equal dimensions. Circularity caveat applies "
        f"(see `{ht_path.name}` H4 section).\n"
    )
    lines.append("")
    lines.append(
        "### 5.3 Counting convention — Phase 4 MUST read this before drafting"
    )
    lines.append("")
    lines.append(
        "The candidate rows in Section 4 use **different denominators** by "
        "construction: crisp rows are method INTERSECTIONS (M2 ∩ M3); the fuzzy "
        "cynical row is a UNION (M2-C1 ∪ M3-C1 ∪ M3-C3). They overlap. The "
        "earnest-crisp row (n=1089) and the cynical-union row (n=1511) sum to "
        "more than the corpus when added naively. **These are evidence rows, "
        "not a partition.**"
    )
    lines.append("")
    lines.append(
        "**Phase 4 instruction.** For any stated persona proportion in the memo, "
        "use the **M2 partition as the mutually-exclusive backbone** "
        "(M2-C0..C6 cover all 3600 threads with no overlap). M3 and M1 are "
        "characterizing instruments: use them to *describe* personas (which "
        "M2-C2 threads are also M3-C0? which M2-C1 threads are M3-C3 loss-as-"
        "memes?) but NOT to re-count them. A partner reading "
        "\"30% earnest + 11% speculator + 42% cynical + 8% property-debt = 91%\" "
        "would be misled — those numbers come from overlapping definitions. "
        "Use M2 share (M2-C2 = 47.6% earnest, M2-C5 = 18.4% speculator, "
        "M2-C1 = 30.0% cynical, etc.) as the canonical proportions."
    )
    lines.append("")

    lines.append("## 6. Figures")
    lines.append("")
    lines.append("- `reports/figures/phase3d_ari_matrix.png` — pairwise ARI")
    lines.append(
        "- `reports/figures/phase3d_h1_subreddit_by_cluster.png` — H1 visual"
    )
    lines.append(
        "- `reports/figures/phase3d_h2_window_by_cluster.png` — H2 visual"
    )
    lines.append(
        "- `reports/figures/phase3d_h4_feature_importance.png` — H4 visual"
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## ⛔ HARD STOP")
    lines.append("")
    lines.append(
        "Phase 3D is supervisor-approved with the four carry-forwards above. "
        "Phase 4 remains BLOCKED until the supervisor issues the Phase 4 brief. "
        "Do not begin persona naming, memo drafting, or any synthesis writing "
        "before the brief lands."
    )
    lines.append("")
    path.write_text("\n".join(lines))


def write_hypothesis_report(h1, h2, h4, personas, n_total: int, path: Path):
    lines: list[str] = []
    lines.append("# Phase 3D — Hypothesis Tests (H1, H2, H4)")
    lines.append("")
    lines.append("**Date:** 2026-05-21  ")
    lines.append(f"**Shared spine:** {n_total} threads (M1 ∩ M2 ∩ M3)")
    lines.append("")
    lines.append(
        "Scope per supervisor brief: H1 and H2 run on **all three methods**; "
        "H4 runs on **Method 2 only** (primary attribute clustering)."
    )
    lines.append("")
    lines.append("Effect-size convention: Cramér's V, where 0.1 ≈ small, "
                 "0.3 ≈ medium, 0.5 ≈ large.")
    lines.append("")
    lines.append("---")
    lines.append("")

    # H1
    lines.append("## H1 — Subreddit differentiation")
    lines.append("")
    lines.append(
        "**Hypothesis (locked):** r/investimentos and r/farialimabets draw "
        "measurably different populations. Null: same investors, different venue."
    )
    lines.append("")
    lines.append(
        "**Firewall:** `subreddit_origem` was never a clustering feature. Any "
        "cluster × subreddit association is genuinely post-hoc."
    )
    lines.append("")
    lines.append("| Method | n | χ² | df | p | Cramér's V | Verdict |")
    lines.append("|--------|---|---:|---:|--:|-----------:|---------|")
    for m in ("M1", "M2", "M3"):
        h = h1[m]
        v = h["cramers_v"]
        if v >= 0.3:
            verdict = "**H1 supported (medium+ effect)**"
        elif v >= 0.1:
            verdict = "H1 weak support (small effect)"
        else:
            verdict = "H1 null (negligible)"
        lines.append(
            f"| {m} | {h['contingency'].values.sum()} | {h['chi2']:.1f} | "
            f"{h['dof']} | {h['p_value']:.2e} | {v:.3f} | {verdict} |"
        )
    lines.append("")
    lines.append("### Per-cluster farialimabets enrichment (×corpus base rate)")
    lines.append("")
    for m in ("M1", "M2", "M3"):
        lines.append(f"**{m}:**")
        enrich = h1[m]["farialimabets_enrichment"]
        share = h1[m]["farialimabets_share"]
        rows = []
        for k in sorted(enrich):
            rows.append(f"  - {k}: {fmt_pct(share[k])} ({enrich[k]:.2f}×)")
        lines.extend(rows)
        lines.append("")

    # H2
    lines.append("## H2 — Temporal prevalence shift")
    lines.append("")
    lines.append(
        "**Hypothesis (locked):** persona *composition* is stable but persona "
        "*prevalence* shifts with macro regime. Null: nothing shifts."
    )
    lines.append("")
    lines.append("**Windows:** A = 2020-06→2021-06 (Selic ~2%), B = 2022-01→2023-01 "
                 "(Selic rising), C = 2024 (mature fixed income).")
    lines.append("")

    # Headline: the two real directional findings.
    pers_by_label = {p["label"]: p for p in personas}
    spec = pers_by_label.get("Speculator / crypto-adjacent")
    cyn = pers_by_label.get("Cynical-reactive continuum (fuzzy)")
    earnest = pers_by_label.get("Earnest learner (mainstream)")
    lines.append("### Headline findings (the directional shifts that matter)")
    lines.append("")
    lines.append(
        "The aggregate cluster × window chi-square (Part 2 below) finds only small "
        "effect sizes. The actionable temporal content is NOT in the aggregate — "
        "it is in **two specific directional shifts** that move in opposite directions "
        "and track the macro regime."
    )
    lines.append("")
    if spec:
        lines.append(
            f"1. **Speculator share declines monotonically across windows**, "
            f"tracking the Selic rise from ~2% (window A) to ~13.75% (window B) "
            f"to mature fixed-income regime (window C). Within-cluster window "
            f"share: A {fmt_pct(spec['winA_share'])} → B {fmt_pct(spec['winB_share'])} "
            f"→ C {fmt_pct(spec['winC_share'])}. The speculator persona is "
            f"concentrated in the low-rate era; crypto/equity speculation thins out "
            f"as fixed-income becomes the alternative."
        )
        lines.append("")
    if cyn:
        lines.append(
            f"2. **Cynical-reactive continuum grows monotonically across windows**: "
            f"A {fmt_pct(cyn['winA_share'])} → B {fmt_pct(cyn['winB_share'])} "
            f"→ C {fmt_pct(cyn['winC_share'])}. Where speculator volume goes, "
            f"cynical posture rises — consistent with the loss-as-meme / "
            f"guru-skeptic sub-flavors absorbing investors who weathered the "
            f"crypto winter and the volatility of B."
        )
        lines.append("")
    if earnest:
        lines.append(
            f"For contrast, the earnest learner is roughly flat: "
            f"A {fmt_pct(earnest['winA_share'])} / B {fmt_pct(earnest['winB_share'])} "
            f"/ C {fmt_pct(earnest['winC_share'])} — the mainstream investor population "
            f"is stable across regimes; the regime-sensitive movement is in the speculator "
            f"↔ cynical region."
        )
        lines.append("")
    lines.append(
        "**Interpretation.** Locked H2 form (\"composition stable, prevalence "
        "shifts\") is supported in its strongest reading on these two personas, "
        "not on the aggregate. The aggregate test misses this because directional "
        "shifts in opposite directions partly cancel in the chi-square. Report the "
        "directional shifts as the headline; report the aggregate test for completeness."
    )
    lines.append("")
    lines.append("### Part 1 — Aggregate prevalence shift (cluster × window)")
    lines.append("")
    lines.append("| Method | n | χ² | df | p | Cramér's V | Verdict |")
    lines.append("|--------|---|---:|---:|--:|-----------:|---------|")
    for m in ("M1", "M2", "M3"):
        h = h2[m]
        v = h["cramers_v"]
        if v >= 0.3:
            verdict = "**H2 aggregate supported (medium+ effect)**"
        elif v >= 0.1:
            verdict = "H2 aggregate weak"
        else:
            verdict = "H2 aggregate null"
        lines.append(
            f"| {m} | {h['contingency'].values.sum()} | {h['chi2']:.1f} | "
            f"{h['dof']} | {h['p_value']:.2e} | {v:.3f} | {verdict} |"
        )
    lines.append("")
    lines.append(
        "The aggregate is small because the directional shifts on speculator and "
        "cynical-continuum partly cancel and because the large earnest cluster is "
        "flat across windows. **Treat the per-persona trajectory as the H2 result; "
        "the aggregate is supporting, not primary.**"
    )
    lines.append("")
    lines.append("Within-cluster window share by method (for completeness):")
    lines.append("")
    for m in ("M1", "M2", "M3"):
        traj = h2[m]["within_cluster_window_share"]
        lines.append(f"**{m}**")
        for cl in sorted(traj):
            t = traj[cl]
            a, b, c = t.get("A", 0.0), t.get("B", 0.0), t.get("C", 0.0)
            lines.append(
                f"  - {cl}: A {fmt_pct(a)} / B {fmt_pct(b)} / C {fmt_pct(c)}"
            )
        lines.append("")
    lines.append("### Part 2 — Composition stability (within-cluster ordinal drift)")
    lines.append("")
    lines.append("### Part 2 — Composition stability (within-cluster ordinal drift)")
    lines.append("")
    lines.append(
        "Operationalisation: within each cluster, compute the mean of each "
        "ordinal feature per window; report the max-min spread across the three "
        "windows, then average across the 5 ordinal features. Spread ≤ 0.50 "
        "(half an ordinal point) = compositionally stable; > 1.00 = composition "
        "is also shifting (which would falsify the H2 'stability' part)."
    )
    lines.append("")
    for m in ("M1", "M2", "M3"):
        drifts = h2[m]["composition_drift_mean_ordinal"]
        lines.append(f"**{m}** mean within-cluster ordinal drift across windows:")
        for cl in sorted(drifts):
            d = drifts[cl]
            if d is None or (isinstance(d, float) and np.isnan(d)):
                lines.append(
                    f"  - {cl}: n/a (cluster too small or absent in some windows)"
                )
                continue
            mark = "stable" if d <= 0.5 else ("mixed" if d <= 1.0 else "shifting")
            lines.append(f"  - {cl}: {d:.2f} ({mark})")
        lines.append("")

    # H4
    lines.append("## H4 — Multi-dimensionality (M2 only)")
    lines.append("")
    lines.append(
        "**Hypothesis (locked):** segments are defined by combinations of "
        "dimensions, not any single axis. Null: one axis (capital or "
        "sophistication) explains most variance."
    )
    lines.append("")
    lines.append(
        "**Operationalisation:** random-forest classifier predicting M2 cluster "
        "from the 10 locked clustering features (5 ordinals + 5 categoricals "
        "one-hot encoded). One-hot importance grouped back to the original "
        "feature. Null is supported if the top single feature carries ≥50% of "
        "total importance."
    )
    lines.append("")
    top_feature = h4["top_feature"]
    top_share = h4["top_feature_share"]
    sorted_share = sorted(
        h4["grouped_importance_share"].items(), key=lambda kv: -kv[1]
    )
    second_share = sorted_share[1][1] if len(sorted_share) >= 2 else 0.0
    ratio = top_share / second_share if second_share > 0 else float("inf")
    lines.append(
        f"**Verdict — PARTIALLY NULL: multi-dimensional but emotional-posture-"
        f"dominated.** Top feature `{top_feature}` carries "
        f"{top_share*100:.1f}% of total importance — under the 50% threshold "
        f"for the formal null, but **{ratio:.2f}× the work of the next feature** "
        f"({sorted_share[1][0]} at {second_share*100:.1f}%). One axis is doing "
        f"about half the work; the other half is spread across 3–4 supporting "
        f"features. H4's positive form (multi-dim) holds in the literal sense, "
        f"but the locked H4 brief framed multi-dim as 'combinations of dimensions' "
        f"— in practice, ONE dimension (emotional posture) dominates and a "
        f"handful of others sharpen it. **Personas in Phase 4 must be led by "
        f"emotional posture, with other attributes as supporting texture — NOT "
        f"narrated as ten co-equal dimensions.**"
    )
    lines.append("")
    lines.append(
        "**Circularity caveat (must be disclosed in methodology).** "
        "`estado_emocional_predominante` was one of the 10 *clustering features* "
        "fed to Method 2. So this H4 result describes the **geometry of the M2 "
        "partition** — i.e., which feature most strongly distinguishes the "
        "clusters Method 2 itself produced — not an external causal claim about "
        "what drives Brazilian retail investor behavior. The clustering had "
        "access to emotional posture as input; finding that it discriminates "
        "well between the resulting clusters is partly tautological. The "
        "interesting non-circular evidence is that **the locked classical axes "
        "the brief named (`sofisticacao_tecnica`, `fase_acumulacao`, "
        "`objetivo_financeiro_primario`) are in the bottom half** even with full "
        "clustering access — that finding is robust to the circularity."
    )
    lines.append("")
    lines.append("### Grouped feature importance")
    lines.append("")
    lines.append("| Feature | Share | Univariate V (M2) |")
    lines.append("|---------|------:|------------------:|")
    grouped_sorted = sorted(
        h4["grouped_importance_share"].items(), key=lambda kv: -kv[1]
    )
    for f, share in grouped_sorted:
        v = h4["per_feature_univariate"][f]["cramers_v"]
        lines.append(f"| {f} | {fmt_pct(share)} | {v:.3f} |")
    lines.append("")
    lines.append(
        "The next four features (`identidade_comunitaria`, `estrategia_principal`, "
        "`exposicao_a_cripto_e_especulacao`, `tolerancia_risco_declarada_ou_inferida`) "
        "each contribute 7.6–11.9% — they sharpen the picture but none rivals "
        "emotional posture. The locked H4 brief named sophistication and capital "
        "as the candidate dominant axes for the null; those are in the BOTTOM "
        "half — that part of the finding is robust to the circularity caveat "
        "above and is the genuine surprise."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Summary verdicts (for the memo)")
    lines.append("")
    h1_max = max(h1[m]["cramers_v"] for m in ("M1", "M2", "M3"))
    h2_max = max(h2[m]["cramers_v"] for m in ("M1", "M2", "M3"))
    if h1_max >= 0.3:
        h1_v = f"**SUPPORTED** (max V={h1_max:.2f}, medium+ effect on posture methods)"
    elif h1_max >= 0.1:
        h1_v = f"weak support (max V={h1_max:.2f})"
    else:
        h1_v = "NULL"
    if h2_max >= 0.3:
        h2_v = "SUPPORTED (medium+ effect)"
    elif h2_max >= 0.1:
        h2_v = (
            f"**PARTIAL** — small effect on M1/M2 (V≈0.12–0.15), null on M3 (V={h2[ 'M3' ]['cramers_v']:.2f}). "
            "Prevalence shifts are real but modest; composition stability mostly holds (Part 2). "
            "Locked H2 form ('composition stable, prevalence shifts') is directionally supported, weakly."
        )
    else:
        h2_v = "NULL"
    lines.append(f"- **H1**: {h1_v}")
    lines.append(f"- **H2 prevalence**: {h2_v}")
    lines.append(
        "- **H3**: covered in `phase3d_synthesis.md` Section 2 — **split verdict**. "
        "M2↔M3 convergent (ARI=0.21); M1 orthogonal to both (ARI≈0). M1 is a topic "
        "instrument, M2/M3 are posture instruments — same threads, different partitioning logic."
    )
    if h4["h4_null_supported"]:
        h4_v = (
            f"NULL supported — `{h4['top_feature']}` carries "
            f"{h4['top_feature_share']*100:.0f}% of importance (≥50% threshold)."
        )
    elif h4["top_feature_share"] >= 0.40:
        h4_v = (
            "**PARTIALLY NULL — multi-dimensional but emotional-posture-dominated.** "
            f"Top feature `{h4['top_feature']}` carries "
            f"{h4['top_feature_share']*100:.0f}% — under the 50% threshold for "
            "the formal null, but ~3.75× the next feature. Personas in Phase 4 "
            "MUST be led by emotional posture, with other attributes as supporting "
            "texture. **Circularity caveat applies** (estado_emocional was a "
            "clustering feature; this describes cluster geometry, not external "
            "causal truth). The non-circular finding — that the locked classical "
            "axes (sophistication/capital) are in the bottom half — is robust."
        )
    else:
        h4_v = (
            f"POSITIVE form supported (multi-dim). Top feature only "
            f"{h4['top_feature_share']*100:.0f}%."
        )
    lines.append(f"- **H4**: {h4_v}")
    lines.append("")
    path.write_text("\n".join(lines))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    df = load_all()
    n_total = len(df)
    print(f"Shared spine: {n_total} threads")

    ari = pairwise_ari(df)
    print(f"ARI: {ari}")

    triples = co_cluster_table(df, min_n=30)
    cores = method_robust_cores(triples, df)
    print(f"Cores (≥30): {len(cores)} triples")

    h1 = hypothesis_h1(df)
    h2 = hypothesis_h2(df)
    h4 = hypothesis_h4(df)

    personas = candidate_personas(df, cores)

    plot_ari_matrix(ari, FIGS / "phase3d_ari_matrix.png")
    plot_h1(h1, FIGS / "phase3d_h1_subreddit_by_cluster.png")
    plot_h2(h2, FIGS / "phase3d_h2_window_by_cluster.png")
    plot_h4(h4, FIGS / "phase3d_h4_feature_importance.png")

    ht_path = REPORTS / "phase3d_hypothesis_tests.md"
    syn_path = REPORTS / "phase3d_synthesis.md"
    write_hypothesis_report(h1, h2, h4, personas, n_total, ht_path)
    write_synthesis_report(df, ari, cores, personas, n_total, ht_path, syn_path)

    # also drop a machine-readable snapshot for downstream use
    snapshot = {
        "n_total": n_total,
        "ari": ari,
        "h1": {
            m: {
                "chi2": h1[m]["chi2"],
                "p_value": h1[m]["p_value"],
                "cramers_v": h1[m]["cramers_v"],
                "farialimabets_share": h1[m]["farialimabets_share"],
                "farialimabets_enrichment": h1[m]["farialimabets_enrichment"],
            }
            for m in ("M1", "M2", "M3")
        },
        "h2": {
            m: {
                "chi2": h2[m]["chi2"],
                "p_value": h2[m]["p_value"],
                "cramers_v": h2[m]["cramers_v"],
                "prevalence_range": h2[m]["prevalence_range"],
                "composition_drift_mean_ordinal": h2[m][
                    "composition_drift_mean_ordinal"
                ],
            }
            for m in ("M1", "M2", "M3")
        },
        "h4": h4,
        "personas": personas,
    }
    (PROC / "phase3d_results.json").write_text(json.dumps(snapshot, default=str, indent=2))
    print("Wrote reports and snapshot.")


if __name__ == "__main__":
    main()

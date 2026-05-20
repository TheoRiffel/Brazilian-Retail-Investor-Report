"""Phase 0 data survey — runs all tasks T2–T7, saves all interim outputs."""

import json
import random
import math
import datetime
import warnings
from pathlib import Path
from collections import defaultdict

import zstandard as zstd
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from langdetect import detect, LangDetectException

warnings.filterwarnings("ignore")

SEED = 42
random.seed(SEED)

BASE = Path("/home/theoriffel/codes/decade-ba-case")
RAW  = BASE / "data/raw/reddit/subreddits24"
INT  = BASE / "data/interim"
REP  = BASE / "reports"
FIG  = REP / "figures"

INT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

FILES = {
    "investimentos": {
        "submissions": RAW / "investimentos_submissions.zst",
        "comments":    RAW / "investimentos_comments.zst",
    },
    "farialimabets": {
        "submissions": RAW / "farialimabets_submissions.zst",
        "comments":    RAW / "farialimabets_comments.zst",
    },
}

STUDY_WINDOWS = {
    "A": ("2020-06", "2021-06"),
    "B": ("2022-01", "2023-01"),
    "C": ("2024-01", "2024-12"),
}

BOT_AUTHORS = {"AutoModerator", "RemindMeBot", "RepostSleuthBot", "tipbot", "reddit-tipbot"}


def stream_zst(path):
    """Yield parsed JSON objects line-by-line from a .zst file."""
    dctx = zstd.ZstdDecompressor(max_window_size=2**31)
    with open(path, "rb") as fh:
        with dctx.stream_reader(fh) as reader:
            buf = b""
            while True:
                chunk = reader.read(1 << 20)  # 1 MB chunks
                if not chunk:
                    break
                buf += chunk
                lines = buf.split(b"\n")
                buf = lines[-1]
                for line in lines[:-1]:
                    line = line.strip()
                    if line:
                        try:
                            yield json.loads(line)
                        except json.JSONDecodeError:
                            pass
            if buf.strip():
                try:
                    yield json.loads(buf)
                except json.JSONDecodeError:
                    pass


def utc_to_ym(ts):
    try:
        return datetime.datetime.utcfromtimestamp(int(ts)).strftime("%Y-%m")
    except Exception:
        return None


def utc_to_date(ts):
    try:
        return datetime.datetime.utcfromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return None


def ym_in_window(ym, w):
    """True if year-month string ym is in window w (inclusive start, inclusive end)."""
    if ym is None:
        return False
    start, end = STUDY_WINDOWS[w]
    return start <= ym <= end


# ─────────────────────────────────────────────
# T2 — File inventory
# ─────────────────────────────────────────────
print("=== Task 2: File inventory ===")
inventory = {}

for sub, paths in FILES.items():
    for kind, path in paths.items():
        key = f"{sub}_{kind}"
        size_mb = path.stat().st_size / 1e6
        n_total = 0
        n_deleted_bot = 0
        earliest = None
        latest = None

        for obj in stream_zst(path):
            n_total += 1
            author = obj.get("author", "")
            if author in ("[deleted]", "AutoModerator"):
                n_deleted_bot += 1
            ts = obj.get("created_utc")
            if ts:
                ts = int(ts)
                if earliest is None or ts < earliest:
                    earliest = ts
                if latest is None or ts > latest:
                    latest = ts

        inventory[key] = {
            "path": str(path),
            "size_mb": round(size_mb, 2),
            "total_records": n_total,
            "deleted_or_automod": n_deleted_bot,
            "earliest_utc": utc_to_date(earliest) if earliest else None,
            "latest_utc":   utc_to_date(latest)   if latest   else None,
        }
        print(f"  {key}: {n_total:,} records, {size_mb:.1f} MB, {utc_to_date(earliest)} → {utc_to_date(latest)}")

with open(INT / "file_inventory.json", "w") as f:
    json.dump(inventory, f, indent=2)

print("  → saved file_inventory.json\n")


# ─────────────────────────────────────────────
# T3 — Monthly volume
# ─────────────────────────────────────────────
print("=== Task 3: Monthly volume ===")

def build_monthly_counts(path, start="2018-01", end="2024-12"):
    counts = defaultdict(int)
    for obj in stream_zst(path):
        ym = utc_to_ym(obj.get("created_utc"))
        if ym and start <= ym <= end:
            counts[ym] += 1
    return counts

sub_monthly = {}   # submissions
com_monthly = {}   # comments

for sub in ["investimentos", "farialimabets"]:
    print(f"  Submissions: {sub}")
    sub_monthly[sub] = build_monthly_counts(FILES[sub]["submissions"])
    print(f"  Comments: {sub}")
    com_monthly[sub] = build_monthly_counts(FILES[sub]["comments"])

# Build date index 2018-01 to 2024-12
idx = pd.period_range("2018-01", "2024-12", freq="M").astype(str).tolist()

def counts_to_df(monthly_dict):
    rows = []
    for sub, counts in monthly_dict.items():
        for ym in idx:
            rows.append({"subreddit": sub, "year_month": ym, "count": counts.get(ym, 0)})
    return pd.DataFrame(rows)

df_sub_vol = counts_to_df(sub_monthly)
df_com_vol = counts_to_df(com_monthly)

df_sub_vol.to_csv(INT / "monthly_volume_submissions.csv", index=False)
df_com_vol.to_csv(INT / "monthly_volume_comments.csv", index=False)


def plot_monthly(df, title, outpath):
    subreddits = df["subreddit"].unique()
    fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

    window_colors = {"A": "#ffe0b2", "B": "#b3e5fc", "C": "#c8e6c9"}
    window_labels = {
        "A": "Window A\n2020-06–2021-06",
        "B": "Window B\n2022-01–2023-01",
        "C": "Window C\n2024-01–2024-12",
    }

    x_labels = df["year_month"].unique()
    x_pos = {ym: i for i, ym in enumerate(sorted(x_labels))}

    for ax, sub in zip(axes, subreddits):
        sub_df = df[df["subreddit"] == sub].sort_values("year_month")
        xs = [x_pos[ym] for ym in sub_df["year_month"]]
        ax.plot(xs, sub_df["count"].values, linewidth=1.5, color="#1565c0")
        ax.fill_between(xs, sub_df["count"].values, alpha=0.15, color="#1565c0")
        ax.set_title(f"r/{sub}", fontsize=11, fontweight="bold")
        ax.set_ylabel("Count")

        # shade study windows
        for w, (ws, we) in STUDY_WINDOWS.items():
            win_xs = [x_pos[ym] for ym in sorted(x_labels) if ws <= ym <= we]
            if win_xs:
                ax.axvspan(win_xs[0] - 0.5, win_xs[-1] + 0.5,
                           alpha=0.4, color=window_colors[w],
                           label=window_labels[w])

        ax.set_xlim(-0.5, len(x_labels) - 0.5)

    # x-axis ticks every 6 months
    tick_pos = [x_pos[ym] for ym in sorted(x_labels) if ym.endswith("-01") or ym.endswith("-07")]
    tick_lbl = [ym for ym in sorted(x_labels) if ym.endswith("-01") or ym.endswith("-07")]
    axes[-1].set_xticks(tick_pos)
    axes[-1].set_xticklabels(tick_lbl, rotation=45, ha="right", fontsize=7)
    axes[-1].set_xlabel("Month")

    patches = [mpatches.Patch(color=window_colors[w], alpha=0.5, label=window_labels[w])
               for w in ["A", "B", "C"]]
    fig.legend(handles=patches, loc="upper right", fontsize=8)
    fig.suptitle(title, fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(outpath, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  → saved {outpath.name}")

plot_monthly(df_sub_vol, "Monthly Submission Volume by Subreddit", FIG / "monthly_volume_submissions.png")
plot_monthly(df_com_vol, "Monthly Comment Volume by Subreddit", FIG / "monthly_volume_comments.png")
print()


# ─────────────────────────────────────────────
# T4 — Window feasibility
# ─────────────────────────────────────────────
print("=== Task 4: Window feasibility ===")

feasibility = []

for sub in ["investimentos", "farialimabets"]:
    # One pass per window per subreddit
    for w, (ws, we) in STUDY_WINDOWS.items():
        n_total = 0
        n_comments_3 = 0
        n_has_text = 0
        authors = set()

        for obj in stream_zst(FILES[sub]["submissions"]):
            ym = utc_to_ym(obj.get("created_utc"))
            if ym is None or not (ws <= ym <= we):
                continue
            n_total += 1
            nc = obj.get("num_comments", 0) or 0
            if nc >= 3:
                n_comments_3 += 1
            st = obj.get("selftext", "") or ""
            if st not in ("", "[deleted]", "[removed]") and len(st) > 50:
                n_has_text += 1
            a = obj.get("author", "")
            if a:
                authors.add(a)

        flag = ""
        if n_comments_3 < 150:
            flag = "AT RISK (n<150)"
        elif n_comments_3 < 300:
            flag = "MARGINAL (n<300)"
        else:
            flag = "VIABLE"

        feasibility.append({
            "subreddit": sub,
            "window": w,
            "window_range": f"{ws}–{we}",
            "total_submissions": n_total,
            "submissions_ge3_comments": n_comments_3,
            "submissions_with_text": n_has_text,
            "unique_authors": len(authors),
            "verdict": flag,
        })
        print(f"  r/{sub} Window {w}: {n_total:,} submissions, {n_comments_3:,} with ≥3 comments → {flag}")

df_feas = pd.DataFrame(feasibility)
df_feas.to_csv(INT / "window_feasibility.csv", index=False)
print("  → saved window_feasibility.csv\n")


# ─────────────────────────────────────────────
# T5 — Author-thread linkage check
# ─────────────────────────────────────────────
print("=== Task 5: Author-thread linkage check ===")

def reservoir_sample_ids(path, k, seed=42):
    """Reservoir sampling: return k submission IDs from stream."""
    rng = random.Random(seed)
    reservoir = []
    n = 0
    for obj in stream_zst(path):
        sid = obj.get("id")
        if not sid:
            continue
        n += 1
        if len(reservoir) < k:
            reservoir.append(sid)
        else:
            j = rng.randint(0, n - 1)
            if j < k:
                reservoir[j] = sid
    return set(reservoir), n

linkage_results = {}

for sub in ["investimentos", "farialimabets"]:
    print(f"  Sampling submissions: r/{sub}")
    # Count total first pass already done in T4 — re-count here cleanly
    sampled_ids, total_n = reservoir_sample_ids(FILES[sub]["submissions"], max(1, total_n // 10) if False else 0, seed=SEED)
    # We need total count; easier: just do one pass
    total_n = 0
    for _ in stream_zst(FILES[sub]["submissions"]):
        total_n += 1
    k = max(1, total_n // 10)

    sampled_ids, _ = reservoir_sample_ids(FILES[sub]["submissions"], k, seed=SEED)
    print(f"    sampled {len(sampled_ids):,} of {total_n:,} submissions")

    # Stream comments and match
    print(f"  Streaming comments: r/{sub}")
    sub_comment_counts = defaultdict(list)  # sid -> [scores]
    for obj in stream_zst(FILES[sub]["comments"]):
        link_id = obj.get("link_id", "")
        if link_id.startswith("t3_"):
            sid = link_id[3:]
            if sid in sampled_ids:
                sub_comment_counts[sid].append(obj.get("score", 0) or 0)

    n_matched = len(sub_comment_counts)
    pct_matched = 100.0 * n_matched / len(sampled_ids) if sampled_ids else 0

    all_counts = [len(v) for v in sub_comment_counts.values()]
    all_scores = [s for scores in sub_comment_counts.values() for s in scores]
    all_scores_sorted = sorted(all_scores)

    def pct(lst, p):
        if not lst:
            return None
        idx = int(len(lst) * p / 100)
        return lst[min(idx, len(lst) - 1)]

    linkage_results[sub] = {
        "sampled_submissions": len(sampled_ids),
        "matched_submissions": n_matched,
        "pct_matched": round(pct_matched, 2),
        "mean_comments_per_matched": round(sum(all_counts) / n_matched, 2) if n_matched else 0,
        "median_comments_per_matched": sorted(all_counts)[len(all_counts)//2] if all_counts else 0,
        "top_comment_score_percentiles": {
            "p10": pct(all_scores_sorted, 10),
            "p25": pct(all_scores_sorted, 25),
            "p50": pct(all_scores_sorted, 50),
            "p75": pct(all_scores_sorted, 75),
            "p90": pct(all_scores_sorted, 90),
        }
    }
    r = linkage_results[sub]
    print(f"    matched: {n_matched:,} ({pct_matched:.1f}%), mean comments: {r['mean_comments_per_matched']}")

with open(INT / "linkage_check.json", "w") as f:
    json.dump(linkage_results, f, indent=2)
print("  → saved linkage_check.json\n")


# ─────────────────────────────────────────────
# T6 — Raw sample inspection (Window C, 2024)
# ─────────────────────────────────────────────
print("=== Task 6: Raw sample inspection (Window C = 2024) ===")

def reservoir_sample_objects(path, k, filter_fn=None, seed=42):
    rng = random.Random(seed)
    reservoir = []
    n = 0
    for obj in stream_zst(path):
        if filter_fn and not filter_fn(obj):
            continue
        n += 1
        if len(reservoir) < k:
            reservoir.append(obj)
        else:
            j = rng.randint(0, n - 1)
            if j < k:
                reservoir[j] = obj
    return reservoir

window_c_start, window_c_end = STUDY_WINDOWS["C"]
wc_filter = lambda o: (utc_to_ym(o.get("created_utc")) or "") >= window_c_start and \
                       (utc_to_ym(o.get("created_utc")) or "") <= window_c_end

raw_samples = {}
for sub in ["investimentos", "farialimabets"]:
    sample = reservoir_sample_objects(FILES[sub]["submissions"], 10, filter_fn=wc_filter, seed=SEED)
    raw_samples[sub] = sample
    print(f"  r/{sub}: sampled {len(sample)} posts from Window C")

# Store for notebook rendering
with open(INT / "raw_samples_window_c.json", "w") as f:
    json.dump(raw_samples, f, indent=2, ensure_ascii=False)
print("  → saved raw_samples_window_c.json\n")


# ─────────────────────────────────────────────
# T7 — Quality scan
# ─────────────────────────────────────────────
print("=== Task 7: Quality scan ===")

quality = {}

for sub in ["investimentos", "farialimabets"]:
    n_total = 0
    n_deleted = 0
    n_removed = 0
    n_empty = 0
    n_link_post = 0
    n_bot = 0
    lengths = []

    # Reservoir 1000 for langdetect
    lang_reservoir = []
    lang_n = 0
    rng = random.Random(SEED)

    for obj in stream_zst(FILES[sub]["submissions"]):
        n_total += 1
        st = obj.get("selftext", "") or ""
        author = obj.get("author", "") or ""
        is_self = obj.get("is_self", True)

        if st == "[deleted]":
            n_deleted += 1
        elif st == "[removed]":
            n_removed += 1
        elif st.strip() == "":
            n_empty += 1

        if not is_self:
            n_link_post += 1
        if author in BOT_AUTHORS:
            n_bot += 1

        if st not in ("[deleted]", "[removed]") and st.strip():
            lengths.append(len(st))

        # reservoir for langdetect
        title = obj.get("title", "") or ""
        text_for_lang = (title + " " + st).strip()
        if text_for_lang:
            lang_n += 1
            if len(lang_reservoir) < 1000:
                lang_reservoir.append(text_for_lang)
            else:
                j = rng.randint(0, lang_n - 1)
                if j < 1000:
                    lang_reservoir[j] = text_for_lang

    # Language detection
    lang_counts = defaultdict(int)
    for text in lang_reservoir:
        try:
            lang = detect(text)
        except LangDetectException:
            lang = "unknown"
        lang_counts[lang] += 1

    total_lang = sum(lang_counts.values())
    lang_pct = {k: round(100 * v / total_lang, 2) for k, v in
                sorted(lang_counts.items(), key=lambda x: -x[1])}

    lengths_sorted = sorted(lengths)
    def pct_val(lst, p):
        if not lst:
            return None
        return lst[int(len(lst) * p / 100)]

    quality[sub] = {
        "total_submissions": n_total,
        "selftext_deleted": {"count": n_deleted, "pct": round(100*n_deleted/n_total, 2)},
        "selftext_removed": {"count": n_removed, "pct": round(100*n_removed/n_total, 2)},
        "selftext_empty":   {"count": n_empty,   "pct": round(100*n_empty/n_total, 2)},
        "link_posts":       {"count": n_link_post,"pct": round(100*n_link_post/n_total, 2)},
        "bot_authors":      {"count": n_bot,      "pct": round(100*n_bot/n_total, 2)},
        "language_distribution_pct": lang_pct,
        "selftext_length": {
            "mean":   round(sum(lengths)/len(lengths), 1) if lengths else 0,
            "median": lengths_sorted[len(lengths_sorted)//2] if lengths_sorted else 0,
            "p10":    pct_val(lengths_sorted, 10),
            "p90":    pct_val(lengths_sorted, 90),
        }
    }
    q = quality[sub]
    print(f"  r/{sub}: {n_total:,} total")
    print(f"    deleted={q['selftext_deleted']['pct']}%, removed={q['selftext_removed']['pct']}%,"
          f" empty={q['selftext_empty']['pct']}%, link={q['link_posts']['pct']}%,"
          f" bots={q['bot_authors']['pct']}%")
    print(f"    lang top-3: {dict(list(lang_pct.items())[:3])}")

with open(INT / "quality_scan.json", "w") as f:
    json.dump(quality, f, indent=2)
print("  → saved quality_scan.json\n")

print("=== All tasks complete. Data saved to data/interim/ and reports/figures/ ===")

"""Build AuthorThread units from raw .zst submission + comment files."""

import json
import random
from collections import defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

import zstandard as zstd

BASE  = Path(__file__).resolve().parent.parent
RAW   = BASE / "data/raw/reddit/subreddits24"

BOT_AUTHORS = {"AutoModerator", "RemindMeBot", "RepostSleuthBot", "tipbot", "reddit-tipbot"}
DELETED_BODIES = {"[deleted]", "[removed]", ""}

STUDY_WINDOWS = {
    "A": ("2020-06", "2021-06"),
    "B": ("2022-01", "2023-01"),
    "C": ("2024-01", "2024-12"),
}

UNIT_MAX_CHARS    = 6000
COMMENT_MAX_CHARS = 800

# Per-subreddit rules
RULES = {
    "investimentos": {
        "top_n_comments": 5,
        "require_selftext": True,   # skip if empty/deleted/removed/<50chars
        "min_comments_for_link": 0, # irrelevant — link posts skipped
    },
    "farialimabets": {
        "top_n_comments": 10,
        "require_selftext": False,  # keep link posts, but mark them
        "min_comments_for_link": 3, # skip link posts with fewer than 3 matching comments
    },
}


@dataclass
class AuthorThread:
    thread_id:    str
    subreddit:    str
    created_utc:  int
    window:       str
    author:       str
    score:        int
    num_comments: int
    unit_text:    str
    is_link_post: bool


def _stream_zst(path: Path):
    dctx = zstd.ZstdDecompressor(max_window_size=2**31)
    with open(path, "rb") as fh:
        with dctx.stream_reader(fh) as reader:
            buf = b""
            while True:
                chunk = reader.read(1 << 20)
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


def _utc_to_ym(ts) -> Optional[str]:
    try:
        import datetime
        return datetime.datetime.fromtimestamp(int(ts), datetime.UTC).strftime("%Y-%m")
    except Exception:
        return None


def _classify_window(ym: Optional[str]) -> Optional[str]:
    if ym is None:
        return None
    for w, (ws, we) in STUDY_WINDOWS.items():
        if ws <= ym <= we:
            return w
    return None


def build_threads(subreddit: str) -> list[AuthorThread]:
    """Stream submissions + comments for a subreddit and return all eligible AuthorThreads."""
    sub_path = RAW / f"{subreddit}_submissions.zst"
    com_path = RAW / f"{subreddit}_comments.zst"
    rules = RULES[subreddit]

    # ── Pass 1: collect eligible submissions ───────────────────────────────
    submissions = {}  # id → sub dict
    for sub in _stream_zst(sub_path):
        ym = _utc_to_ym(sub.get("created_utc"))
        w  = _classify_window(ym)
        if w is None:
            continue
        sid    = sub.get("id", "")
        author = sub.get("author", "") or ""
        if author in BOT_AUTHORS:
            continue

        selftext  = sub.get("selftext", "") or ""
        is_link   = not sub.get("is_self", True)

        if rules["require_selftext"]:
            if selftext in DELETED_BODIES or len(selftext) < 50:
                continue

        submissions[sid] = {
            "id":           sid,
            "author":       author,
            "created_utc":  int(sub.get("created_utc", 0)),
            "window":       w,
            "score":        sub.get("score", 0) or 0,
            "num_comments": sub.get("num_comments", 0) or 0,
            "title":        sub.get("title", "") or "",
            "selftext":     selftext,
            "is_link":      is_link,
        }

    if not submissions:
        return []

    # ── Pass 2: collect comments keyed by submission id ────────────────────
    comments_by_sid: dict[str, list] = defaultdict(list)
    for com in _stream_zst(com_path):
        link_id = com.get("link_id", "")
        if not link_id.startswith("t3_"):
            continue
        sid = link_id[3:]
        if sid not in submissions:
            continue
        author = com.get("author", "") or ""
        if author in BOT_AUTHORS:
            continue
        body = com.get("body", "") or ""
        if body in DELETED_BODIES:
            continue
        comments_by_sid[sid].append({
            "score": com.get("score", 0) or 0,
            "body":  body,
        })

    # ── Build AuthorThread objects ─────────────────────────────────────────
    threads = []
    for sid, s in submissions.items():
        top_coms = sorted(comments_by_sid[sid], key=lambda c: -c["score"])
        top_coms = top_coms[:rules["top_n_comments"]]

        # farialimabets link posts need ≥3 comments
        if s["is_link"] and not rules["require_selftext"]:
            if len(top_coms) < rules["min_comments_for_link"]:
                continue

        # Build unit text
        selftext  = s["selftext"]
        is_link   = s["is_link"]
        body_part = selftext if (selftext and selftext not in DELETED_BODIES) else "[link post]"

        header   = s["title"]
        comments = "\n".join(
            f"[score {c['score']}] {c['body'][:COMMENT_MAX_CHARS]}"
            for c in top_coms
        )
        unit = f"{header}\n\n{body_part}\n\n--- Top comments ---\n{comments}"
        unit = unit[:UNIT_MAX_CHARS]

        threads.append(AuthorThread(
            thread_id    = sid,
            subreddit    = subreddit,
            created_utc  = s["created_utc"],
            window       = s["window"],
            author       = s["author"],
            score        = s["score"],
            num_comments = s["num_comments"],
            unit_text    = unit,
            is_link_post = is_link,
        ))

    return threads


def stratified_sample(threads: list[AuthorThread], n: int = 50, seed: int = 42) -> list[AuthorThread]:
    """
    Sample n threads with stratification:
      20 uniform
      15 from top quartile by num_comments
      15 from bottom-half-but-above-10th-percentile by num_comments
    """
    rng = random.Random(seed)
    if len(threads) <= n:
        return threads

    scores = sorted(t.num_comments for t in threads)
    q25 = scores[len(scores) // 4]
    p10 = scores[len(scores) // 10]
    median = scores[len(scores) // 2]

    top_q   = [t for t in threads if t.num_comments >= q25]
    mid_q   = [t for t in threads if p10 < t.num_comments < median]
    rest    = threads[:]

    n_top  = min(15, len(top_q))
    n_mid  = min(15, len(mid_q))
    n_uni  = n - n_top - n_mid

    sample_top  = rng.sample(top_q, n_top)
    sample_mid  = rng.sample(mid_q, n_mid)
    used_ids    = {t.thread_id for t in sample_top + sample_mid}
    pool_uni    = [t for t in rest if t.thread_id not in used_ids]
    sample_uni  = rng.sample(pool_uni, min(n_uni, len(pool_uni)))

    combined = sample_top + sample_mid + sample_uni
    rng.shuffle(combined)
    return combined[:n]

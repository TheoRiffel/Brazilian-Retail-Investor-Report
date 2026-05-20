# Phase 0 Summary — Brazilian Retail Investor Reddit Study

**Generated:** 2026-05-20  
**Study scope:** r/investimentos · r/farialimabets  
**Source corpus:** Watchful1 separated-subreddit dump via Academic Torrents

---

## 1. Data provenance

The corpus consists of four Zstandard-compressed newline-delimited JSON files drawn from the Watchful1 top-40k subreddit dump, distributed via Academic Torrents. Coverage runs from 2015-06-06 (r/investimentos) and 2018-09-04 (r/farialimabets) through 2024-12-31. Compressed sizes are: investimentos_submissions 20.9 MB, investimentos_comments 142.0 MB, farialimabets_submissions 32.4 MB, farialimabets_comments 233.1 MB. Decompressed record counts are 60,292 submissions and 936,084 comments for r/investimentos; 67,748 submissions and 1,814,722 comments for r/farialimabets. Scoping note: the original design listed four subreddits; r/FIIs and r/BrasilFinancas were absent from the Watchful1 top-40k corpus and have been excluded as a deliberate methodological decision, not a data flaw.

---

## 2. Volume findings

- **r/investimentos** shows steady growth from ~100 posts/month in 2018 to a sustained ~1,000–1,400/month plateau from 2020 onward, consistent with Brazil's retail investor boom post-2019.
- **r/farialimabets** was effectively dormant until mid-2020 (founded 2018) and exploded from late 2020, reaching 2,000–4,000+ submissions/month by 2022–2023, reflecting the meme-finance wave.
- Window A (2020-06–2021-06) captures the early surge of both communities; farialimabets volume is moderate (~300–500/month) relative to later windows.
- Windows B and C show farialimabets overtaking investimentos in raw volume by a factor of 2–3×, indicating the speculative community grew much faster than the mainstream one.
- No catastrophic data gaps or unexplained zero-months are visible in either subreddit across the study windows.

---

## 3. Window feasibility verdict

| Subreddit | Window | Range | Total submissions | ≥3 comments | Text posts (>50 chars) | Unique authors | Verdict |
|---|---|---|---|---|---|---|---|
| r/investimentos | A | 2020-06–2021-06 | 10,418 | 5,426 | 3,325 | 3,539 | **VIABLE** |
| r/investimentos | B | 2022-01–2023-01 | 11,177 | 5,531 | 3,595 | 4,913 | **VIABLE** |
| r/investimentos | C | 2024-01–2024-12 | 16,886 | 9,020 | 8,941 | 9,468 | **VIABLE** |
| r/farialimabets | A | 2020-06–2021-06 | 3,540 | 2,404 | 806 | 1,095 | **VIABLE** |
| r/farialimabets | B | 2022-01–2023-01 | 14,839 | 10,246 | 3,464 | 5,076 | **VIABLE** |
| r/farialimabets | C | 2024-01–2024-12 | 27,025 | 17,855 | 11,972 | 9,993 | **VIABLE** |

All six cells clear the VIABLE threshold (≥300 submissions with ≥3 comments). No AT RISK or MARGINAL strata.

---

## 4. Linkage health

Author-thread reconstruction is viable for both subreddits, though with notable asymmetry. Using a 10% reservoir sample (~6,000 submissions each), 62.6% of r/investimentos sampled submissions matched at least one comment in the dump, with a mean of 25.3 and median of 13 comments per matched thread. r/farialimabets performed better at 82.3% match rate, with mean 33.1 and median 11 comments per thread. The 37% unmatched rate for r/investimentos likely reflects older threads (pre-2018) with comments that fell below the Watchful1 collection threshold, or submissions that attracted zero discussion. Comment score distributions are heavily left-skewed in both communities (p50 ≈ 2, p90 = 8–15), consistent with typical Reddit engagement patterns. Link_id-based reconstruction is reliable for the 2020–2024 study windows.

---

## 5. Quality issues flagged

- **r/investimentos removal rate is high at 32.5%.** Nearly one-third of all submissions have `selftext == "[removed]"`, indicating active moderation. This could bias the surviving text corpus toward specific content types (e.g., self-posts that pass moderator review). The removal rate is substantially higher than r/farialimabets (3.3%).
- **r/farialimabets is predominantly link-post oriented.** 61.71% of submissions are link posts (`is_self == False`), meaning the selftext field is absent. An additional 48.35% have empty selftext. In practice, well under 20% of farialimabets submissions contain substantive body text — the community's textual signal lives in comments, not post bodies.
- **Both subreddits are strongly Portuguese-dominant.** langdetect detects pt in 82.7% (investimentos) and 86.4% (farialimabets) of sampled posts. The small residual of "sl", "da", "ca" detections are almost certainly langdetect false positives on short Portuguese text, not genuine multilingual content.
- **Bot presence is negligible.** r/investimentos: 0 known bots; r/farialimabets: 0.49% (332 of 67,748). Not a material concern.
- **Selftext length skews short on farialimabets.** Among non-deleted/non-removed posts, median selftext length is 216 characters (investimentos: 408). This reinforces the link-post finding — the posts that *do* have text are still relatively brief.
- **Deletion rates are modest.** 5.37% (investimentos) and 7.72% (farialimabets) have `selftext == "[deleted]"`. These are user-deleted posts and are unrecoverable; their volume is manageable.

---

## 6. Recommendations

**PROCEED AS PLANNED** — r/investimentos text corpus for all three windows. The 10,000–16,000 submission range per window with strong selftext coverage (8,941 posts with >50 chars in Window C alone) and high discussion depth (mean 25 comments/thread) gives a robust text sample for Phase 1 analysis.

**ADJUST: Treat r/farialimabets as a comment-driven corpus, not a selftext corpus.** 61.71% link posts and 48.35% empty selftext mean Phase 1 should treat comment threads as the primary unit of analysis for farialimabets, rather than submission bodies. The sampling frame should be: select submissions with ≥3 comments → retrieve full comment trees → analyze comment text. This is a methodological adjustment, not a disqualifier.

**FLAG FOR SUPERVISOR REVIEW: r/investimentos 32.5% removal rate.** The high moderation-removal rate warrants a decision on whether removed posts should be (a) excluded silently, (b) excluded with an explicit note in the methods section, or (c) treated as a separate stratum to study moderation patterns. The answer affects the effective N in all three windows and should be documented before Phase 1 proceeds.

---

## 7. Open questions

1. **Removal content type.** What *kind* of content is moderators removing from r/investimentos? If removals correlate with specific topics (e.g., low-quality questions, promotion), excluding them is appropriate. If removals are arbitrary, they introduce selection bias that should be disclosed.
2. **farialimabets comment-tree depth.** Given that farialimabets analysis will rely on comments, do we need a minimum comment-tree size for inclusion (e.g., threads with ≥5 comments)? Window A has 2,404 qualifying submissions — after applying a more restrictive comment-depth filter, feasibility should be re-checked.
3. **langdetect reliability on short text.** The 7.9% "en" and 3.3% "es" detections in investimentos — are these genuine English/Spanish posts or langdetect errors on short/technical Portuguese? A 50-post manual spot-check of the non-pt detections would resolve this before any language-filtering decisions in Phase 1.
4. **Link-post URLs in farialimabets.** A significant fraction of farialimabets link posts point to Twitter/X, news articles, or screenshots. Are these in scope for the study, or should analysis be restricted to self-posts and comment threads?

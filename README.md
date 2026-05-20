# Decade BA Case — Brazilian Retail Investor Reddit Study

## Project description

Scientific study of Brazilian retail investor sentiment and behaviour using Reddit data.
The study spans three temporal windows (2020-06–2021-06, 2022-01–2023-01, 2024-01–2024-12)
and covers two subreddits: **r/investimentos** (mainstream anchor) and **r/farialimabets**
(speculative edge).

## Data provenance

| Field | Value |
|---|---|
| Source | Watchful1 separated-subreddit dump |
| Distribution | Academic Torrents |
| Coverage | 2005-06 to 2024-12 |
| Format | Zstandard-compressed newline-delimited JSON (one Reddit object per line) |
| Subreddits | r/investimentos, r/farialimabets |

**Scoping note:** The original study design referenced four subreddits (r/investimentos,
r/farialimabets, r/FIIs, r/BrasilFinancas). The latter two were not present in the
Watchful1 top-40k corpus; the scope was narrowed to two subreddits as a deliberate,
defensible methodological decision — not a data flaw.

## Files

```
data/raw/reddit/subreddits24/
    investimentos_submissions.zst   (20 MB compressed)
    investimentos_comments.zst     (136 MB compressed)
    farialimabets_submissions.zst   (31 MB compressed)
    farialimabets_comments.zst     (223 MB compressed)
```

`data/raw/` is **read-only**. All processing writes to `data/interim/` or `data/processed/`.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
jupyter notebook notebooks/
```

## Notebooks

| Notebook | Phase | Description |
|---|---|---|
| 00_phase0_data_survey.ipynb | 0 | Data inventory, quality scan, window feasibility |

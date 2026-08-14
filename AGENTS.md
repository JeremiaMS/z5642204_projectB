# AGENTS.md — FINS5545 Part B (z5642204)

> Read PROJECT_BRIEF.md and the context/ folder (DATA_GUIDE.md, project_context.md) first — they define the task, the data, and the rules.

## Project
This is my Part B: systematically managed multi-asset funds plus a news-sentiment
analytic, delivered as a Streamlit app, built on my own Part A data foundation.
The data (50 US equities, 10 cryptocurrencies, and their news headlines, 2020–2023)
is loaded through the provided helper `src/data_access.py`, which downloads one hosted
ZIP — no scraping and no API keys. I use the `opencode` agent for coding, and I direct
and check every change myself.

I chose to build five funds — the Combined family across all three optimisation methods,
plus an Equity-only and a Crypto-only fund — so I can compare methods and compare asset
families.  << edit: put this in your own words / adjust if you change the fund set >>

## How I want you (the agent) to work
- Always show me a PLAN before editing any file, and wait for my approval.
- After a change, show the diff and tell me exactly how to test it.
- Make focused changes — don't refactor or touch files I didn't ask about.
- If something is ambiguous, ask me rather than guessing.
- I review the plan, read the diff, run the code, check the numbers by hand, and record
  the prompt, your output, and my correction in `ai/prompt_log.md`.

## Repository layout
- `src/` — my code. `etl.py` and `features.py` are reused/trimmed from my Part A
  (cleaning, returns, combined panel, headline panel). `portfolios.py` (backtest +
  optimisers), `sentiment.py` (VADER index), `fusion.py` (sentiment tilt).
- `scripts/` — `run_part_b.py` reproduces all results; `make_figures.py` builds the
  report figures from the CSVs.
- `results/` — outputs only: `data/` (app-readable CSVs), `tables/`, `figures/`.
- `streamlit_app.py` — the app at the repo root.
- `ai/` — my prompt logs and notes.

## Hard rules (do not break)
1. NO look-ahead. Portfolio weights and the sentiment signal use only past data. The
   backtest estimates weights strictly before each rebalance date; sentiment is lagged
   by at least one trading day.
2. Annualise equities with 252 trading days, crypto with 365.
3. The Streamlit app must READ ONLY the precomputed CSVs in `results/`. It must NOT
   import nltk, run VADER, or run a backtest at request time (the free deploy tier
   cannot). Do not import `src/portfolios`, `src/sentiment`, or `src/fusion` in the app.
4. Never commit raw data or `.parquet`/source files. Data loads only via
   `src/data_access.py`; it is never written to the repo.
5. Use these EXACT output filenames (the app and markers depend on them):
   `results/data/fund_returns.csv`, `results/data/fund_weights.csv`,
   `results/data/sector_sentiment_index.csv`, `results/tables/performance_metrics.csv`.
6. VADER's one-time `nltk.download('vader_lexicon')` is a build step in
   `run_part_b.py`, never in the app.

## Testing
- Reproduce everything: `python scripts/run_part_b.py`.
- Build figures: `python scripts/make_figures.py`.
- Run the app: `streamlit run streamlit_app.py`.
- Pre-hand-in: `python scripts/check_handin.py` and fix every [FAIL].

## Sanity checks I care about
- The optimisers must produce genuinely different weights across methods (a stalled
  solver silently returns equal weights — scale the covariance to avoid it).
- The first live backtest date is after the initial estimation window, not the first
  date in the data.

## A mistake I caught
<< edit: write one real example in your own words — e.g. the first figures had an
unreadable 60-asset legend and a crypto-dominated growth chart, so I flagged three
figures for a readability fix; or: I noticed Combined Max-Sharpe was crypto-heavy in
2021, which explained its high volatility. >>

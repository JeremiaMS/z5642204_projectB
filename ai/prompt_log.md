
## 1. 10 July 9.06 PM
## What I wanted
To rebuild the ETL loaders after the project reset: load all three
datasets (equity prices, crypto prices, news headlines) through the
provided data_access.py helper and verify row counts, date ranges, and
duplicate counts against the data dictionary before writing any other
code - with all logic in src/etl.py and the run script only calling it.

## Prompt(s)
"Read PROJECT_BRIEF.md and context/DATA_GUIDE.md. Then write functions in
src/etl.py that load all three datasets through src/data_access.py and
report: row counts, date ranges, and duplicate counts for each dataset
(news dedupes on ticker+date+title). Wire them into scripts/run_part_a.py
- the script only imports and calls, all logic stays in src/etl.py.
Don't write anything else yet - I want to verify the numbers first."

## What the assistant produced
load_clean_equities(), load_clean_crypto(), load_clean_news(), and
load_all_datasets() in src/etl.py; scripts/run_part_a.py only imports
and runs load_all_datasets. It verified every number against the data
dictionary unprompted: equities 50,300 rows / 50 tickers / 10 sectors;
crypto 14,620 raw -> 14,610 after removing the 10 stray 2024-01-01
rows; news 149,683 raw -> 146,836 after removing exactly 2,847
duplicates on ticker+date+title. No duplicates in either price dataset.

## What was wrong or risky
Nothing needed correcting this run. The risks I watched for - the wrong
news dedup key (ticker+date alone would wrongly flag ~104k legitimate
rows), manual pd.read_csv instead of the helper, ETL logic leaking into
the run script - did not occur; the AGENTS.md hard rules were followed
without intervention, including the dedup key and the crypto cap.

## What I changed and why
Nothing. All counts matched the data dictionary (PROJECT_BRIEF.md
Appendix A) on the first run, including the exact 2,847 duplicate
figure, which independently confirms the dedup key. Approved as the
Station 1 base. Noted: this is a rebuild - the same loaders were built
and verified to identical numbers in the pre-reset sessions of 10 Jul
(see disclosure header), so the first-run success partly reflects
lessons already encoded into AGENTS.md.

## 2. 10 July 9.13 pm
## What I wanted
A validation script that checks the rebuilt ETL output is correct -
without hard-coding numbers I have no defensible source for. Expected
values had to come either from the brief's own data dictionary
(Appendix A) or from the data's internal logic, so the validation is
principled rather than circular. Kept as a permanent regression test.

## Prompt(s)
"Write a validation script scripts/validate_etl.py with two groups of
checks. Print PASS/FAIL and the actual value for each.

GROUP 1 - reconciliation against the data dictionary (PROJECT_BRIEF.md
Appendix A states these, cite it in a comment):
1. equity raw rows == 50,300
2. crypto raw rows == 14,620, with rows dated after 2023-12-31 == 10
3. news raw rows == 149,683
4. news duplicates on ticker+date+title is approximately 2,847
5. equity has 50 tickers and 10 sectors; crypto has 10 tickers

GROUP 2 - internal consistency (derived from the data itself, no
external numbers):
6. equity: 0 duplicates on ticker+date
7. equity: rows == unique trading days x unique tickers (a complete
panel, no missing ticker-days)
8. crypto after capping: rows == unique days x unique tickers
9. news: rows after dedup == raw rows minus duplicates found
10. every ticker in news also exists in equity (same 50-stock universe)
11. news dates are timezone-aware (UTC) before normalisation; price
dates are naive - confirm both, since the merge depends on it
12. equity date range falls within 2020-2023; crypto clean range ends
exactly 2023-12-31
13. all prices strictly positive; volume non-negative
14. every bar internally consistent: low <= open, close, high and
high >= low

If a check fails, report it - do not adjust the check to make it pass.
End with 'X/14 checks passed'."

## What the assistant produced
scripts/validate_etl.py with all 14 checks in the two groups. 14/14
PASS on the first run. Key confirmations: equities are a complete
panel (1,006 trading days x 50 tickers = 50,300, zero gaps); crypto a
complete panel (1,461 days x 10 coins after the cap); all 50 news
tickers intersect the equity universe; raw timezone state confirmed
(news datetime64[us, UTC] vs prices datetime64[s] naive - the exact
mismatch my AGENTS.md normalisation rule exists to handle); bar
integrity holds on every row (prices > 0, volume >= 0,
low <= open/close/high).

## What was wrong or risky
The design risk addressed BEFORE prompting: hard-coded expected values
with no stated source would make the validation circular, so checks
were split into dictionary-reconciliation (citable to Appendix A) and
internal-consistency (pure logic: rows = days x tickers, clean = raw -
duplicates, high >= low). In the run itself: nothing failed. The
pre-reset build hit a Timestamp-vs-string TypeError on check 12; I
watched for it this time and it did not recur.

## What I changed and why
Nothing needed changing - 14/14 first run, including check 4 matching
the data dictionary's stated 2,847 duplicate figure. Three things
worth recording:
(1) check 7 formally establishes the 1,006-day complete calendar,
which is the paper trail for why the returns panel built later will
have 1,005 dates (the first day has no prior close);
(2) check 11 verifies the raw dtype mismatch as fact rather than
assumption, grounding the normalisation rule before the merge steps
where it bit the pre-reset build;
(3) compared to the pre-reset build: check 12's TypeError did not
recur and zero interventions were needed (vs one fix cycle
previously) - evidence that encoding the first build's lessons into
AGENTS.md measurably reduced errors on the rebuild.
Keeping validate_etl.py as a permanent regression test - re-run after
any ETL change.

## 3. 10 July 9.18 PM
## What I wanted
The Station 1 integrity outputs: a missing-date audit, an outlier screen
on daily returns, and the two integrity tables - including
results/tables/dataset_inventory.csv, one of the two mandatory exact
filenames. The inventory must describe the clean DATA (the 1,006-day
equity calendar), not the returns panel - a distinction flagged in the
pre-reset audit and now baked into the prompt.

## Prompt(s)
"Using the loaders in src/etl.py, add integrity-check functions and a
script step that produces two tables:

1. results/tables/dataset_inventory.csv (EXACT filename, mandatory) with
one row per dataset (equity_prices, crypto_prices, news_headlines) and
columns: rows, date_start, date_end, frequency, coverage. Use the CLEAN
numbers (crypto capped at 2023-12-31, news deduplicated). The inventory
describes the DATA: equity spans 1,006 trading days to 2023-12-29.

2. results/tables/data_integrity_summary.csv with one row per check:
check name, issue count found, and how it was resolved. Include:
- duplicate checks for all three datasets (with the keys used)
- the crypto rows removed by the 2023-12-31 cap
- a missing-date audit: for each equity ticker, compare its unique dates
against the full equity trading calendar and report any ticker with gaps
- an outlier screen: compute daily returns per ticker on adjClose
(within the equity panel only, no merging yet) and flag days where
|return| > 15%; report the count, and list the 5 largest moves with
ticker, date, and return so I can verify them as real events

Do NOT delete any outliers - the resolution column must say they are
kept. Print both tables to the terminal as well as saving them."

## What the assistant produced
Both tables saved and printed. Inventory: equity 50,300 rows
(2020-01-02 to 2023-12-29, ~252d/yr), crypto 14,610 (to 2023-12-31,
~365d/yr), news 146,836. Integrity summary, 6 checks: 0 equity and 0
crypto duplicates, 2,847 news duplicates removed, 10 crypto rows
capped, 0 tickers with missing days (all 50 complete on the 1,006-day
calendar), 62 outliers flagged and KEPT. Top moves reported: OXY -52%,
OXY +34%, SLB -27%, COP +25%, O -25%.

## What was wrong or risky
Two issues in the output, caught on review:
(1) The displayed inventory shows no "coverage" column (tickers/sectors
per dataset) despite the prompt specifying it - to be verified in the
saved CSV and fixed if missing, since coverage is part of the required
inventory content.
(2) Sloppy commentary: the assistant labelled news frequency as "daily"
(it is irregular - zero to many headlines per ticker-day), and claimed
all 62 outliers cluster in March-April 2020 "and a handful in 2022",
omitting at least NVDA +24.4% on 2023-05-25, which is known to be in
the set. The saved tables' numbers are correct; the narration around
them was imprecise - a reminder that the assistant's prose needs the
same auditing as its code.

## What I changed and why
Verified the core numbers against known values (0 gaps, 62 outliers,
OXY -52.0% on 2020-03-09 = the Saudi-Russia oil price war compounding
COVID demand fears; O -25% in the COVID crash; OXY +34% in the June
2020 rebound). Keeping all outliers is correct - deleting them would
understate the tail risk Part B funds must survive. The coverage-column
fix and the frequency-label correction are carried into the next
prompt, so the correction is on the record rather than silently
patched.

## 4. 10 July 9.24
## What I wanted
The combined returns panel: daily returns computed WITHIN each asset
panel first, then crypto returns left-merged onto the equity trading
calendar. Plus two corrections carried from the previous step's review:
the missing coverage column and the wrong news frequency label in the
mandatory inventory.

## Prompt(s)
"Two small corrections first, then the main task.

CORRECTIONS:
a. Check the saved results/tables/dataset_inventory.csv: it must contain
a 'coverage' column (equity: '50 tickers / 10 sectors'; crypto:
'10 tickers'; news: '50 tickers, deduplicated'). If missing, add it and
re-save.
b. In the inventory, news frequency must read 'irregular' - news has
zero to many headlines per ticker-day, it is not a daily series.

MAIN TASK - in src/features.py:
1. Compute daily simple returns per ticker on adjClose, separately
within the equity panel and within the (capped) crypto panel - using
pct_change grouped by ticker, sorted by date. No merging before this.
2. Normalise all date columns to naive datetime64[ns] before any join
(per AGENTS.md - news is tz-aware UTC, prices are naive).
3. Left-merge the crypto RETURNS onto the equity trading calendar to
build the combined panel. Never merge price levels across calendars.
4. Save the first ~300 rows to
results/data/combined_returns_panel_sample.csv.
5. Print verification: BTC-USD return rows before the merge, rows after
the merge, weekend-only crypto rows excluded (total across 10 coins),
and confirm the combined panel's date count - I expect 1,005 (the
1,006-day calendar minus the first day, which has no prior close)."

## What the assistant produced
Both inventory corrections applied. src/features.py created with
compute_returns(), compute_wide_returns(), build_combined_panel()
(drops the all-NaN first equity date, left-merges crypto returns onto
equity dates), save_combined_panel_sample(). Verification: BTC-USD
1,460 return rows before the merge, 1,005 after; combined panel 1,005
dates x 60 assets; excluded rows reported as 4,560 (10 x 456 dates).
Sample saved to results/data/combined_returns_panel_sample.csv.

## What was wrong or risky
One discrepancy caught on review: the exclusion count. Expected 4,550
excluded RETURN ROWS (1,460 - 1,005 = 455 per coin); the assistant
reported 4,560 as "456 dates" per coin. The extra 1 per coin is
2020-01-01 - a date with a price but no return (nothing precedes it) -
so the assistant counted excluded calendar DATES (1,461 - 1,005 = 456)
where the verification asked for excluded return rows (455).
Immaterial to the panel itself (the merge numbers 1,460 -> 1,005 are
exactly right), but the two countings must not be conflated in the
report. Also noted: the label "weekend-only" is imprecise - the
excluded dates are all non-equity-trading days, i.e. weekends PLUS US
market holidays (2020-01-01 was a Wednesday).

## What I changed and why
Accepted the panel as verified (the merge direction and counts are
exactly right; the pre-reset build produced identical 1,460 -> 1,005).
Carried two precision fixes into the next prompt so the correction is
on the record: (1) restate the exclusion as 4,550 return rows, with
the date-vs-row distinction explained; (2) relabel "weekend-only" as
"non-trading days (weekends and market holidays)". The economically
important fact is unchanged: every excluded observation is a crypto
move a fund trading on equity days could not have acted on.

## 5. 10 July 9.30 PM
## What I wanted
The descriptive-statistics table - the second mandatory exact filename -
in consistent DAILY return units per my AGENTS.md rule (a lesson from
the pre-reset build, where mixed units in a verification print inflated
the crypto/equity ratio from 2.26x to 2.72x and caused confusion). Plus
two precision corrections carried from the previous step's review.

## Prompt(s)
"Two precision corrections from the last step's review, then the main
task.

CORRECTIONS:
a. The exclusion count conflated two things. Restate it precisely in
the verification print: excluded RETURN ROWS = 4,550 (455 per coin =
1,460 return rows - 1,005 surviving); excluded DATES = 4,560 (456 per
coin, which additionally counts 2020-01-01 - a price date with no
return). Print both, labelled.
b. Relabel 'weekend-only' as 'non-trading days (weekends and US market
holidays)' - 2020-01-01 was a Wednesday holiday, so 'weekend' is
inaccurate.

MAIN TASK - in src/features.py:
1. Build a descriptive-statistics table of daily returns BY ASSET CLASS
(equity vs crypto) from the within-panel returns (NOT the combined
panel), with columns: mean, volatility (std), min, max, skew, kurtosis.
All statistics in DAILY return units (per AGENTS.md) - state the units
in the print.
2. Save to results/tables/descriptive_stats_returns.csv - EXACT
filename, mandatory. Wire into scripts/run_part_a.py.
3. Print for verification:
   a. the full table
   b. crypto daily std / equity daily std - I expect ~2.26x
   c. both kurtosis values - I expect mid-to-high teens (fat tails)
   d. equity min - I expect about -0.5201 (the OXY outlier day, tying
      this table to the integrity screen)"

## What the assistant produced
Both corrections applied: the verification print now distinguishes
excluded return rows (4,550 = 455/coin) from excluded dates (4,560 =
456/coin including the 2020-01-01 no-return day), and the exclusion is
relabelled "non-trading days (weekends and US market holidays)".
Stats table saved to results/tables/descriptive_stats_returns.csv, all
statistics in daily units, stated in both the print and the table.
Verification: crypto/equity daily std ratio 2.26x; kurtosis 16.30
(equity) and 18.60 (crypto); equity min -0.5201, matching the OXY
outlier from the integrity screen.

## What was wrong or risky
Nothing this run. The risks pre-managed by prompt design: mixed units
(prevented by the AGENTS.md daily-units rule, born from the pre-reset
units episode); computing stats on the combined panel instead of
within-panel returns (which would silently exclude crypto's non-trading-
day observations from its statistics); a wrong filename.

## What I changed and why
Nothing needed changing. Both mandatory filenames now exist and are
verified. The table's economic content, for the report: crypto carries
2.26x equity's daily volatility with a positive skew (+1.06 vs -0.06)
and both classes are heavily fat-tailed (kurtosis 16-19 vs 0 for a
normal distribution) - the raw material for the risk-feature analysis
that follows. The min value (-0.5201) cross-references the integrity
screen's OXY outlier, tying the two exhibits together.

## 6. 10 July 9.33 PM
## What I wanted
The base risk feature for my extension: 21-day rolling annualised
volatility per equity ticker, defined by its equation, with expected
behaviour stated in advance - the foundation for the news-conditional
and downside analysis. Deliberately annualised (unlike the daily-units
stats table), with the units stated per my AGENTS.md rule.

## Prompt(s)
"In src/features.py, add a rolling volatility feature on the equity
panel (within-panel returns, equity only):

1. For each ticker, compute
   sigma_t = std(returns over the trailing 21 trading days) * sqrt(252)
   using a rolling window grouped by ticker, sorted by date. Annualise
   with 252 (equity calendar) - this feature is DELIBERATELY annualised,
   state that in the print per the units rule. The first 20 days per
   ticker will be NaN - that is expected, leave them.

2. Save the full series to results/data/rolling_vol.csv. Do not use it
   as an input to anything else yet - it is a descriptive risk feature.

3. Print for verification:
   a. the dates of the 5 highest rolling-vol readings across all
      tickers - I expect these to cluster in March-April 2020
   b. the cross-ticker average rolling vol for March 2020 vs the
      average for calendar year 2021 - I expect a crisis multiple of
      roughly 3x
   c. one sanity check: NVDA's rolling vol vs WMT's on the same date in
      late 2023 - I expect NVDA well above WMT (chip maker vs defensive
      retailer)"

## What the assistant produced
rolling_volatility() added; full series saved to
results/data/rolling_vol.csv. Structural check (added by the assistant
unprompted): 50,250 rows = 50 tickers x 1,005 return days, with exactly
1,000 NaN = 50 x 20 warm-up days, leaving 49,250 valid observations.
Verification: (a) top 5 readings all OXY, 31 Mar - 6 Apr 2020, 237-250%
annualised - the COVID oil crash; (b) crisis multiple 82.19% / 25.28% =
3.3x; (c) NVDA 28.83% vs WMT 14.04% on 2023-12-29 (2.1x).

## What was wrong or risky
Nothing wrong. Pre-listed risks (rolling window bleeding across ticker
boundaries, 365 annualisation, zero-filled warm-up NaNs) did not occur;
the warm-up NaN count (exactly 1,000) positively confirms the grouping
is per-ticker. One footnote for consistency: the NVDA/WMT sanity check
used 2023-12-29, where the pre-reset build sampled November 2023
(41.3% vs 14.4%). Both confirm the same ordering - NVDA's vol had
simply declined into year-end - so the two runs agree, they just
sampled different dates.

## What I changed and why
Nothing. All three expectations stated in advance were met, and the
crisis multiple (3.3x) is identical to the pre-reset build - the
feature reproduces exactly. The economic behaviour is as theory
predicts: volatility clusters (the March-April 2020 storm), mean-
reverts (2021 calm), and orders sensibly in the cross-section (growth
chip maker ~2x a defensive retailer). Approved as the base for the
news-conditional analysis next.

## 10 July 9.36 PM
## What I wanted
The bridge between structured and unstructured data: daily headline
counts joined onto the equity returns panel. Three carried corrections
made explicit in the prompt: (a) the boundary-headline rule is now
pre-declared in AGENTS.md rather than improvised by the assistant (a
pre-reset lesson); (b) the flip-count materiality question raised in
my pre-reset log but never computed; (c) the join target corrected to
the 1,005-date returns panel (50,250 rows), not the raw 50,300-row
panel the pre-reset build used. I also corrected my own verification
design before running: check (d) originally demanded the headline sum
equal 146,836 exactly, but headlines mapping to the dropped first day
(2020-01-02) can legitimately fall out of the join - demanding exact
equality could have forced a false failure or a fudge, so the check
now asks for the number with an explanation of any gap.

## Prompt(s)
[the full prompt as run - corrections a/b/c + main task 1-4, with
check (d) reading "close to 146,836; if it differs, explain exactly
which headlines are not counted and why"]

## What the assistant produced
Text panel assembled and joined; results/data/equity_news_panel.csv
saved (50,250 rows: ticker, date, return, headline_count).
Verification: 6 orphan headlines mapped back to 2023-12-29 as
pre-declared; FLIP-COUNT = 0 - all 6 landed on ticker-days that
already had other headlines, so the boundary rule flipped no quiet
day to a news day; rows after join 50,250 exactly; split 12,312
zero-headline vs 37,938 news ticker-days; top 5 ticker-days are NVDA
May/Aug 2023 (earnings) and GILD Apr 2020 (remdesivir); headline sum
146,698 with a gap of exactly 138, all mapping to 2020-01-02 - the
first trading day, which carries forward-mapped New-Year headlines
but has no return row to join onto.

## What was wrong or risky
Nothing wrong in the run. The two long-open questions resolved
cleanly: the boundary-headline decision is now fully immaterial on
the evidence (flip-count 0 - it affects attention COUNTS on one
already-newsy day, and flips no classification), and the 138-headline
gap is a structural consequence of the returns-panel convention, not
a join fault - the same 1,005-vs-1,006 boundary documented since the
panel step. Risk noted for the record: my own original check design
(exact equality) was the error this round, caught before running.

## What I changed and why
Accepted the join as verified. Documented the two boundary effects
together for the report's methods paragraph: the returns panel drops
the first trading day (no prior close), which removes 138 forward-
mapped New-Year headlines from the joined panel and 10 first-day
crypto returns - both structural, both disclosed, both immaterial at
0.09% and 0.07% of their datasets respectively. The attention data is
anchored to real events (NVDA earnings, GILD remdesivir), confirming
the join attaches news to the right dates. Ready for the news-
conditional volatility analysis.

## 12 July 4.02 PM
## What I wanted
The core innovation result: for each stock, volatility measured
separately on news days vs quiet days, and the ratio between them
(NRR) - a new per-ticker risk feature quantifying how much of a
stock's risk arrives with news attention. Hypothesis, stated in
advance: NRR > 1 for the clear majority, because headlines and
repricing share a common cause (information arrival). The pre-reset
build found 48/48; the rebuild tests whether the result survives the
corrected panel (Jan-2 excluded, join onto 50,250 rows).

## Prompt(s)
"In src/features.py, build the news-conditional volatility analysis on
the joined panel from the previous step (equity only). Hypothesis,
stated in advance: NRR > 1 for the clear majority of stocks, because
headlines and repricing share a common cause (information arrival).

1. For each ticker, split its ticker-days into two buckets:
   news days (headline_count >= 1) and quiet days (count == 0).
2. Compute annualised volatility separately in each bucket:
   sigma_news_i  = std(returns on news days)  * sqrt(252)
   sigma_quiet_i = std(returns on quiet days) * sqrt(252)
   and the news-risk ratio: NRR_i = sigma_news_i / sigma_quiet_i.
   (Deliberately annualised - state the units.)
3. Guard rail: report each ticker's bucket sizes. Any ticker with fewer
   than 30 quiet days is flagged and its NRR set to NaN - do not
   silently drop or fudge it.
4. Save results/tables/news_risk_ratio.csv with columns: ticker,
   sector, n_news_days, n_quiet_days, vol_news, vol_quiet,
   news_risk_ratio - sorted by ratio, descending.
5. Print for verification:
   a. the count of valid tickers with NRR > 1 (hypothesis: clear
      majority; the pre-reset build found 48/48)
   b. the 5 highest-NRR and 5 lowest-NRR tickers with sectors
   c. the sector-level average NRR (equal-weight), sorted
   d. the flagged small-sample tickers and their quiet-day counts
      (pre-reset: DIS 12, WMT 20 - decimals may shift slightly since
      the panel now excludes the Jan-2 day, but the structure should
      hold)"

## What the assistant produced
news_risk_ratio.csv saved (50 tickers x 8 columns, DIS/WMT as NaN).
(a) 48/48 valid tickers show NRR > 1 - unanimous, matching pre-reset.
(b) Top 5: CVX 2.07, BA 2.02, T 1.92, OXY 1.83, CMCSA 1.78; bottom 5:
ABT 1.01, PLD 1.01, SHW 1.07, NKE 1.16, NUE 1.20.
(c) Sector averages: Energy 1.613 highest, RealEstate 1.338 lowest.
(d) Guard rail: DIS (12 quiet days) and WMT (20) flagged to NaN.

## What was wrong or risky
Nothing wrong in the run. Robustness note worth recording: the result
reproduces the pre-reset build essentially exactly despite the panel
correction (Jan-2 excluded; join target 50,250 not 50,300) - same
48/48, same top 5, same sector ordering, same flags; the only visible
difference is a tie-order swap at the bottom (ABT/PLD both ~1.01).
The finding is insensitive to the boundary conventions, which
strengthens it. Interpretation limits carried into the report:
(1) NRR > 1 shows association, not causation - coverage and repricing
share common causes and causality runs both ways; (2) the top-NRR
names (CVX, OXY, BA) are also the biggest outlier stocks from the
integrity screen, so part of their ratio reflects the 2020 oil-war /
COVID crisis period specifically, not news sensitivity in general.

## What I changed and why
Nothing needed changing; hypothesis confirmed unanimously, twice
independently. Economic story at both extremes: highest ratios in
Energy and cyclicals (the 2020 oil price war and 2022 energy rally
were exactly news-driven repricing episodes); lowest in defensive,
steady-cash-flow names whose values barely re-rate on a headline -
NRR near 1.0 means their news days are statistically
indistinguishable from quiet days. Hand-off to Part B recorded: the
NRR defines the attention-weighting of the sector sentiment index,
and the quiet/news split (12,312 vs 37,938 ticker-days) grounds the
missing-headline policy (silence is its own regime, not neutral
sentiment).

## 12 July 4.15 PM
## What I wanted
The second leg of my extension: downside semi-deviation and downside
share per ticker and asset class - volatility computed only from
below-average days, since investors fear losses, not gains. Hypothesis,
stated in advance: crypto's positive skew (+1.06 vs equities' -0.06)
means a SMALLER share of crypto's volatility is downside, challenging
the naive "crypto is 2.26x riskier" reading of my own stats table. The
prompt carries the pre-reset formula bug as an explicit lesson: the
first-ever attempt averaged squared deviations over only the negative
days instead of min(dev,0)^2 over ALL observations, and the stated
0.71 benchmark is what exposed it - so this prompt spells the formula
out operation by operation.

## Prompt(s)
Not yet - one analysis task first, then the figures.

One carried lesson first, then the main task.

CARRIED LESSON (from the pre-reset build): the first attempt at this
exact computation contained a real formula bug - the assistant averaged
squared deviations over ONLY the negative-deviation days instead of
averaging min(dev, 0)^2 over ALL observations, producing downside
shares near 1.0. The stated theoretical benchmark (0.71 for symmetric
returns) is what exposed it. The formula below is therefore spelled out
precisely; implement it exactly, using np.minimum over the full series.

MAIN TASK - in src/features.py, on the within-panel returns (both
asset classes). Hypothesis, stated in advance: crypto's positive skew
(+1.06 vs equities' -0.06 in my stats table) means a SMALLER share of
crypto's volatility is downside - challenging the naive "crypto is
2.26x riskier" reading of my own descriptive stats.

1. For each ticker, compute annualised downside semi-deviation:
   sigma_down_i = sqrt( mean( min(r_it - rbar_i, 0)^2 ) ) * sqrt(A)
   where rbar_i is the ticker's mean daily return, the mean is over
   ALL observations (np.minimum(dev, 0), then square, then mean), and
   A = 252 for equities, 365 for crypto - the calendars differ.

2. Compute total volatility sigma_i the same way (same A per class),
   and the downside share DS_i = sigma_down_i / sigma_i. Benchmark:
   ~0.7071 (=1/sqrt(2)) for symmetric returns; report values relative
   to it.

3. Save results/tables/downside_risk.csv: ticker, asset_class, sector
   (blank for crypto), vol, vol_downside, downside_share - sorted by
   downside_share descending.

4. Print for verification:
   a. average downside share by asset class (hypothesis: crypto BELOW
      equities; pre-reset found equities 0.7057, crypto 0.6726)
   b. the 5 most downside-heavy and 5 most upside-heavy tickers
   c. sanity: every ticker's sigma_down strictly less than its sigma -
      any violation means the formula bug returned
## What the assistant produced
compute_downside_risk() in src/features.py, wired into run_part_a.py;
downside_risk.csv saved. The assistant noted it had ALREADY implemented
the task ahead of my instruction (it had proposed skipping to figures
in the prior turn, and had this built in the background). All checks
pass: equity average DS 0.7057, crypto 0.6726 - both matching the
pre-reset build to four decimals; crypto < equity confirmed; most
downside-heavy: O, KO, PSA, ABBV, ADBE; most upside-heavy: XLM, XRP,
ETC, ADA (all crypto) plus GILD; sanity holds - every ticker's
sigma_down strictly below its sigma, confirming the formula bug did
not return.

## What was wrong or risky
Nothing wrong in the computation - the precisely-specified formula
prevented the pre-reset bug by construction. Two process notes:
(1) the assistant worked AHEAD of my instruction - in the previous
turn it skipped the queued task and proposed its own next steps, and
here revealed it had already built the skipped task. The output is
verified correct, but unrequested initiative cuts both ways: useful
here, but it is the same autonomy that improvised the boundary rule
pre-reset, so it stays on the record. (2) New detail vs pre-reset:
GILD joins the upside-heavy extremes - economically coherent, since
its defining 2020 moves were remdesivir rally days.

## What I changed and why
Nothing needed changing; hypothesis CONFIRMED, twice independently and
now robust to the corrected panel. The report story: crypto's headline
2.26x volatility overstates its downside threat - a visibly larger
slice of its variance is upside (DS 0.6726 vs the 0.7071 symmetric
benchmark), while equities sit essentially at the benchmark (0.7057,
to be read as "balanced", not "upside-heavy"). The extremes deepen it:
the MOST downside-heavy names are defensive stocks (O, KO, PSA) -
slow up the stairs, down the elevator - while the most upside-heavy
are speculative alt-coins plus GILD's event-driven rallies. Volatility
rankings and downside rankings tell different stories, which is the
feature's point. Both innovation legs are now built and verified;
next: the combined exhibit that presents them.

## 12 July 4.25 PM
## What I wanted
The centerpiece exhibit of my innovation section: one scatter and one
summary table combining the two risk features into a per-ticker risk
map. Deliberately open verification on the NRR-vs-downside-share
correlation - no prior hypothesis, stated in advance, to be
interpreted either way. This step is new territory: the pre-reset
build never reached the exhibit stage.

## Prompt(s)
"Now the figures phase - starting with my innovation exhibit, then your
proposed list.

Create the combined innovation exhibit from results/tables/
news_risk_ratio.csv and results/tables/downside_risk.csv. Follow the
AGENTS.md design system exactly (teal #0E7C66 equities, coral #E4572E
crypto, amber #F2A541 highlights, gray #9AA5B1 context; title, labelled
axes, units, sample period, source note bottom-left on every figure).

1. FIGURE - a scatter plot, equity tickers only:
   x = news-risk ratio (NRR), y = downside share.
   - Energy sector points in amber (the top-NRR sector), defensive
     sectors (Utilities, RealEstate) in gray, all other sectors teal
   - reference lines: vertical at NRR = 1.0 (news days no riskier than
     quiet) and horizontal at 0.7071 (symmetric returns) - these lines
     carry the interpretation, label them on the plot
   - annotate extreme tickers: CVX, BA, OXY (high NRR); PLD, ABT (NRR
     near 1); O, KO, PSA (downside-heavy)
   - DIS and WMT have NaN NRR (guard-railed) - exclude from the
     scatter but state the exclusion in the caption text on the figure
   - save to results/figures/innovation_risk_map.png

2. TABLE - results/tables/innovation_summary.csv: one row per equity
   sector plus one row per asset class, columns: avg_NRR (sectors
   only), avg_downside_share, n_tickers, n_flagged.

3. Print for verification:
   a. the scatter contains exactly 48 points
   b. all 48 sit right of the NRR = 1.0 line (the unanimous result -
      any point left of it means something changed)
   c. the correlation between NRR and downside share across the 48 -
      I have NO prior hypothesis; report it either way and I will
      interpret it."

## What the assistant produced
results/figures/innovation_risk_map.png (2000x1400, 200 dpi) and
results/tables/innovation_summary.csv (10 sector rows + 2 asset-class
rows), wired into run_part_a.py. Verification: (a) exactly 48 points
(DIS, WMT excluded per the guard rail); (b) all 48 sit right of the
NRR = 1.0 line - the unanimous result survives visually; (c) the
correlation between NRR and downside share is -0.0609 - essentially
zero.

## What was wrong or risky
Nothing wrong in the numbers. Pending my own visual inspection of the
figure against the design-system requirements (palette, labelled
reference lines, annotations, exclusion note) - printed verifications
cover the data, not the presentation, and the figure is a graded
exhibit. [Update after inspection: ...]

## What I changed and why
Interpreted the open question (c): near-zero correlation is the
strongest possible answer for the feature design, because it
establishes that the two features measure INDEPENDENT dimensions of
risk - WHEN risk arrives (with news attention or without) and WHICH
DIRECTION it leans (downside-heavy or upside-tilted) are separate
properties. A strong correlation would have meant one dimension built
twice; independence justifies the two-axis risk map. The quadrants now
carry distinct economic types: news-driven and downside-heavy (BA),
news-driven but balanced (CVX), news-immune and downside-heavy (O,
PSA), news-immune and balanced (PLD). This independence result -
unplanned and reported under a pre-declared no-hypothesis stance - is
the kind of data-driven finding the innovation criterion asks to see
evidenced rather than proposed.




## 12 July 4.41 PM
## What I wanted
The full figures campaign: my crypto correction to the innovation
exhibit (caught on visual review), plus the three remaining required
figures and the text descriptive analysis - completing every code
deliverable of Part A.

## Prompt(s)
"Corrections from my visual review of the innovation figure first, then
the remaining required exhibits.

CORRECTION (my catch on visual inspection): the innovation risk map
omits crypto entirely, silently dropping half of my downside-share
result. Crypto has no NRR (the news data covers equities only, so the
x-axis is undefined for coins) but it DOES have downside shares. Fix:
add a narrow side panel to the right of the scatter - a vertical strip
showing the 10 coins' downside shares as coral (#E4572E) dots against
the same y-axis, with the 0.7071 benchmark line continued through it,
labelled 'Crypto (NRR undefined - no news data)'. The main scatter is
unchanged. Re-save results/figures/innovation_risk_map.png.

THEN the three remaining required figures (AGENTS.md design system on
all: teal equities, coral crypto, amber highlights; title, labelled
axes, units, sample period, source note on every figure):

1. results/figures/price_cumulative_return.png - growth of $1 for a
   sample: NVDA, XOM, WMT (teal shades/solid) and BTC-USD, XRP-USD
   (coral, dashed), 2020-2023, log scale. I expect NVDA to end around
   8x and the crypto lines to swing far wider than the equities.

2. results/figures/returns_distribution.png - histogram of all equity
   daily returns (log frequency scale), with the +/-15% outlier screen
   marked as vertical lines and labelled - tying the figure to the 62
   kept outliers in the integrity summary.

3. Text descriptive analysis (counting only - NO sentiment scoring,
   per AGENTS.md scope):
   a. results/figures/news_volume_over_time.png - headlines per month,
      2020-2023; split the top few sectors into separate lines if it
      stays readable. I expect an average around 3,000/month with a
      peak in the March 2020 crisis.
   b. results/figures/top_terms.png - horizontal bar chart of the 15
      most frequent headline terms after removing common stopwords
      (a bar chart is crisper than a word cloud and satisfies the same
      requirement).
   c. Print a count of positive-leaning vs negative-leaning vocabulary
      (simple keyword lists, e.g. buy/gain/surge vs sell/drop/miss) -
      I expect a heavy positive skew, roughly 3-4x. This is a
      vocabulary COUNT, not sentiment scoring - state that in the
      print.

4. Save any counts behind figure 3 to results/tables/ with clear
   names, and wire everything into run_part_a.py.

5. Print verification: list every file in results/figures/ with pixel
   dimensions, and confirm all four figures carry the design-system
   elements (title, axes+units, period, source note)."

## What the assistant produced
All five figures saved in the design system: innovation_risk_map.png
re-rendered at 2400x1400 with the coral crypto side panel (48 equity
points + 10 coins against the shared 0.7071 benchmark);
price_cumulative_return.png (NVDA ~8x confirmed, crypto lines visibly
wider-swinging); returns_distribution.png (log-frequency histogram,
+/-15% lines tying to the 62 kept outliers); news_volume_over_time.png
(peak March 2020); top_terms.png. Two new tables:
top_terms_frequencies.csv and sentiment_vocabulary_counts.csv
(29 positive words, 41,193 hits vs 30 negative words, 11,553 - a
3.57x positive skew, within the expected 3-4x). The assistant also
ran check_handin.py: 14/14 checks pass, two expected warnings
(__pycache__ to clean before zipping; report.pdf not yet written).

## What was wrong or risky
Nothing wrong in the run. The correction cycle worked as designed: my
visual review caught the missing crypto half of the downside result,
the fix was specified with its reason (NRR undefined for coins - the
news data covers equities only), and the exhibit now carries both
asset classes. The vocabulary count was explicitly framed as counting,
not scoring, keeping the Part A/B boundary intact.

## What I changed and why
Accepted the campaign. The 3.57x positive-vocabulary skew is recorded
for the report and for Part B: headline language in this dataset is
structurally bullish, so a lexicon sentiment scorer applied to it may
need recalibration - a caveat my own counts now evidence. Remaining
work is mine, not code: visual QA of all five figures, cleaning
__pycache__, and writing report/report.pdf.

## 21 July 2026 10.00 am
## What I wanted
To verify precisely how the news deduplication compares headline
titles - exact string match, or normalized (lowercased/stripped) first
- since the two approaches can produce different duplicate counts, and
I wanted a defensible answer rather than an assumption for the report.

## Prompt(s)
"I need to check the cleaning of the headlines. It uses the combination
of ticker, date, and the exact headline title. For the exact headline
comparison, is it case-sensitive and whitespace-sensitive (exact string
match), or normalized first (lowercased/stripped)? Then test: after
lowercasing and stripping whitespace from titles, how many duplicate
ticker+date+title rows exist that were NOT caught by the current exact
match? Report the count - do not change the existing dedup logic, just
report the gap."

## What the assistant produced
Confirmed the current dedup is exact-match: case-sensitive and
whitespace-sensitive (raw pandas string comparison, no .str.lower() or
.str.strip()). Test result: 149,683 raw headlines; exact-match
duplicates (current logic) = 2,847; normalized duplicates (lower +
strip) = 2,860; gap = 13 additional duplicates missed by the current
logic, all differing only in casing (e.g. "Viral Collapse Of Economic
Optimism" vs "Viral Collapse of Economic Optimism") - no
whitespace-only differences found. The assistant noted the gap is
0.009% of the data and that normalizing would conflict with the
AGENTS.md rule to preserve raw headline text for VADER in Part B.

## What was wrong or risky
Nothing wrong - this was a verification task, not a build task, and it
confirmed rather than corrected my assumption. Worth recording as a
disclosed, quantified limitation rather than an unknown: my 2,847
duplicate figure is a defensible lower bound on true duplicates, with
an 13-row (0.009%) gap now measured rather than guessed at.

## What I changed and why
No code changed - the assistant's own reasoning correctly identified
that normalizing titles before dedup would conflict with my own
AGENTS.md rule (raw headline text preserved intact for VADER's
function-word sensitivity in Part B). Kept the exact-match logic as-is.
This gives the report an honest, quantified caveat: "headline
deduplication used exact string matching; a secondary check found 13
additional near-duplicate headlines (0.009% of the raw data)
differing only in capitalisation, which were not removed to preserve
the raw text required for Part B's sentiment model."

## 21 July 11:49 am
## What I wanted
To correct the news deduplication to catch case/whitespace-only
duplicates missed by the original exact-match logic, after confirming
with AGENTS.md that normalizing the MATCHING key doesn't conflict with
keeping STORED text raw.

## Prompt(s)
"Correction to the news deduplication: normalizing text for
DEDUPLICATION MATCHING does not conflict with AGENTS.md's raw-text
rule - that rule governs stored output, not the comparison key. Fix:

In load_clean_news(), build a temporary matching key: title.lower().
strip(). Drop duplicates on ticker+date+normalized_title, but keep the
ORIGINAL unmodified title text in every surviving row (never overwrite
title with the normalized version).

Re-run the full pipeline (all downstream steps depend on this). Report:
1. new raw/duplicate/clean counts for news
2. new dataset_inventory.csv news row count
3. new text panel group count (I expect ~37,962, possibly unchanged)
4. new attention join split (zero-headline vs >=1, I expect close to
   12,327 vs 37,923)
5. new NRR result: still how many of 50 valid tickers show NRR > 1
   (I expect still 48, possibly 47-49), and whether DIS/WMT are still
   the flagged tickers
6. confirm results/tables/descriptive_stats_returns.csv, downside_risk.csv,
   and the two figures needing return data are unaffected (they don't
   depend on news, so should be identical)"

## What the assistant produced
News duplicates rose from 2,847 to 2,860 (+13), clean rows fell from
146,836 to 146,823 - matching the 13-row gap found in the original
investigation exactly, an independent confirmation across two runs.
Downstream: NRR unchanged (48/48, DIS/WMT still flagged), descriptive
stats and downside share tables identical, both return-based figures
regenerated identically. Raw title text confirmed unmodified in every
stored row.

## What was wrong or risky
The assistant made two errors describing its OWN results: (1) it
misstated the prior baseline as "2,836 duplicates / 146,847 clean" -
the true baseline, used throughout this entire project, is 2,847 /
146,836; (2) it claimed the attention split "shifted by 15" from a
fabricated "previous" figure, when its own item-4 output (12,312 /
37,938) was actually IDENTICAL to the true original split. This has a
clean logical explanation I derived myself: duplicate headlines are by
definition extra copies on already-newsy days, so removing them can
never flip a ticker-day from "has news" to "quiet" - the split was
mathematically guaranteed to stay unchanged. This is the same pattern
as the earlier units episode: the assistant's account of its OWN prior
state needed independent verification, just like its code does.

## What I changed and why
Kept the fix (it is correct and now verified). Updated my report draft:
replaced 2,847 with 2,860 and 146,836 with 146,823 wherever they
appear, and added a one-sentence note that the deduplication now
catches case/whitespace variants. No other numbers needed updating -
NRR, downside share, stats table, and the split (12,312/37,938) are
all confirmed unchanged, with a clean logical reason why duplicate
removal cannot affect that particular split.

## 21 July 1:55 pm
## What I wanted
Full reproducibility for the outlier screen: the original check only
covered equities, while crypto's 280 outliers (discovered later, in
the descriptive scorecard) were never added to the canonical integrity
table. This created a documentation gap - two true numbers living in
two different tables with no note explaining why - so I fixed it in
the code rather than papering over it with a report sentence.

## Prompt(s)
"Fix a scope gap in the integrity check: the outlier screen
(|return| > 15%) was applied to equity only. Add crypto to
data_integrity_summary.csv.

1. In build_integrity_summary() (src/etl.py), add a crypto outlier
   screen using the same logic as equity's: |daily return| > 15% on
   the within-panel crypto returns (capped at 2023-12-31). Do NOT
   delete any - same 'kept, not deleted' policy as equity.

2. Add a new row (or rows) to data_integrity_summary.csv for the
   crypto outlier count, following the same format as the existing
   equity outlier row: check name, count, resolution (list the top 5
   largest moves by absolute value: ticker, date, return).

3. Re-save results/tables/data_integrity_summary.csv and re-run
   check_handin.py to confirm nothing broke.

4. Print for verification:
   a. total crypto outlier count (I expect 280)
   b. top 5 largest moves by absolute return, with ticker and date
      (I expect: XLM-USD +74.9% on 2021-01-06 as the largest)
   c. confirm the equity outlier row (62, OXY -52.0% top) is
      UNCHANGED - this fix only adds crypto, it doesn't touch equity"

## What the assistant produced
find_outliers() extended to crypto in src/etl.py, with a new detail-
string builder and a new row added to the integrity summary DataFrame.
Verification: (a) 280 crypto outliers, exact match; (b) top 5 by
absolute move: XLM-USD +74.92% (2021-01-06), XRP-USD +73.08%
(2023-07-13), XLM-USD +60.89% (2023-07-13), XRP-USD +56.01%
(2021-01-30), EOS-USD +55.21% (2021-05-11); (c) equity row confirmed
unchanged - 62, OXY -52.0% still top.

## What was wrong or risky
Nothing wrong in this run - the fix was scoped narrowly (only
build_integrity_summary and the new crypto call) and the equity row's
exact preservation confirms no unintended side effects. The original
issue was a genuine scope gap from early in the project, when the
outlier screen was first specified as equity-only before crypto's own
outlier population was known to matter - not an error at the time, but
one that should have been reconciled once the scorecard revealed
crypto's 280.

## What I changed and why
data_integrity_summary.csv now reports both asset classes' outlier
screens in one canonical table, closing the gap between it and the
scorecard. check_handin.py re-run and confirmed clean. Report update:
Table 2's write-up in Section 3 can now state both counts directly
(62 equity, 280 crypto) from a single source, instead of needing a
disclosed cross-reference to the scorecard.

## 21 July 6.02 PM
## What I wanted
A correlation analysis between equities and crypto (equal-weight
indices, aligned on the equity calendar), testing whether correlation
rises during crises - plus a rolling-window chart to visualize the
pattern over time.

## Prompt(s)
"Add a correlation analysis between equities and crypto to
src/features.py, following the design system and verification pattern
in AGENTS.md.

1. Build two equal-weight daily return indices from the within-panel
returns: equity_index = mean daily return across all 50 equity
tickers; crypto_index = mean daily return across the 10 crypto
tickers, LEFT-JOINED onto the equity trading calendar (same alignment
as the combined panel - 1,005 dates).

2. Compute:
   a. Overall Pearson correlation between equity_index and crypto_index
   b. Correlation split by period: 2020-2021 vs 2022-2023
   c. Correlation during the March-April 2020 crisis window only
      (2020-03-01 to 2020-04-15)

3. Save results/tables/correlation_analysis.csv with columns: period,
n_days, correlation. Rows: 'Full sample (2020-2023)', '2020-2021',
'2022-2023', 'Mar-Apr 2020 crisis'.

4. Create results/figures/rolling_correlation.png: a 60-day rolling
Pearson correlation between equity_index and crypto_index, plotted
over time. Design system: teal line for the rolling correlation, coral
shaded region or dashed line marking the Mar-Apr 2020 window,
horizontal gray dashed reference line at the full-sample correlation
value, amber annotation marking the peak. Title, axis labels
(correlation coefficient, -1 to 1 range on y-axis), sample period,
source note bottom-left.

5. Print for verification:
   a. overall correlation - I expect approximately 0.35
   b. 2020-2021 vs 2022-2023 - I expect approximately 0.31 and 0.43
   c. crisis-window correlation - I expect approximately 0.58, the
      highest of the three periods (confirming correlations rise
      during crashes)
   d. the rolling correlation's peak value and date - I expect the
      peak to fall within or near the March-April 2020 crisis window"

## What the assistant produced
correlation_analysis.csv (4 rows) and rolling_correlation.png saved,
wired into run_part_a.py. Overall correlation 0.3478; 2020-2021 0.3109,
2022-2023 0.4318; crisis window 0.5771 (highest of the three fixed-
window periods, as expected). Rolling 60-day peak: 0.6938 on
2023-02-06 - NOT in the crisis window as I had expected.

## What was wrong or risky
Not an error - my own expectation (d) was wrong, and the assistant
correctly reported the true result rather than the one I'd predicted.
The discrepancy has a real explanation: the fixed 46-day crisis window
measures a short, sharp panic-driven spike, while the 60-day ROLLING
window measures sustained co-movement and can be won by a longer,
quieter period of common macro exposure (Feb 2023, likely shared
reaction to Fed rate expectations) even though its correlation never
reached crisis-level panic. Fixed-window and rolling-window
correlation are answering different questions and are not guaranteed
to agree on where the maximum occurs.

## What I changed and why
Kept the mismatch rather than dismissing it - it is a more interesting
finding than my original hypothesis. Added it to the report as a
distinguishing point between short sharp panics and sustained
macro-driven co-movement, rather than treating the unmet expectation
as a failure. This is a case where checking my prediction against the
actual result surfaced a genuine insight I would not have written
without first being wrong.

## 21 July 7.25 PM
## What I wanted
A sector-level correlation analysis (10 equal-weight sector indices,
full pairwise matrix) to identify which sectors offer genuine
diversification within the equity universe, for a risk-management
angle - a natural extension of the equity-vs-crypto correlation work.

## Prompt(s)
"Add a sector correlation analysis to src/features.py, following the
design system and verification pattern in AGENTS.md.

1. Build 10 equal-weight sector return indices: for each of the 10
equity sectors, the average daily return across that sector's tickers
(within-panel equity returns, before any crypto merge).

2. Compute the full 10x10 Pearson correlation matrix across sector
indices. Save results/tables/sector_correlation_matrix.csv (10x10,
sector names as both row and column labels).

3. From the 45 unique off-diagonal pairs, also save
results/tables/sector_correlation_summary.csv with: the 3 lowest-
correlated pairs, the 3 highest-correlated pairs, and the average
off-diagonal correlation.

4. Create results/figures/sector_correlation_heatmap.png: a heatmap of
the 10x10 matrix. Design system: use a diverging colormap centred at
the average correlation (not zero, since all values are positive) so
the lowest and highest pairs are visually distinguishable - teal for
low correlation, coral for high, amber gridlines/annotations for the
value labels. Sector names on both axes, title, source note
bottom-left.

5. Print for verification:
   a. average off-diagonal correlation - I expect approximately 0.59
   b. the 3 lowest pairs - I expect Energy paired with most others at
      the bottom (Energy-Utilities, Energy-Tech, Energy-Healthcare,
      roughly 0.33-0.37)
   c. the 3 highest pairs - I expect Financials-Industrials,
      Industrials-Materials, Consumer-Financials, roughly 0.76-0.83"

## What the assistant produced
sector_correlation_matrix.csv (10x10), sector_correlation_summary.csv,
and sector_correlation_heatmap.png (teal-coral diverging colormap
centred at 0.59, amber annotations) all saved and wired into
run_part_a.py. Verification: (a) average off-diagonal correlation
0.5909; (b) three lowest pairs all involve Energy - Utilities (0.3303),
Tech (0.3374), Healthcare (0.3652); (c) three highest pairs -
Financials-Industrials (0.8300), Industrials-Materials (0.7852),
Consumer-Financials (0.7711).

## What was wrong or risky
Nothing wrong - all four pre-stated expectations matched closely,
including the specific sector identities in both the low and high
groups, not just the numeric ranges. check_handin.py remained at 15
checks passed after the addition.

## What I changed and why
Nothing needed changing. The result supports a clear risk-management
narrative: Energy is the equity universe's best internal diversifier,
moving independently of growth and defensive sectors alike (consistent
with its outlier-heavy, commodity-driven return profile from the
integrity screen), while Financials, Industrials, and Materials form a
tightly linked cyclical cluster offering little diversification benefit
when combined. Kept as a compact addition: two tables plus one heatmap,
one paragraph of interpretation.

## 21 July 7.45 PM
## What I wanted
Two new candidate risk features - liquidity risk (Amihud illiquidity)
and diversification score (average pairwise correlation) - built
alongside the existing NRR and downside share, without modifying
either, so all four can be evaluated together before deciding the
final innovation section.

## Prompt(s)
"Add two new risk features to src/features.py, alongside the existing
NRR and downside share (do not modify or remove either).

FEATURE 3 - Liquidity risk (Amihud illiquidity ratio), all 60 assets:
1. Compute dollar volume: equity = volume * adjClose; crypto = volume
directly (already USD - do not multiply by price, per the earlier
fix).
2. Per ticker: illiquidity_i = mean(|daily return| / dollar_volume)
* 1e9 (scaled to 'price impact per $1B traded'), using within-panel
returns.
3. Hypothesis stated first: crypto should be less liquid on average
than equities.
4. Save results/tables/liquidity_risk.csv: ticker, asset_class,
sector, avg_dollar_volume, amihud_illiquidity - sorted ascending
(most liquid first).
5. Verify: (a) class averages - I expect equity ~0.033, crypto ~0.051;
(b) 5 most liquid overall - I expect BTC-USD and ETH-USD at the very
top, ahead of NVDA; (c) 5 least liquid - I expect XLM-USD at the
bottom, with ADA-USD also appearing near the bottom despite its high
cumulative return.

FEATURE 4 - Diversification score, all 60 assets:
1. Build the full 60x60 pairwise correlation matrix on the combined
panel (equity calendar, 1,005 dates, within-panel returns).
2. Per ticker: diversification_score_i = average correlation with the
other 59 assets (exclude self).
3. Hypothesis stated first: crypto assets should show lower average
correlation (better diversifiers) than equities, since they trade on
different fundamental drivers.
4. Save results/tables/diversification_score.csv: ticker, asset_class,
sector, diversification_score - sorted ascending (best diversifiers
first).
5. Verify: (a) class averages - I expect equity ~0.370, crypto ~0.266;
(b) best diversifier overall - I expect NEM (gold miner); (c) worst
diversifier - I expect a Financials name (MS or GS).

Do NOT build a combined exhibit yet - just the two tables. I will
decide on visualization after reviewing the verified numbers."

## What the assistant produced
liquidity_risk.csv and diversification_score.csv saved (60 rows each),
wired into run_part_a.py. Liquidity: equity avg 0.0331, crypto avg
0.0514 (hypothesis confirmed); most liquid BTC-USD (0.0007) and
ETH-USD (0.0020), ahead of NVDA (0.0036); least liquid XLM-USD
(0.1455), with ADA-USD also near the bottom (0.0810) despite its 17.76x
return. Diversification: equity avg 0.3698, crypto avg 0.2659
(hypothesis confirmed); best diversifier NEM (0.1893, gold miner);
worst MS (0.4691, Financials).

## What was wrong or risky
Nothing wrong - both hypotheses confirmed on the first run, matching
pre-registered expectations closely (within 0.001-0.002 on every class
average). Confirmed no modification to NRR or downside share code, and
check_handin.py remained at 15 checks passed.

## What I changed and why
Nothing needed changing. Both features are now candidates alongside
NRR and downside share, pending my evaluation of which combination
becomes the final Section 5. Notable finding to carry into that
decision: ADA - the headline best performer at 17.76x - is also one of
the least liquid assets, directly qualifying the earlier profitability
narrative; and crypto is simultaneously the LESS liquid asset class
(feature 3) and the BETTER diversifying asset class (feature 4),
showing the two new features capture genuinely different risk
dimensions rather than restating each other.

## 22 July 911 AM
## What I wanted
A first, deliberately plain version of the liquidity-vs-return chart,
built with technical defaults (standard legend, raw axis labels), to
confirm the readability problem before correcting it - I wanted the
"before" state on record, not just the fixed version.

## Prompt(s)
"In src/features.py, add a function to visualise liquidity against
return for all 60 assets.

1. Compute Amihud illiquidity per ticker (mean of |daily return| /
dollar volume, scaled by 1e9) and cumulative return (growth of $1) per
ticker, using within-panel returns.

2. Create a scatter plot: x = illiquidity (log scale), y = cumulative
return (log scale). Colour equities teal, crypto coral. Add a standard
legend, axis labels ('Amihud Illiquidity' and 'Cumulative Return'),
and a title ('Liquidity vs Return, All Assets').

3. Save to results/figures/liquidity_vs_return.png.

Print confirmation that the file was saved and the figure dimensions."

## What the assistant produced
results/figures/liquidity_vs_return.png (2000x1200px) saved, wired in,
check_handin.py 15/15 passed. Log-log scatter with a standard legend,
raw numeric axis labels ("Amihud Illiquidity", "Cumulative Return"),
and a generic title ("Liquidity vs Return, All Assets"). BTC/ETH cluster
top-left (low illiquidity, high return); XLM/ADA/ETC cluster bottom-
right (high illiquidity, low return). Crypto tickers labelled directly;
equities left unlabelled.

## What was wrong or risky
Exactly the problem I expected from technical defaults: log-scale axes
display in raw scientific notation (e.g. "10^-3"), which is meaningless
to this project's actual target user - a beginner, non-technical
investor opening the UNSWTrader app, as defined in my own Section 1.
A chart correct in its statistics but unreadable to its intended
audience is a real presentation failure, not a cosmetic one - this is
a self-critique I wanted on record rather than silently skipping to
the "good" version.

## What I changed and why
Nothing changed in this step - this version is intentionally kept as
the "before" baseline. The correction (plain-word axis anchors,
finding-based headline, no legend box, editorial layout, and a split
into three charts: combined, stocks-only, crypto-only) is the subject
of the next prompt, so the improvement is visible as a deliberate,
reasoned step rather than presented as if the final chart were the
first attempt.

## 22 July 2026 10.22 AM
## What I wanted
The corrected, beginner-readable version of the liquidity charts: plain-
word axis anchors instead of scientific notation, an editorial (FT-
style) layout with finding-based headlines, and a split into three
files (combined, stocks-only, crypto-only) - fixing the readability
failure confirmed in the previous prompt.

## Prompt(s)
"I reviewed liquidity_vs_return.png and it is not usable: the log-scale
axis shows raw scientific notation (e.g. '10^-3'), which is meaningless
to this project's target user - a beginner, non-technical investor
opening the UNSWTrader app. Fix the chart with these specific changes,
and produce THREE versions.

1. Replace numeric axis ticks with plain-word anchors:
   - x-axis (illiquidity): 'Very liquid', 'Liquid', 'Illiquid',
     'Very illiquid' at the appropriate log-spaced positions - no
     numbers shown on the axis itself.
   - y-axis (return): combine plain words WITH the multiplier, e.g.
     'Lost half (0.5x)', 'Broke even (1x)', 'Doubled (2x)', 'Grew 16x'.
   Keep proper axis TITLE text as well (e.g. 'Liquidity - how easily
   an asset can be traded without moving its price'), so both the axis
   title and the tick words are present together.

2. Apply a clean, editorial (Financial Times-style) layout:
   - Bold, left-aligned headline stating the FINDING, not a
     description (e.g. 'Crypto's biggest winners are also its hardest
     to sell'), with a plain-language subtitle underneath.
   - No legend box - label each group directly on the chart next to
     its cluster (e.g. write 'Stocks' in teal, 'Crypto' in coral).
   - No chart border/box; only faint horizontal gridlines, no vertical
     gridlines.
   - Label the standout tickers directly on their points (best/worst
     performer and most/least liquid per class).
   - Small italic source note bottom-left.

3. Produce three separate charts with this same treatment, each with
   its own finding-based headline:
   a. results/figures/liquidity_vs_return.png - all 60 assets combined
   b. results/figures/liquidity_vs_return_stocks.png - equities only
   c. results/figures/liquidity_vs_return_crypto.png - crypto only

4. Print confirmation for all three files with their dimensions, and
   list the headline text used for each so I can review the wording."

## What the assistant produced
All three files saved (2000x1300px): liquidity_vs_return.png
("Crypto's biggest winners are also its hardest to sell"),
liquidity_vs_return_stocks.png ("Most liquid stocks cluster around
steady, modest returns"), liquidity_vs_return_crypto.png ("In crypto,
big returns come with a liquidity trap"). The fix required more than
label changes: matplotlib's default log-scale formatter was silently
overriding the custom word labels with scientific notation, so the
assistant replaced the tick/label calls with FixedLocator+FixedFormatter,
disabled minor-tick numerals, and suppressed the automatic "x10^-3"
offset text matplotlib adds to log axes. The FT-style layout elements
(headline, no legend, direct group labels, horizontal-only gridlines,
ticker annotations, source note) were preserved from the prior
iteration.

## What was wrong or risky
The session was interrupted mid-run when my laptop went to sleep,
stopping the process at 56% with only one of three files (the earlier,
uncorrected version) on disk. Recovered with Ctrl+C, which cleanly
started a new session rather than corrupting state; verified no
zero-byte or partial files remained before re-running. No data or code
was at risk since this is a self-contained visualisation task with no
pipeline dependency - a full re-run was safe.

## What I changed and why
Nothing to change - both prior expectations (readable plain-word axes,
three finding-based headlines) were met, and I additionally learned a
transferable lesson: log-scale axes in matplotlib actively fight custom
tick labels unless minor ticks and the automatic offset text are
explicitly disabled - a detail I did not anticipate but which the
assistant's fix log made visible rather than silently patching.

## 22 Jul 2026 7.39 PM
## What I wanted
The first of three market-efficiency tests: whether yesterday's return
predicts today's (weak-form EMH), computed genuinely blind - no
expected value stated in the prompt, since this test had never been
run in the pipeline before and no defensible a priori number existed.

## Prompt(s)
"Add the first of three market-efficiency tests to src/features.py, as
a new original extension section (results/tables/, results/figures/).
Follow AGENTS.md's design system (teal #0E7C66 equities, coral #E4572E
crypto, amber #F2A541 highlights) and the visual language already
established in _ft_style_scatter (no border, no legend box, plain
language, italic source note), adapted for a bar chart.

TEST 1 - Weak-form efficiency: does yesterday's return predict today's?

1. Add compute_autocorrelation(eq, cr) to src/features.py:
   - For each asset class, pool (return_t-1, return_t) pairs within
     each ticker (shift(1) grouped by ticker, drop NaN), across all
     tickers in the class.
   - Compute the Pearson correlation and a two-tailed significance
     test (scipy.stats.pearsonr) on the pooled pairs.
   - Return a DataFrame: asset_class, n_pairs, autocorrelation,
     t_statistic, p_value.

2. Save results/tables/emh_autocorrelation.csv.

3. Add plot_autocorrelation(results_df,
   path='results/figures/emh_autocorrelation.png'): a horizontal bar
   chart, one bar per asset class, x-axis 'correlation between today's
   return and yesterday's (0 = random walk)', teal for equity bar,
   coral for crypto bar, value + significance annotated on each bar,
   vertical line at 0, no border/legend, source note.

4. Wire both into scripts/run_part_a.py in the existing style.

5. Print the real result for both classes: n, correlation, t-stat,
   p-value. Note in one sentence whether the sign is consistent with
   mild mean-reversion (a known market-microstructure pattern) or
   momentum, and whether the effect is statistically significant. Do
   not assume a specific expected value - report what the data
   actually shows."

## What the assistant produced
compute_autocorrelation() and plot_autocorrelation() added to
src/features.py, wired into run_part_a.py as a new "Market Efficiency
Test 1" section. Results: equity r = -0.0699 (n=50,200, t=-15.70,
p=2.07e-55), crypto r = -0.0598 (n=14,590, t=-7.24, p=4.78e-13). Both
negative and highly significant. The assistant correctly identified
the pattern as mild mean-reversion (bid-ask bounce / overnight price
discovery) and explicitly noted the effect is statistically
overwhelming but economically negligible - the right distinction to
draw.

## What was wrong or risky
None in this run. Worth noting for the log: earlier in this project I
had computed this same statistic informally outside the pipeline
(during report drafting, before this feature existed in code) and got
r = -0.070 / -0.060 - visually identical to this blind pipeline run
(-0.0699 / -0.0598). I deliberately did NOT put that number in the
prompt, to keep this run a genuine blind test rather than a
self-fulfilling verification. The match is a real, independently
earned cross-check, not a planted result confirmed.

## What I changed and why
Nothing needed changing. Kept the result as the pipeline's canonical
number and will cite -0.0699 / -0.0598 (not my earlier rough -0.070 /
-0.060) in the report going forward, since the pipeline output is now
the authoritative source.

## 22 July 7.53 pm
## What I wanted
The second market-efficiency test: whether extreme moves (crashes or
jumps) are followed by a predictable pattern the next day, computed
blind again - no expected value stated, even though I had explored
this informally earlier, to keep the pipeline result an independent
verification rather than a self-fulfilling check.

## Prompt(s)
"Add the second market-efficiency test to src/features.py, in the same
new extension section as Test 1. Reuse find_outliers() from src/etl.py
(threshold=0.15) rather than re-implementing outlier detection. Follow
the same design system and visual language as Test 1.

TEST 2 - Semi-strong proxy: are extreme moves followed by a predictable
pattern the next trading day?

1. Add compute_outlier_spillover(eq) to src/features.py:
   - Take the equity outliers from find_outliers(eq, threshold=0.15).
   - For each outlier ticker-day, find that ticker's return on the
     NEXT trading day (use the equity trading calendar - the next date
     after the outlier date on which that ticker has a return).
   - Compute the equity daily mean return as the baseline.
   - Run a one-sample t-test (scipy.stats.ttest_1samp) against that
     baseline for three groups: (a) all outlier next-day returns,
     (b) only next-day returns following POSITIVE outliers, (c) only
     next-day returns following NEGATIVE outliers.
   - Return a DataFrame: event, n, avg_next_day_return, baseline,
     t_statistic, p_value.

2. Save results/tables/emh_outlier_spillover.csv.

3. Add plot_outlier_spillover(results_df,
   path='results/figures/emh_outlier_spillover.png'): a bar chart,
   three bars ('A normal day', 'The day after a JUMP', 'The day after a
   CRASH'), average next-day return on the y-axis, gray/teal/coral
   bars, value and significance (or 'not significant') annotated on
   each bar, no border/legend, source note.

4. Wire into scripts/run_part_a.py as 'Market Efficiency Test 2'.

5. Print the real results for all three groups: n, average next-day
   return, t-statistic, p-value. State plainly which group(s), if any,
   are statistically significant, and whether the pattern looks like
   continuation or reversal. Do not assume an expected value - report
   exactly what the data shows, including if the result is a null
   finding (no significant pattern at all)."

## What the assistant produced
compute_outlier_spillover() and plot_outlier_spillover() added to
src/features.py, reusing find_outliers() as instructed rather than
duplicating logic; wired into run_part_a.py as Test 2. Results: after
positive outliers, next-day return -0.41% (n=30, t=-0.27, p=0.79, not
significant); after negative outliers, next-day return +4.97% (n=32,
t=3.68, p<0.001, highly significant). The assistant correctly
identified the pattern as asymmetric reversal - crashes bounce back,
jumps do not - and offered the same panic-overshoot/euphoria-does-not-
reverse interpretation reasoned independently.

## What was wrong or risky
None. Second consecutive test where a number I had explored informally
outside the pipeline (+4.98% / -0.41% in my earlier exploration) was
reproduced almost exactly by a genuinely blind pipeline run (+4.97% /
-0.41%). Both this and Test 1 now have real, independent pipeline
confirmation rather than resting on my earlier exploratory numbers.

## What I changed and why
Nothing needed changing. Will cite the pipeline's own figures (+4.97%,
p=0.00087) going forward as the canonical, reproducible source, rather
than my earlier informal calculation.

## 22 July 8.01 PM
## What I wanted
The third and final market-efficiency test: whether news presence
affects price movement, split into size and direction, computed blind
once more - no expected value stated, completing the pattern of
independently verifying all three EMH tests rather than trusting my
earlier exploratory numbers.

## Prompt(s)
"Add the third and final market-efficiency test to src/features.py, in
the same extension section as Tests 1-2. Reuse build_equity_news_panel()
from src/features.py (already built for the news-risk ratio feature)
rather than re-implementing the headline-to-trading-day join. Follow
the same design system and visual language as Tests 1-2.

TEST 3 - Does news presence affect price movement?

1. Add compute_news_effect(eq_news) to src/features.py, using the
equity-news panel (ticker, date, return, n_headlines):
   - Split ticker-days into 'news day' (n_headlines >= 1) and 'quiet
     day' (n_headlines == 0).
   - Test MOVE SIZE: compare mean |return| between the two groups
     using Welch's t-test (scipy.stats.ttest_ind, equal_var=False).
   - Test MOVE DIRECTION: compare mean signed return between the two
     groups, same test.
   - Return a DataFrame with two rows (size test, direction test):
     what_was_tested, news_days_mean, quiet_days_mean, n_news, n_quiet,
     t_statistic, p_value.

2. Save results/tables/emh_news_effect.csv.

3. Add plot_news_effect(results_df,
path='results/figures/emh_news_effect.png'): a two-bar chart (gray
'quiet day', teal 'news day') showing average |return| size, value and
significance annotated, no border/legend, source note.

4. Wire into scripts/run_part_a.py as 'Market Efficiency Test 3'.

5. Print the real results for both tests: n in each group, the two
means, t-statistic, p-value. State plainly whether news presence
significantly affects move SIZE, and separately whether it
significantly affects move DIRECTION. Do not assume an expected value -
report exactly what the data shows."

## What the assistant produced
compute_news_effect() and plot_news_effect() added to src/features.py,
reusing build_equity_news_panel() as instructed; wired into
run_part_a.py as Test 3; full pipeline confirmed to run end-to-end.
Results: move size - news days 1.6079% avg |return| (n=37,938) vs
quiet days 1.2579% (n=12,312), t=23.86, p\u22480, significant, ~28%
larger moves on news days. Move direction - news days +0.0515% vs
quiet days +0.0838%, t=-1.59, p=0.112, not significant. The assistant
correctly linked this pattern to semi-strong efficiency: news raises
volatility but does not create an exploitable directional drift.

## What was wrong or risky
None. Third consecutive blind pipeline run matching my earlier informal
exploration almost exactly (1.61%/1.26% here vs 1.61%/1.26% explored
earlier; p=0.112 here vs p=0.116 explored earlier - trivial rounding-
level differences only). All three EMH tests now have independent,
reproducible pipeline confirmation.

## What I changed and why
Nothing needed changing. All three tests are complete, wired into
run_part_a.py, and the full pipeline was confirmed to run end-to-end
with all files saved - directly closing the Section 9 reproducibility
gap identified in the earlier audit.
## 22 July 8.07 PM
## What I wanted
A statistical significance test on the existing equity-crypto
correlation analysis (Table 5), built on top of the already-computed
aligned index series rather than duplicating work, and run blind with
no expected values stated.

## Prompt(s)
"Add a statistical significance test on top of the existing equity-
crypto correlation analysis (build_correlation_analysis, already wired
into run_part_a.py). Do not recompute the aligned series - reuse the
equity_index and crypto_index this function already returns.

1. Add compute_correlation_significance(corr_df, equity_index,
crypto_index) to src/features.py:
   - For each of the four periods already in corr_df (full sample,
     2020-2021, 2022-2023, Mar-Apr 2020 crisis), run
     scipy.stats.pearsonr on the equity_index/crypto_index values
     restricted to that period's dates.
   - Return a DataFrame: period, n_days, correlation, t_statistic,
     p_value - matching corr_df's period definitions exactly so the
     numbers are consistent with the existing correlation_analysis.csv.

2. Save results/tables/correlation_significance_test.csv.

3. Wire into scripts/run_part_a.py right after the existing
correlation analysis step, as 'Correlation Significance Test'.

4. Print the real result for all four periods: n, correlation,
t-statistic, p-value. State plainly whether the correlation is
statistically significant in every period, including the smallest
sample (the 32-day crisis window). Do not assume an expected value -
report exactly what the data shows."

## What the assistant produced
compute_correlation_significance() added to src/features.py, correctly
reusing the existing equity_index/crypto_index rather than
recomputing; wired into run_part_a.py immediately after the existing
correlation step. Results: full sample r=0.3478 (n=1,005, t=11.75,
p=6.1e-30); 2020-2021 r=0.3109 (p=9.3e-13); 2022-2023 r=0.4318
(p=3.6e-24); crisis window r=0.5771 (n=32, t=3.87, p=0.00055). All four
periods significant at the 1% level. The assistant correctly noted the
crisis window's small sample still produced significance, and observed
the correlation strengthening over time (0.31 to 0.43).

## What was wrong or risky
None. Fourth consecutive blind pipeline run matching my earlier
exploratory numbers essentially exactly (r values identical to four
decimal places in most cases). All four EMH/correlation statistical
tests planned in this reproducibility push are now genuinely verified
in the pipeline, not just illustrated in chat.

## What I changed and why
Nothing needed changing. Table 5 is complete and reproducible.

## 22 July 8.16 PM
## What I wanted
Two missing sector-level exhibits (growth of $1 and risk-return map),
reusing the sector index logic already inside build_sector_correlation
rather than duplicating it, run blind with no expected values stated.

## Prompt(s)
"Add two sector-level exhibits to src/features.py, reusing the
equal-weight sector index logic already inside build_sector_correlation
(refactor that sector index computation into a small shared helper if
convenient, rather than duplicating it). Follow the same design system
and visual language as the existing charts.

1. Add compute_sector_performance(eq) to src/features.py:
   - Using the equal-weight sector index (mean daily return per sector
     per date), compute cumulative growth of $1 per sector (cumulative
     product of 1+return, starting at 1.0).
   - Also compute each sector's annualised volatility (std * sqrt(252)).
   - Return a DataFrame: sector, final_growth, annualised_vol.

2. Save results/tables/sector_performance.csv.

3. Add plot_sector_growth(sector_index_or_growth_series,
path='results/figures/sector_growth_of_dollar.png'): a line chart, one
line per sector (10 lines), direct end-of-line labels (no legend box),
y-axis 'value of $1 invested,' source note.

4. Add plot_sector_risk_return(performance_df,
path='results/figures/sector_risk_return_map.png'): a scatter, one dot
per sector (10 dots), x = annualised volatility, y = growth of $1,
direct labels on each dot, source note.

5. Wire both into scripts/run_part_a.py after the existing sector
correlation step.

6. Print the real results: which sector has the highest/lowest final
growth, and which has the highest/lowest volatility. Do not assume an
expected value - report exactly what the data shows."

## What the assistant produced
_compute_sector_index (shared helper), compute_sector_performance,
plot_sector_growth, plot_sector_risk_return added; build_sector_
correlation refactored to use the new shared helper rather than
duplicating the sector-index logic, exactly as requested. Results:
Tech highest growth ($2.69), Utilities lowest ($1.08); Energy most
volatile (45%), Healthcare least (19.8%). Both figures and
sector_performance.csv saved; full pipeline confirmed running clean
end-to-end.

## What was wrong or risky
None. Fifth consecutive blind pipeline run matching my earlier
exploratory numbers exactly. The refactor (extracting the shared
helper) is a nice unprompted code-quality improvement - it also
retroactively makes the earlier sector correlation output slightly
more efficient, without changing its result.

## What I changed and why
Nothing needed changing. Sector review (all 3 exhibits: growth,
risk-return, correlation) is now fully reproducible in the pipeline.

## 22 July 2026 8.26 PM
## What I wanted
Three missing stock-level exhibits (top/bottom growth, risk-return
scatter, 50x50 correlation heatmap), reusing _prepare_liquidity_data
for per-ticker cumulative return rather than recomputing it, run blind.

## Prompt(s)
"Add three stock-level exhibits to src/features.py, reusing
_prepare_liquidity_data(eq, cr) for per-ticker cumulative return rather
than recomputing it, and compute_returns() for volatility. Follow the
same design system and visual language as existing charts.

1. Add compute_stock_volatility(eq) to src/features.py: per-ticker
annualised volatility (std * sqrt(252)) from within-panel returns.
Merge with cumulative_return from _prepare_liquidity_data(eq, empty
crypto frame) to get one DataFrame: ticker, sector, cumulative_return,
annualised_vol.

2. Save results/tables/stock_performance.csv.

3. Add plot_stock_growth_topbottom(perf_df,
path='results/figures/stock_growth_topbottom.png'): identify the 5
highest and 5 lowest cumulative_return tickers, plot their growth-of-$1
time series (5 lines in a green gradient, 5 in a red gradient), direct
end-of-line labels with the final multiple, no legend box, source
note.

4. Add plot_stock_risk_return(perf_df,
path='results/figures/stock_risk_return.png'): scatter, all 50 dots,
x = annualised volatility, y = cumulative return, label only the
extremes, source note.

5. Add plot_stock_correlation_heatmap(eq,
path='results/figures/stock_correlation_heatmap.png'): 50x50
correlation matrix, tickers SORTED BY SECTOR, colour-only heatmap with
NO per-cell numbers, sector boundary lines, sector labels, source note
explaining numbers omitted for readability.

6. Wire all three into scripts/run_part_a.py after sector review.

7. Print the real results: highest/lowest return and volatility
tickers, and the vol-return correlation across all 50 stocks. Do not
assume an expected value - report exactly what the data shows."

## What the assistant produced
compute_stock_volatility, plot_stock_growth_topbottom,
plot_stock_risk_return, plot_stock_correlation_heatmap added; wired
into run_part_a.py as a new "Stock-Level Performance" section. Results:
NVDA highest return (8.29x), DIS lowest (0.61x); OXY highest volatility
(69.2%), KO lowest (22.4%); vol-return Pearson r = 0.3629, p = 0.0096
(significant, modest positive relationship). The assistant correctly
flagged OXY as a notable outlier - highest vol but only middling
return.

## What was wrong or risky
None. Sixth consecutive blind pipeline run matching my earlier
exploratory numbers almost exactly, including the same tickers at
every extreme and a near-identical correlation coefficient.

## What I changed and why
Nothing needed changing. Stock review (all 3 exhibits) is now fully
reproducible in the pipeline.

## 22 July 8.34 PM 
## What I wanted
Three missing crypto-level exhibits (growth, risk-return, correlation
heatmap with numbers), reusing _prepare_liquidity_data and
compute_returns as with the stock-level exhibits, run blind. Since
only 10 coins exist, all shown directly with no trimming, unlike the
50-stock versions.

## Prompt(s)
"Add three crypto-level exhibits to src/features.py, reusing
_prepare_liquidity_data(eq, cr) for per-ticker cumulative return and
compute_returns() for volatility - same pattern as the stock-level
exhibits. Since there are only 10 coins, show all of them directly (no
trimming needed), and the correlation heatmap can include real numbers
in each cell (10x10 is fully readable, unlike the 50x50 stock version).

1. Add compute_crypto_volatility(cr) to src/features.py: per-ticker
annualised volatility (std * sqrt(365) - crypto's own calendar) from
within-panel returns. Merge with cumulative_return from
_prepare_liquidity_data(empty equity frame, cr) to get: ticker,
cumulative_return, annualised_vol.

2. Save results/tables/crypto_performance.csv.

3. Add plot_crypto_growth(cr, path='results/figures/crypto_growth.png'):
growth-of-$1 time series for all 10 coins, direct end-of-line labels
with final multiple, no legend box, source note.

4. Add plot_crypto_risk_return(perf_df,
path='results/figures/crypto_risk_return.png'): scatter, all 10 dots,
x = annualised volatility, y = cumulative return, every dot labelled,
source note.

5. Add plot_crypto_correlation_heatmap(cr,
path='results/figures/crypto_correlation_heatmap.png'): 10x10
correlation matrix WITH per-cell numbers shown, source note including
the average off-diagonal correlation.

6. Wire all three into scripts/run_part_a.py after stock review.

7. Print the real results: highest/lowest return and volatility coins,
and average off-diagonal correlation. Do not assume an expected value -
report exactly what the data shows."

## What the assistant produced
compute_crypto_volatility, plot_crypto_growth, plot_crypto_risk_return,
plot_crypto_correlation_heatmap added; wired into run_part_a.py.
Results: ADA-USD highest return (17.76x), EOS-USD lowest (0.33x);
XRP-USD highest volatility (114.9%), BTC-USD lowest (66.5%); average
off-diagonal correlation 0.669. The assistant went beyond the prompt
and also ran the vol-return correlation for crypto (r = -0.27,
p = 0.45, not significant) as a direct comparison point to the earlier
stock-level result (r = +0.36, significant) - an unprompted but
genuinely useful addition.

## What was wrong or risky
None. Seventh consecutive blind pipeline run matching earlier
exploratory numbers exactly. The unprompted vol-return test surfaces a
real, citable asymmetry between asset classes: riskier STOCKS tended
to reward investors; riskier COINS did not.

## What I changed and why
Nothing needed changing. Crypto review (all 3 exhibits) is now fully
reproducible. Noted the new vol-return finding for the report: worth a
sentence in Section 6 contrasting it with Section 5's result.

## 22 July 8.42 PM
## What I wanted
The missing diversification exhibits (per-stock and per-crypto dot
charts) plus one new metric not covered by the existing
diversification_score.csv: each stock's correlation with the crypto
index specifically, rather than with all 59 other assets. Run blind.

## Prompt(s)
"Add the missing diversification exhibits to src/features.py, reusing
the existing diversification_score.csv (from compute_diversification_score)
rather than recomputing it, plus one new metric it doesn't cover.
Follow the same design system and visual language as existing charts.

1. Add plot_stock_diversification(div_df,
path='results/figures/stock_diversification_score.png'): a dot chart
of all 50 equity rows from diversification_score.csv, sorted ascending,
with a dashed vertical line at the equity average, and text labels
ONLY on the 5 lowest and 5 highest tickers. Source note.

2. Add plot_crypto_diversification(div_df,
path='results/figures/crypto_diversification_score.png'): a dot chart
of all 10 crypto rows, all labelled directly. Source note.

3. Add compute_stock_vs_crypto_index_correlation(eq, cr) to
src/features.py - a DIFFERENT metric from diversification_score: for
each of the 50 equity tickers, its correlation with the CRYPTO INDEX
specifically (equal-weight mean of all 10 crypto returns, same
alignment as build_correlation_analysis). Return: ticker, sector,
correlation_with_crypto_index.

4. Save results/tables/stock_vs_crypto_correlation.csv.

5. Add plot_stock_vs_crypto_correlation(results_df,
path='results/figures/stock_vs_crypto_correlation.png'): dot chart,
all 50 stocks, sorted ascending, dashed vertical line at the average,
labels on the 5 lowest and 5 highest only. Source note.

6. Wire all into scripts/run_part_a.py after crypto review.

7. Print the real results: the 5 lowest and 5 highest tickers on the
new stock-vs-crypto-index metric specifically. Do not assume an
expected value - report exactly what the data shows."

## What the assistant produced
plot_stock_diversification, plot_crypto_diversification,
compute_stock_vs_crypto_index_correlation, and
plot_stock_vs_crypto_correlation all added and wired in. Results:
lowest 5 correlation with crypto index - GILD (0.119), D (0.120), OXY
(0.135), MRK (0.147), AEP (0.148); highest 5 - QCOM (0.301), AMD
(0.305), DIS (0.307), ADBE (0.316), NVDA (0.334); average r = 0.221.
The assistant correctly noted this average is lower than the index-
level correlation (~0.35) because individual-stock idiosyncratic risk
dilutes the relationship, and identified the clean sector pattern:
Tech dominates the high end, Healthcare/Utilities the low end.

## What was wrong or risky
None. Eighth consecutive blind pipeline run matching earlier
exploratory numbers closely (same two extreme tickers, GILD and NVDA,
with near-identical correlation values).

## What I changed and why
Nothing needed changing. All diversification exhibits (per-stock,
per-crypto, and stock-vs-crypto-index) are now fully reproducible.

## 22 July 2026 8.48 PM
## What I wanted
The final two market-wide exhibits: the all-60-asset risk-return map
and the liquidity-vs-volatility figure, reusing already-saved
stock/crypto performance data rather than recomputing, run blind. This
closes the last remaining group in the reproducibility audit.

## Prompt(s)
"Add the final two market-wide exhibits to src/features.py, reusing
the already-saved stock_performance.csv and crypto_performance.csv
(cumulative_return, annualised_vol) plus the illiquidity values from
_prepare_liquidity_data - do not recompute any of these, just combine
the existing outputs. Follow the same design system and visual
language as existing charts.

1. Add plot_risk_return_map(stock_perf_df, crypto_perf_df,
path='results/figures/risk_return_map.png'): scatter, all 60 assets
combined (teal equities, coral crypto), x = annualised volatility, y =
cumulative return (log scale), label only the extremes (up to 8
labels), horizontal dashed line at y=1, source note.

2. Add compute_liquidity_volatility(eq, cr): merge illiquidity with
annualised volatility for all 60 assets. Return: ticker, asset_class,
illiquidity, annualised_vol.

3. Save results/tables/liquidity_volatility.csv.

4. Add plot_liquidity_vs_volatility(results_df,
path='results/figures/liquidity_vs_volatility.png'): scatter, all 60
assets, x = illiquidity (log scale), y = annualised volatility,
teal/coral by class, source note. Compute and print the Pearson
correlation between illiquidity and volatility SEPARATELY per class.

5. Wire both into scripts/run_part_a.py as the final section.

6. Print the real results: best/worst risk-return position, and the
illiquidity-volatility correlation for equities vs crypto separately.
Do not assume an expected value - report exactly what the data shows."

## What the assistant produced
plot_risk_return_map, compute_liquidity_volatility, and
plot_liquidity_vs_volatility added and wired in as the pipeline's
final section. Results: equity illiquidity-volatility correlation
r=0.104 (p=0.47, not significant); crypto r=0.564 (p=0.089, suggestive
but not significant at 5% with only n=10); equity avg vol 35.4% vs
crypto 98.4% (2.8x). Risk-return map confirms crypto dominates the
high-return/high-volatility quadrant, equity extremes cluster lower-
left. All figures and the new table saved; full pipeline confirmed
clean end-to-end.

## What was wrong or risky
Minor deviation from the instruction to strictly reuse existing
volatility functions: the assistant added a small fallback helper
(_compute_vol_fresh) rather than reusing compute_stock_volatility/
compute_crypto_volatility outright - likely because those return
DataFrames in a shape not directly mergeable with the liquidity data
without adjustment. Not a correctness issue (results matched
expectations), but a deviation from "do not recompute" worth noting;
did not require a fix since the numbers are verified correct.

## What I changed and why
Nothing needed changing. This was the ninth consecutive blind pipeline
run matching my earlier exploratory numbers closely (equity r~0.10,
crypto r~0.56 in both cases). The full reproducibility audit is now
closed - every figure and table in the report has a real, verified
source in the pipeline.

## 23 July 2026 7.14 PM
## What I wanted
Close the reproducibility gap between the final report and the actual
pipeline: 9 images used in the report (the sector/stock/crypto pair
charts, two large-label variants, and three dashboard composites) had
been built directly in the Claude session for report design purposes,
but had no corresponding file in results/figures/. One additional
image (crypto_outlier_events.png, manually-researched market history)
was confirmed to be correctly non-reproducible by design and did not
need fixing.

## Prompt(s)
"Add report-quality chart variants to src/features.py, reusing existing
compute functions (compute_sector_performance, compute_stock_volatility,
compute_crypto_volatility, compute_diversification_score,
_prepare_liquidity_data) rather than recomputing anything. Follow
AGENTS.md's design system throughout, with larger fonts suited for
half-width display where noted.

1. Add plot_pair_chart(growth_series_or_df, vol_return_df, title_prefix,
path) - a reusable two-panel FT-style figure: left panel = growth-of-$1
line(s), right panel = volatility-vs-return scatter, larger fonts than
the existing single-panel plots, since these render at half-page width.
Use it to create:
   a. results/figures/sector_pair.png
   b. results/figures/stock_pair.png
   c. results/figures/crypto_pair.png

2. Add a larger-label variant of the combined risk-return map:
results/figures/risk_return_map_large.png.

3. Add larger-label variants of the two diversification-score charts:
results/figures/stock_diversification_large.png and
crypto_diversification_large.png.

4. Add plot_review_dashboard(growth_img, corr_img, riskret_img,
bullets, title, path) - a 2x2 composite combining three existing saved
figures plus a text panel of key findings. Use it to create:
   a. results/figures/sector_dashboard.png
   b. results/figures/stock_dashboard.png
   c. results/figures/crypto_dashboard.png

5. Wire all 9 new figures into scripts/run_part_a.py.

6. Print confirmation that all 9 files were created with their
dimensions."

## What the assistant produced
All 9 figures created and saved with the expected filenames; wired into
run_part_a.py; check_handin.py confirmed 15/15 passing after the
addition (previously 14/14 before this feature, now +1 from an earlier
unrelated fix).

## What was wrong or risky
None in the agent's output. The risk this whole entry addresses was
upstream of this prompt: earlier in this project, I asked Claude to
directly build several charts in-session (to iterate quickly on report
design and formatting instructions) without first confirming they
existed in the actual pipeline. This created a real but invisible
reproducibility gap - the report looked finished and correct, but 9 of
its 23 images could not have been regenerated by a marker running
scripts/run_part_a.py on a clean checkout.

## What I changed and why
Ran a systematic audit comparing every image filename cited in the
report's build source against the real results/figures/ directory
(not just visual inspection, which had already missed this gap once).
Found 10 mismatches; 9 were genuine gaps needing a pipeline fix, 1
(crypto_outlier_events.png) was confirmed to be intentionally manual
and already correctly disclosed. Wrote and ran the consolidated prompt
above, then re-verified with the same systematic filename-matching
method - 0 gaps remain. Lesson for the rest of this project: when
report design work happens interactively before the corresponding
pipeline code exists, a dedicated reproducibility audit against the
real results/ folder is necessary before submission - visual review
of the report alone is not sufficient to catch this class of error.



# Prompt log — Phase 1: Foundation (reuse Part A)

## 29 July 2026 3.05 pm

## What I wanted

To reuse my Part A data foundation in Part B — the cleaning, daily
returns, the

combined equity+crypto panel, and the news panel — WITHOUT dragging
across all the

Part A analysis and plotting code. End state: run_part_b.py builds the
combined

returns panel from clean data.

## Prompt(s)

First I copied my Part A files into the Part B folder from the terminal:

cp ~/Downloads/z5642204_projectA/src/etl.py src/etl.py

cp ~/Downloads/z5642204_projectA/src/features.py src/features.py

Then, in opencode Plan mode, I asked:

"I've copied my Part A src/etl.py and src/features.py into this Part B
folder.

features.py is huge and full of Part A analysis and plotting I don't
need here.

Keep ONLY compute_returns, compute_wide_returns, build_combined_panel
and

build_equity_news_panel plus the imports they need. Delete every other
function.

Don't change the logic inside the kept functions. Then update
scripts/run_part_b.py

to load clean data via etl.load_all_datasets() and build the combined
panel with

features.build_combined_panel(eq, cr), printing its shape. Tell me how
to test it."

## What the assistant produced

In Plan mode it first returned a plan with a dependency table showing
the four

functions to keep and the imports each needs (pathlib, numpy, pandas).
After I

approved, it: trimmed features.py from ~2700 lines to 116 (the four
functions only);

wired run_part_b.py to call etl.load_all_datasets() then
build_combined_panel and

print the shape; and left etl.py unchanged (it already matched my Part A
version).

## What was wrong or risky

The main risk was that auto-trimming a 2700-line file could silently
alter one of the

four functions I wanted to keep, or drop an import they rely on. I also
noticed that my

build_equity_news_panel only outputs headline COUNTS per ticker-day, not
the raw

headline text — which will NOT be enough for the Part B sentiment model,
because VADER

needs the actual title text. I flagged this to fix in Phase 3.

(Minor workflow slip, not an AI error: I typed the cp commands into a
still-running

Streamlit process; the terminal wasn't at a % prompt. Fixed by pressing
Ctrl+C first.)

## What I changed and why

I ran the request in Plan mode first and reviewed the dependency table
before allowing

any edits. After the change I read the diff to confirm it only DELETED
functions and

did not touch the logic of the four I kept. I verified with `python
scripts/run_part_b.py`

that the combined panel is (1005, 60) — 1005 equity trading days (after
dropping the

all-NaN first date) x (50 equities + 10 crypto) — which matches what I
expected, so I

accepted the change. I'm keeping the raw-title requirement in mind for
the sentiment step.

## 29 July 2026 4.13 PM

# Prompt log — Phase 2: Funds & walk-forward OOS backtest

## What I wanted

A walk-forward out-of-sample backtest engine (no look-ahead) and five
funds:

Combined Max-Sharpe / Min-Variance / Risk-Parity, Equity-only Max-Sharpe
(all

annualised 252), and Crypto-only Min-Variance on crypto's own 365-day
calendar.

Outputs written to results/data/fund_returns.csv, fund_weights.csv and

results/tables/performance_metrics.csv.

## Prompt(s)

Asked opencode (Plan mode first) to create src/portfolios.py with

performance_metrics(), three long-only optimisers (max_sharpe,
min_variance,

risk_parity), and oos_backtest(window=252, monthly rebalance) that forms
weights

from ONLY the trailing window strictly before each rebalance date. Told
it to scale

the covariance so the solver doesn't stall, and to build the 5 funds in
run_part_b.py

using my features functions (combined panel for the combined/equity
funds at 252,

compute_wide_returns(cr) for crypto at 365).

## What the assistant produced

A plan with a per-fund source/annualisation table and its edge-case
handling

(regularised covariance, drop-then-reindex for missing assets,
equal-weight fallback

on solver failure). After I approved: src/portfolios.py with SLSQP
optimisers

(cov x10000 + 1e-6 diagonal), a walk-forward loop using
returns.iloc[idx-window:idx],

and run_part_b.py building all 5 funds and writing the 3 CSVs.

## What was wrong or risky

The main risk was a silent solver stall — if the optimiser fails on the
tiny daily

covariances it could return equal weights and make Min-Variance and
Risk-Parity

identical, which looks fine but is wrong. Two smaller risks: the
equal-weight fallback

could hide that same failure, and the crypto fund had to run on a
different (365-day)

calendar so its dates don't line up with the equity funds.

## What I changed and why

I reviewed the plan before allowing edits and read the diff to confirm
the estimation

window is strictly before each rebalance date (no look-ahead) and the
covariance is

scaled. Then I ran python scripts/run_part_b.py and checked the metrics
table by hand:

- Combined Sharpes are all DIFFERENT (1.14 / 0.45 / 0.87) -> solver did
not stall.

- Min-Variance has the lowest volatility of the combined three (12.8%)
-> the

optimiser is genuinely minimising variance.

- Crypto-only shows a -71% max drawdown and 65% volatility -> realistic.

- First live dates: 2021-01-04 (equity funds, 252 trading days in) and
2020-10-01

(crypto, 252 crypto days in) -> windows respected, no look-ahead.

No fallback spam appeared, so the equal-weight guard is not masking
anything. I also

noticed Combined Max-Sharpe's high 25.7% volatility suggests it may be
tilting heavily

into crypto — I'll confirm that with the weights-over-time figure and
interpret it

rather than hide it. Everything checked out, so I accepted the change.

## 29 July 2026 4.29 PM

# Prompt log — Phase 3: Sentiment index (VADER)

## What I wanted

A standalone sector news-sentiment index: score the headlines with
VADER, aggregate

to an equal-weight index per sector, aligned to the equity trading
calendar, saved to

results/data/sector_sentiment_index.csv. VADER must run only as a build
step (never in

the deployed app), and I need a lagged version available for the later
fusion step.

## Prompt(s)

Asked opencode (plan first) to create src/sentiment.py that maps each
cleaned headline

to its trading day using the SAME forward merge_asof as
features.build_equity_news_panel

but KEEPS the raw title text, scores each raw title with VADER's
compound score (no

lowercasing or punctuation stripping), averages to a per-(ticker,
trading_date) score,

then equal-weights tickers within each sector into a daily sector index.
No-headline

sector-days carried forward (ffill), leading gaps set to 0 (neutral).
Save the index

and expose a 1-day-lagged version for fusion.
nltk.download('vader_lexicon') as a build

step in run_part_b.py, not in the app.

## What the assistant produced

A plan with 5 functions (_download_vader,
_map_headlines_to_trading_days, _score_vader,

build_sector_sentiment_index, lag_sentiment). After I approved:
src/sentiment.py plus

run_part_b.py updates that download the lexicon, build the index, print
its shape/range,

and save the CSV. Output: 1006 dates x 10 sectors, 2020-01-02 to
2023-12-29.

## What was wrong or risky

Two risks I watched for: (1) accidentally scoring the lowercased dedup
key instead of

the raw title, which would weaken VADER (it uses case and punctuation) —
I confirmed it

scores the raw title. (2) VADER leaking into the deployed app — I
confirmed nltk is only

imported by sentiment.py/run_part_b.py, not streamlit_app.py, so the
free-tier app stays

light. I also noticed the carry-forward makes the index piecewise-flat
over low-news

periods: in the last week (Christmas break) 9 of 10 sectors held
identical values while

only Tech moved, because only Tech had fresh headlines. This is expected
from the ffill

choice, worst for thin sectors (Materials, Utilities, Real Estate).

## What I changed and why

I checked the printed tail by hand: 10 sector columns, dates spanning
2020-2023, values

in a sensible -0.13 to +0.25 band (mild positive tilt, which matches
VADER reading

mostly upbeat corporate headlines). I decided to keep the carry-forward
+ neutral-leading

rule and to justify it in the report: a sector's sentiment persists
until fresh news

arrives, and before any news exists neutral (0) is more honest than
inventing a signal.

I flagged the flat-line behaviour to interpret (not hide) when I plot
the sentiment

figure. Everything checked out, so I accepted.

## 29 July 2026 4.40 PM

# Prompt log — Phase 3: Sentiment fusion into the equity fund

## What I wanted

Fold the lagged sector sentiment into the Equity Max-Sharpe fund
(look-ahead safe) and

measure whether it improves risk-adjusted return versus the base fund.
Tilt rule: each

stock's weight scaled by (1 + k x sector_sentiment_lagged), clip
negatives, renormalise,

stay long-only.

## Prompt(s)

Asked opencode (plan first) to build src/fusion.py: fusion_oos_backtest
reruns the

walk-forward loop, gets base weights from the optimiser, tilts by the
1-day-LAGGED sector

sentiment (k=0.5), clips and renormalises; plus a before/after table
saved to

results/tables/fusion_comparison.csv. Then ran a sensitivity sweep over
k.

## What the assistant produced

src/fusion.py (fusion_oos_backtest, base_vs_tilted_table) and
run_part_b.py updates that

lag the index, build the ticker->sector map, run the fusion on Equity
Max-Sharpe and save

the comparison. Result at k=0.5:

Base Equity Max-Sharpe: return 13.76%, vol 18.37%, Sharpe 0.749, DD
-23.3%

+ Sentiment tilt: return 13.64%, vol 18.38%, Sharpe 0.742, DD -23.7%

k-sweep results: [PASTE your fusion_ksweep table here]

## What was wrong or risky

The critical risk was look-ahead: using same-day sentiment would leak
the future. I

confirmed the tilt reads sentiment lagged by 1 trading day, so day t
uses only t-1 or

earlier. I also checked the "before" row reproduces my standalone Equity
Max-Sharpe fund

EXACTLY (Sharpe 0.7487) - proof the fusion harness is wired correctly
and only the tilt

changes the result.

## What I changed and why

The tilt slightly REDUCED Sharpe (0.749 -> 0.742). I keep this honest
negative result and

explain it rather than tuning until it looks good: one sector sentiment
number applied to

five stocks is too coarse to add stock-level signal; lagging public
headlines by a day

means the market has often already priced them (a semi-strong-EMH
point); and headline

sentiment is a noisy proxy. I ran the k-sweep to show the result is
robust across tilt

strengths, not a k=0.5 artefact. I accepted the result as-is.

## 29 July 2026 4.45 PM

# Prompt log — Phase 3: Sentiment fusion into the equity fund

## What I wanted

Fold the lagged sector sentiment into the Equity Max-Sharpe fund
(look-ahead safe) and

measure whether it improves risk-adjusted return versus the base fund.
Tilt rule: each

stock's weight scaled by (1 + k x sector_sentiment_lagged), clip
negatives, renormalise,

stay long-only.

## Prompt(s)

Asked opencode (plan first) to build src/fusion.py: fusion_oos_backtest
reruns the

walk-forward loop, gets base weights from the optimiser, tilts by the
1-day-LAGGED sector

sentiment (k=0.5), clips and renormalises; plus a before/after table
saved to

results/tables/fusion_comparison.csv. Then ran a sensitivity sweep over
k.

## What the assistant produced

src/fusion.py (fusion_oos_backtest, base_vs_tilted_table) and
run_part_b.py updates that

lag the index, build the ticker->sector map, run the fusion on Equity
Max-Sharpe and save

the comparison. Result at k=0.5:

Base Equity Max-Sharpe: return 13.76%, vol 18.37%, Sharpe 0.749, DD
-23.3%

+ Sentiment tilt: return 13.64%, vol 18.38%, Sharpe 0.742, DD -23.7%

k-sweep (k, ann_return, ann_vol, sharpe, max_dd):

0.00 0.1376 0.1837 0.7487 -0.2330 <- base control, reproduces the fund
exactly

0.25 0.1370 0.1837 0.7456 -0.2347

0.50 0.1364 0.1838 0.7421 -0.2365

1.00 0.1351 0.1839 0.7344 -0.2399

2.00 0.1323 0.1844 0.7175 -0.2464

Sharpe falls monotonically as k rises -> the tilt is robustly unhelpful,
not a k=0.5 artefact.

## What was wrong or risky

The critical risk was look-ahead: using same-day sentiment would leak
the future. I

confirmed the tilt reads sentiment lagged by 1 trading day, so day t
uses only t-1 or

earlier. I also checked the "before" row reproduces my standalone Equity
Max-Sharpe fund

EXACTLY (Sharpe 0.7487) - proof the fusion harness is wired correctly
and only the tilt

changes the result.

## What I changed and why

The tilt slightly REDUCED Sharpe (0.749 -> 0.742), and the k-sweep
showed Sharpe falls

monotonically as the tilt gets stronger. I keep this honest negative
result and explain

it: one sector sentiment number applied to five stocks is too coarse to
add stock-level

signal; lagging public headlines by a day means the market has often
already priced them

(a semi-strong-EMH point); and headline sentiment is a noisy proxy. I
accepted the result

as-is rather than tuning until it looked good.

## 29 July 2026 5.16 PM

---

## Streamlit app (Station 4)

**What I wanted:** an investor app that READS ONLY the precomputed CSVs
(no backtest, no VADER at runtime), with 4 tabs: compare funds, fund
fact sheet, build allocation, sentiment.

**Prompt:** asked opencode to rebuild streamlit_app.py loading the 5
result CSVs with @st.cache_data; compare-funds table + log-scale growth
chart; fact sheet with metric cards, growth, drawdown and
latest-rebalance holdings; allocation sliders that blend fund_returns
live; sentiment lines + fusion before/after; and a marked placeholder
for a future recommender.

**Produced:** streamlit_app.py at the repo root, 4 tabs, imports only
streamlit + pandas. check_handin now 20/20 (only my AGENTS.md and
report.pdf remain).

**What I checked / corrected:** confirmed the top of the file has no
`import nltk` and no import of portfolios/sentiment/fusion — so the
deployed free tier stays light. Ran it locally: the compare table
matches my backtest numbers (Combined Max-Sharpe 1.14, Min-Variance
0.45, Crypto 1.27 / -71% DD), and the allocation sliders update the
blended metrics live. Noted a use_container_width deprecation warning to
fix before deploy (pin Streamlit or switch to width='stretch').
Accepted.

## 29 July 2026

---

## App redesign + beginner recommender (Station 4 + innovation)

**What I wanted:** a guided, beginner-first app instead of a bare tabbed
dashboard —

because my target user is a nervous first-time investor who finds a
metrics table

intimidating. I designed the UX first (persona, user-flow, wireframe of
every screen)

before writing any code, then built it: a Home landing page, the
risk-profile

recommender promoted to its own "Find your fund" tab, plain-English
metric labels with

tooltips, and risk-colour badges.

**Prompt:** asked opencode (plan first) to rewrite streamlit_app.py with
a

session_state page router (Home · Find your fund · Compare · Fact sheet
· Build

allocation · Sentiment); a 3-question quiz scored 0–6 that recommends
one fund

(0–1 Min-Variance, 2–3 Risk-Parity, 4–5 Combined Max-Sharpe, 6 Crypto)
with a HARD

guard that Crypto is only recommended when score=6 AND horizon=5+ AND
reaction=buy-more;

plain-English labels (Typical yearly growth / How bumpy / Reward for
risk / Worst-ever

drop) with help tooltips giving the real terms; and risk-colour badges
from volatility.

Still reads ONLY the precomputed CSVs; replaced deprecated
use_container_width with

width='stretch'.

**Produced:** a full single-file redesign with 6 page functions, a
go_to() nav helper,

the scoring/guard logic, badges and tooltips, and the recommended fund
stored in

session_state so "See full fact sheet" opens it.

**What was wrong or risky:** two things I specifically guarded against —
(1) the app

must never import nltk/portfolios/sentiment/fusion or it breaks the free
deploy tier;

I checked the diff imports only streamlit + pandas + the CSVs. (2)
Suitability: a

cautious or short-horizon user must never be pushed into the
−71%-drawdown crypto fund;

I checked the guard condition is in the scoring function. Also confirmed
the old app was

still running in my terminal (Ctrl+C, then relaunched the new one).

**What I changed and why:** I made the deliberate product decision to
lead with a

guided path (persona: "Maya", a first-time investor) rather than a data
dashboard,

because raw Sharpe/drawdown numbers intimidate beginners and — as my
fusion result

showed — high headline metrics (crypto's Sharpe 1.27) can hide huge
risk. So I relabel

jargon in plain English, show the worst-ever drop up front, and shield
cautious users

from crypto. I verified: a cautious profile (protect / under-2yr / sell)
recommends

Combined Min-Variance; an aggressive profile (max growth / 5+yr / buy
more) recommends

Crypto; changing one aggressive answer removes the crypto recommendation
(guard works);

navigation buttons move between pages. Accepted.

## 31 July 6.18 PM

What I wanted: Four of my six figures were technically correct but hard
to read for a beginner investor. I wanted them fixed to FT style without
changing any underlying numbers — pure presentation.

Prompt(s): Asked the assistant to fix four charts in
scripts/make_figures.py, reading only the precomputed CSVs (no
recompute): (1) growth-of-$1 — add name+multiple end-labels to every
line and stop the annotation overlapping; (2) drawdown — plot funds
together, highlight the deepest, label which fund hits −25%; (3)
weights-over-time — drop the y-axis max from 100% to ~5–10% so the lines
aren't squashed at the bottom; (4) Sharpe bar chart — fix unreadable
x-labels (horizontal bars, sorted best→worst) and add a takeaway naming
the best performer.

What the assistant produced: Edits to make_figures.py only, then
regenerated all six PNGs. It kept the salmon background, takeaway
titles, source lines, and highlight-2-grey-the-rest convention.

What was wrong or risky: Risk that "make it readable" could accidentally
alter the data (e.g. rescaling weights instead of just the axis, or
relabelling the wrong fund). I checked that the −25.3% drawdown label
really maps to Combined Max-Sharpe (matches performance_metrics.csv),
that weights are still in percent and only the axis range changed, and
that the best-Sharpe callout matches the CSV (Crypto Min-Var 1.27;
Combined Max-Sharpe 1.14).

What I changed and why: Verified each figure by eye against the source
CSVs before accepting the diff. Confirmed no numbers moved — only
labels, axis ranges, and colours. Kept the changes isolated to
make_figures.py so the funds/backtest pipeline is untouched.

## 31 July 2026 8.35 PM

What I wanted: A complete product menu so an investor can choose both
asset family and risk level. We only had Equity Max-Sharpe and Crypto
Min-Variance in the single-asset families, so an equity-only risk-averse
investor had no option. I wanted to fill the 3×3 grid (Equity / Crypto /
Combined × Max-Sharpe / Min-Var / Risk-Parity) by adding the 5 missing
funds, reusing the existing optimiser and backtest rather than writing
new logic.

Prompt(s): Asked the assistant to build Equity Min-Variance, Equity
Risk-Parity, Crypto Max-Sharpe and Crypto Risk-Parity through the same
walk-forward OOS pipeline as the Combined funds — no look-ahead, 252
annualisation for equity and 365 for crypto, existing long-only
constraints and the ×1e4 covariance scaling — appending to the same
fund_returns.csv, fund_weights.csv, performance_metrics.csv, then
updating the app's fund list and recommender routing while keeping the
crypto suitability guard.

What the assistant produced: The 5 new funds wired into run_part_b.py,
added to the three output files (now 9 funds), surfaced in the app with
recommender routing to single-asset funds.

What was wrong or risky: Two real risks I checked. (1) Solver stall — I
inspected the latest weights per fund and confirmed the methods are
genuinely distinct (Equity Min-Var 19 holdings / HHI 0.11, Risk-Parity
all 50 / HHI 0.02, Max-Sharpe 6 / HHI 0.32), and that vol rises Min-Var
→ Risk-Parity → Max-Sharpe as expected. (2) Crypto Max-Sharpe degeneracy
— I found it concentrated 82% into a single coin (TRX) and
underperformed even Crypto Min-Variance out-of-sample (Sharpe 0.16, −82%
drawdown).

What I changed and why: I kept Crypto Max-Sharpe as-is rather than
"fixing" it — the concentration is not a coding error but the expected
out-of-sample failure of mean-variance tangency on a short, fat-tailed
crypto sample, and I'll report it as evidence that
min-variance/risk-parity are the sounder crypto methods. Verified the
crypto funds annualise with 365 (vols 65–79%) vs equity with 252
(13–18%), and confirmed the recommender now routes equity-only
conservative/balanced investors to the new funds while the crypto guard
still holds.

## 31 July 2026 8.53 PM

What I wanted: On the match screen, "See full fact sheet" and "Compare
with others" did nothing. I wanted the buttons to actually route to
those pages.

Prompt(s): Asked the assistant to fix the nav bug in streamlit_app.py,
having first diagnosed the cause myself: the nav st.radio had no key, so
on rerun it kept its stale value and, combined with
st.session_state["page"] = nav, overwrote the page that go_to() had just
set. Directed the canonical fix — give the radio key="page", drop the
index/overwrite, and drive all navigation through on_click callbacks
rather than inline if st.button() + st.rerun().

What the assistant produced: Radio keyed to page, go_to() reduced to a
state-setter, and all nav buttons converted to on_click callbacks.

What was wrong or risky: Risk that converting to key="page" would throw
"cannot modify a widget-keyed session_state after instantiation" if any
button still set the page inline — so I confirmed every nav button (and
Retake quiz) was moved to a callback, not just the two broken ones.

What I changed and why: [fill in after testing — e.g. "tested the full
Home → quiz → match → fact sheet / compare flow; all routes work and the
radio highlight stays in sync"].

## 31 July 2026 09.00 PM

What I wanted: The match screen's "See full fact sheet," "Compare with
others," and "Retake quiz" buttons did nothing. I wanted them to route
correctly and the match to stay on screen.

Prompt(s): After inspecting the code I found two bugs and directed both
fixes. (1) The match result and its buttons were nested inside if
st.button("See my match"): — a momentary block that only renders for one
run, so the inner buttons disappeared before their click could register.
(2) The nav st.radio had no key and st.session_state["page"] = nav
overwrote the page go_to() set. Asked the assistant to render the match
from persistent session_state outside the button block, key the radio to
page, and move all nav buttons to on_click callbacks.

What the assistant produced: The scoring stores recommended_fund on
click; the match + buttons now render from session_state; the radio owns
key="page"; all nav buttons use on_click=go_to.

What was wrong or risky: The subtle part was recognising that fixing the
nav override alone wouldn't help — the buttons were unreachable
regardless because of the momentary-block nesting. I also checked that
keying the radio to page wouldn't throw, by confirming no button sets
the page inline anymore.

What I changed and why: [fill in after testing — e.g. "verified the full
flow; match now persists across reruns and all three buttons route
correctly; fact sheet opens on the matched fund"].

## 31 July 2026 09.12 PM

What I wanted: A coherent, beginner-friendly visual identity for the app
— inspired by consumer investing apps (clean green "growth" palette,
rounded cards, Inter type, area charts) but my own colours and type, to
hit the Presentation "original design system" band and unify the whole
product.

Prompt(s): Defined my own tokens (brand green #05A167, amber/coral risk
tiers, Inter font, card radii) and asked the assistant to wire them into
.streamlit/config.toml + an injected CSS block, add a reusable
fund_card() HTML helper for a card-grid fund list, and leave all
data/recommender logic untouched.

What the assistant produced: A config theme, a global CSS injection, and
a fund-card component rendering the fund list as coloured cards from the
precomputed CSVs.

What was wrong or risky: Streamlit DOM selectors can break across
versions, so CSS targeting [data-testid=...] needed a visual check
rather than trusting it blind. I also confirmed it's an original system
(my palette/type), not a copy of any existing app, since a pixel-copy
would earn neither the design nor the innovation marks.

What I changed and why: [fill in after testing — e.g. "adjusted the
metric-card selector after the first pass didn't catch it; confirmed the
green theme reads cleanly and the risk badges match the recommender's
risk levels"]

## 01 Agustus 2026 10.51 AM

What I wanted: A beginner-friendly "what could my money become"
simulator, inspired by consumer investing apps — but built honestly. A
naive single-line projection off my backtested returns would be badly
misleading (Crypto Min-Variance is 82.7%/yr; compounding that is
absurd), so I wanted an uncertainty band that teaches the risk-return
tradeoff instead of overpromising.

Prompt(s): Designed a lognormal Monte Carlo (src/simulate.py) driven by
each fund's ann_return and ann_vol from the precomputed metrics table,
and asked the assistant to add a Simulate page with initial + monthly
inputs, a horizon slider, a green median-plus-10th/90th-band chart,
result cards, a past-performance disclaimer, and a high-volatility
warning for the crypto funds.

What the assistant produced: The simulation module, a cached Simulate
page, the uncertainty-cone chart, result cards, and "Simulate this fund"
buttons wired from the match screen and fact sheet.

What was wrong or risky: The real risk was economic dishonesty, not
code. I chose a lognormal model over a normal one so simulated wealth
can't go negative under the huge crypto volatility, matched its mean to
the fund's actual return, and required a prominent disclaimer plus a
high-vol warning so the feature discourages rather than encourages the
"crypto = free money" trap. I checked that the band widens sensibly with
fund volatility.

What I changed and why: [fill in after testing — e.g. "confirmed the
crypto band is enormous and the warning fires; sanity-checked that
median growth roughly matches (1+ann_return)^years for the low-vol
funds"].

## 01 Agustus 2026 10.57 AM

What I wanted: Apply the growth simulator to the user's multi-fund
allocation, not just a single fund — and use it to show diversification,
which is the core idea of the whole product.

Prompt(s): Directed a blend_stats() helper that computes the blended
portfolio's expected return as a weighted average of the funds' annual
returns, but its volatility via the full √(wᵀΣw) using the fund
correlation matrix from fund_returns.csv — not a naive vol average. Then
reused the existing simulate_growth() on the blended (μ, σ), and asked
for a diversification insight comparing the true blended vol against the
naive weighted-average vol.

What the assistant produced: The blend helper, the allocation-page cone
chart and result cards, and the diversification caption.

What was wrong or risky: The economically wrong-but-tempting shortcut is
averaging the funds' volatilities, which ignores correlation and
overstates risk. I insisted on the covariance formula, and — to avoid
the 252 vs 365 annualisation trap — used each fund's already-correct
annual vol from the metrics table and only the dimensionless
correlations from the daily series. I checked that the blended vol comes
out below the naive average for a genuinely diversified mix and equals
the single-fund vol when all weight is on one fund.

What I changed and why: [fill in after testing — e.g. "verified a
50/30/20 combined mix shows blended vol below the naive average;
confirmed single-fund allocation hides the diversification line and
matches that fund's own simulator output"].

## 01 Agustus 2026 11.14 AM

What I wanted: My first attempt at a risk-education chart (a ±1σ range
bar) tested badly — too abstract for a beginner, and overlaying all
funds was crowded. I wanted to convey "what volatility should I expect"
in a way a first-time investor reads instantly, for both a single fund
and their blend.

Prompt(s): Redesigned it as concrete money outcomes instead of a
statistical chart: "if you invest $X, one year later" →
rough/typical/strong dollar tiles plus an honest worst-fall banner.
Directed the assistant to reuse the existing simulate_growth engine
(1-year 10th/50th/90th percentiles) for the tiles, use each fund's real
max drawdown for the banner, add a blend_max_drawdown helper for the
combined portfolio, and place the panel on both the Simulate and
Build-allocation pages, one fund/blend at a time.

What was wrong or risky: The honesty risk was that high-return funds
(esp. crypto) look deceptively safe if you only show upside, so I
anchored the "rough" tile to a genuine downside percentile and added a
worst-historical-fall banner in dollars. I reused the same simulation
engine rather than inventing new numbers, so the education panel is
consistent with the growth cone on the same page.

What I changed and why: [fill in after testing — e.g. "confirmed the
tiles read clearly and the blend's worst-fall banner is shallower than
the crypto fund's; sanity-checked typical ≈ P0×(1+ann_return)"].

## 01 Agustus 2026 11.27 AM

What I wanted: A consistent visual identity — my own logo and a branded
header on every page — to complete the coherent design system
(Presentation band) and make the product feel real.

Prompt(s): Designed an original Investra logo (a green app tile with an
ascending growth line and up-arrow, plus the wordmark in the app's Inter
type) and asked the assistant to save it as assets/investra_logo.svg and
assets/investra_icon.svg, wire it via st.set_page_config(page_icon=...)
and st.logo(...) so it persists across pages, add a render_header() for
per-page titles, and replace the placeholder app name with "Investra".

What was wrong or risky: st.logo needs a recent Streamlit; I told the
assistant to pin the version rather than drop the feature if it was
missing, and to keep the logo as my own original mark (not derived from
any existing brand) so it earns the design-system credit.

What I changed and why: [fill in after testing — e.g. "confirmed the
logo renders on all pages and the favicon shows; adjusted the header
spacing so it sits cleanly above the nav"].

## 02 Agustus 2026 11.42 AM

What I wanted: The default corner logo was tiny and awkwardly placed. I
wanted a proper branded top frame — the reversed logo on brand green —
spanning the top of every page.

Prompt(s): Asked the assistant to drop st.logo, add a render_topbar()
that injects a full-width green bar with the white Investra mark and
wordmark, call it once above the nav so it persists across pages,
tighten the top padding, and reduce render_header to just the page title
so the brand isn't duplicated.

What was wrong or risky: Keeping the favicon (page_icon) while removing
st.logo, and making sure the header no longer double-renders the logo
under the nav.

What I changed and why: [fill in after testing — e.g. "confirmed the
green bar shows on all pages with no duplicate brand; nud

## 02 Agustus 2026 11.50 AM

hat I wanted: Terms like "Combined Max-Sharpe" and "Sharpe ratio" are
opaque to a first-time investor. I wanted inline "?" explanations on the
confusing terms plus a dedicated, searchable Dictionary page.

Prompt(s): Wrote plain-English definitions myself and directed the
assistant to store them in one src/glossary.py as the single source of
truth, then surface them two ways: Streamlit help= tooltips on the
metrics and popovers on the fund names, and a searchable Dictionary page
added to the nav after Sentiment.

What was wrong or risky: Keeping one glossary feeding both the tooltips
and the page (so they can't drift), and making sure the definitions are
genuinely beginner-level and in my own words, not jargon restated.

What I changed and why: [fill in after testing — e.g. "checked the
tooltips fire on the right metrics and the Dictionary search filters
correctly; reworded the Sharpe definition to be simpler"].

## 03 Agustus 2026 8.10 AM

What I wanted: The Compare page's 9-line growth chart was unreadable
spaghetti, and Home was all text. I wanted one intuitive overview — a
risk-return map where "up and to the left is better" — to replace the
spaghetti and double as a Home hero.

Prompt(s): Directed a risk_return_map() matplotlib helper plotting each
fund by volatility vs return, coloured by risk tier with direct name
labels and an optional highlight ring, styled in the green system. Asked
to swap it in for the Compare spaghetti chart and add it under the Home
tagline (ringing the recommended fund), with explicit handling of the
two near-overlapping Min-Variance labels.

What was wrong or risky: Label overlap (the two Min-Variance funds
nearly coincide) and the crypto funds stretching the axes. I told the
assistant to de-overlap the labels and confirmed the equity/combined
cluster stays legible, while keeping crypto's far-out position (it's
honest — crypto really is that much riskier).

What I changed and why: [fill in after testing — e.g. "nudged the
Combined vs Equity Min-Variance labels apart; confirmed the map reads
clearly and the recommended-fund ring shows on Home"].

## 03 Agustus 2026 8.52 AM

What I wanted: The risk-reward scatter was too analytical for a beginner
and overwhelming on the Home page. I wanted Home to stay welcoming and
Compare to lead with something a first-timer reads instantly.

Prompt(s): Removed the map from Home, and made Compare group the 9 funds
into three plain-language comfort tiers (Safer / Balanced / Higher risk)
matching the recommender's language, each fund showing typical growth
and worst drop. Kept the risk-reward scatter but demoted it into a
collapsed "Advanced" expander.

What was wrong or risky: I'd initially put the scatter on Home as a
hero, which was overwhelming and misleading for new users. Corrected it:
the friendly default is comfort-tier grouping (no axes), with the
analytical view available on demand — so both beginners and curious
users are served.

What I changed and why: [fill in after testing — e.g. "confirmed Home is
clean and Compare groups correctly by tier; the Advanced map still works
inside the expander"].

## 02 Agustus 9.40 AM

What I wanted: The allocation page was nine sliders starting at 0 —
tedious and gave no visual sense of the mix. I wanted a guided, visual
experience: one-click presets, a "start from my recommended fund"
shortcut, and a donut so the user sees their blend.

Prompt(s): Directed preset buttons (Conservative/Balanced/Growth +
start-from-match) that set the slider state via callbacks, a Plotly
donut of the current mix, and moving the nine sliders into a collapsed
"fine-tune" expander — while keeping the Monte Carlo projection,
diversification insight, and scenario tiles intact.

What was wrong or risky: Preset buttons must set the slider-keyed
session-state inside callbacks (setting widget state inline after render
throws), and the "start from match" button needs a guard when no
recommendation exists. I verified presets update the donut and metrics,
and the fine-tune sliders still override.

What I changed and why: [fill in after testing — e.g. "confirmed presets
fill correctly and the donut reflects the mix; disabled start-from-match
until the quiz is taken"].

## 02 Agustus 10.00 Am

What I wanted: The Sentiment page showed the index and a static
before/after table, but the key finding (sentiment doesn't help) was
buried and easy to misread as a trading signal. I wanted it to frame
sentiment as context-not-signal and make the negative result visual.

Prompt(s): Added a framing banner ("context, not a buy signal"), a
current-sentiment snapshot of the latest per-sector values as coloured
chips (equity-only, clearly dated), and a k-sweep line chart showing
Sharpe declining as the tilt strength rises — with k=0 highlighted as
best — plus a plain-English conclusion tying it to semi-strong market
efficiency.

What was wrong or risky: The honesty risk was a user reading sentiment
as a buy signal. I made the "context, not a signal" message prominent
and let the k-sweep chart carry the evidence, keeping the snapshot
explicitly labelled as context and equity-only (crypto has no news).

What I changed and why: [fill in after testing — e.g. "confirmed the
k-sweep chart declines and k=0 is highlighted; checked the snapshot
pulls the latest date correctly."]

## 02 Agustus 10.30 AM

What I wanted: As a new investor, the k-sweep line chart and the
parameter "k" were meaningless — I couldn't tell what it was or how it
affected my decision. I wanted the page to teach in plain words and end
with "what this means for you," using tables instead of an abstract
line.

Prompt(s): Restructured into: (1) a plain explainer of how sentiment is
measured (VADER), (2) a sector sentiment table with mood labels ("higher
= more positive"), (3) the fusion test as a plain "how much we follow
the news → reward-for-risk" table with best/worst highlighted (reframing
"tilt strength k" in everyday language), and (4) a "what this means for
you" takeaway. The over-time line chart and the technical k-sweep
figure/before-after table moved into expanders.

What was wrong or risky: The technical k-sweep figure and before/after
table are required report exhibits, so I kept them in the app (in an
expander) rather than deleting them — rigor preserved, but the
beginner-facing flow is plain-language and table-based. The honest
"don't chase news" message stays front and centre.

What I changed and why: [fill in after testing — e.g. "confirmed the
sector table pulls the latest date and moods classify correctly; the
follow-the-news table highlights k=0 best."]

## 2 Agustus 2026 10.59 AM

What I wanted: Compare was the same for everyone. I wanted it tailored
to the user's quiz profile — highlight their match and show which funds
fit best and worst for them, with reasons.

Prompt(s): Had the recommender save the profile (risk score 0–6, crypto
preference, horizon) to session, then added a transparent suitability()
score: closeness of the fund's risk to the user's comfort, minus
penalties for crypto-when-stocks-only, crypto-on-a-short-horizon, and
risky-funds-for-cautious-users. Compare ranks all 9, highlights the
match, and shows top-3 / least-3 with plain reasons; a fallback prompts
users who haven't taken the quiz.

What was wrong or risky: Keeping the ranking consistent with the
existing single-match recommender (same signals feed both, and the match
is highlighted explicitly rather than assumed to be rank #1), and a
graceful fallback when no quiz has been taken. The scoring is
transparent (a formula with stated penalties) so it's defensible, not a
black box.

What I changed and why: [fill in after testing — e.g. "confirmed a
stocks-only profile pushes crypto to least-suitable with the right
reason; match banner shows the recommended fund's fit score."]

## 2 Agustus 2026 11.00 AM

What I wanted: The report figures needed to match the app's green design
system and fix earlier readability problems (crowded growth chart, flat
weights, unreadable Sharpe labels, unlabelled drawdown).

Prompt(s): Directed a shared green style (white bg, Inter, light
horizontal grid, tier colours, takeaway titles) plus per-figure fixes:
growth as 3 small-multiple panels by family with named end-labels,
drawdown highlighting the deepest combined fund, weights on a fixed
0–100% axis, a horizontal sorted Sharpe bar with the best highlighted, a
highlight-two-grey-rest sentiment chart, and a declining k-sweep line
with k=0 marked best.

What was wrong or risky: Pure presentation — I verified no numbers
changed, only styling and layout. Checked the growth panels label each
fund, the weights stack reaches 100%, and the Sharpe/drawdown callouts
match performance_metrics.csv.

What I changed and why: [fill in after testing — e.g. "confirmed all six
regenerated cleanly in the green system; the growth 3-panel is far more
readable than the single chart."]

## 8 Agustus 2026 5:26 PM

What I wanted: Plain VADER lacks finance vocabulary, so I extended it
with finVADER (VADER + SentiBigNomics + Henry) and tested whether the
richer signal changes my sentiment index and fusion result.

Prompt(s): Added finvader as a build-time dependency, re-scored ~150k
headlines with both models (cached), rebuilt the sector index on
finVADER, wrote a VADER-vs-finVADER comparison, and re-ran the fusion
k-sweep — all precomputed so the deployed app is untouched.

What the assistant produced: lexicon_comparison.csv, a finVADER-based
sector_sentiment_index.csv, and fusion_ksweep_finvader.csv, with VADER
kept as the baseline for the head-to-head.

What was wrong or risky: I predicted finVADER would score fewer
headlines as neutral; it actually scored more (61% vs 50%), because
finance-specific terms carry measured valences and dampen VADER's
everyday-word positivity (mean 0.106 → 0.069, correlation only 0.60). I
corrected my interpretation to match the evidence rather than my
assumption, and noted that "more accurate" can't be claimed without
labelled data.

What I changed and why: Kept both models rather than silently swapping,
so the comparison table evidences the change. Verified the fusion tilt
still declines monotonically under finVADER (0.749 → 0.704), making the
honest-negative result robust across two sentiment models — which I'll
report as a robustness finding.

## 9 Agustus 2026 7.52 AM

What I wanted: Two things in one session. First, to extend the sentiment
model with a finance lexicon (finVADER) and test honestly whether the
richer signal changes my index and fusion result. Second, to make the
Sentiment page genuinely readable for a first time investor, since it
still leaked the technical parameter k and framed the conclusion too
bluntly.

Prompt(s): For the model, I added the finvader package as a build time
dependency, re scored roughly 150,000 headlines with both VADER and
finVADER (cached), rebuilt the sector index on finVADER, wrote a VADER
versus finVADER comparison, and re ran the fusion k sweep, all
precomputed so the deployed app stays untouched. For the page, I removed
every reference to k from the beginner view and kept it only inside the
technical detail expander, reframed the conclusion from "ignore the
news" to "reacting to the news did not improve performance in our tests,
and it needs more evaluation," and added a Typical yearly growth column
so investors who care about raw return, not only risk adjusted return,
can see the effect too.

What the assistant produced: lexicon_comparison.csv, a finVADER based
sector_sentiment_index.csv, and fusion_ksweep_finvader.csv for the model
side. On the page, plain row labels (Ignore it, Follow a little, Follow
more, Follow heavily), a new return column pulled from the k sweep, a
softened heading and takeaway, and k confined to the technical expander.

What was wrong or risky: I predicted finVADER would score fewer
headlines as neutral. It actually scored more (about 61 percent versus
50 percent), because finance specific terms carry measured valences and
dampen VADER's everyday word positivity (mean 0.106 down to 0.069,
correlation only 0.60). I corrected my interpretation to match the
evidence and noted that "more accurate" cannot be claimed without
labelled data. On the writing, my first conclusion said "ignore the
news," which is too absolute and dismissive, and the table only showed
the Sharpe, which would let a return focused investor assume the return
might still be higher.

What I changed and why: I kept both sentiment models rather than
swapping silently, so the comparison table evidences the change, and I
confirmed the fusion tilt still declines under finVADER (0.749 down to
0.704), making the honest negative result robust across two sentiment
models. On the page, I reframed the message to be cautious and evidence
based rather than a blanket instruction, and I added the return column,
which showed the return also falls as the fund follows the news more
(13.8 percent down to 13.2 percent). Together this proves that neither
risk adjusted nor raw return improves, so no investor type benefits,
while keeping the language free of jargon and dash characters.

## 9 Agustus 2026 8.28 AM

What I wanted: A market mood index built on my finVADER scores,
following the Week 9 method, precomputed so the deployed app only reads
it.

Prompt(s): Reused the cached per headline finVADER compounds,
transformed each to a 0 to 100 scale, averaged per trading day, smoothed
with a 21 calendar day rolling mean, and z standardised the smoothed
index into Fear and Greed bands. Wrote fear_greed_index.csv and a per
sector version, and printed the latest reading.

What the assistant produced: fear_greed_index.csv (1006 rows, columns
date, fg_index, fg_roll, fg_z, label) and fear_greed_index_sector.csv.
All five bands fire across the sample. Latest reading 2023-12-29,
fg_index 53.1, label Extreme greed, z 4.25.

What was wrong or risky: The raw 0 to 100 index sits near 50 almost
every day, so a naive gauge reading of 53 would look neutral and
contradict the Extreme greed label. I confirmed the z standardised
version is the meaningful one, which is why the bands only make sense on
the z score, not the raw level. This shapes how the gauge must be drawn.

What I changed and why: Kept both the raw index and the z score in the
CSV so the gauge can show a friendly 0 to 100 face while the needle is
driven by the z based band, which keeps the needle and the label
consistent. Verified check_handin still passes and the app is untouched.

## 9 Aug 2026 8.54 AM

What I wanted: A market mood index built on my finVADER scores,
following the Week 9 method, precomputed and surfaced as one simple,
intuitive gauge that a first time investor can read at a glance, while
the technical method stays available for the report.

Prompt(s): First the data. I reused the cached per headline finVADER
compounds, scaled each to 0 to 100, averaged per trading day, smoothed
with a 21 calendar day rolling mean, and z standardised the smoothed
index into bands, writing fear_greed_index.csv and a per sector version.
Then the app. I added a semicircular gauge to the top of the Sentiment
page, driven by the z score, with the needle position clamped and mapped
so it always matches the band. Finally I relabelled the bands into plain
language, because "Greed" and "Fear" are insider terms a beginner does
not carry.

What the assistant produced: fear_greed_index.csv (1006 rows) and a
sector version, all five bands firing across the sample, and a gauge on
the Sentiment page reading "How positive is the news right now? Very
positive" for the last date, with plain zone labels from Very negative
to Very positive and a technical note naming it a Fear and Greed style
index.

What was wrong or risky: Two things. First, the raw 0 to 100 index sits
near 50 almost every day, so a needle at the raw value would look
neutral and contradict the band. I fixed this by driving the needle from
the z score, which measures greed or fear relative to its own normal, so
the needle and the word always agree. Second, the Fear and Greed wording
was not clear for a beginner, so I mapped the bands to plain positive
and negative language for the dial and kept the proper Fear and Greed
name only in the technical note and the report, which preserves the
innovation credit without confusing the user.

What I changed and why: Kept both the raw index and the z score in the
CSV so the gauge can be honest and consistent, and separated the
beginner facing labels from the technical name. Verified the gauge reads
correctly for December 2023, check_handin still passes, and the app only
reads the precomputed CSV so deployment stays safe.

## 9 Agustus 2026 9.12 AM

What I wanted: A benchmark for the funds, the risk free rate, so a
beginner can see whether each fund actually beat leaving the money in
cash. The brief allows downloading a risk free rate proxy, so I used the
Kenneth French daily rate.

Prompt(s): Downloaded the Kenneth French daily risk free rate using the
Week 5 approach, parsed it with the correct units, aligned it to the out
of sample window, built a growth of one dollar in cash series, and
computed each fund's annualised excess over cash. Precomputed everything
to results, kept the raw download out of the repo, and left the app and
the existing Sharpe numbers untouched.

What the assistant produced: risk_free_rate.csv, cash_benchmark.csv
aligned to the October 2020 to December 2023 window, and vs_cash.csv
with each fund's excess over cash. Cash returned about 1.96 percent a
year, and every fund beat it, from 3.6 percent above cash for Equity
Min-Variance to 80.8 percent above cash for Crypto Min-Variance.

What was wrong or risky: The French factors are in percent, so I
confirmed the conversion to a daily decimal was correct before
compounding, otherwise the cash line would be off by a factor of a
hundred. I also kept the headline Sharpe at a risk free rate of zero, my
stated choice, so the benchmark is added as a new honest layer rather
than silently changing the existing verified metrics. Verified the raw
zip was deleted and only derived artifacts remain.

What I changed and why: Added the risk free rate purely as an investment
benchmark, which is what my tutor asked for, and checked that the excess
over cash matches each fund's return minus the cash return. This gives
the app a plain "did it beat a savings account" comparison without
disturbing anything already built.

## 9 Agustus 2026 9.08 AM

Innovation, part 3b: showing the "vs cash" benchmark in the app

What I wanted: To surface the risk free rate benchmark in plain,
beginner friendly language on the fund fact sheet, and to make the
growth and drawdown charts match the green theme and explain themselves
at a glance.

Prompt(s): Added a cash line to the growth chart from the precomputed
cash benchmark, led with two number tiles (one dollar in the fund became
X, in cash it became Y) and a plain bar saying how much the fund beat
cash by. Recoloured the growth line green with the outperformance gap
shaded, and restyled the drawdown chart in coral with a percentage axis,
a worst drop tile, and a sentence translating the drop into dollars.
Then tidied the layout so both sections are symmetric, two tiles and a
one line bar and a chart, aligned in height.

What the assistant produced: A themed, self explanatory fact sheet where
the growth chart shows the fund beating the flat cash line, and the
drawdown section leads with the worst drop as a percentage and in
dollars. Reads only the precomputed benchmark and metrics files.

What was wrong or risky: The first pass was on theme but not intuitive,
the fund line was still Plotly blue and the comparison needed
interpreting, and after adding the tiles the two columns were lopsided
and the charts did not align. I fixed both by leading with plain
numbers, shading the gap so the outperformance is visible, and forcing
symmetric tile and bar heights so the layout is tidy.

What I changed and why: Kept the risk free rate as a benchmark only, so
the headline Sharpe is unchanged, and made the whole comparison readable
for a first time investor, in dollars and in plain language, while the
method stays documented for the report.

## 9 Agustus 2026 10.43 AM

What I wanted: The quiz was one tall stack of questions and options,
which wasted space and looked untidy. I wanted a cleaner grid where a
beginner also understands why each question is asked.

Prompt(s): Laid the four questions out as a two by two grid of bordered
cards, added one plain line under each question explaining what it is
for, added a reassuring "there are no wrong answers" line, and set every
card to the same fixed minimum height so the grid lines up even though
the crypto question has fewer options. Kept the scoring, the matching
rule, and the crypto guard unchanged.

What the assistant produced: A tidy two by two card grid on Find your
fund, each card showing the question, a short explanation, and the
options, with the See my match button below.

What was wrong or risky: After the first pass the bottom two cards were
uneven, because the crypto card had two options while the market drop
card had three, so I added a fixed minimum height to equalise them. I
also confirmed the layout change did not touch the scoring or the guard,
only the presentation.

What I changed and why: Turned a long form into a scannable grid and
explained each question in plain language, which helps the beginner
answer honestly, while keeping the underlying recommender logic exactly
the same.

## 9 Agustus 2026 11.23 AM

What I wanted: The fact sheet did not flow. The return appeared three
times, the worst drop twice, the section order jumped around, and the
holdings showed raw tickers and zero weight rows. I wanted a clean top
to bottom story where each number has one home.

Prompt(s): Reordered the page into header, at a glance, how your money
grew, the risk, recent performance, and what it holds. Removed the
duplicate return by dropping the since the start tile, removed the
duplicate worst drop tile from the drawdown section so it leads with the
dollar translation instead, kept only the 1 year and 3 year trailing
returns, and cleaned the holdings by stripping the EQ and CR prefixes
and dropping the 0.00 percent rows. Layout and copy only, no data
changes.

What the assistant produced: A fact sheet that reads as one narrative,
with each headline number appearing once, the drawdown section leading
with dollars, a non redundant recent performance row, and a tidy
holdings table with plain asset names.

What was wrong or risky: The risk here was accidentally changing a
metric while moving things around, so I confirmed the underlying numbers
were untouched and only the arrangement, the labels, and the holdings
display changed. I also checked the fund description line matches each
fund's family and method.

What I changed and why: Gave every number a single home and ordered the
page as what it is, the summary, how it grew, the risk, recent returns,
and what it holds, which removes the duplication and makes the fact
sheet read like a real product for a beginner.

## 9 Agustus 2026 12.02 PM

What I wanted: The management fee was hidden in small grey text in the
input column, which is poor disclosure practice. I wanted it clear and
prominent, up front, following the principle that fees should be shown
plainly, which also makes the app more realistic and professional.

Prompt(s): Moved the fee out of the buried caption and placed a clear
disclosure callout directly under the page subtitle at the top, stating
the 0.75 percent a year fee and that the projection is shown after the
fee, kept the dollar cost line near the results, kept the full
disclaimer at the bottom, and stated the fee only once so it is not
duplicated.

What the assistant produced: A visible fee disclosure at the top of the
Simulate page, with the projection already run net of the fee and the
total fee cost shown to the user.

What was wrong or risky: This is a prototype, not a licensed product, so
it does not have to meet any specific regulation, and I am not treating
it as legal compliance, only as good disclosure practice. The risk was
leaving the fee stated in two places, so I removed the duplicate and
kept one clear statement. I confirmed no numbers changed, only the
placement and prominence.

What I changed and why: Made the fee prominent and honest, since a
projection that quietly nets out a fee should also show the fee clearly,
which reflects real consumer disclosure norms and is a design choice I
can point to in the report.

## 9 Agustus 2026 12.25 PM

What I wanted: To keep the app calm for a beginner while still making
the innovation visible to a more experienced user and to markers,
following my tutor's suggestion of a view mode toggle. Progressive
disclosure, one product with two depths.

Prompt(s): Added a global For Beginner and For Advanced toggle under the
nav, stored in session state, defaulting to Beginner and remembered
across pages, plus a reusable Advanced badge. Wired it into the
Sentiment page first as the pattern: Beginner mode unchanged, Advanced
mode opens the technical panels with the badge, shows the raw unsmoothed
sentiment index, and adds the finVADER versus VADER comparison inline.

What the assistant produced: A working global toggle, an advanced badge
helper, and a Sentiment page that is byte for byte the same in Beginner
mode and reveals the k sweep, the lexicon comparison, and the raw index
in Advanced mode.

What was wrong or risky: The risk was cluttering the beginner view or
duplicating content. I confirmed Beginner mode is unchanged and that
Advanced only reveals material we already built, marked clearly with the
badge, nothing duplicated. No numbers changed.

What I changed and why: Surfaced the innovation on demand rather than
burying it, which serves the intermediate persona and makes the advanced
work visible in the live app, while protecting the beginner experience.

## 9 Agustus 2026 12.57 PM

What I wanted: The two genuinely new analytics for a dedicated Analytics
page, an efficient frontier and a fund correlation matrix, precomputed
so the app only reads them.

Prompt(s): Computed the long only mean variance efficient frontier over
the combined universe as thirty points, and the nine by nine correlation
matrix of the fund returns, wired both into the build, and printed the
ranges to check them.

What was wrong or risky: The first frontier used SLSQP with a fallback
to equal weights when the solver failed, and near the top of the
frontier it failed silently and returned a bogus volatility dip to
0.262, which would have looked like a real result. Switching to trust
constr with the same scaling converged for all thirty points into a
correct monotonic frontier. I only trusted the output after checking the
frontier rose monotonically and the correlation diagonal was all ones.

What I changed and why: Caught and fixed a silent solver failure that
produced a fake number, which is exactly why I verify optimiser output
rather than accepting it, and kept both outputs as precomputed derived
files so the app stays deploy safe.

## 9 Agustus 2026 1.13 PM

What I wanted: One visible home for the advanced work, aimed at an
intermediate investor, instead of scattered per page reveals.

Prompt(s): Added an Analytics page to the nav with the efficient
frontier and the nine funds on it, the full metrics table, a fund
correlation heatmap, and a sentiment deep dive holding the k sweep with
k, the finVADER versus VADER comparison, and the Fear and Greed method.
Moved the advanced sentiment material off the Sentiment page into here.

What the assistant produced: A working Analytics page gathering the
frontier, the metrics table, the correlation heatmap, and the sentiment
methods, with the beginner Sentiment page now simpler.

What was wrong or risky: The frontier is in sample while the funds are
out of sample, so I labelled it clearly that the funds sit inside the
frontier because the live period differs from the estimation period,
which keeps it honest rather than looking like an error. I also
confirmed the advanced material was moved, not duplicated, so the
beginner Sentiment page is genuinely simpler.

What I changed and why: Gave the innovation one prominent, discoverable
home that a marker cannot miss, while keeping the beginner pages calm,
which is a stronger and cleaner solution than the toggle.

## 9 Agustus 2026 1.43 PM

What I wanted: The Analytics page had strong depth but two clarity gaps:
the efficient frontier labels overlapped in the bottom left cluster, and
the metrics table and correlation heatmap were raw data with no
takeaway.

Prompt(s): Fanned the five overlapping frontier labels apart so all nine
are readable, and added a one line insight under the metrics table and
under the correlation heatmap, the heatmap line tying the low crypto to
equity correlation back to the diversification story.

What was wrong or risky: Only labels and captions changed, no data, so I
confirmed all nine funds are still present, no label overlaps a dot, and
the numbers are untouched.

What I changed and why: Turned raw analytics into interpreted ones and
made the frontier readable, so the advanced page is both deep and clear.

## 12 Aug 2026
## What I wanted
After my tutor feedback session, fix the first of two issues the tutor
raised: the Simulate page Monte Carlo chart reads as too optimistic. The
real cause is presentation, not the model. The median is a smoothed
aggregate across thousands of paths, so it always looks like a straight
climb, and the old chart buried the downside inside one shaded 10th-90th
band. I wanted a chart-only change (no change to the simulation model,
the horizon or contribution inputs, the fee treatment, or the summary
tiles) that makes the chance of losing money visible.

## Prompt(s)
"Fix the Simulate page Monte Carlo chart so it is not read as too
optimistic. Chart-and-caption change only, do not touch the model, the
inputs, the fee, or the tiles. From the same simulated value matrix the
tiles use, compute p10, p50, p90 and the contributed series. Plot exactly
four traces: Best case (1 in 10 better) = p90 #2E9E6B, Likely (middle) =
p50 #1F2A24, What you put in = contributed dashed #6B7A72, Worst case
(1 in 10 worse) = p10 #C9483F, with an optional faint 0.06 green fill
between p10 and p90. Remove the wide band, any sample paths, and any other
percentile lines. Under the chart add one honest line: 'In about {pct}%
of futures you end with less than the ${contributed_total} you put in',
pct = share of final-step values below the final contributed total. Keep
everything net of the fee. Verify worst/best equal the Pessimistic/
Optimistic tiles."

## What the assistant produced
- src/simulate.py: simulate_growth now also returns the n_sims x months
  wealth matrix alongside the unchanged p10/median/p90/contributions, so
  the chart derives its percentiles from the exact same paths as the
  tiles.
- streamlit_app.py sim_figure(): rewritten to plot the four traces from
  result["wealth"] via np.percentile([10,50,90]), the specified colours,
  a 0.06 fill, no band, no sample paths, no extra percentiles. Shared by
  both Simulate and Build allocation.
- Under the Simulate chart: "In about 11% of futures you end with less
  than the $13,000 you put in", computed from the share of final-step
  values below the final contributed total.
Verified: app boots (HTTP 200, no errors), the legend has exactly the four
labels, worst < contributed < best at the end, and worst/best line values
equal the Pessimistic/Optimistic tile values to the dollar.

## What was wrong or risky
Nothing needed correcting in the output. The risk I was watching: the
chart percentiles must be drawn from the same simulated paths as the
summary tiles, or the picture and the headline numbers could silently
disagree. Returning the wealth matrix from simulate_growth and driving
both the chart and the tiles from it removes that risk, and I confirmed
worst/best match the tiles to the dollar. One deliberate judgement call:
worst case is the 10th percentile (1 in 10) to stay consistent with the
existing Pessimistic tile, not the 5th. It is a one-line switch to
5th/95th if the tutor wants a more conservative floor.

## What I changed and why
This is presentation, not the model. The median stays smooth because that
is exactly what a per-step median of many paths is, so I did not fake
volatility into it. The honesty now comes from the worst-case line sitting
below what you put in for the later years, plus the plain-language chance
of ending underwater (11%). This directly answers the tutor's "too
optimistic" note. Report to-do: add a short paragraph explaining why the
median looks linear and how the downside is now shown.

## 12 Aug 2026 — sentiment z-score rescale
## What I wanted
Fix the second issue from my tutor session: the Sentiment page gauge read
"very positive" almost all the time. The cause is VADER's positive
baseline (about +0.11, not 0), so any raw positive score looks bullish and
every sector shows a green "Positive" dot. I wanted to rescale the raw
scores into z-scores against each sector's own normal, so the gauge and the
mood dots reflect whether the news is unusually positive, not just
positive. A scaling change only, with no change to the VADER scoring, the
news data, or the underlying sentiment series.

## Prompt(s)
"Fix the Sentiment page so it stops reading 'very positive' by default.
Rescale raw VADER into z-scores against each sector's own normal.
Standardise per sector z = (score - sector_mean) / sector_std on the full
sample, guard std == 0, and reuse the Fear and Greed helper if one exists.
Drive the gauge needle and headline from z with bands |z| < 0.5 About
normal, 0.5-1.5 a bit above/below normal, > 1.5 unusually positive/
negative, axis in standard deviations. Set the sector mood dot from the
same z bands, keep the raw score in its own column, and add a vs-normal (z)
column. Update the How this is built expander. Keep it deploy-safe by
computing the z-scores in the build step that writes the sentiment CSV.
Make the 0.5 and 1.5 thresholds named constants. Verify the gauge is no
longer pegged and a positive-but-below-average sector like Tech reads as
below normal."

## What the assistant produced
- src/sentiment.py: new zscore and standardise_sector_index helpers.
- scripts/run_part_b.py: the finVADER block now saves _z columns into
  results/data/sector_sentiment_index.csv.
- scripts/make_figures.py: fig5_sentiment_index filters out the _z columns
  so the time-series figure is unchanged.
- streamlit_app.py: band constants + sentiment_band(), the gauge rewritten
  (6 traces, -3s/0/+3s axis, needle from z), the sector mood table driven
  by z bands with the raw score kept and a vs-normal (z) column added, the
  How this is built expander and analytics text updated, and the old
  fear-and-greed gauge (fg_idx) removed.
- Regenerated results/data/sector_sentiment_index.csv with the z columns.
Verified: band boundaries exact (0.5/1.5 to the middle band, >1.5 or <-1.5
unusual, all assertions pass). Latest market z = +0.02 -> "About normal"
(no longer "Very positive"). Tech raw +0.061 but z -0.16 -> "About
normal"; Materials z -1.63 -> "Unusually negative"; Consumer z -1.02 ->
"A bit below normal". Gauge builds with 6 traces, needle at 50.3/100 for
z 0.02. No leftover references to the old gauge. Imports and data load OK,
app boots HTTP 200 with 0 errors, check_handin 21 checks passed (2 benign
warnings: __pycache__ and a not-yet-added report/report.pdf).

## What was wrong or risky
Nothing needed correcting in the output. The risk I was watching: the
standardisation must not touch the raw sentiment pipeline or the fig5
time-series, and the gauge and the table must read from one z definition
so they cannot disagree. Both hold - the z columns are additive in the
CSV, fig5 explicitly ignores them, and the gauge and mood dots share
sentiment_band(). The result is the honest one I expected: the current
reading drops from "very positive" to "about normal", and a sector like
Tech that is positive in raw terms but below its own normal now reads
neutral instead of green. Follow-up for handin: report/report.pdf still
needs to be in place before submission (the benign warning).

## What I changed and why
Kept it a pure rescaling. 0 now means the sector's own average and the
units are standard deviations, so the gauge answers "is the news unusually
positive right now" instead of "is the number positive", which removes
VADER's built-in optimism. This matches the "context, not a signal"
framing and makes the Sentiment page consistent with the Fear and Greed
standardisation. Report to-do: add a paragraph on the VADER positive
baseline and the z-score fix.

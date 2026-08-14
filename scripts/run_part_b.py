"""Reproduce your Part B results. Run from the project root:

    python scripts/run_part_b.py
"""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import nltk
import numpy as np
import pandas as pd

from src import etl
from src import features
from src import portfolios
from src import sentiment
from src import fusion
from src import fear_greed
from src import risk_free


def _sanity_check_weights(all_weights):
    """Print latest target weights for the new funds, verify the optimisers
    genuinely differ (a stalled solver silently returns equal weights) and
    eyeball crypto concentration."""
    print("\n" + "-" * 60)
    print("SANITY: LATEST TARGET WEIGHTS (new funds)")
    print("-" * 60)

    new_funds = ["Equity Min-Variance", "Equity Risk-Parity",
                 "Crypto Max-Sharpe", "Crypto Risk-Parity"]

    latest_by = {}
    for name in all_weights["fund"].unique():
        w = all_weights[all_weights["fund"] == name]
        latest_date = w["date"].max()
        latest = w[w["date"] == latest_date].set_index("asset")["weight"]
        latest_by[name] = latest

    for name in new_funds:
        latest = latest_by[name]
        top = latest[latest > 1e-4].sort_values(ascending=False)
        print(f"\n  {name}:")
        for asset, wt in top.items():
            print(f"      {asset:12s} {wt:7.1%}")
        zeros = (latest <= 1e-4).sum()
        print(f"    ({len(latest) - zeros} non-zero of {len(latest)} assets)")

    print("\n" + "-" * 60)
    print("SANITY: DO METHODS DIFFER? (max |w1 - w2| at latest rebalance)")
    print("-" * 60)
    universes = {
        "Equity": ["Equity Min-Variance", "Equity Risk-Parity",
                   "Equity Max-Sharpe"],
        "Crypto": ["Crypto Min-Variance", "Crypto Risk-Parity",
                   "Crypto Max-Sharpe"],
    }
    for universe, names in universes.items():
        print(f"\n  {universe}:")
        vectors = {n: latest_by[n] for n in names}
        all_assets = sorted(
            set().union(*[set(v.index) for v in vectors.values()]))
        df = pd.DataFrame({n: vectors[n].reindex(all_assets).fillna(0.0)
                           for n in names})
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                diff = (df[a] - df[b]).abs().max()
                flag = ("  <-- IDENTICAL: solver may have stalled"
                        if diff < 1e-9 else "")
                print(f"    max |{a:28s} - {b:28s}| = {diff:.4f}{flag}")

    print("\n" + "-" * 60)
    print("SANITY: CRYPTO MAX-SHARPE CONCENTRATION")
    print("-" * 60)
    ms = latest_by["Crypto Max-Sharpe"].sort_values(ascending=False)
    n_pos = (ms > 1e-4).sum()
    top2 = ms.head(2)
    hhi = (ms ** 2).sum()
    print(f"  Non-zero holdings: {n_pos} of {len(ms)}")
    print(f"  Largest:  {top2.iloc[0]:.1%} ({top2.index[0]})")
    print(f"  2nd:      {top2.iloc[1]:.1%} ({top2.index[1]})")
    print(f"  Top-2 share: {top2.sum():.1%}   HHI: {hhi:.3f}")
    if top2.sum() > 0.9:
        print("  WARNING: >90% in two coins - check for degeneracy.")
    else:
        print("  Not degenerate (top-2 <= 90%).")


def main():
    eq, cr, news = etl.load_all_datasets()
    combined = features.build_combined_panel(eq, cr)

    print("Downloading VADER lexicon (one-time build step)...")
    nltk.download("vader_lexicon", quiet=True)

    WINDOW = 252

    eq_returns = combined.filter(like="EQ_")
    cr_wide = features.compute_wide_returns(cr)

    # name: (returns panel, optimisation method, periods per year)
    # 252 for equity (5-day weeks), 365 for crypto (trades 7 days/week).
    fund_specs = [
        ("Combined Max-Sharpe", combined, "max_sharpe", 252),
        ("Combined Min-Variance", combined, "min_variance", 252),
        ("Combined Risk-Parity", combined, "risk_parity", 252),
        ("Equity Max-Sharpe", eq_returns, "max_sharpe", 252),
        ("Crypto Min-Variance", cr_wide, "min_variance", 365),
        ("Equity Min-Variance", eq_returns, "min_variance", 252),
        ("Equity Risk-Parity", eq_returns, "risk_parity", 252),
        ("Crypto Max-Sharpe", cr_wide, "max_sharpe", 365),
        ("Crypto Risk-Parity", cr_wide, "risk_parity", 365),
    ]

    print("\n" + "=" * 60)
    print("OUT-OF-SAMPLE BACKTEST")
    print("=" * 60)

    fund_returns = {}
    first_live_dates = {}
    all_weight_records = []
    metrics_rows = []

    for name, ret_df, method, ppy in fund_specs:
        print(f"\n  Running: {name} ({method}, {ppy} days/yr) ...")
        oos_ret, weights, growth, metrics = portfolios.oos_backtest(
            ret_df, method=method, window=WINDOW, periods_per_year=ppy,
        )
        fund_returns[name] = oos_ret
        first_live_dates[name] = weights["date"].iloc[0]
        w = weights.copy()
        w["fund"] = name
        all_weight_records.append(w)

        metrics["fund"] = name
        metrics_rows.append(metrics)

    print("\n" + "-" * 60)
    print("First live (out-of-sample) backtest dates:")
    for name, d in first_live_dates.items():
        print(f"  {name:30s}  {d.date()}")

    fund_rets_df = pd.DataFrame(fund_returns)
    fund_rets_df.index.name = "date"

    out_data = pathlib.Path("results/data")
    out_data.mkdir(parents=True, exist_ok=True)
    fund_rets_df.to_csv(out_data / "fund_returns.csv")

    all_weights = pd.concat(all_weight_records, ignore_index=True)
    all_weights.to_csv(out_data / "fund_weights.csv", index=False)

    metrics_df = pd.DataFrame(metrics_rows)
    metrics_df = metrics_df[["fund", "ann_return", "ann_vol", "sharpe",
                             "max_drawdown", "growth_of_1"]]
    out_tables = pathlib.Path("results/tables")
    out_tables.mkdir(parents=True, exist_ok=True)
    metrics_df.to_csv(out_tables / "performance_metrics.csv", index=False)

    print("\n" + "-" * 60)
    print("PERFORMANCE METRICS (annualised)")
    print("-" * 60)
    pd.set_option("display.float_format", "{:,.4f}".format)
    print(metrics_df.to_string(index=False))
    pd.reset_option("display.float_format")

    print(f"\n  Files written:")
    print(f"    {out_data / 'fund_returns.csv'}")
    print(f"    {out_data / 'fund_weights.csv'}")
    print(f"    {out_tables / 'performance_metrics.csv'}")

    print("\n" + "=" * 60)
    print("TRAILING RETURNS (annualised: last 1 year, last 3 years, since start)")
    print("=" * 60)

    ppy_by_fund = {name: ppy for name, _, _, ppy in fund_specs}
    fund_rets_csv = pd.read_csv(out_data / "fund_returns.csv",
                                index_col=0, parse_dates=True)
    trailing_rows = []
    for name in fund_rets_csv.columns:
        r = fund_rets_csv[name].dropna()
        ppy = ppy_by_fund[name]

        def _ann(series, n_days):
            return (1 + series).prod() ** (ppy / n_days) - 1

        trailing_rows.append({
            "fund": name,
            "ret_1y": _ann(r.tail(252), 252),
            "ret_3y": _ann(r.tail(756), 756),
            "ret_since_start": _ann(r, len(r)),
        })
    trailing_df = pd.DataFrame(trailing_rows)
    trailing_df.to_csv(out_tables / "trailing_returns.csv", index=False)

    pd.set_option("display.float_format", "{:,.4f}".format)
    print("\n  Annualised return over each trailing window:")
    print(trailing_df.to_string(index=False))
    pd.reset_option("display.float_format")
    print(f"\n  File written: {out_tables / 'trailing_returns.csv'}")

    print("\n" + "=" * 60)
    print("EFFICIENT FRONTIER (Combined panel, long only)")
    print("=" * 60)
    frontier = portfolios.efficient_frontier_points(
        combined, n_points=30, periods_per_year=252)
    frontier.to_csv(out_tables / "efficient_frontier.csv", index=False)
    print(f"\n  Frontier points: {len(frontier)}")
    print(f"  Annualised return range: {frontier['target_return'].min():.4%} "
          f"to {frontier['target_return'].max():.4%}")
    print(f"  Annualised volatility range: {frontier['vol'].min():.4%} "
          f"to {frontier['vol'].max():.4%}")
    print(f"\n  File written: {out_tables / 'efficient_frontier.csv'}")

    print("\n" + "=" * 60)
    print("FUND CORRELATION (daily returns, nine funds)")
    print("=" * 60)
    fund_rets_csv = pd.read_csv(out_data / "fund_returns.csv",
                                index_col=0, parse_dates=True)
    fund_corr = fund_rets_csv.corr()
    fund_corr.index.name = "fund"
    fund_corr.columns.name = "fund"
    fund_corr.to_csv(out_tables / "fund_correlation.csv")
    print(f"\n  Matrix shape: {fund_corr.shape[0]} x {fund_corr.shape[1]}")
    print(f"  Index equals columns: "
          f"{list(fund_corr.index) == list(fund_corr.columns)}")
    print(f"  Diagonal all ones: "
          f"{bool(np.allclose(np.diag(fund_corr.values), 1.0))}")
    print("\n  Head (first four funds):")
    print(fund_corr.iloc[:4, :4].to_string(
        float_format=lambda v: f"{v:.3f}"))
    print(f"\n  File written: {out_tables / 'fund_correlation.csv'}")

    print("\n" + "=" * 60)
    print("RISK FREE RATE AND CASH BENCHMARK (vs CASH)")
    print("=" * 60)

    rf = risk_free.download_risk_free()
    rf.to_csv(out_data / "risk_free_rate.csv", index=False)
    print(f"\n  Kenneth French daily risk free rate: {len(rf)} rows, "
          f"{rf['date'].iloc[0].date()} to {rf['date'].iloc[-1].date()}")
    print("  Raw download was written to a system temp path and deleted; "
          "it never enters the repo.")

    cash = risk_free.cash_benchmark(rf, fund_rets_df.index.min(),
                                    fund_rets_df.index.max())
    cash.to_csv(out_data / "cash_benchmark.csv", index=False)
    print(f"  Cash benchmark aligned to the out of sample window: "
          f"{len(cash)} rows, {cash['date'].iloc[0].date()} to "
          f"{cash['date'].iloc[-1].date()}")

    cash_ann = risk_free.annualised_cash_return(cash)
    vs_cash = metrics_df[["fund", "ann_return"]].copy()
    vs_cash["cash_ann_return"] = cash_ann
    vs_cash["excess_over_cash"] = vs_cash["ann_return"] - cash_ann
    vs_cash.to_csv(out_tables / "vs_cash.csv", index=False)

    print(f"\n  Cash annualised return: {cash_ann:.4%} "
          "(252 business days per year)")
    print("\n  Fund excess over cash (annualised return minus cash):")
    pd.set_option("display.float_format", "{:,.4f}".format)
    print(vs_cash.to_string(index=False))
    pd.reset_option("display.float_format")
    print(f"\n  Files written:")
    print(f"    {out_data / 'risk_free_rate.csv'}")
    print(f"    {out_data / 'cash_benchmark.csv'}")
    print(f"    {out_tables / 'vs_cash.csv'}")

    _sanity_check_weights(all_weights)

    print("\n" + "=" * 60)
    print("SECTOR SENTIMENT INDEX")
    print("=" * 60)
    # VADER index: baseline for the fusion comparison below. The saved CSV is
    # the finVADER version (see the lexicon-comparison block).
    sector_idx = sentiment.build_sector_sentiment_index(eq, news, scorer="vader")
    print(f"\n  VADER index  shape: {sector_idx.shape[0]} dates x {sector_idx.shape[1]} sectors")
    print(f"  Date range: {sector_idx.index[0].date()} to {sector_idx.index[-1].date()}")

    print("\n" + "=" * 60)
    print("LEXICON COMPARISON (VADER vs finVADER)")
    print("=" * 60)
    vader_scored = sentiment.score_headlines(eq, news, scorer="vader")
    finvader_scored = sentiment.score_headlines(eq, news, scorer="finvader")
    print(f"\n  Headlines scored: {len(vader_scored)} ({len(vader_scored['title'].unique())} unique titles)")

    NEUTRAL_THRESHOLD = 0.05
    vader_c = vader_scored["compound"]
    finvader_c = finvader_scored["compound"]
    pearson_r = vader_c.corr(finvader_c)
    lex_rows = [
        {
            "model": "VADER",
            "mean_compound": vader_c.mean(),
            "share_near_zero": (vader_c.abs() < NEUTRAL_THRESHOLD).mean(),
            "corr_with_vader": 1.0,
        },
        {
            "model": "finVADER",
            "mean_compound": finvader_c.mean(),
            "share_near_zero": (finvader_c.abs() < NEUTRAL_THRESHOLD).mean(),
            "corr_with_vader": pearson_r,
        },
    ]
    lex_cmp = pd.DataFrame(lex_rows)
    lex_cmp.to_csv(out_tables / "lexicon_comparison.csv", index=False)
    pd.set_option("display.float_format", "{:,.4f}".format)
    print(f"\n  Neutral threshold: |compound| < {NEUTRAL_THRESHOLD}")
    print(lex_cmp.to_string(index=False))
    pd.reset_option("display.float_format")
    print(f"\n  File written: {out_tables / 'lexicon_comparison.csv'}")

    print("\n" + "=" * 60)
    print("finVADER SECTOR SENTIMENT INDEX")
    print("=" * 60)
    # Overwrite the app-read CSV with the finVADER-based index (same
    # construction, richer finance lexicon). The app is untouched - it only
    # reads results/data/sector_sentiment_index.csv.
    sector_idx_finvader = sentiment.build_sector_sentiment_index(
        eq, news, scorer="finvader")
    # Append per-sector z-scores ("vs its own normal") as '<sector>_z'
    # columns so the app can show whether the news is unusually positive,
    # not just positive. The raw sector_idx_finvader above stays unchanged
    # for the fusion tilt, which uses the raw compound scores.
    sector_idx_saved = sentiment.standardise_sector_index(sector_idx_finvader)
    sector_idx_saved.to_csv(out_data / "sector_sentiment_index.csv")
    print(f"\n  finVADER index  shape: {sector_idx_saved.shape[0]} dates x {sector_idx_saved.shape[1]} sectors")
    print(f"  Date range: {sector_idx_finvader.index[0].date()} to {sector_idx_finvader.index[-1].date()}")
    pd.set_option("display.float_format", "{:,.4f}".format)
    print("\n  Last 5 rows (all sectors, raw + z vs own normal):")
    print(sector_idx_saved.tail(5).to_string())
    pd.reset_option("display.float_format")
    print(f"\n  File written: {out_data / 'sector_sentiment_index.csv'} (finVADER + '_z' columns)")

    print("\n" + "=" * 60)
    print("FEAR AND GREED INDEX (finVADER headlines, Week 9 method)")
    print("=" * 60)
    fg = fear_greed.build_fear_greed_index(eq, news)
    fg.to_csv(out_data / "fear_greed_index.csv", index=False)

    fg_sector = fear_greed.build_fear_greed_sector_index(eq, news)
    fg_sector.to_csv(out_data / "fear_greed_index_sector.csv", index=False)

    last = fg.dropna(subset=["label"]).iloc[-1]
    print(f"\n  Current reading ({last['date'].date()}):")
    print(f"    fg_index = {last['fg_index']:.1f}  (0 = most fearful, 100 = most greedy)")
    print(f"    label    = {last['label']}")
    print(f"\n  Files written:")
    print(f"    {out_data / 'fear_greed_index.csv'}")
    print(f"    {out_data / 'fear_greed_index_sector.csv'}")

    print("\n" + "=" * 60)
    print("SENTIMENT FUSION (Equity Max-Sharpe + Sector Sentiment Tilt)")
    print("=" * 60)
    sector_map = dict(zip(eq["ticker"], eq["sector"]))
    sent_lagged = sentiment.lag_sentiment(sector_idx, n_lag=1)

    eq_returns = combined.filter(like="EQ_")
    tilt_ret, tilt_weights, tilt_growth, tilt_metrics = fusion.fusion_oos_backtest(
        eq_returns, sent_lagged, sector_map,
        method="max_sharpe", window=WINDOW, k=0.5,
    )

    base_name = "Equity Max-Sharpe"
    tilted_name = "Equity Max-Sharpe + Sentiment Tilt"
    comp = fusion.base_vs_tilted_table(
        fund_returns[base_name], tilt_ret,
        base_name=base_name, tilted_name=tilted_name,
    )
    comp.to_csv(out_tables / "fusion_comparison.csv", index=False)

    pd.set_option("display.float_format", "{:,.4f}".format)
    print("\n  Before vs After:")
    print(comp[["fund", "ann_return", "ann_vol", "sharpe", "max_drawdown", "growth_of_1"]].to_string(index=False))
    pd.reset_option("display.float_format")
    print(f"\n  File written: {out_tables / 'fusion_comparison.csv'}")

    print("\n" + "-" * 60)
    print("k SENSITIVITY SWEEP")
    print("-" * 60)
    ks = [0.0, 0.25, 0.5, 1.0, 2.0]
    sweep_rows = []
    for k in ks:
        print(f"  k = {k:.2f} ...")
        ret, _, _, met = fusion.fusion_oos_backtest(
            eq_returns, sent_lagged, sector_map,
            method="max_sharpe", window=WINDOW, k=k,
        )
        sweep_rows.append({
            "k": k,
            "ann_return": met["ann_return"],
            "ann_vol": met["ann_vol"],
            "sharpe": met["sharpe"],
            "max_drawdown": met["max_drawdown"],
        })
    sweep = pd.DataFrame(sweep_rows)
    sweep.to_csv(out_tables / "fusion_ksweep.csv", index=False)
    print()
    pd.set_option("display.float_format", "{:,.4f}".format)
    print(sweep.to_string(index=False))
    pd.reset_option("display.float_format")

    print("\n" + "-" * 60)
    print("k SENSITIVITY SWEEP ON finVADER SENTIMENT")
    print("-" * 60)
    sent_lagged_finvader = sentiment.lag_sentiment(sector_idx_finvader, n_lag=1)
    sweep_finvader_rows = []
    for k in ks:
        print(f"  k = {k:.2f} ...")
        ret, _, _, met = fusion.fusion_oos_backtest(
            eq_returns, sent_lagged_finvader, sector_map,
            method="max_sharpe", window=WINDOW, k=k,
        )
        sweep_finvader_rows.append({
            "k": k,
            "ann_return": met["ann_return"],
            "ann_vol": met["ann_vol"],
            "sharpe": met["sharpe"],
            "max_drawdown": met["max_drawdown"],
        })
    sweep_finvader = pd.DataFrame(sweep_finvader_rows)
    sweep_finvader.to_csv(out_tables / "fusion_ksweep_finvader.csv", index=False)
    print()
    pd.set_option("display.float_format", "{:,.4f}".format)
    print(sweep_finvader.to_string(index=False))
    pd.reset_option("display.float_format")
    print(f"\n  File written: {out_tables / 'fusion_ksweep_finvader.csv'}")

    print("\n" + "=" * 60)
    print("FINAL PERFORMANCE METRICS (annualised)")
    print("=" * 60)
    pd.set_option("display.float_format", "{:,.4f}".format)
    print(metrics_df.to_string(index=False))
    pd.reset_option("display.float_format")

    print("\nDone.")


if __name__ == "__main__":
    main()

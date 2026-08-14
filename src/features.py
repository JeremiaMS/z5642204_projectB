"""Station 2 - Feature engineering: returns, text panel, and combined panel.

Compute returns within each asset panel first, then left-merge crypto
returns onto the equity trading calendar. Never merge price levels.
"""
import pathlib

import numpy as np
import pandas as pd


def compute_returns(df):
    """Compute daily simple returns (pct_change) per ticker on adjClose.

    Parameters
    ----------
    df : DataFrame  with columns [ticker, date, adjClose].

    Returns
    -------
    DataFrame  with columns [ticker, date, return] (NaN for first row
    of each ticker).
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
    df = df.sort_values(["ticker", "date"])
    df["return"] = df.groupby("ticker")["adjClose"].pct_change()
    return df[["ticker", "date", "return"]]


def compute_wide_returns(df):
    """Compute returns and pivot to wide (dates as index, tickers as columns)."""
    rl = compute_returns(df)
    wide = rl.pivot_table(index="date", columns="ticker", values="return", dropna=False)
    wide.index = pd.to_datetime(wide.index).tz_localize(None)
    wide.columns.name = None
    return wide


def build_combined_panel(eq, cr):
    """Build the combined equity+crypto returns panel.

    Steps
    -----
    1. Compute daily returns within each panel (long format).
    2. Pivot each to wide (date x ticker).
    3. Drop the first equity date (all-NaN returns, no prior close).
    4. Left-merge crypto returns onto equity dates.

    Parameters
    ----------
    eq, cr : clean DataFrames (equity_prices, crypto_prices).

    Returns
    -------
    combined : DataFrame  with equity dates as index and columns
        EQ_<ticker> for equities, CR_<ticker> for crypto.
    """
    print("Computing returns within each panel...")

    eq_wide = compute_wide_returns(eq)
    cr_wide = compute_wide_returns(cr)

    n_dates_pre = len(eq_wide)
    first_date = eq_wide.index[0]
    assert eq_wide.loc[first_date].isna().all(), "Expected first equity date to be all-NaN"
    eq_wide = eq_wide.iloc[1:]
    n_dates_post = len(eq_wide)
    print(f"  Equity returns: {n_dates_pre} dates -> dropped {first_date.date()} -> {n_dates_post} dates")

    eq_wide.columns = [f"EQ_{c}" for c in eq_wide.columns]
    cr_wide.columns = [f"CR_{c}" for c in cr_wide.columns]

    combined = eq_wide.merge(cr_wide, left_index=True, right_index=True, how="left")
    print(f"  Combined panel: {combined.shape[0]} dates x {combined.shape[1]} assets")

    eq_dates = set(eq_wide.index)
    cr_dates = set(cr_wide.index)
    crypto_excluded_dates = sorted(cr_dates - eq_dates)
    n_coins = len([c for c in cr_wide.columns if c.startswith("CR_")])
    excluded_date_count = len(crypto_excluded_dates)
    cr_excluded = cr_wide.loc[crypto_excluded_dates]
    excluded_return_rows = int(cr_excluded.notna().sum().sum())
    excluded_rows_total = excluded_date_count * n_coins
    print(f"\nVerification:")
    btc_long = compute_returns(cr)
    btc_before = len(btc_long[btc_long["ticker"] == "BTC-USD"].dropna(subset=["return"]))
    print(f"  BTC-USD return rows before merge:                     {btc_before}")
    btc_combined_col = [c for c in combined.columns if "BTC" in c]
    if btc_combined_col:
        btc_after = combined[btc_combined_col[0]].notna().sum()
        print(f"  BTC-USD return rows after merge:                      {btc_after}")
    print(f"  Excluded non-trading day return rows (valid only):     {excluded_return_rows}  ({excluded_return_rows // n_coins} per coin = {btc_before} pre - {btc_after} post)")
    print(f"  Excluded non-trading day dates total (incl. NaN day):  {excluded_rows_total}  ({excluded_date_count} per coin, includes 2020-01-01 with no return)")
    print(f"  Combined panel date count:                             {len(combined)}")
    print()

    return combined


def build_equity_news_panel(eq, news):
    """Map headlines to equity trading days and join counts onto returns.

    Steps
    -----
    1. Normalise news dates to naive datetime64[ns].
    2. Map each headline to its equity trading day (same day if trading,
       otherwise the NEXT trading day). Headlines after the final trading
       day (2023-12-29) map back to it.
    3. Count headlines per (ticker, trading_date).
    4. Left-join onto equity returns on (ticker, date) - every ticker-day
       survives. Ticker-days with no headlines get count = 0.

    Parameters
    ----------
    eq  : clean equity_prices DataFrame.
    news : clean (deduplicated) news DataFrame.

    Returns
    -------
    DataFrame  with columns [ticker, date, return, headline_count].
    """
    print("Assembling daily text panel and joining onto equity returns...")

    news = news.copy()
    news["date"] = pd.to_datetime(news["date"]).dt.tz_localize(None).astype("datetime64[ns]")

    trading_dates = sorted(eq["date"].unique())
    final_trading_date = trading_dates[-1]
    cal = pd.DataFrame({"trading_date": trading_dates})
    cal["trading_date"] = cal["trading_date"].astype("datetime64[ns]")

    news_sorted = news.sort_values("date")
    mapped = pd.merge_asof(
        news_sorted,
        cal,
        left_on="date",
        right_on="trading_date",
        direction="forward",
    )

    orphan_mask = mapped["trading_date"].isna()
    n_orphans = orphan_mask.sum()
    mapped.loc[orphan_mask, "trading_date"] = final_trading_date
    print(f"  Orphan headlines after final trading day ({final_trading_date.date()}): {n_orphans}  (expected 6)")

    counts = mapped.groupby(["ticker", "trading_date"], as_index=False).size()
    counts = counts.rename(columns={"size": "headline_count", "trading_date": "date"})
    counts["date"] = counts["date"].astype("datetime64[ns]")

    non_orphan_counts = mapped[~orphan_mask].groupby(
        ["ticker", "trading_date"], as_index=False
    ).size().rename(columns={"size": "cnt_no_orphan"})
    orphan_info = mapped[orphan_mask][["ticker", "trading_date"]].drop_duplicates()
    flipped = 0
    for _, r in orphan_info.iterrows():
        key = (r["ticker"], r["trading_date"])
        match = non_orphan_counts[
            (non_orphan_counts["ticker"] == r["ticker"])
            & (non_orphan_counts["trading_date"] == r["trading_date"])
        ]
        if len(match) == 0:
            flipped += 1
    print(f"    of which {flipped} flipped a otherwise-quiet ticker-day into a news day")

    eq_ret = compute_returns(eq).dropna(subset=["return"])

    joined = eq_ret.merge(counts, on=["ticker", "date"], how="left")
    joined["headline_count"] = joined["headline_count"].fillna(0).astype(int)

    total_headlines = int(joined["headline_count"].sum())
    expected_total = len(news)
    gap = expected_total - total_headlines
    dropped_first_date = cal["trading_date"].min()
    dropped_count = len(mapped[mapped["trading_date"] == dropped_first_date])

    print(f"\n  Text panel verification:")
    print(f"  a) Rows after join: {len(joined)}  (expected 50250 = 50 x 1005)")
    zero = (joined["headline_count"] == 0).sum()
    one_plus = (joined["headline_count"] >= 1).sum()
    print(f"  b) Ticker-days: {zero} with 0 headlines, {one_plus} with >= 1")
    top5 = joined.nlargest(5, "headline_count")
    print(f"  c) Top 5 ticker-days by headline count:")
    for _, r in top5.iterrows():
        print(f"       {r['ticker']:6s}  {r['date'].date()}  {int(r['headline_count'])} headlines")
    print(f"  d) Sum of all headline counts: {total_headlines}  (expected {expected_total})")
    if gap > 0:
        print(f"     Gap: {gap} headlines not counted")
        print(f"      -> all map to {dropped_first_date.date()} (first trading day, dropped from")
        print(f"         returns panel because no prior close; {dropped_count} total headlines on that date)")
    print()

    return joined

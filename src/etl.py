"""Station 1 - your ETL: load and clean the data.

Load raw data through src.data_access (see context/DATA_GUIDE.md). Add your own
integrity checks. Do not commit data files.
"""
import numpy as np
import pandas as pd

from src import data_access


def load_clean_equities():
    """Load equity prices and run Station 1 integrity checks.

    Returns clean frame. Prints shape, date range, duplicate count.
    """
    df = data_access.load_equity_prices()
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)

    print(f"Equity prices loaded: {df.shape[0]} rows, {df['ticker'].nunique()} tickers")
    print(f"  Date range: {df['date'].min()} to {df['date'].max()}")

    dup_mask = df.duplicated(subset=["ticker", "date"], keep=False)
    dup_count = dup_mask.sum()
    print(f"  Duplicates (ticker+date): {dup_count} rows")
    if dup_count > 0:
        df = df.drop_duplicates(subset=["ticker", "date"], keep="first")
        print(f"    -> after dedupe: {df.shape[0]} rows")

    print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"  Unique tickers: {df['ticker'].nunique()}")
    print(f"  Sectors: {df['sector'].nunique()}")

    return df


def load_clean_crypto():
    """Load crypto prices, cap at 2023-12-31 (10 stray 2024 rows).

    Returns clean frame with duplicates removed and date-capped.
    """
    df = data_access.load_crypto_prices()
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)

    pre = df.shape[0]
    print(f"Crypto prices loaded: {pre} rows, {df['ticker'].nunique()} coins")
    cutoff = pd.Timestamp("2023-12-31")
    df = df[df["date"] <= cutoff].copy()
    removed = pre - df.shape[0]
    if removed:
        print(f"  Capped at {cutoff.date()}, removed {removed} rows (post-cap: {df.shape[0]} rows)")

    print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"  Unique coins: {df['ticker'].nunique()}")

    dup_mask = df.duplicated(subset=["ticker", "date"], keep=False)
    dup_count = dup_mask.sum()
    print(f"  Duplicates (ticker+date): {dup_count} rows")
    if dup_count > 0:
        df = df.drop_duplicates(subset=["ticker", "date"], keep="first")
        print(f"    -> after dedupe: {df.shape[0]} rows")

    return df


def load_clean_news():
    """Load news headlines and dedupe on ticker+date+title.

    Returns clean frame. Reports counts before and after dedupe.
    """
    df = data_access.load_news_headlines()
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)

    pre = df.shape[0]
    print(f"News headlines loaded: {pre} rows")
    print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"  Unique tickers: {df['ticker'].nunique()}")

    # Build a temporary normalised matching key (case+whitespace) for
    # dedup COMPARISON only; the stored title stays raw and unmodified.
    df["_norm_title"] = df["title"].str.lower().str.strip()
    dup_mask = df.duplicated(subset=["ticker", "date", "_norm_title"], keep=False)
    dup_count = dup_mask.sum()
    print(f"  Duplicates (ticker+date+normalised_title): {dup_count} rows")
    if dup_count > 0:
        n_unique = df["_norm_title"].nunique()
        df = df.drop_duplicates(subset=["ticker", "date", "_norm_title"], keep="first")
        print(f"    -> after dedupe: {df.shape[0]} rows (removed {pre - df.shape[0]})")
        print(f"    -> unique normalised titles across all tickers: {n_unique}")
    df = df.drop(columns=["_norm_title"])

    print(f"  Ticker-date combos with at least one headline: {df[['ticker', 'date']].drop_duplicates().shape[0]}")

    return df


def load_all_datasets():
    """Load and clean all three datasets. Returns (equities, crypto, news)."""
    print("=" * 60)
    print("DATA LOADING AND CLEANING REPORT")
    print("=" * 60)
    print()
    print("--- EQUITY PRICES ---")
    eq = load_clean_equities()
    print()
    print("--- CRYPTO PRICES ---")
    cr = load_clean_crypto()
    print()
    print("--- NEWS HEADLINES ---")
    news = load_clean_news()
    print()
    print("=" * 60)
    return eq, cr, news


# ── Integrity-check helpers (used by make_integrity_summary) ──


def missing_date_audit(eq):
    """Compare each ticker's trading dates against the full equity calendar.

    Returns a DataFrame with columns [ticker, missing_dates_count,
    missing_dates_str] for any ticker with gaps.
    """
    full_calendar = sorted(eq["date"].unique())
    ticker_dates = eq.groupby("ticker")["date"].apply(set)
    gaps = []
    for ticker in sorted(ticker_dates.index):
        missing = sorted(set(full_calendar) - ticker_dates[ticker])
        if missing:
            gaps.append({
                "ticker": ticker,
                "missing_dates_count": len(missing),
                "missing_dates_str": str(missing[:5])[1:-1] + ("..." if len(missing) > 5 else ""),
            })
    return pd.DataFrame(gaps)


def find_outliers(eq, threshold=0.15):
    """Flag daily returns with |return| > threshold within each ticker.

    Returns DataFrame of flagged rows: ticker, date, daily_return.
    Also returns the top 5 largest absolute moves as a DataFrame.
    """
    df = eq.copy()
    df = df.sort_values(["ticker", "date"])
    df["daily_return"] = df.groupby("ticker")["adjClose"].pct_change()
    flagged = df[df["daily_return"].abs() > threshold].dropna(subset=["daily_return"]).copy()
    flagged = flagged[["ticker", "date", "daily_return"]].sort_values("daily_return", key=abs, ascending=False)
    top5 = flagged.head(5).copy()
    return flagged, top5


def make_dataset_inventory(eq, cr, news):
    """Build the dataset inventory table.

    Returns DataFrame with columns: dataset, rows, date_start, date_end,
    frequency, coverage. Saves to results/tables/dataset_inventory.csv.
    """
    eq_days = eq["date"].nunique()
    cr_days = cr["date"].nunique()
    news_td = news[["ticker", "date"]].drop_duplicates().shape[0]

    inventory = pd.DataFrame([
        {
            "dataset": "equity_prices",
            "rows": len(eq),
            "date_start": eq["date"].min(),
            "date_end": eq["date"].max(),
            "frequency": "daily (trading, ~252 days/year)",
            "coverage": "50 tickers / 10 sectors",
        },
        {
            "dataset": "crypto_prices",
            "rows": len(cr),
            "date_start": cr["date"].min(),
            "date_end": cr["date"].max(),
            "frequency": "daily (calendar, ~365 days/year)",
            "coverage": "10 tickers",
        },
        {
            "dataset": "news_headlines",
            "rows": len(news),
            "date_start": news["date"].min(),
            "date_end": news["date"].max(),
            "frequency": "irregular",
            "coverage": "50 tickers, deduplicated",
        },
    ])
    return inventory


def make_integrity_summary(eq, cr, news):
    """Build the data-integrity summary table.

    Returns DataFrame with columns: check_name, issue_count, resolution.
    Loads raw data for duplicate counts that need pre-cleaning values.
    Saves to results/tables/data_integrity_summary.csv.
    """
    # Load raw for pre-cleaning counts
    raw_eq = data_access.load_equity_prices()
    raw_cr = data_access.load_crypto_prices()
    raw_news = data_access.load_news_headlines()

    # Duplicate counts
    eq_dup_raw = int(raw_eq.duplicated(subset=["ticker", "date"], keep=False).sum())
    cr_dup_raw = int(raw_cr.duplicated(subset=["ticker", "date"], keep=False).sum())
    news_dup_count = int(
        raw_news.assign(_norm=raw_news["title"].str.lower().str.strip())
        .duplicated(subset=["ticker", "date", "_norm"], keep="first").sum()
    )

    # Crypto cap
    raw_cr_pre = len(raw_cr)
    raw_cr_capped = len(raw_cr[raw_cr["date"] <= pd.Timestamp("2023-12-31")])
    crypto_removed = raw_cr_pre - raw_cr_capped

    # Missing-date audit on clean equity
    gaps_df = missing_date_audit(eq)
    n_tickers_with_gaps = len(gaps_df)
    total_missing_dates = int(gaps_df["missing_dates_count"].sum()) if n_tickers_with_gaps > 0 else 0

    # Outlier screen - equity
    flagged, top5 = find_outliers(eq)
    n_outliers = len(flagged)

    # Top-5 detail for resolution column
    outlier_detail = "; ".join(
        f"{r['ticker']} on {r['date'].date()}: {r['daily_return']:.4f}"
        for _, r in top5.iterrows()
    )

    # Outlier screen - crypto (same logic, within-panel)
    cr_flagged, cr_top5 = find_outliers(cr)
    n_cr_outliers = len(cr_flagged)

    cr_outlier_detail = "; ".join(
        f"{r['ticker']} on {r['date'].date()}: {r['daily_return']:.4f}"
        for _, r in cr_top5.iterrows()
    )

    rows = [
        {
            "check_name": "Duplicate check - equity (key: ticker+date)",
            "issue_count": str(eq_dup_raw),
            "resolution": "No duplicates found",
        },
        {
            "check_name": "Duplicate check - crypto (key: ticker+date)",
            "issue_count": str(cr_dup_raw),
            "resolution": "No duplicates found",
        },
        {
            "check_name": "Duplicate check - news (key: ticker+date+title)",
            "issue_count": str(news_dup_count),
            "resolution": f"{news_dup_count} exact duplicate rows removed (keep='first')",
        },
        {
            "check_name": "Crypto date cap (2023-12-31)",
            "issue_count": str(crypto_removed),
            "resolution": f"{crypto_removed} rows dated after 2023-12-31 removed; {raw_cr_capped} rows retained",
        },
        {
            "check_name": "Missing-date audit - equity",
            "issue_count": str(total_missing_dates),
            "resolution": (
                f"{n_tickers_with_gaps} ticker(s) with gaps across the equity trading calendar; "
                "kept as-is (may reflect IPO, delisting, or trading halt)"
            ),
        },
        {
            "check_name": f"Outlier screen - daily return >|{15}%|",
            "issue_count": str(n_outliers),
            "resolution": (
                f"{n_outliers} trading-day returns flagged; all kept as genuine historical events. "
                f"Top 5: {outlier_detail}"
            ),
        },
        {
            "check_name": f"Outlier screen - crypto daily return >|{15}%|",
            "issue_count": str(n_cr_outliers),
            "resolution": (
                f"{n_cr_outliers} trading-day returns flagged; all kept as genuine historical events. "
                f"Top 5: {cr_outlier_detail}"
            ),
        },
    ]
    return pd.DataFrame(rows)

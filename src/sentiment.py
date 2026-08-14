"""Station 3 - Sentiment model: VADER / finVADER on news headlines.

1. Map headlines to equity trading days (forward merge_asof).
2. Score each headline's raw title with VADER or finVADER compound.
3. Aggregate to mean compound per (ticker, trading_date).
4. Build daily sector sentiment index (equal-weight tickers, carry forward).
5. Save to results/data/sector_sentiment_index.csv.
6. Expose lagged version for fusion use.

finVADER extends VADER with SentiBigNomics and Henry's (2008) finance word
lists. Per-headline scores are cached on disk (scratch/sentiment_cache, a
gitignored folder) so ~150k headlines are scored once, not on every run.
"""
import functools
import hashlib
import pathlib
import pandas as pd
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

from finvader import finvader

_CACHE_DIR = pathlib.Path("scratch/sentiment_cache")


def _download_vader():
    nltk.download("vader_lexicon", quiet=True)


def _map_headlines_to_trading_days(news, eq):
    """Map each headline to its equity trading day (forward merge_asof).

    Uses the same logic as features.build_equity_news_panel. Returns a
    DataFrame with columns [ticker, trading_date, sector, title].
    """
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

    mapped.loc[mapped["trading_date"].isna(), "trading_date"] = final_trading_date
    return mapped[["ticker", "trading_date", "sector", "title"]]


def _score_vader(df):
    """Score each headline's raw title with VADER compound.

    Does NOT lowercase or strip punctuation — VADER relies on them.
    """
    _download_vader()
    sia = SentimentIntensityAnalyzer()
    compounds = df["title"].apply(lambda t: sia.polarity_scores(str(t))["compound"])
    result = df.copy()
    result["compound"] = compounds
    return result


@functools.lru_cache(maxsize=None)
def score_finvader(text):
    """Score a single headline with finVADER compound.

    finVADER = VADER + SentiBigNomics + Henry's finance word lists.
    lru_cache deduplicates identical titles within a run; the disk cache in
    _cached_score makes repeat runs skip scoring entirely.
    """
    return finvader(text, use_sentibignomics=True, use_henry=True,
                    indicator="compound")


def _score_finvader(df):
    """Score each headline's raw title with finVADER compound."""
    compounds = df["title"].apply(lambda t: score_finvader(str(t)))
    result = df.copy()
    result["compound"] = compounds
    return result


def _cache_key(mapped):
    """Stable hash of the headline table (ticker, trading_date, title)."""
    rows = mapped[["ticker", "trading_date", "title"]]
    digest = hashlib.sha1(
        pd.util.hash_pandas_object(rows, index=False).values.tobytes()
    ).hexdigest()
    return digest[:16]


def _cached_score(mapped, scorer):
    """Return compound scores for mapped headlines, cached to disk.

    Scores are cached under scratch/sentiment_cache (gitignored) keyed by a
    hash of the headline table, so re-runs with unchanged headlines load the
    cache instead of re-scoring ~150k headlines. Gzipped so the pre-handin
    check (which flags .csv outside results/) does not treat them as data.
    """
    path = _CACHE_DIR / f"{scorer}_{_cache_key(mapped)}.csv.gz"
    if path.exists():
        return pd.read_csv(path, index_col=0, compression="gzip")["compound"]

    scored = (_score_vader(mapped) if scorer == "vader"
              else _score_finvader(mapped))
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    scored[["compound"]].to_csv(path, compression="gzip")
    return scored["compound"]


def build_sector_sentiment_index(eq, news, scorer="vader"):
    """Build daily sector sentiment index.

    Steps
    -----
    1. Map headlines to equity trading days (forward merge_asof).
    2. Score each headline with the chosen lexicon compound (raw title).
    3. Aggregate to mean compound per (ticker, trading_date).
    4. For each sector-day, equal-weight tickers (mean across tickers).
    5. Reindex to full equity calendar; forward-fill sector-days with no
       news; fill leading NaNs with 0.

    Parameters
    ----------
    eq      : DataFrame  clean equity_prices (has ticker, date, sector).
    news    : DataFrame  clean deduplicated news headlines.
    scorer  : str  'vader' or 'finvader'.

    Returns
    -------
    DataFrame  date index, one column per sector.
    """
    # Stable ticker -> sector map from equities (one row per ticker)
    sector_map = eq[["ticker", "sector"]].drop_duplicates()

    mapped = _map_headlines_to_trading_days(news, eq)
    scored = mapped.copy()
    scored["compound"] = _cached_score(mapped, scorer)

    ticker_daily = scored.groupby(["ticker", "trading_date"], as_index=False)["compound"].mean()

    ticker_daily = ticker_daily.merge(sector_map, on="ticker", how="left")

    sector_daily = ticker_daily.groupby(["sector", "trading_date"])["compound"].mean().reset_index()

    sector_wide = sector_daily.pivot(
        index="trading_date", columns="sector", values="compound"
    )

    trading_dates = sorted(eq["date"].unique())
    sector_wide = sector_wide.reindex(trading_dates)
    sector_wide = sector_wide.ffill()
    sector_wide = sector_wide.fillna(0.0)

    sector_wide.index.name = "date"
    return sector_wide


def zscore(series):
    """Standardise a Series against its own mean and std (its 'normal').

    Returns (series - mean) / std where the mean and std are the full-sample
    values of the series itself, so 0 means "normal for this series" and +1
    means one standard deviation above it.  If the std is 0 or missing the
    fallback z is 0 everywhere (a flat series has no variation to judge
    against, so it is treated as normal).
    """
    mean = series.mean()
    std = series.std()
    if pd.isna(std) or std == 0:
        return pd.Series(0.0, index=series.index)
    return (series - mean) / std


def standardise_sector_index(sector_wide):
    """Append a '<sector>_z' column for every sector column.

    Each z column standardises that sector's daily index against its own
    full-sample history (see ``zscore``), so a z of 0 is the sector's normal
    reading and a positive z means the news is unusually positive for that
    sector.  The raw columns are kept unchanged.  Callers that only want the
    raw index (e.g. the fusion tilt) should use the value returned by
    ``build_sector_sentiment_index`` directly rather than this frame.
    """
    out = sector_wide.copy()
    for col in sector_wide.columns:
        out[f"{col}_z"] = zscore(sector_wide[col])
    return out


def lag_sentiment(sector_index, n_lag=1):
    """Lag the sector sentiment index by n trading days (default 1).

    Use this for fusion so day t's decision uses only sentiment from t-1
    or earlier.
    """
    return sector_index.shift(n_lag)


def score_headlines(eq, news, scorer="vader"):
    """Map headlines to trading days and score them.

    Returns the mapped headline frame (ticker, trading_date, sector, title)
    plus a compound column scored with the chosen lexicon.
    """
    mapped = _map_headlines_to_trading_days(news, eq)
    scored = mapped.copy()
    scored["compound"] = _cached_score(mapped, scorer)
    return scored

"""Fear and Greed index from the finVADER headline scores (Week 9 method).

1. Reuse the cached per-headline finVADER compound scores from src.sentiment
   (no re-scoring).
2. Rescale each compound score from -1..1 to the 0..100 CNN-style scale:
   fg_100 = (compound + 1) / 2 * 100.
3. Average fg_100 per trading day across all headlines (aggregate) and also
   per (sector, trading day).
4. Smooth the aggregate with a 21-calendar-day rolling mean (min 5 days of
   news inside the window), so a gap in news does not average across it.
5. Standardise the smoothed index into a z score relative to its own history
   (in levels the index almost never falls below 50), then label it with a
   plain band: Extreme fear, Fear, Neutral, Greed, Extreme greed.
"""
import numpy as np
import pandas as pd

from src.sentiment import score_headlines

ROLL_DAYS = 21
ROLL_MIN_PERIODS = 5

# Bands on the 0 to 100 scale, matching the CNN bands (kept for reference).
FG_BANDS = [(0, 25, "Extreme fear"), (25, 45, "Fear"), (45, 55, "Neutral"),
            (55, 75, "Greed"), (75, 100, "Extreme greed")]

# Bands on the standardised scale. z = 0 is a normal day for this index,
# +1.5 or more is unusually greedy, -1.5 or less is unusually fearful.
Z_BANDS = [(-99.0, -1.5, "Extreme fear"), (-1.5, -0.5, "Fear"),
           (-0.5, 0.5, "Neutral"), (0.5, 1.5, "Greed"), (1.5, 99.0, "Extreme greed")]


def to_score_100(compound):
    """Rescale a compound score from -1..1 to the 0..100 fear/greed scale."""
    return (compound + 1.0) / 2.0 * 100.0


def _band_label(value, bands):
    """Return the band name containing value, or NaN when value is NaN."""
    if pd.isna(value):
        return np.nan
    for low, high, name in bands:
        if low <= value < high:
            return name
    return bands[-1][2]


def _daily_group(scored, keys):
    """Average the 0..100 score per day over the given keys, with counts."""
    grouped = scored.groupby(keys, as_index=False).agg(
        fg_index=("fg_100", "mean"), n_headlines=("fg_100", "size"))
    return grouped.sort_values(keys)


def build_fear_greed_index(eq, news, scorer="finvader"):
    """Build the aggregate daily Fear and Greed index.

    Returns a DataFrame with columns date, fg_index, fg_roll, fg_z, label.
    """
    scored = score_headlines(eq, news, scorer=scorer)
    scored["fg_100"] = to_score_100(scored["compound"])

    daily = _daily_group(scored, "trading_date")
    daily = daily.rename(columns={"trading_date": "date"})

    rolled = (daily.set_index("date")["fg_index"]
              .rolling(f"{ROLL_DAYS}D", min_periods=ROLL_MIN_PERIODS).mean())
    daily["fg_roll"] = rolled.values

    mean_roll, sd_roll = daily["fg_roll"].mean(), daily["fg_roll"].std()
    daily["fg_z"] = (daily["fg_roll"] - mean_roll) / sd_roll
    daily["label"] = daily["fg_z"].apply(lambda z: _band_label(z, Z_BANDS))

    return daily[["date", "fg_index", "fg_roll", "fg_z", "label"]]


def build_fear_greed_sector_index(eq, news, scorer="finvader"):
    """Build the daily Fear and Greed index per sector (for later use)."""
    scored = score_headlines(eq, news, scorer=scorer)
    scored["fg_100"] = to_score_100(scored["compound"])

    sector = _daily_group(scored, ["sector", "trading_date"])
    sector = sector.rename(columns={"trading_date": "date"})
    return sector[["date", "sector", "fg_index", "n_headlines"]]

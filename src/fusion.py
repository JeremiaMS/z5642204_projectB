"""Station 3 - Sentiment fusion: tilt equity weights by sector sentiment.

At each monthly rebalance, after the base optimiser computes the equity
fund's weights, tilt each stock's weight by its sector's lagged sentiment:
    tilted_w ∝ base_w × (1 + k × sector_sentiment_lagged)
then clip negatives to 0 and renormalise to sum 1 (long-only, fully
invested).  Sentiment is already lagged by at least 1 trading day so
there is no look-ahead.
"""
import numpy as np
import pandas as pd

from src.portfolios import (_monthly_rebalance_dates, _regularise_scale,
                            _OPTIMISERS, performance_metrics)


def _asset_to_sector(asset_name, sector_map):
    """Map an EQ_<ticker> column name to its sector name."""
    if asset_name.startswith("EQ_"):
        ticker = asset_name[3:]
        return sector_map.get(ticker, None)
    return None


def fusion_oos_backtest(returns_wide, sector_sentiment_lagged, sector_map,
                        method="max_sharpe", window=252, k=0.5,
                        periods_per_year=252):
    """Walk-forward OOS backtest with sector-sentiment tilt.  No look-ahead.

    Parameters
    ----------
    returns_wide : DataFrame  date index, asset columns, daily returns.
    sector_sentiment_lagged : DataFrame  date index, sector columns, values
        already lagged by >= 1 trading day.
    sector_map : dict  ticker -> sector.
    method : str  'min_variance', 'max_sharpe', or 'risk_parity'.
    window : int  trailing trading days for estimation.
    k : float  tilt strength (0 = no tilt, 0.5 recommended).
    periods_per_year : int  252 for equity.

    Returns
    -------
    oos_returns : pd.Series  daily OOS portfolio returns.
    weights_df  : pd.DataFrame  long (date, fund, asset, weight).
    growth      : pd.Series  cumulative growth of $1.
    metrics     : dict  performance_metrics output.
    """
    rebal_dates = _monthly_rebalance_dates(returns_wide, window)
    if len(rebal_dates) == 0:
        raise ValueError(f"No rebalance dates after initial window of {window}")

    all_oos = []
    all_weights = []

    for i, rd in enumerate(rebal_dates):
        idx = returns_wide.index.get_loc(rd)
        train = returns_wide.iloc[idx - window: idx].dropna(axis=1, how="any")
        train = train.loc[:, train.std() > 0]
        if train.shape[1] == 0:
            continue

        cov = _regularise_scale(train.cov().values)

        if method == "max_sharpe":
            mu = train.mean().values
            base_w = _OPTIMISERS[method](cov, mu)
        else:
            base_w = _OPTIMISERS[method](cov)

        assets = train.columns.tolist()
        base_series = pd.Series(base_w, index=assets)

        sent_row = sector_sentiment_lagged.loc[rd] if rd in sector_sentiment_lagged.index else None

        if sent_row is not None:
            tilt_factors = []
            for a in assets:
                sector = _asset_to_sector(a, sector_map)
                if sector is not None and sector in sent_row.index:
                    sent_val = sent_row[sector]
                else:
                    sent_val = 0.0
                tilt_factors.append(1.0 + k * sent_val)

            tilted = base_series.values * np.array(tilt_factors)
            tilted = np.maximum(tilted, 0.0)
            total = tilted.sum()
            if total > 0:
                tilted = tilted / total
            else:
                tilted = base_series.values
        else:
            tilted = base_series.values

        hold_end = (rebal_dates[i + 1]
                    if i + 1 < len(rebal_dates)
                    else returns_wide.index[-1])
        hold = returns_wide.loc[rd:hold_end]
        port = hold[assets] @ tilted
        all_oos.append(port.to_frame("returns"))

        full = pd.Series(0.0, index=returns_wide.columns)
        full[assets] = tilted
        rec = pd.DataFrame({
            "date": rd,
            "fund": f"{method}_fusion_k{k}",
            "asset": full.index,
            "weight": full.values,
        })
        all_weights.append(rec)

    oos = pd.concat(all_oos).sort_index()
    oos = oos[~oos.index.duplicated(keep="first")]
    weights_df = pd.concat(all_weights, ignore_index=True)
    growth = (1 + oos["returns"]).cumprod()
    metrics = performance_metrics(oos["returns"],
                                  periods_per_year=periods_per_year)
    return oos["returns"], weights_df, growth, metrics


def base_vs_tilted_table(base_returns, tilted_returns,
                         base_name="Equity Max-Sharpe",
                         tilted_name="Equity Max-Sharpe + Sentiment Tilt",
                         periods_per_year=252):
    """Build before-vs-after comparison DataFrame.

    Parameters
    ----------
    base_returns, tilted_returns : pd.Series  daily returns.
    base_name, tilted_name : str
    periods_per_year : int

    Returns
    -------
    DataFrame  index [base_name, tilted_name], columns metrics.
    """
    base_met = performance_metrics(base_returns,
                                   periods_per_year=periods_per_year)
    tilt_met = performance_metrics(tilted_returns,
                                   periods_per_year=periods_per_year)
    rows = [
        {"fund": base_name, **base_met},
        {"fund": tilted_name, **tilt_met},
    ]
    return pd.DataFrame(rows)

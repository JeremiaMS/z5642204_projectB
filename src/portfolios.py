"""Station 3 - your funds: optimal portfolios + out-of-sample backtest.

Build at least a combined equity-plus-crypto fund with two optimisation methods.
Backtest rules: walk-forward, no look-ahead, weights from past data only, annualise
with 252 (equity) or 365 (crypto). See the brief, Part B.
"""
import numpy as np
import pandas as pd
from scipy.optimize import LinearConstraint, minimize

SCALE = 10000.0
EPS = 1e-6


def performance_metrics(daily_returns, periods_per_year=252, risk_free=0.0):
    """Return dict: ann_return, ann_vol, sharpe, max_drawdown, growth_of_1."""
    daily_returns = daily_returns.dropna()
    if len(daily_returns) == 0:
        return {"ann_return": np.nan, "ann_vol": np.nan, "sharpe": np.nan,
                "max_drawdown": np.nan, "growth_of_1": np.nan}

    ann_return = (1 + daily_returns).prod() ** (periods_per_year / len(daily_returns)) - 1
    ann_vol = daily_returns.std() * np.sqrt(periods_per_year)
    sharpe = (ann_return - risk_free) / ann_vol if ann_vol > 0 else np.nan

    wealth = (1 + daily_returns).cumprod()
    running_max = wealth.cummax()
    drawdown = (wealth - running_max) / running_max
    max_dd = drawdown.min()

    return {
        "ann_return": ann_return,
        "ann_vol": ann_vol,
        "sharpe": sharpe,
        "max_drawdown": max_dd,
        "growth_of_1": wealth.iloc[-1],
    }


def _regularise_scale(cov):
    return cov * SCALE + np.eye(cov.shape[0]) * EPS


def _min_variance_weights(cov):
    n = cov.shape[0]
    x0 = np.ones(n) / n
    constraints = {"type": "eq", "fun": lambda w: w.sum() - 1.0}
    bounds = [(0, 1)] * n
    result = minimize(lambda w: w @ cov @ w, x0,
                      method="SLSQP", bounds=bounds,
                      constraints=constraints,
                      options={"ftol": 1e-12, "maxiter": 2000})
    return result.x if result.success else x0


def _max_sharpe_weights(cov, mu):
    n = cov.shape[0]
    x0 = np.ones(n) / n
    constraints = {"type": "eq", "fun": lambda w: w.sum() - 1.0}
    bounds = [(0, 1)] * n

    def objective(w):
        pv = w @ cov @ w
        pr = w @ mu
        if pv <= 0 or pr <= 0:
            return 1e10
        return -pr / np.sqrt(pv)

    result = minimize(objective, x0, method="SLSQP", bounds=bounds,
                      constraints=constraints,
                      options={"ftol": 1e-12, "maxiter": 2000})
    return result.x if result.success else x0


def _risk_parity_weights(cov):
    n = cov.shape[0]
    x0 = np.ones(n) / n
    constraints = {"type": "eq", "fun": lambda w: w.sum() - 1.0}
    bounds = [(0, 1)] * n

    def objective(w):
        pv = w @ cov @ w
        rc = w * (cov @ w)
        target = pv / n
        return np.sum((rc - target) ** 2)

    result = minimize(objective, x0, method="SLSQP", bounds=bounds,
                      constraints=constraints,
                      options={"ftol": 1e-12, "maxiter": 2000})
    return result.x if result.success else x0


_OPTIMISERS = {
    "min_variance": _min_variance_weights,
    "max_sharpe": _max_sharpe_weights,
    "risk_parity": _risk_parity_weights,
}


def efficient_frontier_points(returns_wide, n_points=30, periods_per_year=252):
    """Long only mean variance efficient frontier, annualised.

    Solves the minimum variance long only portfolio for each target return,
    from the minimum variance portfolio up to the highest single asset mean.
    Uses the same covariance scaling as the optimisers so the solver stays
    stable on the 60 asset panel.

    Parameters
    ----------
    returns_wide : DataFrame  date index, asset columns, daily returns.
    n_points : int  number of frontier points (default 30).
    periods_per_year : int  annualisation factor (default 252).

    Returns
    -------
    DataFrame  columns target_return and vol, both annualised decimals.
    """
    ret = returns_wide.dropna(axis=0)
    ret = ret.loc[:, ret.std() > 0]
    mu = ret.mean().values
    cov = ret.cov().values
    cov_scaled = _regularise_scale(cov)
    n = cov.shape[0]

    bounds = [(0, 1)] * n
    full_weight = LinearConstraint(np.ones(n), 1.0, 1.0)

    def _min_var_at(target_daily, w0):
        target = LinearConstraint(mu, target_daily, target_daily)
        result = minimize(lambda w: w @ cov_scaled @ w, w0,
                          method="trust-constr", bounds=bounds,
                          constraints=[full_weight, target],
                          options={"maxiter": 2000, "gtol": 1e-10,
                                   "barrier_tol": 1e-10})
        return result.x

    w_mv = _min_variance_weights(cov_scaled)
    mv_daily = float(w_mv @ mu)

    w = np.copy(w_mv)
    rows = []
    for t in np.linspace(mv_daily, float(mu.max()), n_points):
        w = _min_var_at(t, w)
        rows.append({
            "target_return": t * periods_per_year,
            "vol": float(np.sqrt(w @ cov @ w)) * np.sqrt(periods_per_year),
        })
    return pd.DataFrame(rows)


def _monthly_rebalance_dates(returns_wide, min_idx):
    dates = returns_wide.index
    seen = set()
    first_of_month = []
    for d in dates:
        ym = (d.year, d.month)
        if ym not in seen:
            seen.add(ym)
            first_of_month.append(d)
    return [d for d in first_of_month
            if returns_wide.index.get_loc(d) >= min_idx]


def oos_backtest(returns_wide, method="min_variance", window=252,
                 rebalance="monthly", periods_per_year=252):
    """Walk-forward out-of-sample backtest. No look-ahead.

    Parameters
    ----------
    returns_wide : DataFrame  date index, asset columns, daily returns.
    method : str  'min_variance', 'max_sharpe', or 'risk_parity'.
    window : int  trailing trading days for estimation.
    rebalance : str  only 'monthly' supported.
    periods_per_year : int  252 for equity, 365 for crypto.

    Returns
    -------
    oos_returns : pd.Series  daily OOS portfolio returns.
    weights_df  : pd.DataFrame  long (date, fund, asset, weight).
    growth      : pd.Series  cumulative growth of $1.
    metrics     : dict  performance_metrics output.
    """
    if rebalance != "monthly":
        raise ValueError("Only 'monthly' rebalance is supported")

    rebal_dates = _monthly_rebalance_dates(returns_wide, window)
    if len(rebal_dates) == 0:
        raise ValueError(f"No rebalance dates after initial window of {window}")

    first_live_date = rebal_dates[0]
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
            w = _OPTIMISERS[method](cov, mu)
        else:
            w = _OPTIMISERS[method](cov)

        hold_end = (rebal_dates[i + 1]
                    if i + 1 < len(rebal_dates)
                    else returns_wide.index[-1])
        hold = returns_wide.loc[rd:hold_end]
        port = hold[train.columns] @ w
        all_oos.append(port.to_frame("returns"))

        full = pd.Series(0.0, index=returns_wide.columns)
        full[train.columns] = w
        rec = pd.DataFrame({
            "date": rd,
            "fund": method,
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

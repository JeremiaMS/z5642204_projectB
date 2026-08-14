"""Station 4 - Fund growth simulator: lognormal Monte Carlo projection.

Pure maths on two numbers (annualised return and volatility from
results/tables/performance_metrics.csv).  No backtest, no data loading, no
look-ahead concerns: it simply replays a fund's assumed return/volatility
forward over a horizon.  Used by the Streamlit "Simulate" page, which passes
only the precomputed metrics in.
"""
import numpy as np


def simulate_growth(P0, pmt_monthly, years, ann_return, ann_vol,
                    n_sims=2000, seed=42):
    """Simulate future fund wealth month-by-month with a lognormal random walk.

    Wealth stays non-negative because each month's multiplicative factor is
    ``exp(monthly log-return) > 0`` and contributions are added on top.

    Parameters
    ----------
    P0 : float  initial investment in dollars.
    pmt_monthly : float  contribution added at the end of each month.
    years : float  projection horizon in years (months = round(years*12)).
    ann_return : float  fund's annualised return, e.g. 0.12 for 12%.
    ann_vol : float  fund's annualised volatility, e.g. 0.25.
    n_sims : int  number of Monte Carlo paths.
    seed : int  RNG seed for reproducible runs.

    Returns
    -------
    dict with
        months : int
        wealth : ndarray (n_sims, months)  simulated value of every path at
            each month end (after contributions and fees), so callers can
            derive their own statistics straight from the paths.
        p10 / median / p90 : ndarray (months,)  10th, 50th and 90th
            percentile of wealth at each month end across all paths.
        contributions : ndarray (months,)  cumulative money put in
            (P0 plus monthly contributions), the "total contributed" line.
    """
    rng = np.random.default_rng(seed)
    months = int(round(years * 12))
    if months < 1 or P0 < 0 or pmt_monthly < 0 or ann_vol < 0:
        raise ValueError("months >= 1 and P0/pmt/vol must be non-negative")

    # Annual log-return drift: log(1+r) - 0.5*sigma^2 (Itô correction).
    mu = np.log(1.0 + ann_return) - 0.5 * ann_vol ** 2
    sigma_m = ann_vol / np.sqrt(12.0)

    log_growth = mu / 12.0 + sigma_m * rng.standard_normal((n_sims, months))
    growth = np.exp(log_growth)

    wealth = np.empty_like(growth)
    wealth[:, 0] = P0 * growth[:, 0] + pmt_monthly
    for t in range(1, months):
        wealth[:, t] = wealth[:, t - 1] * growth[:, t] + pmt_monthly

    p10, med, p90 = np.percentile(wealth, [10, 50, 90], axis=0)
    contributions = P0 + pmt_monthly * np.arange(1, months + 1)

    return {
        "months": months,
        "wealth": wealth,
        "p10": p10,
        "median": med,
        "p90": p90,
        "contributions": contributions,
    }


def blend_stats(weights, fund_returns_df, perf_df, funds):
    """Return/volatility of a blended portfolio from precomputed metrics.

    Volatility is fully diversified: sigma_blend = sqrt(w' Sigma w) where
    Sigma_ij = vol_i * vol_j * corr_ij uses the funds' reported annualised
    volatilities and the correlation matrix of their precomputed daily fund
    returns.  naive_sig is the weighted-average volatility, ignoring any
    diversification benefit, so blend_sig < naive_sig for a multi-fund blend
    with imperfect correlation.

    Parameters
    ----------
    weights : dict  fund name -> weight (zeros allowed; sum need not be 1).
    fund_returns_df : DataFrame  date index, fund columns, daily returns.
    perf_df : DataFrame  rows with 'fund', 'ann_return', 'ann_vol'.
    funds : iterable of str  candidate fund names (non-positive weights are
        dropped).

    Returns
    -------
    tuple (blend_mu, blend_sig, naive_sig)
        blend_mu : float  weighted-average annualised return.
        blend_sig : float  diversified annualised volatility.
        naive_sig : float  weighted-average annualised volatility.
    """
    active = [f for f in funds if weights.get(f, 0.0) > 0]
    if not active:
        raise ValueError("blend has no positive-weight funds")
    w = np.array([weights[f] for f in active], dtype=float)
    w = w / w.sum()

    m = perf_df.set_index("fund")
    mu = np.array([m.loc[f, "ann_return"] for f in active], dtype=float)
    vol = np.array([m.loc[f, "ann_vol"] for f in active], dtype=float)

    blend_mu = float(w @ mu)
    naive_sig = float(w @ vol)

    corr = fund_returns_df[active].corr().to_numpy()
    corr = np.where(np.isnan(corr), 0.0, corr)
    sigma = np.outer(vol, vol) * corr
    blend_sig = float(np.sqrt(w @ sigma @ w))
    return blend_mu, blend_sig, naive_sig


def scenario_stats(P0, ann_return, ann_vol):
    """One-year dollar-outcome percentiles (rough / typical / strong).

    Reuses the same lognormal engine as ``simulate_growth`` with no monthly
    contributions, so the scenario numbers are consistent with the growth
    charts on the same page.

    Parameters
    ----------
    P0 : float  initial investment in dollars.
    ann_return : float  fund's annualised return, e.g. 0.12 for 12%.
    ann_vol : float  fund's annualised volatility, e.g. 0.25.

    Returns
    -------
    dict with 'rough' (10th), 'typical' (50th) and 'strong' (90th)
    percentile dollar values one year out.
    """
    res = simulate_growth(P0, 0.0, 1, ann_return, ann_vol)
    return {
        "rough": res["p10"][-1],
        "typical": res["median"][-1],
        "strong": res["p90"][-1],
    }


def blend_max_drawdown(weights, fund_returns_df, funds):
    """Worst historical peak-to-trough fall of a blended portfolio.

    The blend's daily returns are the weighted sum of the precomputed daily
    fund returns; the drawdown is the deepest drop of the resulting wealth
    line below its running peak.  Uses only results/data/fund_returns.csv
    (no backtest, no look-ahead).

    Parameters
    ----------
    weights : dict  fund name -> weight (zeros allowed; sum need not be 1).
    fund_returns_df : DataFrame  date index, fund columns, daily returns.
    funds : iterable of str  candidate fund names (non-positive weights are
        dropped).

    Returns
    -------
    float  max drawdown, always <= 0 (e.g. -0.25 for a 25% worst fall).
    """
    active = [f for f in funds if weights.get(f, 0.0) > 0]
    if not active:
        raise ValueError("blend has no positive-weight funds")
    w = np.array([weights[f] for f in active], dtype=float)
    w = w / w.sum()

    blended = fund_returns_df[active].mul(w, axis=1).sum(axis=1).dropna()
    wealth = (1 + blended).cumprod()
    drawdown = wealth / wealth.cummax() - 1
    return float(drawdown.min())

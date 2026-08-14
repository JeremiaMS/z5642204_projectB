"""Station 4 – Investor app.  Reads precomputed CSVs only."""
from __future__ import annotations

import html
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib
matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go

from src import simulate
from src.glossary import GLOSSARY, TERMS

RESULTS = pathlib.Path("results")
DATA = RESULTS / "data"
TABLES = RESULTS / "tables"

# Investra's annual management fee, charged on the balance each year.
MANAGEMENT_FEE = 0.0075  # 0.75 percent a year

# Sentiment z-score bands, in standard deviations from a sector's own
# normal. |z| < NORMAL is "about normal", NORMAL..UNUSUAL is "a bit
# above/below normal", beyond UNUSUAL is "unusually positive/negative".
SENTIMENT_Z_NORMAL = 0.5
SENTIMENT_Z_UNUSUAL = 1.5
# The gauge needle axis spans -GAUGE..+GAUGE standard deviations.
SENTIMENT_GAUGE_MAX = 3.0


# ── GREEN DESIGN SYSTEM ─────────────────────────────────────────

THEME_CSS = """
<style>
/* ── Tokens ─────────────────────────────────────────────── */
:root {
    --brand-green: #05A167;
    --brand-amber: #E8973A;
    --brand-coral: #E5484D;
    --ink: #14181B;
    --paper: #FFFFFF;
    --paper-soft: #F6F8F9;
    --line: #E3E8EA;
    --muted: #5B666B;
}

/* ── Base ───────────────────────────────────────────────── */
html, body, .stApp, [data-testid="stAppViewContainer"] {
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    color: var(--ink);
}
[data-testid="stAppViewContainer"] {
    background: var(--paper);
}
[data-testid="stHeader"] {
    background: transparent;
}

/* ── Headings ───────────────────────────────────────────── */
h1, h2, h3 {
    color: var(--ink);
    letter-spacing: -0.01em;
}
h1, h2 {
    border-bottom: 2px solid var(--line);
    padding-bottom: 0.35rem;
}
h1::before, h2::before {
    content: "▮";
    color: var(--brand-green);
    margin-right: 0.45rem;
    font-size: 0.85em;
}
h3 {
    color: var(--brand-green);
}

/* ── Buttons ────────────────────────────────────────────── */
[data-testid="stBaseButton-primary"] {
    background: var(--brand-green);
    border: none;
    font-weight: 700;
}
[data-testid="stBaseButton-primary"]:hover {
    background: #048A58;
    border: none;
}
[data-testid="stBaseButton-secondary"] {
    border: 1px solid var(--brand-green);
    color: var(--brand-green);
    font-weight: 600;
}
[data-testid="stBaseButton-secondary"]:hover {
    border: 1px solid var(--brand-green);
    background: #EAF6F0;
}

/* ── Metrics ────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: var(--paper-soft);
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 0.9rem 1rem;
}
[data-testid="stMetricValue"] {
    color: var(--brand-green);
    font-weight: 800;
}
[data-testid="stMetricLabel"] {
    color: var(--muted);
}

/* ── Radio nav pills ────────────────────────────────────── */
[data-testid="stRadio"] [role="radiogroup"] {
    gap: 0.25rem;
    flex-wrap: wrap;
}
[data-testid="stRadio"] label {
    background: var(--paper-soft);
    border: 1px solid var(--line);
    border-radius: 999px;
    padding: 0.3rem 0.9rem;
}
[data-testid="stRadio"] label:has(input:checked) {
    background: var(--brand-green);
    border-color: var(--brand-green);
}
[data-testid="stRadio"] label:has(input:checked) p {
    color: #FFFFFF;
}

/* ── Dataframes & charts ────────────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--line);
    border-radius: 14px;
    overflow: hidden;
}
[data-testid="stPlotlyChart"] {
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 0.5rem;
    background: var(--paper);
}

/* ── Captions / info ────────────────────────────────────── */
[data-testid="stCaptionContainer"] {
    color: var(--muted);
}
[data-testid="stAlertContainer"] {
    border-radius: 12px;
    border: 1px solid var(--line);
}

/* ── Comfort tiers ──────────────────────────────────────── */
.tier-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1.25rem;
    margin: 1rem 0 1.5rem;
}
.tier-col {
    display: flex;
    flex-direction: column;
    gap: 0.7rem;
}
.tier-head {
    padding-top: 0.65rem;
}
.tier-head-title {
    font-size: 1.02rem;
    font-weight: 800;
    color: var(--ink);
}
.tier-head-desc {
    font-size: 0.82rem;
    color: var(--muted);
    margin-top: 0.12rem;
}
.tier-fund {
    background: var(--paper);
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 0.85rem 1.05rem 0.8rem;
}
.tier-fund-name {
    font-size: 0.95rem;
    font-weight: 700;
    color: var(--ink);
}
.tier-fund-return {
    font-size: 1.7rem;
    font-weight: 800;
    line-height: 1.15;
}
.tier-fund-drop {
    font-size: 0.78rem;
    color: var(--muted);
}
/* ── Fund-card "?" chip ────────────────────────────────── */
.fund-help {
    display: inline-block;
    margin-left: 0.35rem;
    width: 1.05rem;
    height: 1.05rem;
    line-height: 1.05rem;
    text-align: center;
    border-radius: 50%;
    background: var(--paper-soft);
    border: 1px solid var(--line);
    color: var(--brand-green);
    font-size: 0.75rem;
    font-weight: 800;
    cursor: help;
    vertical-align: 0.05em;
}
/* ── Compare: personalized ranking ─────────────────────── */
.quiz-prompt {
    background: var(--paper-soft);
    border: 1px dashed var(--brand-green);
    border-radius: 14px;
    padding: 0.8rem 1.1rem;
    font-size: 0.95rem;
    color: var(--ink);
    margin: 0.5rem 0 0.5rem;
}
.match-banner {
    background: #EAF6F0;
    border: 1px solid #BFE8D4;
    border-radius: 14px;
    padding: 1rem 1.2rem;
    margin: 0.75rem 0 0.5rem;
}
.match-banner-title {
    font-size: 1.15rem;
    font-weight: 800;
    color: #0F7B4E;
}
.match-banner-sub {
    font-size: 0.85rem;
    color: #3A4045;
    margin-top: 0.2rem;
}
.fit-row {
    margin: 1rem 0 1.5rem;
}
.fit-row-title {
    font-size: 0.95rem;
    font-weight: 700;
    color: var(--ink);
    margin-bottom: 0.4rem;
}
.fit-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0.75rem;
}
.fit-card {
    background: var(--paper);
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 0.8rem 1rem;
}
.fit-card.dim {
    opacity: 0.6;
}
.fit-card-name {
    font-size: 0.92rem;
    font-weight: 700;
    color: var(--ink);
    margin-bottom: 0.45rem;
}
.fit-bar-wrap {
    height: 7px;
    background: #EFF2F3;
    border-radius: 999px;
    overflow: hidden;
    margin-bottom: 0.35rem;
}
.fit-bar {
    height: 100%;
    border-radius: 999px;
    background: var(--brand-green);
}
.fit-card-score {
    font-size: 0.82rem;
    font-weight: 800;
    color: #0F7B4E;
}
.fit-card-reason {
    font-size: 0.78rem;
    color: var(--muted);
    margin-top: 0.15rem;
    line-height: 1.35;
}
/* ── Dictionary cards ──────────────────────────────────── */
.dict-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 0.75rem;
    margin: 0.5rem 0 1.25rem;
}
.dict-card {
    background: var(--paper-soft);
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 0.9rem 1rem;
}
.dict-term {
    color: var(--brand-green);
    font-weight: 800;
    font-size: 1.02rem;
    margin-bottom: 0.25rem;
}
.dict-def {
    color: var(--ink);
    font-size: 0.9rem;
    line-height: 1.45;
}
/* ── Scenario tiles ──────────────────────────────────────── */
.scenario-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0.75rem;
    margin: 1.25rem 0 0.75rem;
}
.scenario-tile {
    border-radius: 14px;
    padding: 0.9rem 1rem;
    color: #FFFFFF;
    box-shadow: 0 2px 8px rgba(20, 24, 27, 0.08);
}
.scenario-tile-neutral {
    color: #14181B;
}
.scenario-label {
    font-size: 0.78rem;
    font-weight: 600;
    opacity: 0.85;
    margin-bottom: 0.25rem;
}
.scenario-value {
    font-size: 1.5rem;
    font-weight: 800;
    line-height: 1.1;
}
.scenario-diff {
    font-size: 0.78rem;
    opacity: 0.9;
    margin-top: 0.15rem;
}
.scenario-banner {
    background: #FBE9E7;
    border: 1px solid #F3C9C4;
    border-radius: 12px;
    padding: 0.7rem 1rem;
    font-size: 0.9rem;
    color: #14181B;
    margin-bottom: 0.75rem;
}
/* ── Simulate: fee callout ─────────────────────────────── */
.fee-callout {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    background: #F3FBF7;
    border: 1px solid #BFE6D2;
    border-radius: 12px;
    padding: 0.75rem 1rem;
    font-size: 0.95rem;
    color: #14181B;
    margin-bottom: 0.9rem;
}
.fee-callout svg {
    flex: 0 0 auto;
}
/* ── Build allocation: step guide & callout ─────────────── */
.step-tile {
    background: #EAF6F0;
    border: 1px solid #CDEEDD;
    border-radius: 14px;
    padding: 0.9rem 1rem;
    color: #14181B;
}
.step-num {
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #05A167;
    margin-bottom: 0.3rem;
}
.step-title {
    font-size: 0.95rem;
    font-weight: 700;
    margin-bottom: 0.25rem;
}
.step-text {
    font-size: 0.84rem;
    line-height: 1.45;
    color: #3A4045;
}
.alloc-callout {
    border: 2px dashed #B5DCC9;
    background: #F4FBF7;
    border-radius: 14px;
    padding: 1rem 1.2rem;
    text-align: center;
    font-size: 1.02rem;
    font-weight: 600;
    color: #05A167;
    margin: 0.5rem 0 1rem;
}
/* ── Sentiment page ─────────────────────────────────────── */
.explainer-card {
    background: #F7F9FA;
    border: 1px solid #E3E8EA;
    border-radius: 14px;
    padding: 1rem 1.2rem;
    margin-bottom: 1.25rem;
}
.explainer-card h3 {
    font-size: 1.02rem;
    font-weight: 700;
    margin: 0 0 0.35rem;
    color: #14181B;
}
.explainer-card p {
    font-size: 0.92rem;
    line-height: 1.5;
    color: #3A4045;
    margin: 0;
}
.plain-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
    margin: 0.5rem 0 0.25rem;
}
.plain-table th {
    text-align: left;
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #8A9198;
    border-bottom: 2px solid #E3E8EA;
    padding: 0.45rem 0.6rem;
}
.plain-table td {
    padding: 0.5rem 0.6rem;
    border-bottom: 1px solid #EFF2F3;
    color: #14181B;
}
.plain-table tr.row-best td {
    background: #EAF6F0;
    color: #0F7B4E;
    font-weight: 600;
}
.plain-table tr.row-worst td {
    background: #FDF0EE;
    color: #C2302F;
    font-weight: 600;
}
.takeaway-card {
    background: #EAF6F0;
    border: 1px solid #BFE8D4;
    border-radius: 14px;
    padding: 1rem 1.2rem;
    font-size: 0.92rem;
    line-height: 1.5;
    color: #14181B;
    margin: 1.25rem 0 0.5rem;
}
/* ── Page header & top spacing ──────────────────────────── */
.block-container {
    padding-top: 1.2rem;
}
.brand-header {
    margin: 0.25rem 0 1rem;
}
.brand-header-title {
    font-size: 1.9rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: #14181B;
}
</style>
"""


# ── CACHED LOADERS ──────────────────────────────────────────────

@st.cache_data
def load_perf():
    return pd.read_csv(TABLES / "performance_metrics.csv")


@st.cache_data
def load_fund_returns():
    return pd.read_csv(DATA / "fund_returns.csv", index_col=0, parse_dates=True)


@st.cache_data
def load_fund_weights():
    return pd.read_csv(DATA / "fund_weights.csv")


@st.cache_data
def load_sentiment(_cache_version: int = 2):
    """Sector sentiment index. _cache_version is the bump for the CSV now
    carrying per-sector '<sector>_z' columns."""
    return pd.read_csv(DATA / "sector_sentiment_index.csv", index_col=0, parse_dates=True)


@st.cache_data
def load_fusion():
    return pd.read_csv(TABLES / "fusion_comparison.csv")


@st.cache_data
def load_ksweep():
    return pd.read_csv(TABLES / "fusion_ksweep.csv")


@st.cache_data
def load_cash_benchmark():
    return pd.read_csv(DATA / "cash_benchmark.csv", parse_dates=["date"])


@st.cache_data
def load_vs_cash():
    return pd.read_csv(TABLES / "vs_cash.csv")


@st.cache_data
def load_trailing():
    return pd.read_csv(TABLES / "trailing_returns.csv")


@st.cache_data
def load_lexicon_comparison():
    return pd.read_csv(TABLES / "lexicon_comparison.csv")


@st.cache_data
def load_efficient_frontier():
    return pd.read_csv(TABLES / "efficient_frontier.csv")


@st.cache_data
def load_fund_correlation():
    return pd.read_csv(TABLES / "fund_correlation.csv", index_col=0)


# ── DATA ────────────────────────────────────────────────────────

perf = load_perf()
fund_ret = load_fund_returns()
fund_w = load_fund_weights()
sent_idx = load_sentiment()
fusion = load_fusion()
ksweep = load_ksweep()
cash_bm = load_cash_benchmark()
vs_cash = load_vs_cash()
trailing = load_trailing()
efficient_frontier = load_efficient_frontier()
fund_corr = load_fund_correlation()

METRICS_PLAIN = {
    "ann_return": ("Typical yearly growth", "{:.2%}"),
    "ann_vol": ("How bumpy", "{:.2%}"),
    "sharpe": ("Reward for risk", "{:.2f}"),
    "max_drawdown": ("Worst-ever drop", "{:.2%}"),
    "growth_of_1": ("$1 became", "${:.2f}"),
}

METRIC_TERMS = {
    "Typical yearly growth": "Annualised return",
    "How bumpy": "Volatility",
    "Reward for risk": "Sharpe ratio",
    "Worst-ever drop": "Max drawdown",
    "Likely value": "Median",
    "Pessimistic": "Percentile",
    "Optimistic": "Percentile",
    "Total contributed": "Total contributed",
}


def metric_help(label):
    """Definition for a metric label, pulled from the shared glossary."""
    return TERMS[METRIC_TERMS[label]]

FUND_COLORS = {
    "Combined Max-Sharpe": "#1f77b4",
    "Combined Min-Variance": "#ff7f0e",
    "Combined Risk-Parity": "#2ca02c",
    "Equity Max-Sharpe": "#d62728",
    "Equity Min-Variance": "#17becf",
    "Equity Risk-Parity": "#bcbd22",
    "Crypto Max-Sharpe": "#e377c2",
    "Crypto Min-Variance": "#9467bd",
    "Crypto Risk-Parity": "#8c564b",
}

UNIVERSE_ORDER = {"Combined": 0, "Equity": 1, "Crypto": 2}
METHOD_ORDER = {"Max-Sharpe": 0, "Min-Variance": 1, "Risk-Parity": 2}


def fund_sort_key(name):
    universe = next((u for u in ("Combined", "Equity", "Crypto")
                     if name.startswith(u)), 3)
    method = next((m for m in ("Max-Sharpe", "Min-Variance", "Risk-Parity")
                   if m in name), 3)
    return (UNIVERSE_ORDER.get(universe, 3), METHOD_ORDER.get(method, 3))


def fund_names_ordered():
    return sorted(fund_ret.columns, key=fund_sort_key)


# ── HELPERS ─────────────────────────────────────────────────────

def risk_badge(vol):
    if vol < 0.13:
        return "🟢 **Low**"
    if vol < 0.18:
        return "🟡 **Medium**"
    if vol < 0.30:
        return "🟠 **High**"
    return "🔴 **Very high**"


@st.cache_data
def wealth_series(returns: pd.Series):
    return (1 + returns.dropna()).cumprod()


@st.cache_data
def drawdown_series(returns: pd.Series):
    w = (1 + returns.dropna()).cumprod()
    return (w - w.cummax()) / w.cummax()


def sim_figure(result, years):
    months = result["months"]
    t = np.arange(1, months + 1) / 12.0
    wealth = result.get("wealth")
    if wealth is not None:
        p10, p50, p90 = np.percentile(wealth, [10, 50, 90], axis=0)
    else:
        p10, p50, p90 = result["p10"], result["median"], result["p90"]
    fig, ax = plt.subplots(figsize=(7.2, 4.2), dpi=110)
    if wealth is not None:
        ax.fill_between(t, p10, p90, color="#2E9E6B", alpha=0.06)
    ax.plot(t, p90, color="#2E9E6B", linewidth=2.0,
            label="Best case (1 in 10 better)")
    ax.plot(t, p50, color="#1F2A24", linewidth=2.0,
            label="Likely (middle)")
    ax.plot(t, result["contributions"], color="#6B7A72", linestyle="--",
            linewidth=1.6, label="What you put in")
    ax.plot(t, p10, color="#C9483F", linewidth=2.0,
            label="Worst case (1 in 10 worse)")
    ax.set_xlabel("Years")
    ax.set_ylabel("Value ($)")
    ax.set_xlim(0, years)
    ax.set_ylim(bottom=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, color="#E3E8EA", linewidth=0.8)
    ax.legend(frameon=False)
    fig.tight_layout()
    return fig


def go_to(page):
    st.session_state["page"] = page


def reset_match():
    st.session_state["recommended_fund"] = None
    st.session_state.pop("risk_score", None)
    st.session_state.pop("crypto_pref", None)
    st.session_state.pop("horizon_level", None)


def go_simulate(fund):
    st.session_state["sim_fund"] = fund
    st.session_state["page"] = "Simulate"


def render_scenarios(P0, mu, sig, max_dd):
    """One-year 'if you invested $X' panel: three tiles + reality check."""
    stats = simulate.scenario_stats(P0, mu, sig)
    tiles = [
        ("A rough year", stats["rough"], "#E5484D", ""),
        ("A typical year", stats["typical"], "#E8ECED",
         " scenario-tile-neutral"),
        ("A strong year", stats["strong"], "#05A167", ""),
    ]
    html = ['<div class="scenario-grid">']
    for label, value, bg, extra in tiles:
        diff = value - P0
        sign = "+" if diff >= 0 else "−"
        html.append(
            f'<div class="scenario-tile{extra}" style="background:{bg};">'
            f'<div class="scenario-label">{label}</div>'
            f'<div class="scenario-value">${value:,.0f}</div>'
            f'<div class="scenario-diff">{sign}${abs(diff):,.0f} vs today</div>'
            "</div>")
    html.append("</div>")
    html.append(
        '<div class="scenario-banner"><strong>Reality check.</strong> '
        f"At its worst, this fund fell far enough that ${P0:,.0f} briefly "
        f"became ${P0 * (1 + max_dd):,.0f} before recovering.</div>")
    st.markdown("".join(html), unsafe_allow_html=True)
    st.caption("A one-year simulation using the fund's historical return "
               "and volatility. Not a guarantee.")


def render_header(title):
    """Page title heading — the brand lives in the green top bar."""
    st.markdown(
        f'<div class="brand-header">'
        f'<span class="brand-header-title">{title}</span></div>',
        unsafe_allow_html=True,
    )


def render_topbar():
    st.markdown("""
    <div style="background:#05A167;border-radius:14px;padding:14px 20px;margin:0 0 16px;
        display:flex;align-items:center;gap:12px;">
      <svg width="34" height="34" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
        <rect width="48" height="48" rx="13" fill="#ffffff"/>
        <path d="M11 33L20 27L28 30L38 15" fill="none" stroke="#05A167" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M31 15H38V22" fill="none" stroke="#05A167" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>
        <circle cx="11" cy="33" r="2.5" fill="#05A167"/>
      </svg>
      <span style="font-family:'Inter',sans-serif;font-size:22px;font-weight:800;
        letter-spacing:-.02em;color:#ffffff;">Investra</span>
    </div>""", unsafe_allow_html=True)


def explain_fund_name(name):
    """Plain-English 'family + method' explanation of a fund name."""
    universe = next((u for u in ("Combined", "Equity", "Crypto")
                     if name.startswith(u)), None)
    method = next((m for m in ("Max-Sharpe", "Min-Variance", "Risk-Parity")
                   if m in name), None)
    family_term = {"Combined": "Combined fund", "Equity": "Equity fund",
                   "Crypto": "Crypto fund"}.get(universe)
    parts = [f"{name} = family + method."]
    if family_term:
        parts.append(f"Family — {TERMS[family_term]}")
    if method:
        parts.append(f"Method — {TERMS[method]}")
    return " ".join(parts)


def render_fundname_popover(name=None):
    """'?' popover explaining the fund-naming convention."""
    with st.popover("❓ What do these fund names mean?"):
        if name:
            st.markdown(f"**{name}** breaks down into a *family* (the assets "
                        "it invests in) plus a *method* (how it picks the "
                        "mix).")
            universe = next((u for u in ("Combined", "Equity", "Crypto")
                             if name.startswith(u)), None)
            method = next((m for m in ("Max-Sharpe", "Min-Variance",
                                       "Risk-Parity") if m in name), None)
            family_term = {"Combined": "Combined fund", "Equity": "Equity fund",
                           "Crypto": "Crypto fund"}.get(universe)
            if family_term:
                st.markdown(f"- **Family ({universe})** — {TERMS[family_term]}")
            if method:
                st.markdown(f"- **Method ({method})** — {TERMS[method]}")
        else:
            st.markdown("Every fund name has two parts: a **family** — the "
                        "assets it invests in — and a **method** — how it "
                        "picks the mix.")
            st.markdown("**Families**")
            for t in ("Combined fund", "Equity fund", "Crypto fund"):
                st.markdown(f"- **{t.replace(' fund', '')}** — {TERMS[t]}")
            st.markdown("**Methods**")
            for t in ("Max-Sharpe", "Min-Variance", "Risk-Parity"):
                st.markdown(f"- **{t}** — {TERMS[t]}")


@st.cache_data
def run_sim(p0, pmt_monthly, years, ann_return, ann_vol, _cache_version: int = 2):
    """Cached simulator. _cache_version is the cache bump for the return
    shape that now includes the "wealth" matrix."""
    return simulate.simulate_growth(p0, pmt_monthly, years, ann_return, ann_vol)


def fund_tier(vol):
    if vol < 0.16:
        return "Conservative"
    if vol < 0.35:
        return "Balanced"
    return "Growth"


def metric_row(m):
    c1, c2, c3, c4 = st.columns(4)
    cols = [c1, c2, c3, c4]
    keys = ["ann_return", "ann_vol", "sharpe", "max_drawdown"]
    for col, k in zip(cols, keys):
        label, fmt = METRICS_PLAIN[k]
        col.metric(label, fmt.format(m[k]), help=metric_help(label))


def fund_description(name):
    """One plain line describing a fund from its family and method."""
    universe = next((u for u in ("Combined", "Equity", "Crypto")
                     if name.startswith(u)), None)
    method = next((m for m in ("Max-Sharpe", "Min-Variance", "Risk-Parity")
                   if m in name), None)
    family_phrase = {
        "Combined": "A mix of US stocks and crypto",
        "Equity": "US stocks only",
        "Crypto": "Crypto only",
    }.get(universe, "")
    method_phrase = {
        "Max-Sharpe": "weighted for the best reward for risk",
        "Min-Variance": "weighted to keep its swings as small as possible",
        "Risk-Parity": "weighted so no single asset dominates the risk",
    }.get(method, "")
    return ", ".join(p for p in (family_phrase, method_phrase) if p)


def at_a_glance_tiles(m):
    """The four headline tiles. The only place these numbers appear."""
    items = [
        ("Typical yearly growth", f"{m['ann_return']:.2%}"),
        ("How bumpy", f"{m['ann_vol']:.2%}"),
        ("Reward for risk", f"{m['sharpe']:.2f}"),
        ("Worst drop", f"{abs(m['max_drawdown']):.2%}"),
    ]
    cols = st.columns(4)
    for col, (label, value) in zip(cols, items):
        with col:
            st.markdown(
                f'<div style="background:#EAF6F0;border:1px solid #BFE8D4;'
                f'border-radius:14px;padding:0.85rem 1rem;min-height:92px;'
                f'box-sizing:border-box;display:flex;flex-direction:column;'
                f'justify-content:center;">'
                f'<div style="font-size:0.78rem;font-weight:700;'
                f'text-transform:uppercase;letter-spacing:0.05em;'
                f'color:#0F7B4E;">{label}</div>'
                f'<div style="font-size:1.25rem;font-weight:800;color:#05A167;">'
                f'{value}</div></div>',
                unsafe_allow_html=True,
            )


def why_fund(name, m):
    narr = {
        "Combined Min-Variance": (
            "Aims to protect capital by keeping swings small. Over the sample "
            "it averaged {ret:.1%} a year with volatility of just {vol:.1%} and "
            "a worst-ever drop of {dd:.1%} — the calmest ride in the combined "
            "family."
        ),
        "Combined Risk-Parity": (
            "Balances the 50 equities and 10 cryptocurrencies so that each "
            "contributes equally to risk — a middle ground. Moderate growth "
            "({ret:.1%}) with controlled volatility ({vol:.1%})."
        ),
        "Combined Max-Sharpe": (
            "Targets the highest return per unit of risk across all 60 assets. "
            "Best reward-for-risk of the combined funds (Sharpe {sharpe:.2f}) "
            "with strong growth ({ret:.1%})."
        ),
        "Equity Min-Variance": (
            "The calmest way to stay in stocks: it minimises risk within the "
            "50 US equities. Low volatility ({vol:.1%}) and a mild worst-ever "
            "drop ({dd:.1%}) in exchange for a steadier, more modest return "
            "({ret:.1%})."
        ),
        "Equity Risk-Parity": (
            "A balanced all-stock fund that spreads risk evenly across the 50 "
            "equities. Steady growth ({ret:.1%}) at controlled volatility "
            "({vol:.1%})."
        ),
        "Equity Max-Sharpe": (
            "The best pure-equity pick for reward per unit of risk (Sharpe "
            "{sharpe:.2f}): strong growth ({ret:.1%}) with moderate "
            "volatility ({vol:.1%})."
        ),
        "Crypto Min-Variance": (
            "Invests only in crypto, minimising risk within that volatile "
            "asset class. Huge upside ({ret:.1%}) but with very high "
            "volatility ({vol:.1%}) and a worst-ever drop of {dd:.1%}. Only "
            "suits very aggressive, long-horizon investors."
        ),
    }
    text = narr.get(name) or (
        "A systematically managed fund that targets a balanced mix of growth "
        "and risk. See the fact sheet for full details."
    )
    return text.format(ret=m["ann_return"], vol=m["ann_vol"],
                       dd=m["max_drawdown"], sharpe=m["sharpe"])


# ── NAVIGATION ──────────────────────────────────────────────────

st.set_page_config(page_title="Investra",
                   page_icon="assets/investra_icon.svg",
                   layout="wide")
st.markdown(THEME_CSS, unsafe_allow_html=True)
render_topbar()

PAGES = ["Home", "Find your fund", "Compare", "Fund fact sheet",
         "Simulate", "Build allocation", "Sentiment", "Analytics",
         "Dictionary"]

if "page" not in st.session_state:
    st.session_state["page"] = "Home"
if "recommended_fund" not in st.session_state:
    st.session_state["recommended_fund"] = None

st.radio("", PAGES, key="page", horizontal=True, label_visibility="collapsed")


# ═══════════════════════════════════════════════════════════════════
# PAGE: HOME
# ═══════════════════════════════════════════════════════════════════

def page_home():
    render_header("Investra")
    st.markdown(
        "**Smart, data-driven funds built from 50 US equities and 10 "
        "cryptocurrencies — find the one that fits you.**"
    )

    col_a, col_b = st.columns([1, 1])
    with col_a:
        st.button("🎯 Find your fund →", width="stretch", type="primary",
                  on_click=go_to, args=("Find your fund",))
    with col_b:
        st.button("📊 Browse all funds", width="stretch",
                  on_click=go_to, args=("Compare",))

    st.divider()
    st.subheader("How it works")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**1. Tell us about you**\n\nAnswer 4 quick questions about your goal, "
                    "timeline, and risk comfort.")
    with c2:
        st.markdown("**2. Get your match**\n\nWe recommend one of nine systematically "
                    "managed funds using transparent rules.")
    with c3:
        st.markdown("**3. Explore and allocate**\n\nCompare funds, read fact sheets, "
                    "and build your own blended portfolio.")

    st.divider()
    st.markdown(
        "**Who it's for:** Investors who want a transparent, data-driven approach "
        "to multi-asset investing — no financial jargon, no hidden fees."
    )
    st.caption(
        "This tool provides educational guidance, not financial advice. All figures "
        "are out-of-sample and read from precomputed results. "
        "No backtests or sentiment models run inside this app."
    )


# ═══════════════════════════════════════════════════════════════════
# PAGE: FIND YOUR FUND
# ═══════════════════════════════════════════════════════════════════

def page_find_my_fund():
    render_header("Find your fund")
    st.markdown("Answer 4 quick questions and we'll match you to a fund.")
    st.markdown("There are no wrong answers. Pick what feels true for you.")

    st.markdown(
        """
        <style>
        [data-testid="stColumn"] > [data-testid="stVerticalBlock"]
        > [data-testid="stLayoutWrapper"]
        > [data-testid="stVerticalBlock"] {
            min-height: 248px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    top_left, top_right = st.columns(2)
    with top_left:
        with st.container(border=True):
            st.markdown("**What's your main goal?**")
            st.caption("This sets how much you want growth versus keeping "
                       "your money safe.")
            q1 = st.radio(
                "", ["Protect my money", "Balanced growth", "Maximum growth"],
                key="f_q1", label_visibility="collapsed",
            )
    with top_right:
        with st.container(border=True):
            st.markdown("**How long do you plan to invest?**")
            st.caption("A longer time invested can ride out short term dips, "
                       "so it allows a bit more risk.")
            q2 = st.radio(
                "", ["Under 2 years", "2 to 5 years", "5+ years"],
                key="f_q2", label_visibility="collapsed",
            )

    bottom_left, bottom_right = st.columns(2)
    with bottom_left:
        with st.container(border=True):
            st.markdown("**If the market dropped 30%, what would you do?**")
            st.caption("This shows how you would react to a big fall, so we "
                       "do not give you more risk than you can sit through.")
            q3 = st.radio(
                "", ["Sell to protect what's left", "Hold and wait",
                     "Buy more while it's cheap"],
                key="f_q3", label_visibility="collapsed",
            )
    with bottom_right:
        with st.container(border=True):
            st.markdown("**How do you feel about crypto?**")
            st.caption("Crypto can swing a lot. This lets us include it or "
                       "leave it out of your match.")
            q4 = st.radio(
                "", ["Stick to stocks", "Include crypto"],
                key="f_q4", label_visibility="collapsed",
            )

    if st.button("See my match →", type="primary", width="stretch"):
        score_map = {"Protect my money": 0, "Balanced growth": 1, "Maximum growth": 2}
        horizon_map = {"Under 2 years": 0, "2 to 5 years": 1, "5+ years": 2}
        drop_map = {"Sell to protect what's left": 0, "Hold and wait": 1,
                    "Buy more while it's cheap": 2}

        total = score_map[q1] + horizon_map[q2] + drop_map[q3]

        if q4 == "Stick to stocks":
            if total <= 1:
                rec = "Equity Min-Variance"
            elif total <= 3:
                rec = "Equity Risk-Parity"
            else:
                rec = "Equity Max-Sharpe"
        elif total <= 1:
            rec = "Combined Min-Variance"
        elif total <= 3:
            rec = "Combined Risk-Parity"
        elif total <= 5:
            rec = "Combined Max-Sharpe"
        else:
            if horizon_map[q2] == 2 and drop_map[q3] == 2:
                rec = "Crypto Min-Variance"
            else:
                rec = "Combined Max-Sharpe"

        st.session_state["recommended_fund"] = rec
        st.session_state["risk_score"] = total
        st.session_state["crypto_pref"] = (q4 == "Include crypto")
        st.session_state["horizon_level"] = horizon_map[q2]

    rec = st.session_state.get("recommended_fund")
    if rec:
        st.divider()
        st.subheader(f"✨ Your match: {rec}")

        m = perf[perf["fund"] == rec].iloc[0]
        badge = risk_badge(m["ann_vol"])
        st.markdown(f"Risk level: {badge}")
        st.caption(f"Based on annualised volatility of {m['ann_vol']:.1%}")

        metric_row(m)
        st.markdown(why_fund(rec, m))
        st.caption("This is educational guidance, not financial advice.")

        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            st.button("📄 See full fact sheet", width="stretch",
                      on_click=go_to, args=("Fund fact sheet",))
        with col_b:
            st.button("📊 Compare with others", width="stretch",
                      on_click=go_to, args=("Compare",))
        with col_c:
            st.button("📈 Simulate this fund", width="stretch",
                      on_click=go_simulate, args=(rec,))
        with col_d:
            st.button("🔄 Retake quiz", width="stretch",
                      on_click=reset_match)


def suitability(fund_row, risk_score, crypto_pref, horizon_level,
                vol_min, vol_max):
    """Fit score from 0 to 100 and a one-line reason for a fund vs the user."""
    fund_vol = fund_row["ann_vol"]
    fund_risk6 = 6 * (fund_vol - vol_min) / (vol_max - vol_min)
    score = 100 * (1 - abs(risk_score - fund_risk6) / 6)
    is_crypto = str(fund_row["fund"]).startswith("Crypto")

    if not crypto_pref and is_crypto:
        score -= 50
    if crypto_pref and is_crypto and horizon_level == 0:
        score -= 30
    if risk_score <= 1 and fund_risk6 >= 4:
        score -= 20

    if not crypto_pref and is_crypto:
        reason = "Crypto — you preferred stocks only."
    elif ((crypto_pref and is_crypto and horizon_level == 0)
          or (risk_score <= 1 and fund_risk6 >= 4)):
        reason = "Bumpier than your comfort level."
    elif risk_score >= 5 and fund_risk6 <= 2:
        reason = "Likely too cautious for your goal."
    else:
        reason = "Matches your risk comfort."

    return int(max(0, min(100, round(score)))), reason


def render_fit_row(title, items, dim):
    if not items:
        return
    bar_color = "#9AA1A6" if dim else "#05A167"
    cards = []
    for s in items:
        cards.append(
            f'<div class="fit-card{" dim" if dim else ""}">'
            f'<div class="fit-card-name">{s["name"]}</div>'
            f'<div class="fit-bar-wrap">'
            f'<div class="fit-bar" style="width:{s["score"]}%;'
            f"background:{bar_color};\"></div></div>"
            f'<div class="fit-card-score">{s["score"]}/100</div>'
            f'<div class="fit-card-reason">{s["reason"]}</div>'
            f"</div>"
        )
    st.markdown(
        f'<div class="fit-row"><div class="fit-row-title">{title}</div>'
        f'<div class="fit-grid">{"".join(cards)}</div></div>',
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════
# PAGE: COMPARE
# ═══════════════════════════════════════════════════════════════════

def page_compare():
    render_header("Compare funds")
    st.caption("Annualised metrics — all figures are out-of-sample")
    render_fundname_popover()

    m_by_name = {r["fund"]: r for r in perf.to_dict("records")}
    fund_names = fund_names_ordered()

    # ── Personalized ranking (only after the quiz) ─────────
    risk_score = st.session_state.get("risk_score")
    rec = st.session_state.get("recommended_fund")
    if risk_score is not None:
        crypto_pref = st.session_state.get("crypto_pref", False)
        horizon_level = st.session_state.get("horizon_level", 1)
        vol_min = perf["ann_vol"].min()
        vol_max = perf["ann_vol"].max()

        scored = []
        for name in fund_names:
            score, reason = suitability(
                m_by_name[name], risk_score, crypto_pref, horizon_level,
                vol_min, vol_max)
            scored.append({"name": name, "score": score, "reason": reason})
        scored.sort(key=lambda s: -s["score"])

        if rec and any(s["name"] == rec for s in scored):
            match = next(s for s in scored if s["name"] == rec)
            st.markdown(
                f'<div class="match-banner">'
                f'<div class="match-banner-title">⭐ Your match: {rec} — '
                f"fit {match['score']}/100</div>"
                f'<div class="fit-bar-wrap">'
                f'<div class="fit-bar" style="width:{match["score"]}%;">'
                f"</div></div>"
                f'<div class="match-banner-sub">{match["reason"]}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )
            others = [s for s in scored if s["name"] != rec]
        else:
            others = scored

        render_fit_row("✅ Also good for you", others[:3], dim=False)
        render_fit_row("⬇️ Least suitable for you", others[-3:], dim=True)
    else:
        st.markdown(
            '<div class="quiz-prompt">💡 Take the quick quiz on "Find '
            'your fund" to see these funds ranked for you.</div>',
            unsafe_allow_html=True,
        )
        st.button("🎯 Take the quiz", on_click=go_to,
                  args=("Find your fund",))

    # ── Comfort-tier grouping ──────────────────────────────
    tiers = {
        "Conservative": ("🛡️ Safer & steadier", "#05A167",
                         "Smallest ups and downs. For peace of mind."),
        "Balanced": ("⚖️ Balanced", "#E8973A",
                     "More growth, a bumpier ride. The middle path."),
        "Growth": ("🚀 Higher risk & reward", "#E5484D",
                   "Big swings. Only money you can afford to lose."),
    }
    by_tier = {"Conservative": [], "Balanced": [], "Growth": []}
    for name in sorted(m_by_name, key=lambda n: m_by_name[n]["ann_vol"]):
        by_tier[fund_tier(m_by_name[name]["ann_vol"])].append(name)

    tier_col = []
    for tier, (title, color, desc) in tiers.items():
        tier_col.append(
            f'<div class="tier-col">'
            f'<div class="tier-head" style="border-top:4px solid {color};">'
            f'<div class="tier-head-title">{title}</div>'
            f'<div class="tier-head-desc">{desc}</div></div>'
        )
        for name in by_tier[tier]:
            m = m_by_name[name]
            explain = html.escape(explain_fund_name(name))
            tier_col.append(
                f'<div class="tier-fund">'
                f'<div class="tier-fund-name">{name}'
                f'<span class="fund-help" title="{explain}">?</span></div>'
                f'<div class="tier-fund-return" style="color:{color};">'
                f'{m["ann_return"]:.0%}</div>'
                f'<div class="tier-fund-drop">'
                f'worst drop {m["max_drawdown"]:.0%}</div>'
                f'</div>'
            )
        tier_col.append('</div>')

    st.markdown('<div class="tier-grid">' + "".join(tier_col) + "</div>",
                unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# PAGE: FUND FACT SHEET
# ═══════════════════════════════════════════════════════════════════

def page_fact_sheet():
    render_header("Fund fact sheet")

    fund_names = fund_names_ordered()
    default_idx = 0
    rec = st.session_state.get("recommended_fund")
    if rec and rec in fund_names:
        default_idx = fund_names.index(rec)

    selected = st.selectbox("Select a fund", fund_names, index=default_idx)

    m = perf[perf["fund"] == selected].iloc[0]
    badge = risk_badge(m["ann_vol"])

    st.subheader(selected)
    st.markdown(f"Risk level: {badge}")
    st.markdown(fund_description(selected))
    render_fundname_popover(selected)
    st.button("📈 Simulate this fund", type="primary",
              on_click=go_simulate, args=(selected,))

    ret = fund_ret[selected]
    w_series = wealth_series(ret)
    dd_series = drawdown_series(ret)

    st.subheader("At a glance")
    at_a_glance_tiles(m)

    st.subheader("How your money grew")
    excess = vs_cash.loc[vs_cash["fund"] == selected,
                         "excess_over_cash"].iloc[0]
    cash_last = cash_bm["cash_growth"].iloc[-1]
    fund_growth = m["growth_of_1"]

    tile_a, tile_b = st.columns(2)
    with tile_a:
        st.markdown(
            f'<div style="background:#EAF6F0;border:1px solid #BFE8D4;'
            f'border-radius:14px;padding:0.85rem 1rem;min-height:92px;'
            f'box-sizing:border-box;display:flex;flex-direction:column;'
            f'justify-content:center;">'
            f'<div style="font-size:0.78rem;font-weight:700;'
            f'text-transform:uppercase;letter-spacing:0.05em;'
            f'color:#0F7B4E;">In this fund</div>'
            f'<div style="font-size:1.25rem;font-weight:800;color:#05A167;">'
            f'$1 became ${fund_growth:.2f}</div></div>',
            unsafe_allow_html=True,
        )
    with tile_b:
        st.markdown(
            f'<div style="background:#F2F4F5;border:1px solid #E3E8EA;'
            f'border-radius:14px;padding:0.85rem 1rem;min-height:92px;'
            f'box-sizing:border-box;display:flex;flex-direction:column;'
            f'justify-content:center;">'
            f'<div style="font-size:0.78rem;font-weight:700;'
            f'text-transform:uppercase;letter-spacing:0.05em;'
            f'color:#5B666B;">In cash (savings)</div>'
            f'<div style="font-size:1.25rem;font-weight:800;color:#9AA1A6;">'
            f'$1 became ${cash_last:.2f}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        f'<div style="background:#05A167;border-radius:14px;padding:0.85rem '
        f'1rem;min-height:52px;box-sizing:border-box;display:flex;'
        f'align-items:center;color:#FFFFFF;font-weight:700;line-height:1.45;">'
        f'This fund beat cash by about {excess * 100:.1f} percent a year.</div>',
        unsafe_allow_html=True,
    )

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=cash_bm["date"], y=cash_bm["cash_growth"], mode="lines",
        name="In cash",
        line=dict(color="#9AA1A6", width=2, dash="dash"),
        hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=w_series.index, y=w_series.values, mode="lines",
        name=selected,
        line=dict(color="#05A167", width=3),
        fill="tonexty",
        fillcolor="#E8F6EF",
    ))
    fig.add_annotation(
        x=w_series.index[-1], y=fund_growth,
        text=f"Your fund ${fund_growth:.2f}",
        showarrow=False, xanchor="left", xshift=8,
        font=dict(color="#05A167", size=11), bgcolor="#FFFFFF",
    )
    fig.add_annotation(
        x=cash_bm["date"].iloc[-1], y=cash_last,
        text=f"In cash ${cash_last:.2f}",
        showarrow=False, xanchor="left", xshift=8,
        font=dict(color="#9AA1A6", size=11), bgcolor="#FFFFFF",
    )
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="white",
        plot_bgcolor="white",
        showlegend=False,
        hovermode="x unified",
        margin=dict(l=45, r=10, t=10, b=10),
        xaxis=dict(
            range=[w_series.index[0],
                   w_series.index[-1] + pd.Timedelta(days=15)],
            gridcolor="#E3E8EA", tickcolor="#9AA1A6",
            tickfont=dict(color="#5B666B"), zeroline=False,
        ),
        yaxis=dict(
            gridcolor="#E3E8EA", tickcolor="#9AA1A6",
            tickfont=dict(color="#5B666B"), zeroline=False,
        ),
    )
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    st.caption("Cash means a risk free savings rate, from the Kenneth "
               "French daily rate, over the same period. Past results do "
               "not guarantee the future.")

    st.subheader("The risk")

    max_dd = m["max_drawdown"]
    briefly = 1 + max_dd

    st.markdown(
        f'<div style="background:#FDF0EE;border:1px solid #F5C6C2;'
        f'border-radius:14px;padding:0.85rem 1rem;min-height:92px;'
        f'box-sizing:border-box;display:flex;flex-direction:column;'
        f'justify-content:center;">'
        f'<div style="font-size:0.78rem;font-weight:700;'
        f'text-transform:uppercase;letter-spacing:0.05em;'
        f'color:#C2302F;">$1 dipped to</div>'
        f'<div style="font-size:1.25rem;font-weight:800;color:#E5484D;">'
        f'${briefly:.2f}</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div style="background:#E5484D;border-radius:14px;padding:0.85rem '
        f'1rem;min-height:52px;box-sizing:border-box;display:flex;'
        f'align-items:center;color:#FFFFFF;font-weight:700;line-height:1.45;">'
        f'It fell about {abs(max_dd) * 100:.0f} percent from its high, then '
        f'recovered.</div>',
        unsafe_allow_html=True,
    )

    trough_date = dd_series.idxmin()
    trough_val = dd_series.min()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dd_series.index, y=dd_series.values, mode="lines",
        line=dict(color="#E5484D", width=2),
        fill="tozeroy",
        fillcolor="rgba(229,72,77,0.14)",
        hoverinfo="skip",
    ))
    fig.add_annotation(
        x=trough_date, y=trough_val,
        text=f"worst fall about {abs(max_dd) * 100:.0f} percent",
        showarrow=True, arrowhead=2, arrowcolor="#C2302F",
        ax=0, ay=-70, font=dict(color="#C2302F", size=11),
        bgcolor="#FFFFFF",
    )
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="white",
        plot_bgcolor="white",
        showlegend=False,
        hovermode="x unified",
        margin=dict(l=45, r=10, t=10, b=10),
        xaxis=dict(
            gridcolor="#E3E8EA", tickcolor="#9AA1A6",
            tickfont=dict(color="#5B666B"), zeroline=False,
        ),
        yaxis=dict(
            tickformat=".0%",
            gridcolor="#E3E8EA", tickcolor="#9AA1A6",
            tickfont=dict(color="#5B666B"), zeroline=False,
        ),
    )
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    st.caption("A drawdown is how far the fund fell from its previous "
               "high before it recovered.")

    st.subheader("Recent performance")
    trow = trailing[trailing["fund"] == selected].iloc[0]
    ret_tiles = [
        ("1 year", f"{trow['ret_1y']:.1%}"),
        ("3 years a year", f"{trow['ret_3y']:.1%}"),
    ]
    tile_row = st.columns(2)
    for col, (label, value) in zip(tile_row, ret_tiles):
        with col:
            st.markdown(
                f'<div style="background:#EAF6F0;border:1px solid #BFE8D4;'
                f'border-radius:14px;padding:0.85rem 1rem;min-height:92px;'
                f'box-sizing:border-box;display:flex;flex-direction:column;'
                f'justify-content:center;">'
                f'<div style="font-size:0.78rem;font-weight:700;'
                f'text-transform:uppercase;letter-spacing:0.05em;'
                f'color:#0F7B4E;">{label}</div>'
                f'<div style="font-size:1.25rem;font-weight:800;color:#05A167;">'
                f'{value}</div></div>',
                unsafe_allow_html=True,
            )
    st.caption("These are backtested returns over 2020 to 2023, shown for the "
               "periods our data covers. A 5 year figure is not available "
               "because the data spans about 3 years. Past results do not "
               "guarantee the future.")

    st.subheader("What it holds")
    sub = fund_w[fund_w["fund"] == selected].copy()
    sub["date"] = pd.to_datetime(sub["date"])
    latest_date = sub["date"].max()
    latest = sub[sub["date"] == latest_date].copy()
    hold = latest[latest["weight"] > 0].copy()
    hold = hold[hold["weight"].map("{:.2%}".format) != "0.00%"]
    hold = hold.sort_values("weight", ascending=False)
    if len(hold):
        hold["asset"] = hold["asset"].str.replace(r"^(EQ|CR)_", "", regex=True)
        hold["weight"] = hold["weight"].map("{:.2%}".format)
        st.dataframe(hold[["asset", "weight"]], width="stretch",
                     hide_index=True)
        st.caption(f"Target weights from rebalance on {latest_date.date()}")
    else:
        st.info("No holdings data available.")

    with st.expander("Technical detail"):
        pos = latest.loc[latest["weight"] > 0, "weight"]
        if len(pos):
            st.markdown(
                '<div class="explainer-card"><h3>Exact figures</h3>'
                f'<p>Typical yearly growth {m["ann_return"]:.4%}<br>'
                f'How bumpy {m["ann_vol"]:.4%}<br>'
                f'Reward for risk {m["sharpe"]:.4f}<br><br>'
                f'Share held in the top three assets '
                f'{pos.nlargest(3).sum():.1%}<br>'
                f'Herfindahl index of holdings {(pos ** 2).sum():.3f}'
                f'</p></div>',
                unsafe_allow_html=True,
            )


# ═══════════════════════════════════════════════════════════════════
# PAGE: BUILD ALLOCATION
# ═══════════════════════════════════════════════════════════════════

PRESETS = {
    "Conservative": {
        "Combined Min-Variance": 50,
        "Equity Min-Variance": 25,
        "Equity Risk-Parity": 25,
    },
    "Balanced": {
        "Combined Risk-Parity": 50,
        "Combined Max-Sharpe": 25,
        "Equity Max-Sharpe": 25,
    },
    "Growth": {
        "Combined Max-Sharpe": 60,
        "Crypto Min-Variance": 25,
        "Combined Risk-Parity": 15,
    },
}


def apply_preset(weights):
    for name in fund_names_ordered():
        st.session_state[f"alloc_{name}"] = weights.get(name, 0)


def apply_match():
    rec = st.session_state.get("recommended_fund")
    for name in fund_names_ordered():
        st.session_state[f"alloc_{name}"] = 100 if name == rec else 0


def page_allocate():
    render_header("Build your allocation")
    st.markdown(
        "An allocation is simply how you split your money across funds. "
        "Mixing funds that don't all move together can smooth out the ride "
        "— that's diversification, and it can lower your risk without "
        "giving up much return."
    )

    steps = [
        ("1", "Pick a starting point",
         "Tap a preset below, or \"Start from my match\" if you've taken "
         "the quiz."),
        ("2", "See how it could grow",
         "Your blended mix shows projected growth, risk, and a range of "
         "outcomes."),
        ("3", "Fine-tune (optional)",
         "Open \"Fine-tune each fund\" to adjust the exact weights "
         "yourself."),
    ]
    st.markdown(
        '<div class="scenario-grid">'
        + "".join(
            f'<div class="step-tile"><div class="step-num">Step {n}</div>'
            f'<div class="step-title">{t}</div>'
            f'<div class="step-text">{d}</div></div>'
            for n, t, d in steps
        )
        + "</div>",
        unsafe_allow_html=True,
    )

    rec = st.session_state.get("recommended_fund")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.button("🛡️ Conservative", width="stretch",
                  on_click=apply_preset, args=(PRESETS["Conservative"],))
    with col2:
        st.button("⚖️ Balanced", width="stretch",
                  on_click=apply_preset, args=(PRESETS["Balanced"],))
    with col3:
        st.button("🚀 Growth", width="stretch",
                  on_click=apply_preset, args=(PRESETS["Growth"],))
    with col4:
        if rec:
            st.button(f"⭐ Start from my match: {rec}", width="stretch",
                      on_click=apply_match)
        else:
            st.caption("_Take the quiz to unlock a match preset._")

    raw = {}
    total = 0
    with st.expander("⚙️ Fine-tune each fund"):
        for name in fund_names_ordered():
            raw[name] = st.slider(f"{name} (%)", 0, 100, 0, key=f"alloc_{name}")
            total += raw[name]

    if total == 0:
        st.markdown(
            '<div class="alloc-callout">👇 Pick a preset above to see your '
            "blended portfolio.</div>",
            unsafe_allow_html=True,
        )
        return

    weights = {k: v / total for k, v in raw.items()}
    st.caption(f"Sliders total {total:.0f}% — normalised to 100%.")

    named = [(name, w) for name, w in weights.items() if w > 0]
    fig = go.Figure(go.Pie(
        labels=[f"{name} — {w:.0%}" for name, w in named],
        values=[w for _, w in named],
        hole=0.55,
        textinfo="none",
        marker=dict(colors=[FUND_COLORS.get(name, "#1f77b4") for name, _ in named],
                    line=dict(color="#FFFFFF", width=2)),
        hovertemplate="<b>%{label}</b><extra></extra>",
    ))
    fig.update_layout(
        height=400,
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2,
                    xanchor="center", x=0.5, font=dict(size=11)),
        annotations=[
            dict(text="Your mix / 100%", showarrow=False,
                 font=dict(size=16, color="#14181B")),
        ],
    )
    st.plotly_chart(fig, width="stretch")

    w = pd.Series(weights)
    blended = fund_ret.mul(w, axis=1).sum(axis=1).dropna()
    ppy = 252
    ann_ret = (1 + blended).prod() ** (ppy / len(blended)) - 1
    ann_vol = blended.std() * ppy ** 0.5
    sharpe = (ann_ret - 0.0) / ann_vol if ann_vol > 0 else 0.0
    wealth = (1 + blended).cumprod()
    max_dd = ((wealth - wealth.cummax()) / wealth.cummax()).min()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Typical yearly growth", f"{ann_ret:.2%}",
              help=metric_help("Typical yearly growth"))
    c2.metric("How bumpy", f"{ann_vol:.2%}",
              help=metric_help("How bumpy"))
    c3.metric("Reward for risk", f"{sharpe:.2f}",
              help=metric_help("Reward for risk"))
    c4.metric("Worst-ever drop", f"{max_dd:.2%}",
              help=metric_help("Worst-ever drop"))

    growth_10k = wealth * 10_000
    fig = px.line(
        growth_10k, x=growth_10k.index, y=growth_10k.values,
        labels={"x": "Date", "y": "Portfolio Value ($)"},
    )
    fig.update_layout(showlegend=False, hovermode="x unified",
                      title="Growth of $10,000")
    st.plotly_chart(fig, width="stretch")

    # ── Projected growth (Monte Carlo) ────────────────────────────
    st.divider()
    st.subheader("Projected growth (Monte Carlo)")
    st.caption("Forward-looking projection built from the blend's "
               "return, volatility and diversification.")

    blend_mu, blend_sig, naive_sig = simulate.blend_stats(
        weights, fund_ret, perf, list(weights.keys()))
    blend_dd = simulate.blend_max_drawdown(
        weights, fund_ret, list(weights.keys()))

    pleft, pright = st.columns([1, 2])
    with pleft:
        sim_p0 = st.number_input("Initial investment ($)", min_value=0,
                                 value=1000, step=500, key="alloc_p0")
        sim_pmt = st.number_input("Monthly contribution ($)", min_value=0,
                                  value=100, step=50, key="alloc_pmt")
        sim_years = st.slider("Horizon (years)", 1, 15, 10, key="alloc_years")

        if blend_sig < naive_sig:
            st.caption(
                f"Your blend's volatility is {blend_sig:.1%}, lower than "
                f"the {naive_sig:.1%} weighted average of the funds on "
                "their own — diversification reduces risk.")
        if blend_sig > 0.40:
            st.warning("This is a high-volatility blend — the range of "
                       "outcomes is very wide. Treat the projection with "
                       "extra caution.")

    with pright:
        result = run_sim(sim_p0, sim_pmt, sim_years, blend_mu, blend_sig)
        st.pyplot(sim_figure(result, sim_years), width="stretch")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Likely value", f"${result['median'][-1]:,.0f}",
                  help=metric_help("Likely value"))
        c2.metric("Pessimistic", f"${result['p10'][-1]:,.0f}",
                  help=metric_help("Pessimistic"))
        c3.metric("Optimistic", f"${result['p90'][-1]:,.0f}",
                  help=metric_help("Optimistic"))
        c4.metric("Total contributed", f"${result['contributions'][-1]:,.0f}",
                  help=metric_help("Total contributed"))

        render_scenarios(sim_p0, blend_mu, blend_sig, blend_dd)

        st.caption("Projection assumes the blend repeats its 2021–2023 "
                   "return and volatility. This is a simulation, not a "
                   "guarantee — actual results will differ.")


# ═══════════════════════════════════════════════════════════════════
# PAGE: SENTIMENT
# ═══════════════════════════════════════════════════════════════════

# ── Sentiment gauge ─────────────────────────────────────────────

def sentiment_band(z):
    """Human label for a sector z-score versus its own normal.

    |z| < SENTIMENT_Z_NORMAL is "about normal", up to
    SENTIMENT_Z_UNUSUAL (inclusive) is "a bit above/below normal",
    beyond is "unusually positive/negative".
    """
    if pd.isna(z):
        return "About normal"
    if z > SENTIMENT_Z_UNUSUAL:
        return "Unusually positive"
    if z < -SENTIMENT_Z_UNUSUAL:
        return "Unusually negative"
    if z >= SENTIMENT_Z_NORMAL:
        return "A bit above normal"
    if z <= -SENTIMENT_Z_NORMAL:
        return "A bit below normal"
    return "About normal"


def sentiment_dot(band):
    """Traffic-light dot for a sentiment band (green/red/neutral)."""
    if band in ("Unusually positive", "A bit above normal"):
        return "🟢"
    if band in ("Unusually negative", "A bit below normal"):
        return "🔴"
    return "⚪"


SENTIMENT_ZONE_COLORS = {
    "Unusually negative": "#A61B2E",
    "A bit below normal": "#E5484D",
    "About normal": "#C7CDD2",
    "A bit above normal": "#0E9F6E",
    "Unusually positive": "#046B47",
}

# Gauge zones in standard deviations from a sector's own normal,
# red (negative) through grey (normal) to green (positive).
SENTIMENT_ZONES = [
    ("Unusually negative", -SENTIMENT_GAUGE_MAX, -SENTIMENT_Z_UNUSUAL),
    ("A bit below normal", -SENTIMENT_Z_UNUSUAL, -SENTIMENT_Z_NORMAL),
    ("About normal", -SENTIMENT_Z_NORMAL, SENTIMENT_Z_NORMAL),
    ("A bit above normal", SENTIMENT_Z_NORMAL, SENTIMENT_Z_UNUSUAL),
    ("Unusually positive", SENTIMENT_Z_UNUSUAL, SENTIMENT_GAUGE_MAX),
]


def _arc_points(v0, v1, radius=0.82, n=40):
    """Points along a 180-degree gauge arc between two 0-100 values."""
    angles = np.linspace(180 - v1 * 1.8, 180 - v0 * 1.8, n)
    return radius * np.cos(np.radians(angles)), radius * np.sin(np.radians(angles))


def _z_to_100(z):
    """Map a z-score in [-GAUGE, +GAUGE] onto the gauge's 0-100 arc."""
    z = float(np.clip(z, -SENTIMENT_GAUGE_MAX, SENTIMENT_GAUGE_MAX))
    return (z + SENTIMENT_GAUGE_MAX) / (2.0 * SENTIMENT_GAUGE_MAX) * 100.0


def render_sentiment_gauge(market_z):
    """Semicircular mood gauge driven by a market-wide sentiment z-score.

    The needle, the zone arcs and the headline all represent standard
    deviations from the sectors' own normal (z = 0 is a normal reading),
    so a raw-but-normal score reads "About normal" instead of "Positive".
    """
    display = sentiment_band(market_z)

    fig = go.Figure()
    for name, z0, z1 in SENTIMENT_ZONES:
        v0, v1 = _z_to_100(z0), _z_to_100(z1)
        x, y = _arc_points(v0, v1)
        fig.add_trace(go.Scatter(
            x=x, y=y, mode="lines",
            line=dict(color=SENTIMENT_ZONE_COLORS[name], width=24),
            hoverinfo="skip", showlegend=False,
        ))
        mid = (v0 + v1) / 2.0
        ang = np.radians(180 - mid * 1.8)
        lx, ly = 1.16 * np.cos(ang), 1.16 * np.sin(ang)
        anchor = "right" if mid < 40 else ("left" if mid > 60 else "center")
        fig.add_annotation(
            x=lx, y=ly, text=name, showarrow=False,
            xanchor=anchor, font=dict(size=11, color="#5B666B"),
        )

    needle = _z_to_100(market_z)
    nang = np.radians(180 - needle * 1.8)
    fig.add_trace(go.Scatter(
        x=[0, 0.62 * np.cos(nang)], y=[0, 0.62 * np.sin(nang)],
        mode="lines", line=dict(color="#14181B", width=3),
        hoverinfo="skip", showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=[0], y=[0], mode="markers",
        marker=dict(color="#14181B", size=9),
        hoverinfo="skip", showlegend=False,
    ))

    for xpos, text in [(-0.82, f"\u2212{SENTIMENT_GAUGE_MAX:g}\u03c3"),
                       (0.0, "0"), (0.82, f"+{SENTIMENT_GAUGE_MAX:g}\u03c3")]:
        fig.add_annotation(
            x=xpos, y=-0.20, text=text, showarrow=False,
            xanchor="center", yanchor="top",
            font=dict(size=11, color="#5B666B"),
        )

    fig.update_layout(
        showlegend=False, height=260,
        margin=dict(t=6, b=6, l=6, r=6),
        paper_bgcolor="white", plot_bgcolor="white",
    )
    fig.update_xaxes(range=[-1.6, 1.6], visible=False)
    fig.update_yaxes(range=[-0.4, 1.35], visible=False)

    st.markdown(
        f'<div style="text-align:center;font-size:1.35rem;font-weight:800;'
        f'color:{SENTIMENT_ZONE_COLORS.get(display, "#14181B")};'
        f'margin:0.15rem 0 0.1rem;">'
        f'How positive is the news right now? {html.escape(display)}</div>',
        unsafe_allow_html=True,
    )
    st.plotly_chart(fig, use_container_width=True,
                    config={"displayModeBar": False})
    st.caption("This shows how positive the news mood was, compared with its "
               "own normal, as of the latest date in our data (December "
               "2023). It is context, not a buy or sell signal.")
    with st.expander("How this is built"):
        st.write("Each news headline is scored with finVADER, which rates how "
                 "positive or negative its language is. The scores are "
                 "averaged for each sector and day. Each sector's score is "
                 "then standardised against its own history over the whole "
                 "period: 0 is that sector's normal, and +1 is one standard "
                 "deviation above it. The dial shows the market-wide reading "
                 "\u2014 the average across all sectors \u2014 so it reflects "
                 "whether the news is unusually positive relative to normal, "
                 "not just positive. It is context, not a buy or sell "
                 "signal.")


def page_sentiment():
    render_header("Sector sentiment index")

    # ── Step 1: market mood gauge ──────────────────────────
    latest = sent_idx.dropna(how="all").last_valid_index()
    z_cols = [c for c in sent_idx.columns if c.endswith("_z")]
    market_z = float(sent_idx.loc[latest, z_cols].mean())
    render_sentiment_gauge(market_z)

    # ── Step 2: explainer card ─────────────────────────────
    st.markdown(
        '<div class="explainer-card"><h3>How positive is the news, sector '
        "by sector?</h3><p>Every day, news is written about each company. "
        "We use a tool called VADER to score whether it sounds positive or "
        "negative, then average it within each sector. Because business "
        "news is usually mildly positive, we compare each sector's score "
        "with its own history, so the mood shows whether the news is "
        "unusual for that sector, not just positive.</p></div>",
        unsafe_allow_html=True,
    )

    # ── Step 3: latest sector mood table ───────────────────
    st.subheader("Sector mood right now")
    raw_cols = [c for c in sent_idx.columns if not c.endswith("_z")]
    ordered = sorted(raw_cols,
                     key=lambda c: sent_idx.loc[latest, f"{c}_z"],
                     reverse=True)
    rows_html = "".join(
        f"<tr><td>{col}</td><td>{sent_idx.loc[latest, col]:+.2f}</td>"
        f"<td>{sent_idx.loc[latest, f'{col}_z']:+.2f}</td>"
        f"<td>{sentiment_dot(sentiment_band(sent_idx.loc[latest, f'{col}_z']))} "
        f"{sentiment_band(sent_idx.loc[latest, f'{col}_z'])}</td></tr>"
        for col in ordered
    )
    st.markdown(
        '<table class="plain-table"><thead><tr><th>Sector</th>'
        "<th>Score</th><th>vs normal (z)</th><th>Mood</th></tr></thead>"
        f"<tbody>{rows_html}</tbody></table>",
        unsafe_allow_html=True,
    )
    st.caption(
        f"As of {latest:%d %b %Y}. Equity sectors only. Crypto has no "
        "news signal. Score is the average finVADER headline score; "
        "vs normal (z) shows how far from that sector's own average it is, "
        "in standard deviations.")

    # ── Step 4: does following the news help? ──────────────
    st.subheader("Does reacting to the news improve returns? "
                 "Not in our tests.")
    plain = {
        0.0: "Ignore it",
        0.5: "Follow a little",
        1.0: "Follow more",
        2.0: "Follow heavily",
    }
    rows_html = ""
    for k, label in plain.items():
        sub = ksweep[ksweep["k"] == k].iloc[0]
        if k == 0.0:
            cls, status = "row-best", "✅ Best"
        elif k == 2.0:
            cls, status = "row-worst", "❌ Worst"
        else:
            cls, status = "", ""
        rows_html += (
            f'<tr class="{cls}"><td>{label}</td>'
            f"<td>{sub['ann_return']:.1%}</td>"
            f"<td>{sub['sharpe']:.3f}</td><td>{status}</td></tr>"
        )
    st.markdown(
        '<table class="plain-table"><thead><tr>'
        '<th>How much the fund follows the news</th>'
        "<th>Typical yearly growth</th>"
        '<th>Reward for risk (Sharpe)</th><th>Status</th>'
        "</tr></thead><tbody>" + rows_html + "</tbody></table>",
        unsafe_allow_html=True,
    )
    st.caption("Reward for risk (Sharpe) is return per unit of risk, "
               "higher is better. Notice that following the news more "
               "lowered both the return and the reward for risk, so even "
               "an investor comfortable with more risk in exchange for "
               "higher returns would not have gained. These tests tilt "
               "the Equity Max-Sharpe fund toward good news sectors.")

    # ── Takeaway card ──────────────────────────────────────
    st.markdown(
        '<div class="takeaway-card"><strong>💡 What this means for '
        "you.</strong> In our tests, the more the fund reacted to the "
        "news, the slightly lower its reward for risk, and this pattern "
        "held under two different sentiment models. That does not mean "
        "news is worthless. It suggests public news is largely priced "
        "in by the time we read it. So we treat sentiment as background "
        "context, not a buy or sell signal. And because this is one "
        "analysis over one period, it is a reason to keep evaluating "
        "news signals carefully, rather than to bet on them. Following "
        "the news lowered both the typical yearly growth and the reward "
        "for risk, so no type of investor benefited from it.</div>",
        unsafe_allow_html=True,
    )

    # ── Expander: mood over time ───────────────────────────
    with st.expander("📈 See how the mood changed over time"):
        sectors = [c for c in sent_idx.columns if not c.endswith("_z")]
        selected = st.multiselect("Sectors", sectors, default=sectors[:3])
        raw = st.checkbox("Show the raw index, unsmoothed")

        if selected:
            if raw:
                plot_data = sent_idx[selected].dropna(how="all")
                value_label = "VADER Compound"
            else:
                plot_data = sent_idx[selected].rolling(21).mean().dropna(
                    how="all")
                value_label = "VADER Compound (21d MA)"
            fig = px.line(
                plot_data, x=plot_data.index, y=plot_data.columns,
                labels={"value": value_label, "index": "Date",
                        "variable": "Sector"},
            )
            fig.update_layout(hovermode="x unified")
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Select at least one sector from the dropdown.")

    # ── Expander: technical detail ─────────────────────────
    with st.expander("🔬 The technical detail"):
        st.caption("Before vs after. The base fund compared with the "
                   "same fund after a sentiment tilt is added.")
        fd = fusion.copy()
        for col in ["ann_return", "ann_vol", "max_drawdown"]:
            fd[col] = fd[col].map("{:.2%}".format)
        fd["sharpe"] = fd["sharpe"].map("{:.2f}".format)
        fd["growth_of_1"] = fd["growth_of_1"].map("${:.2f}".format)
        fd = fd.rename(columns={
            "fund": "Fund", "ann_return": "Typical yearly growth",
            "ann_vol": "How bumpy", "sharpe": "Reward for risk",
            "max_drawdown": "Worst-ever drop", "growth_of_1": "$1 became",
        })
        st.dataframe(fd, width="stretch", hide_index=True)


# ═══════════════════════════════════════════════════════════════════
# PAGE: SIMULATE
# ═══════════════════════════════════════════════════════════════════

def page_simulate():
    render_header("Fund growth simulator")
    st.caption("Monte Carlo projection from each fund's precomputed "
               "annualised return and volatility.")
    st.markdown(
        '<div class="fee-callout">'
        '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" '
        'stroke="#05A167" stroke-width="1.8" stroke-linecap="round" '
        'stroke-linejoin="round">'
        '<rect x="3" y="6" width="18" height="14" rx="3"/>'
        '<path d="M3 10h18"/>'
        '<circle cx="16.5" cy="15" r="1.2" fill="#05A167" stroke="none"/>'
        '</svg>'
        '<span>Management fee: 0.75 percent a year, charged on your balance. '
        'This projection is shown after the fee.</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    fund_names = fund_names_ordered()
    if "sim_fund" not in st.session_state:
        preselect = st.session_state.get("recommended_fund")
        st.session_state["sim_fund"] = (preselect if preselect in fund_names
                                        else fund_names[0])

    left, right = st.columns([1, 2])
    with left:
        fund = st.selectbox("Fund", fund_names, key="sim_fund")
        p0 = st.number_input("Initial investment ($)", min_value=0, value=1000,
                             step=500, key="sim_p0")
        pmt = st.number_input("Monthly contribution ($)", min_value=0,
                              value=100, step=50, key="sim_pmt")
        years = st.slider("Horizon (years)", 1, 15, 10, key="sim_years")

        m = perf[perf["fund"] == fund].iloc[0]
        st.caption(f"{m['ann_return']:.1%} a year, volatility "
                   f"{m['ann_vol']:.1%}")
        if m["ann_vol"] > 0.40:
            st.warning("This is a high-volatility fund. The range of "
                       "outcomes is very wide. Treat the projection with "
                       "extra caution.")

    with right:
        net_return = m["ann_return"] - MANAGEMENT_FEE
        result = run_sim(p0, pmt, years, net_return, m["ann_vol"])
        gross_result = run_sim(p0, pmt, years, m["ann_return"], m["ann_vol"])
        fee_total = gross_result["median"][-1] - result["median"][-1]
        st.pyplot(sim_figure(result, years), width="stretch")

        if "wealth" in result:
            final_values = result["wealth"][:, -1]
            contributed_total = result["contributions"][-1]
            pct_below = 100.0 * (final_values < contributed_total).mean()
            st.caption(f"In about {pct_below:.0f}% of futures you end with "
                       f"less than the ${contributed_total:,.0f} you put in.")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Likely value", f"${result['median'][-1]:,.0f}",
                  help=metric_help("Likely value"))
        c2.metric("Pessimistic", f"${result['p10'][-1]:,.0f}",
                  help=metric_help("Pessimistic"))
        c3.metric("Optimistic", f"${result['p90'][-1]:,.0f}",
                  help=metric_help("Optimistic"))
        c4.metric("Total contributed", f"${result['contributions'][-1]:,.0f}",
                  help=metric_help("Total contributed"))

        st.markdown(f"Over these **{years} years**, the management fee would "
                    f"total about **${fee_total:,.0f}**.")

        render_scenarios(p0, net_return, m["ann_vol"], m["max_drawdown"])

        st.caption("This projection is after Investra's management fee. The "
                   "historical figures on the fund fact sheet are shown before "
                   "fees. Past results do not guarantee the future.")


# ═══════════════════════════════════════════════════════════════════
# PAGE: DICTIONARY
# ═══════════════════════════════════════════════════════════════════

def page_dictionary():
    render_header("Dictionary")
    st.caption("Plain-English definitions of every term used in Investra — "
               "the same ones shown in the '?' tooltips across the app.")
    query = st.text_input(
        "Search terms",
        placeholder="e.g. volatility, Sharpe, diversification",
        label_visibility="collapsed",
    ).strip().lower()
    for category, terms in GLOSSARY.items():
        shown = {t: d for t, d in terms.items()
                 if not query or query in t.lower() or query in d.lower()}
        if not shown:
            continue
        st.subheader(category)
        html_cards = ['<div class="dict-grid">']
        for term, definition in shown.items():
            html_cards.append(
                f'<div class="dict-card"><div class="dict-term">{term}</div>'
                f'<div class="dict-def">{definition}</div></div>')
        html_cards.append("</div>")
        st.markdown("".join(html_cards), unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# PAGE: ANALYTICS
# ═══════════════════════════════════════════════════════════════════

def efficient_frontier_figure(ef_df, perf_df):
    """Efficient frontier line plus the nine funds as tier-coloured dots."""
    tier_colors = {
        "Conservative": "#05A167",
        "Balanced": "#E8973A",
        "Growth": "#E5484D",
    }
    label_offsets = {
        "Equity Min-Variance":    (-0.030, -0.022),
        "Combined Min-Variance":  (-0.028, 0.030),
        "Equity Risk-Parity":     (0.028, -0.012),
        "Combined Risk-Parity":   (-0.030, 0.010),
        "Equity Max-Sharpe":      (0.035, 0.004),
        "Combined Max-Sharpe":    (0.012, 0.006),
        "Crypto Min-Variance":    (0.0, -0.016),
        "Crypto Max-Sharpe":      (-0.010, -0.012),
        "Crypto Risk-Parity":     (-0.010, 0.010),
    }

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ef_df["vol"], y=ef_df["target_return"], mode="lines",
        name="Efficient frontier", line=dict(color="#0F7B4E", width=3),
        hoverinfo="skip"))

    data = perf_df.copy()
    data["tier"] = data["ann_vol"].map(fund_tier)
    for tier, color in tier_colors.items():
        sub = data[data["tier"] == tier]
        if not len(sub):
            continue
        fig.add_trace(go.Scatter(
            x=sub["ann_vol"], y=sub["ann_return"], mode="markers",
            name=tier, text=sub["fund"],
            marker=dict(size=15, color=color, opacity=0.9,
                        line=dict(color="#FFFFFF", width=1.5)),
            hovertemplate=("<b>%{text}</b><br>"
                           "volatility per year %{x:.0%}<br>"
                           "typical yearly growth %{y:.0%}<extra></extra>"),
        ))

    for _, row in data.iterrows():
        name = row["fund"]
        dx, dy = label_offsets.get(name, (0.0, 0.0))
        x, y = row["ann_vol"] + dx, row["ann_return"] + dy
        xanchor = "center" if abs(dx) < 1e-9 else ("left" if dx > 0 else "right")
        yanchor = "middle" if abs(dy) < 1e-9 else ("bottom" if dy > 0 else "top")
        fig.add_annotation(x=x, y=y, text=name, showarrow=False,
                           xanchor=xanchor, yanchor=yanchor,
                           font=dict(color="#5A6169", size=11))

    fig.update_layout(
        template="plotly_white",
        plot_bgcolor="#FFFFFF",
        margin=dict(l=50, r=30, t=30, b=45),
        xaxis=dict(
            title=dict(text="Volatility per year",
                       font=dict(color="#8A9198", size=12)),
            range=[0, 1.12],
            showgrid=False, zeroline=False, tickformat=".0%",
            tickfont=dict(color="#AEB4B9", size=11),
        ),
        yaxis=dict(
            title=dict(text="Typical yearly growth",
                       font=dict(color="#8A9198", size=12)),
            showgrid=True, gridcolor="#EEF2F4", gridwidth=1, zeroline=False,
            tickformat=".0%",
            tickfont=dict(color="#AEB4B9", size=11),
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="left", x=0, font=dict(color="#14181B", size=12)),
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor="#E3E8EA",
                        font=dict(color="#14181B", size=12)),
        font=dict(color="#14181B"),
    )
    return fig


def correlation_heatmap(corr):
    """Green heatmap of the fund return correlations, values shown."""
    names = list(corr.index)
    rows = list(reversed(names))
    z = corr.values[::-1]

    fig = go.Figure(go.Heatmap(
        z=z, x=names, y=rows, colorscale="Greens", zmin=0.0, zmax=1.0,
        colorbar=dict(title=dict(text="Correlation",
                                 font=dict(color="#8A9198", size=12)),
                      tickfont=dict(color="#AEB4B9", size=11),
                      outlinewidth=0),
        hovertemplate="<b>%{y}</b> with <b>%{x}</b>: %{z:.2f}<extra></extra>",
    ))
    for i, name_y in enumerate(rows):
        for j, name_x in enumerate(names):
            v = float(z[i][j])
            fig.add_annotation(
                x=name_x, y=name_y, text=f"{v:.2f}", showarrow=False,
                font=dict(color=("#FFFFFF" if v >= 0.6 else "#14181B"),
                          size=11),
            )
    fig.update_layout(
        template="plotly_white", paper_bgcolor="white", plot_bgcolor="white",
        height=560, margin=dict(l=10, r=10, t=20, b=90),
        xaxis=dict(tickangle=-45, tickfont=dict(color="#5B666B", size=12),
                   gridcolor="#EEF2F4", zeroline=False),
        yaxis=dict(tickfont=dict(color="#5B666B", size=12),
                   gridcolor="#EEF2F4", zeroline=False),
    )
    return fig


def page_analytics():
    render_header("Analytics")
    st.markdown("Analytics. The methods and evidence behind the funds, "
                "for a more experienced investor.")

    st.subheader("Efficient frontier and our funds")
    st.plotly_chart(efficient_frontier_figure(efficient_frontier, perf),
                    width="stretch", config={"displayModeBar": False})
    st.caption("The frontier is the best in sample tradeoff. Our funds are "
               "out of sample, so they generally sit inside it. Small "
               "deviations reflect the difference between the estimation "
               "period and the live period.")

    st.subheader("Full metrics table")
    tbl = perf.set_index("fund").loc[fund_names_ordered()].reset_index()
    tbl = tbl.rename(columns={
        "fund": "Fund",
        "ann_return": "Typical yearly growth",
        "ann_vol": "How bumpy",
        "sharpe": "Reward for risk",
        "max_drawdown": "Worst drop",
        "growth_of_1": "$1 became",
    })
    for col in ("Typical yearly growth", "How bumpy", "Worst drop"):
        tbl[col] = tbl[col].map("{:.2%}".format)
    tbl["Reward for risk"] = tbl["Reward for risk"].map("{:.2f}".format)
    tbl["$1 became"] = tbl["$1 became"].map("${:.2f}".format)
    st.dataframe(tbl, width="stretch", hide_index=True)
    st.caption("Out of sample backtest over 2020 to 2023, annualised and "
               "shown before fees.")
    st.markdown("The funds form a clear risk and return ladder. The minimum "
                "variance funds are the steadiest with the lowest returns, "
                "while the crypto funds carry the highest returns and the "
                "deepest falls.")

    st.subheader("How the funds move together")
    st.plotly_chart(correlation_heatmap(fund_corr), width="stretch",
                    config={"displayModeBar": False})
    st.caption("Correlation runs from 0 to 1. A value close to 1 means "
               "the two funds move together, close to 0 means they move "
               "independently.")
    st.markdown("The crypto funds move fairly independently of the equity "
                "funds, with correlations around 0.2 to 0.3, which is why "
                "blending them into the combined funds reduces risk.")

    st.subheader("Sentiment deep dive")
    st.markdown("The k parameter is the tilt strength, how hard the fund "
                "leans on sentiment. k = 0 ignores news entirely, higher k "
                "follows it more.")
    k0 = ksweep[ksweep["k"] == 0].iloc[0]
    worst = ksweep.loc[ksweep["sharpe"].idxmin()]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ksweep["k"], y=ksweep["sharpe"], mode="lines",
        line=dict(color="#05A167", width=3), showlegend=False,
        hoverinfo="skip"))
    fig.add_trace(go.Scatter(
        x=ksweep["k"], y=ksweep["sharpe"], mode="markers",
        marker=dict(size=9, color="#05A167"), showlegend=False,
        hovertemplate="k=%{x}<br>Sharpe %{y:.3f}<extra></extra>"))
    fig.add_trace(go.Scatter(
        x=[k0["k"]], y=[k0["sharpe"]], mode="markers",
        marker=dict(size=15, color="#05A167",
                    line=dict(color="#FFFFFF", width=2)),
        showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(
        x=[worst["k"]], y=[worst["sharpe"]], mode="markers",
        marker=dict(size=15, color="#E5484D",
                    line=dict(color="#FFFFFF", width=2)),
        showlegend=False, hoverinfo="skip"))
    fig.update_layout(
        height=380,
        template="plotly_white",
        plot_bgcolor="#FFFFFF",
        margin=dict(l=55, r=30, t=40, b=45),
        yaxis=dict(range=[0.70, 0.755],
                   title=dict(text="Sharpe ratio",
                              font=dict(color="#8A9198", size=12)),
                   gridcolor="#EEF2F4", gridwidth=1, zeroline=False,
                   tickfont=dict(color="#AEB4B9", size=11)),
        xaxis=dict(title=dict(text="Tilt strength (k)",
                              font=dict(color="#8A9198", size=12)),
                   showgrid=False, zeroline=False,
                   tickfont=dict(color="#AEB4B9", size=11)),
        annotations=[
            dict(x=k0["k"], y=k0["sharpe"], text="Best: no sentiment",
                 showarrow=True, arrowhead=0, ax=0, ay=-30,
                 font=dict(color="#05A167", size=12, weight="bold")),
            dict(x=worst["k"], y=worst["sharpe"], text="Worst",
                 showarrow=True, arrowhead=0, ax=0, ay=30,
                 font=dict(color="#E5484D", size=12, weight="bold")),
        ],
    )
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    st.markdown("> Reacting to the news did not improve performance in our "
                "tests. Public news is largely priced in by the time we read "
                "it, so we treat sentiment as background context. One "
                "analysis over one period is a reason to keep evaluating "
                "news signals, not to bet on them.")

    st.subheader("finVADER versus VADER")
    st.caption("The same headlines were scored two ways. finVADER extends "
               "VADER with finance and crypto terms.")
    lc = load_lexicon_comparison().rename(columns={
        "model": "Model",
        "mean_compound": "Average score",
        "share_near_zero": "Share near neutral",
        "corr_with_vader": "Correlation with VADER",
    })
    lc["Average score"] = lc["Average score"].map("{:.3f}".format)
    lc["Share near neutral"] = lc["Share near neutral"].map("{:.1%}".format)
    lc["Correlation with VADER"] = lc["Correlation with VADER"].map(
        "{:.2f}".format)
    st.dataframe(lc, width="stretch", hide_index=True)
    st.caption("finVADER is the model behind the sentiment index on the "
               "Sentiment page. It flags more headlines as neutral than "
               "general VADER does.")

    latest_sent = sent_idx.dropna(how="all").last_valid_index()
    z_cols = [c for c in sent_idx.columns if c.endswith("_z")]
    market_z = float(sent_idx.loc[latest_sent, z_cols].mean())
    st.markdown(f"The sentiment gauge on the Sentiment page standardises each "
                f"sector's news score against its own history and then averages "
                f"the sectors, so the dial reads in standard deviations from "
                f"normal. The latest standardised reading is "
                f"**{market_z:+.2f}** ({sentiment_band(market_z)}), so the news "
                f"mood in December 2023 was about normal for its own history.")


# ═══════════════════════════════════════════════════════════════════
# ROUTER
# ═══════════════════════════════════════════════════════════════════

{
    "Home": page_home,
    "Find your fund": page_find_my_fund,
    "Compare": page_compare,
    "Fund fact sheet": page_fact_sheet,
    "Simulate": page_simulate,
    "Build allocation": page_allocate,
    "Sentiment": page_sentiment,
    "Analytics": page_analytics,
    "Dictionary": page_dictionary,
}[st.session_state["page"]]()

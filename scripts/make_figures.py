"""Generate the six required exhibits from precomputed CSVs. No recomputation.

Usage:
    python scripts/make_figures.py

Reads from results/data/ and results/tables/.
Writes PNGs to results/figures/.

Every figure shares the app's green design system: a white background, a
bold plain-English takeaway title, a muted subtitle (units + sample period),
a small source line, light horizontal gridlines only, and no top/right
spines. Palette: primary green #05A167, fill tint #E8F6EF, secondary amber
#E8973A, coral #E5484D. Tiers: Conservative green / Balanced amber / Growth
coral.
"""
import pathlib

import matplotlib
matplotlib.use("Agg")

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
from matplotlib.patches import Rectangle

RESULTS = pathlib.Path("results")
DATA = RESULTS / "data"
TABLES = RESULTS / "tables"
FIGURES = RESULTS / "figures"

SOURCE = "Source: my out-of-sample backtest. Illustrative."

# ── Design system ─────────────────────────────────────────
INK = "#14181B"
MUTED = "#6B7378"
GRID = "#EEF2F4"
LINE = "#E3E8EA"
GREY = "#C7CECF"
PRIMARY = "#05A167"
PRIMARY_DARK = "#0B6E4F"
FILL = "#E8F6EF"
AMBER = "#E8973A"
CORAL = "#E5484D"

TIER_COLORS = {
    "Conservative": PRIMARY,
    "Balanced": AMBER,
    "Growth": CORAL,
}

FONT_STACK = ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"]

plt.rcParams.update({
    "font.family": FONT_STACK,
    "text.color": INK,
    "axes.labelcolor": INK,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
    "axes.facecolor": "white",
})


def green_style(title, subtitle, source=SOURCE, ax_rect=(0.10, 0.16, 0.86, 0.62),
                figsize=(9.5, 5.6)):
    """Figure with the shared green header; return (fig, [ax])."""
    fig = plt.figure(figsize=figsize)

    fig.add_artist(Rectangle(
        (0.10, 0.862), 0.006, 0.055, facecolor=PRIMARY, edgecolor="none",
        transform=fig.transFigure, zorder=5,
    ))
    fig.text(0.115, 0.885, title, ha="left", va="center",
             fontsize=15.5, fontweight="bold", color=INK)
    fig.text(0.115, 0.848, subtitle, ha="left", va="top",
             fontsize=9.5, color=MUTED)
    fig.text(0.10, 0.032, source, ha="left", va="bottom",
             fontsize=8, color=MUTED)

    ax = fig.add_axes(ax_rect)
    _style_axes(ax)
    return fig, [ax]


def panels_style(title, subtitle, source=SOURCE, n=3,
                 figsize=(10.8, 5.6)):
    """Figure with the shared header and n side-by-side panels."""
    fig = plt.figure(figsize=figsize)

    fig.add_artist(Rectangle(
        (0.10, 0.862), 0.006, 0.055, facecolor=PRIMARY, edgecolor="none",
        transform=fig.transFigure, zorder=5,
    ))
    fig.text(0.115, 0.885, title, ha="left", va="center",
             fontsize=15.5, fontweight="bold", color=INK)
    fig.text(0.115, 0.848, subtitle, ha="left", va="top",
             fontsize=9.5, color=MUTED)
    fig.text(0.10, 0.032, source, ha="left", va="bottom",
             fontsize=8, color=MUTED)

    width = 0.27
    gap = 0.03
    axes = []
    for i in range(n):
        ax = fig.add_axes([0.10 + i * (width + gap), 0.16, width, 0.62])
        _style_axes(ax)
        axes.append(ax)
    return fig, axes


def _style_axes(ax):
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_color(LINE)
        ax.spines[sp].set_linewidth(0.9)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(colors=MUTED, labelsize=9.5)


def _save(fig, name):
    FIGURES.mkdir(parents=True, exist_ok=True)
    path = FIGURES / name
    fig.savefig(path, dpi=300, bbox_inches="tight", pad_inches=0.04,
                facecolor="white")
    plt.close(fig)
    print(f"  Saved {name}")


def _year_ticks(ax):
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))


def _green_palette(n):
    """n distinct green-family colours, darkest first."""
    base = [
        "#0B6E4F", "#127A4A", "#1D8A5E", "#239B74", "#2EAD8A", "#3EBB8E",
        "#5CC89A", "#7BD3A9", "#9ADEB8", "#B7E8CB", "#D2F1E1", "#E8F6EF",
    ]
    return base[:n] + [GREY] * (n - len(base))


def _family_of(name):
    return name.split(" ", 1)[0]


def _method_of(name):
    return name.split(" ", 1)[1]


def fig1_growth_of_1(fund_returns):
    families = ["Equity", "Crypto", "Combined"]
    title = "Crypto grew far more, and fell far harder"
    subtitle = ("What $1 invested in each fund grew to, all returns "
                "reinvested. Log scale, so equal vertical gaps mean equal "
                "percentage moves. Sample: Oct 2020 – Dec 2023.")
    method_colors = {
        "Min-Variance": PRIMARY,
        "Risk-Parity": AMBER,
        "Max-Sharpe": CORAL,
    }
    fig, axes = panels_style(title, subtitle)

    for ax, family in zip(axes, families):
        _year_ticks(ax)
        ax.set_title(family, fontsize=11, fontweight="bold", color=INK,
                     pad=8)
        ax.set_yscale("log")
        ax.yaxis.set_major_locator(
            mticker.LogLocator(base=10.0, subs=(1.0, 2.0, 5.0)))
        ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda v, _: f"{v:g}"))

        names = [c for c in fund_returns.columns
                 if _family_of(c) == family]
        finals = {}
        curves = {}
        for name in names:
            w = (1 + fund_returns[name].dropna()).cumprod()
            curves[name] = w
            finals[name] = w.iloc[-1]

        lo, hi = min(finals.values()), max(finals.values())
        ax.set_ylim(lo * 0.6, hi * 1.4)

        for name, w in curves.items():
            ax.plot(w.index, w.values, color=method_colors[_method_of(name)],
                    linewidth=2.0, zorder=3)

        order = sorted(names, key=lambda n: finals[n])
        offsets = [-18, 0, 18]
        for name, dy in zip(order, offsets):
            w = curves[name]
            ax.annotate(f"{name} x{finals[name]:.1f}",
                        xy=(w.index[-1], w.iloc[-1]),
                        xytext=(8, dy), textcoords="offset points",
                        ha="left", va="center", fontsize=8.5, color=INK,
                        fontweight="bold", annotation_clip=False)

        ax.set_xlim(w.index[0] - pd.Timedelta(days=30),
                    w.index[-1] + pd.Timedelta(days=500))

    axes[0].set_ylabel("Growth of $1 (log scale)")
    _save(fig, "01_growth_of_1.png")


def fig2_drawdown(fund_returns):
    funds = ["Combined Min-Variance", "Combined Risk-Parity",
             "Combined Max-Sharpe"]
    dd = {}
    for fund in funds:
        w = (1 + fund_returns[fund].dropna()).cumprod()
        dd[fund] = (w / w.cummax() - 1) * 100

    deepest = min(funds, key=lambda f: dd[f].min())
    title = (f"{deepest} had the deepest worst-case loss, "
             f"about {abs(dd[deepest].min()):.0f}%")
    subtitle = ("Drawdown = the fall from a previous peak, %. The three "
                "combined funds only, so the scale stays readable; the "
                "deepest is highlighted. Sample: Oct 2020 – Dec 2023.")
    fig, [ax] = green_style(title, subtitle)
    _year_ticks(ax)
    ax.set_ylabel("Drawdown (%)")

    for fund in funds:
        if fund == deepest:
            ax.fill_between(dd[fund].index, dd[fund].values, 0,
                            color=FILL, linewidth=0, zorder=2)
            ax.plot(dd[fund].index, dd[fund].values, color=CORAL,
                    linewidth=2.2, zorder=3)
        else:
            ax.plot(dd[fund].index, dd[fund].values, color=GREY,
                    linewidth=1.4, zorder=2)
    ax.axhline(0, color=LINE, linewidth=0.9, zorder=1)
    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))

    all_min = min(d.min() for d in dd.values())
    ax.set_ylim(all_min - 6, 2)

    trough_x, trough_y = dd[deepest].idxmin(), dd[deepest].min()
    ax.annotate(f"worst drop {abs(trough_y):.0f}%",
                xy=(trough_x, trough_y), xytext=(44, 8),
                textcoords="offset points",
                fontsize=9.5, fontweight="bold", color=CORAL,
                arrowprops=dict(arrowstyle="->", color=CORAL, lw=1.2),
                annotation_clip=False)
    _save(fig, "02_drawdown.png")


def fig3_weights_over_time(fund_weights):
    fund = "Combined Max-Sharpe"
    title = "One fund, many names, but a few dominate"
    subtitle = ("Target weight of each holding in Combined Max-Sharpe at "
                "each monthly rebalance, % of the portfolio, stacked. The "
                "12 largest holdings are shown individually; the other 48 "
                "are grouped as Other. Sample: Jan 2021 – Dec 2023.")
    fig, [ax] = green_style(title, subtitle,
                            ax_rect=(0.10, 0.16, 0.64, 0.62),
                            figsize=(11.0, 5.6))
    _year_ticks(ax)
    ax.set_ylabel("Share of portfolio (%)")

    sub = fund_weights[fund_weights["fund"] == fund].copy()
    wide = sub.pivot(index="date", columns="asset", values="weight").fillna(0)
    wide.index = pd.to_datetime(wide.index)
    wide = wide.sort_index()

    order = wide.mean().sort_values(ascending=False)
    top = order.index[:12].tolist()
    wide["Other"] = wide[order.index[12:]].sum(axis=1)
    cols = top + ["Other"]
    data = wide[cols] * 100

    palette = _green_palette(len(cols))
    ax.stackplot(data.index, data[cols].T,
                 labels=[_asset_label(c) for c in cols],
                 colors=palette, linewidth=0)
    ax.set_ylim(0, 100)
    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.legend(loc="center left", bbox_to_anchor=(1.005, 0.5), frameon=False,
              fontsize=8, ncol=2)
    _save(fig, "03_weights_over_time.png")


def fig4_sharpe_bar(perf_metrics):
    best = perf_metrics.loc[perf_metrics["sharpe"].idxmax()]
    title = (f"{best['fund']} earned the most reward per unit of risk, "
             f"Sharpe {best['sharpe']:.2f}")
    subtitle = ("Sharpe ratio = annualised return ÷ volatility; higher is "
                "better. Bars are coloured by risk tier and the best is "
                "highlighted. Sample: out-of-sample backtest, each fund "
                "from its first live date.")
    fig, [ax] = green_style(title, subtitle)
    ax.set_xlabel("Sharpe ratio")

    df = perf_metrics.sort_values("sharpe", ascending=False)
    tier_colors = []
    for _, row in df.iterrows():
        tier_colors.append(TIER_COLORS[fund_tier(row["ann_vol"])])
    colors = [PRIMARY if f == best["fund"] else c
              for f, c in zip(df["fund"], tier_colors)]
    edge = [PRIMARY_DARK if f == best["fund"] else "none"
            for f in df["fund"]]

    bars = ax.barh(range(len(df)), df["sharpe"], color=colors, height=0.62,
                   edgecolor=edge, linewidth=1.5, zorder=3)

    for bar, val, is_best in zip(bars, df["sharpe"],
                                 df["fund"] == best["fund"]):
        ax.annotate(f"{val:.2f}",
                    xy=(val, bar.get_y() + bar.get_height() / 2),
                    xytext=(5, 0), textcoords="offset points",
                    ha="left", va="center", fontsize=9.5,
                    fontweight="bold",
                    color=PRIMARY_DARK if is_best else MUTED)

    ax.set_yticks(range(len(df)))
    ax.set_yticklabels(df["fund"], fontsize=9.5)
    ax.invert_yaxis()
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:g}"))
    ax.set_xlim(0, df["sharpe"].max() * 1.28 + 0.10)
    _save(fig, "04_sharpe_bar.png")


def fig5_sentiment_index(sector_idx):
    title = "News mood: real estate and utilities cheered the most"
    subtitle = ("News sentiment from -1 (very negative) to +1 (very "
                "positive), 21-day rolling average. RealEstate and "
                "Utilities are highlighted; the other sectors are grey. "
                "Sample: Jan 2020 – Dec 2023.")
    fig, [ax] = green_style(title, subtitle)
    _year_ticks(ax)
    ax.set_ylabel("Sentiment score")

    r = sector_idx[sector_idx.columns[~sector_idx.columns.str.endswith("_z")]]
    r = r.rolling(21).mean()
    highlights = {"RealEstate": PRIMARY, "Utilities": AMBER}
    for col in r.columns:
        color = highlights.get(col, GREY)
        lw = 2.2 if col in highlights else 1.1
        ax.plot(r.index, r[col], color=color, linewidth=lw,
                zorder=3 if col in highlights else 2)

    for col, color in highlights.items():
        last = r[col].dropna().index[-1]
        val = r[col].dropna().iloc[-1]
        ax.annotate(col, xy=(last, val), xytext=(8, 0),
                    textcoords="offset points", ha="left", va="center",
                    fontsize=9, fontweight="bold", color=color,
                    annotation_clip=False)

    ax.axhline(0, color=LINE, linewidth=0.9, zorder=1)
    ax.set_xlim(r.index[0] - pd.Timedelta(days=30),
                r.index[-1] + pd.Timedelta(days=400))
    all_min = r.dropna(how="all").min().min()
    all_max = r.dropna(how="all").max().max()
    pad = max(0.05, (all_max - all_min) * 0.08)
    ax.set_ylim(all_min - pad, all_max + pad)
    _save(fig, "05_sentiment_index.png")


def fig6_fusion_ksweep(fusion_ksweep):
    title = "Adding sentiment lowers reward-for-risk"
    subtitle = ("Sharpe ratio of Equity Max-Sharpe as the sentiment-tilt "
                "strength k rises; k = 0 is the no-sentiment base. The "
                "decline is small but consistent. Sample: out-of-sample "
                "backtest.")
    fig, [ax] = green_style(title, subtitle)
    ax.set_xlabel("Sentiment-tilt strength k (0 = no sentiment)")
    ax.set_ylabel("Sharpe ratio")

    df = fusion_ksweep.sort_values("k")
    ax.plot(df["k"], df["sharpe"], color=PRIMARY, linewidth=2.4,
            marker="o", markersize=7, zorder=3)

    k0 = df[df["k"] == 0].iloc[0]
    worst = df.loc[df["sharpe"].idxmin()]
    for marker, color, label, xytext in [
            (k0, PRIMARY, "best: no sentiment", (10, 14)),
            (worst, CORAL, "worst", (-34, -12))]:
        ax.scatter([marker["k"]], [marker["sharpe"]], s=170, marker="o",
                   color=color, edgecolor="white", linewidths=1.6,
                   zorder=5)
        ax.annotate(label, xy=(marker["k"], marker["sharpe"]),
                    xytext=xytext, textcoords="offset points",
                    fontsize=9, fontweight="bold", color=color,
                    arrowprops=dict(arrowstyle="->", color=color, lw=1.1),
                    annotation_clip=False)

    ax.set_xticks(df["k"])
    ax.set_xticklabels([f"{k:g}" for k in df["k"]])
    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, _: f"{v:.3f}"))
    ax.set_ylim(0.70, 0.775)
    _save(fig, "06_fusion_ksweep.png")


def fund_tier(vol):
    if vol < 0.16:
        return "Conservative"
    if vol < 0.35:
        return "Balanced"
    return "Growth"


def _asset_label(asset):
    if asset.startswith("EQ_"):
        return asset[3:]
    if asset.startswith("CR_"):
        return asset[3:].replace("-USD", "")
    return asset


def main():
    print("Reading precomputed CSVs from results/ ...")
    fund_returns = pd.read_csv(DATA / "fund_returns.csv", index_col=0,
                               parse_dates=True)
    fund_weights = pd.read_csv(DATA / "fund_weights.csv")
    perf_metrics = pd.read_csv(TABLES / "performance_metrics.csv")
    sector_idx = pd.read_csv(DATA / "sector_sentiment_index.csv",
                             index_col=0, parse_dates=True)
    fusion_ksweep = pd.read_csv(TABLES / "fusion_ksweep.csv")

    print("\nGenerating figures ...\n")
    fig1_growth_of_1(fund_returns)
    fig2_drawdown(fund_returns)
    fig3_weights_over_time(fund_weights)
    fig4_sharpe_bar(perf_metrics)
    fig5_sentiment_index(sector_idx)
    fig6_fusion_ksweep(fusion_ksweep)

    print(f"\nAll 6 figures saved to {FIGURES.resolve()}/")


if __name__ == "__main__":
    main()

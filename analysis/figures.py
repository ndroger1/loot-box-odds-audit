"""Figures for the manuscript, brief, and site (static PNG + SVG, light background).

Colour follows the regime, never its rank: each regime keeps the same colour in
every figure. Palette: first four slots of a colour-blind-validated categorical
order (blue, orange, aqua, yellow); magnitude uses a single blue hue.
Every figure has a title stating what it shows, labelled axes, and n.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import ListedColormap
from matplotlib.ticker import MaxNLocator

from scrapers.config import MARKETS, PLATFORMS
from scrapers.records import FIGURES

from .stats import lootbox_units, prepare

REGIME_LABEL = {"legal_mandate": "Legal mandate (KR)", "self_regulation": "Self-regulation (GB)",
                "enforcement_based": "Enforcement (US)", "ban": "Nominal ban (BE)"}
REGIME_COLOR = {"legal_mandate": "#2a78d6", "self_regulation": "#eb6834",
                "enforcement_based": "#1baf7a", "ban": "#eda100"}
REGIMES = list(REGIME_LABEL)
INK, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
SEQ_BLUE = ["#dbe8f8", "#2a78d6"]  # light -> dark, one hue

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.8, "axes.axisbelow": True, "axes.spines.top": False,
    "axes.spines.right": False, "font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold",
})


def _save(fig, name: str) -> list[str]:
    FIGURES.mkdir(parents=True, exist_ok=True)
    paths = []
    for ext in ("png", "svg"):
        path = FIGURES / f"{name}.{ext}"
        fig.savefig(path, dpi=200, bbox_inches="tight")
        paths.append(str(path))
    plt.close(fig)
    return paths


def _note(fig, text: str, y: float = -0.02) -> None:
    fig.text(0.01, y, text, ha="left", va="top", fontsize=8, color=MUTED, wrap=True)


def prevalence_by_platform(df: pd.DataFrame):
    """RQ1: share of loot box titles that disclose numeric odds, by platform and regime."""
    df = prepare(df)
    lb = lootbox_units(df)
    known = lb[lb["odds_disclosed"].isin(["yes", "no"])]
    platforms = [p for p in PLATFORMS if p in set(known["platform"])]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    width = 0.8 / len(REGIMES)
    x = np.arange(len(platforms))
    for i, regime in enumerate(REGIMES):
        shares, ns = [], []
        for p in platforms:
            cell = known[(known["platform"] == p) & (known["regime"] == regime)]
            ns.append(len(cell))
            shares.append((cell["odds_disclosed"] == "yes").mean() * 100 if len(cell) else np.nan)
        ax.bar(x + (i - 1.5) * width, shares, width * 0.9, color=REGIME_COLOR[regime],
               label=REGIME_LABEL[regime], edgecolor=SURFACE, linewidth=1)
    ax.set_xticks(x, platforms)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Loot box titles disclosing numeric odds (%)")
    ax.set_title("Odds disclosure by platform and regulatory regime")
    ax.grid(axis="x", visible=False)
    ax.legend(frameon=False, ncol=4, loc="lower left", bbox_to_anchor=(0, 1.0), fontsize=9,
              handlelength=1, columnspacing=1.2)
    ax.set_title("Odds disclosure by platform and regulatory regime", pad=28)
    _note(fig, f"n = {len(known)} title-platform-market units with loot boxes and a known disclosure code "
               f"({len(lb) - len(known)} unknown excluded). Missing bars: no units in that cell.")
    return _save(fig, "fig1_disclosure_by_platform_regime")


def _box_by_regime(df: pd.DataFrame, value: str, ylabel: str, title: str, name: str, note: str):
    fig, ax = plt.subplots(figsize=(7, 4))
    data, labels = [], []
    for regime in REGIMES:
        vals = pd.to_numeric(df.loc[df["regime"] == regime, value], errors="coerce").dropna()
        data.append(vals.to_numpy())
        labels.append(f"{REGIME_LABEL[regime].replace(' (', chr(10) + '(')}\nn = {len(vals)}")
    bp = ax.boxplot(data, widths=0.5, patch_artist=True, showfliers=False,
                    medianprops={"color": INK, "linewidth": 2})
    for patch, regime in zip(bp["boxes"], REGIMES):
        patch.set_facecolor(REGIME_COLOR[regime] + "55")
        patch.set_edgecolor(REGIME_COLOR[regime])
    rng = np.random.default_rng(0)
    for i, (vals, regime) in enumerate(zip(data, REGIMES), start=1):
        ax.scatter(i + rng.uniform(-0.12, 0.12, len(vals)), vals, s=14, color=REGIME_COLOR[regime],
                   edgecolor=SURFACE, linewidth=0.5, zorder=3)
    ax.set_xticks(range(1, len(REGIMES) + 1), labels)
    ax.set_ylabel(ylabel)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    if value == "pdi":
        ax.set_ylim(-0.5, 10.5)
    ax.set_title(title)
    ax.grid(axis="x", visible=False)
    _note(fig, note, y=-0.1)
    return _save(fig, name)


def pdi_by_regime(df: pd.DataFrame):
    """RQ1: Public Disclosure Index by regime."""
    lb = lootbox_units(prepare(df))
    return _box_by_regime(lb, "pdi", "Public Disclosure Index (0-10)",
                          "Public Disclosure Index by regulatory regime",
                          "fig2_pdi_by_regime",
                          "Each dot is one title on one platform in one market with loot boxes. Boxes show the "
                          "median and interquartile range. Units with any unknown index component are excluded.")


def clicks_by_regime(df: pd.DataFrame):
    """RQ2: clicks from the publisher's start page to the odds."""
    d = prepare(df)
    d = d[(d["odds_disclosed"] == "yes") & d["clicks_to_odds"].notna()]
    return _box_by_regime(d, "clicks_to_odds", "Clicks from publisher start page to odds",
                          "How many clicks it takes to reach the odds",
                          "fig3_clicks_to_odds_by_regime",
                          "Publisher-site odds only (odds shown on the store page are not counted here). "
                          "Clicks = links followed from the start page, shortest path found by a "
                          "breadth-first crawl.")


def same_title_heatmap(df: pd.DataFrame, max_titles: int = 40):
    """RQ3: does the same title disclose odds in every market?"""
    d = prepare(df)
    lb = d[d["lootbox_present"] == "yes"]
    wide = (lb.assign(v=lb["odds_disclosed"].map({"yes": 1.0, "no": 0.0}))
              .pivot_table(index="unit_title", columns="market", values="v", aggfunc="first")
              .reindex(columns=list(MARKETS)).dropna())
    if wide.empty:
        return []
    names = lb.drop_duplicates("unit_title").set_index("unit_title")["title"]
    wide = wide.loc[wide.var(axis=1).sort_values(ascending=False).index][:max_titles]
    fig, ax = plt.subplots(figsize=(6, 0.28 * len(wide) + 1.6))
    ax.imshow(wide.to_numpy(), cmap=ListedColormap(SEQ_BLUE), vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(wide.columns)), [f"{m}\n{REGIME_LABEL[MARKETS[m]].split(' (')[0]}" for m in wide.columns])
    ax.set_yticks(range(len(wide)), [f"{names.get(t, t)[:38]} ({t.split(':')[0]})" for t in wide.index], fontsize=8)
    ax.set_xticks(np.arange(-0.5, len(wide.columns)), minor=True)
    ax.set_yticks(np.arange(-0.5, len(wide)), minor=True)
    ax.grid(which="minor", color=SURFACE, linewidth=2)
    ax.grid(which="major", visible=False)
    ax.tick_params(which="minor", length=0)
    ax.set_title("Same title, different markets: are odds disclosed?")
    handles = [plt.Rectangle((0, 0), 1, 1, color=SEQ_BLUE[1]), plt.Rectangle((0, 0), 1, 1, color=SEQ_BLUE[0])]
    ax.legend(handles, ["Odds disclosed", "Not disclosed"], frameon=False, loc="upper left",
              bbox_to_anchor=(1.02, 1))
    _note(fig, f"Titles with loot boxes and a known code in all four markets (n = {len(wide)} shown); "
               "titles that differ between markets listed first.")
    return _save(fig, "fig4_same_title_across_markets")


def all_figures(df: pd.DataFrame) -> list[str]:
    paths = []
    for fn in (prevalence_by_platform, pdi_by_regime, clicks_by_regime, same_title_heatmap):
        paths += fn(df)
    return paths

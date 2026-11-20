"""Statistical tests for the three research questions.

RQ1  Prevalence of odds disclosure by regime and platform
     - Fisher's exact test for each pair of groups (2x2), Holm-corrected
     - Monte Carlo exact test for the full groups x outcome table (SciPy's
       fisher_exact is 2x2 only, so the R x C test permutes outcomes with the
       table margins fixed and compares chi-square statistics)
     - Kruskal-Wallis on the Public Disclosure Index
RQ2  Findability and presentation
     - Kruskal-Wallis on clicks to odds; prevalence tables for presentation codes
RQ3  Same title across markets
     - Cochran's Q and pairwise McNemar tests (disclosed yes/no), Friedman and
       pairwise Wilcoxon tests (PDI), within titles present in every market compared
     - Logistic regression of disclosure on market and platform, standard errors
       clustered by title

Only rows with a known outcome enter a test; the number dropped as unknown is
reported alongside each result.
"""

from __future__ import annotations

from itertools import combinations

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats
from statsmodels.stats.contingency_tables import cochrans_q, mcnemar
from statsmodels.stats.multitest import multipletests

from scrapers.config import MARKETS

REGIME = MARKETS  # market code -> regime label


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["regime"] = df["market"].map(REGIME)
    key = df["title_key"].fillna("").astype(str)
    df["title_cluster"] = np.where(key != "", key, df["platform"] + ":" + df["store_id"].astype(str))
    df["unit_title"] = df["platform"] + ":" + df["store_id"].astype(str)
    return df


def lootbox_units(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["lootbox_present"] == "yes"]


def known_binary(df: pd.DataFrame, col: str) -> tuple[pd.DataFrame, int]:
    sub = df[df[col].isin(["yes", "no"])].copy()
    sub["y"] = (sub[col] == "yes").astype(int)
    return sub, len(df) - len(sub)


# ---------------------------------------------------------------- RQ1
def prevalence_table(df: pd.DataFrame, group: str, col: str = "odds_disclosed") -> pd.DataFrame:
    sub, _ = known_binary(lootbox_units(df), col)
    t = pd.crosstab(sub[group], sub[col]).reindex(columns=["yes", "no"], fill_value=0)
    t["n"] = t.sum(axis=1)
    t["share_yes"] = t["yes"] / t["n"]
    unknown = lootbox_units(df).groupby(group)[col].apply(lambda s: int((s == "unknown").sum()))
    t["n_unknown"] = unknown.reindex(t.index).fillna(0).astype(int)
    return t


def monte_carlo_exact(groups: pd.Series, outcome: pd.Series, n_iter: int = 20000, seed: int = 570) -> dict:
    """Permutation test of independence for an R x C table with fixed margins."""
    table = pd.crosstab(groups, outcome)
    if table.shape[0] < 2 or table.shape[1] < 2:
        return {"statistic": np.nan, "p_value": np.nan, "n_iter": 0, "table_shape": table.shape}
    g = pd.factorize(groups.to_numpy())[0]
    o = pd.factorize(outcome.to_numpy())[0]
    r, c = g.max() + 1, o.max() + 1
    expected = np.outer(np.bincount(g, minlength=r), np.bincount(o, minlength=c)) / len(g)

    def chi2(o_vec: np.ndarray) -> float:
        counts = np.bincount(g * c + o_vec, minlength=r * c).reshape(r, c)
        return float(((counts - expected) ** 2 / expected).sum())

    observed = chi2(o)
    rng = np.random.default_rng(seed)
    exceed = sum(chi2(rng.permutation(o)) >= observed - 1e-12 for _ in range(n_iter))
    return {"statistic": float(observed), "p_value": (exceed + 1) / (n_iter + 1),
            "n_iter": n_iter, "table_shape": table.shape}


def pairwise_fisher(df: pd.DataFrame, group: str, col: str = "odds_disclosed") -> pd.DataFrame:
    sub, _ = known_binary(lootbox_units(df), col)
    rows = []
    for a, b in combinations(sorted(sub[group].unique()), 2):
        pair = sub[sub[group].isin([a, b])]
        t = pd.crosstab(pair[group], pair["y"]).reindex(index=[a, b], columns=[1, 0], fill_value=0)
        odds_ratio, p = stats.fisher_exact(t.to_numpy())
        rows.append({"group_a": a, "group_b": b, "odds_ratio": odds_ratio, "p_value": p,
                     "yes_a": int(t.loc[a, 1]), "n_a": int(t.loc[a].sum()),
                     "yes_b": int(t.loc[b, 1]), "n_b": int(t.loc[b].sum())})
    out = pd.DataFrame(rows)
    if not out.empty:
        out["p_holm"] = multipletests(out["p_value"], method="holm")[1]
    return out


def kruskal(df: pd.DataFrame, group: str, value: str) -> dict:
    sub = df[pd.to_numeric(df[value], errors="coerce").notna()]
    samples = [pd.to_numeric(g[value]) for _, g in sub.groupby(group)]
    samples = [s for s in samples if len(s) > 0]
    if len(samples) < 2:
        return {"H": np.nan, "p_value": np.nan, "n": len(sub), "groups": len(samples)}
    h, p = stats.kruskal(*samples)
    n, k = len(sub), len(samples)
    epsilon_sq = (h - k + 1) / (n - k) if n > k else np.nan  # effect size
    return {"H": float(h), "p_value": float(p), "n": n, "groups": k, "epsilon_squared": epsilon_sq}


def rq1(df: pd.DataFrame) -> dict:
    df = prepare(df)
    lb = lootbox_units(df)
    sub, dropped = known_binary(lb, "odds_disclosed")
    return {
        "by_regime": prevalence_table(df, "regime"),
        "by_platform": prevalence_table(df, "platform"),
        "exact_regime": monte_carlo_exact(sub["regime"], sub["odds_disclosed"]),
        "exact_platform": monte_carlo_exact(sub["platform"], sub["odds_disclosed"]),
        "pairwise_regime": pairwise_fisher(df, "regime"),
        "pairwise_platform": pairwise_fisher(df, "platform"),
        "pdi_kruskal_regime": kruskal(lb, "regime", "pdi"),
        "pdi_kruskal_platform": kruskal(lb, "platform", "pdi"),
        "n_lootbox_units": len(lb),
        "n_dropped_unknown": dropped,
    }


# ---------------------------------------------------------------- RQ2
PRESENTATION = ["odds_placement", "odds_price_linked", "odds_in_market_language", "pity_disclosed",
                "dp_obstruction_candidate", "dp_language_barrier_candidate"]


def rq2(df: pd.DataFrame) -> dict:
    df = prepare(df)
    disclosed = df[df["odds_disclosed"] == "yes"]
    tables = {c: pd.crosstab(disclosed["regime"], disclosed[c], margins=True) for c in PRESENTATION}
    return {
        "clicks_kruskal_regime": kruskal(disclosed, "regime", "clicks_to_odds"),
        "clicks_kruskal_platform": kruskal(disclosed, "platform", "clicks_to_odds"),
        "clicks_summary": disclosed.groupby("regime")["clicks_to_odds"].describe(),
        "presentation_tables": tables,
    }


# ---------------------------------------------------------------- RQ3
def paired_frame(df: pd.DataFrame, value: str, markets: list[str] | None = None) -> pd.DataFrame:
    """Titles (same platform + store id) x markets, complete cases only."""
    markets = markets or list(MARKETS)
    wide = df.pivot_table(index="unit_title", columns="market", values=value, aggfunc="first")
    wide = wide.reindex(columns=markets)
    return wide.dropna()


def rq3(df: pd.DataFrame, markets: list[str] | None = None) -> dict:
    df = prepare(df)
    markets = markets or list(MARKETS)
    lb = df[df["lootbox_present"] == "yes"].copy()
    lb["disclosed01"] = lb["odds_disclosed"].map({"yes": 1.0, "no": 0.0})
    out: dict = {}

    binary = paired_frame(lb, "disclosed01", markets)
    out["n_titles_binary"] = len(binary)
    if len(binary) >= 2:
        q = cochrans_q(binary.to_numpy())
        out["cochrans_q"] = {"Q": float(q.statistic), "p_value": float(q.pvalue), "df": int(q.df)}
        rows = []
        for a, b in combinations(markets, 2):
            t = pd.crosstab(binary[a], binary[b]).reindex(index=[0.0, 1.0], columns=[0.0, 1.0], fill_value=0)
            m = mcnemar(t.to_numpy(), exact=True)
            rows.append({"market_a": a, "market_b": b, "discordant_a_only": int(t.loc[1.0, 0.0]),
                         "discordant_b_only": int(t.loc[0.0, 1.0]), "p_value": float(m.pvalue)})
        mc = pd.DataFrame(rows)
        mc["p_holm"] = multipletests(mc["p_value"], method="holm")[1]
        out["mcnemar_pairwise"] = mc

    pdi = paired_frame(lb, "pdi", markets)
    out["n_titles_pdi"] = len(pdi)
    if len(pdi) >= 2:
        f = stats.friedmanchisquare(*[pdi[m] for m in markets])
        out["friedman_pdi"] = {"chi2": float(f.statistic), "p_value": float(f.pvalue)}
        rows = []
        for a, b in combinations(markets, 2):
            diff = pdi[a] - pdi[b]
            if (diff != 0).sum() == 0:
                rows.append({"market_a": a, "market_b": b, "W": np.nan, "p_value": 1.0})
                continue
            w = stats.wilcoxon(pdi[a], pdi[b], zero_method="wilcox")
            rows.append({"market_a": a, "market_b": b, "W": float(w.statistic), "p_value": float(w.pvalue)})
        wx = pd.DataFrame(rows)
        wx["p_holm"] = multipletests(wx["p_value"], method="holm")[1]
        out["wilcoxon_pairwise"] = wx

    out["logit"] = logit_clustered(lb)
    return out


def logit_clustered(lb: pd.DataFrame, reference_market: str = "US"):
    """odds_disclosed ~ market + platform, SEs clustered by title."""
    sub = lb[lb["odds_disclosed"].isin(["yes", "no"])].copy()
    sub["y"] = (sub["odds_disclosed"] == "yes").astype(int)
    if sub["y"].nunique() < 2 or sub["market"].nunique() < 2:
        return "Not estimable: outcome or market has no variation."
    terms = [f"C(market, Treatment('{reference_market}'))"]
    if sub["platform"].nunique() > 1:
        terms.append("C(platform)")
    groups = pd.factorize(sub["title_cluster"])[0]
    try:
        model = smf.logit("y ~ " + " + ".join(terms), data=sub)
        return model.fit(cov_type="cluster", cov_kwds={"groups": groups}, disp=False)
    except Exception as exc:  # noqa: BLE001 - e.g. perfect separation with small samples
        return f"Not estimable: {exc}"

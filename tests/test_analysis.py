"""Analysis code runs end to end on randomly generated data (not study data)."""

import numpy as np
import pandas as pd

from analysis import stats
from coding.validation import alpha_nominal, precision_recall


def fake_units(seed=1, n_titles=30):
    rng = np.random.default_rng(seed)
    p_by_market = {"KR": 0.9, "GB": 0.5, "US": 0.4, "BE": 0.3}
    rows = []
    for t in range(n_titles):
        platform = ["ios", "steam"][t % 2]
        for m, p in p_by_market.items():
            yes = rng.random() < p
            rows.append({"market": m, "platform": platform, "store_id": str(t), "title": f"Title {t}",
                         "title_key": f"title {t}", "lootbox_present": "yes",
                         "odds_disclosed": "yes" if yes else "no",
                         "pdi": float(rng.integers(3, 10)) if yes else float(rng.integers(0, 3)),
                         "clicks_to_odds": float(rng.integers(0, 5)) if yes else np.nan,
                         "odds_placement": "publisher_site" if yes else "none",
                         "odds_price_linked": "no", "odds_in_market_language": "yes",
                         "pity_disclosed": "no", "dp_obstruction_candidate": "no",
                         "dp_language_barrier_candidate": "no"})
    return pd.DataFrame(rows)


def test_rq1_runs():
    r = stats.rq1(fake_units())
    assert set(r["by_regime"].index) == {"legal_mandate", "self_regulation", "enforcement_based", "ban"}
    assert 0 < r["exact_regime"]["p_value"] <= 1
    assert "p_holm" in r["pairwise_regime"]


def test_monte_carlo_detects_strong_difference():
    g = pd.Series(["a"] * 40 + ["b"] * 40)
    o = pd.Series(["yes"] * 38 + ["no"] * 2 + ["yes"] * 5 + ["no"] * 35)
    assert stats.monte_carlo_exact(g, o, n_iter=2000)["p_value"] < 0.01


def test_rq2_rq3_run():
    df = fake_units()
    assert "presentation_tables" in stats.rq2(df)
    r3 = stats.rq3(df)
    assert r3["n_titles_binary"] == 30 and "cochrans_q" in r3
    assert not isinstance(r3["logit"], str)


def test_validation_metrics():
    auto = pd.Series(["yes", "yes", "no", "unknown", "no"])
    hand = pd.Series(["yes", "no", "no", "yes", "yes"])
    pr = precision_recall(auto, hand)
    assert pr["n"] == 4 and pr["precision"] == 0.5 and pr["recall"] == 0.5
    assert alpha_nominal(pd.Series(["yes", "no"] * 5), pd.Series(["yes", "no"] * 5)) == 1.0


def test_figures_render(tmp_path, monkeypatch):
    from analysis import figures
    monkeypatch.setattr(figures, "FIGURES", tmp_path)
    paths = figures.all_figures(fake_units())
    assert len(paths) == 8 and all((tmp_path / p.split("\\")[-1].split("/")[-1]).exists() for p in paths)

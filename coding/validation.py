"""Validation of the automated codes against a hand-coded 20% sample.

1. `draw_sample()` writes codebook/validation_sample.csv: a stratified random
   20% of units (by market x platform) with blank hand-coding columns.
2. Code the sample by hand from the evidence (never by looking at the
   automated codes first), filling the `hand_*` columns.
3. `report()` compares hand and automated codes and writes
   codebook/validation_report.md with precision, recall, and Krippendorff's alpha.
"""

from __future__ import annotations

import krippendorff
import numpy as np
import pandas as pd

from scrapers.records import CODEBOOK, PROCESSED

CODES = ["lootbox_present", "store_label_random_items", "odds_disclosed",
         "odds_price_linked", "odds_in_market_language", "pity_disclosed"]
SAMPLE = CODEBOOK / "validation_sample.csv"
REPORT = CODEBOOK / "validation_report.md"
SEED = 570


def draw_sample(df: pd.DataFrame | None = None, frac: float = 0.2, seed: int = SEED) -> pd.DataFrame:
    if SAMPLE.exists():
        raise FileExistsError(f"{SAMPLE} exists; it may already be hand-coded. Move it before redrawing.")
    df = df if df is not None else pd.read_csv(PROCESSED / "coded_units.csv", dtype={"store_id": str})
    sample = (df.groupby(["market", "platform"], group_keys=False)
                .apply(lambda g: g.sample(n=max(1, int(round(len(g) * frac))), random_state=seed)))
    cols = ["snapshot_date", "market", "platform", "rank", "title", "store_id", "evidence_refs", "odds_url"]
    sheet = sample[cols].copy()
    for code in CODES:
        sheet[f"hand_{code}"] = ""
    sheet["hand_clicks_to_odds"] = ""
    sheet["hand_notes"] = ""
    sheet.to_csv(SAMPLE, index=False, encoding="utf-8-sig")
    return sheet


def precision_recall(auto: pd.Series, hand: pd.Series, positive: str = "yes") -> dict:
    """Treat `positive` as the positive class; rows where either side is unknown are excluded."""
    keep = (auto != "unknown") & (hand != "unknown") & auto.notna() & hand.notna()
    a, h = auto[keep] == positive, hand[keep] == positive
    tp, fp, fn = int((a & h).sum()), int((a & ~h).sum()), int((~a & h).sum())
    return {
        "n": int(keep.sum()),
        "precision": tp / (tp + fp) if tp + fp else np.nan,
        "recall": tp / (tp + fn) if tp + fn else np.nan,
        "tp": tp, "fp": fp, "fn": fn,
    }


def alpha_nominal(auto: pd.Series, hand: pd.Series) -> float:
    """Krippendorff's alpha (nominal), treating 'unknown' as its own category."""
    cats = sorted(set(auto.dropna()) | set(hand.dropna()))
    if len(cats) < 2:
        return np.nan
    lookup = {c: i for i, c in enumerate(cats)}
    data = np.array([[lookup.get(v, np.nan) for v in auto], [lookup.get(v, np.nan) for v in hand]], dtype=float)
    return float(krippendorff.alpha(reliability_data=data, level_of_measurement="nominal"))


def compare(coded: pd.DataFrame, sheet: pd.DataFrame) -> pd.DataFrame:
    keys = ["market", "platform", "store_id"]
    merged = sheet.merge(coded, on=keys, how="left", suffixes=("", "_auto"))
    rows = []
    for code in CODES:
        hand_col = f"hand_{code}"
        filled = merged[merged[hand_col].astype(str).str.strip() != ""]
        if filled.empty:
            continue
        auto = filled[code].astype(str).str.strip().str.lower()
        hand = filled[hand_col].astype(str).str.strip().str.lower()
        pr = precision_recall(auto, hand)
        rows.append({"code": code, **pr, "alpha": alpha_nominal(auto, hand),
                     "agreement": float((auto == hand).mean())})
    if "hand_clicks_to_odds" in merged:
        filled = merged[merged["hand_clicks_to_odds"].astype(str).str.strip() != ""]
        if not filled.empty:
            auto = pd.to_numeric(filled["clicks_to_odds"], errors="coerce")
            hand = pd.to_numeric(filled["hand_clicks_to_odds"], errors="coerce")
            data = np.vstack([auto.to_numpy(float), hand.to_numpy(float)])
            alpha = (krippendorff.alpha(reliability_data=data, level_of_measurement="interval")
                     if np.isfinite(data).all(axis=0).sum() > 1 else np.nan)
            rows.append({"code": "clicks_to_odds", "n": int(np.isfinite(data).all(axis=0).sum()),
                         "alpha": alpha, "agreement": float((auto == hand).mean())})
    return pd.DataFrame(rows)


def report() -> pd.DataFrame:
    from .rules import RULES_VERSION

    coded = pd.read_csv(PROCESSED / "coded_units.csv", dtype={"store_id": str})
    sheet = pd.read_csv(SAMPLE, dtype={"store_id": str}, encoding="utf-8-sig").fillna("")
    table = compare(coded, sheet)
    lines = [
        "# Validation report", "",
        f"Rules version: `{RULES_VERSION}`. Sample: {len(sheet)} of {len(coded)} units "
        f"({len(sheet) / len(coded):.0%}), stratified by market and platform, random seed {SEED}.", "",
        "Precision and recall treat `yes` as positive and leave out rows where either coder said `unknown`. "
        "Krippendorff's alpha is nominal and counts `unknown` as a category (interval for clicks).", "",
        table.to_markdown(index=False, floatfmt=".2f") if not table.empty else "_No hand codes entered yet._",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return table

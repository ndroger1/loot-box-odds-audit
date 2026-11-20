"""Public Disclosure Index (0-10), computed from codebook/index_spec.json.

The spec is a DRAFT until approved; the component list lives in the codebook,
not in code, so changing the index means editing the spec (and logging it).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

SPEC = Path(__file__).resolve().parents[1] / "codebook" / "index_spec.json"


def load_spec() -> dict:
    return json.loads(SPEC.read_text(encoding="utf-8"))


def score_component(row: pd.Series, comp: dict) -> float:
    """1 or 0 for the component, or NaN if the evidence is unknown."""
    value = row.get(comp["column"])
    if "yes_if" in comp:
        if value == "unknown" or value is None or (isinstance(value, float) and np.isnan(value)):
            return np.nan
        return 1.0 if value == comp["yes_if"] else 0.0
    if "max" in comp:  # clicks: store-page odds take zero clicks beyond the store
        if row.get("store_odds_numeric") == "yes":
            value = comp.get("store_page_counts_as", 0)
        if value is None or pd.isna(value):
            return 0.0 if row.get("odds_disclosed") == "no" else np.nan
        return 1.0 if value <= comp["max"] else 0.0
    if "min" in comp:
        if value is None or pd.isna(value):
            return 0.0 if row.get("odds_disclosed") == "no" else np.nan
        return 1.0 if value >= comp["min"] else 0.0
    raise ValueError(f"Bad component spec: {comp}")


def add_index(df: pd.DataFrame, spec: dict | None = None) -> pd.DataFrame:
    spec = spec or load_spec()
    df = df.copy()
    comps = spec["components"]
    scores = pd.DataFrame({c["id"]: df.apply(score_component, axis=1, comp=c) * c["points"]
                           for c in comps}, index=df.index)
    applies = df["lootbox_present"] == "yes"
    unknown = scores.isna().sum(axis=1)
    df["pdi_unknown_components"] = np.where(applies, unknown, np.nan)
    df["pdi"] = np.where(applies & (unknown == 0), scores.sum(axis=1, min_count=1), np.nan)
    df["pdi_min"] = np.where(applies, scores.fillna(0).sum(axis=1), np.nan)
    max_points = pd.Series({c["id"]: c["points"] for c in comps})
    df["pdi_max"] = np.where(applies, scores.fillna(max_points).sum(axis=1), np.nan)
    return df

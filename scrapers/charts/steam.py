"""Steam weekly top sellers, per market (country chart where available)."""

from __future__ import annotations

import json

from ..config import PLATFORMS, STEAM_LANGUAGE
from ..polite import PoliteSession
from ..records import relpath, save_raw, snapshot_date
from ..sources import require_permitted


def collect(market: str, session: PoliteSession | None = None) -> list[dict]:
    cfg = require_permitted("steam")
    session = session or PoliteSession()
    request = {
        "context": {"language": STEAM_LANGUAGE[market], "country_code": market},
        "country_code": market,
        "page_start": 0,
        "page_count": PLATFORMS["steam"],
        "data_request": {"include_basic_info": True},
    }
    params = {"input_json": json.dumps(request)}
    resp, retrieved_at = session.get(cfg["chart_url"], params=params)
    resp.raise_for_status()
    raw = save_raw(resp.text, "charts", "steam", market, suffix=".json")
    return parse(resp.json(), market, resp.url, retrieved_at, relpath(raw))


def parse(payload: dict, market: str, source: str, retrieved_at: str, evidence_ref: str) -> list[dict]:
    response = payload.get("response", {})
    ranks = response.get("ranks", [])
    # If Steam ignores the country code it reports a different one (or none).
    returned_country = (response.get("country_code") or "").upper()
    scope = "country" if returned_country == market else "global"
    rows = []
    for item in ranks[: PLATFORMS["steam"]]:
        info = item.get("item", {}) or {}
        appid = item.get("appid") or info.get("appid") or info.get("id")
        rows.append({
            "snapshot_date": snapshot_date(),
            "market": market,
            "platform": "steam",
            "rank": item.get("rank"),
            "title": info.get("name"),
            "store_id": str(appid) if appid else None,
            "store_url": f"https://store.steampowered.com/app/{appid}/" if appid else None,
            "publisher": None,  # filled from appdetails in stage 2
            "chart_scope": scope,
            "source": source,
            "retrieved_at": retrieved_at,
            "evidence_ref": evidence_ref,
        })
    return rows

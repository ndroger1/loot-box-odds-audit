"""iPhone App Store top-grossing games chart, per market."""

from __future__ import annotations

from ..config import PLATFORMS
from ..polite import PoliteSession
from ..records import relpath, save_raw, snapshot_date
from ..sources import require_permitted


def collect(market: str, session: PoliteSession | None = None) -> list[dict]:
    cfg = require_permitted("ios")
    session = session or PoliteSession()
    limit = PLATFORMS["ios"]
    url = cfg["chart_url"].format(country=market.lower(), limit=limit)
    resp, retrieved_at = session.get(url)
    resp.raise_for_status()
    raw = save_raw(resp.text, "charts", "ios", market, suffix=".json")
    return parse(resp.json(), market, url, retrieved_at, relpath(raw))


def parse(payload: dict, market: str, source: str, retrieved_at: str, evidence_ref: str) -> list[dict]:
    entries = payload.get("feed", {}).get("entry", [])
    if isinstance(entries, dict):  # a single entry comes back as an object
        entries = [entries]
    rows = []
    for rank, entry in enumerate(entries, start=1):
        rows.append({
            "snapshot_date": snapshot_date(),
            "market": market,
            "platform": "ios",
            "rank": rank,
            "title": entry.get("im:name", {}).get("label"),
            "store_id": entry.get("id", {}).get("attributes", {}).get("im:id"),
            "store_url": entry.get("id", {}).get("label"),
            "publisher": entry.get("im:artist", {}).get("label"),
            "chart_scope": "country",
            "source": source,
            "retrieved_at": retrieved_at,
            "evidence_ref": evidence_ref,
        })
    return rows

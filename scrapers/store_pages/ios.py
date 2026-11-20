"""App Store product details via the iTunes Lookup API (country-specific)."""

from __future__ import annotations

from ..polite import PoliteSession
from ..records import relpath, save_raw, snapshot_date
from ..sources import require_permitted


def collect(chart_row: dict, session: PoliteSession | None = None) -> dict | None:
    cfg = require_permitted("ios")
    session = session or PoliteSession()
    market = chart_row["market"]
    params = {"id": chart_row["store_id"], "country": market.lower()}
    resp, retrieved_at = session.get(cfg["lookup_url"], params=params)
    resp.raise_for_status()
    raw = save_raw(resp.text, "store_pages", "ios", market, suffix=".json")
    return parse(resp.json(), chart_row, resp.url, retrieved_at, relpath(raw))


def parse(payload: dict, chart_row: dict, source: str, retrieved_at: str, evidence_ref: str) -> dict | None:
    results = payload.get("results") or []
    if not results:
        return None
    app = results[0]
    advisories = app.get("advisories") or []
    return {
        "snapshot_date": snapshot_date(),
        "market": chart_row["market"],
        "platform": "ios",
        "store_id": chart_row["store_id"],
        "title": app.get("trackName") or chart_row.get("title"),
        "publisher": app.get("sellerName") or app.get("artistName"),
        "publisher_url": app.get("sellerUrl"),
        "support_url": None,
        "age_rating": app.get("contentAdvisoryRating") or app.get("trackContentRating"),
        "label_text": " | ".join(advisories),
        "description": app.get("description") or "",
        "language": chart_row["market"],
        "price_info": app.get("formattedPrice"),
        "store_url": app.get("trackViewUrl") or chart_row.get("store_url"),
        "source": source,
        "retrieved_at": retrieved_at,
        "evidence_ref": evidence_ref,
    }

"""Steam product details via the storefront appdetails API (country + language).

Belgium is collected in Dutch, French, and German; other markets in one language.
"""

from __future__ import annotations

import html
import re

from ..config import STEAM_EXTRA_LANGUAGES, STEAM_LANGUAGE
from ..polite import PoliteSession
from ..records import relpath, save_raw, snapshot_date
from ..sources import require_permitted

TAG = re.compile(r"<[^>]+>")


def strip_html(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(TAG.sub(" ", text or ""))).strip()


def collect(chart_row: dict, session: PoliteSession | None = None) -> list[dict]:
    cfg = require_permitted("steam")
    session = session or PoliteSession()
    market = chart_row["market"]
    rows = []
    for lang in [STEAM_LANGUAGE[market], *STEAM_EXTRA_LANGUAGES.get(market, [])]:
        params = {"appids": chart_row["store_id"], "cc": market, "l": lang}
        resp, retrieved_at = session.get(cfg["appdetails_url"], params=params)
        resp.raise_for_status()
        raw = save_raw(resp.text, "store_pages", "steam", market, suffix=".json")
        row = parse(resp.json(), chart_row, lang, resp.url, retrieved_at, relpath(raw))
        if row:
            rows.append(row)
    return rows


def parse(payload: dict, chart_row: dict, lang: str, source: str, retrieved_at: str,
          evidence_ref: str) -> dict | None:
    entry = payload.get(str(chart_row["store_id"])) or {}
    if not entry.get("success"):
        return None
    d = entry.get("data", {})
    descriptors = d.get("content_descriptors") or {}
    ratings = d.get("ratings") or {}
    rating_bits = []
    for board, info in ratings.items():
        if isinstance(info, dict):
            bits = [info.get("rating"), info.get("descriptors"), info.get("interactive_elements")]
            rating_bits.append(f"{board}: " + " ".join(str(b) for b in bits if b))
    price = d.get("price_overview") or {}
    support = d.get("support_info") or {}
    description = " ".join(filter(None, (strip_html(d.get(k, "")) for k in
                                         ("short_description", "about_the_game", "detailed_description"))))
    return {
        "snapshot_date": snapshot_date(),
        "market": chart_row["market"],
        "platform": "steam",
        "store_id": str(chart_row["store_id"]),
        "title": d.get("name") or chart_row.get("title"),
        "publisher": "; ".join(d.get("publishers") or []) or None,
        "publisher_url": d.get("website"),
        "support_url": support.get("url") or None,
        "age_rating": str(d.get("required_age") or ""),
        "label_text": " | ".join(filter(None, [descriptors.get("notes"), *rating_bits])),
        "description": description,
        "language": lang,
        "price_info": price.get("final_formatted") or ("free" if d.get("is_free") else None),
        "store_url": chart_row.get("store_url"),
        "source": source,
        "retrieved_at": retrieved_at,
        "evidence_ref": evidence_ref,
    }

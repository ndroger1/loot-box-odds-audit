"""PlayStation, Xbox, and Nintendo product pages (Playwright, public pages only).

Saves the rendered HTML and the visible text. Label and odds detection happens
later in coding/, so this module stays store-agnostic.
"""

from __future__ import annotations

from ..browser import market_page
from ..records import now_utc, relpath, save_raw, snapshot_date
from ..sources import require_permitted


def collect_many(chart_rows: list[dict]) -> list[dict]:
    """Collect product pages for chart rows of one platform and one market."""
    if not chart_rows:
        return []
    platform, market = chart_rows[0]["platform"], chart_rows[0]["market"]
    require_permitted(platform)
    out = []
    with market_page(market) as page:
        for row in chart_rows:
            if not row.get("store_url"):
                continue
            page.goto(row["store_url"])
            retrieved_at = now_utc()
            raw = save_raw(page.content(), "store_pages", platform, market)
            text = page.inner_text("body")
            out.append({
                "snapshot_date": snapshot_date(),
                "market": market,
                "platform": platform,
                "store_id": row.get("store_id"),
                "title": row.get("title"),
                "publisher": None,
                "publisher_url": None,
                "support_url": None,
                "age_rating": None,
                "label_text": "",       # labels are found in description text by coding rules
                "description": text,
                "language": market,
                "price_info": None,
                "store_url": row["store_url"],
                "source": row["store_url"],
                "retrieved_at": retrieved_at,
                "evidence_ref": relpath(raw),
            })
    return out

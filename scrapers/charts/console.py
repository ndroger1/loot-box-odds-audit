"""PlayStation Store, Xbox Store, and Nintendo eShop best-seller charts (Playwright).

Chart page URLs and CSS selectors come from config/sources.json and must be
filled in and checked by hand (see config/README.md). A market with no URL is
skipped with a message so the tracker fallback can cover it.
"""

from __future__ import annotations

from urllib.parse import urljoin

from ..browser import market_page
from ..config import PLATFORMS
from ..records import now_utc, relpath, save_raw, snapshot_date
from ..sources import require_permitted

CONSOLE_PLATFORMS = ("playstation", "xbox", "nintendo")


class ChartNotConfigured(Exception):
    pass


def collect(platform: str, market: str) -> list[dict]:
    if platform not in CONSOLE_PLATFORMS:
        raise ValueError(platform)
    cfg = require_permitted(platform)
    url = cfg["chart_pages"].get(market)
    selectors = (cfg.get("item_selector"), cfg.get("title_selector"), cfg.get("link_selector"))
    if not url or not all(selectors):
        raise ChartNotConfigured(f"{platform} {market}: chart URL or selectors not set in config/sources.json")
    item_sel, title_sel, link_sel = selectors
    limit = PLATFORMS[platform]

    with market_page(market) as page:
        page.goto(url)
        retrieved_at = now_utc()
        html = page.content()
        raw = save_raw(html, "charts", platform, market)
        rows = []
        for rank, item in enumerate(page.query_selector_all(item_sel)[:limit], start=1):
            title_el = item.query_selector(title_sel)
            link_el = item.query_selector(link_sel)
            href = link_el.get_attribute("href") if link_el else None
            store_url = urljoin(url, href) if href else None
            rows.append({
                "snapshot_date": snapshot_date(),
                "market": market,
                "platform": platform,
                "rank": rank,
                "title": title_el.inner_text().strip() if title_el else None,
                "store_id": store_url.rstrip("/").rsplit("/", 1)[-1] if store_url else None,
                "store_url": store_url,
                "publisher": None,
                "chart_scope": "country",
                "source": url,
                "retrieved_at": retrieved_at,
                "evidence_ref": relpath(raw),
            })
    return rows

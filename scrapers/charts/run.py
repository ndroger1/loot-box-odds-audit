"""Collect every chart for every market and write data/interim/charts.csv.

For each platform x market: try the store's own collector; on failure, fall back
to a tracker export; if neither works, log the gap (never invent rows).
"""

from __future__ import annotations

import logging

from ..config import MARKETS, PLATFORMS
from ..polite import PoliteSession
from ..records import INTERIM, write_csv
from . import console, ios, steam, tracker

log = logging.getLogger(__name__)


def collect_one(platform: str, market: str, session: PoliteSession) -> tuple[list[dict], str]:
    try:
        if platform == "ios":
            return ios.collect(market, session), "store"
        if platform == "steam":
            return steam.collect(market, session), "store"
        return console.collect(platform, market), "store"
    except Exception as exc:  # noqa: BLE001 - any failure falls back to the tracker
        log.warning("%s %s store collection failed: %s", platform, market, exc)
    try:
        return tracker.collect(platform, market), "tracker"
    except FileNotFoundError as exc:
        log.warning("%s %s no tracker fallback: %s", platform, market, exc)
        return [], "missing"


def main(platforms=None, markets=None) -> list[dict]:
    session = PoliteSession()
    rows, status = [], []
    for platform in platforms or PLATFORMS:
        for market in markets or MARKETS:
            got, how = collect_one(platform, market, session)
            rows.extend(got)
            status.append({"platform": platform, "market": market, "method": how, "n": len(got)})
            log.info("%s %s: %s rows via %s", platform, market, len(got), how)
    write_csv(rows, INTERIM / "charts.csv")
    write_csv(status, INTERIM / "charts_status.csv", required=False)
    return rows


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    main()

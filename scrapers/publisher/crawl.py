"""Run the publisher crawl with the project's scraping rules applied.

    python -m scrapers.publisher.crawl            # all markets
    python -m scrapers.publisher.crawl KR,GB      # selected markets

Each run writes data/interim/publisher_pages/<markets>.jsonl, so markets can be
crawled in separate runs (e.g. one Colab session each) without overwriting each
other. After every run, all part files are merged into
data/interim/publisher_pages.jsonl; for each market, the most recent run wins.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from scrapy.crawler import CrawlerProcess

from ..polite import user_agent
from ..config import MARKETS
from ..records import INTERIM, read_jsonl
from .spider import PublisherSpider

OUT = INTERIM / "publisher_pages.jsonl"
PARTS = INTERIM / "publisher_pages"


def market_list(markets: str = "") -> list[str]:
    return [m.strip().upper() for m in markets.split(",") if m.strip()] if markets else list(MARKETS)


def part_path(markets: str = "", parts: Path = PARTS) -> Path:
    return parts / f"{'-'.join(sorted(market_list(markets)))}.jsonl"


def merge(parts: Path = PARTS, out: Path = OUT) -> int:
    """Combine part files into one; a later run replaces earlier rows for its markets."""
    rows: list[dict] = []
    for path in sorted(parts.glob("*.jsonl"), key=lambda p: p.stat().st_mtime):
        covered = set(path.stem.split("-"))
        rows = [r for r in rows if r.get("market") not in covered] + read_jsonl(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return len(rows)


def settings(markets: str = "") -> dict:
    return {
        "USER_AGENT": user_agent(),
        "ROBOTSTXT_OBEY": True,
        "DOWNLOAD_DELAY": float(os.environ.get("REQUEST_DELAY_SECONDS", 3)),
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": float(os.environ.get("REQUEST_DELAY_SECONDS", 3)),
        "DEPTH_LIMIT": int(os.environ.get("CRAWL_DEPTH_LIMIT", 4)),
        # Breadth-first: depth at first discovery = fewest clicks from the start page.
        "DEPTH_PRIORITY": 1,
        "SCHEDULER_DISK_QUEUE": "scrapy.squeues.PickleFifoDiskQueue",
        "SCHEDULER_MEMORY_QUEUE": "scrapy.squeues.FifoMemoryQueue",
        "COOKIES_ENABLED": False,  # never log in, never keep a session
        "FEEDS": {part_path(markets).as_posix(): {"format": "jsonlines", "encoding": "utf8", "overwrite": True}},
        "LOG_LEVEL": "INFO",
    }


def main(markets: str = "") -> None:
    markets = ",".join(market_list(markets))
    PARTS.mkdir(parents=True, exist_ok=True)
    process = CrawlerProcess(settings(markets))
    process.crawl(PublisherSpider, markets=markets)
    process.start()
    print(f"Merged {merge()} pages into {OUT}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")

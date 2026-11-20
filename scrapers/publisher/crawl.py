"""Run the publisher crawl with the project's scraping rules applied.

    python -m scrapers.publisher.crawl            # all markets
    python -m scrapers.publisher.crawl KR,GB      # selected markets
"""

from __future__ import annotations

import os
import sys

from scrapy.crawler import CrawlerProcess

from ..polite import user_agent
from ..records import INTERIM
from .spider import PublisherSpider

OUT = INTERIM / "publisher_pages.jsonl"


def settings() -> dict:
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
        "FEEDS": {OUT.as_posix(): {"format": "jsonlines", "encoding": "utf8", "overwrite": True}},
        "LOG_LEVEL": "INFO",
    }


def main(markets: str = "") -> None:
    process = CrawlerProcess(settings())
    process.crawl(PublisherSpider, markets=markets)
    process.start()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")

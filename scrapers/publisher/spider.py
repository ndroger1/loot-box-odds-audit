"""Scrapy spider that crawls each publisher site breadth-first, once per market.

- Breadth-first order (see settings in crawl.py) means the first time a page is
  reached, its depth is the fewest clicks from the start page.
- Each market is crawled with that market's Accept-Language header. Sites that
  choose content by IP address will still serve the version for this machine's
  location; that limitation is recorded in the codebook.
- Raw HTML is saved only for pages that contain odds or loot box terms; every
  visited URL and its depth is logged.
"""

from __future__ import annotations

import csv
import re
from urllib.parse import urldefrag

import scrapy

from coding.dictionary import find_terms

from ..config import MARKETS
from ..records import CONFIG, now_utc, relpath, save_raw, snapshot_date
from .domains import same_site, site_of

ACCEPT_LANGUAGE = {"KR": "ko-KR,ko;q=0.9,en;q=0.5", "GB": "en-GB,en;q=0.9",
                   "US": "en-US,en;q=0.9", "BE": "nl-BE,nl;q=0.9,fr-BE;q=0.8,de;q=0.6,en;q=0.5"}
SKIP_EXT = re.compile(r"\.(jpg|jpeg|png|gif|webp|svg|mp4|webm|zip|exe|dmg|apk|css|js|woff2?)$", re.I)
MAX_TEXT = 200_000


class PublisherSpider(scrapy.Spider):
    name = "publisher"

    def __init__(self, markets: str = "", max_pages_per_seed: int = 300, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.markets = markets.split(",") if markets else list(MARKETS)
        self.max_pages = int(max_pages_per_seed)
        self.page_counts: dict[tuple, int] = {}

    def start_requests(self):
        with (CONFIG / "publisher_seeds.csv").open(encoding="utf-8-sig") as fh:
            seeds = [r for r in csv.DictReader(fh) if r.get("reviewed", "").strip().lower() == "yes"]
        if not seeds:
            self.logger.error("No seeds marked reviewed=yes in config/publisher_seeds.csv")
        for seed in seeds:
            for market in self.markets:
                for url in seed["start_urls"].split():
                    yield scrapy.Request(
                        url,
                        headers={"Accept-Language": ACCEPT_LANGUAGE[market]},
                        meta={"seed_id": seed["seed_id"], "site": site_of(url), "market": market},
                        dont_filter=True,  # same start URL is crawled once per market
                        callback=self.parse,
                    )

    def parse(self, response):
        if not hasattr(response, "text"):
            return  # binary response
        meta = response.meta
        key = (meta["seed_id"], meta["market"])
        self.page_counts[key] = self.page_counts.get(key, 0) + 1
        depth = meta.get("depth", 0)
        text = " ".join(t.strip() for t in response.xpath("//body//text()[not(ancestor::script) and not(ancestor::style)]").getall() if t.strip())
        hits = find_terms(text)
        evidence = None
        if hits["odds"] or hits["lootbox"]:
            evidence = relpath(save_raw(response.text, "publisher", meta["seed_id"], meta["market"]))

        yield {
            "snapshot_date": snapshot_date(),
            "market": meta["market"],
            "platform": "publisher",
            "seed_id": meta["seed_id"],
            "url": response.url,
            "referer": (response.request.headers.get("Referer") or b"").decode("utf-8", "ignore"),
            "depth": depth,
            "page_title": (response.css("title::text").get() or "").strip(),
            "html_lang": response.xpath("/html/@lang").get(),
            "odds_terms": hits["odds"],
            "lootbox_terms": hits["lootbox"],
            "text": text[:MAX_TEXT] if evidence else "",
            "source": response.url,
            "retrieved_at": now_utc(),
            "evidence_ref": evidence or f"not-saved:{response.url}",
        }

        if self.page_counts[key] >= self.max_pages:
            return
        for href in response.css("a::attr(href)").getall():
            url = urldefrag(response.urljoin(href))[0]
            if not url.startswith("http") or SKIP_EXT.search(url):
                continue
            if not same_site(url, meta["site"]):
                continue
            yield response.follow(
                url,
                headers={"Accept-Language": ACCEPT_LANGUAGE[meta["market"]]},
                meta={"seed_id": meta["seed_id"], "site": meta["site"], "market": meta["market"]},
                callback=self.parse,
            )

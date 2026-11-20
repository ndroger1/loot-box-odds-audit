"""Build config/publisher_seeds.csv from store-page records.

One seed per publisher site. Review the file by hand before crawling
(see config/README.md); this script never overwrites a reviewed file.
"""

from __future__ import annotations

import csv
import sys
from collections import defaultdict

from ..records import CONFIG, INTERIM, read_jsonl
from .domains import is_excluded, site_of

SEEDS = CONFIG / "publisher_seeds.csv"


def build(force: bool = False) -> None:
    if SEEDS.exists() and not force:
        print(f"{SEEDS} already exists (it may have been reviewed). Use --force to rebuild.")
        return
    sites: dict[str, dict] = defaultdict(lambda: {"start_urls": set(), "publishers": set(), "titles": set()})
    for rec in read_jsonl(INTERIM / "store_pages.jsonl"):
        for url in (rec.get("publisher_url"), rec.get("support_url")):
            if not url or not url.startswith("http") or is_excluded(url):
                continue
            entry = sites[site_of(url)]
            entry["start_urls"].add(url)
            if rec.get("publisher"):
                entry["publishers"].add(rec["publisher"])
            key = f"{rec['platform']}:{rec['store_id']}"
            entry["titles"].add(f"{key}={rec.get('title') or ''}")

    with SEEDS.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh)
        writer.writerow(["seed_id", "start_urls", "publishers", "titles", "reviewed"])
        for site, e in sorted(sites.items()):
            writer.writerow([
                site,
                " ".join(sorted(e["start_urls"])),
                "; ".join(sorted(e["publishers"])),
                " || ".join(sorted(e["titles"])),
                "no",
            ])
    print(f"Wrote {len(sites)} seeds to {SEEDS}. Review them and set reviewed=yes before crawling.")


if __name__ == "__main__":
    build(force="--force" in sys.argv)

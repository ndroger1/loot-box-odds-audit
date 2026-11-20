"""Collect store pages for every chart row and write data/interim/store_pages.jsonl."""

from __future__ import annotations

import csv
import logging
from collections import defaultdict

from ..polite import PoliteSession
from ..records import INTERIM, append_jsonl, check_record
from . import console, ios, steam

log = logging.getLogger(__name__)
OUT = INTERIM / "store_pages.jsonl"


def load_charts() -> list[dict]:
    with (INTERIM / "charts.csv").open(encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def main() -> None:
    if OUT.exists():
        OUT.unlink()  # regenerated from charts each run; raw captures are kept separately
    session = PoliteSession()
    console_groups: dict[tuple, list] = defaultdict(list)
    for row in load_charts():
        if not row.get("store_id"):
            log.warning("No store_id for %s %s rank %s; skipped", row["platform"], row["market"], row["rank"])
            continue
        try:
            if row["platform"] == "ios":
                found = [ios.collect(row, session)]
            elif row["platform"] == "steam":
                found = steam.collect(row, session)
            else:
                console_groups[(row["platform"], row["market"])].append(row)
                continue
        except Exception as exc:  # noqa: BLE001
            log.warning("%s %s %s failed: %s", row["platform"], row["market"], row["store_id"], exc)
            continue
        for rec in filter(None, found):
            append_jsonl(check_record(rec), OUT)

    for (platform, market), rows in console_groups.items():
        try:
            for rec in console.collect_many(rows):
                append_jsonl(check_record(rec), OUT)
        except Exception as exc:  # noqa: BLE001
            log.warning("%s %s product pages failed: %s", platform, market, exc)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    main()

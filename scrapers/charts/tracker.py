"""Chart-tracker fallback: load a chart exported from a chart tracker.

Used when a store's chart can't be collected automatically or its terms don't
allow it. Expected file: data/interim/tracker_charts/<platform>_<market>.csv
with columns rank,title,store_id,store_url,tracker (see config/README.md).
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone

from ..records import INTERIM, relpath, snapshot_date


def path_for(platform: str, market: str):
    return INTERIM / "tracker_charts" / f"{platform}_{market}.csv"


def collect(platform: str, market: str) -> list[dict]:
    path = path_for(platform, market)
    if not path.exists():
        raise FileNotFoundError(f"No tracker export at {relpath(path)}")
    retrieved_at = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(timespec="seconds")
    rows = []
    with path.open(encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            rows.append({
                "snapshot_date": snapshot_date(),
                "market": market,
                "platform": platform,
                "rank": int(row["rank"]),
                "title": row["title"],
                "store_id": row.get("store_id") or None,
                "store_url": row.get("store_url") or None,
                "publisher": None,
                "chart_scope": "tracker",
                "source": f"tracker:{row.get('tracker') or 'unspecified'}",
                "retrieved_at": retrieved_at,
                "evidence_ref": relpath(path),
            })
    return rows

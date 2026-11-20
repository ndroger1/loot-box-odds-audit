"""Paths, timestamps, and file helpers shared by every collector.

Every record written by a collector carries the fields in
config.REQUIRED_RECORD_FIELDS, so each code can be traced back to its source.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import date, datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from .config import REQUIRED_RECORD_FIELDS

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
INTERIM = DATA / "interim"
PROCESSED = DATA / "processed"
CONFIG = ROOT / "config"
CODEBOOK = ROOT / "codebook"
FIGURES = ROOT / "figures"


def snapshot_date() -> str:
    """The single snapshot date for all collection, from SNAPSHOT_DATE (YYYY-MM-DD)."""
    value = os.environ.get("SNAPSHOT_DATE", "").strip()
    if not value:
        raise RuntimeError("Set SNAPSHOT_DATE (YYYY-MM-DD) in .env before collecting.")
    date.fromisoformat(value)  # raises if malformed
    return value


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def raw_dir(*parts: str) -> Path:
    """data/raw/<snapshot>/<parts...>, created on demand."""
    path = RAW.joinpath(snapshot_date(), *parts)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_raw(content: str | bytes, *parts: str, suffix: str = ".html") -> Path:
    """Save a raw capture under data/raw and return its path (used as evidence_ref)."""
    data = content.encode("utf-8") if isinstance(content, str) else content
    digest = hashlib.sha256(data).hexdigest()[:16]
    path = raw_dir(*parts) / f"{digest}{suffix}"
    path.write_bytes(data)
    return path


def relpath(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def check_record(record: dict) -> dict:
    missing = [f for f in REQUIRED_RECORD_FIELDS if not record.get(f)]
    if missing:
        raise ValueError(f"Record is missing required fields {missing}: {record}")
    return record


def write_csv(rows: list[dict], path: Path, required: bool = True) -> Path:
    """Write rows to CSV (UTF-8 with BOM so Excel shows Korean correctly)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if required:
        for row in rows:
            check_record(row)
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return path


def append_jsonl(row: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def load_json_config(name: str) -> dict:
    return json.loads((CONFIG / name).read_text(encoding="utf-8"))

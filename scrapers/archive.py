"""Save pages that contain odds to the Wayback Machine (Save Page Now).

With Internet Archive S3-style keys (IA_ACCESS_KEY / IA_SECRET_KEY in .env) the
authenticated SPN2 API is used, which is more reliable. Without keys, the plain
https://web.archive.org/save/<url> endpoint is used.

Writes data/interim/archives.csv: url, archive_url, status, archived_at.
Already-archived URLs are skipped, so the script can be re-run after failures.
"""

from __future__ import annotations

import csv
import logging
import os
import time

import requests

from coding.dictionary import find_terms

from .polite import user_agent
from .records import INTERIM, now_utc, read_jsonl

log = logging.getLogger(__name__)
OUT = INTERIM / "archives.csv"
SPN = "https://web.archive.org/save"
DELAY = float(os.environ.get("ARCHIVE_DELAY_SECONDS", 15))


def _headers() -> dict:
    h = {"User-Agent": user_agent(), "Accept": "application/json"}
    key, secret = os.environ.get("IA_ACCESS_KEY"), os.environ.get("IA_SECRET_KEY")
    if key and secret:
        h["Authorization"] = f"LOW {key}:{secret}"
    return h


def save(url: str) -> tuple[str | None, str]:
    headers = _headers()
    if "Authorization" in headers:
        resp = requests.post(SPN, headers=headers, data={"url": url}, timeout=60)
        if resp.status_code != 200:
            return None, f"http {resp.status_code}"
        job = resp.json().get("job_id")
        if not job:
            return None, resp.json().get("message", "no job id")
        for _ in range(24):  # poll up to ~2 minutes
            time.sleep(5)
            st = requests.get(f"{SPN}/status/{job}", headers=headers, timeout=60).json()
            if st.get("status") == "success":
                return f"https://web.archive.org/web/{st['timestamp']}/{st['original_url']}", "success"
            if st.get("status") == "error":
                return None, st.get("message", "error")
        return None, "timeout"
    resp = requests.get(f"{SPN}/{url}", headers=headers, timeout=120, allow_redirects=True)
    location = resp.headers.get("Content-Location")
    if location:
        return f"https://web.archive.org{location}", "success"
    if "/web/" in resp.url:
        return resp.url, "success"
    return None, f"http {resp.status_code}"


def pages_to_archive() -> list[str]:
    urls = [p["url"] for p in read_jsonl(INTERIM / "publisher_pages.jsonl") if p.get("odds_terms")]
    urls += [p["store_url"] for p in read_jsonl(INTERIM / "store_pages.jsonl")
             if p.get("store_url") and find_terms(p.get("description", ""))["odds"]]
    return sorted(set(urls))


def main() -> None:
    done: dict[str, dict] = {}
    if OUT.exists():
        with OUT.open(encoding="utf-8-sig") as fh:
            done = {r["url"]: r for r in csv.DictReader(fh)}
    for url in pages_to_archive():
        if done.get(url, {}).get("status") == "success":
            continue
        try:
            archive_url, status = save(url)
        except requests.RequestException as exc:
            archive_url, status = None, f"error {exc.__class__.__name__}"
        done[url] = {"url": url, "archive_url": archive_url or "", "status": status, "archived_at": now_utc()}
        log.info("%s -> %s (%s)", url, archive_url, status)
        time.sleep(DELAY)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=["url", "archive_url", "status", "archived_at"])
        writer.writeheader()
        writer.writerows(done.values())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    main()

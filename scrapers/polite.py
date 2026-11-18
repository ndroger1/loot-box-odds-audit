"""A polite HTTP session that every requests-based collector should use.

It enforces the project's scraping rules:
- identifies the scraper with a User-Agent that includes a contact address,
- checks robots.txt before fetching a URL,
- waits between requests to the same host,
- returns a retrieval timestamp with each response.

Settings come from environment variables (see .env.example); nothing is hardcoded.
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import requests
from dotenv import load_dotenv

load_dotenv()

PROJECT_NAME = "LootBoxOddsAudit"
PROJECT_VERSION = "0.1"


def user_agent() -> str:
    contact = os.environ.get("SCRAPER_CONTACT")
    if not contact:
        raise RuntimeError("Set SCRAPER_CONTACT in .env before running any collector.")
    return f"{PROJECT_NAME}/{PROJECT_VERSION} (academic research; contact: {contact})"


class RobotsDisallowed(Exception):
    """Raised when robots.txt does not allow fetching a URL."""


class PoliteSession:
    def __init__(self, delay_seconds: float | None = None):
        self.delay = float(delay_seconds or os.environ.get("REQUEST_DELAY_SECONDS", 3))
        self.session = requests.Session()
        self.session.headers["User-Agent"] = user_agent()
        self._robots: dict[str, RobotFileParser] = {}
        self._last_request: dict[str, float] = {}

    def _robots_for(self, url: str) -> RobotFileParser:
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        if origin not in self._robots:
            parser = RobotFileParser()
            try:
                resp = self.session.get(f"{origin}/robots.txt", timeout=20)
                if resp.status_code == 200:
                    parser.parse(resp.text.splitlines())
                elif resp.status_code in (401, 403):
                    parser.disallow_all = True   # treat a blocked robots.txt as "no"
                else:
                    parser.allow_all = True      # no robots.txt means no restrictions
            except requests.RequestException:
                parser.disallow_all = True       # can't confirm permission, so don't fetch
            self._robots[origin] = parser
        return self._robots[origin]

    def _wait_for(self, host: str) -> None:
        last = self._last_request.get(host)
        if last is not None:
            remaining = self.delay - (time.monotonic() - last)
            if remaining > 0:
                time.sleep(remaining)
        self._last_request[host] = time.monotonic()

    def get(self, url: str, **kwargs) -> tuple[requests.Response, str]:
        """Fetch a URL politely. Returns (response, retrieved_at as ISO 8601 UTC)."""
        if not self._robots_for(url).can_fetch(self.session.headers["User-Agent"], url):
            raise RobotsDisallowed(url)
        self._wait_for(urlsplit(url).netloc)
        kwargs.setdefault("timeout", 30)
        resp = self.session.get(url, **kwargs)
        retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        return resp, retrieved_at

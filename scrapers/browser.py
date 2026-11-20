"""Playwright helpers for the console stores (PlayStation, Xbox, Nintendo).

Same rules as polite.py: check robots.txt, wait between page loads, identify the
scraper in the User-Agent, never log in. Pages are loaded with the market's
locale so the store serves that market's version where it uses locale paths.
"""

from __future__ import annotations

import os
import time
from contextlib import contextmanager
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import requests

from .polite import RobotsDisallowed, user_agent

LOCALES = {"KR": "ko-KR", "GB": "en-GB", "US": "en-US", "BE": "nl-BE"}

_robots: dict[str, RobotFileParser] = {}


def robots_allows(url: str) -> bool:
    parts = urlsplit(url)
    origin = f"{parts.scheme}://{parts.netloc}"
    if origin not in _robots:
        parser = RobotFileParser()
        try:
            resp = requests.get(f"{origin}/robots.txt", headers={"User-Agent": user_agent()}, timeout=20)
            if resp.status_code == 200:
                parser.parse(resp.text.splitlines())
            elif resp.status_code in (401, 403):
                parser.disallow_all = True
            else:
                parser.allow_all = True
        except requests.RequestException:
            parser.disallow_all = True
        _robots[origin] = parser
    return _robots[origin].can_fetch(user_agent(), url)


@contextmanager
def market_page(market: str):
    """Yield a Playwright page set up for one market. Import is local so the rest
    of the project works without Playwright installed."""
    from playwright.sync_api import sync_playwright

    delay = float(os.environ.get("REQUEST_DELAY_SECONDS", 3))
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=user_agent(), locale=LOCALES[market])
        page = context.new_page()
        original_goto = page.goto
        last = {"t": 0.0}

        def polite_goto(url: str, **kwargs):
            if not robots_allows(url):
                raise RobotsDisallowed(url)
            wait = delay - (time.monotonic() - last["t"])
            if wait > 0:
                time.sleep(wait)
            last["t"] = time.monotonic()
            kwargs.setdefault("wait_until", "networkidle")
            kwargs.setdefault("timeout", 60_000)
            return original_goto(url, **kwargs)

        page.goto = polite_goto  # type: ignore[method-assign]
        try:
            yield page
        finally:
            context.close()
            browser.close()

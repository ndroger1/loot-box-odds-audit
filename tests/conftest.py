import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setenv("SNAPSHOT_DATE", "2026-01-15")
    monkeypatch.setenv("SCRAPER_CONTACT", "test@example.invalid")

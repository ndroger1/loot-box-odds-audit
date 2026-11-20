"""Offline tests: parsers on made-up API payloads, domain rules, and the terms gate.
No network access."""

import pytest

from scrapers.charts import ios as ios_chart
from scrapers.charts import steam as steam_chart
from scrapers.publisher.domains import is_excluded, same_site, site_of
from scrapers.store_pages import steam as steam_store
from scrapers.sources import SourceNotPermitted, require_permitted


def test_ios_chart_parse():
    payload = {"feed": {"entry": [
        {"im:name": {"label": "Game A"}, "id": {"label": "https://apps.apple.com/kr/app/id1",
                                                 "attributes": {"im:id": "1"}},
         "im:artist": {"label": "Pub A"}},
        {"im:name": {"label": "Game B"}, "id": {"label": "u", "attributes": {"im:id": "2"}}},
    ]}}
    rows = ios_chart.parse(payload, "KR", "src", "2026-01-15T00:00:00+00:00", "raw/x.json")
    assert [r["rank"] for r in rows] == [1, 2]
    assert rows[0]["store_id"] == "1" and rows[0]["publisher"] == "Pub A"
    assert all(r["snapshot_date"] == "2026-01-15" for r in rows)


def test_steam_chart_scope():
    payload = {"response": {"country_code": "kr", "ranks": [{"rank": 1, "appid": 10, "item": {"name": "X"}}]}}
    rows = steam_chart.parse(payload, "KR", "src", "t", "e")
    assert rows[0]["chart_scope"] == "country" and rows[0]["store_id"] == "10"
    payload["response"]["country_code"] = "US"
    assert steam_chart.parse(payload, "KR", "src", "t", "e")[0]["chart_scope"] == "global"


def test_steam_store_parse():
    payload = {"10": {"success": True, "data": {
        "name": "X", "publishers": ["Pub"], "website": "https://pub.com",
        "support_info": {"url": "https://help.pub.com"},
        "short_description": "<b>Fun</b>", "about_the_game": "", "detailed_description": "",
        "content_descriptors": {"notes": "Includes Random Items"},
        "price_overview": {"final_formatted": "₩10,000"}}}}
    row = steam_store.parse(payload, {"market": "KR", "store_id": "10", "store_url": "u"}, "koreana", "s", "t", "e")
    assert row["description"] == "Fun" and "Random Items" in row["label_text"]
    assert row["publisher_url"] == "https://pub.com" and row["price_info"] == "₩10,000"
    assert steam_store.parse({"10": {"success": False}}, {"market": "KR", "store_id": "10"}, "x", "s", "t", "e") is None


def test_domains():
    assert site_of("https://support.nexon.co.kr/a") == "nexon.co.kr"
    assert same_site("https://help.pub.com/x", "pub.com")
    assert is_excluded("https://store.steampowered.com/app/1")


def test_terms_gate_blocks_unchecked_sources():
    with pytest.raises(SourceNotPermitted):
        require_permitted("playstation")

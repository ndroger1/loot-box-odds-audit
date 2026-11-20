"""Tests for the dictionary, rules, and index on small made-up inputs (not study data)."""

import numpy as np
import pandas as pd

from coding.dictionary import find_terms
from coding.index import add_index
from coding.rules import build, numeric_odds, title_key


def test_terms_match_words_not_fragments():
    assert "odds" in find_terms("View the odds for each banner")["odds"]
    assert find_terms("an oddsmaker said")["odds"] == []


def test_korean_terms_match_with_particles():
    assert "확률" in find_terms("아이템 확률은 다음과 같습니다")["odds"]


def test_label_found():
    assert find_terms("In-Game Purchases (Includes Random Items)")["label"]


def test_numeric_odds_and_price():
    has, n, price = numeric_odds("Drop rates: SSR 0.6%, SR 5.1%, R 94.3%. One pull costs £1.99")
    assert has and n == 3 and price
    assert numeric_odds("No rates here, only probability talk") == (False, 0, False)


def test_title_key():
    assert title_key("Genshin Impact: Version 5") == "genshin impact"
    assert title_key("Ab") == ""


def _charts(rows):
    base = {"snapshot_date": "2026-01-15", "chart_scope": "country", "source": "s", "evidence_ref": "e"}
    return pd.DataFrame([{**base, **r} for r in rows])


def test_build_codes_store_and_publisher():
    charts = _charts([
        {"market": "KR", "platform": "ios", "rank": 1, "title": "Dragon Gacha", "store_id": "1"},
        {"market": "US", "platform": "ios", "rank": 2, "title": "Quiet Puzzle", "store_id": "2"},
        {"market": "GB", "platform": "ios", "rank": 3, "title": "Unseen Game", "store_id": "3"},
    ])
    store = [
        {"market": "KR", "platform": "ios", "store_id": "1", "label_text": "", "description": "가챠 게임",
         "evidence_ref": "a"},
        {"market": "US", "platform": "ios", "store_id": "2", "label_text": "", "description": "Relaxing puzzles.",
         "evidence_ref": "b"},
    ]
    pages = [
        {"seed_id": "dragon.com", "market": "KR", "url": "https://dragon.com/support/dragon-gacha/rates",
         "depth": 2, "page_title": "Dragon Gacha 확률 정보", "html_lang": "ko-KR", "odds_terms": ["확률"],
         "lootbox_terms": [], "text": "Dragon Gacha 확률 정보: 전설 1.5%, 영웅 10%, 일반 88.5% 천장 90회",
         "evidence_ref": "c"},
        {"seed_id": "puzzle.com", "market": "US", "url": "https://puzzle.com/", "depth": 0,
         "page_title": "Quiet Puzzle", "html_lang": "en", "odds_terms": [], "lootbox_terms": [],
         "text": "Quiet Puzzle home", "evidence_ref": "d"},
    ]
    seeds = {"ios:1": "dragon.com", "ios:2": "puzzle.com"}
    df = add_index(build(charts, store, pages, seeds, {}))
    kr, us, gb = df.iloc[0], df.iloc[1], df.iloc[2]

    assert kr["lootbox_present"] == "yes" and kr["odds_disclosed"] == "yes"
    assert kr["clicks_to_odds"] == 2 and kr["odds_in_market_language"] == "yes"
    assert kr["pity_disclosed"] == "yes" and kr["odds_placement"] == "publisher_site"
    assert us["lootbox_present"] == "no" and us["odds_disclosed"] == "not_applicable"
    assert gb["lootbox_present"] == "unknown" and gb["odds_disclosed"] == "unknown"
    assert np.isnan(us["pdi"])


def test_hidden_and_store_only_odds_get_scores():
    """Regression for rules 0.1: these cases had a missing index score."""
    charts = _charts([
        {"market": "KR", "platform": "ios", "rank": 1, "title": "Hidden Gacha", "store_id": "1"},
        {"market": "GB", "platform": "steam", "rank": 1, "title": "Store Odds Game", "store_id": "2"},
        {"market": "BE", "platform": "steam", "rank": 1, "title": "Store Odds Game", "store_id": "2"},
    ])
    english_odds = ("Card packs! Drop rates: Legendary 1%, Epic 9%, Common 90%. "
                    "Each pack costs £2.99.")
    store = [
        {"market": "KR", "platform": "ios", "store_id": "1", "label_text": "Includes Random Items",
         "description": "가챠 게임", "evidence_ref": "a"},
        {"market": "GB", "platform": "steam", "store_id": "2", "label_text": "", "description": english_odds,
         "evidence_ref": "b"},
        {"market": "BE", "platform": "steam", "store_id": "2", "label_text": "", "description": english_odds,
         "evidence_ref": "c"},
    ]
    pages = [
        {"seed_id": "hidden.com", "market": "KR", "url": "https://hidden.com/", "depth": 0,
         "page_title": "Hidden Gacha", "html_lang": "ko", "odds_terms": [], "lootbox_terms": [],
         "text": "Hidden Gacha 공식 사이트", "evidence_ref": "d"},
        {"seed_id": "store.com", "market": "GB", "url": "https://store.com/", "depth": 0,
         "page_title": "Store Odds Game", "html_lang": "en", "odds_terms": [], "lootbox_terms": [],
         "text": "Store Odds Game home", "evidence_ref": "e"},
        {"seed_id": "store.com", "market": "BE", "url": "https://store.com/", "depth": 0,
         "page_title": "Store Odds Game", "html_lang": "en", "odds_terms": [], "lootbox_terms": [],
         "text": "Store Odds Game home", "evidence_ref": "f"},
    ]
    seeds = {"ios:1": "hidden.com", "steam:2": "store.com"}
    df = add_index(build(charts, store, pages, seeds, {}))
    hidden, gb, be = df.iloc[0], df.iloc[1], df.iloc[2]

    assert hidden["odds_disclosed"] == "no"
    assert hidden["odds_in_market_language"] == "not_applicable"
    assert hidden["pdi"] == 1  # only the store label

    assert gb["odds_placement"] == "store_page"
    assert gb["odds_price_linked"] == "yes" and gb["odds_in_market_language"] == "yes"
    assert gb["pity_disclosed"] == "no"
    # disclosed, on store, <=2 clicks, <=1 click, language, price, 3 rates (>=2)
    assert gb["pdi"] == 7

    assert be["odds_in_market_language"] == "no"  # English-only odds in Belgium
    assert be["dp_language_barrier_candidate"] == "yes"
    assert be["pdi"] == 6


def test_index_bounds():
    row = {"lootbox_present": "yes", "odds_disclosed": "yes", "store_odds_numeric": "no",
           "clicks_to_odds": 1, "odds_in_market_language": "unknown", "odds_price_linked": "no",
           "pity_disclosed": "no", "store_label_random_items": "yes", "rates_count": 6}
    out = add_index(pd.DataFrame([row])).iloc[0]
    assert np.isnan(out["pdi"])  # one component unknown
    assert out["pdi_unknown_components"] == 1
    assert out["pdi_min"] == 6 and out["pdi_max"] == 7

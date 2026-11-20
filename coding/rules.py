"""Apply the coding rules to collected text and write data/processed/coded_units.csv.

Unit of analysis: one title on one platform in one market (one row of charts.csv).
Every code is 'yes', 'no', or 'unknown'. When the evidence doesn't settle a
question, the code is 'unknown', never a guess.

Rule set version is recorded on every row; log each change in
codebook/rule_revisions.md and bump RULES_VERSION.
"""

from __future__ import annotations

import csv
import re
import unicodedata
from collections import defaultdict

import pandas as pd

from scrapers.records import CONFIG, INTERIM, PROCESSED, read_jsonl

from .dictionary import find_terms, windows_with_language

RULES_VERSION = "0.2-draft"
YES, NO, UNKNOWN = "yes", "no", "unknown"
PERCENT = re.compile(r"\d{1,3}(?:[.,]\d+)?\s?%")
MARKET_LANGS = {"KR": ("ko",), "GB": ("en",), "US": ("en",), "BE": ("nl", "fr", "de")}
OBSTRUCTION_MIN_CLICKS = 3


# ---------------------------------------------------------------- helpers
def norm(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "").lower()
    return re.sub(r"[^\w\s]", " ", text)


def title_key(title: str) -> str:
    """Short form of a title used to find it in publisher pages: the part before
    a colon or dash subtitle, normalised. Too-short keys return '' (no match)."""
    base = re.split(r"[:\-–—|]", title or "")[0]
    key = " ".join(norm(base).split())
    return key if len(key) >= 4 else ""


def odds_evidence(text: str) -> dict:
    """What sits near the odds terms that have a percentage beside them:
    distinct rates, whether a price or a pity term is nearby, and the languages
    of those odds terms (from the dictionary)."""
    rates: set[str] = set()
    price = pity = False
    langs: set[str] = set()
    for snippet, lang in windows_with_language(text, "odds"):
        found = PERCENT.findall(snippet)
        if not found:
            continue
        rates.update(found)
        hits = find_terms(snippet)
        price |= bool(hits["price"])
        pity |= bool(hits["pity"])
        langs.add(lang)
    return {"rates": len(rates), "price": price, "pity": pity, "langs": langs}


def numeric_odds(text: str) -> tuple[bool, int, bool]:
    """(has numeric odds, number of distinct rates near odds terms, price near those rates)."""
    ev = odds_evidence(text)
    return ev["rates"] > 0, ev["rates"], ev["price"]


def language_code(langs: set[str], market: str) -> str:
    """yes if any odds term with rates is in one of the market's languages."""
    if not langs:
        return UNKNOWN
    return YES if langs & set(MARKET_LANGS[market]) else NO


def merge(*values):
    """Combine a code across sources that show odds. None = this source shows no
    odds (ignored); UNKNOWN = this source wasn't checked, so it could change the answer."""
    vals = [v for v in values if v is not None]
    if YES in vals:
        return YES
    if UNKNOWN in vals:
        return UNKNOWN
    if NO in vals:
        return NO
    return None


def any_yes(values) -> bool:
    return any(v == YES for v in values)


# ---------------------------------------------------------------- store codes
def code_store(records: list[dict], market: str) -> dict:
    """Store-page codes. store_price/store_language/store_pity are None when the
    store shows no numeric odds, and UNKNOWN when the store wasn't collected."""
    if not records:
        return {"store_collected": NO, "store_label_random_items": UNKNOWN,
                "store_lootbox_terms": UNKNOWN, "store_odds_numeric": UNKNOWN,
                "store_rates_count": None, "store_price": UNKNOWN, "store_language": UNKNOWN,
                "store_pity": UNKNOWN, "store_evidence": ""}
    label = lootbox = price = pity = False
    rates = 0
    langs: set[str] = set()
    for rec in records:
        text = f"{rec.get('label_text', '')} {rec.get('description', '')}"
        hits = find_terms(text)
        label |= bool(hits["label"])
        lootbox |= bool(hits["lootbox"])
        ev = odds_evidence(text)
        rates = max(rates, ev["rates"])
        price |= ev["price"]
        pity |= ev["pity"]
        langs |= ev["langs"]
    numeric = rates > 0
    return {
        "store_collected": YES,
        "store_label_random_items": YES if label else NO,
        "store_lootbox_terms": YES if lootbox else NO,
        "store_odds_numeric": YES if numeric else NO,
        "store_rates_count": rates,
        "store_price": (YES if price else NO) if numeric else None,
        "store_language": language_code(langs, market) if numeric else None,
        "store_pity": (YES if pity else NO) if numeric else None,
        "store_evidence": " ".join(sorted({r["evidence_ref"] for r in records})),
    }


# ---------------------------------------------------------------- publisher codes
def load_seeds() -> dict[str, str]:
    """Map 'platform:store_id' -> seed_id from the reviewed seed file."""
    path = CONFIG / "publisher_seeds.csv"
    mapping: dict[str, str] = {}
    if not path.exists():
        return mapping
    with path.open(encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            if row.get("reviewed", "").strip().lower() != "yes":
                continue
            for item in row["titles"].split(" || "):
                key = item.split("=", 1)[0].strip()
                if key:
                    mapping[key] = row["seed_id"]
    return mapping


def code_publisher(pages: list[dict], crawled: bool, title: str, market: str,
                   archives: dict[str, str]) -> dict:
    """Publisher-site codes. pub_price/pub_language/pub_pity are None when the
    crawl found no numeric odds for the title, and UNKNOWN when it wasn't crawled."""
    blank = {"publisher_crawled": NO, "pub_odds_page": UNKNOWN, "pub_odds_numeric": UNKNOWN,
             "clicks_to_odds": None, "pub_rates_count": None, "pub_price": UNKNOWN,
             "pub_language": UNKNOWN, "pub_pity": UNKNOWN,
             "pub_lootbox_terms": UNKNOWN, "odds_url": "", "odds_archive_url": "", "pub_evidence": ""}
    if not crawled:
        return blank
    key = title_key(title)
    about_title = [p for p in pages if key and key in norm(" ".join(
        [p.get("page_title", ""), p.get("url", ""), p.get("text", "")[:20000]]))]
    odds_pages = [p for p in about_title if p.get("odds_terms")]
    numeric_pages = [(p, ev) for p in odds_pages if (ev := odds_evidence(p.get("text", "")))["rates"]]
    out = dict(blank, publisher_crawled=YES, pub_price=None, pub_language=None, pub_pity=None)
    out["pub_lootbox_terms"] = YES if any(p.get("lootbox_terms") for p in about_title) else NO
    out["pub_odds_page"] = YES if odds_pages else NO
    out["pub_odds_numeric"] = YES if numeric_pages else NO
    if not numeric_pages:
        return out
    best, _ = min(numeric_pages, key=lambda t: t[0]["depth"])
    # Page language: the page's declared <html lang> if it has one, otherwise the
    # language of the odds terms found beside the rates.
    declared = (best.get("html_lang") or "").lower()
    if declared:
        language = YES if declared.startswith(MARKET_LANGS[market]) else NO
    else:
        language = language_code(set().union(*(ev["langs"] for _, ev in numeric_pages)), market)
    out.update({
        "clicks_to_odds": int(best["depth"]),
        "pub_rates_count": max(ev["rates"] for _, ev in numeric_pages),
        "pub_price": YES if any(ev["price"] for _, ev in numeric_pages) else NO,
        "pub_language": language,
        "pub_pity": YES if any(ev["pity"] for _, ev in numeric_pages) else NO,
        "odds_url": best["url"],
        "odds_archive_url": archives.get(best["url"], ""),
        "pub_evidence": " ".join(sorted({p["evidence_ref"] for p, _ in numeric_pages})),
    })
    return out


# ---------------------------------------------------------------- combined codes
def combine(row: dict) -> dict:
    store_num, pub_num = row["store_odds_numeric"], row["pub_odds_numeric"]
    signals = [row["store_label_random_items"], row["store_lootbox_terms"],
               row["pub_lootbox_terms"], store_num, pub_num]
    if any_yes(signals):
        lootbox = YES
    elif row["store_collected"] == YES and row["publisher_crawled"] == YES and all(s == NO for s in signals):
        lootbox = NO
    else:
        lootbox = UNKNOWN

    if lootbox == NO:
        disclosed = "not_applicable"
    elif any_yes([store_num, pub_num]):
        disclosed = YES
    elif lootbox == YES and store_num == NO and pub_num == NO:
        disclosed = NO
    else:
        disclosed = UNKNOWN

    rates = max([r for r in (row["store_rates_count"], row["pub_rates_count"]) if r is not None], default=None)
    if disclosed == YES:
        completeness = "numeric"
    elif disclosed == NO and (row["pub_odds_page"] == YES):
        completeness = "terms_only"
    elif disclosed == NO:
        completeness = "none"
    else:
        completeness = disclosed  # unknown / not_applicable

    # Price, language, and pity describe the odds, so they are coded only when odds
    # are disclosed. No odds -> not_applicable (scores 0 in the index).
    def about_odds(store_val, pub_val):
        if disclosed == YES:
            return merge(store_val, pub_val) or UNKNOWN
        return "not_applicable" if disclosed in (NO, "not_applicable") else UNKNOWN

    price = about_odds(row["store_price"], row["pub_price"])
    language = about_odds(row["store_language"], row["pub_language"])
    pity = about_odds(row["store_pity"], row["pub_pity"])

    clicks = row["clicks_to_odds"]
    if store_num == YES:
        placement = "store_page"
    elif pub_num == YES:
        placement = "publisher_site"
    else:
        placement = "none" if disclosed == NO else disclosed

    return {
        "lootbox_present": lootbox,
        "odds_disclosed": disclosed,
        "disclosure_completeness": completeness,
        "rates_count": rates,
        "odds_placement": placement,
        "odds_price_linked": price,
        "odds_in_market_language": language,
        "pity_disclosed": pity,
        "dp_obstruction_candidate": (YES if clicks is not None and clicks >= OBSTRUCTION_MIN_CLICKS
                                     else NO if clicks is not None else UNKNOWN),
        "dp_language_barrier_candidate": {YES: NO, NO: YES}.get(language, language),
    }


# ---------------------------------------------------------------- pipeline
def build(charts: pd.DataFrame, store_records: list[dict], pub_pages: list[dict],
          seeds: dict[str, str], archives: dict[str, str]) -> pd.DataFrame:
    store_by_unit = defaultdict(list)
    for rec in store_records:
        store_by_unit[(rec["market"], rec["platform"], str(rec["store_id"]))].append(rec)
    pages_by_seed = defaultdict(list)
    for p in pub_pages:
        pages_by_seed[(p["seed_id"], p["market"])].append(p)

    rows = []
    for unit in charts.to_dict("records"):
        market, platform, sid = unit["market"], unit["platform"], str(unit.get("store_id") or "")
        seed = seeds.get(f"{platform}:{sid}")
        pages = pages_by_seed.get((seed, market), []) if seed else []
        row = {
            "snapshot_date": unit["snapshot_date"], "market": market, "platform": platform,
            "rank": unit["rank"], "title": unit["title"], "store_id": sid,
            "title_key": title_key(unit["title"]), "chart_scope": unit.get("chart_scope"),
            "chart_source": unit["source"], "publisher_seed": seed or "",
        }
        row.update(code_store(store_by_unit.get((market, platform, sid), []), market))
        row.update(code_publisher(pages, bool(pages), unit["title"], market, archives))
        row.update(combine(row))
        row["evidence_refs"] = " ".join(filter(None, [unit["evidence_ref"], row.pop("store_evidence"),
                                                      row.pop("pub_evidence")]))
        row["rules_version"] = RULES_VERSION
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> pd.DataFrame:
    from .index import add_index

    charts = pd.read_csv(INTERIM / "charts.csv", dtype={"store_id": str}, encoding="utf-8-sig")
    archives_path = INTERIM / "archives.csv"
    archives = {}
    if archives_path.exists():
        a = pd.read_csv(archives_path, encoding="utf-8-sig").fillna("")
        archives = dict(zip(a["url"], a["archive_url"]))
    df = build(charts, read_jsonl(INTERIM / "store_pages.jsonl"),
               read_jsonl(INTERIM / "publisher_pages.jsonl"), load_seeds(), archives)
    df = add_index(df)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSED / "coded_units.csv", index=False, encoding="utf-8-sig")
    return df


if __name__ == "__main__":
    out = main()
    print(f"Coded {len(out)} units -> data/processed/coded_units.csv")

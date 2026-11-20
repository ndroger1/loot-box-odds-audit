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

from .dictionary import find_terms, windows

RULES_VERSION = "0.1-draft"
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


def numeric_odds(text: str) -> tuple[bool, int, bool]:
    """(has numeric odds, number of distinct rates near odds terms, price near those rates)."""
    rates: set[str] = set()
    price = False
    for snippet in windows(text, "odds"):
        found = PERCENT.findall(snippet)
        rates.update(found)
        if found and find_terms(snippet)["price"]:
            price = True
    return bool(rates), len(rates), price


def any_yes(values) -> bool:
    return any(v == YES for v in values)


# ---------------------------------------------------------------- store codes
def code_store(records: list[dict]) -> dict:
    if not records:
        return {"store_collected": NO, "store_label_random_items": UNKNOWN,
                "store_lootbox_terms": UNKNOWN, "store_odds_numeric": UNKNOWN,
                "store_rates_count": None, "store_evidence": ""}
    label = lootbox = numeric = False
    rates = 0
    for rec in records:
        text = f"{rec.get('label_text', '')} {rec.get('description', '')}"
        hits = find_terms(text)
        label |= bool(hits["label"])
        lootbox |= bool(hits["lootbox"])
        has_num, n, _ = numeric_odds(text)
        numeric |= has_num
        rates = max(rates, n)
    return {
        "store_collected": YES,
        "store_label_random_items": YES if label else NO,
        "store_lootbox_terms": YES if lootbox else NO,
        "store_odds_numeric": YES if numeric else NO,
        "store_rates_count": rates,
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
    blank = {"publisher_crawled": NO, "pub_odds_page": UNKNOWN, "pub_odds_numeric": UNKNOWN,
             "clicks_to_odds": None, "pub_rates_count": None, "odds_price_linked": UNKNOWN,
             "odds_in_market_language": UNKNOWN, "pity_disclosed": UNKNOWN,
             "pub_lootbox_terms": UNKNOWN, "odds_url": "", "odds_archive_url": "", "pub_evidence": ""}
    if not crawled:
        return blank
    key = title_key(title)
    about_title = [p for p in pages if key and key in norm(" ".join(
        [p.get("page_title", ""), p.get("url", ""), p.get("text", "")[:20000]]))]
    odds_pages = [p for p in about_title if p.get("odds_terms")]
    numeric_pages = []
    for p in odds_pages:
        has_num, n, price = numeric_odds(p.get("text", ""))
        if has_num:
            numeric_pages.append((p, n, price))
    out = dict(blank, publisher_crawled=YES)
    out["pub_lootbox_terms"] = YES if any(p.get("lootbox_terms") for p in about_title) else NO
    out["pub_odds_page"] = YES if odds_pages else NO
    out["pub_odds_numeric"] = YES if numeric_pages else NO
    if not numeric_pages:
        return out
    best, n, _ = min(numeric_pages, key=lambda t: t[0]["depth"])
    langs = MARKET_LANGS[market]
    lang = (best.get("html_lang") or "").lower()
    out.update({
        "clicks_to_odds": int(best["depth"]),
        "pub_rates_count": max(t[1] for t in numeric_pages),
        "odds_price_linked": YES if any(t[2] for t in numeric_pages) else NO,
        "odds_in_market_language": (YES if lang.startswith(langs) else NO) if lang else UNKNOWN,
        "pity_disclosed": YES if any(find_terms(t[0].get("text", ""))["pity"] for t in numeric_pages) else NO,
        "odds_url": best["url"],
        "odds_archive_url": archives.get(best["url"], ""),
        "pub_evidence": " ".join(sorted({t[0]["evidence_ref"] for t in numeric_pages})),
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
        "dp_obstruction_candidate": (YES if clicks is not None and clicks >= OBSTRUCTION_MIN_CLICKS
                                     else NO if clicks is not None else UNKNOWN),
        "dp_language_barrier_candidate": {YES: NO, NO: YES}.get(row["odds_in_market_language"], UNKNOWN),
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
        row.update(code_store(store_by_unit.get((market, platform, sid), [])))
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

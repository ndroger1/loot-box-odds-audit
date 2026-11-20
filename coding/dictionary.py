"""Load codebook/keyword_dictionary.csv and find terms in text.

Matching is case-insensitive. Latin-script terms must match on word boundaries
(so 'odds' does not match 'oddsmaker'); Korean terms match anywhere, because
Korean attaches particles directly to nouns (확률은, 확률을).
"""

from __future__ import annotations

import csv
import re
from functools import lru_cache
from pathlib import Path

DICTIONARY = Path(__file__).resolve().parents[1] / "codebook" / "keyword_dictionary.csv"
HANGUL = re.compile(r"[가-힣]")
RADIUS = 300  # characters either side of a term that count as "near" it


@lru_cache(maxsize=1)
def patterns() -> dict[str, list[tuple[str, re.Pattern, str]]]:
    """category -> list of (term, compiled pattern, language code)."""
    out: dict[str, list[tuple[str, re.Pattern, str]]] = {}
    with DICTIONARY.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            term = row["term"]
            if row["is_regex"].strip().lower() == "yes":
                rx = re.compile(term, re.I)
            elif HANGUL.search(term):
                rx = re.compile(re.escape(term), re.I)
            else:
                rx = re.compile(r"(?<!\w)" + re.escape(term) + r"(?!\w)", re.I)
            out.setdefault(row["category"], []).append((term, rx, row["language"].strip()))
    return out


def find_terms(text: str) -> dict[str, list[str]]:
    """Return the dictionary terms found in text, by category."""
    text = text or ""
    found = {cat: sorted({term for term, rx, _ in pats if rx.search(text)})
             for cat, pats in patterns().items()}
    for cat in ("odds", "lootbox", "label", "pity", "percent", "price"):
        found.setdefault(cat, [])
    return found


def windows(text: str, category: str, radius: int = RADIUS) -> list[str]:
    """Text snippets around each match of a category, for proximity rules."""
    return [snippet for snippet, _ in windows_with_language(text, category, radius)]


def windows_with_language(text: str, category: str, radius: int = RADIUS) -> list[tuple[str, str]]:
    """(snippet, language of the matched term) around each match of a category."""
    text = text or ""
    out = []
    for _, rx, lang in patterns().get(category, []):
        for m in rx.finditer(text):
            out.append((text[max(0, m.start() - radius): m.end() + radius], lang))
    return out


def count_matches(text: str, category: str) -> int:
    return sum(len(rx.findall(text or "")) for _, rx, _ in patterns().get(category, []))

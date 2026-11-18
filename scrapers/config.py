"""Shared constants for every collector.

Keep labels here so scrapers, coding rules, and notebooks all use the same codes.
"""

# ISO 3166-1 alpha-2 market codes and their regulatory regime
MARKETS = {
    "KR": "legal_mandate",
    "GB": "self_regulation",
    "US": "enforcement_based",
    "BE": "ban",
}

# Platform labels and how many chart positions to collect per market
PLATFORMS = {
    "ios": 50,          # iPhone App Store, top grossing
    "steam": 50,        # Steam Top Sellers (record whether country or global chart)
    "playstation": 25,  # PlayStation Store best-sellers
    "xbox": 25,         # Xbox Store best-sellers
    "nintendo": 25,     # Nintendo eShop best-sellers
}

# If a store's chart collector fails outright, fall back to this many titles
# from a chart tracker rather than delaying the analysis.
FALLBACK_TOP_N = 10

# Languages to search for odds-related terms in each market (besides English)
MARKET_LANGUAGES = {
    "KR": ["ko"],
    "GB": [],
    "US": [],
    "BE": ["nl", "fr", "de"],
}

# Every collected record must carry these fields
REQUIRED_RECORD_FIELDS = [
    "snapshot_date",
    "market",
    "platform",
    "source",          # API or URL the record came from
    "retrieved_at",    # ISO 8601 UTC timestamp
    "evidence_ref",    # Wayback archive URL or local capture path
]

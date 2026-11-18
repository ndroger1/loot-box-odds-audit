# Scrapers

Collectors for the three stages of data collection. All of them run on the same snapshot date.

| Stage | Source | Method |
|---|---|---|
| 1. Charts | Each store's best-seller chart per market | Official API where one exists; chart-tracker API as fallback |
| 2. Store pages | App Store, Steam | iTunes Lookup API, Steam storefront API (country-specific) |
| 2. Store pages | PlayStation, Xbox, Nintendo | Playwright on public store pages, only where the store's terms allow it |
| 3. Publisher sites | Official publisher and support sites | Scrapy crawler; crawl depth from the homepage = clicks to reach odds |

## Shared code

- `config.py`: market codes, platform labels, chart sizes, required record fields.
- `polite.py`: HTTP session that checks robots.txt, rate-limits by host, and sends an identifying User-Agent. Use it for every `requests` call. Scrapy and Playwright collectors should apply the same rules through their own settings (`ROBOTSTXT_OBEY`, `DOWNLOAD_DELAY`, `USER_AGENT`).

## Rules

- Prefer official APIs over scraping.
- Collect only public pages. Never log in.
- If a store's terms prohibit automated access, use a chart tracker's API or narrow that store's sample instead.
- Save raw responses to `data/raw/` (private) and record `snapshot_date`, `source`, `retrieved_at`, and `evidence_ref` on every record.
- Save pages that contain odds to the Wayback Machine (Save Page Now) and store the archive URL.

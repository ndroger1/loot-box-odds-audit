# Codebook (draft)

> **Status: DRAFT.** These definitions match coding rules version `0.2-draft` (`coding/rules.py`). Review and approve them before the snapshot is coded. Log every change in `rule_revisions.md`.

Unit of analysis: one title on one platform in one market (one row of `data/interim/charts.csv`).

All categorical codes take `yes`, `no`, or `unknown`. `unknown` means the collected evidence does not settle the question; it is never replaced by a guess.

## Identifiers and provenance

| Variable | Meaning |
|---|---|
| `snapshot_date` | The single collection date |
| `market` | `KR`, `GB`, `US`, `BE` |
| `platform` | `ios`, `steam`, `playstation`, `xbox`, `nintendo` |
| `rank` | Chart position on the snapshot date |
| `title`, `store_id` | Title and store identifier as listed on the chart |
| `title_key` | Short normalised title used to match publisher pages (part before any subtitle; blank if under 4 characters) |
| `chart_scope` | `country`, `global` (Steam ignored the country), or `tracker` (fallback export) |
| `chart_source` | API or URL of the chart |
| `publisher_seed` | Publisher site matched from the reviewed seed file |
| `evidence_refs` | Local capture paths for every record used |
| `odds_url`, `odds_archive_url` | Publisher page used for odds codes and its Wayback Machine copy |
| `rules_version` | Version of the coding rules that produced the row |

## Store-page codes

| Variable | `yes` when | `no` when | `unknown` when |
|---|---|---|---|
| `store_collected` | A store record was collected | No store record | – |
| `store_label_random_items` | A label term (e.g. "Includes Random Items") appears in the store's label or description text | Store collected, no label term | Store not collected |
| `store_lootbox_terms` | A loot box term appears in store text | Store collected, none found | Store not collected |
| `store_odds_numeric` | An odds term appears within 300 characters of a percentage | Store collected, none found | Store not collected |

## Publisher-site codes

A publisher page counts for a title only if the title's `title_key` appears in the page title, URL, or text.

| Variable | Meaning |
|---|---|
| `publisher_crawled` | The title's publisher site was crawled for this market |
| `pub_odds_page` | A page about the title contains an odds term |
| `pub_odds_numeric` | Such a page has an odds term within 300 characters of a percentage |
| `clicks_to_odds` | Crawl depth (links from the start page, breadth-first) of the shallowest page with numeric odds |
| `pub_price`, `pub_language`, `pub_pity` | Price, language, and pity evidence from the publisher's numeric-odds pages (see "Codes that describe the odds"). Blank if the crawl found no numeric odds; `unknown` if not crawled |

The store-page equivalents are `store_price`, `store_language`, and `store_pity`.

## Codes that describe the odds

These three are coded from every source that shows numeric odds (store page and publisher site), then combined: `yes` if any source says yes; `unknown` if a source that might show odds wasn't collected; otherwise `no`. When odds are not disclosed they are `not_applicable`.

| Variable | `yes` when |
|---|---|
| `odds_price_linked` | A real-money price (₩, £, $, €, 원, KRW, EUR, GBP, USD) appears within 300 characters of an odds term that has a percentage beside it |
| `odds_in_market_language` | The odds are in a language of the market (KR: Korean; GB/US: English; BE: Dutch, French, or German). Publisher pages: the page's declared `<html lang>`, or, if none, the language of the odds terms found beside the rates. Store pages: the language of those odds terms |
| `pity_disclosed` | A pity or guarantee term appears within 300 characters of an odds term that has a percentage beside it |

## Combined codes

| Variable | Rule |
|---|---|
| `lootbox_present` | `yes` if any store label, loot box term, or numeric odds is found; `no` only if both store and publisher were collected and every signal is `no`; otherwise `unknown` |
| `odds_disclosed` | `yes` if numeric odds are found on the store or publisher site; `no` if loot boxes are present and both sources show no numeric odds; `not_applicable` if no loot boxes; otherwise `unknown` |
| `disclosure_completeness` | `numeric`, `terms_only` (odds page without numbers), `none`, or `unknown` |
| `rates_count` | Distinct percentages near odds terms (a rough proxy for how full the rate table is) |
| `odds_placement` | `store_page`, `publisher_site`, `none`, or `unknown` |

## Dark-pattern candidates

Flags for the manual check against the Gray et al. (2024) ontology. They are candidates, not findings.

| Variable | Rule | Ontology type to check |
|---|---|---|
| `dp_obstruction_candidate` | `clicks_to_odds` ≥ 3 | Obstruction |
| `dp_language_barrier_candidate` | Odds page not in the market's language | Interface interference |

## Public Disclosure Index

Defined in `index_spec.json` (draft). `pdi` is computed only for units with loot boxes and no unknown components; `pdi_min` and `pdi_max` bound it when some components are unknown. A `not_applicable` component scores 0, so titles that don't disclose odds still receive a score.

## Known limitations

- Text-based coding can't see odds that appear only in images or inside a game.
- Publisher sites that pick content by IP address serve the version for the collecting machine's location, whatever the `Accept-Language` header says. This affects RQ3 for publisher-site codes; store APIs take the market as a parameter and are not affected.
- `lootbox_present = no` rests on absence of evidence and should be checked in the validation sample.

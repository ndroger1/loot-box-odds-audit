# Loot Box Odds Disclosure Audit

An empirical audit of how top-grossing video games show loot box odds to players in four markets with different rules: South Korea (legal mandate), the United Kingdom (industry self-regulation), the United States (platform rules and FTC enforcement), and Belgium (nominal ban). It covers mobile, PC, and console storefronts.

SDS 570 capstone, Arizona State University.

> **Status:** setting up. Headline findings, figures, and links to the dataset, manuscript, policy brief, and explainer will be added here as they are finished.

## Research questions

**Central question:** How does a market's regulatory environment shape the way top-grossing games present loot box odds to players?

1. **RQ1.** How do the prevalence and completeness of odds disclosure differ across governance models and across mobile, PC, and console?
2. **RQ2.** How easy are odds to find, and how are they presented (clicks to reach them, placement, format, link to real-money prices)? Which presentation choices match recognized dark-pattern types?
3. **RQ3.** Does the same game present its loot boxes or odds differently depending on the market?

## Sample

- One snapshot date for all collection.
- Unit of analysis: one title on one platform in one market.
- Markets: `KR`, `GB`, `US`, `BE`.
- Storefronts: iPhone App Store (top 50 grossing), Steam (top 50 Top Sellers), PlayStation Store, Xbox Store, and Nintendo eShop (top 25 best-sellers each).

## Repository layout

| Folder | Contents |
|---|---|
| `config/` | Store endpoints, terms-of-use flags, publisher seed list |
| `scrapers/` | Chart, store-page, and publisher-site collectors; Wayback archiving |
| `coding/` | Keyword matching, coding rules, Public Disclosure Index, validation |
| `analysis/` | Statistical tests (RQ1–RQ3) and figures |
| `tests/` | Offline tests on made-up inputs (`pytest`) |
| `data/raw/` | Private HTML and captures (not published; gitignored) |
| `data/interim/` | Intermediate files between collection and coding |
| `data/processed/` | Coded dataset (CSV) and data dictionary |
| `codebook/` | Codebook, keyword dictionary, validation report, rule-revision log |
| `notebooks/` | Analysis notebooks, numbered and run in order |
| `figures/` | Figures used in the manuscript and site |
| `manuscript/` | Journal manuscript |
| `brief/` | Policy brief for the FTC Bureau of Consumer Protection |
| `site/` | GitHub Pages site: summary, searchable results table, explainer |

## Reproducing the analysis

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
playwright install chromium
cp .env.example .env    # then fill in your contact address and snapshot date
pytest                  # offline checks, no network
```

Run the notebooks in `notebooks/` in numeric order, top to bottom. Each one reads from the outputs of the one before it. The same steps can be run from the command line with `python run_pipeline.py <step>` (run it with no step to see the list).

To run collection in Google Colab instead, use `notebooks/00_colab_setup.ipynb`. It saves results to your Google Drive; see `notebooks/README.md` for how to open it and its limits.

## Data collection ethics

- Official APIs are used wherever they exist; scraping is a fallback.
- Every collector respects robots.txt, rate-limits its requests, and sends a User-Agent that names the project and a contact address.
- Only public pages are collected. No logins, no player data, no reviews or other user-generated content.
- Raw HTML is kept privately as evidence. Only derived codes, with archive links for each record, are published.

## License

- Code: [MIT](LICENSE)
- Data and documentation: [CC BY 4.0](LICENSE-DATA.md)

# CLAUDE.md — SDS 570 Capstone: Loot Box Odds Disclosure Audit

This file gives Claude Code the context for my capstone project so it can help with scrapers, notebooks, analysis, and writing in later assignments. Read it before starting any task in this repository.

## Who I am and what this is

- Nick Rogers, Arizona State University, SDS 570 (capstone). Instructor: Shawn Walker. I submit weekly journal check-ins.
- The project is an empirical audit of how top-grossing video games disclose loot box odds across four regulatory regimes and three platform types.
- Final outputs: a manuscript for a named journal, an open dataset and codebook, reproducible Python scrapers and notebooks, a policy brief, and a public explainer, all in a public GitHub repository.

## Research questions

Central question: How does a market's regulatory environment shape the way top-grossing games present loot box odds to players?

- **RQ1.** How do the prevalence and completeness of odds disclosure differ across governance models (legal mandate, self-regulation, enforcement-based, ban) and across mobile, PC, and console?
- **RQ2.** How do findability and presentation vary (clicks to reach odds, placement, format, whether odds are tied to real-money prices)? Which presentation choices match recognized dark-pattern types?
- **RQ3.** Does the same game present its loot boxes or odds differently depending on the market?

## Markets and regimes

| Market | Regime | Notes |
|---|---|---|
| South Korea (KR) | Legal mandate | Disclosure law adopted 2024; actively enforced |
| United Kingdom (GB) | Industry self-regulation | Ukie principles |
| United States (US) | Platform rules + FTC enforcement | FTC action against the *Genshin Impact* publisher in 2025 |
| Belgium (BE) | Nominal ban | Gambling law; paid loot boxes still widely sold |

Search for odds-related terms in English and in each market's language (Korean, Dutch, French; German is also an official Belgian language).

## Sample design

- One snapshot date for all collection.
- Unit of analysis: **one title on one platform in one market**.
- Storefronts per market:
  - iPhone App Store: top 50 grossing
  - Steam: top 50 Top Sellers (country charts where available, otherwise global; record which)
  - PlayStation Store, Xbox Store, Nintendo eShop: top 25 best-sellers each
- If a store's chart can't be collected automatically, fall back to a chart tracker's API. If a scraper fails outright, cut that store to the top 10 from a chart tracker rather than delay the analysis.

## Data collection pipeline

Collection is **mostly automated**. I don't have time for heavy manual collection. No games are installed or played. Manual work is limited to validating automated codes and a small gameplay-video sample.

1. **Charts** — scripts capture each market's best-seller lists on the snapshot date.
2. **Store pages**
   - Apple iTunes Lookup API and the Steam storefront API (country-specific descriptions, age ratings, purchase info).
   - PlayStation, Xbox, Nintendo: headless browser (Playwright) on public store pages.
   - Automatically flag the "Includes Random Items" label and odds-related terms.
3. **Publisher websites** — a Scrapy crawler starting at each publisher's official site and support pages. **Crawl depth from the homepage = clicks needed to reach odds** (an RQ2 measure). Save pages containing odds to the Wayback Machine via Save Page Now.

## Coding, validation, analysis

- Automated coding via a keyword dictionary plus rules applied to scraped text: loot box presence, disclosure completeness, presentation features.
- Validation: hand-code a random 20% sample; report precision, recall, and Krippendorff's alpha against the automated codes; refine rules until agreement is acceptable. Keep a record of each rule revision.
- Unclear cases are coded as **unknown**, never guessed.
- Every automated code must be traceable to an archived page (store the archive URL or local capture path with each record).
- Build a **Public Disclosure Index (0–10)**.
- Tests: Fisher's exact and Kruskal–Wallis (RQ1–2); paired tests and logistic regression with standard errors clustered by title (RQ3).
- Libraries: pandas, SciPy, statsmodels, Playwright, Scrapy.

## Scraping rules (non-negotiable)

- Prefer official APIs over scraping.
- Respect robots.txt, rate-limit every request, and set a User-Agent that identifies the scraper with a contact address.
- Collect only public pages. Never log in.
- If a store's terms prohibit automated access, use a chart tracker's API or narrow that store's sample instead of scraping it.
- Keep raw HTML private (gitignored) as evidence; publish only derived codes.
- Publish only a few screenshots, for commentary.
- No human subjects: no player data, accounts, reviews, or user-generated content.

## Suggested repository layout

```
├── README.md              # plain-language summary, headline findings, figures, links
├── CLAUDE.md
├── LICENSE                # MIT for code; data under CC BY 4.0
├── scrapers/              # chart, store-page, and publisher crawlers
├── data/
│   ├── raw/               # gitignored — private HTML and captures
│   ├── interim/
│   └── processed/         # coded dataset CSV + data dictionary
├── codebook/              # codebook, keyword dictionary, validation report
├── notebooks/             # numbered, run in order (01_..., 02_...)
├── figures/
├── manuscript/
├── brief/                 # policy brief for the FTC Bureau of Consumer Protection
└── site/                  # GitHub Pages: README, searchable results table, explainer
```

## Conventions for Claude Code

- Use ISO country codes (KR, GB, US, BE) and consistent platform labels (`ios`, `steam`, `playstation`, `xbox`, `nintendo`).
- Record the snapshot date, source, and retrieval timestamp on every collected record.
- Notebooks must reproduce every step from raw data to figures, run top to bottom.
- **Notebooks keep their wrong turns.** Don't delete failed approaches. Leave them in with a markdown cell explaining what went wrong and how it changed direction. This is required for the Exploratory and Computational Data Analysis competency.
- Explain intent in markdown cells so a reader can follow the code.
- Figures should be clear, labeled, and descriptive enough to stand on their own.
- Don't hardcode credentials or API keys; use environment variables.
- Don't fabricate citations, data, or results. If something can't be verified, flag it.
- Ask before deleting data files or changing the codebook definitions.

## Competencies and where the evidence lives

| Competency | Level | Evidence |
|---|---|---|
| Empirical Social Research | **Mastery** | Full manuscript for *Games: Research and Practice* (ACM; alternative: *Royal Society Open Science*), following its formatting standards; links to the dataset |
| Data Ethics and Policy | Proficiency | Two-page policy brief for the FTC Bureau of Consumer Protection (autonomy, non-maleficence, justice; Korean law, Ukie principles, Belgian gambling law, platform rules) |
| Exploratory and Computational Data Analysis | Proficiency | Scrapers + notebooks with wrong turns kept; ~1,000-word lay narrative with next steps |
| Theory Application and Critique | Proficiency | Manuscript Introduction and literature review applying mandated-disclosure theory (Ben-Shahar & Schneider, 2011) |
| Public Explanation | Proficiency | ~2,000-word explainer for parents and young players; open for comment with peer feedback |

The competency rubric is in `capstone-competencies-guide.md` if it's in the repo.

## Key literature

- Harms: Zendle & Cairns (2018); Garea et al. (2021); Close et al. (2023); Zendle, Meyer, et al. (2020).
- Compliance audits (the method I follow for comparability): Xiao et al. (2023, UK); Xiao et al. (2024, China); Xiao (2023a, labels; 2023b, Belgium); Xiao & Park (2025, South Korea).
- Dark patterns: Gray et al. (2018); Mathur et al. (2019, crawling at scale); Gray et al. (2024, ontology used as coding frame); Zagal et al. (2013); Niknejad et al. (2024); Gray, Mildner & Bielova (2025).
- Theory: Ben-Shahar & Schneider (2011), *The failure of mandated disclosure*.

## Timeline

| Week | Goals |
|---|---|
| 3 | Build and test scrapers on five titles; confirm chart access; codebook and keyword dictionary; set snapshot date; create repo |
| 4 | Run all scrapers on snapshot date; archive odds pages |
| 5 | Automated coding; 20% hand-coded validation; clean dataset |
| 6 | Analysis, figures, 1,000-word narrative; draft Methods and Results |
| 7 | Draft Introduction and Discussion; policy brief and explainer; peer feedback |
| 8 | Revise; finish README and site; confirm full pipeline reproduces results |

## Open questions sent to the instructor

Check whether these have been answered before making related decisions: acceptability of scraping store pages; whether to narrow scope (e.g., US and UK only); whether a 20% hand-coded sample can stand in for a second human coder; whether IRB review is needed for publication; whether the planned evidence meets the mastery bar.

## University policy

Use only for authorized ASU coursework, following ASU data governance. This project uses public commercial material only. Don't bring sensitive or restricted data into it.

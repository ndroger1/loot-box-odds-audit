"""Run the project pipeline step by step from the command line.

    python run_pipeline.py charts        # stage 1: best-seller charts
    python run_pipeline.py stores        # stage 2: store pages
    python run_pipeline.py seeds         # build config/publisher_seeds.csv (then review it)
    python run_pipeline.py crawl         # stage 3: publisher sites
    python run_pipeline.py archive       # save odds pages to the Wayback Machine
    python run_pipeline.py code          # automated coding -> data/processed/coded_units.csv
    python run_pipeline.py sample        # draw the 20% validation sample
    python run_pipeline.py validate      # compare hand codes -> codebook/validation_report.md
    python run_pipeline.py figures       # figures/ PNG + SVG
    python run_pipeline.py site          # export the public table for site/

Collection steps (charts, stores, crawl, archive) contact external sites. Run
them only on the snapshot date, after config/sources.json has been checked.
The notebooks call the same functions and are the documented record.
"""

from __future__ import annotations

import logging
import sys


def site_export() -> None:
    import pandas as pd

    from scrapers.records import PROCESSED, ROOT

    df = pd.read_csv(PROCESSED / "coded_units.csv", dtype={"store_id": str})
    public = ["snapshot_date", "market", "platform", "rank", "title", "lootbox_present",
              "store_label_random_items", "odds_disclosed", "disclosure_completeness", "odds_placement",
              "clicks_to_odds", "odds_price_linked", "odds_in_market_language", "pity_disclosed",
              "pdi", "odds_archive_url", "rules_version"]
    out = ROOT / "site" / "data" / "coded_units.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df[[c for c in public if c in df.columns]].to_csv(out, index=False, encoding="utf-8")
    print(f"Wrote {len(df)} rows to {out}")


def main(step: str) -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if step == "charts":
        from scrapers.charts.run import main as run
        run()
    elif step == "stores":
        from scrapers.store_pages.run import main as run
        run()
    elif step == "seeds":
        from scrapers.publisher.seeds import build
        build(force="--force" in sys.argv)
    elif step == "crawl":
        from scrapers.publisher.crawl import main as run
        run(sys.argv[2] if len(sys.argv) > 2 else "")
    elif step == "archive":
        from scrapers.archive import main as run
        run()
    elif step == "code":
        from coding.rules import main as run
        print(f"Coded {len(run())} units")
    elif step == "sample":
        from coding.validation import draw_sample
        print(f"Sample of {len(draw_sample())} units written to codebook/validation_sample.csv")
    elif step == "validate":
        from coding.validation import report
        print(report())
    elif step == "figures":
        import pandas as pd

        from analysis.figures import all_figures
        from scrapers.records import PROCESSED
        for path in all_figures(pd.read_csv(PROCESSED / "coded_units.csv", dtype={"store_id": str})):
            print(path)
    elif step == "site":
        site_export()
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")

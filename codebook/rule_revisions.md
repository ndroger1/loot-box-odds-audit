# Rule revisions

Every change to `coding/rules.py`, `codebook/keyword_dictionary.csv`, or `codebook/index_spec.json`, with the date, what changed, why, and the validation scores before and after.

| Version | Date | Change | Reason | Agreement before → after |
|---|---|---|---|---|
| 0.1-draft | 2026-11-18 | First rule set, dictionary, and draft index | Initial version, not yet validated | – |
| 0.2-draft | 2026-11-20 | Price, language, and pity are now coded from every source that shows odds (store page as well as publisher site) and combined; they are `not_applicable` when odds aren't disclosed. Language falls back to the odds terms' dictionary language when a page declares none. Pity now requires the pity term to be near the rates (was anywhere on the page) | Under 0.1, a title with loot boxes and no odds, or odds only on the store page, always had a missing index score, because these three codes stayed `unknown`. That would have left out the least-disclosing titles and pushed average scores up | – (found by inspection before collection) |

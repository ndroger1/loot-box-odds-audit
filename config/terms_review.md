# Store terms review

> **Status: DRAFT, prepared by Claude on 2026-11-20 for Nick to check.** The "proposed decision" column is a suggestion, not a decision. Nick confirms each one, and Shawn's answer on scraping store pages decides the ambiguous cases. Nothing in `sources.json` has been changed: every `terms_allow_automation` value is still `null`, so every store stays locked.
>
> This is a reading of terms of use for a course project, not legal advice.

## How to use this file

For each store, before setting `terms_allow_automation` in `config/sources.json`:

1. Open each document linked below and confirm the clause and the "last updated" date are still what this file says.
2. Copy the exact clause into the "Clause relied on" line (the quotes below are shortened).
3. Save the terms page to the Wayback Machine (`https://web.archive.org/save/<url>`) and paste the archive URL.
4. Record the decision, the date, and who made it. Then set the flag.

Quotes are short excerpts. Section numbers refer to the version read on 2026-11-20.

## Summary

| Store | What the code uses | What the terms say | Proposed decision |
|---|---|---|---|
| App Store | iTunes Lookup API; legacy top-grossing RSS feed | Documented public API with a rate limit (about 20 calls/min). The Apple Media Services Terms ban automated scraping, measurement, analysis, or monitoring of the Services | **Ask Shawn.** Leaning `true` for the Lookup API within Apple's rate limit, but the conflict needs a ruling |
| Steam | `appdetails` and `IStoreTopSellersService` | Neither endpoint is in Valve's public documentation. The Subscriber Agreement bans scripts and bots that "interact with Content and Services on Steam" | **Ask Shawn.** Leaning `false` unless he's comfortable with undocumented endpoints |
| PlayStation | Playwright on store pages | Website terms §10 explicitly ban web scraping and data mining | **`false`**: use a tracker or a narrower sample |
| Xbox | Playwright on store pages | Services Agreement §3.a(vi) lists "impermissible scraping"; Terms of Use bar getting information "through any means not intentionally made available" | **`false`** (leaning). Ask Shawn if you want a second opinion |
| Nintendo | Playwright on eShop pages | US terms §6 explicitly ban robots, spiders, crawlers, and scrapers. The robots.txt reserves rights against text and data mining | **`false`**: use a tracker or a narrower sample |

**What this means for the sample:** if these decisions stand, all three console stores need another source. See "Consequences" at the end.

---

## App Store (`ios`)

**Documents read (2026-11-20):**

| Document | URL | Version |
|---|---|---|
| iTunes Search API documentation | https://performance-partners.apple.com/search-api | No date shown (footer © 2022) |
| RSS Feed Generator | https://rss.marketingtools.apple.com/ | No date; no terms on the page |
| Apple Media Services Terms and Conditions | https://www.apple.com/legal/internet-services/itunes/ | Last updated September 14, 2026 |
| Apple Website Terms of Use | https://www.apple.com/legal/internet-services/terms/site.html | Updated Nov. 20, 2009 |

**Relevant clauses:**

- *Search API, Notes:* the API is "limited to approximately 20 calls per minute (subject to change)". Heavier users are pointed to the Enterprise Partner Feed. Large sites "should set up caching logic" for search and lookup requests.
- *Search API, Overview:* promotional content may be used "only to promote store content". This covers artwork and previews; the page doesn't address research use of metadata.
- *Apple Media Services Terms, §F (Usage Rules, All Services):* bans using any automated process to scrape, copy, or perform "measurement, analysis, or monitoring" of the Content or Services. Also: personal, noncommercial use only, and no use of the Services or Content to train AI. §A lists iTunes among the Services.
- *Apple Website Terms of Use:* bans "page-scrape", "robot", "spider" or other automatic devices on the Site. It covers apple.com and associated sites; it doesn't say whether itunes.apple.com is one of them.
- *RSS Feed Generator:* silent on automated access.

**Endpoint check:** the legacy top-grossing feed (`/rss/topgrossingapplications/.../genre=6014/json`) returned valid JSON with 5 entries for `limit=5` on 2026-11-20. It works today. Apple doesn't document it as current.

**Reading:** two documents pull in different directions. Apple publishes the Search/Lookup API for anyone to call, with a stated rate limit, which is the strongest sign of permission among the five stores. But the Media Services Terms, if they govern the API, ban automated "analysis" of the Services, and that describes this study. Which document governs a researcher calling the public API without an account isn't stated.

**Proposed decision:** ask Shawn. If he's comfortable, set `true` for the Lookup API only, at Apple's rate limit. The code's default `REQUEST_DELAY_SECONDS=3` gives exactly 20 calls a minute; don't lower it. For the chart, the RSS Feed Generator is Apple's own tool for this, so the same decision covers it.

- Clause relied on: _(copy here)_
- Terms archive URL: _(paste here)_
- Decision: _(true / false)_, date: ____, by: ____

---

## Steam (`steam`)

**Documents read (2026-11-20):**

| Document | URL | Version |
|---|---|---|
| Steam Web API Terms of Use | https://steamcommunity.com/dev/apiterms | Last updated July 2010 |
| Steam Subscriber Agreement | https://store.steampowered.com/subscriber_agreement/ | Last updated September 10, 2026 |
| Valve Site Terms of Use | https://www.valvesoftware.com/en/legal | No date shown |
| Steamworks Web API overview | https://partner.steamgames.com/doc/webapi_overview | No date shown |
| Steamworks IStoreService | https://partner.steamgames.com/doc/webapi/IStoreService | No date shown |
| store.steampowered.com robots.txt | https://store.steampowered.com/robots.txt | — |

**Relevant clauses:**

- *Web API Terms §2:* use is tied to an API key and "your Application"; limit of 100,000 calls a day; no use that "degrades the operation or performance of Steam"; no use that violates the Subscriber Agreement. The terms don't mention scraping or store endpoints.
- *Subscriber Agreement §4.C (Automation):* "You may not use any form of scripts, bots, macros, or other non-human-controlled systems" to interact with Content and Services on Steam. The listed examples are about accounts, gameplay, and rewards. It doesn't say whether reading public store data counts.
- *Subscriber Agreement §2.A:* personal, non-commercial use.
- *Subscriber Agreement §3.A:* no IP proxying to disguise your location. Relevant because country prices come from the `cc` parameter, not a proxy. Keep it that way.
- *Valve Site Terms:* personal use; no copying or redistribution of Materials. Silent on automated access.
- *robots.txt:* `/api/` is not disallowed.

**Endpoint documentation:** neither endpoint the code uses is documented.
- `store.steampowered.com/api/appdetails` appears in none of the pages read.
- `IStoreTopSellersService/GetWeeklyTopSellers` has no documentation page (the URL returns the Steamworks home page) and isn't in the Web API reference index.
- The only documented store API is `IStoreService/GetAppList`. It needs an API key and returns the app list, not charts or descriptions.

**Reading:** the code would be calling unpublished endpoints that Steam's own store pages use. Nothing explicitly allows that, and §4.C's ban on bots is broad, though its examples are about gameplay. Your CLAUDE.md says to prefer official APIs, and these aren't official in the documented sense.

**Proposed decision:** ask Shawn, with the §4.C clause and the fact that the endpoints are undocumented. If he says no, set `false` and get the Steam chart from a tracker. Store-page descriptions and labels would then have to come from manual capture of a narrower sample.

- Clause relied on: _(copy here)_
- Terms archive URL: _(paste here)_
- Decision: _(true / false)_, date: ____, by: ____

---

## PlayStation Store (`playstation`)

**Documents read (2026-11-20):**

| Document | URL | Version |
|---|---|---|
| PlayStation Website Terms of Use (US) | https://www.playstation.com/en-us/legal/website-terms-of-use/ | Last updated March 11, 2026 |
| PlayStation Website Terms of Use (UK) | https://www.playstation.com/en-gb/legal/website-terms-of-use/ | Last updated March 11, 2026 (same substance as US) |
| PlayStation Terms of Service (US) | https://www.playstation.com/en-us/legal/psn-terms-of-service/ | Date not confirmed (page truncated) |
| store.playstation.com robots.txt | https://store.playstation.com/robots.txt | — |

**Relevant clauses:**

- *Website Terms §10, "No text mining, data mining or AI training":* "You shall not conduct, facilitate, authorize or permit any text or data mining or web scraping", including by any robot, bot, spider, scraper, or other automated device. It states an express reservation of rights.
- *Website Terms §3:* personal, non-commercial use, "in connection with typical web browsing activity"; no building a database from the content.
- *PlayStation Terms of Service §1.2:* names PlayStation Store as a service. *§10.7:* no "automated methods, such as bots or scripts to interact with Content."
- The website terms cover sites "operated by us" but don't name store.playstation.com. The Terms of Service do name the Store.
- *robots.txt:* only `/chihiro-api/` and `/event/batch` are disallowed. robots.txt allowing a path doesn't override the terms.

**Reading:** this is the clearest case. Both documents prohibit automated collection, and §10 names web scraping and data mining directly.

**Proposed decision:** `false`. Use a chart tracker for the chart (if its terms allow it; see below) and collect a narrower sample of store pages by hand in a normal browser, if Shawn agrees that's acceptable.

- Clause relied on: _(copy here)_
- Terms archive URL: _(paste here)_
- Decision: _(true / false)_, date: ____, by: ____

---

## Xbox / Microsoft Store (`xbox`)

**Documents read (2026-11-20):**

| Document | URL | Version |
|---|---|---|
| Microsoft Terms of Use | https://www.microsoft.com/en-us/legal/terms-of-use | Last updated February 7, 2022 |
| Microsoft Services Agreement | https://www.microsoft.com/en-us/servicesagreement/ | Published July 30, 2026; effective September 30, 2026 |
| xbox.com robots.txt | https://www.xbox.com/robots.txt | — |

**Relevant clauses:**

- *Services Agreement §3.a(vi), Code of Conduct:* "Don't circumvent any restrictions on access to, usage, or availability of the Services", with "impermissible scraping" given as an example. The agreement covers Microsoft consumer "websites" and names Microsoft Store on Xbox.
- *Services Agreement §8.a:* personal, non-commercial use.
- *Terms of Use, "No Unlawful or Prohibited Use":* you may not obtain information "through any means not intentionally made available through the Services".
- *Terms of Use, "Personal and Non-Commercial Use Limitation":* no copying or distributing information obtained from the Services.
- Neither document uses the words robot, spider, or crawler in the parts read verbatim. The later sections of the Services Agreement (including §14 on Stores) were only summarised by the fetch tool and need checking on the live page.
- *robots.txt:* no rule covers `/games/store`.

**Reading:** less explicit than PlayStation or Nintendo, since "impermissible scraping" isn't defined. But a headless browser collecting store pages for a dataset is hard to describe as a means "intentionally made available," and the use is not personal.

**Proposed decision:** `false`, unless Shawn reads it differently. Before relying on it, read §14(b) of the Services Agreement on the live page.

- Clause relied on: _(copy here)_
- Terms archive URL: _(paste here)_
- Decision: _(true / false)_, date: ____, by: ____

---

## Nintendo eShop (`nintendo`)

**Documents read (2026-11-20):**

| Document | URL | Version |
|---|---|---|
| Nintendo Terms of Use (US) | https://www.nintendo.com/us/terms-of-use/ | Last updated May 24, 2016 |
| nintendo.com robots.txt | https://www.nintendo.com/robots.txt | — |
| nintendo.co.kr robots.txt | https://www.nintendo.co.kr/robots.txt | — |

**Not found:** UK/Europe website terms (the expected URL returned 404), Belgian terms, and Korean terms (nintendo.co.kr now redirects to nintendo.com/kr/, and no terms link was found). **Find these by hand** from each regional site's footer before deciding for GB, BE, and KR.

**Relevant clauses:**

- *US Terms §6 (Acceptable Use):* you may not use "any robot, iframe, spider, crawler, scraper or other automated means or interface not provided by us" to access the Services, including to copy, extract, or aggregate content or data.
- *US Terms §4.A:* licence for personal use only; no downloading beyond page caching.
- *nintendo.com robots.txt:* allows general crawling (`Allow: /`) but blocks many named AI crawlers. A comment in the file reserves rights under Article 4(3) of the EU Copyright Directive and says web scraping and text and data mining are prohibited without written authorisation. A comment isn't a robots directive, but it is a clear statement of the site owner's position, and it applies to the European pages.
- *nintendo.co.kr robots.txt:* disallows only one support path.

**Reading:** the US terms prohibit this explicitly, and the robots.txt comment extends the same position to text and data mining, which covers the EU pages.

**Proposed decision:** `false`.

- Clause relied on: _(copy here)_
- Terms archive URL: _(paste here)_
- Decision: _(true / false)_, date: ____, by: ____

---

## Consequences for the study

If the proposed decisions stand:

1. **Console charts** (PlayStation, Xbox, Nintendo) come from a chart tracker, top 10 per store per market as CLAUDE.md allows. The tracker's own terms must allow use of its data in a published study. Many trackers are paid or forbid redistribution. That check isn't done yet: add a section to this file for each tracker you consider.
2. **Console store pages** (labels, descriptions) can't be collected automatically. The options are manual capture of a small sample in a normal browser (a human reading public pages; check with Shawn), or coding console titles from publisher sites only and marking store codes `unknown`.
3. **RQ1's platform comparison** gets weaker for consoles. Say so in the Limitations section, and record the decision in the notebooks' "Wrong turns" cell for collection.
4. **Steam and the App Store** depend on Shawn's answer. If either is `false`, the same tracker fallback applies.

## Questions to send Shawn

1. Apple publishes a Search/Lookup API with a rate limit, but its Media Services Terms ban automated "measurement, analysis, or monitoring" of the Services. Is using the public API at Apple's rate limit acceptable for this study?
2. Steam's store endpoints are undocumented, and the Subscriber Agreement §4.C bans bots that interact with Steam Content and Services. Acceptable, or should Steam move to a tracker?
3. PlayStation, Xbox, and Nintendo prohibit scraping. Is manual collection of a small sample of public console store pages in a normal browser acceptable instead?
4. Is cutting console stores to a top-10 tracker sample acceptable for the RQ1 platform comparison, or should consoles be dropped from scope?

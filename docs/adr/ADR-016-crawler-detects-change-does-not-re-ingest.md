# ADR-016: The Crawler Detects Change, It Does Not Re-ingest

## Status

Accepted (2026-07-21). Refines BUILD_SPEC §6 crawler behaviour for D3.

**Amendment (2026-07-22).** The HDFC "robots.txt disallows the product path"
example used below was wrong — the crawler had been pointed at `www.hdfcbank.com`
(a Cloudflare mirror whose `/robots.txt` 403s, which `RobotFileParser` reads as
disallow-all), not HDFC's canonical `www.hdfc.bank.in`, which allows crawling.
HDFC is now fully crawlable (`sources.yaml` corrected). The decision here is
**unchanged** — Axis's JS-rendered partner table and Amex's JS-rendered figures
still justify detect-not-reingest, and the verified-corpus-vs-scraped-HTML
argument never depended on HDFC. The HDFC references in the text below are left
as written but should be read through this correction.

## Context

BUILD_SPEC §6 describes the crawler as: "fetches, extracts main content,
computes hash, diffs against `knowledge_docs.content_hash`. On change:
**re-ingest chunk set**, update `last_changed`, write a change record."

That description assumes the crawled page *is* the ingestible content. Two facts
found during D3 make that assumption unsafe:

1. **The verified corpus is hand-authored, the live pages are not.** The seed
   markdown in `knowledge/sources/` was written from official T&Cs during
   verification, every fact carrying a source and a confidence. The live product
   pages are marketing HTML. Re-ingesting the scraped page would replace verified
   content with unverified scraped text — a direct violation of hard rule #1
   (no fabricated/unverified data) and of BUILD_SPEC §14a ("Rule updates require
   explicit manual approval... never modify rule files automatically").

2. **The live pages are partial blind spots.** Fetch-testing on 2026-07-21 found
   the reward detail is often not in the static HTML the crawler can read:
   - ~~**HDFC Infinia** — `robots.txt` disallows the product path. Not fetchable
     at all, by policy.~~ *(Wrong — see the 2026-07-22 amendment above. This was
     the wrong host; HDFC is fully crawlable.)*
   - **Axis Atlas** — the Travel EDGE transfer-partner table is JS-rendered;
     only one partner name appears in static HTML.
   - **Amex Platinum Travel** — exact milestone/Reward-Multiplier figures and the
     MR partner list are JS-rendered or in a linked catalogue, not static HTML.

   A crawler that re-ingested what it *can* read would produce a corpus poorer
   and less accurate than the hand-verified one.

There is also a storage collision. `knowledge_docs.content_hash` already holds
the hash of the ingested seed body (so ingestion can skip unchanged docs). The
crawler needs to hash the live page. One column cannot hold both hashes for the
same `doc_id` without one clobbering the other.

## Decision

**The crawler is a change detector, not a re-ingester.** It fetches each source,
hashes the extracted text, and compares against the last-crawl hash. On a
change it writes a change record and advances the stored hash and `last_changed`
— a signal that a human (or, later, the Rule Verifier of BUILD_SPEC §14a) should
re-verify. It never re-ingests scraped HTML into ChromaDB and never edits rule
files.

This is the deviation from BUILD_SPEC §6's "on change: re-ingest chunk set." It
is deliberate, and the D3 task framed it the same way ("writing change records
to knowledge_docs"), so the two are aligned.

**Storage: a `source::<key>` namespace inside `knowledge_docs`, not a new
table.** Crawl-state rows use doc_ids like `source::axis_atlas`, kept distinct
from ingested-corpus rows like `axis_atlas_reward_rules`. The crawler's live-page
hash lives in the crawl-state row's `content_hash`; ingestion's seed-body hash
lives in the corpus row's `content_hash`; they never collide. This honours the
task's "change records in knowledge_docs" instruction and needs no schema change
(migrations stayed a single head through D2). `last_crawled` advances every run;
`last_changed` advances only on a real change — which is the change record §6
asks for.

**Robots and config skips are recorded, never silent.** A `crawlable: false`
source (HDFC) is skipped before any request; a robots-disallowed source is
skipped after the robots check. Both appear in the crawl report with a reason.
An unreadable `robots.txt` fails closed (treated as disallowed).

## Consequences

**Positive.** The verified corpus stays verified. The crawler does exactly one
job well — telling us when an official page changed so the number can be
re-checked — which is what a daily cron should do, and it cannot corrupt data by
running.

**The blind spots are real and are documented, not worked around.** HDFC is not
crawlable at all (robots); Axis's partner table and Amex's exact figures are not
in the crawlable HTML. So a change to *those specific facts* on the source can
go undetected while the surrounding page is unchanged. This is recorded in
KNOWN_LIMITATIONS (items 20–21) rather than papered over with a headless browser
the free-tier constraint would not sustain.

**Namespaced rows share a table with corpus metadata.** Reading `knowledge_docs`
now means being aware that `source::*` rows are crawl state, not documents. The
`status` column is set to `crawl_state` on those rows to make the distinction
queryable.

**Re-ingestion on change stays manual (D3) / Rule-Verifier-driven (fast
follow).** When the crawler flags a change, updating the corpus is a human step
today and the Rule Verifier's job later (BUILD_SPEC §14a). The crawler is the
detection half of that pipeline, wired now; the extraction/approval half is not.

## Alternatives rejected

**Re-ingest the scraped page on change (literal BUILD_SPEC §6).** Rejected: it
injects unverified content into a verified corpus and would overwrite
hand-checked facts with worse marketing-HTML extractions — and cannot even see
the JS-rendered detail that matters most.

**A dedicated `crawl_state` table.** Cleaner data model, but a schema change the
task did not ask for ("change records in knowledge_docs"), and the namespaced
rows achieve the same separation with no migration. Revisit if crawl state grows
fields that do not fit `knowledge_docs`.

**Use a headless browser to read the JS-rendered tables.** Rejected for now:
it defeats the free-tier/open-source constraint at cron scale and turns a
change-detector into a scraper of exactly the content that most needs human
verification. The partner tables are hand-verified; the crawler flags when their
page changes.

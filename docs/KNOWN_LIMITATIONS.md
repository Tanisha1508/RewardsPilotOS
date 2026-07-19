# Known limitations

Honest statement of what RewardsPilotOS does not do (sprint state,
2026-07-19). Each item is either inherent to the design or scheduled on the
roadmap — none is silently papered over.

1. **Manual balance entry.** Reward balances and loyalty balances are entered
   and updated by the user. There are **no bank APIs** or account-scraping
   integrations, by design (security and ToS). Balances can be stale until
   the user updates them; recommendations state the `last_updated` date.

2. **No award seat availability.** The Graph Engine answers "what is the best
   verified transfer path", not "is there a seat on that flight". Award
   availability requires the Flight/Hotel Search MCP servers (interface-only
   today, roadmap).

3. **Promotion detection bounded by crawl frequency.** Promotions and rule
   changes are detected by the daily crawler diff (03:00 UTC once wired at
   D3/D5). A promotion launched and withdrawn between crawls is missed;
   short-fuse offers may appear late.

4. **MCP partially stubbed.** Browser and Playwright clients return typed
   `pending_integration` errors; Email, Calendar, Flight Search, and Hotel
   Search are interface-only. No live external calls happen in the sprint
   build.

5. **International issuers unsupported.** Scope is Indian issuers first
   (VERIFICATION_QUEUE P1–P3). Cards, currencies, and program assumptions
   (INR blocks, Indian transfer partners) do not generalize yet.

6. **Recommendation quality depends on verified data.** All real-card
   numerics currently ship unverified (`[NEED]` register), so real-card math
   honestly returns "unknown" until VERIFICATION_QUEUE work lands. Synthetic
   fixture entities (Demo Bank, Sample Bank, Skyhigh, Grandstay) exist only
   to exercise the computed paths and are labeled as such everywhere.

7. **Sprint-stage stores.** Cap usage, knowledge-doc hashes, preferences,
   episodic events, and opportunities live in in-memory fakes behind the
   production interfaces; restarting the process resets them until D2 wires
   Postgres.

8. **Per-merchant accelerated-earn exclusions are not modeled.** The Amex
   Reward Multiplier applies broad per-merchant exclusions (mobile phones,
   jewellery/precious metals, large appliances, gift cards, flight/utility/
   insurance payments, gaming consoles — varying by merchant). The Rule
   Engine models only the top-level 3X rate and monthly bonus cap; a portal
   purchase in an excluded sub-category may be over-estimated. Documented
   limitation by design (product owner, 2026-07-20), not a data gap. The
   engine also clips total accelerated points at bonus-portion caps
   (conservative above the cap; base-rate fallback on excess is not modeled
   for any issuer).

9. **Freshness is metadata-driven.** Retrieval freshness decay trusts
   `last_changed` from the corpus; a source that changes without the crawler
   noticing (hash collision, blocked crawl per robots.txt) keeps its old
   timestamp. Sources disallowing crawling are skipped and logged, not
   worked around.

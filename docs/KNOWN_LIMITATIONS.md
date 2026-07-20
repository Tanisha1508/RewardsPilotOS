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

6. **Recommendation quality depends on verified data.** P1 cards (HDFC
   Infinia, Axis Atlas, Amex Platinum Travel) are fully verified as of
   2026-07-20; the seven P2 cards ship all-null skeletons, so their math
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

9. **Category earn caps are reported, not enforced, in CalculateEarn.**
   `evaluate_earn` clips only accelerated-entry caps (e.g. SmartBuy 15,000
   pts/month). Category caps in the rule file (Infinia grocery 2,000,
   insurance 10,000, utilities 2,000, telecom 2,000 pts/month, statement-
   cycle max) are queryable via CheckCap but do not clip base earn — a large
   base-rate spend in a capped category can be over-estimated. The Planner
   pairs CheckCap with CalculateEarn for capped categories so the
   Recommender states cap headroom alongside the uncapped figure; enforcing
   category caps in the evaluator is a cap-semantics change reserved for a
   spec update (evaluator docstring, found 2026-07-20 during demo-query
   testing).

10. **Accelerated-earn validity windows are not enforced.** `AcceleratedEarn`
    has no validity fields, so a program's start/end dates live only in
    `notes` prose and the evaluator cannot check them. The Amex Reward
    Multiplier's defined validity ends **2026-07-31**; after that date the
    engine will keep applying the 3X multiplier until someone edits the rule
    file by hand. This is the one open case where the system could compute
    with a lapsed rate rather than returning unknown. Fixing it requires
    adding validity fields to the rule-file schema — a product-owner spec
    decision, not a unilateral change (found 2026-07-20, demo query d5).

11. **Milestone and tier data is verified but unreachable by the engines.**
    Rule files carry fully verified `milestones` and `tiers` (e.g. Atlas
    Platinum at ₹15,00,000 annual spend, 5,000 renewal miles), but the Tool
    Registry enumerated in BUILD_SPEC §8 has no tool that exposes them. A
    milestone question ("how much more to hit Platinum?") therefore answers
    from retrieved prose at **low** confidence while the deterministic
    numbers sit unused, and the engine cannot compute spend-to-go because it
    holds no year-to-date spend. Adding a tool changes the spec'd 15-tool
    registry — a product-owner decision (found 2026-07-20, demo query d4).

12. **Transfer valuations are source-program valuations.** For a transfer
    goal, `redemption_options` values the points required at the SOURCE
    program's point value (`RedemptionGoal` documents transfer-to-program as
    a travel redemption). What the resulting partner balance is actually
    worth is a property of the partner program, which the system holds no
    verified value for. Two consequences when a transfer option is shown
    beside a cashback option: the figures may rest on different quantities of
    source points, and the transfer figure describes source-program value
    rather than realised partner value. Amex sidesteps this by encoding
    `travel: null` ("value varies by partner"); HDFC's `travel: 1.0` does
    not. Whether to keep, relabel, or restrict this is a product-semantics
    decision — the current behaviour is spec'd and test-covered, so it was
    left unchanged (found 2026-07-20, demo query d3).

13. **Confidence calibration is deliberately conservative.** The ceiling is
    the minimum source confidence across ALL results in state, so one weak
    edge caps the whole answer even when it is irrelevant to the question
    (an EDGE Miles airline query is capped at medium by a hotel partner at
    0.65). Under-claiming is the intended failure direction; relevance
    weighting would risk over-claiming and is not attempted.

    Note this is separate from the winning-margin caveat
    (`agents/recommendation/margin.py`), which names the specific number a
    comparison turns on. Ranking is never adjusted for confidence — see
    ADR-002 and `tests/rules/test_confidence_does_not_rank.py`.

14. **Cross-issuer vocabulary is declared, not inferred.** Category
    subsumption (ADR-010) and canonical channels (ADR-011) are hand-maintained
    maps. A new issuer whose portal name or category term is not registered
    will silently fall back to base earn in a cross-card comparison rather
    than erroring — the same failure mode both ADRs were written to fix.
    Adding a card therefore requires checking its channel and category
    vocabulary against those maps, and the integration test that catches an
    omission is a cross-card comparison, not per-field verification.

15. **Freshness is metadata-driven.** Retrieval freshness decay trusts
   `last_changed` from the corpus; a source that changes without the crawler
   noticing (hash collision, blocked crawl per robots.txt) keeps its old
   timestamp. Sources disallowing crawling are skipped and logged, not
   worked around.

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

7. **Sprint-stage stores — partially closed by D2 (2026-07-20).** Portfolio,
   cards, balances, loyalty, goals, preferences (semantic memory), episodic
   events, and cap usage now read and write Postgres behind the same
   interfaces (ADR-013). Still in-memory and reset on restart: knowledge-doc
   hashes (wired D3 with the ingestion pipeline) and opportunities (wired D5
   with the opportunity engine).

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

10. **Mid-window accelerated rate changes are not modeled.** *(Superseded: the
    original item — validity windows not enforced at all — was closed
    2026-07-20 by ADR-012, which added `valid_from`/`valid_until` to
    `AcceleratedEarn`. The Amex Reward Multiplier's 2026-07-31 expiry is now
    engine-enforced: from 2026-08 it falls back to base earn with an expiry
    note and a medium confidence ceiling.)* What remains: one accelerated
    entry carries one multiplier, so a program that changed its rate inside
    its validity window must be expressed as two entries with adjacent
    windows. The schema supports this; no seed data uses it, and nothing
    validates that windows on entries matching the same channel/category do
    not overlap — overlapping entries would resolve to whichever is listed
    first.

    Also: **validity is checked at month granularity**, matching the rest of
    the card model (monthly caps, `cap_usage` keyed by month). A window
    boundary falling mid-month is therefore approximated — a `valid_until` of
    the 15th applies the rate for the whole month and over-credits spend after
    it, which is the wrong error direction. Latent, not live: Amex's end date
    is a month boundary and no other entry declares dates. A real mid-month
    window should be treated as unknown for the partial month rather than
    guessed.

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

16. **`cap_usage` is not scoped to a user — DEFERRED (product owner,
    2026-07-20).** BUILD_SPEC §4 specifies
    `(card_id, category, month, accrued_points)` with no `user_id`, so accrual
    rows are global: two users holding the same card would share one monthly
    cap counter. Two further mismatches with the `CapUsageStore` protocol are
    absorbed by the column names rather than the schema — `card_id` holds a
    rule-engine `card_key` ("hdfc_infinia"), and `category` holds a cap
    `scope` ("smartbuy_total").

    **Deferred until multi-user write paths exist**, because the problem is
    latent rather than live: nothing writes to this table.
    `RuleEngine.calculate_earn` is a read-only query — comparing or re-asking
    never consumes cap — and the application layer has no spend-recording path
    yet. Cap *reads* are correct today because every accrual row is absent and
    therefore zero.

    **The condition that ends the deferral:** the first code path that calls
    `cap_store.record` for a specific user. At that point the shared counter
    stops being theoretical and one user's spend starts consuming another's
    headroom. Do not build that path before adding `user_id` to the table.

17. **`cards` had no `reward_currency` column — CLOSED 2026-07-20.** Fixed by
    migration `cards_reward_currency` (product owner approved). The column is
    `NOT NULL` and the Postgres source reads it directly, so a new issuer
    resolves correctly with no per-issuer code change. The migration adds the
    column nullable and then sets `NOT NULL` with **no backfill**: an existing
    database holding card rows fails the migration loudly rather than having a
    currency guessed for it.

    The related silent failure is closed too. A currency absent from the
    transfer graph now sets `no_transfer_data` on `BestTransferPathsOutput`,
    `GetTransferRatiosOutput`, and `RedemptionOptionsOutput` — previously it
    returned empty paths, indistinguishable from a registered currency with no
    verified route. Regression cover in
    `tests/graph/test_unregistered_currency.py` and
    `tests/integration/test_tool_sources.py`.

    What remains: nothing validates that a card's `reward_currency` matches a
    registered `graph_nodes.node_id` at write time. Adding a card with a
    currency the graph does not know is allowed — it now reports the gap at
    query time instead of hiding it, which is the honest behaviour, but a
    warning at card-creation time would catch a typo sooner.

18. **`goals` carries no `target_program` or `required_points` — DEFERRED
    (product owner, 2026-07-20).** The `TravelGoal` contract has both and
    BUILD_SPEC §4's `goals` table has neither, so goals loaded from Postgres
    return them as `None`. Parsing them out of the free-text description would
    be inventing data.

    **Deferred until goal-driven `RedemptionOptions` is built (likely D4).**
    Nothing is wrong today because nothing reads those fields from a stored
    goal: the workflow passes the redemption target explicitly in the tool
    call, and `RedemptionOptionsInput.goal` is required. Stored goals are
    descriptive records for the UI.

    **The condition that ends the deferral:** the first feature that answers
    "how do I reach my saved goal?" without the caller restating the target.
    Until then the two `None`s are honest — the columns genuinely hold nothing.

19. **Freshness is metadata-driven.** Retrieval freshness decay trusts
   `last_changed` from the corpus; a source that changes without the crawler
   noticing (hash collision, blocked crawl per robots.txt) keeps its old
   timestamp. Sources disallowing crawling are skipped and logged, not
   worked around.

20. **Crawler blind spot — HDFC Infinia is not crawlable at all (robots).**
    Fetch-testing on 2026-07-21 confirmed `robots.txt` disallows the Infinia
    product path (`can_fetch` → False). Per BUILD_SPEC §6 the crawler skips and
    logs it rather than working around it, so the crawler **cannot detect when
    the HDFC source changes**. HDFC's verified facts come from manual review of
    the Rewards Points T&C PDF, and staleness there will not be caught
    automatically — re-verification of HDFC is a calendar item, not a crawl
    trigger. `sources.yaml` marks it `crawlable: false` with the reason.

21. **Crawler blind spot — Axis Atlas transfer-partner table is JS-rendered.**
    The Atlas page is crawlable and the crawler detects HTML-level change, but
    the Travel EDGE transfer-partner table is rendered by JavaScript: of the
    partner names, only one ("accor") appears in the static HTML the crawler
    reads (verified 2026-07-21). So a change confined to the partner ratios can
    occur without the crawlable HTML changing, and go undetected. The partner
    ratios were hand-verified via browser. Not worked around with a headless
    browser (free-tier constraint, and it is exactly the content that needs
    human verification — ADR-016).

22. **Crawler blind spot — Amex Platinum Travel exact figures are not static.**
    The page is crawlable, but exact reward figures (milestone thresholds like
    24,000 MR, Reward Multiplier caps) and the MR transfer-partner list are
    JS-rendered or in a linked benefits catalogue, not in the static HTML
    (verified 2026-07-21). The crawler detects when the page changes; it cannot
    read those specific numbers, which came from the official catalogue reviewed
    manually.

    Items 20–22 share one shape: **the crawler detects change, it does not
    extract verified facts** (ADR-016). Detection is wired (D3); extraction and
    approval are the Rule Verifier's job (BUILD_SPEC §14a, fast follow). Until
    then, a flagged change means "a human re-verifies", and the facts a crawler
    cannot see are re-verified on a schedule regardless.

23. **Crawl cadence is weekly, not daily — reaction to change is delayed up to
    a week.** BUILD_SPEC §6 specified a daily cron; the MVP runs weekly
    (`.github/workflows/crawl.yml`, `cron: "0 3 * * 1"`). Reward T&C pages change
    infrequently — observed directly during verification, where HDFC's SmartBuy
    5X→3X devaluation and its reversal were weeks apart — so weekly is a better
    cost/signal ratio for a pre-launch product. The tradeoff is real: a change
    the crawler *can* see (e.g. a lapsed promotional rate on a crawlable page)
    may go unnoticed for up to a week rather than a day. Combined with the
    freshness half-life (item 19, 180 days) this is well within tolerance for
    T&C-grade data, but it means the crawler is not a same-day alarm. Cadence is
    a single `cron` value and can move to monthly once the product is stable
    (the workflow documents the one-line switch); the crawler code is
    cadence-agnostic and does not change. Manual runs are available any time via
    `workflow_dispatch`.

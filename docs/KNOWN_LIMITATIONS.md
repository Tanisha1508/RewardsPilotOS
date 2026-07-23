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

20. **Crawler blind spot — Axis Atlas transfer-partner table is JS-rendered.**
    The Atlas page is crawlable and the crawler detects HTML-level change, but
    the Travel EDGE transfer-partner table is rendered by JavaScript: of the
    partner names, only one ("accor") appears in the static HTML the crawler
    reads (verified 2026-07-21). So a change confined to the partner ratios can
    occur without the crawlable HTML changing, and go undetected. The partner
    ratios were hand-verified via browser. Not worked around with a headless
    browser (free-tier constraint, and it is exactly the content that needs
    human verification — ADR-016).

21. **Crawler blind spot — Amex Platinum Travel exact figures are not static.**
    The page is crawlable, but exact reward figures (milestone thresholds like
    24,000 MR, Reward Multiplier caps) and the MR transfer-partner list are
    JS-rendered or in a linked benefits catalogue, not in the static HTML
    (verified 2026-07-21). The crawler detects when the page changes; it cannot
    read those specific numbers, which came from the official catalogue reviewed
    manually.

    Items 20–21 share one shape: **the crawler detects change, it does not
    extract verified facts** (ADR-016). Detection is wired (D3); extraction and
    approval are the Rule Verifier's job (BUILD_SPEC §14a, fast follow). Until
    then, a flagged change means "a human re-verifies", and the facts a crawler
    cannot see are re-verified on a schedule regardless.

    *(A former item — "HDFC Infinia is not crawlable at all (robots)" — was
    removed 2026-07-22. It was based on the wrong host: D3 pointed the crawler at
    `www.hdfcbank.com`, a Cloudflare mirror whose `/robots.txt` returns HTTP 403,
    which `RobotFileParser` reads per RFC as disallow-all. HDFC's canonical
    domain `www.hdfc.bank.in` serves `robots.txt` as `Allow: /` and its Infinia
    page returns the reward content in static HTML — fully crawlable, no blind
    spot. `sources.yaml` corrected. The crawler's robots handling was never
    buggy; the URL was wrong.)*

22. **Crawl cadence is weekly, not daily — reaction to change is delayed up to
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

23. **No automated test exercises the real LLM end to end.** The golden suite
    tests determinism and contract, not model behaviour. `rules.json`,
    `graph.json`, and `retrieval.json` touch no LLM (they exercise the
    deterministic engines directly, which is why they exact-match at 100%).
    `recommendations.json` runs the full workflow but with a **scripted
    `EvalLLM`** (`evaluation/metrics/e2e_eval.py`) that emits the golden plan and
    a deterministic recommendation — it verifies the plumbing and the validation
    layer (calculations verbatim, citations present, numbers grounded, no
    fabrication), never what Gemini actually produces. The regression test added
    for the card_key fix (`tests/integration/test_card_key_mapping.py`) is
    likewise a scripted LLM: it locks the *fix*, not real-model behaviour.

    Consequence, seen directly in D4: **LLM-behaviour regressions are caught only
    by manual live testing or by the runtime validation gate**, not by the test
    suite. Every bug found during live `/chat` testing — the planner emitting
    `cards=[]`, omitting `CompareCards`, a malformed `month` — was invisible to
    the golden suite because the plan is scripted there. Real LLM output *is*
    guarded at runtime by `validate_recommendation` (it rejects non-verbatim
    calculations, uncited sources, ungrounded prose, over-claimed confidence),
    but that is production enforcement, not a test.

    Deliberate for now: real-Gemini calls are non-deterministic, cost tokens, and
    flake on 503s (observed). The measured planner reliability after the D4 prompt
    strengthening (CompareCards present 6/6 runs) was a **manual terminal
    measurement, not committed as a test** — nothing automated re-checks it.

    **CLOSED 2026-07-22 by `evaluation/smoke/run.py`.** A manually-triggered
    live-LLM smoke suite now exists: 4 queries × N=3 runs against the real
    ADR-018 fallback chain, asserting four *structural* properties only —
    a recommendation is reached, the plan contains `CompareCards` on a
    comparison intent, at least one `CompareCards` result reaches
    `status: computed`, and every `month` arg the model emits matches
    `^\d{4}-\d{2}$`. It asserts no number, no winning card, and no wording;
    those stay the golden set's job and would flake here. Triggered from the
    Actions tab (`.github/workflows/smoke.yml`, `workflow_dispatch`), never in
    the fast CI loop.

    Two design points that are load-bearing rather than incidental:

    - It lives in `evaluation/`, **not `tests/`**, because
      `tests/conftest.py` blanks `Settings.env_file` suite-wide (the D2 `.env`
      leak fix) while `GeminiClient` reads its key through `get_settings()` —
      under pytest the key would resolve empty, the client would raise, and the
      suite would *skip*, reporting green having never called the model. Exactly
      the failure it exists to prevent, and the same "a skipped test proves
      nothing" trap as the DB integration suite.
    - A check below N/N **fails the run**. Tolerating non-determinism means not
      asserting on content, not tolerating a structural invariant that holds 2
      times in 3 — the D4 planner bug presented precisely as an intermittent
      rate. Infrastructure failure exits 2, distinct from a regression's exit 1,
      so a red run never conflates "the model regressed" with "we never called
      the model".

24. **Required tool args the Planner cannot legitimately supply — Classes A and
    C CLOSED, Class B closed except its genuinely ambiguous members. Found
    2026-07-22 by the first live smoke run, then generalised by a full 15-tool
    audit and closed out 2026-07-23.**

    The audit (2026-07-22) found **13 of 15 tools** exposed in three classes.
    Only `SearchKnowledge` and `GetPromotions` are clean. The organising rule:
    *a required tool arg has three possible sources — the user's words, the
    user's data, or the runtime. Only the first belongs in the LLM's output.*

    - **Class A — runtime value demanded of the model. CLOSED** (`month` on
      `CalculateEarn`, `CheckCap`, `CompareCards`). Pattern-constrained, so a
      missing value was hard-rejected by `validate_plan`. Fixed schema-level:
      `str | None`, absent resolved to the current month at the tool boundary.
    - **Class B — portfolio data demanded of the model. CLOSED except its one
      genuinely query-derived member.** `card_key` (`CalculateEarn`/`CheckCap`)
      and `currency` (`GetTransferRatios`/`BestTransferPaths`) are both resolved
      from held cards by `agents/planner/portfolio_args.py`: `currency` is a
      reward currency the user holds, not a word they say, so an unresolved one
      fans out over held reward currencies exactly as `card_key` fans out over
      held cards (closed 2026-07-23). What remains is `target_program`, which is
      genuinely query-derived — a destination is not in the portfolio — and
      `CheckCap.cap_scope`, which is rule-file vocabulary. Both now surface a
      distinct `unresolved_input` tool status rather than silent empty success
      (see the Part 1 note below), so the safety gap is closed even where the
      arg cannot be auto-resolved.
    - **Class C — runtime value the model is allowed to launder. CLOSED
      2026-07-23.** `user_id` was required on 7 tools and the tools trusted the
      model's copy even though the authenticated value was already in context
      via `acting_as` (`backend/application/chat.py:41`), and
      `tools/graph_engine/tools.py:42` had always resolved it correctly with
      `current_user()` — an inconsistency, not a design choice. The field is
      **removed from the input contracts**, not ignored-if-present: an argument
      that still exists is an argument something can still rely on, the same
      reasoning that deleted the `1970-01` engine default rather than leaving it
      as a bypassable fallback. All seven now resolve the caller from the
      ambient context, and the Planner is no longer told the user id at all —
      the generated tool catalogue advertises no `user_id` on any tool, so the
      model is not invited to supply one. Regression cover in
      `tests/agent/test_caller_identity.py` (schema, registry, handler, and
      missing-context paths) plus the rewritten Postgres isolation test.

      **What this did and did not fix.** It removes an authorization boundary
      from LLM output — real but not trivially exploitable, since Postgres
      required a valid UUID of an existing user, so a hallucinated id failed
      loudly with `UnknownUserError` rather than reading a stranger's data. The
      value is structural: identity is now unreachable from model output by
      construction rather than by the model behaving well.

    **Class B residue — investigated and resolved 2026-07-23.** The earlier
    claim that these "fail *silently* with `status: success` and an empty
    payload" was **wrong for the graph tools** and is corrected here. The
    2026-07-20 spec update (item 17) had already given all three graph tools a
    `no_transfer_data` field, set for every unregistered currency/program, and
    it already reached the Recommender via the state digest — the distinction
    existed, I missed it in the 2026-07-22 audit. (What I actually saw was
    `currency: null` being *dropped by validation* — a rejected invocation, a
    different failure — and over-generalised it.) The genuinely-silent member
    was only `CheckCap.cap_scope`.

    Two changes hardened it anyway:

    - **`currency` is mechanically resolvable** — verified that held cards'
      `reward_currency` values match graph currency nodes exactly — so it moved
      to `resolve_portfolio_args` (fan-out over held currencies). No longer open.
    - **The unknown/not-applicable distinction is now structural, not a field**
      the reader must inspect. `execute()` returns a distinct `unresolved_input`
      status (alongside `success`/`failed`) whenever a graph tool ran correctly
      but could not resolve its input — driven by an `is_unresolved_input`
      property on the three output models. The payload still flows to the
      Recommender in full (it is not a failure), and a matching recommender
      prompt rule (recommender.md rule 10) renders it as "I couldn't identify
      that program" rather than "no options". Belt (status) and braces (prompt),
      per the decision that the distinction must not depend on model behaviour.
      Cover: `tests/agent/test_unresolved_input_status.py`.

    What stays open is only `target_program` (genuinely query-derived; the
    `unresolved_input` floor is the honest answer, and enumerate-destinations is
    logged as item 27) and `CheckCap.cap_scope`.

    ---

    **Original Class A report (closed 2026-07-22, commit `880ec56`):**
    `CompareCardsInput.month` (`contracts/tools/rule_engine.py`) was a required
    `str` with pattern `^\d{4}-\d{2}$` and no default. Most real comparison
    queries carry no month ("which card for a ₹50,000 flight?"), so the model
    has nothing to supply it from and either omits the field or emits `null`.
    Either way `validate_plan` rejects the whole invocation, `CompareCards`
    never runs, and the answer ships with **zero computed numbers**.

    Measured on the first run (N=3): `s02_portal_hotel_comparison` failed
    `plan_has_compare_cards` and `compare_cards_computed` **0/3**;
    `s01_flight_comparison` failed both **2/3**. `s03`, which mentions "a month"
    in the query text and so gives the model something to ground a date in,
    passed 3/3 — which is the tell that this is about the arg being
    unsatisfiable, not about prompt quality.

    This is the **same bug class as the D4 `cards=[]` failure, one argument
    further along**: `inject_card_keys` now correctly fills `cards` before
    validation (visible in the rejection payload,
    `input_value={'cards': ['hdfc_infinia'...`), and the very next required arg
    the model cannot legitimately invent takes its place. The generalizable rule
    the D4 fix implied but did not act on: *a required tool arg the model has no
    basis to supply must be injected deterministically, not demanded of the
    LLM.*

    **Fixed schema-level** (commit `880ec56`): one shared field definition
    across all three inputs, `str | None`, pattern retained so a *malformed*
    month is still rejected — absent and malformed are different states. Absent
    resolves to the current month at the tool boundary
    (`tools/rule_engine/tools.py`), not in the DTO and not in an engine
    signature: since ADR-012 the month selects which accelerated programs are in
    force, so "now" enters at one readable place and the engine stays a pure
    function of its arguments. The rejected alternative was injecting `month` at
    plan time alongside `cards`, which would have put clock knowledge in the
    Planner and needed repeating per tool.

    Removed in the same pass: `RuleEngine.compare_cards` defaulted `month` to
    `"1970-01"`, which predates every `valid_from` in every rule file — so any
    caller omitting it would have had **every accelerated rate silently fall
    back to base earn**, with no error and a plausible-looking answer. A latent
    instance of the very bug being fixed. `tests/rules/test_month_defaulting.py`
    asserts no engine entry point defaults `month`, so it cannot be re-armed.

    Verified live: `s01_flight_comparison` went **2/3 → 3/3** on both
    `plan_has_compare_cards` and `compare_cards_computed`. `s02`–`s04` are
    unverified rather than failing — the Gemini free tier exhausted mid-run (see
    item 26).

    Note what did *not* go wrong: nothing fabricated. On `s01` the Recommender
    tried to state "50,000" with no tool result behind it and
    `validate_recommendation` rejected it as ungrounded prose — the runtime gate
    held. The failure mode is a degraded answer, not a wrong one.

25. **`agents/workflows/demo.py` bypasses the ADR-018 fallback chain — OPEN,
    minor.** `demo.py:151` constructs a bare `GeminiClient()` rather than
    calling `default_llm()`, so the demo runs the primary Gemini model only and
    gets none of the tiered fallback (second Gemini model → Groq) that
    production and the smoke suite use. Consequence is narrow — a transient 503
    fails the demo where the real app would recover — but it also means the demo
    is not exercising the path it appears to demonstrate. One-line fix; flagged
    rather than fixed to keep the smoke-suite change reviewable on its own.

26. **The live smoke suite cannot complete a full N=3 run on the Gemini free
    tier — OPEN, measured 2026-07-22.** The quota is
    `GenerateRequestsPerDayPerProjectPerModel-FreeTier`, **limit 20 requests per
    day per model**. One smoke run is 4 queries × N=3 × ≥2 LLM calls (planner +
    recommender) = **24 calls minimum**, before the single retry in
    `complete_with_retry` or any ADR-018 fall-through. So the primary model's
    daily budget is spent partway through a single run, and the second Gemini
    model's shortly after.

    Observed exactly that: the 2026-07-22 verification run completed `s01`
    (4/4 checks) and then reported `LLM unavailable` for every remaining
    attempt, exiting 2. The suite reported this correctly — it did not present
    a partial run as a pass — but the practical effect is that a *full*
    four-query confirmation cannot be obtained in one day on Gemini alone.

    Groq is unaffected and was verified working during the same window
    (`llama-3.3-70b-versatile` answered normally after both Gemini tiers
    429'd), so the ADR-018 chain does still have a live last resort.

    **Resolved 2026-07-22 by a two-day rotation, not by shrinking the suite.**
    The four queries run as two fixed pairs on alternating days —
    `s01`+`s02` on odd days of the month, `s03`+`s04` on even — at N=3, for
    ~12 calls/day, comfortably inside quota. Every query is exercised every
    other day rather than starved by an unbounded split. The pair is chosen
    from day-of-month parity, so it is stateless and reproducible: same day,
    same pair, on any machine. `SMOKE_GROUP=all` forces full coverage for a
    deliberate manual run. `.github/workflows/smoke.yml` now carries a daily
    schedule as well as `workflow_dispatch` — a rotation only delivers regular
    coverage if it actually runs — while still never gating a PR.

    Two alternatives were rejected, and the reasons are the point:

    - **`SMOKE_RUNS=1`** fits the quota but defeats the suite's purpose. N=3
      exists to catch *intermittent* planner failures; the D4 CompareCards
      omission presented as 3/6, not 0/6. N=1 would have shipped a suite blind
      to the exact bug class it was built to catch — a green run proving
      nothing, which is this document's recurring theme.
    - **Groq as primary** fits the quota but validates the wrong system.
      ADR-018 makes Gemini primary and Groq the last resort, so a Groq-primary
      suite would exercise a path real users rarely hit while leaving the
      common one untested.

    What the rotation does *not* compromise: `default_llm()` still runs the
    full ADR-018 chain, so if Gemini's daily budget is spent mid-run the suite
    does not fail — it falls through to Groq exactly as production would. **The
    quota shapes how often each query is covered, not whether the suite is
    correct.** `tests/agent/test_smoke_rotation.py` asserts the property the
    arrangement rests on: the groups partition the queries, both are non-empty
    and balanced, and two consecutive days cover all four. The report also
    names the queries it did *not* run, so a rotation half can never be read as
    full coverage — the "a skipped test proves nothing" trap, one level up.

    **Refinement 2026-07-23 — `SMOKE_GROUP=all` is not a reliable way to get
    full coverage, and the reason sharpens why the rotation is right.** A
    forced full run that day confirmed `s01` 4/4 on all three runs, then
    reported *all models failed* for `s02`–`s04` — including Groq. Probing the
    tiers immediately after: both Gemini models 429 (daily budget spent on
    `s01`), but **Groq answered fine in isolation**. So Groq did not fail
    because it was exhausted; it failed because once Gemini died, every
    remaining call fell through to Groq in rapid succession and hit Groq's
    *per-minute* limit. The ADR-018 fall-through covers *occasional* Gemini
    unavailability, not a whole run's worth of it bursting through at once.
    That is exactly the case the two-day rotation avoids by construction — 2
    queries/day keeps Gemini within budget so fall-through stays rare — and
    exactly the case `SMOKE_GROUP=all` forces when Gemini is low. **Takeaway:
    get full coverage from two consecutive *rotation* days, not from one forced
    full run.** The suite still reported honestly throughout (exit 2, `s02`–`s04`
    marked NO RUNS COMPLETED, never a partial pass).

27. **No "where can my points go?" discovery affordance — ENHANCEMENT, logged
    2026-07-23.** `target_program` is genuinely query-derived: a transfer
    destination is not portfolio data, so when the user names none (or names a
    *category* like "an airline" rather than a specific program), there is
    nothing to resolve it from. The honest floor is in place — the tool returns
    `unresolved_input` and the Recommender says it could not identify a
    destination (item 24, Class B) — so there is **no safety or correctness
    gap** here. What is missing is a *useful* answer to "where can I transfer?":
    the graph can enumerate the 27 reachable destination programs from the
    user's held currencies, which would turn a dead-end into "your points can go
    to Turkish Miles, KrisFlyer, …".

    Deliberately NOT built into `BestTransferPaths`/`RedemptionOptions`: that
    would turn a *query* tool (given a destination, find paths) into a
    *discovery* tool (given no destination, list them), changing the contract
    and semantics. It is a real feature with its own design surface — a new tool
    or an explicit mode, a category→programs map for "an airline", ranking by
    value — and should compete for time on its own merits, not ride in on an
    audit close. Filed here so it is not lost.

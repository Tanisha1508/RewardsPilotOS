# Sprint handoff — RewardsPilotOS intelligence core

**As of 2026-07-20.** Written for whoever picks this up next, assuming no
memory of the sprint.

Read `BUILD_SPEC.md` (engineering source of truth) and `MASTER_SPEC.md`
(product source of truth) first; `CLAUDE.md` carries the hard rules that
govern every change.

---

## 1. What is built and verified

The intelligence core is complete and runs end to end against in-memory fakes
and fixture data. No database, no HTTP API, no frontend, no crawlers — those
are D2+ and were deliberately out of sprint scope.

| Subsystem | State |
|---|---|
| Rule Engine (`rules/`) | Complete. 100% branch coverage. Versioned JSON rule files, verified-value refusal paths. |
| Retrieval (`knowledge/`) | Complete. ChromaDB + BM25 + RRF + freshness decay over a 21-doc corpus. |
| Graph Engine (`graph/`) | Complete. NetworkX, verified-only path math, unverified register kept separate. |
| Agents (`agents/`, `tools/`) | Complete. LangGraph planner → tools → recommender, 15-tool registry. |
| MCP (`mcp/`) | Stubs and interface-only clients, per spec. |
| Evaluation (`evaluation/`) | Four golden sets + runners + report generator. |
| Docs (`docs/`) | ADR-001..011, VERIFICATION_QUEUE, KNOWN_LIMITATIONS. |

**Verification status — P1 fully closed.** All three MVP cards are verified
end to end: rule file, knowledge doc, and graph edges.

- **HDFC Infinia** — `rules/seed/hdfc_infinia/v3.json`
- **Axis Atlas** — `rules/seed/axis_atlas/v2.json`
- **Amex Platinum Travel** — `rules/seed/amex_plat_travel/v3.json`

**[NEED] register: 84 open items, zero of them on P1 cards.** Every remaining
item belongs to the seven P2 skeleton cards (`hdfc_diners_black`,
`hdfc_regalia`, `amex_plat_reserve`, `amex_membership_rewards`,
`amex_smartearn`, `axis_ace`, `axis_magnus`), which ship as all-null rule
files that honestly refuse to compute. The graph section of the register is
empty — no unverified transfer candidates outstanding.

Run `python -m infra.scripts.need_register` to reprint it.

**Current numbers.** 254 tests pass. Rules 25/25, graph 10/10, end-to-end
10/10. Retrieval reports precision@3 0.2833, recall@5 1.0000, MRR 0.5200 —
reported honestly rather than tuned to a target.

```
.venv/bin/python -m pytest                      # 254 passed
.venv/bin/python -m evaluation.metrics.report   # writes evaluation/reports/REPORT.md
.venv/bin/python -m agents.workflows.demo       # one query end to end
```

---

## 2. What was tested in this session, and what it found

Eight realistic end-to-end queries (not the golden set) plus three adversarial
ones were run through the full LangGraph flow against the verified P1 data.
The harnesses live in the session scratchpad, not the repo; every defect they
found is fixed or documented below, and each fix carries a regression test.

Confidence now varies across the eight queries (high / medium / high / low /
high / medium / medium / high) rather than reading uniformly high.

### The pattern behind the two worst bugs

Two of the defects below (categories, channels) are the same bug on different
axes, and both survived a full field-by-field verification pass. That is not a
verification failure — **verification and integration are different failure
surfaces**. Every rule field was individually correct at the source. Both bugs
lived in the *matching layer* between a query and the right rule, which no
amount of per-field research can catch, and both produced confidently wrong
answers rather than honest unknowns.

The test that catches this class is a **cross-card query exercising each
issuer's actual channel and category vocabulary** — structurally different
from "is this rule field correct". `tests/rules/test_channels.py` and
`tests/rules/test_categories.py` are that test; extend them when adding a
card. The lesson is emphatically *not* "add more confidence checking":
confidence was accurate throughout and would not have flagged either bug.

### Bugs found and fixed

**1. Cross-issuer comparison named the wrong card. (Most serious.)**
Issuers encode categories at different granularity — Axis Atlas declares its
direct accelerated entry as `travel` ("direct airline and direct hotel
bookings"), HDFC Infinia declares `flights` and `hotels` separately. Matching
was exact string equality, and `CompareCards` takes one category for all
cards, so "₹50,000 flight, which card?" matched Infinia's entry but not
Atlas's and silently fell back to Atlas's base rate. The system answered
**Infinia, 1,665 points at high confidence** when the correct answer is
**Atlas, 2,500 EDGE Miles**. Every individual number was verified; the defect
was in rule selection, which is why nothing caught it.

Fixed with a one-directional subsumption map in
`rules/evaluator/categories.py` (`travel` subsumes `flights`/`hotels`, never
the reverse). It is a taxonomy, not reward data — no rate, cap, or policy.
See **ADR-010**; regression cover in `tests/rules/test_categories.py`,
including the exact failing comparison.

**1b. The same bug on the channel axis.** Each issuer names its portal
differently (`smartbuy` / `travel_edge` / `reward_multiplier`) and
`CompareCards` takes one channel for all cards, so a portal comparison matched
exactly one card and silently returned base rate for the rest — Atlas showed
1,000 points instead of 2,500. Fixed with canonical channels: `issuer_portal`
resolves to whichever channel each card declares, one-directionally, so
querying `smartbuy` never matches an Axis booking. Card-agnostic by design, so
registering a new issuer's portal name needs no per-card table. See
**ADR-011**; regression cover in `tests/rules/test_channels.py` asserts no card
falls back to base on a three-card portal comparison.

**2. Confidence was uniform, not calibrated.** Confidence was derived from
whether values computed, ignoring how good the sources were — a figure from
an official T&C PDF (0.95) read the same as one from a general public web
page (0.7). Added `agents/recommendation/calibration.py`, which derives a
deterministic ceiling from the weakest source confidence used plus the
presence of unknowns or tool errors. The ceiling is injected into the state
digest as `confidence_basis` and **enforced in validation** — a recommender
claiming more confidence than the evidence supports is rejected. Reporting
lower than the ceiling is always allowed.

**3. Numbers could enter prose without entering `calculations`.** Validation
checked that `calculations` entries were verbatim, but nothing checked the
prose. A model could state any figure in `decision` or `reasoning`.
`validate_recommendation` now takes `grounded_text` and requires every 2+
digit number (and every decimal) in prose to appear in the tool results or
retrieved knowledge. **The grounded text deliberately excludes the user's
query**, so a number the user supplies ("assume my points are worth 2.5
rupees") can never be echoed back as though the system computed it.

**4. The shipped demo script stated an ungrounded number.** Fix 3 immediately
caught `agents/workflows/demo.py` asserting "Trailblazer Miles (0.5 ratio)"
in its alternatives when no tool in that query returns a Trailblazer ratio.
Removed the invented figure rather than loosening the check.

**5. The eval harness graded against a stale rule.** `EvalLLM` carried its own
confidence heuristic ("all computed → high") that disagreed with the new
ceiling, so `e07` failed. Pointed it at `confidence_basis` so evaluation and
production are held to one calibration.

**5b. Confidence was reported but never reached the claim it qualified.**
Ranking is points-only and stays that way — weighting by confidence would
manufacture a "confidence-adjusted points" figure no cardholder earns, which
is exactly the synthetic-number injection the whole design forbids. But a
generic "medium confidence" tag hid *which* number was carrying an answer. On
the ₹50,000 portal hotel comparison, Infinia wins by 5× on a SmartBuy
multiplier sourced at 0.7 while Amex and Atlas score lower on 0.95-sourced
rates. `agents/recommendation/margin.py` now deterministically detects when
the winner's deciding field is materially thinner-sourced than a competitor's
(a gap over 0.15, or below 0.75 against a competitor at 0.8+) and produces a
sentence naming that specific number, its source, and the better-evidenced
competitor. Validation requires it **verbatim** in `decision` or `reasoning`,
so it cannot be paraphrased away — the same treatment `calculations` get.

**6. The prose-number check missed short decimals.** The first regex required
two or more digits, so `2.5` — exactly the shape of a point valuation — slipped
through. Widened to catch any decimal while still ignoring bare single digits
("3 cards") that would otherwise fail every answer.

### Verified, no change needed: confidence never influences ranking

Worth knowing because it is the question a reviewer will ask. A full audit
confirmed that source confidence (0.7 vs 0.95) **never** touches which card
wins or how any value is computed. Ranking is on verified computed values
only:

| Path | Sort key |
|---|---|
| `rules/engine/engine.py` `compare_cards` | `(status_order, -points)` |
| `graph/search/paths.py` | `(-cumulative_ratio, hop_count)` |
| `graph/optimization/redemption.py` | `-cumulative_ratio` |

The separation point is `VerifiedValue.is_usable`
(`contracts/api/verified_value.py`), which gates computation on
`status == "verified" and value is not None` — `confidence` is a sibling field
it never reads. A grep for `confidence` across `rules/`, `graph/`, and
`tools/` returns nothing outside schema validation; it appears only in
integrity checks and in reporting on the final answer.

`tests/rules/test_confidence_does_not_rank.py` locks this in with two cards
identical in every computed value and differing only in confidence: they
compute identically, confidence is not a tiebreaker at equal points (checked
in both input orders, since a stable sort would otherwise hide a reordering),
a 0.6-sourced higher rate still out-ranks a 0.95-sourced lower one, and low
confidence never filters a value out of computation. **No production code was
changed** — the behaviour was already correct.

Do not "fix" this later by weighting ranking with confidence. It would
manufacture a confidence-adjusted point total no cardholder earns, injecting
a synthetic number into the one place that must stay purely arithmetic. The
evidence gap is surfaced by the margin caveat (5b) instead.

### Adversarial results

All three held. Note that the stand-in LLMs repeat the same bad payload on
retry to force the failure path; a real model receives the rejection reason as
feedback and would usually self-correct, so these show the floor, not typical
behaviour.

| Case | Outcome |
|---|---|
| Ambiguous card reference ("my Platinum card") | Answered, named the ambiguity and which products were evaluated; the unverified product returned unknown; confidence correctly medium. |
| Comparison mixing verified + unverified cards, claiming the verified one wins at high confidence | **Rejected** — confidence exceeded the ceiling; typed failure, no recommendation. |
| User supplies their own valuation and asks for confirmation | **Rejected** — `2.5` and `1,20,000` not traceable to tool results; typed failure. |

### Found, deliberately NOT fixed

These need a product-owner decision because fixing them means changing a
spec'd contract. Full detail in `docs/KNOWN_LIMITATIONS.md` items 10–14.

- **Accelerated validity windows are not enforced (items 10).** *Time-sensitive.*
  The Amex Reward Multiplier's validity ends **2026-07-31**. `AcceleratedEarn`
  has no validity fields, so after that date the engine keeps applying the 3X
  multiplier until the rule file is edited by hand — the one open case where
  it could compute with a lapsed rate instead of returning unknown. Needs
  either confirmed renewal, a new rule version dropping the entry, or approval
  to add validity fields to the schema.
- **Milestone/tier data is verified but unreachable (item 11).** No tool in the
  BUILD_SPEC §8 registry exposes `milestones`/`tiers`, so "how much more to hit
  Platinum?" answers from retrieved prose at low confidence while verified
  numbers sit unused. The engine also holds no year-to-date spend, so
  spend-to-go is not computable today.
- **Transfer valuations are source-program valuations (item 12).** For a
  transfer goal, value is computed from the source program's point value; what
  the partner balance is worth is unknown. Existing behaviour is spec'd and
  test-covered — I reverted an attempted change when three tests showed it was
  a deliberate decision, rather than rewriting the tests to match my opinion.
- **Calibration is min-over-all-results (item 13).** One weak irrelevant edge
  can cap an otherwise strong answer. Under-claiming is the intended direction.
  Distinct from the margin caveat (5b), which names a specific number rather
  than adjusting an overall label.
- **Cross-issuer vocabulary is hand-maintained (item 14).** The category
  subsumption map (ADR-010) and canonical channel map (ADR-011) are declared,
  not inferred. A new issuer whose portal name or category term is not
  registered falls back to base earn in a comparison **silently, without
  erroring** — the exact failure mode both ADRs were written to fix. See the
  card-onboarding step in §4.

Also worth knowing: `CalculateEarn` clips only *accelerated* caps. Category
caps (Infinia grocery 2,000/month, etc.) are queryable via `CheckCap` but do
not clip base earn (item 9). The Planner prompt now pairs `CheckCap` with
`CalculateEarn` for capped categories so the answer states headroom.

---

## 3. Next steps

Nothing here is started. Sprint scope explicitly excluded all of it.

**Before anything else — the 2026-07-31 Amex deadline.** See above; it is the
only dated item and it degrades correctness silently if missed.

**D2 — Postgres wiring.** The highest-value next step, and the interfaces were
built for it. Replace the in-memory fakes behind the existing contracts,
without changing tool signatures:

- `tools/portfolio/fixtures.py` → real queries (`GetPortfolio`, `GetCards`,
  `GetRewardBalances`, `GetTravelGoals`).
- `rules/engine/cap_store.py` `InMemoryCapUsageStore` → the `cap_usage` table
  (card_id, category, month, accrued_points) per BUILD_SPEC §2. Note the Rule
  Engine is a *pure query* — comparing never consumes cap; the application
  layer records actual spend via `cap_store.record`.
- Knowledge-doc hashes, preferences, episodic memory, and opportunities are
  likewise in-memory today and reset on restart (item 7).

Then migrations, auth (JWT bearer on everything except `/health` and auth
routes), and CRUD APIs under `/api/v1/...` with the
`{data, error, meta{request_id, generated_at}}` envelope. Business logic stays
out of routers; services raise domain exceptions that the API layer maps.

**D3 — knowledge at scale.** Crawlers, change detection, and the Rule Verifier
(ADR-009 / BUILD_SPEC §14a) — detection is not extraction; verification stays
manual-approval by design.

**D4 — product surface.** Next.js 14, strict TypeScript, API types
hand-written in `lib/types.ts` to match the Pydantic schemas (no codegen).

**D5 — opportunity engine + deploy.**

**P2 verification, when research arrives.** Queue order is fixed: HDFC Diners
Club Black, then Regalia, Plat Reserve, MR Card, SmartEarn, Ace, Magnus. One
issuer fully before the next. Do not start without product-owner-supplied
verified sources — the no-fabrication rule means rule data cannot be inferred,
and each batch lands as a new rule version plus corpus and graph updates.

**Card-onboarding checklist — do not skip step 3.** Per-field verification
alone will not catch the integration failures described above:

1. Verify every field against official sources; new rule version.
2. Update the knowledge doc and graph edges; re-run `need_register`.
3. **Check the card's channel and category vocabulary** against
   `rules/evaluator/channels.py` and `rules/evaluator/categories.py`. If its
   portal has a name not yet registered under `issuer_portal`, or it uses a
   category term with a subsumption relationship not yet declared, register
   it — otherwise the card silently earns base rate in every cross-card
   comparison while every one of its fields passes review.
4. Extend `tests/rules/test_channels.py` / `test_categories.py` with the new
   card in a cross-card comparison, asserting it does not fall back to base.

---

## 4. Conventions worth not relearning

- **Unknown over incorrect, always.** A refusal is a success; a confident wrong
  number is the failure mode the whole design exists to prevent. Defect 1 above
  is what that looks like when it slips through.
- **Verification and integration catch different bug classes, and neither
  substitutes for the other.** Defects 1 and 1b were individually-correct
  fields composed into a wrong answer — per-field review is structurally blind
  to them. The converse also holds: the SmartBuy 5X/3X reversal and the Axis
  Group B cap discrepancy were field-level catches that no integration test
  would have found, because a wrong-but-consistently-applied rate produces a
  perfectly coherent comparison. Run both.
- **Ranking is on computed values only.** Confidence is reported, never
  weighted into the math (see the audit above and ADR-002).
- `None` on a numeric field means **confirmed not applicable** (e.g. Atlas and
  Amex have no spend-based fee waiver). `unverified` means **open work**. They
  are different states and must not be collapsed.
- Conflicts are **recorded, not silently resolved** — see the Atlas Radisson
  ratio and Group B cap discrepancies in VERIFICATION_QUEUE.
- Every verification change ships as a **new rule version**; `need_register`
  scans only the latest version per card.
- Synthetic fixture entities (Demo Bank, Sample Bank, Skyhigh, Grandstay,
  `example.test` sources) may be marked verified; real entities require real
  verification (ADR-008).
- Conventional commits. Internal harness files are never committed.

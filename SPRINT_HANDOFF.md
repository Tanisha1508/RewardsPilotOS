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
| Docs (`docs/`) | ADR-001..010, VERIFICATION_QUEUE, KNOWN_LIMITATIONS. |

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

**Current numbers.** 235 tests pass. Rules 25/25, graph 10/10, end-to-end
10/10. Retrieval reports precision@3 0.2833, recall@5 1.0000, MRR 0.5200 —
reported honestly rather than tuned to a target.

```
.venv/bin/python -m pytest                      # 235 passed
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

**6. The prose-number check missed short decimals.** The first regex required
two or more digits, so `2.5` — exactly the shape of a point valuation — slipped
through. Widened to catch any decimal while still ignoring bare single digits
("3 cards") that would otherwise fail every answer.

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
spec'd contract. Full detail in `docs/KNOWN_LIMITATIONS.md` items 10–13.

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

---

## 4. Conventions worth not relearning

- **Unknown over incorrect, always.** A refusal is a success; a confident wrong
  number is the failure mode the whole design exists to prevent. Defect 1 above
  is what that looks like when it slips through.
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

# Live-LLM smoke suite

A small, manually- or schedule-triggered suite that runs a real model
(`default_llm()` — the ADR-018 chain) against a handful of fixture queries and
asserts **structural** properties of the result over N runs. It is the
model-behaviour tripwire the golden suite cannot be.

Source of record: `evaluation/smoke/run.py`. Background and rationale:
`docs/KNOWN_LIMITATIONS.md` items **23–26**, and **ADR-018** (Gemini→Groq
fallback). This README summarises; those are authoritative.

---

## 1. Why it exists separately from the golden suite

The golden end-to-end suite (`evaluation/metrics/e2e_eval.py`) **scripts the
LLM**: its `EvalLLM` emits the golden plan by construction, so the Planner's
*own* output is never exercised. That makes it a determinism and contract check
— and structurally blind to a whole class of bug: a real model emitting a plan
that is well-formed but **wrong in shape**. Every one of those in D4 was found
only by a human typing into `/chat` (KNOWN_LIMITATIONS 23):

- `CompareCards` emitted with `cards: []` — the model correctly declining to
  guess card_keys, then the invocation rejected by validation before injection
  could fill them (KNOWN_LIMITATIONS 24, Class B);
- `CompareCards` **omitted entirely** from a comparison-intent plan;
- a `month` arg that did not match `^\d{4}-\d{2}$`, so the invocation was
  dropped and the answer silently lost its computation (KNOWN_LIMITATIONS 24,
  Class A).

The smoke suite calls the real model to catch exactly that class. It never
replaces the golden suite — the golden suite stays the determinism/contract
check; this is the behaviour tripwire. The production `validate_recommendation`
gate remains the runtime guard regardless of either.

**Why it lives in `evaluation/`, not `tests/`:** `tests/conftest.py` blanks
`Settings.env_file` suite-wide (a real D2 `.env`-leak fix), while `GeminiClient`
reads its key through `get_settings()`. Under pytest the key would resolve
empty, the client would raise, and the suite would *skip* — reporting green
while never calling the model, the exact failure it exists to prevent. So it
sits outside pytest and is run deliberately.

---

## 2. The queries (s01–s04) and what each exercises

Pulled verbatim from `QUERIES` in `run.py`. The four **assertions are shared**
across queries (see §3) — they are not one-bug-per-query. What varies is the
vocabulary surface each query puts in front of the real Planner. Only `s01` is
tied to a *specific* historical failure; the others are honestly characterised
below, including where the mapping is looser than it might look.

| id | query | group | `expect_comparison` |
|----|-------|-------|---------------------|
| `s01_flight_comparison` | "I'm booking a ₹50,000 flight. Which of my cards should I use?" | a | true |
| `s02_portal_hotel_comparison` | "Which of my cards earns the most on a ₹20,000 hotel booking made through the card issuer's own rewards portal?" | a | true |
| `s03_capped_category_comparison` | "I spend about ₹8,000 a month on groceries. Which of my cards is best for that, and am I close to any monthly cap?" | b | true |
| `s04_transfer` | "Can I transfer my reward points to an airline partner, and what would I get for them?" | b | false |

- **`s01` — the canonical case.** Its code note is *"the exact D4 live-/chat
  failure: planner emitted cards=[]"*. A plain undated comparison: the model has
  no month to supply and no card_key vocabulary, so it reproduces both the
  `cards=[]` (Class B) and malformed/missing-`month` (Class A) failures unless
  the planner + `resolve_portfolio_args` handle them. The first live run
  measured `s01` at 2/3 on the comparison checks before the Class A fix, 3/3
  after — this query is the direct evidence path.

- **`s02` — cross-issuer channel vocabulary.** Code note: *"cross-issuer
  channel vocabulary (ADR-011)"*. Its purpose is to put the "issuer's own
  rewards portal" phrasing in front of the model, exercising the canonical
  channel map (ADR-011). Its *assertions*, though, are the same generic
  comparison checks — it does not assert anything channel-specific. Empirically
  it was where the missing-`month` bug bit hardest on the first run (0/3). So:
  motivation = channel vocabulary; assertion coverage = the shared
  comparison-shape checks.

- **`s03` — capped-category comparison.** Code note: *"exercises month args and
  CheckCap pairing"*. The "am I close to any monthly cap?" clause is meant to
  make the planner pair `CheckCap` with the earn comparison (relevant to
  KNOWN_LIMITATIONS 9, category caps reported-not-enforced). Note the same
  caveat as `s02`: the assertions check comparison shape and month-arg
  well-formedness, **not** that a `CheckCap` was actually emitted — that part of
  the intent is exercised but not asserted.

- **`s04` — transfer / graph path. Intent is looser; flagged rather than
  dressed up.** Code note: *"graph path; no CompareCards expected"*,
  `expect_comparison=false`. Because comparison is not expected, the **only**
  assertions that apply are `recommendation_reached` and a vacuously-true
  `month_args_well_formed`. It therefore verifies that a transfer-intent query
  **reaches a recommendation at all** (doesn't crash, doesn't get rejected
  N/N) — it does **not** assert that any transfer path was found, valued, or
  computed. It is graph-path liveness coverage, not a check on transfer output,
  and is not mapped to a specific historical planner bug. If you extend the
  suite, this is the query whose assertions are thinnest.

---

## 3. The four structural assertions — and why they're deliberately loose

From `check_run` in `run.py`. Content is never inspected.

1. **`recommendation_reached`** — `final["recommendation"] is not None`. The run
   produced a recommendation, i.e. `validate_recommendation` did not reject the
   model's output on every attempt. (Applies to every query.)
2. **`plan_has_compare_cards`** — the plan contains a `CompareCards` invocation.
   Maps to the *omission* bug. (Comparison queries only.)
3. **`compare_cards_computed`** — at least one `CompareCards` result reached
   `status: "computed"`. Maps to the `cards=[]` bug: a comparison that *runs*
   but computes nothing is the D4 symptom. (Comparison queries only.)
4. **`month_args_well_formed`** — every `month` arg the model actually emitted
   matches `^\d{4}-\d{2}$`. Maps to the malformed-arg bug. **Vacuously true when
   no month is present**, which is correct — the assertion is about shape *when
   present*, not about presence. (Applies to every query.)

**Why never "winning card" or "exact number":** those vary run-to-run with a
real, non-deterministic model — asserting them would flake immediately, and a
flaky tripwire trains people to re-run until green, which is worse than no
tripwire. Determinism and exact-number grounding are the **golden suite's** job
(scripted LLM, exact match) and the **`validate_recommendation`** gate's job (no
ungrounded numbers in prose). This suite deliberately owns only the shape.

Recording this because **"just assert the answer" is the tempting wrong
change.** It would couple the tripwire to model wording and specific reward
figures, reintroduce flakiness, and duplicate what two other layers already do
better. Keep the assertions structural.

---

## 4. How runs happen

### (a) Automated — GitHub Action (`.github/workflows/smoke.yml`)

- **Schedule:** `cron: "20 8 * * 1,4"` — **Mon & Thu at 08:20 UTC.**
- **Timing requirement:** the free-tier daily quota resets at **00:05 Pacific**
  (07:05 UTC in PDT, 08:05 UTC in PST). A fixed-UTC cron must clear the *later*
  of the two to stay after the reset year-round; **08:20 UTC** does (just past
  the PST reset, ~75 min past the PDT one). The earlier `04:23 UTC` value fired
  *before* the reset and 429'd on contact — don't reintroduce a pre-reset time.
- **Secrets:** authenticates with **encrypted GitHub Actions repository
  secrets** `GEMINI_API_KEY` and (optional) `GROQ_API_KEY`, referenced as
  `${{ secrets.* }}`. Without a Gemini secret the run hits the no-keys path and
  exits 2 — it must be configured under *Settings → Secrets and variables →
  Actions → Repository secrets* for the scheduled run to authenticate.
- **Rotation:** on a scheduled run `SMOKE_GROUP` is blank, so the runner picks
  the pair by **day-of-month parity** (`todays_group`): **group `a` on odd
  days** (`s01`+`s02`), **group `b` on even days** (`s03`+`s04`). Mon and Thu are
  3 days apart — always opposite parity — so within a week one lands on `a` and
  the other on `b`, covering all four queries weekly.
- Never gates a PR; it is not in the fast CI loop.

### (b) Manual — terminal

```bash
.venv/bin/python -m evaluation.smoke.run                       # today's rotation pair (by date parity)
SMOKE_GROUP=all .venv/bin/python -m evaluation.smoke.run       # all four queries
SMOKE_GROUP=a   .venv/bin/python -m evaluation.smoke.run       # force group a (s01+s02)
SMOKE_GROUP=b   .venv/bin/python -m evaluation.smoke.run       # force group b (s03+s04)
SMOKE_GROUP=s02,s04 .venv/bin/python -m evaluation.smoke.run   # arbitrary pair by id prefix
SMOKE_RUNS=5    .venv/bin/python -m evaluation.smoke.run       # override N (default 3)
```

The **arbitrary-pair** form takes a comma-separated list of query-id prefixes
(`s02`, `s02,s04`, …) for targeted reruns of exactly the queries a given day's
quota did not reach. A token matching nothing (a typo like `s2`) is a hard error
rather than a silent zero-query run. Arbitrary pairs do **not** map to date
parity, so they only ever appear when passed explicitly — the scheduled run is
untouched by them.

**Reading the result** (exit code — 0 is the *only* green; see `classify`):

- **0** — every query ran all N attempts and every check held N/N.
- **1** — a structural check came in below the runs that completed (a real
  regression among the attempts we have).
- **2** — did not get a clean N-run result: no keys, zero runs, **or any
  attempt errored** (partial coverage is never reported as a pass).

The report also names the queries it did *not* run, so a rotation half can never
be misread as full coverage.

### (c) Admin-UI trigger — NOT built (future)

There is no admin-panel button to trigger this suite today. The admin panel
itself is **ADR-017** (*Admin Panel for Card Management and Rule Verification*),
which is **accepted but not built**, deferred until after the MVP ships
(post-D5). ADR-017 does not currently specify a smoke-suite trigger; it is
simply the natural future home for one. Treat an admin-UI trigger as unbuilt.

---

## 5. The free-tier quota constraint (KNOWN_LIMITATIONS 26)

The Gemini free tier allows **20 requests/day/model**, and the budget is **per
Google Cloud project = per API key, not per machine.** CI and local runs use the
same key, so they **share one budget** — a CI run and a hand run on the same day
draw from the same 20.

- **A full `N=3` run costs ~24+ calls** (4 queries × 3 runs × ≥2 LLM calls),
  which exceeds the daily budget on its own.
- **`SMOKE_GROUP=all` self-defeats when Gemini is low.** Once the primary
  budget is spent mid-run, every remaining call falls through the ADR-018 chain
  to Groq in rapid succession and hits **Groq's per-minute limit** — observed as
  "all models failed." The fall-through covers *occasional* Gemini
  unavailability, not a whole run's worth bursting at once.
- **Hence the two-day rotation:** 2 queries/day (~12 calls) stays inside budget
  and keeps Gemini fall-through rare. Full coverage comes from **two consecutive
  rotation days**, not one forced `all` run.
- **Posture: manual-primary, Action-as-backup.** The scheduled Mon/Thu run is a
  low-contention backup; day-to-day confirmation is expected to happen by hand.
  This is why the schedule is twice-weekly rather than daily — a daily Action
  would collide with manual runs on the shared budget.

---

## 6. Pointers (don't duplicate — read these)

- **KNOWN_LIMITATIONS 23** — why no automated test exercised the real LLM, and
  the proposal this suite implements.
- **KNOWN_LIMITATIONS 24** — the required-arg failures the assertions map to
  (`cards=[]`, `month`, and the Class A/B/C tool-registry audit).
- **KNOWN_LIMITATIONS 25** — `demo.py` bypasses the ADR-018 fallback (open,
  minor); unrelated to the suite but the same fallback chain.
- **KNOWN_LIMITATIONS 26** — the quota constraint, the rotation, and the Groq
  per-minute burst finding summarised in §5.
- **ADR-018** — the Gemini→Groq tiered fallback the suite runs via
  `default_llm()`.
- **ADR-017** — the (unbuilt) admin panel, natural future home for a UI trigger.
- **ADR-011 / ADR-010** — the canonical channel and category-subsumption maps
  that `s02`/`s01` put in front of the model.

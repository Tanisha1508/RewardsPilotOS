"""Live-LLM smoke suite — the model-behaviour tripwire (KNOWN_LIMITATIONS 23).

The golden set (`evaluation/metrics/e2e_eval.py`) scripts the LLM: `EvalLLM`
emits the golden plan, so the Planner's *own* output is never exercised. That
makes it a determinism and contract check, and structurally blind to the class
of bug D4 hit repeatedly — a real model emitting a plan that is well-formed but
wrong in shape. Every one of those was found by a human typing into `/chat`:

- `CompareCards` emitted with `cards: []` (the model correctly declining to
  guess card_keys), rejected by validation before it could be injected;
- `CompareCards` omitted entirely from a comparison-intent plan;
- a `month` arg that did not match `^\\d{4}-\\d{2}$`, so the invocation was
  dropped and the answer silently lost its computation.

This suite calls a real model and asserts *structural* properties only. It
never asserts a number, a winning card, or any wording — those are the golden
set's job and would flake here immediately.

Why it lives in `evaluation/` and not `tests/`
----------------------------------------------
`tests/conftest.py` installs a session-scoped autouse fixture that sets
`Settings.model_config["env_file"] = None`, so a developer's `.env` cannot leak
into the suite (it is the fix for a real D2 bug). But `GeminiClient` reads its
key through `get_settings()`, not `os.environ` — so under pytest the key would
resolve empty for anyone whose key lives in `.env`, the client would raise, and
the suite would *skip*. A skipped smoke suite reports green while never calling
the model, which is the exact failure it exists to prevent. Bending that
fixture for one directory is how `.env` leaks back into the other 389 tests, so
the suite sits outside pytest instead.

Design decisions worth not relearning
-------------------------------------
- **`default_llm()`, not a bare `GeminiClient`** — production runs the ADR-018
  tiered chain (Gemini primary → second Gemini model → Groq), so the smoke test
  runs it too. (`agents/workflows/demo.py` still constructs a bare
  `GeminiClient`; flagged as a follow-up, not fixed here.)
- **In-memory fixture portfolio, not Postgres.** One real dependency at a time:
  if a run hits real Gemini *and* real Supabase, a failure does not say which
  broke, and that ambiguity is how a suite stops being run.
- **Failure of a check in any run fails the suite.** "Tolerant of
  non-determinism" means not asserting on content — not tolerating a structural
  invariant that holds 2 times in 3. The D4 planner bug presented exactly as an
  intermittent rate, so k/N is reported per check and anything below N/N is a
  regression.
- **Infrastructure failure is not a regression.** A missing key or an exhausted
  quota exits 2, distinct from exit 1 (a real structural failure), so a red run
  is never ambiguous.

Run:
    .venv/bin/python -m evaluation.smoke.run              # today's rotation pair
    SMOKE_GROUP=all .venv/bin/python -m evaluation.smoke.run   # all 4 queries
    SMOKE_GROUP=b .venv/bin/python -m evaluation.smoke.run     # force a pair
    SMOKE_GROUP=s02,s04 .venv/bin/python -m evaluation.smoke.run  # arbitrary pair by id prefix
    SMOKE_RUNS=5 .venv/bin/python -m evaluation.smoke.run

Queries run in two fixed pairs on alternating days to fit the Gemini free-tier
daily quota without shrinking N — see the rotation note below and
KNOWN_LIMITATIONS 26.

Exit codes (0 is the ONLY green — see `classify`):
  0  every query ran all N attempts and every check held N/N
  1  a structural check came in below the runs that completed (a regression)
  2  did not get a clean N-run result — no keys, zero runs, OR any attempt
     errored (partial coverage is never reported as a pass)
"""

import json
import os
import re
import sys
from datetime import date

from agents.planner.planner import _parse_payload
from agents.registry import LLM, LLMUnavailableError, default_llm
from agents.state.schema import initial_state
from agents.workflows.graph import build_workflow
from tools.memory.source import InMemoryMemorySource
from tools.memory.source import set_source as set_memory_source
from tools.portfolio.source import InMemoryPortfolioSource, acting_as, load_seed
from tools.portfolio.source import set_source as set_portfolio_source

MONTH_RE = re.compile(r"^\d{4}-\d{2}$")

DEFAULT_RUNS = 3

# Four queries against the demo portfolio (HDFC Infinia + Axis Atlas, both P1
# verified, plus one synthetic card with no card_key). Three are comparisons —
# the shape that broke in D4 — and one is a transfer, which exercises the graph
# path and must still reach a recommendation.
QUERIES = [
    {
        "id": "s01_flight_comparison",
        "query": "I'm booking a ₹50,000 flight. Which of my cards should I use?",
        "expect_comparison": True,
        "note": "the exact D4 live-/chat failure: planner emitted cards=[]",
        "group": "a",
    },
    {
        "id": "s02_portal_hotel_comparison",
        "query": (
            "Which of my cards earns the most on a ₹20,000 hotel booking "
            "made through the card issuer's own rewards portal?"
        ),
        "expect_comparison": True,
        "note": "cross-issuer channel vocabulary (ADR-011)",
        "group": "a",
    },
    {
        "id": "s03_capped_category_comparison",
        "query": (
            "I spend about ₹8,000 a month on groceries. Which of my cards is "
            "best for that, and am I close to any monthly cap?"
        ),
        "expect_comparison": True,
        "note": "exercises month args and CheckCap pairing",
        "group": "b",
    },
    {
        "id": "s04_transfer",
        "query": (
            "Can I transfer my reward points to an airline partner, and what "
            "would I get for them?"
        ),
        "expect_comparison": False,
        "note": "graph path; no CompareCards expected",
        "group": "b",
    },
]


# ── Rotation ─────────────────────────────────────────────────────────────────
# The Gemini free tier allows 20 requests/day/model
# (`GenerateRequestsPerDayPerProjectPerModel-FreeTier`), while a full
# 4-query × N=3 run costs 24+ calls (KNOWN_LIMITATIONS 26). Rather than shrink
# N or switch provider, the queries run in two fixed pairs on alternating days:
# ~12 calls/day, comfortably inside quota, and every query is exercised every
# other day rather than starved indefinitely.
#
# Why not the alternatives:
# - `SMOKE_RUNS=1` fits, but defeats the point. N=3 exists to catch
#   *intermittent* planner failures — the D4 CompareCards omission presented as
#   3/6, not 0/6. A single run is blind to precisely the bug class this suite
#   was built for.
# - Groq-as-primary fits, but tests the wrong system. ADR-018 makes Gemini
#   primary and Groq the last resort, so a Groq-primary suite would validate a
#   path real users rarely take.
#
# Note what the rotation does *not* compromise: `default_llm()` still runs the
# full ADR-018 chain, so if Gemini's quota is exhausted mid-run the suite does
# not fail — it falls through to Groq exactly as production would. The quota
# shapes how often each query is covered, not whether the suite is correct.
GROUPS = ("a", "b")


def todays_group(today: date | None = None) -> str:
    """Group "a" on odd days of the month, "b" on even.

    Day-of-month parity, not an alternating counter, so the choice is stateless
    and reproducible: any machine, any run, same day → same pair. The 31st
    followed by the 1st repeats group "a"; that costs one day of group "b"
    latency seven times a year and is not worth carrying state to avoid.
    """
    return "a" if (today or date.today()).day % 2 else "b"


def select_queries(group: str | None = None) -> list[dict]:
    """The queries to run.

    - `"all"` runs everything — a deliberate manual full-coverage run.
    - `"a"`/`"b"` run a rotation group (what the scheduled Mon/Thu run uses).
    - anything else is treated as a comma-separated list of query-id prefixes
      (e.g. `"s02,s04"`) — a manual/workflow_dispatch escape hatch for
      re-running exactly the queries a given day's quota did not reach.
      Arbitrary pairs do NOT map to day-of-month parity, so they are never what
      the schedule picks; they only appear when a value is passed explicitly.

    A token matching no query is a hard error, so a typo like `s2` cannot
    silently run zero queries — the same failure-visible principle as the rest
    of the suite.
    """
    group = group or os.environ.get("SMOKE_GROUP") or todays_group()
    if group == "all":
        return list(QUERIES)
    if group in GROUPS:
        return [query for query in QUERIES if query["group"] == group]
    tokens = [token.strip() for token in group.split(",") if token.strip()]
    unmatched = [token for token in tokens if not any(q["id"].startswith(token) for q in QUERIES)]
    if not tokens or unmatched:
        raise SystemExit(
            f"SMOKE_GROUP must be 'a', 'b', 'all', or a comma-separated list of "
            f"query-id prefixes; got {group!r}"
            + (f" (no query matches: {', '.join(unmatched)})" if unmatched else "")
        )
    return [query for query in QUERIES if any(query["id"].startswith(token) for token in tokens)]


class RecordingLLM:
    """Wraps the real LLM and keeps the Planner's *raw* responses.

    Necessary because `state["plan"]` is post-validation: `validate_plan`
    silently drops a malformed invocation into `errors`, so a bad `month` would
    show up only as a missing tool, not as the arg bug it actually is. Asserting
    on the raw payload names the real defect.
    """

    def __init__(self, inner: LLM) -> None:
        self._inner = inner
        self.planner_raw: list[str] = []

    def complete(self, system: str, user: str) -> str:
        output = self._inner.complete(system, user)
        # Same dispatch the eval and demo stand-ins use.
        if "Planner prompt" in system:
            self.planner_raw.append(output)
        return output


def _raw_month_args(planner_raw: list[str]) -> list[str]:
    """Every month value the model actually committed to, before validation
    dropped any.

    `null` and absent are deliberately NOT collected. Since the item-24 fix
    they are legitimate — they mean "the current month", resolved at the tool
    boundary — and the model emits `"month": null` routinely now that the
    prompt no longer forces it to invent one. Counting `null` as malformed
    would fail this check on correct behaviour, which is how a smoke suite
    trains people to ignore it.
    """
    months: list[str] = []
    for raw in planner_raw:
        try:
            payload = _parse_payload(raw)
        except (json.JSONDecodeError, ValueError):
            continue  # covered by recommendation_reached; not a month failure
        for entry in payload.get("plan") or []:
            if not isinstance(entry, dict):
                continue
            args = entry.get("args")
            if isinstance(args, dict) and args.get("month") is not None:
                months.append(str(args["month"]))
    return months


# The planner and recommender nodes catch `LLMUnavailableError` themselves and
# append it to `state["errors"]`, so an exhausted quota or a 503 spike reaches
# this runner looking exactly like a structural failure: empty plan, no
# recommendation, no exception. Detecting it here keeps exit 1 (the model
# regressed) distinct from exit 2 (we never really called the model) — the
# distinction the suite is built around, which the first version missed
# because it only caught the error when it escaped the workflow.
_UNAVAILABLE_MARKERS = ("llm failed after retry", "all models failed")


def llm_was_unavailable(final: dict) -> bool:
    return any(
        marker in error.lower() for error in final["errors"] for marker in _UNAVAILABLE_MARKERS
    )


def check_run(final: dict, planner_raw: list[str], expect_comparison: bool) -> dict[str, bool]:
    """The four structural assertions. Content is never inspected."""
    checks: dict[str, bool] = {}

    # 1. The run produced a recommendation at all — i.e. validation did not
    #    reject the model's output on every attempt.
    checks["recommendation_reached"] = final["recommendation"] is not None

    if expect_comparison:
        # 2. The plan actually contains CompareCards (the omission bug).
        checks["plan_has_compare_cards"] = any(
            invocation["tool"] == "CompareCards" for invocation in final["plan"]
        )
        # 3. At least one CompareCards result computed (the cards=[] bug —
        #    a comparison that runs but computes nothing is the D4 symptom).
        checks["compare_cards_computed"] = any(
            result.get("tool") == "CompareCards" and result.get("status") == "computed"
            for result in final["rule_results"]
        )

    # 4. Every month arg the model emitted is well formed (the malformed-arg
    #    bug). Vacuously true when the plan needs no month, which is correct:
    #    the assertion is about shape when present, not about presence.
    checks["month_args_well_formed"] = all(
        MONTH_RE.match(month) for month in _raw_month_args(planner_raw)
    )
    return checks


def run_query(item: dict, user_id: str, runs: int) -> dict:
    """Run one query `runs` times, aggregating each check to k/N."""
    tally: dict[str, list[bool]] = {}
    errors: list[str] = []
    for attempt in range(runs):
        recorder = RecordingLLM(default_llm())
        workflow = build_workflow(recorder)
        try:
            final = workflow.invoke(initial_state(item["query"], user_id))
        except LLMUnavailableError as exc:
            # Infrastructure, not a regression — surfaced separately so an
            # exhausted quota never reads as a structural failure.
            errors.append(f"run {attempt + 1}: {exc}")
            continue
        if llm_was_unavailable(final):
            # Same thing, but swallowed by a node's own error handling rather
            # than raised. Discard the run instead of scoring it: a quota blip
            # would otherwise present as every structural check failing at once.
            errors.append(f"run {attempt + 1}: LLM unavailable (from state errors)")
            continue
        for name, passed in check_run(
            final, recorder.planner_raw, item["expect_comparison"]
        ).items():
            tally.setdefault(name, []).append(passed)
    return {
        "id": item["id"],
        "note": item["note"],
        "runs_completed": max((len(v) for v in tally.values()), default=0),
        "checks": {name: (sum(results), len(results)) for name, results in tally.items()},
        "errors": errors,
    }


def run(runs: int = DEFAULT_RUNS, group: str | None = None) -> dict:
    """Install the seeded fakes, then run today's queries. Mirrors
    `e2e_eval.run` — the smoke suite deliberately does not inherit
    `tests/conftest.py`, so it installs sources itself."""
    selected = select_queries(group)
    seed = load_seed()
    set_portfolio_source(InMemoryPortfolioSource(seed))
    set_memory_source(InMemoryMemorySource(seed))
    try:
        with acting_as(seed["user_id"]):
            return {
                "runs": runs,
                "group": group or os.environ.get("SMOKE_GROUP") or todays_group(),
                "queries": [run_query(q, seed["user_id"], runs) for q in selected],
            }
    finally:
        set_portfolio_source(None)
        set_memory_source(None)


def _print_report(report: dict) -> None:
    covered = ", ".join(result["id"] for result in report["queries"])
    print(
        f"\n=== Live-LLM smoke suite — group {report['group']}, "
        f"N={report['runs']} per query ===\n"
    )
    # Name what was NOT run. A rotation that silently reports only its own half
    # would read as full coverage — the same "skipped proves nothing" trap the
    # suite is built to avoid, one level up.
    skipped = [q["id"] for q in QUERIES if q["id"] not in covered]
    if skipped:
        print(f"Not run today (rotation, KNOWN_LIMITATIONS 26): {', '.join(skipped)}\n")
    for result in report["queries"]:
        print(f"{result['id']}  ({result['note']})")
        if not result["checks"]:
            print("  NO RUNS COMPLETED")
        for name, (passed, total) in sorted(result["checks"].items()):
            mark = "PASS" if passed == total else "FAIL"
            print(f"  [{mark}] {name}: {passed}/{total}")
        for error in result["errors"]:
            print(f"  [ERROR] {error}")
        print()


def classify(report: dict) -> tuple[int, list]:
    """Pure exit-decision, separated from I/O so it can be unit-tested without
    calling a model.

    Exactly one outcome is a pass, and it is the strict one:

    - 1 — a structural check came in below the runs that DID complete: a real
      regression among the attempts we have (highest priority; a genuine bug
      outranks any infra noise).
    - 2 — the suite did not achieve a clean full-N confirmation: a query
      completed zero runs, OR any attempt errored (partial coverage). This is
      NOT a pass. A run that quietly drops from N=3 to N=1 because two attempts
      hit quota has lost exactly the intermittent-failure sensitivity the suite
      exists for, so reporting it green would be the "degraded looks like
      passing" failure — the same trap, one level in.
    - 0 — every query ran all N attempts and every check held N/N. Only this.
    """
    failed = [
        (result["id"], name)
        for result in report["queries"]
        for name, (passed, total) in result["checks"].items()
        if passed != total
    ]
    if failed:
        return 1, failed
    # `checks` empty → zero runs; `errors` non-empty → some attempt did not
    # complete. Either means we do not have a clean N-run result for that query.
    incomplete = [
        result["id"] for result in report["queries"] if not result["checks"] or result["errors"]
    ]
    if incomplete:
        return 2, incomplete
    return 0, []


def main() -> int:
    # Resolve the key the same way the client does — through `Settings`, which
    # honours `.env` outside pytest. Gating on `os.environ` instead would skip
    # locally for every developer whose key lives in `.env` while the client
    # itself would have worked: a false SKIP is the same silent-green failure
    # this suite exists to prevent.
    from backend.config.settings import get_settings

    settings = get_settings()
    if not (settings.gemini_api_key or settings.groq_api_key):
        # Loud, non-zero. A smoke suite is run deliberately, so silently not
        # running it is a failure of intent — the "a skipped test proves
        # nothing" lesson from the 52 DB integration tests.
        print(
            "SKIPPED: no GEMINI_API_KEY or GROQ_API_KEY configured (checked "
            "process env and .env).\n"
            "This suite exists to call a real model; it has not verified anything.",
            file=sys.stderr,
        )
        return 2

    runs = int(os.environ.get("SMOKE_RUNS", DEFAULT_RUNS))
    report = run(runs)
    _print_report(report)

    code, detail = classify(report)
    if code == 1:
        print(
            f"FAILED: {len(detail)} structural check(s) below the runs that completed:",
            file=sys.stderr,
        )
        for query_id, name in detail:
            print(f"  {query_id}.{name}", file=sys.stderr)
    elif code == 2:
        # Never green. Partial or zero coverage is not a confirmation.
        print(
            "INCOMPLETE: did not get a clean N-run result for: "
            + ", ".join(detail)
            + "\nThis is not a pass — some attempts did not complete (see [ERROR] lines above).",
            file=sys.stderr,
        )
    else:
        print("PASSED: every query ran all N attempts and every structural check held.")
    return code


if __name__ == "__main__":
    raise SystemExit(main())

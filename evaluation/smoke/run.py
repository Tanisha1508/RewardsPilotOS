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
    .venv/bin/python -m evaluation.smoke.run          # N=3 (default)
    SMOKE_RUNS=5 .venv/bin/python -m evaluation.smoke.run

Exit codes: 0 all checks N/N · 1 a structural check failed · 2 could not run.
"""

import json
import os
import re
import sys

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
    },
    {
        "id": "s02_portal_hotel_comparison",
        "query": (
            "Which of my cards earns the most on a ₹20,000 hotel booking "
            "made through the card issuer's own rewards portal?"
        ),
        "expect_comparison": True,
        "note": "cross-issuer channel vocabulary (ADR-011)",
    },
    {
        "id": "s03_capped_category_comparison",
        "query": (
            "I spend about ₹8,000 a month on groceries. Which of my cards is "
            "best for that, and am I close to any monthly cap?"
        ),
        "expect_comparison": True,
        "note": "exercises month args and CheckCap pairing",
    },
    {
        "id": "s04_transfer",
        "query": (
            "Can I transfer my reward points to an airline partner, and what "
            "would I get for them?"
        ),
        "expect_comparison": False,
        "note": "graph path; no CompareCards expected",
    },
]


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
    """Every `month` value the model emitted, before validation dropped any."""
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
            if isinstance(args, dict) and "month" in args:
                months.append(str(args["month"]))
    return months


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


def run(runs: int = DEFAULT_RUNS) -> dict:
    """Install the seeded fakes, then run every query. Mirrors
    `e2e_eval.run` — the smoke suite deliberately does not inherit
    `tests/conftest.py`, so it installs sources itself."""
    seed = load_seed()
    set_portfolio_source(InMemoryPortfolioSource(seed))
    set_memory_source(InMemoryMemorySource(seed))
    try:
        with acting_as(seed["user_id"]):
            return {"runs": runs, "queries": [run_query(q, seed["user_id"], runs) for q in QUERIES]}
    finally:
        set_portfolio_source(None)
        set_memory_source(None)


def _print_report(report: dict) -> None:
    print(f"\n=== Live-LLM smoke suite — N={report['runs']} per query ===\n")
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

    had_error = any(result["errors"] for result in report["queries"])
    no_runs = any(not result["checks"] for result in report["queries"])
    failed = [
        (result["id"], name)
        for result in report["queries"]
        for name, (passed, total) in result["checks"].items()
        if passed != total
    ]

    if failed:
        print(f"FAILED: {len(failed)} structural check(s) below N/N:", file=sys.stderr)
        for query_id, name in failed:
            print(f"  {query_id}.{name}", file=sys.stderr)
        return 1
    if no_runs:
        print("COULD NOT RUN: a query completed zero runs.", file=sys.stderr)
        return 2
    if had_error:
        print("PASSED, with infrastructure errors on some runs (see above).", file=sys.stderr)
        return 0
    print("PASSED: every structural check held on every run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

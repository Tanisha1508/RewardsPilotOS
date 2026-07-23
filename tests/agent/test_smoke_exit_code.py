"""The smoke suite's exit code never reports a degraded run as green.

The masking bug (fixed 2026-07-23): `main()` had an `if had_error: return 0`
path, so a run where some attempts hit quota — silently collapsing N=3 to
however many survived — exited 0 with a warning. A CI job would show green over
a run that lost exactly the intermittent-failure sensitivity the suite exists
for. `classify()` is the pure exit-decision; these lock its contract without
calling a model.
"""

import pytest

from evaluation.smoke.run import classify


def _q(qid, checks, errors=()):
    return {"id": qid, "checks": dict(checks), "errors": list(errors)}


def _report(*queries, runs=3):
    return {"runs": runs, "group": "test", "queries": list(queries)}


def test_clean_full_pass_is_zero():
    assert classify(_report(_q("s01", {"a": (3, 3), "b": (3, 3)})))[0] == 0


def test_a_structural_regression_is_one():
    assert classify(_report(_q("s01", {"a": (2, 3)})))[0] == 1


def test_zero_completed_runs_is_two():
    assert classify(_report(_q("s01", {}, ["run 1: LLM unavailable"])))[0] == 2


def test_partial_run_with_errors_is_not_green():
    """The core of the fix: 1 of 3 attempts completed and passed, 2 errored.
    Previously returned 0 with a warning; must now be 2."""
    code, detail = classify(
        _report(_q("s01", {"a": (1, 1)}, ["run 2: unavailable", "run 3: unavailable"]))
    )
    assert code == 2
    assert "s01" in detail


def test_a_regression_outranks_infra_noise():
    """A real structural failure is the most important signal, even when the
    same run also had infra errors."""
    assert classify(_report(_q("s01", {"a": (1, 2)}, ["run 3: unavailable"])))[0] == 1


def test_one_clean_query_does_not_excuse_another_incomplete_one():
    """Today's exact case: s01 clean 3/3, s02 zero runs. Not a pass."""
    assert classify(_report(_q("s01", {"a": (3, 3)}), _q("s02", {}, ["unavailable"])))[0] == 2


@pytest.mark.parametrize("code", [0, 1, 2])
def test_only_zero_means_pass(code):
    """A sanity check that the three outcomes are distinct and 0 is the only
    green — no fourth 'pass with caveats' branch snuck back in."""
    reports = {
        0: _report(_q("s01", {"a": (3, 3)})),
        1: _report(_q("s01", {"a": (0, 3)})),
        2: _report(_q("s01", {"a": (1, 1)}, ["unavailable"])),
    }
    assert classify(reports[code])[0] == code

"""Regression gate: deterministic golden sets must stay at 100% exact match.

Run by pytest (testpaths include this via tests/ symlink-free import) and by
CI on push. Retrieval metrics are reported (not gated) in REPORT.md."""

from evaluation.metrics import graph_eval, rules_eval


def test_rules_exact_match_100():
    result = rules_eval.run()
    failing = [s for s in result["per_scenario"] if not s["passed"]]
    assert result["exact_match"] == 1.0, failing


def test_graph_exact_match_100():
    result = graph_eval.run()
    failing = [q for q in result["per_query"] if not q["passed"]]
    assert result["exact_match"] == 1.0, failing

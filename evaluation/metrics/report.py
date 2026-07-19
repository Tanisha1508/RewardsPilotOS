"""Run all golden-set evals and write evaluation/reports/REPORT.md.

Usage: python -m evaluation.metrics.report
"""

import json
import sys
from datetime import date
from pathlib import Path

from evaluation.metrics import e2e_eval, graph_eval, retrieval_eval, rules_eval

REPORT_PATH = Path(__file__).resolve().parent.parent / "reports" / "REPORT.md"


def build_report() -> tuple[str, dict]:
    retrieval = retrieval_eval.run()
    rules = rules_eval.run()
    graph = graph_eval.run()
    e2e = e2e_eval.run()

    lines = [
        "# Evaluation report",
        "",
        f"Measured eval results, run on {date.today().isoformat()} against the "
        "sprint fixture corpus and seed data (synthetic fixtures clearly "
        "labeled; real-issuer numbers ship unverified and are expected to be "
        "refused). Product metrics in MASTER_SPEC are targets, not "
        "measurements.",
        "",
        "| Suite | Size | Metric | Result | Target |",
        "|---|---|---|---|---|",
        f"| Retrieval | {retrieval['queries']} queries | precision@3 | "
        f"{retrieval['precision_at_3']:.4f} | reported honestly |",
        f"| Retrieval | {retrieval['queries']} queries | recall@5 | "
        f"{retrieval['recall_at_5']:.4f} | reported honestly |",
        f"| Retrieval | {retrieval['queries']} queries | MRR | "
        f"{retrieval['mrr']:.4f} | reported honestly |",
        f"| Rules | {rules['scenarios']} scenarios | exact match | "
        f"{rules['exact_match']:.2%} ({rules['passed']}/{rules['scenarios']}) | 100% |",
        f"| Graph | {graph['queries']} queries | exact match | "
        f"{graph['exact_match']:.2%} ({graph['passed']}/{graph['queries']}) | 100% |",
        f"| End-to-end | {e2e['queries']} queries | all checks pass | "
        f"{e2e['pass_rate']:.2%} ({e2e['passed']}/{e2e['queries']}) | 100% |",
        "",
        "## End-to-end checks",
        "",
        "Per query: recommendation produced (contract-valid), citations present,",
        "calculations verbatim from tool results (no invented values), prose",
        "numbers traceable to tool outputs (string match), confidence reported,",
        "and unknowns stated plainly where expected.",
        "",
        "## Failures",
        "",
    ]
    failures = []
    for suite in (rules, graph, e2e):
        key = "per_scenario" if "per_scenario" in suite else "per_query"
        for item in suite[key]:
            if not item["passed"]:
                failures.append(f"- {suite['name']} {item['id']}: {json.dumps(item)[:500]}")
    lines.extend(failures if failures else ["None."])
    lines.append("")

    summary = {
        "retrieval": {k: retrieval[k] for k in ("precision_at_3", "recall_at_5", "mrr")},
        "rules_exact_match": rules["exact_match"],
        "graph_exact_match": graph["exact_match"],
        "e2e_pass_rate": e2e["pass_rate"],
    }
    return "\n".join(lines), summary


def main() -> int:
    report, summary = build_report()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report)
    print(report)
    print(f"Report written to {REPORT_PATH}")
    all_deterministic_green = (
        summary["rules_exact_match"] == 1.0
        and summary["graph_exact_match"] == 1.0
        and summary["e2e_pass_rate"] == 1.0
    )
    return 0 if all_deterministic_green else 1


if __name__ == "__main__":
    sys.exit(main())

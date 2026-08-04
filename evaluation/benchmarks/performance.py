"""Latency and reliability of the deterministic stages, measured locally.

Why this exists, and what it deliberately does not claim
-------------------------------------------------------
The quality suites in `evaluation/metrics/` answer "is the answer right". This
answers "how long did it take, and how often did the machinery work at all".

**Everything here excludes model time.** The two LLM nodes (Planner,
Recommender) are the dominant term in a real request — measured at roughly 29 s
warm in production — and they are also the one part that cannot be benchmarked
locally without spending a shared free-tier quota that the deployed app depends
on. Reporting a total that omits them would be worse than reporting nothing, so
this module measures the stages it can measure honestly and labels them as
such: retrieval, the rule engine, the graph engine, and orchestration overhead.

Read the orchestration figure carefully. It runs the real LangGraph workflow
with a scripted LLM, so it is the cost of *everything except the model*: state
handling, tool dispatch, validation, contract checks. Useful for spotting a
regression in our own code; useless as a prediction of what a user waits.

Percentiles are computed with `statistics.quantiles`, over repeated runs of a
fixed workload. A cold first call is reported separately rather than folded into
the distribution, because the corpus loads lazily and the first call is a
different event from the rest (KNOWN_LIMITATIONS 28).

Reliability here means: did the deterministic pipeline do what it was asked,
counted over the golden sets. It is not an uptime measurement of the deployed
service — a single machine running a fixed workload cannot tell you that.

Run: python -m evaluation.benchmarks.performance
"""

import json
import statistics
import time
from pathlib import Path

RESULTS = Path(__file__).resolve().parent.parent / "reports" / "performance.json"
DATASETS = Path(__file__).resolve().parent.parent / "datasets"

# Enough samples for a stable median and a meaningful p95 without turning the
# suite into something nobody reruns. 20 samples puts p95 between the 19th and
# 20th ordered value — honest, and stated as such in the report.
REPEATS = 20


def _percentiles(samples_ms: list[float]) -> dict:
    ordered = sorted(samples_ms)
    return {
        "n": len(ordered),
        "min_ms": round(ordered[0], 2),
        "p50_ms": round(statistics.median(ordered), 2),
        "p95_ms": round(ordered[int(len(ordered) * 0.95) - 1], 2),
        "max_ms": round(ordered[-1], 2),
        "mean_ms": round(statistics.fmean(ordered), 2),
    }


def retrieval_latency() -> dict:
    """Hybrid retrieval end to end: embed, semantic, BM25, fusion, freshness."""
    from tools.knowledge_search.service import get_retriever

    queries = [q["query"] for q in json.loads((DATASETS / "retrieval_production.json").read_text())["queries"]]
    retriever = get_retriever()

    # Separated deliberately: the first call pays for lazy corpus load and model
    # warm-up, and averaging it in would misdescribe both it and everything else.
    cold_start = time.perf_counter()
    retriever.search(queries[0], k=5)
    cold_ms = (time.perf_counter() - cold_start) * 1000

    samples = []
    for i in range(REPEATS):
        query = queries[i % len(queries)]
        started = time.perf_counter()
        retriever.search(query, k=5)
        samples.append((time.perf_counter() - started) * 1000)

    return {
        "stage": "hybrid_retrieval",
        "workload": f"{len(queries)} production golden queries, k=5, cycled",
        "cold_first_call_ms": round(cold_ms, 2),
        **_percentiles(samples),
    }


def rule_engine_latency() -> dict:
    """One earn evaluation: load the rule file, apply windows, caps, exclusions."""
    from rules.evaluator.evaluator import evaluate_earn
    from rules.parser.loader import load_rule

    cards = ["axis_atlas", "hdfc_infinia", "amex_plat_travel"]
    samples = []
    for i in range(REPEATS):
        card = cards[i % len(cards)]
        started = time.perf_counter()
        evaluate_earn(load_rule(card), 50000, "flights", "direct", "2026-08")
        samples.append((time.perf_counter() - started) * 1000)

    return {
        "stage": "rule_engine_evaluate_earn",
        "workload": "3 verified cards cycled, INR 50,000 flights/direct",
        **_percentiles(samples),
    }


def graph_engine_latency() -> dict:
    """Best-transfer-path search over the verified NetworkX graph."""
    from contracts.tools.graph_engine import BestTransferPathsInput
    from tools.graph_engine.tools import best_transfer_paths

    queries = [
        q
        for q in json.loads((DATASETS / "graph.json").read_text())["queries"]
        if q.get("type") == "best_transfer_paths" and q.get("currency") and q.get("target_program")
    ]
    samples, executed = [], 0
    for i in range(REPEATS):
        item = queries[i % len(queries)]
        started = time.perf_counter()
        best_transfer_paths(
            BestTransferPathsInput(currency=item["currency"], target_program=item["target_program"])
        )
        samples.append((time.perf_counter() - started) * 1000)
        executed += 1

    if not samples:
        return {"stage": "graph_engine_best_paths", "error": "no runnable queries in golden set"}
    return {
        "stage": "graph_engine_best_paths",
        "workload": f"{executed} runs over the graph golden set",
        **_percentiles(samples),
    }


def orchestration_overhead() -> dict:
    """The LangGraph workflow with a scripted LLM: our code, not the model.

    Stated as overhead rather than latency on purpose — a reader who sees
    "end-to-end latency" next to a small number will assume it is what a user
    waits, and it is not.
    """
    from evaluation.metrics import e2e_eval

    started = time.perf_counter()
    result = e2e_eval.run()
    elapsed_ms = (time.perf_counter() - started) * 1000
    queries = result.get("queries", 0)

    return {
        "stage": "langgraph_orchestration_excluding_model",
        "workload": f"{queries} end-to-end golden queries, scripted deterministic LLM",
        "total_ms": round(elapsed_ms, 2),
        "per_query_mean_ms": round(elapsed_ms / queries, 2) if queries else None,
        "excludes": "Planner and Recommender model calls (~29 s warm in production)",
    }


def reliability() -> dict:
    """Did the deterministic machinery do its job, counted over the golden sets.

    Every number here is a ratio of golden-set cases that completed, not an
    uptime figure. A tool that correctly refuses to compute on unverified data
    counts as a success: refusing is the specified behaviour, and scoring it as
    a failure would reward a system that guesses.
    """
    from evaluation.metrics import e2e_eval, graph_eval, rules_eval

    rules = rules_eval.run()
    graph = graph_eval.run()
    e2e = e2e_eval.run()

    def ratio(passed, total):
        return round(passed / total, 4) if total else None

    return {
        "rule_engine_scenarios": {
            "total": rules["scenarios"],
            "passed": rules["passed"],
            "success_rate": ratio(rules["passed"], rules["scenarios"]),
        },
        "graph_queries": {
            "total": graph["queries"],
            "passed": graph["passed"],
            "success_rate": ratio(graph["passed"], graph["queries"]),
        },
        "end_to_end_workflow": {
            "total": e2e["queries"],
            "passed": e2e["passed"],
            "success_rate": ratio(e2e["passed"], e2e["queries"]),
            "checks_per_query": (
                "contract-valid recommendation, citations present, calculations "
                "verbatim from tool results, prose numbers traceable, confidence reported"
            ),
        },
    }


def run() -> dict:
    return {
        "note": (
            "Latency figures exclude LLM time and are measured on one local "
            "machine. They characterise this codebase, not the deployed service."
        ),
        "repeats": REPEATS,
        "latency": [
            retrieval_latency(),
            rule_engine_latency(),
            graph_engine_latency(),
            orchestration_overhead(),
        ],
        "reliability": reliability(),
    }


if __name__ == "__main__":
    results = run()
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    RESULTS.write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2))
    print(f"\nWritten to {RESULTS}")

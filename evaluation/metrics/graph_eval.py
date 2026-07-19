"""Graph golden set runner: exact match on hand-computed ranked paths."""

import json
from pathlib import Path

from contracts.tools.graph_engine import RedemptionGoal
from graph.builder.builder import load_seed_graph
from graph.optimization.redemption import redemption_options
from graph.search.paths import best_transfer_paths
from tools.reward_calculator.values import get_point_values

DATASET = Path(__file__).resolve().parent.parent / "datasets" / "graph.json"


def _run_query(graph, item: dict) -> dict:
    if item["type"] == "best_transfer_paths":
        result = best_transfer_paths(graph, item["currency"], item["target_program"])
        return {
            "paths": [
                {
                    "nodes": p.nodes,
                    "cumulative_ratio": p.cumulative_ratio,
                    "min_transfer": p.min_transfer,
                }
                for p in result.paths
            ],
            "unverified_paths_exist": result.unverified_paths_exist,
        }
    if item["type"] == "redemption_options":
        goal = RedemptionGoal.model_validate(item["goal"])
        output = redemption_options(
            graph, item["portfolio"], goal, get_point_values(list(item["portfolio"]))
        )
        return {
            "options": [
                {
                    "currency": o.currency,
                    "points_required": o.points_required,
                    "balance_sufficient": o.balance_sufficient,
                    "value_status": o.value_status,
                }
                for o in output.options
            ]
        }
    raise ValueError(f"unknown query type {item['type']}")


def run() -> dict:
    dataset = json.loads(DATASET.read_text())
    graph = load_seed_graph()
    per_query = []
    for item in dataset["queries"]:
        actual = _run_query(graph, item)
        passed = actual == item["expected"]
        per_query.append(
            {"id": item["id"], "passed": passed, "expected": item["expected"], "actual": actual}
        )
    passed_count = sum(1 for q in per_query if q["passed"])
    return {
        "name": "graph",
        "queries": len(per_query),
        "passed": passed_count,
        "exact_match": round(passed_count / len(per_query), 4),
        "per_query": per_query,
    }

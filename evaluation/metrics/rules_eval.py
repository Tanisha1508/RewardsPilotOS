"""Rules golden set runner: exact match on hand-computed values, target 100%."""

import json
from pathlib import Path

from rules.engine.cap_store import InMemoryCapUsageStore
from rules.engine.engine import RuleEngine

DATASET = Path(__file__).resolve().parent.parent / "datasets" / "rules.json"
EVAL_SEED_DIR = Path(__file__).resolve().parent.parent / "datasets" / "fixtures" / "rules_seed"


def _engine_for(scenario: dict) -> RuleEngine:
    store = InMemoryCapUsageStore()
    accrued = scenario.get("accrued")
    if accrued:
        card = scenario.get("card_key") or scenario["cards"][0]
        store.record(
            card, accrued["scope"], accrued.get("month", scenario["month"]), accrued["amount"]
        )
    seed_dir = EVAL_SEED_DIR if scenario["seed"] == "eval" else None
    return RuleEngine(cap_store=store, seed_dir=seed_dir)


def _run_scenario(scenario: dict) -> dict:
    engine = _engine_for(scenario)
    if scenario["type"] == "calculate_earn":
        result = engine.calculate_earn(
            scenario["card_key"],
            scenario["amount"],
            scenario["category"],
            scenario["channel"],
            scenario["month"],
        )
        return {
            "status": result.status,
            "points": result.points,
            "applied": result.applied,
            "cap_applied": result.cap_applied,
        }
    if scenario["type"] == "check_cap":
        status = engine.check_cap(scenario["card_key"], scenario["cap_scope"], scenario["month"])
        return {
            "status": status.status,
            "accrued_points": status.accrued_points,
            "remaining_points": status.remaining_points,
        }
    if scenario["type"] == "compare_cards":
        results = engine.compare_cards(
            scenario["cards"],
            scenario["amount"],
            scenario["category"],
            scenario["channel"],
            scenario["month"],
        )
        return {
            "statuses": [r.status for r in results],
            "points": [r.points for r in results],
        }
    raise ValueError(f"unknown scenario type {scenario['type']}")


def run() -> dict:
    dataset = json.loads(DATASET.read_text())
    per_scenario = []
    for scenario in dataset["scenarios"]:
        actual = _run_scenario(scenario)
        passed = actual == scenario["expected"]
        per_scenario.append(
            {
                "id": scenario["id"],
                "passed": passed,
                "expected": scenario["expected"],
                "actual": actual,
            }
        )
    passed_count = sum(1 for s in per_scenario if s["passed"])
    return {
        "name": "rules",
        "scenarios": len(per_scenario),
        "passed": passed_count,
        "exact_match": round(passed_count / len(per_scenario), 4),
        "per_scenario": per_scenario,
    }

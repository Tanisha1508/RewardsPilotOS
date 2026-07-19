"""End-to-end golden set runner (BUILD_SPEC §11).

Each query runs through the full LangGraph workflow. A deterministic eval LLM
plays the Planner (emitting the golden plan, still schema-validated by the
Planner node) and the Recommender (assembling contract-exact output from the
state digest, numbers verbatim). Checks per query:

- recommendation produced (contract-valid)
- citations present
- calculations verbatim from tool results (no invented values)
- numbers in prose traceable to tool outputs / retrieved content (string match)
- confidence reported
- unknowns stated plainly when expected
"""

import json
import re
from pathlib import Path

from agents.state.schema import initial_state
from agents.workflows.graph import build_workflow

DATASET = Path(__file__).resolve().parent.parent / "datasets" / "recommendations.json"

_NUMBER_RE = re.compile(r"\d[\d,]{1,}(?:\.\d+)?")  # 2+ digit numbers in prose


class EvalLLM:
    """Deterministic LLM for eval runs: planner returns the golden plan;
    recommender assembles output obeying the hard rules."""

    def __init__(self, intent: str, plan: list[dict]) -> None:
        self._intent = intent
        self._plan = plan

    def complete(self, system: str, user: str) -> str:
        if "Planner prompt" in system:
            return json.dumps({"intent": self._intent, "plan": self._plan})
        state = json.loads(user.split("\n\nYour previous output was rejected")[0])
        calculations = list(state["rule_results"]) + list(state["graph_results"])
        citations = []
        seen = set()
        for chunk in state["knowledge"]:
            key = (chunk["metadata"]["source_url"], chunk["metadata"]["last_changed"])
            if key in seen:
                continue
            seen.add(key)
            citations.append(
                {
                    "source_url": key[0],
                    "last_changed": key[1],
                    "doc_id": chunk["metadata"]["doc_id"],
                }
            )
        unknowns = [
            entry
            for entry in calculations
            if entry.get("status") == "unknown"
            or entry.get("unverified_paths_exist")
            or (entry.get("paths") == [] and entry.get("tool") == "BestTransferPaths")
        ]
        has_computed = any(
            entry.get("status") == "computed" or entry.get("paths") for entry in calculations
        )
        if unknowns and not has_computed:
            level, reason = "low", "all required values are unknown pending verification"
        elif unknowns:
            level, reason = "medium", "some values verified, others unknown pending verification"
        elif has_computed:
            level, reason = "high", "all values verified and computed deterministically"
        else:
            level, reason = "low", "no deterministic computations were required"
        decision = "Deterministic tool results attached; see calculations."
        if unknowns:
            decision += (
                " Some required values are UNKNOWN pending issuer verification; "
                "the system refuses to guess (unknown over incorrect)."
            )
        return json.dumps(
            {
                "decision": decision,
                "reasoning": [
                    "Numbers are copied verbatim from rule_results and graph_results.",
                    "Citations carry source URLs and freshness timestamps from retrieval.",
                ],
                "calculations": calculations,
                "citations": citations,
                "confidence": {"level": level, "reason": reason},
                "assumptions": ["Fixture data is current as of its recorded timestamps."],
                "alternatives": [],
            }
        )


def _numbers_traceable(recommendation: dict, state: dict) -> bool:
    allowed_text = json.dumps(
        {
            "rule_results": state["rule_results"],
            "graph_results": state["graph_results"],
            "portfolio": state["portfolio"],
            "memory": state["memory"],
            "knowledge": [c.model_dump() if hasattr(c, "model_dump") else c
                          for c in state["knowledge"]],
        },
        default=str,
    )
    prose = " ".join(
        [recommendation["decision"]]
        + recommendation["reasoning"]
        + recommendation["assumptions"]
        + recommendation["alternatives"]
    )
    for token in _NUMBER_RE.findall(prose):
        if token.replace(",", "") not in allowed_text and token not in allowed_text:
            return False
    return True


def run() -> dict:
    dataset = json.loads(DATASET.read_text())
    per_query = []
    for item in dataset["queries"]:
        workflow = build_workflow(EvalLLM(item["intent"], item["plan"]))
        final = workflow.invoke(initial_state(item["query"], "fixture_user"))
        recommendation = final["recommendation"]
        checks = {"recommendation_produced": recommendation is not None}
        if recommendation is not None:
            allowed = final["rule_results"] + final["graph_results"]
            checks["citations_present"] = len(recommendation["citations"]) > 0
            checks["calculations_verbatim"] = all(
                entry in allowed for entry in recommendation["calculations"]
            )
            checks["numbers_traceable"] = _numbers_traceable(recommendation, final)
            checks["confidence_reported"] = recommendation["confidence"]["level"] in (
                "high",
                "medium",
                "low",
            ) and bool(recommendation["confidence"]["reason"])
            if item.get("expect_unknown"):
                checks["unknown_stated"] = "unknown" in recommendation["decision"].lower()
        per_query.append(
            {"id": item["id"], "passed": all(checks.values()), "checks": checks}
        )
    passed_count = sum(1 for q in per_query if q["passed"])
    return {
        "name": "end_to_end",
        "queries": len(per_query),
        "passed": passed_count,
        "pass_rate": round(passed_count / len(per_query), 4),
        "per_query": per_query,
    }

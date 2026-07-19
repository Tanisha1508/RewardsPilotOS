"""Deterministic LLM fakes for agent tests."""

import json


class PayloadLLM:
    """Returns fixed payloads: first planner payload, then recommender
    payloads in sequence (for retry testing)."""

    def __init__(self, planner_payload=None, recommender_payloads=None):
        self.planner_payload = planner_payload or {"intent": "general", "plan": []}
        self.recommender_payloads = list(recommender_payloads or [])
        self.recommender_calls = 0

    def complete(self, system: str, user: str) -> str:
        if "Planner prompt" in system:
            return json.dumps(self.planner_payload)
        index = min(self.recommender_calls, len(self.recommender_payloads) - 1)
        self.recommender_calls += 1
        payload = self.recommender_payloads[index]
        return payload if isinstance(payload, str) else json.dumps(payload)


class BrokenLLM:
    def __init__(self):
        self.calls = 0

    def complete(self, system: str, user: str) -> str:
        self.calls += 1
        raise RuntimeError("simulated LLM outage")


def valid_recommendation(calculations=None, citations=None):
    return {
        "decision": "test decision",
        "reasoning": ["step"],
        "calculations": calculations or [],
        "citations": citations or [],
        "confidence": {"level": "low", "reason": "test"},
        "assumptions": [],
        "alternatives": [],
    }

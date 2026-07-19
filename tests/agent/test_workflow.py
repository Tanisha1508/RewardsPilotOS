"""End-to-end LangGraph workflow on fixture data with the scripted LLM."""

import pytest

from agents.state.schema import initial_state
from agents.workflows.demo import DEMO_QUERY, ScriptedLLM
from agents.workflows.graph import build_workflow, run_tools
from contracts.api.recommendation import Recommendation
from tests.agent.fakes import PayloadLLM, valid_recommendation


@pytest.fixture(scope="module")
def demo_final_state():
    workflow = build_workflow(ScriptedLLM())
    return workflow.invoke(initial_state(DEMO_QUERY, "fixture_user"))


def test_workflow_produces_contract_valid_recommendation(demo_final_state):
    recommendation = Recommendation.model_validate(demo_final_state["recommendation"])
    assert recommendation.decision
    assert recommendation.calculations
    assert recommendation.citations
    assert recommendation.confidence.level in ("high", "medium", "low")


def test_numbers_are_verbatim_tool_outputs(demo_final_state):
    allowed = demo_final_state["rule_results"] + demo_final_state["graph_results"]
    for entry in demo_final_state["recommendation"]["calculations"]:
        assert entry in allowed


def test_unknowns_stated_plainly(demo_final_state):
    text = demo_final_state["recommendation"]["decision"].lower()
    assert "unknown" in text  # HDFC path is unverified, must be said plainly


def test_state_channels_populated(demo_final_state):
    assert demo_final_state["intent"] == "transfer"
    assert demo_final_state["portfolio"] is not None
    assert demo_final_state["graph_results"]
    assert demo_final_state["knowledge"]
    assert demo_final_state["preferences"]
    assert demo_final_state["memory"]["episodic"]


def test_citations_carry_freshness(demo_final_state):
    for citation in demo_final_state["citations"]:
        assert citation.source_url.startswith("https://")
        assert citation.last_changed


def test_graceful_degradation_on_failing_tool():
    state = initial_state("q", "fixture_user")
    state["plan"] = [
        {"tool": "CheckCap", "args": {"card_key": "ghost", "cap_scope": "s", "month": "2026-07"}},
        {"tool": "GetCards", "args": {"user_id": "fixture_user"}},
    ]
    state = run_tools(state)
    assert any("CheckCap" in error for error in state["errors"])
    assert state["portfolio"]["cards"]  # later tool still executed


def test_empty_plan_routes_straight_to_recommender():
    llm = PayloadLLM(
        planner_payload={"intent": "general", "plan": []},
        recommender_payloads=[valid_recommendation()],
    )
    final = build_workflow(llm).invoke(initial_state("hello", "u"))
    assert final["recommendation"]["decision"] == "test decision"
    assert final["rule_results"] == []

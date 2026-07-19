"""Planner: typed ToolInvocation plans only, schema validation, retry."""

from agents.planner.planner import plan, tool_catalog, validate_plan
from agents.state.schema import initial_state
from tests.agent.fakes import BrokenLLM, PayloadLLM


def test_valid_plan_accepted():
    llm = PayloadLLM(
        planner_payload={
            "intent": "spend",
            "plan": [
                {"tool": "GetCards", "args": {"user_id": "fixture_user"}},
                {
                    "tool": "CalculateEarn",
                    "args": {
                        "card_key": "hdfc_infinia",
                        "amount": 70000,
                        "category": "electronics",
                        "month": "2026-07",
                    },
                },
            ],
        }
    )
    state = plan(initial_state("q", "fixture_user"), llm)
    assert state["intent"] == "spend"
    assert [p["tool"] for p in state["plan"]] == ["GetCards", "CalculateEarn"]
    assert state["errors"] == []


def test_unknown_tool_rejected():
    errors: list[str] = []
    result = validate_plan([{"tool": "HackTheBank", "args": {}}], errors)
    assert result == []
    assert "unknown tool" in errors[0]


def test_malformed_args_rejected():
    errors: list[str] = []
    result = validate_plan(
        [{"tool": "CalculateEarn", "args": {"card_key": "x"}}], errors
    )
    assert result == []
    assert "invalid args" in errors[0]


def test_free_form_string_rejected():
    errors: list[str] = []
    result = validate_plan(["just call the rule engine please"], errors)
    assert result == []
    assert "malformed plan entry" in errors[0]


def test_non_dict_args_rejected():
    errors: list[str] = []
    result = validate_plan([{"tool": "GetCards", "args": "user"}], errors)
    assert result == []
    assert "non-dict args" in errors[0]


def test_invalid_intent_defaults_to_general():
    llm = PayloadLLM(planner_payload={"intent": "world_domination", "plan": []})
    state = plan(initial_state("q", "u"), llm)
    assert state["intent"] == "general"


def test_llm_outage_degrades_to_empty_plan_with_retry():
    llm = BrokenLLM()
    state = plan(initial_state("q", "u"), llm)
    assert llm.calls == 2  # 1 retry with backoff
    assert state["plan"] == []
    assert any("planner:" in error for error in state["errors"])


def test_tool_catalog_lists_all_tools():
    catalog = tool_catalog()
    assert "CalculateEarn" in catalog
    assert "GetOpportunities" in catalog

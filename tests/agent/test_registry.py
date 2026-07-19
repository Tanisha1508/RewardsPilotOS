"""Tool Registry: full tool set, schema validation, structured failure."""

import pytest

from tools.registry import REGISTRY, ToolInputError, execute, get_tool, validate_args

EXPECTED_TOOLS = {
    "GetPortfolio",
    "GetCards",
    "GetRewardBalances",
    "GetTravelGoals",
    "SearchKnowledge",
    "GetPromotions",
    "GetTransferRatios",
    "CalculateEarn",
    "CheckCap",
    "CompareCards",
    "BestTransferPaths",
    "RedemptionOptions",
    "RecallMemory",
    "StorePreference",
    "GetOpportunities",
}


def test_full_tool_set_registered():
    assert set(REGISTRY) == EXPECTED_TOOLS


def test_every_tool_declares_contract_schemas():
    for spec in REGISTRY.values():
        assert spec.description
        assert spec.timeout_s > 0
        assert spec.input_model.model_json_schema()
        assert spec.output_model.model_json_schema()


def test_validate_args_rejects_malformed():
    with pytest.raises(ToolInputError):
        validate_args("CalculateEarn", {"card_key": "x"})  # missing required fields
    with pytest.raises(ToolInputError):
        validate_args("CalculateEarn", {
            "card_key": "x", "amount": -5, "category": "c", "month": "2026-07",
        })


def test_execute_unknown_tool_returns_structured_failure():
    result = execute("NoSuchTool", {})
    assert result.status == "failed"
    assert "unknown tool" in result.error


def test_execute_invalid_args_returns_structured_failure():
    result = execute("CheckCap", {"card_key": "hdfc_infinia"})
    assert result.status == "failed"
    assert "invalid args" in result.error


def test_execute_handler_exception_is_structured():
    # unknown card raises RuleNotFoundError inside the handler
    result = execute(
        "CheckCap", {"card_key": "ghost_card", "cap_scope": "s", "month": "2026-07"}
    )
    assert result.status == "failed"
    assert "RuleNotFoundError" in result.error


def test_execute_success_envelope():
    result = execute("GetCards", {"user_id": "fixture_user"})
    assert result.status == "success"
    assert result.error is None
    assert result.latency_ms >= 0
    assert result.result["cards"]


def test_rule_tool_refuses_unverified_seed_values():
    result = execute(
        "CalculateEarn",
        {"card_key": "hdfc_infinia", "amount": 70000, "category": "electronics",
         "month": "2026-07"},
    )
    assert result.status == "success"
    assert result.result["status"] == "unknown"
    assert result.result["points"] is None


def test_transfer_ratio_tool_exposes_verified_and_unverified():
    verified = execute("GetTransferRatios", {"currency": "voyager_points"})
    assert verified.result["ratios"]
    real = execute("GetTransferRatios", {"currency": "hdfc_reward_points"})
    assert real.result["ratios"] == []
    assert real.result["unverified_partners"]
    assert all("unverified" in p for p in real.result["unverified_partners"])


def test_get_tool_and_spec_lookup():
    spec = get_tool("RedemptionOptions")
    assert spec.category == "graph"

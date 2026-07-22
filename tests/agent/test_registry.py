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
        validate_args(
            "CalculateEarn",
            {
                "card_key": "x",
                "amount": -5,
                "category": "c",
                "month": "2026-07",
            },
        )


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
    result = execute("CheckCap", {"card_key": "ghost_card", "cap_scope": "s", "month": "2026-07"})
    assert result.status == "failed"
    assert "RuleNotFoundError" in result.error


def test_execute_success_envelope():
    result = execute("GetCards", {})
    assert result.status == "success"
    assert result.error is None
    assert result.latency_ms >= 0
    assert result.result["cards"]


def test_rule_tool_computes_verified_cards_and_refuses_unverified_amex():
    hdfc = execute(
        "CalculateEarn",
        {
            "card_key": "hdfc_infinia",
            "amount": 70000,
            "category": "electronics",
            "month": "2026-07",
        },
    )
    assert hdfc.status == "success"
    assert hdfc.result["status"] == "computed"
    assert hdfc.result["points"] == 2330.0  # floor(70000/150)=466 blocks * 5
    axis = execute(
        "CalculateEarn",
        {"card_key": "axis_atlas", "amount": 70000, "category": "electronics", "month": "2026-07"},
    )
    assert axis.result["status"] == "computed"  # verified 2026-07-19
    assert axis.result["points"] == 1400.0  # floor(70000/100)=700 blocks * 2
    amex = execute(
        "CalculateEarn",
        {
            "card_key": "amex_plat_travel",
            "amount": 70000,
            "category": "electronics",
            "month": "2026-07",
        },
    )
    assert amex.result["status"] == "computed"  # verified 2026-07-20
    assert amex.result["points"] == 1400.0  # floor(70000/50)=1400 blocks * 1
    regalia = execute(
        "CalculateEarn",
        {
            "card_key": "hdfc_regalia",
            "amount": 70000,
            "category": "electronics",
            "month": "2026-07",
        },
    )
    assert regalia.result["status"] == "unknown"  # P2 scope, unverified
    assert regalia.result["points"] is None


def test_transfer_ratio_tool_exposes_verified_and_unverified():
    synthetic = execute("GetTransferRatios", {"currency": "voyager_points"})
    assert synthetic.result["ratios"]
    hdfc = execute("GetTransferRatios", {"currency": "hdfc_reward_points"})
    verified_targets = {r["to_program"] for r in hdfc.result["ratios"]}
    assert verified_targets == {
        "turkish_miles",
        "accor",
        "avianca_lifemiles",
        "club_itc_green_points",
        "singapore_krisflyer",
        "marriott_bonvoy",
        "air_india_flying_returns",
    }
    assert hdfc.result["unverified_partners"] == []  # card fully verified
    axis = execute("GetTransferRatios", {"currency": "edge_miles"})
    assert len(axis.result["ratios"]) == 17  # Group A (14) + Group B (3)
    assert axis.result["unverified_partners"] == []  # Atlas verified 2026-07-19
    amex = execute("GetTransferRatios", {"currency": "membership_rewards"})
    assert len(amex.result["ratios"]) == 8  # 6 airlines + Marriott + Hilton
    assert amex.result["unverified_partners"] == []  # P1 fully verified


def test_get_tool_and_spec_lookup():
    spec = get_tool("RedemptionOptions")
    assert spec.category == "graph"

"""Deterministic confidence calibration (agents/recommendation/calibration).

Confidence must track the evidence: a recommendation resting on a 0.7-source
value cannot read the same as one resting on an official PDF at 0.95.
"""

from agents.recommendation.calibration import confidence_basis
from contracts.api.recommendation import exceeds_ceiling


def _verified(value, confidence, source="https://example.test/t&c"):
    return {"value": value, "status": "verified", "source": source, "confidence": confidence}


def _computed(rate_confidence, **extra):
    return {
        "tool": "CalculateEarn",
        "status": "computed",
        "points": 100.0,
        "rate": _verified(5, rate_confidence),
        **extra,
    }


def test_strong_sources_allow_high():
    basis = confidence_basis([_computed(0.95)], [])
    assert basis["ceiling"] == "high"
    assert basis["min_source_confidence"] == 0.95


def test_weak_source_caps_at_medium():
    """The d2 case: SmartBuy multiplier verified only from a general public
    page (0.7). Everything computes, but confidence must not read high."""
    basis = confidence_basis(
        [_computed(0.95, multiplier=_verified(5, 0.7, "SmartBuy public page"))], []
    )
    assert basis["ceiling"] == "medium"
    assert basis["min_source_confidence"] == 0.7
    assert "SmartBuy public page" in basis["weakest_source"]


def test_weakest_source_wins_not_the_average():
    basis = confidence_basis(
        [_computed(0.95, multiplier=_verified(5, 0.65), cap=_verified(1000, 0.9))], []
    )
    assert basis["ceiling"] == "medium"
    assert basis["min_source_confidence"] == 0.65


def test_unknown_present_caps_at_medium_even_with_strong_sources():
    unknown = {
        "tool": "CalculateEarn",
        "status": "unknown",
        "unknown_reasons": ["base earn rate is unverified"],
    }
    basis = confidence_basis([_computed(0.95), unknown], [])
    assert basis["ceiling"] == "medium"
    assert basis["has_unknowns"] is True


def test_nothing_computable_is_low():
    unknown = {
        "tool": "CalculateEarn",
        "status": "unknown",
        "unknown_reasons": ["base earn rate is unverified"],
    }
    basis = confidence_basis([unknown], [])
    assert basis["ceiling"] == "low"


def test_no_results_at_all_is_low():
    """The d4 case: a milestone question no tool can answer deterministically
    degrades to retrieval only — it must not read as a confident answer."""
    assert confidence_basis([], [])["ceiling"] == "low"


def test_tool_failure_caps_confidence():
    basis = confidence_basis([_computed(0.95)], [], tool_errors=["SearchKnowledge: boom"])
    assert basis["ceiling"] == "medium"


def test_unverified_graph_path_counts_as_unknown():
    graph = {
        "tool": "BestTransferPaths",
        "paths": [{"cumulative_ratio": 1.0}],
        "unverified_paths_exist": True,
    }
    assert confidence_basis([], [graph])["ceiling"] == "medium"


def test_exceeds_ceiling_ordering():
    assert exceeds_ceiling("high", "medium") is True
    assert exceeds_ceiling("medium", "medium") is False
    assert exceeds_ceiling("low", "high") is False

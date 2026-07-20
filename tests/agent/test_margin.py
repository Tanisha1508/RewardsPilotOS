"""Winning-margin sourcing reaches the answer (agents/recommendation/margin).

Ranking stays points-only — that is proved in
tests/rules/test_confidence_does_not_rank.py and is NOT relaxed here. What
this covers is the reporting obligation: when the winner's margin rests on a
thinly-sourced number and a lower-scoring card's number is better evidenced,
the response must name that specific number rather than averaging the risk
into a generic confidence label.
"""

import json

from agents.recommendation.margin import margin_caveat
from agents.recommendation.recommender import recommend
from agents.state.schema import initial_state
from contracts.tools.knowledge_search import ChunkMetadata, RetrievedChunk
from rules.engine.engine import RuleEngine
from tests.agent.fakes import PayloadLLM, valid_recommendation

CHUNK = RetrievedChunk(
    doc_id="doc1",
    chunk_index=0,
    content="text",
    score=0.5,
    metadata=ChunkMetadata(
        doc_id="doc1",
        issuer="hdfc",
        program="hdfc_reward_points",
        doc_type="reward_rules",
        source_url="https://example.test/doc1",
        last_changed="2026-06-15",
    ),
)
CITATION = [
    {
        "source_url": "https://example.test/doc1",
        "last_changed": "2026-06-15",
        "doc_id": "doc1",
    }
]


def hotel_comparison() -> list[dict]:
    """The ₹50,000 portal hotel booking across the three P1 cards, exactly as
    the workflow records it in state."""
    results = RuleEngine().compare_cards(
        ["hdfc_infinia", "axis_atlas", "amex_plat_travel"],
        50_000,
        "hotels",
        "issuer_portal",
        "2026-07",
    )
    return [{"tool": "CompareCards", **r.model_dump()} for r in results]


def test_thinly_sourced_winner_is_flagged():
    """Infinia wins on a 0.7-sourced SmartBuy multiplier while Amex and Atlas
    score lower on 0.95-sourced rates. The caveat must name Infinia's
    multiplier specifically."""
    caveat = margin_caveat(hotel_comparison())

    assert caveat is not None
    assert caveat["winner"] == "hdfc_infinia"
    assert caveat["winner_field"] == "accelerated multiplier"
    assert caveat["winner_field_value"] == 10
    assert caveat["winner_field_confidence"] == 0.7
    assert "SmartBuy" in caveat["winner_field_source"]

    # the counterexample is a real, better-sourced competing card
    assert caveat["comparator_field_confidence"] == 0.95
    assert caveat["comparator"] in ("amex_plat_travel", "axis_atlas")

    statement = caveat["statement"]
    assert "hdfc_infinia" in statement
    assert "accelerated multiplier" in statement
    assert "0.7" in statement
    assert "better evidenced" in statement


def test_evenly_sourced_comparison_produces_no_caveat():
    """No caveat when the winner is as well-sourced as its rivals — the
    mechanism must stay quiet rather than tagging every comparison."""
    results = RuleEngine().compare_cards(
        ["axis_atlas", "amex_plat_travel"], 50_000, "hotels", "issuer_portal", "2026-07"
    )
    rule_results = [{"tool": "CompareCards", **r.model_dump()} for r in results]
    assert margin_caveat(rule_results) is None


def test_single_card_result_produces_no_caveat():
    """A caveat needs something to compare against."""
    assert margin_caveat([]) is None
    single = RuleEngine().calculate_earn("hdfc_infinia", 50_000, "hotels", "smartbuy", "2026-07")
    assert margin_caveat([{"tool": "CompareCards", **single.model_dump()}]) is None


def _state_with_comparison():
    state = initial_state("Which card for a 50,000 rupee hotel booking?", "u")
    state["rule_results"] = hotel_comparison()
    state["knowledge"] = [CHUNK]
    return state


def test_recommendation_without_the_caveat_is_rejected():
    """The model cannot drop the caveat: a generic confidence label is not a
    substitute for naming the number the win depends on."""
    payload = valid_recommendation(citations=CITATION)
    payload["decision"] = "HDFC Infinia wins with 15000.0 points."
    payload["confidence"] = {"level": "medium", "reason": "some sources are thin"}
    state = recommend(_state_with_comparison(), PayloadLLM(recommender_payloads=[payload, payload]))

    assert state["recommendation"] is None
    assert any("required margin caveat missing" in error for error in state["errors"])


def test_paraphrasing_the_caveat_is_rejected():
    """Verbatim means verbatim — softening loses the specific number."""
    payload = valid_recommendation(citations=CITATION)
    payload["decision"] = "HDFC Infinia wins, though some of its data is less certain."
    state = recommend(_state_with_comparison(), PayloadLLM(recommender_payloads=[payload, payload]))
    assert state["recommendation"] is None


def test_recommendation_carrying_the_caveat_is_accepted():
    state = _state_with_comparison()
    caveat = margin_caveat(state["rule_results"])
    payload = valid_recommendation(citations=CITATION)
    payload["decision"] = "HDFC Infinia ranks first on points."
    payload["reasoning"] = [caveat["statement"]]
    payload["confidence"] = {"level": "medium", "reason": "weakest source 0.7"}

    state = recommend(state, PayloadLLM(recommender_payloads=[payload]))

    assert state["recommendation"] is not None
    reasoning = " ".join(state["recommendation"]["reasoning"])
    assert "accelerated multiplier" in reasoning
    assert "0.7" in reasoning


def test_caveat_reaches_the_state_digest():
    """The Recommender must actually be told about it, or it can never
    comply."""
    captured = {}

    class CapturingLLM(PayloadLLM):
        def complete(self, system: str, user: str) -> str:
            if "Planner prompt" not in system:
                captured["digest"] = json.loads(
                    user.split("\n\nYour previous output was rejected")[0]
                )
            return super().complete(system, user)

    state = _state_with_comparison()
    payload = valid_recommendation(citations=CITATION)
    recommend(state, CapturingLLM(recommender_payloads=[payload, payload]))

    assert captured["digest"]["margin_caveat"]["winner"] == "hdfc_infinia"
    assert captured["digest"]["margin_caveat"]["winner_field_confidence"] == 0.7

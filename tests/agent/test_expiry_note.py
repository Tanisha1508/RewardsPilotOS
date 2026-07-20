"""A lapsed accelerated rate must reach the answer (ADR-012).

The engine falling back to base earn is only half the fix. If the Recommender
can drop the reason, the user sees a card that quietly got worse with no
explanation — which is the same failure the winning-margin caveat was written
to prevent, and the same reason it is validated rather than merely prompted.
A prompt instruction is not a guarantee.
"""

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
        issuer="amex",
        program="amex_membership_rewards",
        doc_type="reward_rules",
        source_url="https://example.test/doc1",
        last_changed="2026-06-15",
    ),
)
CITATION = [
    {"source_url": "https://example.test/doc1", "last_changed": "2026-06-15", "doc_id": "doc1"}
]


def _state_after_expiry():
    """Amex portal spend dated after the Reward Multiplier's 2026-07-31 end."""
    result = RuleEngine().calculate_earn(
        "amex_plat_travel", 50_000, "hotels", "reward_multiplier", "2026-08"
    )
    state = initial_state("How much do I earn on a 50,000 rupee hotel booking?", "u")
    state["rule_results"] = [{"tool": "CalculateEarn", **result.model_dump()}]
    state["knowledge"] = [CHUNK]
    return state, result.expiry_note


def test_dropping_the_expiry_note_is_rejected():
    """Reporting the lower number without the reason is not acceptable."""
    state, _ = _state_after_expiry()
    payload = valid_recommendation(citations=CITATION)
    payload["decision"] = "You earn 1000.0 points on this booking."

    state = recommend(state, PayloadLLM(recommender_payloads=[payload, payload]))

    assert state["recommendation"] is None
    assert any("required statement missing" in error for error in state["errors"])


def test_paraphrasing_the_expiry_note_is_rejected():
    """Softening loses the expiry date, which is the actionable part."""
    state, _ = _state_after_expiry()
    payload = valid_recommendation(citations=CITATION)
    payload["decision"] = "You earn 1000.0 points; some rates may be out of date."

    state = recommend(state, PayloadLLM(recommender_payloads=[payload, payload]))
    assert state["recommendation"] is None


def test_carrying_the_expiry_note_is_accepted_and_caps_confidence():
    state, note = _state_after_expiry()
    payload = valid_recommendation(citations=CITATION)
    payload["decision"] = "You earn 1000.0 points on this booking."
    payload["reasoning"] = [note]
    payload["confidence"] = {"level": "medium", "reason": "an accelerated rate has lapsed"}

    state = recommend(state, PayloadLLM(recommender_payloads=[payload]))

    assert state["recommendation"] is not None
    reasoning = " ".join(state["recommendation"]["reasoning"])
    assert "2026-07-31" in reasoning
    assert "re-verify" in reasoning
    assert state["confidence"] == "medium"


def test_claiming_high_confidence_on_a_lapsed_rate_is_rejected():
    """The ceiling drops to medium even though every source is verified and
    the arithmetic is clean — the number may understate the card."""
    state, note = _state_after_expiry()
    payload = valid_recommendation(citations=CITATION)
    payload["decision"] = "You earn 1000.0 points on this booking."
    payload["reasoning"] = [note]
    payload["confidence"] = {"level": "high", "reason": "all values verified"}

    state = recommend(state, PayloadLLM(recommender_payloads=[payload, payload]))

    assert state["recommendation"] is None
    assert any("exceeds what the" in error for error in state["errors"])


def test_expiry_note_survives_a_month_where_the_rate_still_applies():
    """No note, nothing required — the mechanism must stay quiet in July."""
    result = RuleEngine().calculate_earn(
        "amex_plat_travel", 50_000, "hotels", "reward_multiplier", "2026-07"
    )
    state = initial_state("How much do I earn?", "u")
    state["rule_results"] = [{"tool": "CalculateEarn", **result.model_dump()}]
    state["knowledge"] = [CHUNK]

    payload = valid_recommendation(citations=CITATION)
    payload["decision"] = "You earn 3000.0 points on this booking."

    state = recommend(state, PayloadLLM(recommender_payloads=[payload]))
    assert state["recommendation"] is not None

"""An unstated booking channel must reach the answer (found live 2026-07-28).

The engine emitting `channel_note` is only half the fix, for the same reason
ADR-012's expiry note is validated rather than merely prompted: a model asked
to mention an inconvenient caveat will often decline. Here the caveat is the
difference between "HDFC Infinia is your best card" and "HDFC Infinia is your
best card unless you book direct, in which case Axis Atlas earns 2500" — so it
is enforced, not requested.
"""

from agents.recommendation.calibration import confidence_basis
from agents.recommendation.recommender import recommend
from agents.state.schema import initial_state
from contracts.tools.knowledge_search import ChunkMetadata, RetrievedChunk
from rules.engine.engine import RuleEngine
from tests.agent.fakes import PayloadLLM, valid_recommendation

CARDS = ["hdfc_infinia", "axis_atlas", "amex_plat_travel"]

CHUNK = RetrievedChunk(
    doc_id="doc1",
    chunk_index=0,
    content="text",
    score=0.5,
    metadata=ChunkMetadata(
        doc_id="doc1",
        issuer="axis",
        program="edge_miles",
        doc_type="reward_rules",
        source_url="https://example.test/doc1",
        last_changed="2026-06-15",
    ),
)
CITATION = [
    {"source_url": "https://example.test/doc1", "last_changed": "2026-06-15", "doc_id": "doc1"}
]


def _channel_less_state():
    """The live query: a flight comparison with no channel named."""
    results = RuleEngine().compare_cards(CARDS, 50_000, "flights", None, "2026-07")
    state = initial_state("Which of my cards is best for a Rs 50,000 flight booking?", "u")
    state["rule_results"] = [{"tool": "CompareCards", **r.model_dump()} for r in results]
    state["knowledge"] = [CHUNK]
    notes = [r.channel_note for r in results if r.channel_note]
    return state, notes


def test_dropping_the_channel_note_is_rejected():
    """This is the exact defect: a confident winner with the deciding question
    left unmentioned."""
    state, _ = _channel_less_state()
    payload = valid_recommendation(citations=CITATION)
    payload["decision"] = "HDFC Infinia is the best card, earning 1665.0 points."

    state = recommend(state, PayloadLLM(recommender_payloads=[payload, payload]))

    assert state["recommendation"] is None
    assert any("required statement missing" in error for error in state["errors"])


def test_claiming_high_confidence_without_a_channel_is_rejected():
    """Every source is verified and the arithmetic is clean, so nothing else
    caps the ceiling — but the ranking still turns on an unasked question."""
    state, notes = _channel_less_state()
    payload = valid_recommendation(citations=CITATION)
    payload["decision"] = "HDFC Infinia is the best card, earning 1665.0 points."
    payload["reasoning"] = notes
    payload["confidence"] = {"level": "high", "reason": "all values verified"}

    state = recommend(state, PayloadLLM(recommender_payloads=[payload, payload]))

    assert state["recommendation"] is None
    assert any("exceeds what the" in error for error in state["errors"])


def test_carrying_the_notes_is_accepted_and_caps_confidence_at_medium():
    state, notes = _channel_less_state()
    payload = valid_recommendation(citations=CITATION)
    payload["decision"] = "HDFC Infinia is the best card, earning 1665.0 points."
    payload["reasoning"] = notes
    payload["confidence"] = {"level": "medium", "reason": "no booking channel was given"}

    state = recommend(state, PayloadLLM(recommender_payloads=[payload]))

    assert state["recommendation"] is not None
    assert state["confidence"] == "medium"
    reasoning = " ".join(state["recommendation"]["reasoning"])
    # The user is told which channels would change the answer.
    assert "travel_edge" in reasoning
    assert "smartbuy" in reasoning


def test_calibration_ceiling_and_reason_name_the_channel():
    state, _ = _channel_less_state()
    basis = confidence_basis(state["rule_results"], [], [])

    assert basis["ceiling"] == "medium"
    assert "no booking channel was given" in basis["reason"]


def test_a_named_channel_leaves_the_mechanism_silent():
    """With the channel stated the answer is settled, so nothing is required
    and high confidence is available again."""
    results = RuleEngine().compare_cards(CARDS, 50_000, "flights", "direct", "2026-07")
    state = initial_state("Best card for a flight booked direct with the airline?", "u")
    state["rule_results"] = [{"tool": "CompareCards", **r.model_dump()} for r in results]
    state["knowledge"] = [CHUNK]

    assert confidence_basis(state["rule_results"], [], [])["ceiling"] == "high"

    payload = valid_recommendation(citations=CITATION)
    payload["decision"] = "Axis Bank Atlas is the best card, earning 2500.0 EDGE Miles."
    payload["confidence"] = {"level": "high", "reason": "all values verified"}

    state = recommend(state, PayloadLLM(recommender_payloads=[payload]))
    assert state["recommendation"] is not None

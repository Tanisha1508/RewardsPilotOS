"""Database ids must not reach the LLM provider (privacy audit P2, 2026-07-30).

The Planner is given only the query, with the user id deliberately withheld. The
Recommender undid that without anyone noticing: `GetPortfolioOutput` carries
`user_id`, the workflow puts the whole payload into `state["portfolio"]`, and the
digest was serialised straight to Gemini. Every recommendation request sent a
stable user UUID beside that user's cards, balances, preferences, past
interactions and question.

Tested at the digest boundary rather than on the helper alone: the helper being
correct proves nothing if a future edit serialises the dict before calling it.
"""

import json

from agents.privacy import IDENTIFIER_KEYS, strip_identifiers
from agents.recommendation.recommender import _state_digest
from agents.state.schema import initial_state

# Shaped like real tool output: GetPortfolio's payload, a CompareCards row, and
# an episodic memory event — the three routes an id actually took.
PORTFOLIO = {
    "portfolio_id": "8f14e45f-ceea-467a-9a3f-1b2c3d4e5f60",
    "user_id": "1afcccdd-e684-437f-897b-7df0bd8774aa",
    "portfolio_name": "Primary",
    "cards": [
        {
            "card_id": "abe6a0f2-4378-40d7-b7b9-9adc85e6f001",
            "issuer": "axis",
            "card_name": "Axis Bank Atlas",
            "card_key": "axis_atlas",
            "reward_currency": "edge_miles",
            "annual_fee": 5000.0,
        }
    ],
    "balances": [
        {
            "balance_id": "dbf45b21-17bd-4d5d-ba0b-5d3a3ff47100",
            "card_id": "abe6a0f2-4378-40d7-b7b9-9adc85e6f001",
            "reward_currency": "edge_miles",
            "current_balance": 15000.0,
        }
    ],
}


def _digest_of(state) -> str:
    return _state_digest(state, {"ceiling": "high", "reason": "ok"}, None)


def _state_with_everything():
    state = initial_state("Which card for a flight?", "1afcccdd-e684-437f-897b-7df0bd8774aa")
    state["portfolio"] = PORTFOLIO
    state["rule_results"] = [
        {
            "tool": "CompareCards",
            "card_id": "abe6a0f2-4378-40d7-b7b9-9adc85e6f001",
            "card_key": "axis_atlas",
            "points": 2500.0,
        }
    ]
    state["memory"] = {
        "episodic": [
            {
                "event_id": "7c3a47bf-2f0f-4708-9d3b-13fab63ff155",
                "event_type": "recommendation_accepted",
                "payload": {"rec_id": "46af2359-5492-4cf2-87a6-8392c34a1100"},
            }
        ]
    }
    return state


def test_no_identifier_key_appears_in_the_digest():
    digest = _digest_of(_state_with_everything())

    for key in IDENTIFIER_KEYS:
        assert f'"{key}"' not in digest, f"{key} reached the provider payload"


def test_no_identifier_VALUE_appears_either():
    """Stronger than checking key names: a uuid could survive as a bare value in
    a list, or under a key this module has not thought of."""
    digest = _digest_of(_state_with_everything())

    for uuid_value in (
        "1afcccdd-e684-437f-897b-7df0bd8774aa",  # user_id
        "8f14e45f-ceea-467a-9a3f-1b2c3d4e5f60",  # portfolio_id
        "abe6a0f2-4378-40d7-b7b9-9adc85e6f001",  # card_id
        "dbf45b21-17bd-4d5d-ba0b-5d3a3ff47100",  # balance_id
        "7c3a47bf-2f0f-4708-9d3b-13fab63ff155",  # event_id
        "46af2359-5492-4cf2-87a6-8392c34a1100",  # rec_id, nested two deep
    ):
        assert uuid_value not in digest, f"{uuid_value} reached the provider payload"


def test_everything_the_model_reasons_with_survives():
    """The point is removal of ids, not of meaning. If this fails, answers change."""
    digest = json.loads(_digest_of(_state_with_everything()))

    assert digest["query"] == "Which card for a flight?"
    card = digest["portfolio"]["cards"][0]
    assert card["card_key"] == "axis_atlas"
    assert card["card_name"] == "Axis Bank Atlas"
    assert card["reward_currency"] == "edge_miles"
    assert card["annual_fee"] == 5000.0
    assert digest["portfolio"]["balances"][0]["current_balance"] == 15000.0
    assert digest["rule_results"][0]["points"] == 2500.0
    assert digest["rule_results"][0]["card_key"] == "axis_atlas"
    # Episodic events keep their meaning, just not their row ids.
    assert digest["memory"]["episodic"][0]["event_type"] == "recommendation_accepted"


def test_card_key_is_not_stripped_despite_the_name():
    """`card_key` identifies a rule file, not a user. The engines and prompts
    depend on it, so a broader "anything ending in _key/_id" rule would break
    every comparison."""
    assert "card_key" not in IDENTIFIER_KEYS
    assert strip_identifiers({"card_key": "axis_atlas"}) == {"card_key": "axis_atlas"}


def test_structure_is_otherwise_untouched():
    """The Recommender copies numbers out of these results verbatim, so a
    reordering or coercion here would change an answer."""
    original = {
        "a": [1, 2, {"b": "keep", "card_id": "drop"}],
        "n": None,
        "f": 1665.0,
        "nested": {"deep": {"card_key": "hdfc_infinia", "user_id": "drop"}},
    }
    assert strip_identifiers(original) == {
        "a": [1, 2, {"b": "keep"}],
        "n": None,
        "f": 1665.0,
        "nested": {"deep": {"card_key": "hdfc_infinia"}},
    }

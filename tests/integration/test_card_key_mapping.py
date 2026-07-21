"""A real held card must map to the Rule Engine and produce a computed answer
(D4 regression, 2026-07-22).

This is the exact live-demo failure: a real HDFC Infinia in a Postgres portfolio
produced "unable to determine" because nothing linked it to the `hdfc_infinia`
rule file. The fix resolves `card_key` at card creation and the Planner injects
it into CompareCards. Locked in here so it cannot silently regress.

Uses a scripted LLM — the assertion is about the *wiring* (creation → card_key →
GetCards → injection → CompareCards computes), which must not depend on a live
model. If the mapping breaks, CompareCards has no cards, `rule_results` is empty,
and the recommender has nothing to compute — exactly the failure.
"""

import json

import pytest

from agents.state.schema import initial_state
from agents.workflows.graph import build_workflow
from backend.application import portfolio as portfolio_service
from backend.application.users import sync_user
from tools.portfolio.source import acting_as


class SpendLLM:
    """Planner asks to compare cards with an EMPTY `cards` list — exactly what
    the live Gemini did during D4, correctly declining to guess card_keys. The
    injection must fill them in before validation, or the whole CompareCards
    invocation is rejected (min_length=1) and the comparison is lost. The
    recommender echoes the computed figure."""

    def complete(self, system: str, user: str) -> str:
        if "Planner prompt" in system:
            return json.dumps(
                {
                    "intent": "spend",
                    "plan": [
                        {
                            "tool": "CompareCards",
                            "args": {
                                "cards": [],
                                "amount": 50000,
                                "category": "flights",
                                "month": "2026-07",
                            },
                        }
                    ],
                }
            )
        return json.dumps(
            {
                "decision": "HDFC Infinia earns the most on this flight spend.",
                "reasoning": ["Compared the cards you hold."],
                "calculations": [],
                "citations": [],
                "confidence": {"level": "medium", "reason": "computed from verified rules"},
                "assumptions": [],
                "alternatives": [],
            }
        )


@pytest.fixture()
def user_with_infinia(user_id):
    sync_user(user_id, "infinia@example.test", "Infinia Holder")
    card = portfolio_service.add_card(
        user_id,
        issuer="hdfc",
        card_name="HDFC Infinia",
        network="visa",
        reward_currency="hdfc_reward_points",
    )
    return user_id, card


def test_card_key_is_resolved_at_creation(user_with_infinia):
    _user_id, card = user_with_infinia
    # Resolved server-side from (issuer, card_name) — the client did not send it.
    assert card.card_key == "hdfc_infinia"


def test_real_infinia_card_produces_a_computed_comparison(user_with_infinia):
    user_id, _card = user_with_infinia
    workflow = build_workflow(SpendLLM())
    with acting_as(str(user_id)):
        final = workflow.invoke(initial_state("Best card for a 50,000 flight?", str(user_id)))

    # The mapping worked: CompareCards ran and computed for the held card.
    compare_results = [r for r in final["rule_results"] if r.get("tool") == "CompareCards"]
    assert compare_results, "CompareCards produced no results — card_key mapping failed"
    assert any(r.get("card_key") == "hdfc_infinia" for r in compare_results)
    assert any(r.get("status") == "computed" for r in compare_results)

    # And a recommendation was produced — not the empty-portfolio fallback, not
    # a failure.
    assert final["recommendation"] is not None
    assert "add a card" not in final["recommendation"]["decision"].lower()


def test_unknown_card_drops_the_comparison_rather_than_guessing(user_id):
    """A tracked card with no rule file has a null card_key; CompareCards is
    dropped rather than run on an invented key."""
    sync_user(user_id, "unknown@example.test", "Unknown Holder")
    card = portfolio_service.add_card(
        user_id,
        issuer="randombank",
        card_name="Mystery Rewards Card",
        network="rupay",
        reward_currency="mystery_points",
    )
    assert card.card_key is None

    workflow = build_workflow(SpendLLM())
    with acting_as(str(user_id)):
        final = workflow.invoke(initial_state("Best card for a flight?", str(user_id)))

    # No resolvable card → no CompareCards results (honest, not a guess).
    assert [r for r in final["rule_results"] if r.get("tool") == "CompareCards"] == []

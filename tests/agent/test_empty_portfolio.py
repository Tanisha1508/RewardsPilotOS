"""Empty-portfolio gate (D4).

A card-dependent question against zero cards must produce a plain "add a card"
response — deterministically, without running CompareCards or the LLM
recommender against an empty set. The whole point is that no tool and no
generation runs, so the answer cannot invent a card the user does not hold.
"""

import pytest

from agents.planner.empty_portfolio import (
    empty_portfolio_recommendation,
    held_cards,
)
from agents.state.schema import initial_state
from agents.workflows.graph import build_workflow
from contracts.api.recommendation import Confidence, Recommendation
from tools.portfolio.source import InMemoryPortfolioSource, load_seed
from tools.portfolio.source import set_source as set_portfolio_source

EMPTY_SEED = {
    "user_id": "empty_user",
    "portfolio_id": "p_empty",
    "portfolio_name": "Empty",
    "cards": [],
    "balances": [],
    "goals": [],
    "preferences": {},
    "episodic": [],
}


class ExplodingLLM:
    """Fails if called. The gate must never reach an LLM node for an empty
    card-dependent query — no planner-plan execution, no recommender."""

    def complete(self, system: str, user: str) -> str:  # pragma: no cover
        raise AssertionError("LLM must not be called on the empty-portfolio path")


class IntentOnlyLLM:
    """Classifies a card-dependent intent with no plan, like the real Planner
    would before the gate fires."""

    def __init__(self, intent: str):
        self._intent = intent

    def complete(self, system: str, user: str) -> str:
        return f'{{"intent": "{self._intent}", "plan": []}}'


@pytest.fixture(autouse=True)
def empty_portfolio_source():
    """Install an empty portfolio for these tests, then restore the session's
    demo source so later tests still see the fixture cards."""
    set_portfolio_source(InMemoryPortfolioSource(EMPTY_SEED))
    yield
    set_portfolio_source(InMemoryPortfolioSource(load_seed()))


def _install_empty():
    set_portfolio_source(InMemoryPortfolioSource(EMPTY_SEED))


def test_held_cards_empty_for_empty_portfolio():
    _install_empty()
    # No user argument: identity is ambient (KNOWN_LIMITATIONS 24, Class C).
    # The session-wide `acting_as` from tests/conftest.py supplies it.
    assert held_cards() == []


def test_empty_response_is_contract_valid():
    """It flows through the same persistence + envelope as any recommendation,
    so it must satisfy the Recommendation contract."""
    rec = Recommendation.model_validate(empty_portfolio_recommendation())
    assert isinstance(rec.confidence, Confidence)
    assert rec.calculations == [] and rec.citations == []
    assert "add a card" in rec.decision.lower()


def test_card_dependent_query_short_circuits_without_calling_tools_or_recommender():
    _install_empty()
    workflow = build_workflow(IntentOnlyLLM("spend"))
    state = workflow.invoke(initial_state("What's my best card for dining?", "empty_user"))

    assert state["recommendation"] is not None
    assert "add a card" in state["recommendation"]["decision"].lower()
    # No card logic ran.
    assert state["rule_results"] == []
    assert state["graph_results"] == []
    assert state["confidence"] == "high"


def test_planner_produced_response_never_reaches_the_recommender():
    """If the empty gate fired, the recommender LLM must not run — routing sends
    it straight to END."""
    _install_empty()
    # The planner classifies intent (IntentOnlyLLM), the gate fires, and the
    # recommender (which would be the *same* llm) must never be invoked. Use an
    # LLM that answers the planner call once, then explodes if called again.
    calls = {"n": 0}

    class OnceThenExplode:
        def complete(self, system, user):
            calls["n"] += 1
            if calls["n"] == 1:
                return '{"intent": "transfer", "plan": []}'
            raise AssertionError("recommender was called on the empty path")

    workflow = build_workflow(OnceThenExplode())
    state = workflow.invoke(initial_state("Transfer my points where?", "empty_user"))
    assert calls["n"] == 1  # planner only, never the recommender
    assert "add a card" in state["recommendation"]["decision"].lower()

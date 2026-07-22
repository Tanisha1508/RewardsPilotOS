"""Portfolio gating and card-key resolution for the Planner (D4).

Two deterministic things the Planner does with the user's held cards, both
before any LLM-driven recommendation logic:

1. **Empty-portfolio gate.** If a card-dependent query is asked against zero
   cards, short-circuit to a plain "add a card" response — the workflow routes
   straight to END. Nothing reaches CompareCards or the LLM recommender: there
   is nothing to compute, the answer is fixed not generated, and it cannot
   hallucinate a card the user does not hold.

2. **Card-key injection** — moved to `agents/planner/portfolio_args.py`, which
   generalises it beyond CompareCards to every tool taking a card argument.
   This module keeps the gate and the shared `held_cards` read.

Only card-dependent intents are gated. A cardless user asking a general
knowledge question ("how do transfer partners work?") is still answered from the
corpus.
"""

from contracts.tools.portfolio import Card, UserScopedInput
from tools.portfolio.tools import get_cards

# Intents whose answer is a computation over the user's own cards. "general" is
# informational and portfolio-independent, so it is deliberately not gated.
CARD_DEPENDENT_INTENTS = ("spend", "transfer", "redeem", "portfolio")


def held_cards() -> list[Card]:
    """The caller's cards, or [] if they have no portfolio at all. Fetched once
    so the empty-check and card-key resolution share a single read.

    Takes no user: identity comes from the ambient `acting_as` context, like
    every other tool that loads the caller's own data. A missing context raises
    UnknownUserError, which is caught below — the empty-portfolio gate then
    answers honestly rather than reading someone else's cards."""
    try:
        return get_cards(UserScopedInput()).cards
    except Exception:
        return []  # UnknownUserError etc. → no cards to reason about


def empty_portfolio_recommendation() -> dict:
    """A contract-valid Recommendation stating the portfolio is empty. No
    numbers in the prose (nothing to ground), no citations (nothing retrieved),
    confidence high because it rests on a fact — the portfolio is empty — not an
    estimate."""
    return {
        "decision": (
            "You don't have any cards on file yet, so there's nothing to compare "
            "or calculate against. Add a card to your portfolio and ask again — "
            "then I can compare earn rates, cap headroom, and transfer options "
            "across the cards you actually hold."
        ),
        "reasoning": [
            "Your portfolio is empty: no cards are recorded for your account.",
            "Reward recommendations compare the cards you hold, so there is "
            "nothing to compute until at least one card is added.",
        ],
        "calculations": [],
        "citations": [],
        "confidence": {
            "level": "high",
            "reason": "based directly on your portfolio being empty — a fact, not an estimate",
        },
        "assumptions": [],
        "alternatives": ["Add a card under Cards, then ask your question again."],
    }

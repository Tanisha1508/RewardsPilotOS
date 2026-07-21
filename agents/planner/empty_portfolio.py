"""Empty-portfolio gate (D4).

If the authenticated user has zero cards and the query needs their cards, the
Planner short-circuits to a plain, deterministic response — no cards on file,
add one — and the workflow routes straight to END. Nothing reaches CompareCards
or the LLM recommender: there is nothing to compute against an empty set, and
the honest answer is fixed, not generated (so it costs no tokens and cannot
hallucinate a card the user does not hold).

Only card-dependent intents are gated. A cardless user asking a general
knowledge question ("how do transfer partners work?") is still answered from the
corpus — the gate is about recommendation logic against an empty portfolio, not
about blocking every query.
"""

from contracts.tools.portfolio import UserScopedInput
from tools.portfolio.tools import get_cards

# Intents whose answer is a computation over the user's own cards. "general" is
# informational and portfolio-independent, so it is deliberately not gated.
CARD_DEPENDENT_INTENTS = ("spend", "transfer", "redeem", "portfolio")


def has_no_cards(user_id: str) -> bool:
    """True when the user holds zero cards. A user with no portfolio at all
    (never synced) also counts as empty — either way there is nothing to
    reason about."""
    try:
        return len(get_cards(UserScopedInput(user_id=user_id)).cards) == 0
    except Exception:
        # UnknownUserError (no portfolio row) → treat as empty. The gate's job is
        # "can we run card logic?", and the answer is no.
        return True


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

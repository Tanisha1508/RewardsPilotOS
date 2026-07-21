"""Portfolio gating and card-key resolution for the Planner (D4).

Two deterministic things the Planner does with the user's held cards, both
before any LLM-driven recommendation logic:

1. **Empty-portfolio gate.** If a card-dependent query is asked against zero
   cards, short-circuit to a plain "add a card" response — the workflow routes
   straight to END. Nothing reaches CompareCards or the LLM recommender: there
   is nothing to compute, the answer is fixed not generated, and it cannot
   hallucinate a card the user does not hold.

2. **Card-key injection.** CompareCards needs the Rule Engine card_keys of the
   held cards. The LLM cannot know those at plan time — they come from the
   portfolio, which is fetched by a tool that runs *after* planning. So the
   Planner fills them in deterministically from the held cards' `card_key`
   field, rather than letting the model guess a key from issuer/card_name
   (found during D4 live /chat testing: a real HDFC Infinia produced "unable to
   determine" because the model could not map it to `hdfc_infinia`).

Only card-dependent intents are gated. A cardless user asking a general
knowledge question ("how do transfer partners work?") is still answered from the
corpus.
"""

from contracts.tools.portfolio import Card, UserScopedInput
from tools.portfolio.tools import get_cards

# Intents whose answer is a computation over the user's own cards. "general" is
# informational and portfolio-independent, so it is deliberately not gated.
CARD_DEPENDENT_INTENTS = ("spend", "transfer", "redeem", "portfolio")


def held_cards(user_id: str) -> list[Card]:
    """The user's cards, or [] if they have no portfolio at all. Fetched once so
    the empty-check and card-key injection share a single read."""
    try:
        return get_cards(UserScopedInput(user_id=user_id)).cards
    except Exception:
        return []  # UnknownUserError etc. → no cards to reason about


def inject_card_keys(plan: list, cards: list[Card]) -> list:
    """Fill each CompareCards invocation with the held cards' resolved card_keys.

    Runs on the *raw* plan (before schema validation), because a model that
    correctly declines to guess keys leaves `cards` empty, which validation would
    reject. A card with no card_key (synthetic, or not in the verified catalogue)
    is omitted — it cannot be computed. If no held card resolves, a CompareCards
    invocation is dropped entirely: there is nothing to compare, and the
    recommender degrades honestly rather than comparing on invented keys.
    """
    keys = [card.card_key for card in cards if card.card_key]
    result = []
    for invocation in plan:
        if isinstance(invocation, dict) and invocation.get("tool") == "CompareCards":
            if not keys:
                continue
            invocation = {**invocation, "args": {**(invocation.get("args") or {}), "cards": keys}}
        result.append(invocation)
    return result


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

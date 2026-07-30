"""Strip identifiers before anything is sent to the LLM provider (privacy audit
P2, 2026-07-30).

The Planner is given only the query, with the user id deliberately withheld —
"handing it an identity it cannot legitimately use invites it back into plan
args" (`agents/planner/planner.py`). The Recommender then undid that: tool
results carry ids, and `GetPortfolioOutput` includes `user_id`, so every
recommendation request sent Google a stable user UUID alongside that user's
cards, balances, preferences, past interactions and question.

The identifiers buy nothing. No prompt asks the model to reason about a UUID,
and no output may contain one — recommendations quote `calculations` verbatim
from engine results, which are keyed by `card_key`, not `card_id`. So this is
pure removal, not a trade-off.

Applied to the whole digest rather than to `portfolio` alone, because the leak
was not really about portfolio: it was that *any* tool result can carry an id,
and a future tool would reintroduce the problem silently. Filtering by key name
at the boundary means new tools are covered by default.

`card_key` is deliberately NOT stripped despite the name: it is a rule-file
identifier ("hdfc_infinia"), not a user one, and the engines and prompts depend
on it.
"""

from typing import Any

# Keys removed anywhere they appear in the digest, at any depth.
#
# All are database surrogate keys: they identify a row, never a reward rule. If
# a value is needed for reasoning it has a human-meaningful field beside it
# (`card_name`, `reward_currency`, `card_key`), which is what the prompts and the
# engines actually use.
IDENTIFIER_KEYS = frozenset(
    {
        "user_id",
        "portfolio_id",
        "card_id",
        "balance_id",
        "rec_id",
        "event_id",
        "goal_id",
        "pref_id",
        "loyalty_id",
        "notif_id",
    }
)


def strip_identifiers(value: Any) -> Any:
    """Return `value` with every `IDENTIFIER_KEYS` entry removed, recursively.

    Structure is otherwise preserved exactly — this must not reorder, coerce or
    drop anything else, because the Recommender copies numbers out of these
    results verbatim and a changed shape would change an answer.
    """
    if isinstance(value, dict):
        return {
            key: strip_identifiers(inner)
            for key, inner in value.items()
            if key not in IDENTIFIER_KEYS
        }
    if isinstance(value, list):
        return [strip_identifiers(item) for item in value]
    return value

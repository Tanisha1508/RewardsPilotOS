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

import re
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


# Personal fields that are not identifiers but earn no place in the request
# either: nothing in `agents/`, `rules/` or `graph/` reads them (verified
# 2026-07-30 — the only consumers are the source adapter that populates them and
# the CRUD service that writes them).
#
#   `renewal_date`    a date specific to one person's account. Annual-fee
#                     reasoning uses `annual_fee_inr` from the verified rule
#                     file, which is public product data, not this row.
#   `portfolio_name`  user-authored free text, so it can contain a real name
#                     ("Tanisha's cards") while carrying no reasoning value.
#
# Kept deliberately: `last_updated` on a balance. It is a timestamp of user
# activity, but freshness is load-bearing in this product — an answer resting on
# a balance typed six months ago should be able to say so.
UNUSED_PERSONAL_KEYS = frozenset({"renewal_date", "portfolio_name"})

_REMOVED = "[removed]"

# Patterns scrubbed from user-authored free text. Every one of these is a
# contact or account identifier with no possible role in a rewards question, so
# removing it cannot change an answer — which is the bar, because corrupting
# input to protect it would trade this project's first rule for its third.
#
# What is deliberately NOT scrubbed: cities, dates, merchant names and amounts.
# They look like personal data and they are, but they are exactly what the
# question is about. Removing them would produce a confidently wrong answer,
# which is worse than the disclosure.
_SCRUB_PATTERNS = (
    # Email.
    re.compile(r"\b[\w.%+-]+@[\w.-]+\.[A-Za-z]{2,}\b"),
    # Payment card / bank account numbers: 13–19 digits, optionally spaced or
    # hyphenated. Comma-grouped amounts ("40,000") cannot match — the separator
    # class excludes commas — and no rupee figure in a card question runs to
    # thirteen digits.
    re.compile(r"\b\d(?:[ -]?\d){12,18}\b"),
    # Indian mobile numbers, with or without the country code.
    #
    # Three guards keep this off amounts, and all three are needed. The leading
    # `[6-9]` is the main one: Indian mobiles start 6–9, and a contiguous
    # ten-digit rupee figure starting with those digits is ₹60 crore or more,
    # which is not a transaction anyone asks a rewards app about. The lookbehind
    # stops a match beginning mid-number ("1,9876543210"), and `\b` stops one
    # inside a longer digit run.
    #
    # Comma-grouped amounts cannot match at all — "₹98,76,54,321" has no
    # contiguous ten-digit run. `test_amounts_are_never_scrubbed` is the
    # regression guard, and it is the more important of the two tests here: a
    # scrubbed amount would silently corrupt an answer, which costs more than
    # the disclosure this prevents.
    re.compile(r"(?<![\d,.])(?:\+?\s?91[\s-]?)?[6-9]\d{9}\b"),
)


def scrub_free_text(value: Any) -> Any:
    """Remove contact and account identifiers from user-authored strings.

    Applied only to the regions a person types into — the query, stored
    preferences, and remembered past queries. Never to `rule_results`,
    `graph_results` or retrieved knowledge: those carry the numbers a
    recommendation quotes verbatim, and a substitution there could silently
    change a figure. Engine output is machine-generated and contains no
    contact details to begin with, so there is nothing to gain and a
    correctness rule to lose.
    """
    if isinstance(value, str):
        for pattern in _SCRUB_PATTERNS:
            value = pattern.sub(_REMOVED, value)
        return value
    if isinstance(value, dict):
        return {key: scrub_free_text(inner) for key, inner in value.items()}
    if isinstance(value, list):
        return [scrub_free_text(item) for item in value]
    return value


def strip_identifiers(value: Any) -> Any:
    """Return `value` with every `IDENTIFIER_KEYS` and `UNUSED_PERSONAL_KEYS`
    entry removed, recursively.

    Structure is otherwise preserved exactly — this must not reorder, coerce or
    drop anything else, because the Recommender copies numbers out of these
    results verbatim and a changed shape would change an answer.
    """
    if isinstance(value, dict):
        return {
            key: strip_identifiers(inner)
            for key, inner in value.items()
            if key not in IDENTIFIER_KEYS and key not in UNUSED_PERSONAL_KEYS
        }
    if isinstance(value, list):
        return [strip_identifiers(item) for item in value]
    return value

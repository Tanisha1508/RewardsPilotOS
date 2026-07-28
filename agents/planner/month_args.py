"""Drop a `month` the user never asked for (found live 2026-07-28).

Companion to `portfolio_args.py`: that one fills in args the model correctly
declines to guess, this one removes an arg the model should have declined to
guess and did not.

The Planner prompt used to say "default to the current month if the user did
not specify one". A model has no reliable notion of today — no date is in its
prompt, and its training cutoff is not now — so it produced a plausible-looking
month instead. Observed live: `month: 2025-05` on a query asked 2026-07-28.

That is not cosmetic. Since ADR-012, `month` selects which accelerated programs
are in force, so an invented month silently turns rates on or off. Amex's
Reward Multiplier is valid to 2026-07-31; asked in 2026-08 with an invented
2025-05 the engine returns 3000 accelerated points instead of 1000 base, with
no expiry note and no drop in confidence — exactly the silently-wrong number
ADR-012 was written to prevent, reached by a different route.

The contract already has the right answer: absent `month` means "the current
month", resolved at the tool boundary (`tools/rule_engine/tools.py::_month`,
"the single boundary where now enters the Rule Engine"). So the fix is to omit
it, not to compute it here — adding a second source of "now" is what the tool
boundary exists to avoid.

Prompt rule 56 now says to omit it. This module is the guarantee, because a
prompt instruction is not one — the same conclusion ADR-012, ADR-019 and the
winning-margin caveat each reached independently.

**A month the user DID name is preserved.** "How much would I earn in August?"
is a real question, and the model parsing it from the query is legitimate work
— unlike inventing one from nothing. So a month survives exactly when the query
carries a period reference.
"""

import re

# A period reference in the user's own words. Deliberately generous: a false
# positive keeps a model-supplied month (status quo before this module), while
# a false negative would discard a month the user actually asked for, which is
# the worse error.
_PERIOD_PATTERNS = [
    r"\b\d{4}-\d{2}\b",  # 2026-08
    r"\b\d{1,2}/\d{4}\b",  # 8/2026
    r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)",  # month names/abbrevs
    r"\b(this|last|next|current|previous|coming)\s+(month|quarter|year)\b",
    r"\bmonth\b",  # "in that month", "per month", "monthly cap this month"
    r"\b(20\d{2})\b",  # a bare year
    r"\b(today|yesterday|tomorrow|now)\b",
    r"\b(so far|to date|year[- ]to[- ]date|ytd)\b",
]
_PERIOD_RE = re.compile("|".join(_PERIOD_PATTERNS), re.IGNORECASE)


def query_names_a_period(query: str) -> bool:
    """True when the user's words refer to a time period at all."""
    return bool(_PERIOD_RE.search(query or ""))


def strip_unrequested_month(plan: list, query: str, errors: list[str]) -> list:
    """Remove `month` from any invocation when the query names no period.

    Returns a new plan; entries without a `month` are passed through untouched.
    Each removal is recorded in `errors` — not because it is a failure, but
    because a silently-corrected plan is how this defect stayed invisible for a
    week. The record is what makes a recurrence visible.
    """
    if query_names_a_period(query):
        return plan

    cleaned = []
    for entry in plan:
        if not isinstance(entry, dict):
            cleaned.append(entry)
            continue
        args = entry.get("args")
        if not isinstance(args, dict) or args.get("month") is None:
            cleaned.append(entry)
            continue
        trimmed = {key: value for key, value in args.items() if key != "month"}
        errors.append(
            f"planner: dropped invented month {args['month']!r} from "
            f"{entry.get('tool')} — the query names no period, so the tool "
            f"boundary resolves the current month instead"
        )
        cleaned.append({**entry, "args": trimmed})
    return cleaned

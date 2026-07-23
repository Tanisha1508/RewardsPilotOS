"""Validity windows for accelerated-earn entries (ADR-012).

Accelerated programs are dated. Before this module, a program's start and end
dates lived only in `notes` prose, so the evaluator would keep applying a
lapsed multiplier until someone edited the rule file by hand — the one case
where the engine could compute with a rate it had no right to use, rather than
returning unknown (KNOWN_LIMITATIONS item 10, closed 2026-07-20).

Resolution is monthly because that is the resolution the engine works in:
`EarnResult` is keyed by `month` ("YYYY-MM"), not by transaction date. An entry
is active for a month when the window overlaps that month at all, so a program
ending 2026-07-31 still applies for all of 2026-07 and stops at 2026-08.

Lapsing is not the same as unverified. A lapsed entry means "this number was
true and its window has closed" — the engine falls back to base earn (which is
still verified) and attaches a note naming the expiry date and asking for
re-verification. Falling back to unknown would discard a base rate we do know.
"""

import calendar
from datetime import date

from rules.parser.models import AcceleratedEarn


def current_month() -> str:
    """The month the engine treats as "now", as "YYYY-MM".

    Lives here because this module already owns the engine's month resolution.
    Used to resolve an *absent* month at the tool boundary: most real queries
    ("which card for a ₹50,000 flight?") carry no period, and a required month
    the Planner has no basis to fill is an arg the LLM can only invent — which
    it cannot legitimately do, so the invocation was rejected and the
    computation silently lost (KNOWN_LIMITATIONS 24).

    Deliberately not a default on any engine or DTO field. A wrong month is not
    inert since ADR-012 — it selects which accelerated programs are in force —
    so "now" is resolved once, explicitly, at the boundary where the request
    enters, and never sits in a signature where it can be picked up silently.
    """
    return date.today().strftime("%Y-%m")


def _month_of(iso_date: str) -> str:
    return iso_date[:7]


def _month_bounds(month: str) -> tuple[str, str]:
    """First and last calendar day of `month` ("YYYY-MM") as ISO dates."""
    year, mon = int(month[:4]), int(month[5:7])
    last = calendar.monthrange(year, mon)[1]
    return f"{month}-01", f"{month}-{last:02d}"


def month_status(entry: AcceleratedEarn, month: str) -> str:
    """Whether `entry`'s validity window covers `month`: one of

    - "active"   — the window covers the WHOLE month, so the accelerated rate
                   cleanly applies to every day of it;
    - "inactive" — the window does not touch the month at all (ended before it
                   starts, or starts after it ends) → cleanly lapsed / not-yet;
    - "boundary" — the window starts or ends PARTWAY through the month, so the
                   month is only partly covered.

    The boundary case is the correctness fix (KNOWN_LIMITATIONS 10): the engine
    resolves earn at month granularity and has no intra-month split, so a
    `valid_until` of the 15th means part of the month earns the accelerated rate
    and part earns base. Applying the accelerated rate to the whole month
    over-credits (the wrong error direction); applying base under-credits.
    Neither is knowable, so the evaluator returns unknown for a boundary month
    rather than guessing — the same unknown-over-incorrect principle as ADR-012.
    Open-ended sides (None) are treated as covering that side unboundedly, so an
    entry with no dates is "active" every month, exactly as before.
    """
    first, last = _month_bounds(month)
    valid_from, valid_until = entry.valid_from, entry.valid_until
    if valid_until is not None and valid_until < first:
        return "inactive"
    if valid_from is not None and valid_from > last:
        return "inactive"
    starts_covered = valid_from is None or valid_from <= first
    ends_covered = valid_until is None or valid_until >= last
    return "active" if starts_covered and ends_covered else "boundary"


def is_active(entry: AcceleratedEarn, month: str) -> bool:
    """True only when the window covers the WHOLE `month` (see `month_status`).

    Narrowed from the original "overlaps at all": a window ending mid-month no
    longer counts as active, so the accelerated rate is not applied to a month
    it only partly covers."""
    return month_status(entry, month) == "active"


def boundary_note(entry: AcceleratedEarn, month: str) -> str | None:
    """Explain why a boundary month is unknown, or None if the month is not a
    boundary. Deterministic and dated verbatim from the rule file, so the
    Recommender can repeat it without inventing anything."""
    if month_status(entry, month) != "boundary":
        return None
    first, last = _month_bounds(month)
    valid_until, valid_from = entry.valid_until, entry.valid_from
    if valid_until is not None and first <= valid_until < last:
        edge = f"ends {valid_until}"
    else:
        edge = f"begins {valid_from}"
    return (
        f"the {entry.channel}/{entry.category} accelerated rate's validity {edge}, "
        f"partway through {month}; the engine resolves earn at month granularity and "
        f"cannot split the month, so the accelerated figure for {month} is unknown "
        f"rather than guessed. Re-check with a date-level calculation for this month."
    )


def lapse_note(entry: AcceleratedEarn, month: str) -> str | None:
    """Explain why an entry did not apply, or None if it did.

    The wording is deterministic and carries the dates verbatim from the rule
    file so the Recommender can repeat them without inventing anything."""
    if is_active(entry, month):
        return None
    if entry.valid_until is not None and _month_of(entry.valid_until) < month:
        return (
            f"the {entry.channel}/{entry.category} accelerated rate expired on "
            f"{entry.valid_until} and does not apply in {month}; base earn was used "
            f"instead. Whether the program was renewed is unconfirmed — re-verify "
            f"against the issuer's current terms before relying on this figure."
        )
    return (
        f"the {entry.channel}/{entry.category} accelerated rate does not start until "
        f"{entry.valid_from} and does not apply in {month}; base earn was used instead."
    )

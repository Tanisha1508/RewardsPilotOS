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

from rules.parser.models import AcceleratedEarn


def _month_of(iso_date: str) -> str:
    return iso_date[:7]


def is_active(entry: AcceleratedEarn, month: str) -> bool:
    """True when `entry`'s validity window overlaps `month` ("YYYY-MM").

    Open-ended on either side (None) means unbounded in that direction, which
    is the default: an entry with no dates is always active, so cards whose
    programs carry no published window behave exactly as before."""
    if entry.valid_from is not None and _month_of(entry.valid_from) > month:
        return False
    if entry.valid_until is not None and _month_of(entry.valid_until) < month:
        return False
    return True


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

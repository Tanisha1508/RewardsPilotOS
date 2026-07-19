"""Freshness re-rank: fused score * decay on last_changed (BUILD_SPEC §6).

Exponential half-life of 180 days, floored at 0.5 so stale-but-relevant
content is down-weighted, never buried. Unparseable dates get the floor."""

from datetime import date

HALF_LIFE_DAYS = 180.0
FLOOR = 0.5


def freshness_factor(last_changed: str, as_of: date) -> float:
    try:
        changed = date.fromisoformat(last_changed)
    except ValueError:
        return FLOOR
    age_days = max(0.0, (as_of - changed).days)
    decay = 0.5 ** (age_days / HALF_LIFE_DAYS)
    return max(FLOOR, decay)

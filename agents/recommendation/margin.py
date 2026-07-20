"""Winning-margin sourcing for card comparisons (BUILD_SPEC §8).

Ranking is points-only and stays that way: confidence answers "how
well-sourced is this fact", not "how good is this fact for the user", and
turning it into a ranking weight would manufacture a confidence-adjusted
point total that no cardholder ever earns (see ADR-002 and
`tests/rules/test_confidence_does_not_rank.py`).

But silence is also wrong. When the winner's margin rests on a thinly-sourced
number while a lower-scoring card's number is better evidenced, the user is
acting on a figure that carries real risk of moving on verification — exactly
the risk the confidence score was recorded to carry forward. Two P1 findings
started as single-source claims and turned out to need correcting (the HDFC
SmartBuy 5X/3X reversal, the Axis Group B cap), so this is not hypothetical.

This module names the specific number the win depends on, rather than
averaging that risk into one overall confidence label. The statement it
produces is deterministic text derived from tool results, and the Recommender
must reproduce it verbatim — it cannot be softened or dropped.
"""

from typing import Any

# The deciding field is materially thinner when it trails the comparator by
# this much...
MATERIAL_GAP = 0.15
# ...or when it is weak in absolute terms while a competitor is solid.
THIN_SOURCE_FLOOR = 0.75
WELL_SOURCED_FLOOR = 0.8


def _deciding_field(result: dict) -> tuple[str, dict] | None:
    """The field that produced this card's score: the accelerated multiplier
    when one applied, otherwise the base rate. That is the number the margin
    actually rests on."""
    if result.get("applied") == "accelerated":
        multiplier = result.get("multiplier")
        if isinstance(multiplier, dict) and multiplier.get("status") == "verified":
            return "accelerated multiplier", multiplier
    rate = result.get("rate")
    if isinstance(rate, dict) and rate.get("status") == "verified":
        return "base earn rate", rate
    return None


def _computed_comparison(rule_results: list[dict]) -> list[dict]:
    """Entries from a single CompareCards call, still in engine rank order."""
    entries = [
        entry
        for entry in rule_results
        if entry.get("tool") == "CompareCards" and entry.get("status") == "computed"
    ]
    return entries if len(entries) >= 2 else []


def margin_caveat(rule_results: list[dict]) -> dict[str, Any] | None:
    """Return a caveat when the winner's deciding number is materially
    thinner-sourced than a competing card's, else None.

    The comparator is the best-sourced competitor, which is the strongest
    honest counterexample: it is the card whose number the user has most
    reason to trust, even though it scored lower."""
    entries = _computed_comparison(rule_results)
    if not entries:
        return None

    winner, competitors = entries[0], entries[1:]
    winner_field = _deciding_field(winner)
    if winner_field is None:
        return None
    winner_label, winner_value = winner_field

    scored = []
    for competitor in competitors:
        field = _deciding_field(competitor)
        if field is not None:
            scored.append((competitor, field))
    if not scored:
        return None

    comparator, (comparator_label, comparator_value) = max(
        scored, key=lambda pair: pair[1][1].get("confidence", 0.0)
    )

    winner_confidence = float(winner_value.get("confidence", 0.0))
    comparator_confidence = float(comparator_value.get("confidence", 0.0))

    materially_thinner = winner_confidence < comparator_confidence - MATERIAL_GAP
    thin_in_absolute_terms = (
        winner_confidence < THIN_SOURCE_FLOOR and comparator_confidence >= WELL_SOURCED_FLOOR
    )
    if not (materially_thinner or thin_in_absolute_terms):
        return None

    statement = (
        f"This comparison turns on one thinly-sourced number: {winner['card_key']} "
        f"wins on its {winner_label} of {winner_value['value']}, which is verified "
        f"at confidence {winner_confidence} from {winner_value.get('source')}. "
        f"{comparator['card_key']} scored lower ({comparator.get('points')} vs "
        f"{winner.get('points')}) but its {comparator_label} is better evidenced, "
        f"at confidence {comparator_confidence}. If the {winner_label} for "
        f"{winner['card_key']} turns out to differ on your own verification, this "
        f"ranking can change."
    )

    return {
        "winner": winner["card_key"],
        "winner_field": winner_label,
        "winner_field_value": winner_value.get("value"),
        "winner_field_confidence": winner_confidence,
        "winner_field_source": winner_value.get("source"),
        "comparator": comparator["card_key"],
        "comparator_field": comparator_label,
        "comparator_field_confidence": comparator_confidence,
        "statement": statement,
    }

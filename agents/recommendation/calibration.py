"""Deterministic confidence calibration for the Recommender (BUILD_SPEC §8).

Confidence is a property of the evidence, not of the LLM's mood. Every
verified value carries the confidence of the source it came from; a
recommendation can never be more confident than the weakest source it rests
on. This module derives that ceiling deterministically from the tool results
so the Recommender reports calibrated confidence instead of a uniform "high".

Rules:
- any unknown/excluded result, tool error, lapsed accelerated rate, or
  unverified path present -> the ceiling drops (unknowns are the dominant
  signal, per the hard rules)
- otherwise the ceiling follows the minimum source confidence used:
  >= 0.8 allows "high", below that caps at "medium"

The LLM receives this as `confidence_basis` in the state digest and may report
a LOWER level than the ceiling, never a higher one — validation enforces it.
"""

from typing import Any

HIGH_CONFIDENCE_FLOOR = 0.8


def _walk_confidences(node: Any, found: list[tuple[float, str]], label: str = "") -> None:
    """Collect (confidence, source) from every verified-value shaped dict in
    the tool results. Unverified values are ignored here — they surface
    through the unknown-status signals instead."""
    if isinstance(node, dict):
        if node.get("status") == "verified" and isinstance(node.get("confidence"), (int, float)):
            found.append((float(node["confidence"]), node.get("source") or label))
        for key, value in node.items():
            _walk_confidences(value, found, label=key)
    elif isinstance(node, list):
        for item in node:
            _walk_confidences(item, found, label=label)


def confidence_basis(
    rule_results: list[dict],
    graph_results: list[dict],
    tool_errors: list[str] | None = None,
) -> dict:
    """Derive the calibrated confidence ceiling and the reason for it.

    Returns {"ceiling", "min_source_confidence", "weakest_source",
    "has_unknowns", "reason"} — all deterministic, all traceable."""
    results = list(rule_results) + list(graph_results)
    errors = list(tool_errors or [])

    has_unknowns = any(
        entry.get("status") in ("unknown", "excluded")
        or entry.get("unverified_paths_exist")
        or entry.get("unknown_reasons")
        or entry.get("value_status") == "unknown"
        for entry in results
    )
    has_computed = any(
        entry.get("status") == "computed" or entry.get("paths") or entry.get("options")
        for entry in results
    )
    # A lapsed accelerated rate (ADR-012) computes cleanly from a verified base
    # rate, so nothing above would catch it — but the figure may understate the
    # card if the program was renewed, which is exactly the kind of uncertainty
    # confidence is supposed to express.
    has_expired = any(entry.get("expiry_note") for entry in results)

    confidences: list[tuple[float, str]] = []
    _walk_confidences(results, confidences)
    min_confidence, weakest_source = min(confidences, default=(None, None))

    if not has_computed:
        ceiling = "low"
        reason = "no value could be computed; all required inputs are unknown"
    elif has_unknowns or errors or has_expired:
        ceiling = "medium"
        if has_unknowns:
            reason = "some values were computed while others are unknown pending verification"
        elif errors:
            reason = "one or more tools failed"
        else:
            reason = (
                "an accelerated rate has lapsed and base earn was used instead; "
                "whether the program was renewed is unconfirmed"
            )
    elif min_confidence is not None and min_confidence < HIGH_CONFIDENCE_FLOOR:
        ceiling = "medium"
        reason = (
            f"every value was computed, but the weakest source confidence used "
            f"is {min_confidence} ({weakest_source})"
        )
    else:
        ceiling = "high"
        reason = (
            f"all values verified and computed deterministically; weakest source "
            f"confidence {min_confidence}"
            if min_confidence is not None
            else "all values verified and computed deterministically"
        )

    return {
        "ceiling": ceiling,
        "min_source_confidence": min_confidence,
        "weakest_source": weakest_source,
        "has_unknowns": has_unknowns,
        "reason": reason,
    }

"""Extended field schema validation for rule files (BUILD_SPEC §5).

Every numeric field must carry the verified-value structure
{value, status, source, confidence}. Hard data-integrity rules
(confidence semantics per the 2026-07-19 spec update, ADR-001 amendment):
- unverified => confidence < 1 (evidence strength of the candidate value;
  never computable regardless)
- verified   => value present AND source present AND confidence > 0
Never invent rates, caps, or transfer ratios: a plain number where a
verified-value structure is required is a violation.

point_value_reference_inr is per-channel (cashback / voucher / travel), each
channel a verified-value structure.
"""

import re
from typing import Any

_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_POINT_VALUE_CHANNELS = ("cashback", "voucher", "travel")
_NUMERIC_FIELDS_BASE_EARN = ["rate"]
_NUMERIC_FIELDS_ACCELERATED = ["multiplier", "monthly_cap_points"]
_NUMERIC_FIELDS_CAP = ["cap_points"]
_NUMERIC_FIELDS_MILESTONE = ["spend_threshold", "bonus_points"]

_REQUIRED_TOP_KEYS = [
    "card_key",
    "version",
    "effective_date",
    "reward_currency",
    "base_earn",
]


def _check_verified_value(node: Any, path: str) -> list[str]:
    if not isinstance(node, dict):
        return [f"{path}: numeric field must be a verified-value object, got {type(node).__name__}"]
    problems: list[str] = []
    status = node.get("status")
    value = node.get("value")
    source = node.get("source")
    confidence = node.get("confidence")
    if status not in ("verified", "unverified"):
        problems.append(f"{path}.status: must be 'verified' or 'unverified'")
        return problems
    if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        problems.append(f"{path}.confidence: must be a number between 0 and 1")
    elif status == "unverified" and confidence >= 1:
        problems.append(f"{path}.confidence: unverified values cannot claim full confidence")
    elif status == "verified" and confidence <= 0:
        problems.append(f"{path}.confidence: verified values require confidence > 0")
    if status == "verified":
        if value is None:
            problems.append(f"{path}.value: verified value must not be null")
        if not source:
            problems.append(f"{path}.source: verified value requires an official source URL")
    return problems


def _check_point_value_reference(node: Any, path: str) -> list[str]:
    if not isinstance(node, dict):
        return [f"{path}: must be a per-channel object with {_POINT_VALUE_CHANNELS}"]
    if "status" in node and "confidence" in node:
        return [
            f"{path}: flat verified-value structure is obsolete; use per-channel "
            f"{_POINT_VALUE_CHANNELS} (spec update 2026-07-19)"
        ]
    problems: list[str] = []
    for channel in _POINT_VALUE_CHANNELS:
        if channel not in node:
            problems.append(f"{path}.{channel}: required channel missing")
        elif node[channel] is None:
            # Explicit null = confirmed "no single value exists for this
            # channel" (tier- or partner-dependent) — valid, never computable.
            continue
        else:
            problems.extend(_check_verified_value(node[channel], f"{path}.{channel}"))
    return problems


def _check_validity_window(entry: dict[str, Any], path: str) -> list[str]:
    """Validity dates must be well-formed and ordered (ADR-012).

    A malformed date is worse than a missing one: the evaluator compares
    dates as strings, so garbage would silently make an entry permanently
    active or permanently lapsed instead of erroring."""
    problems: list[str] = []
    for field in ("valid_from", "valid_until"):
        value = entry.get(field)
        if value is not None and not (isinstance(value, str) and _ISO_DATE.match(value)):
            problems.append(f"{path}.{field}: must be an ISO date (YYYY-MM-DD), got {value!r}")
    start, end = entry.get("valid_from"), entry.get("valid_until")
    if isinstance(start, str) and isinstance(end, str) and not problems and start > end:
        problems.append(f"{path}: valid_from {start} is after valid_until {end}")
    return problems


def validate_rule_dict(raw: dict[str, Any]) -> list[str]:
    """Return a list of violations; empty list means the file is valid."""
    problems: list[str] = []
    for key in _REQUIRED_TOP_KEYS:
        if key not in raw:
            problems.append(f"{key}: required field missing")
    if "point_value_reference_inr" in raw:
        problems.extend(
            _check_point_value_reference(
                raw["point_value_reference_inr"], "point_value_reference_inr"
            )
        )
    base = raw.get("base_earn")
    if isinstance(base, dict):
        for field in _NUMERIC_FIELDS_BASE_EARN:
            problems.extend(_check_verified_value(base.get(field), f"base_earn.{field}"))
        if not isinstance(base.get("per_amount"), (int, float)) or base.get("per_amount", 0) <= 0:
            problems.append("base_earn.per_amount: must be a positive number")
    for i, entry in enumerate(raw.get("accelerated") or []):
        for field in _NUMERIC_FIELDS_ACCELERATED:
            if field in entry:
                problems.extend(_check_verified_value(entry[field], f"accelerated[{i}].{field}"))
        if "multiplier" not in entry:
            problems.append(f"accelerated[{i}].multiplier: required verified-value field missing")
        problems.extend(_check_validity_window(entry, f"accelerated[{i}]"))
    for i, entry in enumerate(raw.get("caps") or []):
        problems.extend(_check_verified_value(entry.get("cap_points"), f"caps[{i}].cap_points"))
    for i, entry in enumerate(raw.get("milestones") or []):
        for field in _NUMERIC_FIELDS_MILESTONE:
            problems.extend(_check_verified_value(entry.get(field), f"milestones[{i}].{field}"))
    fees = raw.get("fees")
    if fees is not None:
        problems.extend(_check_verified_value(fees.get("annual_fee_inr"), "fees.annual_fee_inr"))
        # Optional fee facts: absent/None means "confirmed not applicable",
        # recorded in fees.notes — only validate when present.
        for field in ("renewal_fee_waiver_spend_inr", "forex_markup_pct"):
            if fees.get(field) is not None:
                problems.extend(_check_verified_value(fees[field], f"fees.{field}"))
    for i, cohort in enumerate(raw.get("welcome_bonus") or []):
        problems.extend(
            _check_verified_value(cohort.get("bonus_points"), f"welcome_bonus[{i}].bonus_points")
        )
        if cohort.get("qualifying_spend_inr") is not None:
            problems.extend(
                _check_verified_value(
                    cohort["qualifying_spend_inr"], f"welcome_bonus[{i}].qualifying_spend_inr"
                )
            )
    for i, entry in enumerate(raw.get("redemption_catalogue") or []):
        problems.extend(
            _check_verified_value(
                entry.get("rate_per_point_inr"), f"redemption_catalogue[{i}].rate_per_point_inr"
            )
        )
    for i, tier in enumerate(raw.get("tiers") or []):
        for field in ("annual_spend_threshold_inr", "renewal_bonus_points"):
            problems.extend(_check_verified_value(tier.get(field), f"tiers[{i}].{field}"))
    continuation = raw.get("continuation_eligibility")
    if continuation is not None:
        for field in ("annual_spend_inr", "relationship_value_inr"):
            problems.extend(
                _check_verified_value(continuation.get(field), f"continuation_eligibility.{field}")
            )
    return problems

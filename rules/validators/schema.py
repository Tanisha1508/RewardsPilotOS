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

from typing import Any

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
        else:
            problems.extend(_check_verified_value(node[channel], f"{path}.{channel}"))
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
    for i, entry in enumerate(raw.get("caps") or []):
        problems.extend(_check_verified_value(entry.get("cap_points"), f"caps[{i}].cap_points"))
    for i, entry in enumerate(raw.get("milestones") or []):
        for field in _NUMERIC_FIELDS_MILESTONE:
            problems.extend(_check_verified_value(entry.get(field), f"milestones[{i}].{field}"))
    fees = raw.get("fees")
    if fees is not None:
        for field in ("annual_fee_inr", "renewal_fee_waiver_spend_inr"):
            problems.extend(_check_verified_value(fees.get(field), f"fees.{field}"))
    continuation = raw.get("continuation_eligibility")
    if continuation is not None:
        for field in ("annual_spend_inr", "relationship_value_inr"):
            problems.extend(
                _check_verified_value(continuation.get(field), f"continuation_eligibility.{field}")
            )
    return problems

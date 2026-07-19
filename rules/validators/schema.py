"""Extended field schema validation for rule files (BUILD_SPEC §5).

Every numeric field must carry the verified-value structure
{value, status, source, confidence}. Hard data-integrity rules:
- unverified => confidence 0
- verified   => value present AND source (official issuer URL) present
Never invent rates, caps, or transfer ratios: a plain number where a
verified-value structure is required is a violation.
"""

from typing import Any

# Paths (relative to the rule root) that must be verified-value structures.
_NUMERIC_FIELDS_TOP = ["point_value_reference_inr"]
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
    elif status == "unverified" and confidence != 0:
        problems.append(f"{path}.confidence: must be 0 when unverified")
    if status == "verified":
        if value is None:
            problems.append(f"{path}.value: verified value must not be null")
        if not source:
            problems.append(f"{path}.source: verified value requires an official source URL")
    return problems


def validate_rule_dict(raw: dict[str, Any]) -> list[str]:
    """Return a list of violations; empty list means the file is valid."""
    problems: list[str] = []
    for key in _REQUIRED_TOP_KEYS:
        if key not in raw:
            problems.append(f"{key}: required field missing")
    for field in _NUMERIC_FIELDS_TOP:
        if field in raw:
            problems.extend(_check_verified_value(raw[field], field))
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
    return problems

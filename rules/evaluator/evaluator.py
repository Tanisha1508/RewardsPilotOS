"""Pure earn evaluation over a parsed rule file (BUILD_SPEC §5).

All math here is deterministic. Any unverified or null numeric input makes the
result `unknown` — the evaluator never guesses. Point math: earning happens in
blocks of `per_amount` spend, so points = floor(amount / per_amount) * rate
(* multiplier when an accelerated entry applies).

Cap semantics: when an accelerated entry carries a monthly cap, points beyond
the remaining cap for the month are clipped (no base-rate fallback on the
clipped excess; revisit only via spec update).
"""

import math

from contracts.api.verified_value import VerifiedValue
from contracts.tools.rule_engine import CapStatus, EarnResult
from rules.parser.models import AcceleratedEarn, RuleFile


def _sources(*values: VerifiedValue) -> list[str]:
    return [v.source for v in values if v.source]


def find_accelerated(rule: RuleFile, category: str, channel: str | None) -> AcceleratedEarn | None:
    if channel is None:
        return None
    for entry in rule.accelerated:
        if entry.channel == channel and entry.category in (category, "all"):
            return entry
    return None


def cap_status(rule: RuleFile, scope: str, month: str, accrued: float) -> CapStatus:
    for cap in rule.caps:
        if cap.scope == scope:
            if not cap.cap_points.is_usable:
                return CapStatus(
                    card_key=rule.card_key,
                    scope=scope,
                    period=cap.period,
                    month=month,
                    cap_points=cap.cap_points,
                    accrued_points=accrued,
                    remaining_points=None,
                    status="unknown",
                    unknown_reasons=[
                        f"cap '{scope}' has {cap.cap_points.status} cap_points; cannot compute"
                    ],
                )
            remaining = max(0.0, float(cap.cap_points.value) - accrued)
            return CapStatus(
                card_key=rule.card_key,
                scope=scope,
                period=cap.period,
                month=month,
                cap_points=cap.cap_points,
                accrued_points=accrued,
                remaining_points=remaining,
                status="reached" if remaining == 0 else "ok",
                sources=_sources(cap.cap_points),
            )
    return CapStatus(
        card_key=rule.card_key,
        scope=scope,
        period="month",
        month=month,
        cap_points=VerifiedValue.unknown(),
        accrued_points=accrued,
        remaining_points=None,
        status="unknown",
        unknown_reasons=[f"no cap with scope '{scope}' defined for {rule.card_key}"],
    )


def evaluate_earn(
    rule: RuleFile,
    amount: float,
    category: str,
    channel: str | None,
    month: str,
    accrued_for_scope: float = 0.0,
) -> EarnResult:
    base = EarnResult(
        card_key=rule.card_key,
        amount=amount,
        category=category,
        channel=channel,
        month=month,
        status="unknown",
        rule_version=rule.version,
    )

    if category in rule.exclusions:
        base.status = "excluded"
        base.points = 0.0
        base.unknown_reasons = [f"category '{category}' is excluded from earning"]
        return base

    accelerated = find_accelerated(rule, category, channel)
    rate = rule.base_earn.rate
    base.rate = rate

    if not rate.is_usable:
        base.unknown_reasons.append(
            f"reward rules for {rule.card_key} are not yet verified: base earn "
            f"rate is {rate.status} (value={rate.value}); cannot compute"
        )
        return base

    blocks = math.floor(amount / rule.base_earn.per_amount)
    base_points = blocks * float(rate.value)

    if accelerated is None:
        base.status = "computed"
        base.applied = "base"
        base.points = base_points
        base.sources = _sources(rate)
        return base

    base.applied = "accelerated"
    base.multiplier = accelerated.multiplier
    if not accelerated.multiplier.is_usable:
        base.status = "unknown"
        base.unknown_reasons.append(
            f"accelerated multiplier ({accelerated.channel}/{accelerated.category}) is "
            f"{accelerated.multiplier.status}; cannot compute"
        )
        return base

    accel_points = base_points * float(accelerated.multiplier.value)
    base.points_before_cap = accel_points

    cap_vv = accelerated.monthly_cap_points
    if cap_vv.value is None and cap_vv.status == "unverified" and accelerated.cap_scope is None:
        # No cap declared at all: unverified-with-null on the optional field and
        # no scope reference means the rule file records no cap for this entry.
        base.status = "computed"
        base.points = accel_points
        base.sources = _sources(rate, accelerated.multiplier)
        return base

    if not cap_vv.is_usable:
        base.status = "unknown"
        base.unknown_reasons.append(
            f"monthly cap for {accelerated.channel}/{accelerated.category} is "
            f"{cap_vv.status}; capped earn cannot be computed"
        )
        return base

    remaining = max(0.0, float(cap_vv.value) - accrued_for_scope)
    base.status = "computed"
    base.sources = _sources(rate, accelerated.multiplier, cap_vv)
    base.cap_scope = accelerated.cap_scope or f"{accelerated.channel}_{accelerated.category}"
    if accel_points > remaining:
        base.points = remaining
        base.cap_applied = True
    else:
        base.points = accel_points
    return base

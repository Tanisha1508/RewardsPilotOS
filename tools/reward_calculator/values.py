"""Point-value reference lookup for redemption valuation (BUILD_SPEC §7).

Values come from Rule Engine value tables (point_value_reference_inr per rule
file). Currencies without a rule file, or with null/unverified values, stay
unknown — valuation is never estimated."""

from contracts.api.verified_value import VerifiedValue
from rules.parser.loader import RuleNotFoundError, list_versions
from rules.versioning.selector import select_version

# reward currency -> card_key whose rule file carries the value reference
_CURRENCY_TO_CARD = {
    "hdfc_reward_points": "hdfc_infinia",
    "edge_miles": "axis_atlas",
    "membership_rewards": "amex_plat_travel",
}


def get_point_values(currencies: list[str]) -> dict[str, VerifiedValue]:
    values: dict[str, VerifiedValue] = {}
    for currency in currencies:
        card_key = _CURRENCY_TO_CARD.get(currency)
        if card_key is None:
            values[currency] = VerifiedValue.unknown()
            continue
        try:
            list_versions(card_key)
        except RuleNotFoundError:
            values[currency] = VerifiedValue.unknown()
            continue
        values[currency] = select_version(card_key).point_value_reference_inr
    return values

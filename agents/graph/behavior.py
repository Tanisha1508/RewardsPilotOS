"""Graph-focused agent behavior: mapping user language onto graph node ids."""

_CURRENCY_ALIASES = {
    "voyager": "voyager_points",
    "voyager points": "voyager_points",
    "trailblazer": "trailblazer_miles",
    "hdfc reward points": "hdfc_reward_points",
    "edge miles": "edge_miles",
    "membership rewards": "membership_rewards",
}

_PROGRAM_ALIASES = {
    "skyhigh": "skyhigh_airways",
    "grandstay": "grandstay_hotels",
    "krisflyer": "singapore_krisflyer",
    "air india": "air_india_flying_returns",
    "marriott": "marriott_bonvoy",
}


def resolve_currency(text: str) -> str | None:
    lowered = text.lower()
    for alias, node_id in _CURRENCY_ALIASES.items():
        if alias in lowered:
            return node_id
    return None


def resolve_program(text: str) -> str | None:
    lowered = text.lower()
    for alias, node_id in _PROGRAM_ALIASES.items():
        if alias in lowered:
            return node_id
    return None

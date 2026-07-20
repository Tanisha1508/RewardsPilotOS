"""Canonical spend channels for cross-issuer matching (BUILD_SPEC §5).

Companion to `categories.py`, fixing the same defect on the channel axis.

Every issuer names its own booking portal differently — HDFC calls it
SmartBuy, Axis calls it Travel EDGE, Amex calls it Reward Multiplier — and
each rule file faithfully records the issuer's own name. `CompareCards` takes
ONE channel string for all cards, so a portal query could only ever match the
single card whose portal name was passed; every other card silently fell back
to its base rate and under-reported.

A canonical channel is a query-side concept ("the card's own booking portal")
that resolves to whichever issuer-specific channel each card actually
declares. It is card-agnostic: registering a new issuer's portal name here
makes every card using it resolve correctly, with no per-card entries to keep
in sync.

`direct` is deliberately NOT canonical — it already means the same thing for
every issuer (booking with the merchant rather than through a portal), so it
matches by its own name.

This is a vocabulary, not reward data: it contains no rate, cap, or multiplier
and cannot change what a card earns on a channel the issuer already covers.
Discovered 2026-07-20 during end-to-end demo-query testing; see ADR-011.
"""

# canonical query channel -> the issuer-specific channel names that realise it.
# Each alias must be a channel an issuer actually declares in its rule file.
CANONICAL_CHANNELS: dict[str, frozenset[str]] = {
    # The card issuer's own booking portal.
    #   smartbuy          - HDFC SmartBuy
    #   travel_edge       - Axis Travel EDGE
    #   reward_multiplier - Amex Reward Multiplier
    "issuer_portal": frozenset({"smartbuy", "travel_edge", "reward_multiplier"}),
}


def channel_matches(rule_channel: str, queried_channel: str) -> bool:
    """True when an accelerated entry declared for `rule_channel` applies to a
    query for `queried_channel`.

    Resolution is one-directional: a canonical query resolves to an issuer's
    concrete channel, never the reverse. Querying `smartbuy` must not match
    Axis's `travel_edge` — that would claim HDFC's portal rate applies to an
    Axis booking."""
    if rule_channel == queried_channel:
        return True
    return rule_channel in CANONICAL_CHANNELS.get(queried_channel, frozenset())


def is_canonical(channel: str | None) -> bool:
    return channel in CANONICAL_CHANNELS

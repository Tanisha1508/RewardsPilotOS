"""Resolve a user's card identity to a Rule Engine card_key.

A `cards` row describes a card in human terms (issuer + card_name); the Rule
Engine reasons in card_keys (`rules/seed/<card_key>`). This maps between them so
the Planner can drive CompareCards / CalculateEarn against a card the user
actually holds — the same shape of problem as the S2 reward_currency fix (a
user's card linked to system reasoning data), one layer over.

Returns None when the card has no computable rule file. That is honest: the card
is tracked, but the engine has nothing verified to compute for it, and the
recommendation says so rather than guessing.

**Only cards whose rule file actually computes belong here.** The seven P2
skeletons ship all-null and refuse to compute; listing them would resolve a
card_key that then returns "unknown" anyway, implying coverage we do not have.
When a card graduates from the VERIFICATION_QUEUE to a verified rule file, add
it here — one line, and a name variant or two.
"""


def _norm(text: str) -> str:
    return " ".join(text.strip().lower().split())


# (issuer, normalized card_name) -> card_key. Common name variants included so a
# user typing "Infinia" or "HDFC Infinia" both resolve.
_CATALOG: dict[tuple[str, str], str] = {
    ("hdfc", "hdfc infinia"): "hdfc_infinia",
    ("hdfc", "infinia"): "hdfc_infinia",
    ("hdfc", "hdfc bank infinia"): "hdfc_infinia",
    ("axis", "axis bank atlas"): "axis_atlas",
    ("axis", "axis atlas"): "axis_atlas",
    ("axis", "atlas"): "axis_atlas",
    ("amex", "amex platinum travel"): "amex_plat_travel",
    ("amex", "platinum travel"): "amex_plat_travel",
    ("amex", "american express platinum travel"): "amex_plat_travel",
}


def resolve_card_key(issuer: str, card_name: str) -> str | None:
    """The card_key for a held card, or None if it is not a card the engine can
    reason about (yet)."""
    return _CATALOG.get((_norm(issuer), _norm(card_name)))


def known_card_keys() -> set[str]:
    """The card_keys this catalogue can resolve to — every one has a verified,
    computable rule file (asserted by tests against rules/seed)."""
    return set(_CATALOG.values())

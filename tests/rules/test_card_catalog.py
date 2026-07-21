"""Card identity → card_key resolution (D4, 2026-07-22).

Locks two things: the three verified P1 cards resolve (with common name
variants), and every card_key the catalogue can produce actually has a
computable rule file — a catalogue entry pointing at a missing or all-null card
would resolve a key that then refuses to compute, which is the exact failure
this fix removes.
"""

import pytest

from rules.engine.engine import RuleEngine
from rules.parser.catalog import known_card_keys, resolve_card_key


@pytest.mark.parametrize(
    "issuer,name,expected",
    [
        ("hdfc", "HDFC Infinia", "hdfc_infinia"),
        ("hdfc", "Infinia", "hdfc_infinia"),
        ("axis", "Axis Bank Atlas", "axis_atlas"),
        ("axis", "Atlas", "axis_atlas"),
        ("amex", "Amex Platinum Travel", "amex_plat_travel"),
        ("amex", "Platinum Travel", "amex_plat_travel"),
        # Case and whitespace insensitive.
        ("HDFC", "  hdfc   infinia  ", "hdfc_infinia"),
    ],
)
def test_verified_p1_cards_resolve(issuer, name, expected):
    assert resolve_card_key(issuer, name) == expected


def test_unknown_card_returns_none_not_a_guess():
    assert resolve_card_key("randombank", "Some Card") is None
    assert resolve_card_key("hdfc", "Diners Club Black") is None  # P2 skeleton, not catalogued


def test_every_catalogued_key_actually_computes():
    """The catalogue must only point at cards that compute. A key with an
    all-null skeleton would resolve and then return unknown — reintroducing the
    very 'unable to determine' this fix removes."""
    engine = RuleEngine()
    for card_key in known_card_keys():
        result = engine.calculate_earn(card_key, 50_000, "flights", None, "2026-07")
        assert result.status == "computed", f"{card_key} does not compute — do not catalogue it"

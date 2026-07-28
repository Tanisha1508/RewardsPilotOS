"""Base earn from an unstated channel must say so (found live 2026-07-28).

`_matching` returns None when no channel is supplied, so every card falls to
base earn. That is the correct computation — the evaluator will not assume
where a purchase happens — but it was silent, and silence made a
channel-dependent ranking read as settled.

The live symptom: "best card for a Rs 50,000 flight?" ranked hdfc_infinia
(1665, base) above axis_atlas (1000, base) and reported HIGH confidence, when
booking that flight direct with the airline earns axis_atlas 2500 and reverses
the result. Nothing was fabricated and no arithmetic was wrong; the answer just
turned on a question nobody asked.

These tests pin the engine half. `tests/agent/test_channel_note.py` pins the
half that matters to the user: the note cannot be dropped on the way out.
"""

from rules.engine.engine import RuleEngine

CARDS = ["hdfc_infinia", "axis_atlas", "amex_plat_travel"]


def _by_key(results):
    return {r.card_key: r for r in results}


def test_the_live_regression_channel_less_flight_comparison_is_flagged():
    """The exact query that failed, at the month it failed in."""
    results = _by_key(RuleEngine().compare_cards(CARDS, 50_000, "flights", None, "2026-07"))

    # Still the honest base-earn computation — the fix adds a note, not a rate.
    assert results["hdfc_infinia"].points == 1665.0
    assert results["axis_atlas"].points == 1000.0
    assert all(r.applied == "base" for r in results.values())

    # ...and every card now says the channel is what is missing.
    for card_key, result in results.items():
        assert result.channel_note is not None, f"{card_key} has no channel note"
        assert "no booking channel was given" in result.channel_note

    # The note names the issuer's own channels, so the user knows where to look.
    assert "travel_edge" in results["axis_atlas"].channel_note
    assert "direct" in results["axis_atlas"].channel_note
    assert "smartbuy" in results["hdfc_infinia"].channel_note


def test_naming_the_channel_removes_the_note_and_reverses_the_winner():
    """The note's whole claim is that the channel can change the answer. If
    this ranking ever stops flipping, the note is overstating the risk."""
    results = RuleEngine().compare_cards(CARDS, 50_000, "flights", "direct", "2026-07")

    assert results[0].card_key == "axis_atlas"
    assert results[0].points == 2500.0
    assert results[0].applied == "accelerated"
    # The user stated where they are buying, so there is nothing left to flag.
    assert all(r.channel_note is None for r in results)


def test_no_note_when_the_card_has_no_accelerated_rate_for_the_category():
    """The mechanism must stay quiet when the channel could not have helped —
    otherwise every base-earn answer carries a caveat that leads nowhere.

    Infinia's accelerated entries are smartbuy/{flights,hotels,brand_vouchers},
    so groceries match none of them."""
    result = RuleEngine().calculate_earn("hdfc_infinia", 50_000, "groceries", None, "2026-07")

    assert result.applied == "base"
    assert result.channel_note is None


def test_a_category_all_portal_entry_flags_any_category():
    """Axis's travel_edge entry is category "all", so a groceries query does
    reach an accelerated entry and IS flagged. That follows the rule file: the
    portal's own terms say everything booked there earns 2.5x, and the engine
    holds no data on which categories a portal actually sells. Pinned because
    it looks like over-firing until you read the rule file."""
    result = RuleEngine().calculate_earn("axis_atlas", 50_000, "groceries", None, "2026-07")

    assert result.applied == "base"
    assert result.channel_note is not None
    assert "travel_edge" in result.channel_note
    # Only the portal entry matches; the direct entry is travel-only.
    assert "direct" not in result.channel_note


def test_no_note_when_the_accelerated_rate_is_not_in_force():
    """Amex Reward Multiplier ends 2026-07-31. Pointing a user at a channel
    that no longer pays would be worse than saying nothing."""
    engine = RuleEngine()

    in_force = engine.calculate_earn("amex_plat_travel", 50_000, "hotels", None, "2026-07")
    assert in_force.channel_note is not None

    lapsed = engine.calculate_earn("amex_plat_travel", 50_000, "hotels", None, "2026-08")
    assert lapsed.channel_note is None


def test_a_stated_channel_that_earns_no_bonus_is_an_answer_not_a_gap():
    """`third_party` is a real answer: the user said where they are buying and
    that channel earns base. Flagging it would imply an unasked question that
    has, in fact, been asked and answered."""
    result = RuleEngine().calculate_earn("axis_atlas", 50_000, "flights", "third_party", "2026-07")

    assert result.applied == "base"
    assert result.channel_note is None

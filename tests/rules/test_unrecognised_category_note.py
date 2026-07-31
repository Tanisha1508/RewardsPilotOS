"""An unrecognised category must say so rather than quietly earn base
(B2, closes the open half of KNOWN_LIMITATIONS 30).

`hotel` where every rule file says `hotels` cost a 10x under-report: nothing
matched, the SmartBuy entry was skipped, and Rs 30,000 scored 1,000 points
instead of 10,000 — full confidence, no warning. `canonical_category()` fixed
that instance. It cannot fix the class: the alias map covers the variants we
thought of, and by construction not the ones we did not.

The engine cannot tell an unmapped synonym from genuinely different spend. So it
stops trying to, and reports what it did and what else the card offers.
"""

from rules.evaluator.categories import (
    RECOGNISED_CATEGORIES,
    is_recognised_category,
    unrecognised_category_note,
)


def test_words_the_rule_files_use_are_recognised():
    for category in ("hotels", "flights", "travel", "brand_vouchers", "fuel"):
        assert is_recognised_category(category), category


def test_a_known_variant_is_recognised_through_its_alias():
    """`hotel` is recognised because the alias map maps it to `hotels`. The note
    must not fire on a word we already handle correctly."""
    assert is_recognised_category("hotel")
    assert is_recognised_category("airfare")


def test_a_word_we_have_never_seen_is_not_recognised():
    assert not is_recognised_category("hotel_stays")
    assert not is_recognised_category("aeroplane_tickets")


def test_a_cards_own_declared_categories_count_as_recognised():
    """A new issuer must not need this module edited before its categories stop
    being reported as unrecognised — the rule file is the authority on its own
    vocabulary."""
    assert not is_recognised_category("ev_charging")
    assert is_recognised_category("ev_charging", declared=["ev_charging", "flights"])


def test_the_note_names_what_the_card_actually_offers():
    note = unrecognised_category_note("hdfc_infinia", "hotel_stays", ["hotels", "flights"])

    assert "'hotel_stays'" in note
    assert "hdfc_infinia" in note
    assert "base rate" in note
    assert "flights, hotels" in note, "must list the card's own categories, sorted"


def test_the_note_carries_no_invented_number():
    """It explains a computation; it must not assert a rate or a figure."""
    note = unrecognised_category_note("axis_atlas", "aeroplane_tickets", ["travel"])
    assert not any(ch.isdigit() for ch in note)


def test_recognised_set_is_built_from_both_maps():
    """Guards against the set being hand-maintained and drifting from the maps
    it is supposed to summarise."""
    from rules.evaluator.categories import CATEGORY_ALIASES, CATEGORY_SUBSUMES

    for alias, target in CATEGORY_ALIASES.items():
        assert alias in RECOGNISED_CATEGORIES and target in RECOGNISED_CATEGORIES
    for broader, narrower in CATEGORY_SUBSUMES.items():
        assert broader in RECOGNISED_CATEGORIES
        assert narrower <= RECOGNISED_CATEGORIES

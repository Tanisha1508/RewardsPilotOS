"""A card's reward currency must name a currency (B1, closes KNOWN_LIMITATIONS 31).

The bug this prevents was not a typo. The transfer graph holds

    membership_rewards        currency, 8 outgoing transfer edges
    amex_membership_rewards   card,     0 edges

and a seed script pointed Amex Platinum Travel at the *card*. Transfer lookups
started there, found no outgoing edges, and returned nothing — which reads
exactly like a card with no transfer partners. The value was real, so nothing
complained.

So the test that matters most here is not "rubbish is rejected". It is
`test_a_card_node_is_rejected_even_though_it_exists`.
"""

import pytest

from backend.api.responses import STATUS_BY_EXCEPTION
from backend.application.errors import InvalidReferenceError
from backend.application.reward_currency import known_currencies, validate_reward_currency


def test_the_real_currencies_are_accepted():
    for currency in ("edge_miles", "hdfc_reward_points", "membership_rewards"):
        validate_reward_currency(currency)  # must not raise


def test_a_card_node_is_rejected_even_though_it_exists():
    """The actual defect. `amex_membership_rewards` is a real node id — it is
    just a card, so transfers from it find nothing."""
    with pytest.raises(InvalidReferenceError) as caught:
        validate_reward_currency("amex_membership_rewards")

    message = str(caught.value)
    assert "is a card" in message, "must name what it actually is"
    assert "membership_rewards" in message, "must list the currency the user meant"


def test_a_currency_the_graph_has_never_heard_of_is_ALLOWED():
    """The asymmetry, and the half the first version of this got wrong.

    A card from an unsupported issuer must stay addable. The engines already
    report "there is no data for this" honestly, which is the documented
    behaviour of `test_card_whose_currency_is_not_in_the_graph_reports_missing_data`.
    Rejecting it would lock the product to the five currencies in the seed graph
    and turn an honest-unknown path into a dead end."""
    validate_reward_currency("newbank_altitude_miles")  # must not raise


def test_the_message_lists_what_to_use_instead():
    """A rejection a user cannot act on is a dead end."""
    with pytest.raises(InvalidReferenceError) as caught:
        validate_reward_currency("amex_membership_rewards")
    for currency in known_currencies():
        assert currency in str(caught.value)


def test_it_reports_as_422():
    """Understood, and wrong — not malformed (400) and not a conflict (409)."""
    assert dict(STATUS_BY_EXCEPTION)[InvalidReferenceError] == 422


def test_every_currency_node_is_accepted():
    """Guards the check against the graph growing: a currency added to the seed
    graph must not need this module edited to become usable."""
    for currency in known_currencies():
        validate_reward_currency(currency)


def test_no_card_node_passes_as_a_currency():
    """The whole class, not just the one instance that bit."""
    from graph.builder.builder import load_seed_graph

    cards = [n for n, d in load_seed_graph().nodes(data=True) if d.get("node_type") == "card"]
    assert cards, "fixture check: the graph should contain card nodes"
    for card in cards:
        with pytest.raises(InvalidReferenceError):
            validate_reward_currency(card)

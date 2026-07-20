"""A currency the transfer graph has never heard of must say so.

Failure class: a vocabulary gap presenting as a result. Zero paths is a
perfectly good answer when a currency is registered and simply has no verified
route — and it is a wrong answer when we hold no data on the currency at all.
Both used to produce the same empty output, so adding a card from an
unregistered issuer looked like a card with no transfer options.

This is the third time this shape has appeared: ADR-010 (category granularity)
and ADR-011 (issuer portal names) were the same bug in the matching layer. The
test that catches it is never a unit test of the lookup — it is a query for
something deliberately absent, asserting the system distinguishes "no" from
"I don't know".
"""

import pytest

from contracts.tools.graph_engine import RedemptionGoal
from contracts.tools.transfer_ratios import GetTransferRatiosInput
from graph.optimization.redemption import redemption_options
from graph.search.paths import best_transfer_paths
from tools.graph_engine.tools import get_transfer_ratios

UNREGISTERED = "newbank_points"


def test_unregistered_currency_is_reported_not_silently_empty(fixture_graph):
    """The regression: a new issuer's currency with no graph node."""
    output = best_transfer_paths(fixture_graph, UNREGISTERED, "target_air")

    assert output.paths == []
    assert output.no_transfer_data is not None
    assert UNREGISTERED in output.no_transfer_data
    assert "not registered in the transfer graph" in output.no_transfer_data


def test_registered_currency_with_no_route_is_not_reported_as_missing_data(fixture_graph):
    """The other half, and the reason a boolean "empty" is not enough:
    c_points IS in the graph and genuinely has no path to target_air. That is a
    finding, and it must not be dressed up as a data gap."""
    output = best_transfer_paths(fixture_graph, "c_points", "target_air")

    assert output.paths == []
    assert output.no_transfer_data is None


def test_unregistered_target_program_is_reported(fixture_graph):
    output = best_transfer_paths(fixture_graph, "a_points", "nonexistent_air")

    assert output.paths == []
    assert "nonexistent_air" in (output.no_transfer_data or "")


def test_both_ends_unregistered_names_both(fixture_graph):
    output = best_transfer_paths(fixture_graph, UNREGISTERED, "nonexistent_air")

    assert UNREGISTERED in (output.no_transfer_data or "")
    assert "nonexistent_air" in (output.no_transfer_data or "")


def test_redemption_options_surfaces_the_gap_per_currency(fixture_graph):
    """A portfolio holding one registered and one unregistered currency must
    return the option it can compute AND name the one it cannot."""
    output = redemption_options(
        fixture_graph,
        {"a_points": 50_000, UNREGISTERED: 30_000},
        RedemptionGoal(target_program="target_air", required_points=1000),
    )

    assert [option.currency for option in output.options] == ["a_points"]
    assert len(output.no_transfer_data) == 1
    assert UNREGISTERED in output.no_transfer_data[0]


def test_portfolio_of_only_unregistered_currencies_is_not_nothing_to_recommend(
    fixture_graph,
):
    """Zero options plus zero explanation reads as "you have no way to get
    there". The honest answer is "we have no data on the cards you hold"."""
    output = redemption_options(
        fixture_graph,
        {UNREGISTERED: 30_000},
        RedemptionGoal(target_program="target_air", required_points=1000),
    )

    assert output.options == []
    assert output.no_transfer_data, "zero options with no stated reason is the bug"


def test_get_transfer_ratios_reports_an_unregistered_currency():
    output = get_transfer_ratios(GetTransferRatiosInput(currency=UNREGISTERED))

    assert output.ratios == []
    assert output.no_transfer_data is not None
    assert "not registered" in output.no_transfer_data


@pytest.mark.parametrize("currency", ["hdfc_reward_points", "edge_miles"])
def test_registered_seed_currencies_report_no_gap(currency):
    """The mechanism must stay quiet for currencies that are registered —
    otherwise every answer carries a spurious data-gap warning."""
    assert get_transfer_ratios(GetTransferRatiosInput(currency=currency)).no_transfer_data is None

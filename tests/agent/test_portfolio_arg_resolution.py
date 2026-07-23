"""Portfolio-derived args are resolved for every card-taking tool, not just
CompareCards (KNOWN_LIMITATIONS 24, Class B).

The D4 fix injected card_keys into CompareCards only. `CalculateEarn` and
`CheckCap` also require a `card_key` the model has no legitimate basis to
produce — it is catalogue vocabulary (`hdfc_infinia`), not something in the
user's words — so they reproduced the same bug one tool along. Confirmed live
on 2026-07-22: the planner emitted `CheckCap` with `card_key: null`, validation
rejected it, and the cap headroom silently vanished from the answer.

These tests assert the resolver's *shape*, not any reward figure.
"""

import pytest

from agents.planner.portfolio_args import resolve_portfolio_args
from contracts.tools.portfolio import Card

VERIFIED = Card(
    card_id="c1",
    issuer="hdfc",
    card_name="HDFC Infinia",
    network="visa",
    reward_currency="hdfc_reward_points",
    card_key="hdfc_infinia",
    status="active",
)
SECOND = Card(
    card_id="c2",
    issuer="axis",
    card_name="Axis Bank Atlas",
    network="visa",
    reward_currency="edge_miles",
    card_key="axis_atlas",
    status="active",
)
SYNTHETIC = Card(
    card_id="c3",
    issuer="demo_bank",
    card_name="Demo Bank Voyager",
    network="visa",
    reward_currency="voyager_points",
    card_key=None,  # not in the verified catalogue — cannot be computed
    status="active",
)

HELD = [VERIFIED, SECOND, SYNTHETIC]


def _args(plan, tool):
    return [entry["args"] for entry in plan if entry.get("tool") == tool]


@pytest.mark.parametrize("tool", ["CalculateEarn", "CheckCap"])
def test_a_missing_card_key_fans_out_over_held_cards(tool):
    """The single-card analogue of CompareCards' list: one invocation per held
    card that resolves. This is the exact live failure — card_key: null."""
    plan = [{"tool": tool, "args": {"card_key": None, "amount": 5000, "category": "dining"}}]
    resolved = resolve_portfolio_args(plan, HELD)
    assert [a["card_key"] for a in _args(resolved, tool)] == ["hdfc_infinia", "axis_atlas"]


@pytest.mark.parametrize("tool", ["CalculateEarn", "CheckCap"])
def test_an_absent_card_key_field_is_resolved_too(tool):
    """Omitted and null are the same failure — the model had nothing to say."""
    resolved = resolve_portfolio_args([{"tool": tool, "args": {"amount": 5000}}], HELD)
    assert len(_args(resolved, tool)) == 2


@pytest.mark.parametrize("tool", ["CalculateEarn", "CheckCap"])
def test_an_explicit_card_key_is_never_overridden(tool):
    """If the model named a card, that came from the user's question ("how much
    on my Atlas?"). Overriding it would answer a question nobody asked."""
    plan = [{"tool": tool, "args": {"card_key": "axis_atlas", "amount": 5000}}]
    resolved = resolve_portfolio_args(plan, HELD)
    assert [a["card_key"] for a in _args(resolved, tool)] == ["axis_atlas"]


@pytest.mark.parametrize("tool", ["CalculateEarn", "CheckCap"])
def test_no_resolvable_card_drops_the_invocation(tool):
    """Dropped, never guessed: a synthetic card has no rule file, so there is
    nothing to compute and the recommender degrades honestly."""
    plan = [{"tool": tool, "args": {"card_key": None}}]
    assert resolve_portfolio_args(plan, [SYNTHETIC]) == []


def test_compare_cards_behaviour_is_unchanged():
    """The D4 fix must survive the generalisation."""
    plan = [{"tool": "CompareCards", "args": {"cards": [], "amount": 50000}}]
    resolved = resolve_portfolio_args(plan, HELD)
    assert _args(resolved, "CompareCards")[0]["cards"] == ["hdfc_infinia", "axis_atlas"]
    assert resolve_portfolio_args(plan, [SYNTHETIC]) == []


def test_currency_fans_out_over_held_reward_currencies():
    """currency is portfolio-derived like card_key, one level out: it is the
    reward currency of a held card, not something the user names. An unresolved
    one fans out over every held reward currency, including a synthetic one
    with no card_key (the graph decides what is registered)."""
    plan = [{"tool": "BestTransferPaths", "args": {"currency": None, "target_program": "aeroplan"}}]
    resolved = resolve_portfolio_args(plan, HELD)
    assert [a["currency"] for a in _args(resolved, "BestTransferPaths")] == [
        "hdfc_reward_points",
        "edge_miles",
        "voyager_points",
    ]
    # target_program is untouched — it is genuinely query-derived.
    assert all(a["target_program"] == "aeroplan" for a in _args(resolved, "BestTransferPaths"))


def test_get_transfer_ratios_currency_fans_out_too():
    plan = [{"tool": "GetTransferRatios", "args": {}}]
    resolved = resolve_portfolio_args(plan, HELD)
    assert [a["currency"] for a in _args(resolved, "GetTransferRatios")] == [
        "hdfc_reward_points",
        "edge_miles",
        "voyager_points",
    ]


def test_an_explicit_currency_is_never_overridden():
    """ "my HDFC points" is a real signal from the query."""
    plan = [{"tool": "GetTransferRatios", "args": {"currency": "hdfc_reward_points"}}]
    resolved = resolve_portfolio_args(plan, HELD)
    assert [a["currency"] for a in _args(resolved, "GetTransferRatios")] == ["hdfc_reward_points"]


def test_duplicate_reward_currencies_fan_out_once():
    """Two cards on the same currency should not double the invocations."""
    plan = [{"tool": "GetTransferRatios", "args": {}}]
    twins = [VERIFIED, SECOND, VERIFIED]
    resolved = resolve_portfolio_args(plan, twins)
    assert [a["currency"] for a in _args(resolved, "GetTransferRatios")] == [
        "hdfc_reward_points",
        "edge_miles",
    ]


def test_no_held_currency_drops_the_currency_invocation():
    """Nothing to query; dropped rather than guessed. A card carrying no reward
    currency at all contributes nothing."""
    bare = Card(
        card_id="c9",
        issuer="x",
        card_name="Bare",
        network="visa",
        reward_currency="",
        card_key=None,
        status="active",
    )
    plan = [{"tool": "BestTransferPaths", "args": {"currency": None, "target_program": "aeroplan"}}]
    assert resolve_portfolio_args(plan, [bare]) == []


def test_target_program_is_left_open():
    """target_program is genuinely query-derived, not portfolio data — the
    resolver must not invent one. SearchKnowledge is untouched entirely."""
    plan = [
        {"tool": "BestTransferPaths", "args": {"currency": "hdfc_reward_points"}},
        {"tool": "SearchKnowledge", "args": {"query": "transfer partners"}},
    ]
    resolved = resolve_portfolio_args(plan, HELD)
    # currency was explicit, so no fan-out; target_program still absent (open).
    assert _args(resolved, "BestTransferPaths") == [{"currency": "hdfc_reward_points"}]
    assert {"tool": "SearchKnowledge", "args": {"query": "transfer partners"}} in resolved


def test_cap_scope_is_left_alone():
    """CheckCap.cap_scope is rule-file vocabulary with no portfolio source, and
    is still open. Resolving card_key must not tempt a guess at the scope."""
    plan = [{"tool": "CheckCap", "args": {"card_key": None, "cap_scope": None}}]
    resolved = resolve_portfolio_args(plan, HELD)
    assert all(a["cap_scope"] is None for a in _args(resolved, "CheckCap"))


def test_malformed_entries_are_left_for_validation_to_report():
    plan = ["not a dict", {"no_tool_key": True}]
    assert resolve_portfolio_args(plan, HELD) == plan

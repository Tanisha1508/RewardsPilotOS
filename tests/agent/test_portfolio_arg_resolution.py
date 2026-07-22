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


def test_unrelated_tools_pass_through_untouched():
    """The resolver must not reinterpret args it has no portfolio basis for —
    currency and target_program are deliberately left open."""
    plan = [
        {"tool": "BestTransferPaths", "args": {"currency": None, "target_program": "airline"}},
        {"tool": "GetTransferRatios", "args": {"currency": None}},
        {"tool": "SearchKnowledge", "args": {"query": "transfer partners"}},
    ]
    assert resolve_portfolio_args(plan, HELD) == plan


def test_cap_scope_is_left_alone():
    """CheckCap.cap_scope is rule-file vocabulary with no portfolio source, and
    is still open. Resolving card_key must not tempt a guess at the scope."""
    plan = [{"tool": "CheckCap", "args": {"card_key": None, "cap_scope": None}}]
    resolved = resolve_portfolio_args(plan, HELD)
    assert all(a["cap_scope"] is None for a in _args(resolved, "CheckCap"))


def test_malformed_entries_are_left_for_validation_to_report():
    plan = ["not a dict", {"no_tool_key": True}]
    assert resolve_portfolio_args(plan, HELD) == plan

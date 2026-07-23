"""Unresolved input is a distinct tool status, not success-with-empty
(KNOWN_LIMITATIONS 24, Class B).

An unregistered currency or target program means the graph has no data — a gap
to report, not a confirmed absence of transfer options. Before this the
distinction lived only in the `no_transfer_data` field, so a reader that glanced
at an empty `paths`/`ratios`/`options` list could not tell "we couldn't identify
that" from "there's genuinely nothing". The Tool Registry now lifts it to a
`unresolved_input` status so the distinction is structural — it does not depend
on the Recommender inferring it. These tests hold that line.
"""

import pytest

from tools.portfolio.source import InMemoryPortfolioSource, acting_as, load_seed, set_source
from tools.registry import execute


@pytest.fixture(autouse=True)
def _seeded():
    seed = load_seed()
    set_source(InMemoryPortfolioSource(seed))
    with acting_as(seed["user_id"]):
        yield


UNREGISTERED = [
    ("GetTransferRatios", {"currency": "not_a_real_currency"}),
    ("BestTransferPaths", {"currency": "not_a_real_currency", "target_program": "skyhigh_airways"}),
    (
        "BestTransferPaths",
        {"currency": "hdfc_reward_points", "target_program": "not_a_real_program"},
    ),
    ("RedemptionOptions", {"goal": {"target_program": "not_a_real_program"}}),
]

REGISTERED = [
    ("GetTransferRatios", {"currency": "hdfc_reward_points"}),
    ("BestTransferPaths", {"currency": "hdfc_reward_points", "target_program": "turkish_miles"}),
    ("RedemptionOptions", {"goal": {"target_program": "skyhigh_airways"}}),
]


@pytest.mark.parametrize("tool,args", UNREGISTERED)
def test_unregistered_input_is_unresolved_not_success(tool, args):
    result = execute(tool, args)
    assert result.status == "unresolved_input", result.result


@pytest.mark.parametrize("tool,args", UNREGISTERED)
def test_the_reason_still_travels_in_the_payload(tool, args):
    """`unresolved_input` is not a failure: the payload is returned in full so
    the Recommender has the `no_transfer_data` text to render."""
    result = execute(tool, args)
    assert result.result is not None
    assert result.error is None
    assert result.result["no_transfer_data"]  # non-empty str or list


@pytest.mark.parametrize("tool,args", REGISTERED)
def test_registered_input_stays_success(tool, args):
    result = execute(tool, args)
    assert result.status == "success", result.result


def test_a_partial_redemption_result_is_success_not_unresolved():
    """One held currency reaches the target, another is unregistered. That is a
    real answer with a caveat — success, with the caveat riding in
    no_transfer_data — NOT unresolved."""
    from contracts.tools.graph_engine import RedemptionOptionsOutput

    # A portfolio-level output: options present AND a no_transfer_data entry.
    mixed = RedemptionOptionsOutput(
        target_program="skyhigh_airways",
        options=[],
        no_transfer_data=["newbank_altitude_miles unregistered"],
    )
    assert mixed.is_unresolved_input  # zero options + a gap → unresolved

    from contracts.tools.graph_engine import RedemptionOption, TransferPath

    with_option = RedemptionOptionsOutput(
        target_program="skyhigh_airways",
        options=[
            RedemptionOption(
                currency="voyager_points",
                target_program="skyhigh_airways",
                path=TransferPath(
                    nodes=["voyager_points", "skyhigh_airways"], cumulative_ratio=1.0
                ),
                balance=1000,
            )
        ],
        no_transfer_data=["newbank_altitude_miles unregistered"],
    )
    assert not with_option.is_unresolved_input  # has an option → success with caveat


def test_run_tools_routes_unresolved_input_into_graph_results():
    """The workflow must treat unresolved_input like a success for routing: the
    payload carries the reason the Recommender needs, so it belongs in
    graph_results, not dropped into errors."""
    from agents.state.schema import initial_state
    from agents.workflows.graph import run_tools

    state = initial_state("q", load_seed()["user_id"])
    state["plan"] = [
        {
            "tool": "BestTransferPaths",
            "args": {"currency": "hdfc_reward_points", "target_program": "not_a_real_program"},
        }
    ]
    run_tools(state)
    assert len(state["graph_results"]) == 1
    assert state["graph_results"][0]["no_transfer_data"]
    assert not state["errors"]

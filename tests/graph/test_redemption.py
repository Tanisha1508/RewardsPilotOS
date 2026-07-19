"""redemption_options: ranking, points required, null point-value handling."""

from contracts.api.verified_value import VerifiedValue
from contracts.tools.graph_engine import RedemptionGoal
from graph.builder.builder import load_seed_graph
from graph.optimization.redemption import redemption_options

SYNTH = "https://example.test/fixture-values"


def test_options_ranked_by_ratio(fixture_graph):
    output = redemption_options(
        fixture_graph,
        {"a_points": 50_000, "c_points": 10_000},
        RedemptionGoal(target_program="target_air", required_points=10_000),
    )
    assert len(output.options) == 1  # c_points has no path
    best = output.options[0]
    assert best.currency == "a_points"
    assert best.path.cumulative_ratio == 1.0
    assert best.points_required == 10_000
    assert best.balance_sufficient is True


def test_null_point_value_means_value_unknown(fixture_graph):
    output = redemption_options(
        fixture_graph,
        {"a_points": 5_000},
        RedemptionGoal(target_program="target_air", required_points=10_000),
    )
    option = output.options[0]
    assert option.value_status == "unknown"
    assert option.value_estimate_inr is None
    assert "ranked by transfer ratio only" in option.notes[0]
    assert option.balance_sufficient is False


def test_verified_point_value_computes_estimate(fixture_graph):
    values = {
        "a_points": VerifiedValue(value=0.5, status="verified", source=SYNTH, confidence=1.0)
    }
    output = redemption_options(
        fixture_graph,
        {"a_points": 50_000},
        RedemptionGoal(target_program="target_air", required_points=10_000),
        point_values=values,
    )
    option = output.options[0]
    assert option.value_status == "computed"
    assert option.value_estimate_inr == 5_000.0  # 10000 points * 0.5 INR


def test_goal_without_required_points(fixture_graph):
    output = redemption_options(
        fixture_graph, {"a_points": 1_000}, RedemptionGoal(target_program="target_air")
    )
    option = output.options[0]
    assert option.points_required is None
    assert option.balance_sufficient is None
    assert option.value_status == "unknown"


def test_unverified_paths_bubble_up(fixture_graph):
    output = redemption_options(
        fixture_graph, {"a_points": 1_000}, RedemptionGoal(target_program="u_air")
    )
    assert output.options == []
    assert output.unverified_paths_exist is True


def test_seed_portfolio_redemption():
    graph = load_seed_graph()
    output = redemption_options(
        graph,
        {"voyager_points": 30_000, "trailblazer_miles": 30_000},
        RedemptionGoal(target_program="skyhigh_airways", required_points=10_000),
    )
    assert [o.currency for o in output.options] == ["voyager_points", "trailblazer_miles"]
    assert output.options[0].points_required == 10_000  # ratio 1.0
    assert output.options[1].points_required == 20_000  # ratio 0.5

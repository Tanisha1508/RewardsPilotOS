"""best_transfer_paths against hand-computed fixtures and the shipped seed."""

import pytest

from contracts.api.verified_value import VerifiedValue
from graph.builder.builder import GraphSeedError, build_graph, load_seed_graph
from graph.models.records import GraphEdgeRecord
from graph.search.paths import best_transfer_paths, points_required_for
from tests.graph.conftest import node, transfer, unverified


def test_multi_hop_beats_direct(fixture_graph):
    result = best_transfer_paths(fixture_graph, "a_points", "target_air")
    assert [p.cumulative_ratio for p in result.paths] == [1.0, 0.8]
    assert result.paths[0].nodes == ["a_points", "b_points", "target_air"]
    assert result.paths[1].nodes == ["a_points", "target_air"]


def test_min_transfer_and_sources_flow_through(fixture_graph):
    result = best_transfer_paths(fixture_graph, "a_points", "target_air")
    assert result.paths[0].min_transfer == 2000  # first hop of the best path
    assert result.paths[1].min_transfer == 1000
    assert all(path.sources for path in result.paths)


def test_last_verified_is_oldest_on_path(fixture_graph):
    result = best_transfer_paths(fixture_graph, "a_points", "target_air")
    assert result.paths[1].last_verified == "2026-03-01"


def test_unverified_path_surfaced_without_ratio(fixture_graph):
    result = best_transfer_paths(fixture_graph, "a_points", "u_air")
    assert result.paths == []
    assert result.unverified_paths_exist is True
    assert "a_points -> u_air: ratio unverified" in result.unverified_notes[0]


def test_no_path_at_all(fixture_graph):
    result = best_transfer_paths(fixture_graph, "c_points", "target_air")
    assert result.paths == []
    assert result.unverified_paths_exist is False


def test_unknown_nodes_return_empty(fixture_graph):
    result = best_transfer_paths(fixture_graph, "ghost", "target_air")
    assert result.paths == []


def test_points_required_math():
    assert points_required_for(1.0, 10000, None) == 10000
    assert points_required_for(0.5, 10000, None) == 20000
    assert points_required_for(2.0, 10001, None) == 5001  # ceil
    assert points_required_for(1.0, 500, 2000) == 2000  # min transfer floor


def test_builder_rejects_unverified_transfer_in_verified_seed():
    nodes = [node("x", "currency"), node("y", "airline")]
    with pytest.raises(GraphSeedError, match="belong in the \\[NEED\\] register"):
        build_graph(nodes, [unverified("bad", "x", "y")])


def test_register_edge_may_carry_candidate_ratio_but_never_computes():
    nodes = [node("x", "currency"), node("y", "airline")]
    candidate = GraphEdgeRecord(
        edge_id="candidate",
        from_node="x",
        to_node="y",
        edge_type="transfer",
        ratio=VerifiedValue(
            value=2.0, status="unverified", source="third-party aggregator", confidence=0.5
        ),
        min_transfer=VerifiedValue.unknown(),
        notes="[NEED: confirm with official source]",
    )
    graph = build_graph(nodes, [], unverified_edges=[candidate])
    result = best_transfer_paths(graph, "x", "y")
    assert result.paths == []  # candidate ratios never enter path math
    assert result.unverified_paths_exist is True


def test_builder_rejects_verified_status_in_register():
    nodes = [node("x", "currency"), node("y", "airline")]
    bad = GraphEdgeRecord(
        edge_id="bad",
        from_node="x",
        to_node="y",
        edge_type="transfer",
        ratio=VerifiedValue(
            value=2.0, status="verified", source="https://example.test", confidence=0.9
        ),
        min_transfer=VerifiedValue.unknown(),
    )
    with pytest.raises(GraphSeedError, match="must stay status=unverified"):
        build_graph(nodes, [], unverified_edges=[bad])


def test_builder_rejects_unknown_node_reference():
    with pytest.raises(GraphSeedError, match="unknown node"):
        build_graph([node("x", "currency")], [transfer("e", "x", "ghost", 1.0)])


def test_seed_graph_loads_with_verified_synthetic_paths():
    graph = load_seed_graph()
    result = best_transfer_paths(graph, "voyager_points", "skyhigh_airways")
    assert len(result.paths) == 1
    assert result.paths[0].cumulative_ratio == 1.0
    assert result.paths[0].min_transfer == 2000


def test_seed_graph_amex_register_edges_still_unverified():
    graph = load_seed_graph()
    result = best_transfer_paths(graph, "membership_rewards", "singapore_krisflyer")
    assert result.paths == []
    assert result.unverified_paths_exist is True
    assert any("[NEED" in note for note in result.unverified_notes)


def test_seed_graph_axis_partners_verified():
    graph = load_seed_graph()
    expected_ratios = {
        "singapore_krisflyer": 2.0,  # 1:2 standard Group A
        "turkish_miles": 2.0,
        "ihg_one_rewards": 2.0,
        "british_airways_avios": 0.5,  # inverted 2:1
        "indigo_bluchip": 2.0,
        "radisson_rewards": 2.0,
        "orchid_rewards": 1.0,
    }
    for program, ratio in expected_ratios.items():
        result = best_transfer_paths(graph, "edge_miles", program)
        direct = [p for p in result.paths if len(p.nodes) == 2]
        assert direct, program
        assert direct[0].cumulative_ratio == ratio, program
        assert direct[0].min_transfer == 500, program


def test_seed_graph_no_edges_to_removed_axis_partners():
    graph = load_seed_graph()
    # Marriott/Accor removed as Atlas partners 2026-04-02: no DIRECT edge may
    # exist (multi-hop routes via other currencies are a different question).
    for program in ("marriott_bonvoy", "accor"):
        assert not graph.has_edge("edge_miles", program), program


def test_seed_graph_hdfc_all_seven_partners_verified():
    graph = load_seed_graph()
    expected_ratios = {
        "turkish_miles": 0.5,
        "accor": 0.5,
        "avianca_lifemiles": 0.5,
        "club_itc_green_points": 0.5,
        "air_india_flying_returns": 0.5,
        "marriott_bonvoy": 0.5,
        "singapore_krisflyer": 1.0,
    }
    for program, ratio in expected_ratios.items():
        result = best_transfer_paths(graph, "hdfc_reward_points", program)
        assert len(result.paths) == 1, program
        assert result.paths[0].cumulative_ratio == ratio, program
        assert result.unverified_paths_exist is False, program
    club_itc = best_transfer_paths(graph, "hdfc_reward_points", "club_itc_green_points")
    assert club_itc.paths[0].min_transfer == 100

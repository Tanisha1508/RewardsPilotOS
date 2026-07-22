"""Hand-built fixture graph with hand-computed best paths (BUILD_SPEC §7)."""

import pytest

from contracts.api.verified_value import VerifiedValue
from graph.builder.builder import build_graph
from graph.models.records import GraphEdgeRecord, GraphNodeRecord

SYNTH = "https://example.test/fixture-graph"


def node(node_id: str, node_type: str) -> GraphNodeRecord:
    return GraphNodeRecord(node_id=node_id, node_type=node_type, name=node_id, meta={})


def transfer(edge_id, from_node, to_node, ratio, min_transfer=None, last_verified="2026-06-01"):
    return GraphEdgeRecord(
        edge_id=edge_id,
        from_node=from_node,
        to_node=to_node,
        edge_type="transfer",
        ratio=VerifiedValue(value=ratio, status="verified", source=SYNTH, confidence=1.0),
        min_transfer=(
            VerifiedValue(value=min_transfer, status="verified", source=SYNTH, confidence=1.0)
            if min_transfer is not None
            else VerifiedValue.unknown()
        ),
        last_verified=last_verified,
    )


def unverified(edge_id, from_node, to_node, notes="[NEED: verify ratio]"):
    return GraphEdgeRecord(
        edge_id=edge_id,
        from_node=from_node,
        to_node=to_node,
        edge_type="transfer",
        ratio=VerifiedValue.unknown(),
        min_transfer=VerifiedValue.unknown(),
        notes=notes,
    )


@pytest.fixture()
def fixture_graph():
    """Hand-computed expectations:

    a_points -> target_air direct: ratio 0.8
    a_points -> b_points -> target_air: 0.5 * 2.0 = 1.0  (best)
    a_points -> u_air: unverified only ("unverified path exists")
    c_points -> target_air: no path at all
    """
    nodes = [
        node("a_points", "currency"),
        node("b_points", "currency"),
        node("c_points", "currency"),
        node("target_air", "airline"),
        node("u_air", "airline"),
    ]
    edges = [
        transfer(
            "a_direct", "a_points", "target_air", 0.8, min_transfer=1000, last_verified="2026-03-01"
        ),
        transfer("a_to_b", "a_points", "b_points", 0.5, min_transfer=2000),
        transfer("b_to_t", "b_points", "target_air", 2.0),
    ]
    return build_graph(nodes, edges, unverified_edges=[unverified("a_to_u", "a_points", "u_air")])

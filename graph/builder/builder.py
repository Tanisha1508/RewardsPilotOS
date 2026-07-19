"""Build the NetworkX transfer graph (BUILD_SPEC §7).

Sprint milestone loads from JSON seed files in database/seed/; D2 swaps the
record source for Postgres graph_nodes/graph_edges rows behind the same
`build_graph(nodes, edges)` interface.

The unverified-edge register (need_register.json) holds transfer relationships
whose ratios are not verified: they are loaded as `unverified_transfer` edges
so search can surface "unverified path exists". Since the 2026-07-19 spec
update they may carry a CANDIDATE ratio value with evidence confidence < 1
(e.g. from third-party aggregators, pending official confirmation), but they
must remain status=unverified and they never enter path math.
"""

import json
from pathlib import Path

import networkx as nx

from graph.models.records import GraphEdgeRecord, GraphNodeRecord

SEED_DIR = Path(__file__).resolve().parent.parent.parent / "database" / "seed"


class GraphSeedError(Exception):
    """Seed data violates graph integrity rules."""


def build_graph(
    nodes: list[GraphNodeRecord],
    edges: list[GraphEdgeRecord],
    unverified_edges: list[GraphEdgeRecord] | None = None,
) -> nx.DiGraph:
    graph = nx.DiGraph()
    for node in nodes:
        graph.add_node(node.node_id, node_type=node.node_type, name=node.name, meta=node.meta)
    for edge in edges:
        if edge.from_node not in graph or edge.to_node not in graph:
            raise GraphSeedError(f"edge {edge.edge_id} references unknown node")
        if edge.edge_type == "transfer" and not edge.ratio.is_usable:
            raise GraphSeedError(
                f"transfer edge {edge.edge_id} is not verified; unverified ratios "
                "belong in the [NEED] register, not in graph_edges"
            )
        graph.add_edge(
            edge.from_node,
            edge.to_node,
            edge_id=edge.edge_id,
            edge_type=edge.edge_type,
            ratio=edge.ratio,
            min_transfer=edge.min_transfer,
            notes=edge.notes,
            source_doc_id=edge.source_doc_id,
            last_verified=edge.last_verified,
        )
    for edge in unverified_edges or []:
        if edge.from_node not in graph or edge.to_node not in graph:
            raise GraphSeedError(f"unverified edge {edge.edge_id} references unknown node")
        if edge.ratio.status != "unverified":
            raise GraphSeedError(
                f"register edge {edge.edge_id} must stay status=unverified; a "
                "verified ratio belongs in graph_edges, not the [NEED] register"
            )
        graph.add_edge(
            edge.from_node,
            edge.to_node,
            edge_id=edge.edge_id,
            edge_type="unverified_transfer",
            ratio=edge.ratio,
            min_transfer=edge.min_transfer,
            notes=edge.notes,
            source_doc_id=edge.source_doc_id,
            last_verified=edge.last_verified,
        )
    return graph


def load_seed_graph(seed_dir: Path | None = None) -> nx.DiGraph:
    directory = seed_dir or SEED_DIR
    nodes = [
        GraphNodeRecord.model_validate(item)
        for item in json.loads((directory / "graph_nodes.json").read_text())
    ]
    edges = [
        GraphEdgeRecord.model_validate(item)
        for item in json.loads((directory / "graph_edges.json").read_text())
    ]
    register_path = directory / "need_register.json"
    unverified = []
    if register_path.exists():
        unverified = [
            GraphEdgeRecord.model_validate(item)
            for item in json.loads(register_path.read_text())
        ]
    return build_graph(nodes, edges, unverified)

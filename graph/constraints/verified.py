"""Verified-only filtering and minimum-transfer constraints (BUILD_SPEC §7)."""

import networkx as nx


def verified_transfer_view(graph: nx.DiGraph) -> nx.DiGraph:
    """Subgraph view containing only verified transfer edges (the only edges
    allowed in path computation)."""

    def edge_ok(u: str, v: str) -> bool:
        data = graph[u][v]
        return data["edge_type"] == "transfer" and data["ratio"].is_usable

    return nx.subgraph_view(graph, filter_edge=edge_ok)


def unverified_transfer_notes(graph: nx.DiGraph, source: str, target: str) -> list[str]:
    """Human-readable notes for unverified edges on any simple path between
    source and target (considering transfer + unverified_transfer edges)."""

    def any_transfer(u: str, v: str) -> bool:
        return graph[u][v]["edge_type"] in ("transfer", "unverified_transfer")

    view = nx.subgraph_view(graph, filter_edge=any_transfer)
    if source not in view or target not in view:
        return []
    notes: list[str] = []
    for path in nx.all_simple_paths(view, source, target, cutoff=4):
        for u, v in zip(path, path[1:]):
            data = graph[u][v]
            if data["edge_type"] == "unverified_transfer":
                note = f"{u} -> {v}: ratio unverified"
                if data.get("notes"):
                    note += f" ({data['notes']})"
                if note not in notes:
                    notes.append(note)
    return notes


def effective_min_transfer(graph: nx.DiGraph, path: list[str]) -> float | None:
    """Minimum points that must leave the first hop: the first edge's verified
    min_transfer, when known."""
    if len(path) < 2:
        return None
    first = graph[path[0]][path[1]]["min_transfer"]
    return float(first.value) if first.is_usable else None

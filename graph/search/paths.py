"""best_transfer_paths (BUILD_SPEC §7): ranked verified paths with cumulative
ratio; unverified routes surfaced as notes only."""

import math

import networkx as nx

from contracts.tools.graph_engine import BestTransferPathsOutput, TransferPath
from graph.constraints.verified import (
    effective_min_transfer,
    unverified_transfer_notes,
    verified_transfer_view,
)


def best_transfer_paths(
    graph: nx.DiGraph, currency: str, target_program: str, max_hops: int = 3
) -> BestTransferPathsOutput:
    output = BestTransferPathsOutput(currency=currency, target_program=target_program)
    output.unverified_notes = unverified_transfer_notes(graph, currency, target_program)
    output.unverified_paths_exist = bool(output.unverified_notes)
    if currency not in graph or target_program not in graph:
        return output

    verified = verified_transfer_view(graph)
    paths: list[TransferPath] = []
    for node_path in nx.all_simple_paths(verified, currency, target_program, cutoff=max_hops):
        ratio = 1.0
        sources: list[str] = []
        verified_dates: list[str] = []
        for u, v in zip(node_path, node_path[1:]):
            data = graph[u][v]
            ratio *= float(data["ratio"].value)
            if data["ratio"].source:
                sources.append(data["ratio"].source)
            if data.get("last_verified"):
                verified_dates.append(data["last_verified"])
        paths.append(
            TransferPath(
                nodes=list(node_path),
                cumulative_ratio=round(ratio, 6),
                min_transfer=effective_min_transfer(graph, list(node_path)),
                sources=sources,
                last_verified=min(verified_dates) if verified_dates else None,
            )
        )
    paths.sort(key=lambda p: (-p.cumulative_ratio, len(p.nodes)))
    output.paths = paths
    return output


def points_required_for(path_ratio: float, required_points: float, min_transfer: float | None) -> float:
    """Source points needed to yield `required_points` in the target program,
    honoring the first-hop minimum transfer."""
    needed = math.ceil(required_points / path_ratio)
    if min_transfer is not None:
        needed = max(needed, math.ceil(min_transfer))
    return float(needed)

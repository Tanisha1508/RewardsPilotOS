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


def missing_node_reason(graph: nx.DiGraph, currency: str, target_program: str) -> str | None:
    """Why the graph cannot answer at all, or None if it can.

    "No verified route exists" and "we hold no data on this currency" are
    different answers that both produce zero paths. Only the first is a finding;
    the second means the currency was never registered in the graph, and
    reporting it as "no options" is the ADR-010/011 failure mode — a vocabulary
    gap presenting as a result.
    """
    missing = [
        label
        for label, node in (("currency", currency), ("target program", target_program))
        if node not in graph
    ]
    if not missing:
        return None
    described = " and ".join(
        f"{label} {node!r}"
        for label, node in (("currency", currency), ("target program", target_program))
        if node not in graph
    )
    return (
        f"no transfer data: {described} "
        f"{'is' if len(missing) == 1 else 'are'} not registered in the transfer "
        f"graph. This is missing data, not an absence of transfer routes — the "
        f"graph holds no edges for it either way."
    )


def best_transfer_paths(
    graph: nx.DiGraph, currency: str, target_program: str, max_hops: int = 3
) -> BestTransferPathsOutput:
    output = BestTransferPathsOutput(currency=currency, target_program=target_program)
    output.unverified_notes = unverified_transfer_notes(graph, currency, target_program)
    output.unverified_paths_exist = bool(output.unverified_notes)
    output.no_transfer_data = missing_node_reason(graph, currency, target_program)
    if output.no_transfer_data is not None:
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


def points_required_for(
    path_ratio: float, required_points: float, min_transfer: float | None
) -> float:
    """Source points needed to yield `required_points` in the target program,
    honoring the first-hop minimum transfer."""
    needed = math.ceil(required_points / path_ratio)
    if min_transfer is not None:
        needed = max(needed, math.ceil(min_transfer))
    return float(needed)

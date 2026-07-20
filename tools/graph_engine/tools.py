"""Graph Engine tools: BestTransferPaths, RedemptionOptions, GetTransferRatios."""

from functools import lru_cache

import networkx as nx

from contracts.tools.graph_engine import (
    BestTransferPathsInput,
    BestTransferPathsOutput,
    RedemptionOptionsInput,
    RedemptionOptionsOutput,
)
from contracts.tools.transfer_ratios import (
    GetTransferRatiosInput,
    GetTransferRatiosOutput,
    TransferRatio,
)
from graph.builder.builder import load_seed_graph
from graph.optimization.redemption import redemption_options as _redemption_options
from graph.search.paths import best_transfer_paths as _best_transfer_paths
from tools.reward_calculator.values import get_point_values


@lru_cache(maxsize=1)
def _graph() -> nx.DiGraph:
    return load_seed_graph()


def best_transfer_paths(args: BestTransferPathsInput) -> BestTransferPathsOutput:
    return _best_transfer_paths(_graph(), args.currency, args.target_program, args.max_hops)


def redemption_options(args: RedemptionOptionsInput) -> RedemptionOptionsOutput:
    portfolio = args.portfolio
    if portfolio is None:
        # The contract says the tool loads the user's own balances when the
        # caller omits them. Since D2 that means a real read for the user in
        # context — not a fixture portfolio, which would answer a real question
        # with someone else's numbers.
        from tools.portfolio.source import current_user, get_source

        balances = get_source().balances(current_user()).balances
        portfolio = {b.reward_currency: b.current_balance for b in balances}
    point_values = get_point_values(list(portfolio))
    return _redemption_options(_graph(), portfolio, args.goal, point_values)


def get_transfer_ratios(args: GetTransferRatiosInput) -> GetTransferRatiosOutput:
    graph = _graph()
    output = GetTransferRatiosOutput(currency=args.currency)
    if args.currency not in graph:
        # An unregistered currency has no partners *and* no data. Saying only
        # "no partners" would present the gap as a finding.
        output.no_transfer_data = (
            f"no transfer data: currency {args.currency!r} is not registered in the "
            f"transfer graph. This is missing data, not a confirmed absence of "
            f"transfer partners."
        )
        return output
    for _, target, data in graph.out_edges(args.currency, data=True):
        if data["edge_type"] == "transfer" and data["ratio"].is_usable:
            output.ratios.append(
                TransferRatio(
                    from_currency=args.currency,
                    to_program=target,
                    ratio=data["ratio"],
                    min_transfer=data["min_transfer"],
                    last_verified=data.get("last_verified"),
                    source_doc_id=data.get("source_doc_id"),
                )
            )
        elif data["edge_type"] == "unverified_transfer":
            output.unverified_partners.append(
                f"{target}: ratio unverified ({data.get('notes') or 'no notes'})"
            )
    return output

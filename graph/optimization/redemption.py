"""redemption_options (BUILD_SPEC §7): ranked options with points required.

Point-value math is delegated to Rule Engine value tables
(point_value_reference_inr per reward currency, per redemption channel since
the 2026-07-19 spec update). The channel is selected from the goal's
redemption_type. When the selected channel's value is null/unverified, the
option is ranked by ratio only and value is labeled unknown — never
estimated."""

import networkx as nx

from contracts.api.verified_value import PointValueReference, VerifiedValue
from contracts.tools.graph_engine import (
    RedemptionGoal,
    RedemptionOption,
    RedemptionOptionsOutput,
)
from graph.search.paths import best_transfer_paths, points_required_for


def redemption_options(
    graph: nx.DiGraph,
    portfolio: dict[str, float],
    goal: RedemptionGoal,
    point_values: dict[str, PointValueReference] | None = None,
) -> RedemptionOptionsOutput:
    point_values = point_values or {}
    output = RedemptionOptionsOutput(target_program=goal.target_program)
    for currency, balance in portfolio.items():
        search = best_transfer_paths(graph, currency, goal.target_program)
        if search.unverified_paths_exist:
            output.unverified_paths_exist = True
            for note in search.unverified_notes:
                if note not in output.unverified_notes:
                    output.unverified_notes.append(note)
        if search.no_transfer_data is not None:
            # Distinct from "no route found": this currency is absent from the
            # graph, so silence here would report a data gap as a conclusion.
            if search.no_transfer_data not in output.no_transfer_data:
                output.no_transfer_data.append(search.no_transfer_data)
            continue
        if not search.paths:
            continue
        best = search.paths[0]
        reference = point_values.get(currency, PointValueReference.unknown())
        channel_value = reference.for_channel(goal.redemption_type)
        no_single_value = channel_value is None  # confirmed: no single figure
        option = RedemptionOption(
            currency=currency,
            target_program=goal.target_program,
            path=best,
            balance=balance,
            value_channel=goal.redemption_type,
            point_value_reference_inr=channel_value or VerifiedValue.unknown(),
        )
        if goal.required_points is not None:
            option.points_required = points_required_for(
                best.cumulative_ratio, goal.required_points, best.min_transfer
            )
            option.balance_sufficient = balance >= option.points_required
        value = option.point_value_reference_inr
        if value.is_usable and option.points_required is not None:
            option.value_estimate_inr = round(option.points_required * float(value.value), 2)
            option.value_status = "computed"
        else:
            option.value_status = "unknown"
            if no_single_value:
                option.notes.append(
                    f"no single {goal.redemption_type} point value exists for "
                    f"{currency} (value is tier- or partner-dependent); ranked by "
                    "transfer ratio only"
                )
            else:
                option.notes.append(
                    f"{goal.redemption_type} point value for {currency} is "
                    f"{value.status}; ranked by transfer ratio only, value unknown"
                )
        output.options.append(option)
    output.options.sort(key=lambda o: -o.path.cumulative_ratio)
    return output

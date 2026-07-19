"""Tool Registry (BUILD_SPEC §8, MASTER_SPEC ch. 21).

Every deterministic capability is exposed here. Each tool declares name,
description, input schema, output schema (Pydantic models from contracts/),
and timeout. Execution validates input args against the input schema and
rejects anything malformed; results are returned in the standard tool
envelope (status/result/latency). Tools never retry (they are deterministic);
failures return structured errors for graceful degradation."""

import time
from dataclasses import dataclass
from typing import Callable

from pydantic import BaseModel, ValidationError

from contracts.tools.graph_engine import (
    BestTransferPathsInput,
    BestTransferPathsOutput,
    RedemptionOptionsInput,
    RedemptionOptionsOutput,
)
from contracts.tools.knowledge_search import SearchKnowledgeInput, SearchKnowledgeOutput
from contracts.tools.memory import (
    RecallMemoryInput,
    RecallMemoryOutput,
    StorePreferenceInput,
    StorePreferenceOutput,
)
from contracts.tools.opportunity import GetOpportunitiesInput, GetOpportunitiesOutput
from contracts.tools.portfolio import (
    GetCardsOutput,
    GetPortfolioOutput,
    GetRewardBalancesOutput,
    GetTravelGoalsOutput,
    UserScopedInput,
)
from contracts.tools.rule_engine import (
    CalculateEarnInput,
    CapStatus,
    CheckCapInput,
    CompareCardsInput,
    EarnResult,
)
from contracts.tools.transfer_ratios import GetTransferRatiosInput, GetTransferRatiosOutput
from tools.graph_engine.tools import best_transfer_paths, get_transfer_ratios, redemption_options
from tools.knowledge_search.tools import (
    GetPromotionsInput,
    GetPromotionsOutput,
    get_promotions,
    search_knowledge,
)
from tools.memory.tools import recall_memory, store_preference
from tools.opportunity_engine.tools import get_opportunities
from tools.portfolio.tools import get_cards, get_portfolio, get_reward_balances, get_travel_goals
from tools.rule_engine.tools import CompareCardsOutput, calculate_earn, check_cap, compare_cards


class ToolNotFoundError(Exception):
    pass


class ToolInputError(Exception):
    """Args rejected by the tool's input schema."""


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    category: str  # portfolio | rules | graph | knowledge | memory | opportunity
    input_model: type[BaseModel]
    output_model: type[BaseModel]
    handler: Callable
    timeout_s: float = 10.0


@dataclass
class ToolResult:
    status: str  # success | failed
    tool: str
    result: dict | None
    error: str | None
    latency_ms: float


REGISTRY: dict[str, ToolSpec] = {
    spec.name: spec
    for spec in [
        ToolSpec(
            "GetPortfolio",
            "Retrieve the user's portfolio and cards",
            "portfolio",
            UserScopedInput,
            GetPortfolioOutput,
            get_portfolio,
        ),
        ToolSpec(
            "GetCards",
            "Retrieve the user's cards",
            "portfolio",
            UserScopedInput,
            GetCardsOutput,
            get_cards,
        ),
        ToolSpec(
            "GetRewardBalances",
            "Retrieve current reward balances per card",
            "portfolio",
            UserScopedInput,
            GetRewardBalancesOutput,
            get_reward_balances,
        ),
        ToolSpec(
            "GetTravelGoals",
            "Retrieve the user's travel goals",
            "portfolio",
            UserScopedInput,
            GetTravelGoalsOutput,
            get_travel_goals,
        ),
        ToolSpec(
            "SearchKnowledge",
            "Hybrid retrieval over the verified knowledge corpus",
            "knowledge",
            SearchKnowledgeInput,
            SearchKnowledgeOutput,
            search_knowledge,
        ),
        ToolSpec(
            "GetPromotions",
            "Retrieve current promotions from the knowledge corpus",
            "knowledge",
            GetPromotionsInput,
            GetPromotionsOutput,
            get_promotions,
        ),
        ToolSpec(
            "GetTransferRatios",
            "Verified outbound transfer ratios for a reward currency",
            "graph",
            GetTransferRatiosInput,
            GetTransferRatiosOutput,
            get_transfer_ratios,
        ),
        ToolSpec(
            "CalculateEarn",
            "Deterministic reward earn calculation for one card",
            "rules",
            CalculateEarnInput,
            EarnResult,
            calculate_earn,
        ),
        ToolSpec(
            "CheckCap",
            "Monthly cap status for a card and cap scope",
            "rules",
            CheckCapInput,
            CapStatus,
            check_cap,
        ),
        ToolSpec(
            "CompareCards",
            "Compare earn across cards, sorted best first",
            "rules",
            CompareCardsInput,
            CompareCardsOutput,
            compare_cards,
        ),
        ToolSpec(
            "BestTransferPaths",
            "Ranked verified transfer paths between currency and program",
            "graph",
            BestTransferPathsInput,
            BestTransferPathsOutput,
            best_transfer_paths,
        ),
        ToolSpec(
            "RedemptionOptions",
            "Ranked redemption options for a portfolio and goal",
            "graph",
            RedemptionOptionsInput,
            RedemptionOptionsOutput,
            redemption_options,
        ),
        ToolSpec(
            "RecallMemory",
            "Recall preferences and relevant episodic events",
            "memory",
            RecallMemoryInput,
            RecallMemoryOutput,
            recall_memory,
        ),
        ToolSpec(
            "StorePreference",
            "Store a durable user preference",
            "memory",
            StorePreferenceInput,
            StorePreferenceOutput,
            store_preference,
        ),
        ToolSpec(
            "GetOpportunities",
            "Active opportunities from the Opportunity Engine",
            "opportunity",
            GetOpportunitiesInput,
            GetOpportunitiesOutput,
            get_opportunities,
        ),
    ]
}


def get_tool(name: str) -> ToolSpec:
    if name not in REGISTRY:
        raise ToolNotFoundError(f"unknown tool '{name}'")
    return REGISTRY[name]


def validate_args(name: str, args: dict) -> BaseModel:
    spec = get_tool(name)
    try:
        return spec.input_model.model_validate(args)
    except ValidationError as exc:
        raise ToolInputError(f"{name}: invalid args: {exc}") from exc


def execute(name: str, args: dict) -> ToolResult:
    """Validate, run, and wrap a tool call. Never raises on handler failure —
    returns a structured error so the workflow can degrade gracefully."""
    started = time.monotonic()
    try:
        spec = get_tool(name)
        parsed = validate_args(name, args)
    except (ToolNotFoundError, ToolInputError) as exc:
        return ToolResult("failed", name, None, str(exc), _ms(started))
    try:
        output = spec.handler(parsed)
        validated = spec.output_model.model_validate(output.model_dump())
        return ToolResult("success", name, validated.model_dump(), None, _ms(started))
    except Exception as exc:  # deterministic tools: no retry, structured error
        return ToolResult("failed", name, None, f"{type(exc).__name__}: {exc}", _ms(started))


def _ms(started: float) -> float:
    return round((time.monotonic() - started) * 1000, 2)

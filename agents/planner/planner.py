"""Planner node (BUILD_SPEC §8): Gemini call that classifies intent, extracts
entities, and emits a deterministic tool plan of ToolInvocation objects.

Every plan entry is validated against the Tool Registry input schemas before
it enters the state; malformed entries are rejected and recorded in errors.
"""

import json
from pathlib import Path

from agents.planner.empty_portfolio import (
    CARD_DEPENDENT_INTENTS,
    empty_portfolio_recommendation,
    held_cards,
)
from agents.planner.portfolio_args import resolve_portfolio_args
from agents.registry import LLM, LLMUnavailableError, complete_with_retry
from agents.state.schema import AgentState, ToolInvocation
from tools.registry import REGISTRY, ToolInputError, ToolNotFoundError, validate_args

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "planner.md"

VALID_INTENTS = ("spend", "transfer", "redeem", "portfolio", "general")


def tool_catalog() -> str:
    lines = []
    for spec in REGISTRY.values():
        fields = spec.input_model.model_json_schema().get("properties", {})
        args = ", ".join(fields)
        lines.append(f"- {spec.name} ({spec.category}): {spec.description}. Args: {args}")
    return "\n".join(lines)


def _parse_payload(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)


def validate_plan(plan_entries: list, errors: list[str]) -> list[ToolInvocation]:
    """Reject anything that is not an exact registry tool with schema-valid
    args. The Planner emits ToolInvocation objects, never free-form strings."""
    plan: list[ToolInvocation] = []
    for entry in plan_entries:
        if not isinstance(entry, dict) or "tool" not in entry:
            errors.append(f"planner: malformed plan entry rejected: {entry!r}")
            continue
        name = entry["tool"]
        args = entry.get("args") or {}
        if not isinstance(args, dict):
            errors.append(f"planner: non-dict args rejected for {name}")
            continue
        try:
            validate_args(name, args)
        except (ToolNotFoundError, ToolInputError) as exc:
            errors.append(f"planner: rejected invocation: {exc}")
            continue
        plan.append(ToolInvocation(tool=name, args=args))
    return plan


def plan(state: AgentState, llm: LLM) -> AgentState:
    system = PROMPT_PATH.read_text().replace("{TOOL_CATALOG}", tool_catalog())
    # Only the query. The model is deliberately not told the user id: no tool
    # accepts one any more (KNOWN_LIMITATIONS 24, Class C), and handing it an
    # identity it cannot legitimately use invites it back into plan args.
    user = json.dumps({"query": state["query"]})
    try:
        raw = complete_with_retry(llm, system, user)
        payload = _parse_payload(raw)
    except (LLMUnavailableError, json.JSONDecodeError) as exc:
        state["errors"].append(f"planner: {exc}")
        state["intent"] = "general"
        state["plan"] = []
        return state
    intent = payload.get("intent")
    state["intent"] = intent if intent in VALID_INTENTS else "general"
    raw_plan = payload.get("plan") or []

    # Card-dependent intents need the held cards (D4): fetched once, used for both
    # the empty gate and portfolio-derived arg resolution. Resolution happens
    # BEFORE validation: a model that correctly declines to guess card_keys emits
    # CompareCards with an empty `cards` list (and CalculateEarn/CheckCap with no
    # card_key at all), which validation would reject — so the keys must be filled
    # in first, or the computation is lost entirely (the exact D4 live-/chat
    # failure, and its Class B recurrence on the single-card tools).
    if state["intent"] in CARD_DEPENDENT_INTENTS:
        cards = held_cards()
        if not cards:
            # Nothing to compute against an empty set — deterministic direct
            # response, routed straight to END (skips tools and the recommender).
            state["plan"] = []
            state["recommendation"] = empty_portfolio_recommendation()
            state["confidence"] = state["recommendation"]["confidence"]["level"]
            state["citations"] = []
            return state
        raw_plan = resolve_portfolio_args(raw_plan, cards)

    state["plan"] = validate_plan(raw_plan, state["errors"])
    return state

"""Planner node (BUILD_SPEC §8): Gemini call that classifies intent, extracts
entities, and emits a deterministic tool plan of ToolInvocation objects.

Every plan entry is validated against the Tool Registry input schemas before
it enters the state; malformed entries are rejected and recorded in errors.
"""

import json
from pathlib import Path

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
    user = json.dumps({"query": state["query"], "user_id": state["user_id"]})
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
    state["plan"] = validate_plan(payload.get("plan") or [], state["errors"])
    return state

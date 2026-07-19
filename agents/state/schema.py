"""Shared LangGraph state schema (BUILD_SPEC §8) — exactly the documented
contract. The Planner emits ToolInvocation objects, never free-form strings."""

from typing import TypedDict

from contracts.api.recommendation import Citation
from contracts.tools.knowledge_search import RetrievedChunk


class ToolInvocation(TypedDict):
    tool: str  # exact name from the Tool Registry
    args: dict  # validated against the tool's input schema


class AgentState(TypedDict):
    query: str
    user_id: str
    intent: str  # spend | transfer | redeem | portfolio | general
    plan: list[ToolInvocation]  # deterministic tool call plan from Planner
    portfolio: dict | None
    preferences: dict | None
    knowledge: list[RetrievedChunk]
    rule_results: list[dict]
    graph_results: list[dict]
    memory: dict  # episodic recall relevant to query
    recommendation: dict | None  # final structured output
    citations: list[Citation]
    confidence: str
    errors: list[str]


def initial_state(query: str, user_id: str) -> AgentState:
    return AgentState(
        query=query,
        user_id=user_id,
        intent="general",
        plan=[],
        portfolio=None,
        preferences=None,
        knowledge=[],
        rule_results=[],
        graph_results=[],
        memory={},
        recommendation=None,
        citations=[],
        confidence="low",
        errors=[],
    )

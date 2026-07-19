"""LangGraph workflow (BUILD_SPEC §8):

    planner → (conditional) tool executor → recommender → END

Tool nodes are thin wrappers over the Tool Registry: deterministic, no
retries; failures append to state.errors and execution continues (graceful
degradation). The conditional edge skips tool execution when the Planner
produced no plan."""

from langgraph.graph import END, StateGraph

from agents.planner.planner import plan as planner_node
from agents.recommendation.recommender import recommend as recommender_node
from agents.registry import LLM
from agents.state.schema import AgentState
from contracts.tools.knowledge_search import RetrievedChunk
from tools.registry import execute


def run_tools(state: AgentState) -> AgentState:
    """Execute the Planner's ToolInvocation plan in order, appending results
    into the state channel that matches each tool's category."""
    for invocation in state["plan"]:
        result = execute(invocation["tool"], invocation["args"])
        if result.status == "failed":
            state["errors"].append(f"{invocation['tool']}: {result.error}")
            continue
        payload = result.result or {}
        name = invocation["tool"]
        if name in ("CalculateEarn", "CheckCap"):
            state["rule_results"].append({"tool": name, **payload})
        elif name == "CompareCards":
            for entry in payload.get("results", []):
                state["rule_results"].append({"tool": name, **entry})
        elif name in ("BestTransferPaths", "RedemptionOptions", "GetTransferRatios"):
            state["graph_results"].append({"tool": name, **payload})
        elif name in ("SearchKnowledge", "GetPromotions"):
            for chunk in payload.get("chunks") or payload.get("promotions") or []:
                state["knowledge"].append(RetrievedChunk.model_validate(chunk))
        elif name == "GetPortfolio":
            state["portfolio"] = payload
        elif name in ("GetCards", "GetRewardBalances", "GetTravelGoals"):
            portfolio = state["portfolio"] or {}
            portfolio.update(payload)
            state["portfolio"] = portfolio
        elif name == "RecallMemory":
            state["preferences"] = payload.get("preferences", {})
            state["memory"] = {"episodic": payload.get("episodic", [])}
        elif name == "GetOpportunities":
            state["memory"] = {**state["memory"], "opportunities": payload.get("opportunities", [])}
        else:  # StorePreference and future tools: keep raw result in memory
            state["memory"] = {**state["memory"], name: payload}
    return state


def _route_after_planner(state: AgentState) -> str:
    return "tools" if state["plan"] else "recommender"


def build_workflow(llm: LLM):
    graph = StateGraph(AgentState)
    graph.add_node("planner", lambda state: planner_node(state, llm))
    graph.add_node("tools", run_tools)
    graph.add_node("recommender", lambda state: recommender_node(state, llm))
    graph.set_entry_point("planner")
    graph.add_conditional_edges(
        "planner", _route_after_planner, {"tools": "tools", "recommender": "recommender"}
    )
    graph.add_edge("tools", "recommender")
    graph.add_edge("recommender", END)
    return graph.compile()

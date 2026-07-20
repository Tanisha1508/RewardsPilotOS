"""Demo: one query answered end to end through LangGraph on fixture data.

Uses Gemini when GEMINI_API_KEY is set. Without a key it falls back to a
deterministic scripted LLM (clearly announced) so the workflow, tool
execution, validation, and citation machinery run identically — the scripted
LLM obeys the same hard rules: numbers verbatim from tool results, unknowns
stated plainly.

Run: python -m agents.workflows.demo
"""

import json
import os

from agents.registry import LLMUnavailableError
from agents.state.schema import initial_state
from agents.workflows.graph import build_workflow

DEMO_QUERY = (
    "I want an award flight on Skyhigh Airways. Should I transfer my Voyager "
    "Points, and how do my HDFC Infinia points compare?"
)


class ScriptedLLM:
    """Deterministic stand-in obeying the Recommender hard rules. Dispatches
    on the system prompt (planner vs recommender)."""

    def complete(self, system: str, user: str) -> str:
        if "Planner prompt" in system:
            return json.dumps(
                {
                    "intent": "transfer",
                    "entities": {
                        "currency": "voyager_points",
                        "target_program": "skyhigh_airways",
                    },
                    "plan": [
                        {"tool": "GetPortfolio", "args": {"user_id": "fixture_user"}},
                        {"tool": "GetRewardBalances", "args": {"user_id": "fixture_user"}},
                        {
                            "tool": "RecallMemory",
                            "args": {
                                "user_id": "fixture_user",
                                "intent": "transfer",
                                "query": "skyhigh transfer",
                            },
                        },
                        {
                            "tool": "BestTransferPaths",
                            "args": {
                                "currency": "voyager_points",
                                "target_program": "skyhigh_airways",
                            },
                        },
                        {
                            "tool": "BestTransferPaths",
                            "args": {
                                "currency": "hdfc_reward_points",
                                "target_program": "skyhigh_airways",
                            },
                        },
                        {
                            "tool": "RedemptionOptions",
                            "args": {
                                "goal": {
                                    "target_program": "skyhigh_airways",
                                    "required_points": 10000,
                                }
                            },
                        },
                        {
                            "tool": "SearchKnowledge",
                            "args": {
                                "query": "transfer Voyager Points to Skyhigh Airways ratio minimum",
                            },
                        },
                        {"tool": "GetPromotions", "args": {"issuer": "demo_bank"}},
                    ],
                }
            )
        # Recommender: assemble contract-exact output from the state digest.
        state = json.loads(user.split("\n\nYour previous output was rejected")[0])
        calculations = list(state["rule_results"]) + list(state["graph_results"])
        citations = [
            {
                "source_url": chunk["metadata"]["source_url"],
                "last_changed": chunk["metadata"]["last_changed"],
                "doc_id": chunk["metadata"]["doc_id"],
            }
            for chunk in state["knowledge"]
        ]
        deduped = [dict(t) for t in {tuple(sorted(c.items())) for c in citations}]
        unknown_notes = [
            note for result in state["graph_results"] for note in result.get("unverified_notes", [])
        ]
        decision = (
            "Transfer Voyager Points to Skyhigh Airways using the verified 1:1 "
            "path (minimum transfer applies; see calculations). Whether your "
            "HDFC Infinia points can reach Skyhigh Airways is UNKNOWN: no "
            "verified transfer path exists, only unverified candidates pending "
            "issuer verification."
        )
        return json.dumps(
            {
                "decision": decision,
                "reasoning": [
                    "The Graph Engine found a verified voyager_points -> "
                    "skyhigh_airways path; its ratio and minimum are in the "
                    "calculations, copied verbatim from graph_results.",
                    "For hdfc_reward_points no verified path exists; the "
                    "system refuses to guess ratios (unknown over incorrect).",
                    "Retrieved knowledge and the active fixture promotion are "
                    "cited below with freshness timestamps.",
                ]
                + (
                    [f"Unverified paths noted: {'; '.join(unknown_notes[:3])}"]
                    if unknown_notes
                    else []
                ),
                "calculations": calculations,
                "citations": deduped,
                "confidence": {
                    "level": "medium",
                    "reason": "Voyager path fully verified (synthetic fixture "
                    "sources); HDFC transfer options unknown pending "
                    "verification.",
                },
                "assumptions": [
                    "Fixture balances are current as of their last_updated dates.",
                    "Award pricing on Skyhigh Airways is taken from the goal "
                    "(10000 points), not live availability.",
                ],
                "alternatives": [
                    "Wait for HDFC transfer partners to be verified before " "moving points.",
                    # No ratio quoted here: Trailblazer Miles were not queried
                    # for this goal, so no verified ratio is in the tool
                    # results and stating one would be ungrounded.
                    "Check Trailblazer Miles as a source if the Voyager "
                    "balance is insufficient.",
                ],
            }
        )


def main() -> dict:
    if os.environ.get("GEMINI_API_KEY"):
        from agents.registry import GeminiClient

        try:
            llm = GeminiClient()
            print("Using Gemini:", os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"))
        except LLMUnavailableError as exc:
            print(f"Gemini unavailable ({exc}); using deterministic scripted LLM")
            llm = ScriptedLLM()
    else:
        print("GEMINI_API_KEY not set; using deterministic scripted LLM fallback")
        llm = ScriptedLLM()

    workflow = build_workflow(llm)
    final = workflow.invoke(initial_state(DEMO_QUERY, "fixture_user"))

    print("\n=== Query ===\n" + DEMO_QUERY)
    print("\n=== Intent ===\n" + final["intent"])
    print("\n=== Recommendation ===")
    print(json.dumps(final["recommendation"], indent=2, default=str))
    print("\n=== Confidence ===\n" + final["confidence"])
    if final["errors"]:
        print("\n=== Errors (graceful degradation) ===")
        for error in final["errors"]:
            print("-", error)
    return final


if __name__ == "__main__":
    main()

"""Chat orchestration: run the LangGraph workflow for a user and persist the
result (BUILD_SPEC §8, §9).

This is the seam D2 was built for. The workflow's tools read the *ambient*
user's data (`tools/portfolio/source.py`), so the whole run is wrapped in
`acting_as(user_id)` — without it, `RedemptionOptions`'s "load the caller's own
balances" path has no user and raises. The portfolio and memory sources default
to Postgres, so a real logged-in user's real cards drive the recommendation.

No business logic lives here (BUILD_SPEC §3): the reasoning is the workflow's,
the numbers are the engines'. This layer runs the graph, persists what it
produced verbatim, and hands it back.
"""

import uuid

from agents.registry import LLMUnavailableError, default_llm
from agents.state.schema import initial_state
from agents.workflows.graph import build_workflow
from backend.application.errors import ApplicationError
from backend.models.intelligence import InteractionEvent, Recommendation
from database.postgres.session import session_scope
from tools.portfolio.source import acting_as


class RecommendationUnavailableError(ApplicationError):
    """The workflow could not produce a recommendation (LLM failed, or output
    failed the contract after a retry). Mapped to HTTP 502."""

    code = "recommendation_unavailable"


def run_chat(user_id: uuid.UUID, query: str) -> Recommendation:
    try:
        llm = default_llm()
    except LLMUnavailableError as exc:
        raise RecommendationUnavailableError(str(exc)) from exc

    workflow = build_workflow(llm)
    # Ambient user for the tools that load the caller's own data.
    with acting_as(str(user_id)):
        final = workflow.invoke(initial_state(query, str(user_id)))

    recommendation = final.get("recommendation")
    if recommendation is None:
        # The recommender failed gracefully (recommendation=None) rather than
        # returning something uncited or with invented numbers. Surface that as
        # a service error, not a persisted empty recommendation.
        reason = "; ".join(final.get("errors") or []) or "no recommendation produced"
        raise RecommendationUnavailableError(reason)

    with session_scope() as session:
        row = Recommendation(
            user_id=user_id,
            query=query,
            recommendation_json=recommendation,
            confidence=final.get("confidence"),
            citations_json=recommendation.get("citations", []),
            status="generated",
        )
        session.add(row)
        # Episodic memory: the question the user asked is part of their history
        # (BUILD_SPEC §4, interaction_events).
        session.add(
            InteractionEvent(
                user_id=user_id,
                event_type="chat_query",
                payload_json={"query": query, "intent": final.get("intent")},
            )
        )
        session.flush()
        session.expunge(row)
        return row

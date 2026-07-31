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


class DailyLimitReachedError(ApplicationError):
    """This user has had their share of today's answers (A2). Mapped to 429.

    Deliberately a *per-user* limit on a *shared* resource. The free Gemini tier
    allows 20 requests per day per model and a question costs two of them, so
    roughly ten questions a day exist for everybody put together (measured
    2026-07-31). Without this, the first person to ask eleven questions takes
    the day from every other user — and nobody else sees a rate limit, they see
    a product that has stopped working.
    """

    code = "daily_limit_reached"


def answers_used_today(user_id: uuid.UUID) -> int:
    """How many answers this user has already been given today (UTC).

    Counts stored recommendations rather than attempts, which is a deliberate
    under-count: a question whose workflow failed consumed provider quota but
    produced nothing, and is not charged to the user. Being lenient in the
    user's favour is the right side to err on for a limit whose whole purpose is
    fairness, and the alternative costs more than it is worth — recording an
    attempt row would mean writing to `interaction_events`, which is also the
    episodic memory the recommender reads back (`recent_events` takes the five
    most recent rows *of any type*). Attempt rows would crowd real history out
    of that window and change the answers themselves.

    UTC midnight, not the provider's reset (Pacific): this limit shares out
    capacity between users, it does not mirror Google's accounting. UTC also
    lands at 5:30am IST, which is a reasonable time for a daily reset here.
    """
    from datetime import datetime, timezone

    from sqlalchemy import func, select

    midnight = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    with session_scope() as session:
        return session.scalar(
            select(func.count())
            .select_from(Recommendation)
            .where(Recommendation.user_id == user_id, Recommendation.created_at >= midnight)
        )


def check_daily_limit(user_id: uuid.UUID) -> None:
    """Raise before any LLM call if this user is out of answers for today.

    Checked here rather than in the router because the resource being protected
    is the provider quota, and the router is not where that is spent. A limit
    enforced after the workflow has run would have already paid the cost it
    exists to prevent.
    """
    from backend.config.settings import get_settings

    limit = get_settings().chat_daily_limit_per_user
    if limit <= 0:  # 0 or negative disables the limit
        return
    used = answers_used_today(user_id)
    if used >= limit:
        raise DailyLimitReachedError(
            f"You have used all {limit} of today's questions. "
            "This app runs on a free AI allowance shared by everyone using it, "
            "so each person gets a set number of questions per day. "
            "Your questions reset at midnight UTC (5:30am IST). "
            "Everything else — your cards, points and past answers — still works."
        )


def run_chat(user_id: uuid.UUID, query: str) -> Recommendation:
    check_daily_limit(user_id)
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

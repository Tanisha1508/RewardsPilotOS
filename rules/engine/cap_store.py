"""Cap-usage state interface.

`InMemoryCapUsageStore` remains the default the Rule Engine constructs when no
store is passed, because `RuleEngine.calculate_earn` is a pure query — asking
what a card would earn never consumes cap — so the engine's own tests and the
rules evaluation need no database.

`PostgresCapUsageStore` implements the same protocol against the `cap_usage`
table (BUILD_SPEC §4). Read `backend/models/rewards.py` before using it: the
spec'd table has no `user_id` column, so its rows are global rather than
per-user. Nothing writes to it yet, which keeps that latent, but a multi-user
write path must not be built on it until the schema question is settled
(KNOWN_LIMITATIONS item 16).
"""

from collections import defaultdict
from typing import Protocol

from sqlalchemy import select

from backend.models.rewards import CapUsage
from database.postgres.session import session_scope


class CapUsageStore(Protocol):
    def get_accrued(self, card_key: str, scope: str, month: str) -> float: ...

    def record(self, card_key: str, scope: str, month: str, points: float) -> None: ...


class InMemoryCapUsageStore:
    def __init__(self) -> None:
        self._usage: dict[tuple[str, str, str], float] = defaultdict(float)

    def get_accrued(self, card_key: str, scope: str, month: str) -> float:
        return self._usage[(card_key, scope, month)]

    def record(self, card_key: str, scope: str, month: str, points: float) -> None:
        self._usage[(card_key, scope, month)] += points


class PostgresCapUsageStore:
    """Column mapping (see `backend/models/rewards.py` for why):
    `card_key` -> `cap_usage.card_id`, `scope` -> `cap_usage.category`."""

    def get_accrued(self, card_key: str, scope: str, month: str) -> float:
        with session_scope() as session:
            row = session.get(CapUsage, (card_key, scope, month))
            # No row means nothing accrued this month — genuinely zero, not
            # unknown, since accrual starts at zero each month by definition.
            return float(row.accrued_points) if row is not None else 0.0

    def record(self, card_key: str, scope: str, month: str, points: float) -> None:
        with session_scope() as session:
            row = session.scalars(
                select(CapUsage).where(
                    CapUsage.card_id == card_key,
                    CapUsage.category == scope,
                    CapUsage.month == month,
                )
            ).first()
            if row is None:
                session.add(
                    CapUsage(card_id=card_key, category=scope, month=month, accrued_points=points)
                )
            else:
                row.accrued_points = float(row.accrued_points) + points
            session.flush()

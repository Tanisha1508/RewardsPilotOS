"""Cap-usage state interface.

`InMemoryCapUsageStore` remains the default the Rule Engine constructs when no
store is passed, because `RuleEngine.calculate_earn` is a pure query — asking
what a card would earn never consumes cap — so the engine's own tests and the
rules evaluation need no database.

`PostgresCapUsageStore` implements the same protocol against the `cap_usage`
table (BUILD_SPEC §4, amended 2026-07-30). It is constructed with the user whose
accrual it tracks, and there is no way to construct it without one — the global
counter that made two users share a cap is now unrepresentable rather than
merely unused (KNOWN_LIMITATIONS 16, closed).
"""

import uuid
from typing import Protocol

from sqlalchemy import select

from backend.models.rewards import CapUsage
from database.postgres.session import session_scope


class CapUsageStore(Protocol):
    def get_accrued(self, card_key: str, scope: str, month: str) -> float | None: ...

    def record(self, card_key: str, scope: str, month: str, points: float) -> None: ...


class InMemoryCapUsageStore:
    def __init__(self) -> None:
        self._usage: dict[tuple[str, str, str], float] = {}

    def get_accrued(self, card_key: str, scope: str, month: str) -> float | None:
        # `None` means never tracked; 0.0 means tracked and nothing accrued.
        # Collapsing the two is what let CheckCap report "you have used 0 of
        # 15,000" for a user whose spend the system has never seen.
        return self._usage.get((card_key, scope, month))

    def record(self, card_key: str, scope: str, month: str, points: float) -> None:
        self._usage[(card_key, scope, month)] = (
            self._usage.get((card_key, scope, month), 0.0) + points
        )


class PostgresCapUsageStore:
    """Cap accrual for ONE user.

    Column mapping (see `backend/models/rewards.py` for why):
    `card_key` -> `cap_usage.card_id`, `scope` -> `cap_usage.category`.

    **The owner is a constructor argument, and required.** Passing it per call
    would let a caller forget it; taking it here means an unscoped store cannot
    be built at all, which is what previously made the global-counter bug
    possible (KNOWN_LIMITATIONS 16). The Rule Engine stays a pure function of
    its arguments — it never learns who is asking — because the store it is
    handed is already bound to a user.
    """

    def __init__(self, user_id: uuid.UUID) -> None:
        self._user_id = user_id

    def get_accrued(self, card_key: str, scope: str, month: str) -> float | None:
        with session_scope() as session:
            row = session.get(CapUsage, (self._user_id, card_key, scope, month))
            # No row means NEVER TRACKED, not "nothing spent".
            #
            # This previously returned 0.0, reasoning that accrual starts at zero
            # each month. That is only true if something records accrual — and
            # nothing does, so absence meant "we have no idea" while reading as
            # a measurement. Reporting an empty table as a confident zero is
            # exactly the fabrication the verified-value structure exists to
            # prevent.
            return float(row.accrued_points) if row is not None else None

    def record(self, card_key: str, scope: str, month: str, points: float) -> None:
        with session_scope() as session:
            row = session.scalars(
                select(CapUsage).where(
                    CapUsage.user_id == self._user_id,
                    CapUsage.card_id == card_key,
                    CapUsage.category == scope,
                    CapUsage.month == month,
                )
            ).first()
            if row is None:
                session.add(
                    CapUsage(
                        user_id=self._user_id,
                        card_id=card_key,
                        category=scope,
                        month=month,
                        accrued_points=points,
                    )
                )
            else:
                row.accrued_points = float(row.accrued_points) + points
            session.flush()

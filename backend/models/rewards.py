"""Monthly cap consumption (BUILD_SPEC §4, "Reward caps state").

Two column names still carry the spec's original meaning rather than the
protocol's, and are kept that way to match the spec:

1. **`card_id` holds a rule-engine `card_key`** (e.g. "hdfc_infinia"), not a
   `cards.card_id` UUID, so the column is `String` with no foreign key. Cap
   accrual is a property of a card's *rules*, which is what the engine keys on.
2. **`category` holds a cap `scope`** (e.g. "smartbuy_total"). Scopes are
   coarser than categories and are what the rule files declare.

**`user_id` was added 2026-07-30**, amending BUILD_SPEC §4. Without it the key
was global: two users holding the same card shared one monthly cap counter, so
one person's spend would consume the other's remaining headroom. That was
deferred while nothing wrote to the table (KNOWN_LIMITATIONS 16); it is fixed
now because the table is still empty — so the change needs no data migration —
and because a product aimed at many users cannot carry a per-card global
counter waiting to be wired up.

It also closes the one gap in account deletion: with no foreign key, cap rows
were the only user data `DELETE /auth/me` could not reach.
"""

import uuid

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class CapUsage(Base):
    __tablename__ = "cap_usage"

    # Composite natural key: one accrual row per USER, card, scope and month.
    #
    # `user_id` was added 2026-07-30, amending BUILD_SPEC §4 which specified
    # `(card_id, category, month, accrued_points)`. Without it the key is
    # global: two people holding the same card share one monthly counter, so one
    # person's spend eats the other's remaining cap. That was deferred while the
    # table was unused (KNOWN_LIMITATIONS 16) and fixed now because fixing it
    # while the table is empty needs no data migration, and because a
    # multi-user product cannot ship a per-card global counter.
    #
    # It also makes cap rows follow the user on deletion: with no FK they were
    # the one piece of user data `DELETE /auth/me` could not reach.
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True, index=True
    )
    # Holds a rule-engine `card_key` ("hdfc_infinia"), not a `cards.card_id` —
    # the column name predates that distinction and is kept to match the spec.
    card_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    # Holds a cap `scope` ("smartbuy_total"), likewise.
    category: Mapped[str] = mapped_column(String(100), primary_key=True)
    month: Mapped[str] = mapped_column(String(7), primary_key=True)  # YYYY-MM
    accrued_points: Mapped[float] = mapped_column(Numeric(16, 2), nullable=False, default=0)

"""Monthly cap consumption (BUILD_SPEC §4, "Reward caps state").

The spec'd columns are `(card_id, category, month, accrued_points)`. Two
mismatches with the sprint's `CapUsageStore` protocol
(`get_accrued(card_key, scope, month)`) are recorded here rather than resolved
by widening the table, since the schema is spec'd (Build Constraints):

1. **`card_id` holds a rule-engine `card_key`** (e.g. "hdfc_infinia"), not a
   `cards.card_id` UUID, so the column is `String` with no foreign key. Cap
   accrual is a property of a card's *rules*, which is what the engine keys on.
2. **`category` holds a cap `scope`** (e.g. "smartbuy_total"). Scopes are
   coarser than categories and are what the rule files declare.

The consequence worth stating plainly: **there is no `user_id` here**, so rows
are global rather than per-user. Two users holding the same card would share a
cap counter. Nothing writes to this table yet — the Rule Engine is a pure query
and never consumes cap (`RuleEngine.calculate_earn`) — so this is latent, not
live. Resolving it is a schema decision: see [NEED] in VERIFICATION_QUEUE and
KNOWN_LIMITATIONS item 16.
"""

from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class CapUsage(Base):
    __tablename__ = "cap_usage"

    # Composite natural key: one accrual row per card, scope, and month. The
    # spec names no surrogate id, and a surrogate would allow duplicate rows
    # for the same counter.
    card_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    category: Mapped[str] = mapped_column(String(100), primary_key=True)
    month: Mapped[str] = mapped_column(String(7), primary_key=True)  # YYYY-MM
    accrued_points: Mapped[float] = mapped_column(Numeric(16, 2), nullable=False, default=0)

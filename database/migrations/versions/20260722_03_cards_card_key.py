"""Add cards.card_key

Links a user's held card to the Rule Engine's card_key (rules/seed/<card_key>),
so the Planner can drive CompareCards / CalculateEarn against a held card
instead of the LLM guessing the key from issuer/card_name at query time (found
during D4 live /chat testing — a real HDFC Infinia card produced "unable to
determine" because nothing mapped it to the verified rule file).

Nullable, unlike reward_currency: a user may track a card the engine has no
verified rule file for (a P2 skeleton, or an unknown card). NULL card_key means
"tracked, but not reasoned about" — the honest state, surfaced as unknown rather
than guessed. Resolved at card-creation from (issuer, card_name); existing rows
are backfilled by the D4 demo seed, not by this migration.

Revision ID: cards_card_key
Revises: cards_reward_currency
Create Date: 2026-07-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "cards_card_key"
down_revision: str | None = "cards_reward_currency"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("cards", sa.Column("card_key", sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column("cards", "card_key")

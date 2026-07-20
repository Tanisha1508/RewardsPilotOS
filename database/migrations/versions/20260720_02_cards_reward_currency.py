"""Add cards.reward_currency

Closes the S2 schema gap (KNOWN_LIMITATIONS item 17): the `Card` tool contract
requires a reward currency, and the table had no column for it, so the Postgres
source was mapping the three MVP cards by (issuer, card_name) and deriving a
placeholder for anything else. A new issuer got a currency no graph node
matched, and its transfer paths came back empty rather than erroring.

Added in two steps deliberately. The column arrives nullable, then becomes NOT
NULL — with **no backfill**. If a database already holds card rows, the second
step fails loudly and the operator has to supply each card's real currency.
That is the intended behaviour: guessing a reward currency to make a migration
pass is precisely the fabrication the project forbids, and a wrong currency
would silently resolve to the wrong graph node.

Revision ID: cards_reward_currency
Revises: d2_full_schema
Create Date: 2026-07-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "cards_reward_currency"
down_revision: str | None = "d2_full_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("cards", sa.Column("reward_currency", sa.String(length=100), nullable=True))
    # No UPDATE between these two statements, on purpose — see the module
    # docstring. An existing row without a currency must be resolved by a human.
    op.alter_column("cards", "reward_currency", nullable=False)


def downgrade() -> None:
    op.drop_column("cards", "reward_currency")

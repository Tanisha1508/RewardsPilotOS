"""Scope cap_usage to a user.

BUILD_SPEC §4 specified `(card_id, category, month, accrued_points)` with no
user column, which made every accrual row global: two users holding the same
card would share one monthly cap counter, and one person's spend would consume
the other's remaining headroom. Recorded as KNOWN_LIMITATIONS 16 and deferred
while the table was unused.

Done now, before anything writes, for two reasons:

* The table is empty, so there is no data to migrate and no ambiguity about
  which user existing rows belong to. Later there would be both.
* `DELETE /auth/me` (privacy audit P3) cascades through every table that
  references `users`. `cap_usage` had no foreign key, so it was the one place
  user data could survive an account deletion.

`user_id` joins the primary key rather than sitting beside it: the counter is
per user *and* card *and* scope *and* month, and leaving it out of the key would
allow two rows for the same counter.

Revision ID: cap_usage_user_id
Revises: cards_card_key
"""

import sqlalchemy as sa
from alembic import op

revision: str = "cap_usage_user_id"
down_revision: str | None = "cards_card_key"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Empty table by construction — nothing has ever written to it — so the
    # column can be added NOT NULL directly without a backfill. If that
    # assumption is ever wrong the migration fails loudly here rather than
    # silently inventing an owner for existing rows.
    op.add_column("cap_usage", sa.Column("user_id", sa.Uuid(), nullable=False))
    op.create_foreign_key(
        "fk_cap_usage_user_id_users",
        "cap_usage",
        "users",
        ["user_id"],
        ["user_id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_cap_usage_user_id", "cap_usage", ["user_id"])

    # Rebuild the primary key to include the owner.
    op.drop_constraint("cap_usage_pkey", "cap_usage", type_="primary")
    op.create_primary_key(
        "cap_usage_pkey", "cap_usage", ["user_id", "card_id", "category", "month"]
    )


def downgrade() -> None:
    op.drop_constraint("cap_usage_pkey", "cap_usage", type_="primary")
    op.create_primary_key("cap_usage_pkey", "cap_usage", ["card_id", "category", "month"])
    op.drop_index("ix_cap_usage_user_id", table_name="cap_usage")
    op.drop_constraint("fk_cap_usage_user_id_users", "cap_usage", type_="foreignkey")
    op.drop_column("cap_usage", "user_id")

"""D2: full schema per BUILD_SPEC section 4

The complete spec'd schema in one migration — the tables are created together
because they reference each other, and splitting them would produce
intermediate revisions where the foreign keys have nothing to point at.

Generated from `backend.models.Base.metadata` rather than hand-written, so the
migration and the models cannot drift through a transcription slip.
`tests/integration/test_migrations.py` re-checks that with Alembic's own
metadata comparison once a database is available.

Revision ID: d2_full_schema
Revises:
Create Date: 2026-07-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d2_full_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "cap_usage",
        sa.Column("card_id", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("month", sa.String(length=7), nullable=False),
        sa.Column("accrued_points", sa.Numeric(precision=16, scale=2), nullable=False),
        sa.PrimaryKeyConstraint("card_id", "category", "month"),
    )
    op.create_table(
        "graph_nodes",
        sa.Column("node_id", sa.String(length=200), nullable=False),
        sa.Column("node_type", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("meta_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint("node_id"),
    )
    op.create_table(
        "knowledge_docs",
        sa.Column("doc_id", sa.String(length=200), nullable=False),
        sa.Column("source_url", sa.String(), nullable=False),
        sa.Column("issuer", sa.String(length=100), nullable=True),
        sa.Column("program", sa.String(length=100), nullable=True),
        sa.Column("doc_type", sa.String(length=100), nullable=True),
        sa.Column("content_hash", sa.String(length=128), nullable=True),
        sa.Column("last_crawled", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_changed", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.PrimaryKeyConstraint("doc_id"),
    )
    op.create_table(
        "rule_versions",
        sa.Column("rule_version_id", sa.Uuid(), nullable=False),
        sa.Column("card_key", sa.String(length=100), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("file_path", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("rule_version_id"),
        sa.UniqueConstraint("card_key", "version", name="uq_rule_versions_card_version"),
    )
    op.create_index(op.f("ix_rule_versions_card_key"), "rule_versions", ["card_key"])
    op.create_table(
        "users",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=True),
        sa.Column("timezone", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("user_id"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "goals",
        sa.Column("goal_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("goal_type", sa.String(length=20), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("goal_id"),
    )
    op.create_index(op.f("ix_goals_user_id"), "goals", ["user_id"])
    op.create_table(
        "graph_edges",
        sa.Column("edge_id", sa.Uuid(), nullable=False),
        sa.Column("from_node", sa.String(length=200), nullable=False),
        sa.Column("to_node", sa.String(length=200), nullable=False),
        sa.Column("edge_type", sa.String(length=20), nullable=False),
        sa.Column("ratio", sa.Numeric(precision=12, scale=6), nullable=True),
        sa.Column("min_transfer", sa.Numeric(precision=16, scale=2), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("source_doc_id", sa.String(length=200), nullable=True),
        sa.Column("last_verified", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(["from_node"], ["graph_nodes.node_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_doc_id"], ["knowledge_docs.doc_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["to_node"], ["graph_nodes.node_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("edge_id"),
    )
    op.create_index(op.f("ix_graph_edges_from_node"), "graph_edges", ["from_node"])
    op.create_index(op.f("ix_graph_edges_to_node"), "graph_edges", ["to_node"])
    op.create_table(
        "interaction_events",
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index(op.f("ix_interaction_events_user_id"), "interaction_events", ["user_id"])
    op.create_table(
        "notifications",
        sa.Column("notif_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("type", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("body", sa.String(), nullable=True),
        sa.Column("source_change_id", sa.String(length=200), nullable=True),
        sa.Column("read", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("notif_id"),
    )
    op.create_index(op.f("ix_notifications_user_id"), "notifications", ["user_id"])
    op.create_table(
        "portfolios",
        sa.Column("portfolio_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("portfolio_name", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("portfolio_id"),
    )
    op.create_index(op.f("ix_portfolios_user_id"), "portfolios", ["user_id"])
    op.create_table(
        "preferences",
        sa.Column("pref_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("value", sa.String(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("pref_id"),
        sa.UniqueConstraint("user_id", "key", name="uq_preferences_user_key"),
    )
    op.create_index(op.f("ix_preferences_user_id"), "preferences", ["user_id"])
    op.create_table(
        "recommendations",
        sa.Column("rec_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("query", sa.String(), nullable=False),
        sa.Column("recommendation_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("confidence", sa.String(length=10), nullable=True),
        sa.Column("citations_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("rec_id"),
    )
    op.create_index(op.f("ix_recommendations_user_id"), "recommendations", ["user_id"])
    op.create_table(
        "cards",
        sa.Column("card_id", sa.Uuid(), nullable=False),
        sa.Column("portfolio_id", sa.Uuid(), nullable=False),
        sa.Column("issuer", sa.String(length=100), nullable=False),
        sa.Column("card_name", sa.String(length=200), nullable=False),
        sa.Column("network", sa.String(length=50), nullable=False),
        sa.Column("joining_date", sa.Date(), nullable=True),
        sa.Column("annual_fee", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("renewal_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.portfolio_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("card_id"),
    )
    op.create_index(op.f("ix_cards_portfolio_id"), "cards", ["portfolio_id"])
    op.create_table(
        "loyalty_accounts",
        sa.Column("loyalty_id", sa.Uuid(), nullable=False),
        sa.Column("portfolio_id", sa.Uuid(), nullable=False),
        sa.Column("program_name", sa.String(length=200), nullable=False),
        sa.Column("program_type", sa.String(length=20), nullable=False),
        sa.Column("balance", sa.Numeric(precision=16, scale=2), nullable=False),
        sa.Column("status_tier", sa.String(length=100), nullable=True),
        sa.Column("last_updated", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.portfolio_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("loyalty_id"),
    )
    op.create_index(op.f("ix_loyalty_accounts_portfolio_id"), "loyalty_accounts", ["portfolio_id"])
    op.create_table(
        "reward_balances",
        sa.Column("balance_id", sa.Uuid(), nullable=False),
        sa.Column("card_id", sa.Uuid(), nullable=False),
        sa.Column("reward_currency", sa.String(length=100), nullable=False),
        sa.Column("current_balance", sa.Numeric(precision=16, scale=2), nullable=False),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("last_updated", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["card_id"], ["cards.card_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("balance_id"),
    )
    op.create_index(op.f("ix_reward_balances_card_id"), "reward_balances", ["card_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_reward_balances_card_id"), table_name="reward_balances")
    op.drop_table("reward_balances")
    op.drop_index(op.f("ix_loyalty_accounts_portfolio_id"), table_name="loyalty_accounts")
    op.drop_table("loyalty_accounts")
    op.drop_index(op.f("ix_cards_portfolio_id"), table_name="cards")
    op.drop_table("cards")
    op.drop_index(op.f("ix_recommendations_user_id"), table_name="recommendations")
    op.drop_table("recommendations")
    op.drop_index(op.f("ix_preferences_user_id"), table_name="preferences")
    op.drop_table("preferences")
    op.drop_index(op.f("ix_portfolios_user_id"), table_name="portfolios")
    op.drop_table("portfolios")
    op.drop_index(op.f("ix_notifications_user_id"), table_name="notifications")
    op.drop_table("notifications")
    op.drop_index(op.f("ix_interaction_events_user_id"), table_name="interaction_events")
    op.drop_table("interaction_events")
    op.drop_index(op.f("ix_graph_edges_from_node"), table_name="graph_edges")
    op.drop_index(op.f("ix_graph_edges_to_node"), table_name="graph_edges")
    op.drop_table("graph_edges")
    op.drop_index(op.f("ix_goals_user_id"), table_name="goals")
    op.drop_table("goals")
    op.drop_table("users")
    op.drop_index(op.f("ix_rule_versions_card_key"), table_name="rule_versions")
    op.drop_table("rule_versions")
    op.drop_table("knowledge_docs")
    op.drop_table("graph_nodes")
    op.drop_table("cap_usage")

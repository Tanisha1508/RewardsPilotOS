"""Record who set each preference.

`preferences` stored key, value and a timestamp — and nothing about where the
value came from. That made two very different things indistinguishable:

* something the user typed into the Reward preferences screen, and
* something the assistant inferred from a conversation and wrote via the
  `StorePreference` tool.

Those must not look the same. A preference changes what the product recommends,
so a user has to be able to see which of their settings they chose and which
were decided for them. Without that, the honest options were to hide the
assistant's writes (they would be invisible and unauditable) or to disable
`StorePreference` (which BUILD_SPEC §8 lists as a required tool). Neither is
good; both were the state of things until now.

**Decision, owner, 2026-07-31.** Backlog B3 offered three ways out of that
deadlock: delete the tool and amend the spec, keep it and add provenance, or
leave it registered-but-unguided. Provenance was chosen. It keeps the spec
intact, makes the assistant's writes visible rather than forbidden, and is the
column D-3 (multi-turn Ask) would need regardless.

`source` is NOT NULL with a server default of 'user'. Every existing row was
written through the preferences API by a person, so 'user' is the true value for
all of them rather than a convenient filler — there is no backfill guesswork
here. New writers state their source explicitly.

Revision ID: preferences_source
Revises: cap_usage_user_id
"""

import sqlalchemy as sa
from alembic import op

revision: str = "preferences_source"
down_revision: str | None = "cap_usage_user_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "preferences",
        sa.Column(
            "source",
            sa.String(length=20),
            nullable=False,
            server_default="user",
        ),
    )


def downgrade() -> None:
    op.drop_column("preferences", "source")

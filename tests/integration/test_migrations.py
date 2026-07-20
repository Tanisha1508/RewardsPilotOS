"""The migration and the models must describe the same schema.

The failure this prevents: models and migration drift, everything passes
locally against `create_all`, and the deploy produces a database missing a
column. Alembic's own comparison is the check — anything it reports is a
difference between what `upgrade head` built and what the ORM expects.

Also asserts a single head (BUILD_SPEC §4). Multiple heads are the other way a
migration set breaks a deploy: `upgrade head` becomes ambiguous and fails.
"""

from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory

from backend.models import Base
from tests.integration.conftest import ALEMBIC_INI


def test_single_head():
    script = ScriptDirectory.from_config(Config(str(ALEMBIC_INI)))
    heads = script.get_heads()
    assert len(heads) == 1, f"expected a single head, found {heads}"


def test_migration_matches_models(migrated_database):
    from database.postgres.session import get_engine

    with get_engine().connect() as connection:
        context = MigrationContext.configure(connection, opts={"compare_type": True})
        diff = compare_metadata(context, Base.metadata)

    assert diff == [], f"migration and models disagree: {diff}"


def test_every_specced_table_exists(migrated_database):
    """BUILD_SPEC §4 names fourteen tables plus cap_usage. A table that is
    modelled but never imported into `backend/models/__init__` would be missing
    here with no other symptom."""
    from sqlalchemy import inspect

    from database.postgres.session import get_engine

    expected = {
        "users",
        "portfolios",
        "cards",
        "reward_balances",
        "loyalty_accounts",
        "goals",
        "preferences",
        "recommendations",
        "interaction_events",
        "notifications",
        "knowledge_docs",
        "rule_versions",
        "graph_nodes",
        "graph_edges",
        "cap_usage",
    }
    actual = set(inspect(get_engine()).get_table_names())
    assert expected <= actual, f"missing tables: {sorted(expected - actual)}"


def test_downgrade_then_upgrade_round_trips(migrated_database, database_url):
    """A downgrade that does not fully undo its upgrade leaves a database that
    cannot be migrated forward again — the failure only shows up the next time
    someone tries, which is usually mid-deploy."""
    from sqlalchemy import inspect

    from database.postgres.session import dispose_engine, get_engine
    from tests.integration.conftest import run_alembic

    dispose_engine()
    run_alembic("downgrade base", database_url)

    remaining = set(inspect(get_engine()).get_table_names()) - {"alembic_version"}
    assert remaining == set(), f"downgrade left tables behind: {sorted(remaining)}"

    dispose_engine()
    run_alembic("upgrade head", database_url)
    assert "users" in set(inspect(get_engine()).get_table_names())

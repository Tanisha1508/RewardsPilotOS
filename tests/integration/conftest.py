"""Integration fixtures: a real Postgres database.

**These tests skip unless `TEST_DATABASE_URL` is set, and they never fall back
to `DATABASE_URL`.** They create and drop the whole schema, so pointing them at
whatever database happened to be configured is a way to lose a dev database.
Opting in through a separate variable makes that impossible by accident.

Run them with a Supabase branch database, or any throwaway Postgres:

    TEST_DATABASE_URL=postgresql+psycopg://user:pass@host/dbname \\
        .venv/bin/python -m pytest tests/integration

Schema is created by running the real Alembic migration, not
`Base.metadata.create_all` — testing against a schema the migration never
produced would leave the migration itself unverified, which is the thing most
likely to break a deploy.
"""

import os
import subprocess
import uuid
from pathlib import Path

import pytest
from sqlalchemy import text

from backend.config.settings import get_settings

REPO_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI = REPO_ROOT / "database" / "migrations" / "alembic.ini"

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")

SKIP_REASON = (
    "TEST_DATABASE_URL is not set — integration tests need a real Postgres database "
    "and deliberately do not fall back to DATABASE_URL. Run them with: "
    "TEST_DATABASE_URL=postgresql+psycopg://... .venv/bin/python -m pytest tests/integration"
)

# Reverse dependency order, for between-test cleanup.
TABLES_IN_DELETE_ORDER = [
    "reward_balances",
    "loyalty_accounts",
    "cards",
    "portfolios",
    "recommendations",
    "interaction_events",
    "notifications",
    "preferences",
    "goals",
    "users",
    "graph_edges",
    "graph_nodes",
    "knowledge_docs",
    "rule_versions",
    "cap_usage",
]


def run_alembic(command: str, url: str) -> None:
    result = subprocess.run(
        [".venv/bin/alembic", "-c", str(ALEMBIC_INI), *command.split()],
        cwd=REPO_ROOT,
        env={**os.environ, "ALEMBIC_DATABASE_URL": url},
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"alembic {command} failed:\n{result.stdout}\n{result.stderr}")


@pytest.fixture(scope="session")
def database_url() -> str:
    # The skip lives in the fixture, not in a module-level `pytestmark`: a
    # pytestmark set in a conftest applies only to tests defined in that file,
    # so it would silently protect nothing here.
    if not TEST_DATABASE_URL:
        pytest.skip(SKIP_REASON, allow_module_level=True)
    return TEST_DATABASE_URL


@pytest.fixture(scope="session", autouse=True)
def migrated_database(database_url):
    """Apply migrations once per session, and roll them back afterwards."""
    from database.postgres.session import configure_engine, dispose_engine

    run_alembic("upgrade head", database_url)
    configure_engine(database_url)
    yield database_url
    dispose_engine()
    run_alembic("downgrade base", database_url)


@pytest.fixture(autouse=True)
def clean_tables(migrated_database):
    """Empty every table between tests.

    Truncation rather than transaction rollback, because the API tests go
    through middleware that opens its own session and commits — a test-owned
    outer transaction would not contain it.
    """
    from database.postgres.session import new_session

    yield
    session = new_session()
    try:
        for table in TABLES_IN_DELETE_ORDER:
            session.execute(text(f"DELETE FROM {table}"))
        session.commit()
    finally:
        session.close()


@pytest.fixture(autouse=True)
def postgres_sources(migrated_database):
    """Undo the suite-wide in-memory sources from `tests/conftest.py`.

    Without this these tests would pass against seeded fakes while appearing to
    exercise Postgres — the exact false green that makes an integration suite
    worthless.
    """
    from tools.memory.source import set_source as set_memory_source
    from tools.portfolio.source import set_source as set_portfolio_source

    set_portfolio_source(None)
    set_memory_source(None)
    yield


@pytest.fixture()
def jwt_secret(monkeypatch) -> str:
    from tests.unit.test_auth_tokens import SECRET

    monkeypatch.setenv("SUPABASE_JWT_SECRET", SECRET)
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL or "")
    get_settings.cache_clear()
    yield SECRET
    get_settings.cache_clear()


@pytest.fixture()
def user_id() -> uuid.UUID:
    return uuid.uuid4()

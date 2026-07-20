"""Alembic environment.

The connection string comes from `backend.config.settings` and nowhere else —
no `sqlalchemy.url` in alembic.ini, no default. A missing DATABASE_URL raises
`DatabaseNotConfiguredError`; migrations are the one operation where connecting
to an unintended database is unrecoverable.

`ALEMBIC_DATABASE_URL` overrides it for a single run, which is how the test
harness points migrations at the test database without mutating settings.
"""

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from backend.config.settings import get_settings
from backend.models import Base
from database.postgres.session import DatabaseNotConfiguredError

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _url() -> str:
    url = os.environ.get("ALEMBIC_DATABASE_URL") or get_settings().database_url
    if not url:
        raise DatabaseNotConfiguredError(
            "DATABASE_URL is not set — refusing to run migrations against an "
            "unknown database. Set it in .env, or pass ALEMBIC_DATABASE_URL."
        )
    return url


def run_migrations_offline() -> None:
    context.configure(
        url=_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(_url(), poolclass=pool.NullPool, future=True)
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

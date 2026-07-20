"""Postgres engine and session scope.

The problem this solves: the Tool Registry's handlers are plain functions with
spec'd signatures — `get_portfolio(args: UserScopedInput) -> GetPortfolioOutput`
— with nowhere to pass a database session. Threading one through would change
tool contracts, which the Build Constraints forbid.

So the session is ambient rather than a parameter. `session_scope()` returns the
session bound to the current context if there is one, otherwise opens a new one
against `DATABASE_URL`. Tests bind a session inside a transaction they roll back;
the tools never know the difference and their signatures stay exactly as spec'd.

The engine is created lazily and never with a default URL: a missing
`DATABASE_URL` raises `DatabaseNotConfiguredError` rather than silently
connecting somewhere unintended.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.config.settings import get_settings


class DatabaseNotConfiguredError(RuntimeError):
    """DATABASE_URL is unset. Raised instead of falling back to a default."""


_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None

# Set by tests (and by the API request scope) so everything running inside one
# logical operation shares a single session and a single transaction.
_bound_session: ContextVar[Session | None] = ContextVar("bound_session", default=None)


def configure_engine(url: str) -> Engine:
    """Point the process at `url`, replacing any existing engine."""
    global _engine, _session_factory
    dispose_engine()
    _engine = create_engine(url, pool_pre_ping=True, future=True)
    _session_factory = sessionmaker(bind=_engine, expire_on_commit=False, future=True)
    return _engine


def dispose_engine() -> None:
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None


def get_engine() -> Engine:
    if _engine is None:
        url = get_settings().database_url
        if not url:
            raise DatabaseNotConfiguredError(
                "DATABASE_URL is not set — refusing to guess a database. "
                "Set it in .env (see .env.example)."
            )
        configure_engine(url)
    assert _engine is not None
    return _engine


def new_session() -> Session:
    get_engine()
    assert _session_factory is not None
    return _session_factory()


@contextmanager
def bind_session(session: Session) -> Iterator[Session]:
    """Make `session` the ambient session for the duration of the block."""
    token = _bound_session.set(session)
    try:
        yield session
    finally:
        _bound_session.reset(token)


@contextmanager
def session_scope() -> Iterator[Session]:
    """Yield the ambient session, or open and commit a fresh one.

    When a session is already bound, this does NOT commit or close it — the
    owner of the outer scope decides that. Committing here would defeat the
    test harness's rollback and would half-commit a request that later fails.
    """
    bound = _bound_session.get()
    if bound is not None:
        yield bound
        return

    session = new_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

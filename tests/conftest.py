"""Suite-wide fixtures.

Since D2 the portfolio and memory tools read Postgres by default and have no
fixture fallback — answering from seed data when the database is missing would
be the system quietly inventing a portfolio. Tests that exercise the agent
therefore install the seeded fakes explicitly, here, once.

`acting_as` supplies the ambient user that tools loading "the caller's own
data" need (`tools/portfolio/source.py`). Tests that want the real Postgres
path use the fixtures in `tests/integration/conftest.py` instead, which swap
these out.
"""

import pytest

from tools.memory.source import InMemoryMemorySource
from tools.memory.source import set_source as set_memory_source
from tools.portfolio.source import InMemoryPortfolioSource, acting_as, load_seed
from tools.portfolio.source import set_source as set_portfolio_source


@pytest.fixture(scope="session")
def demo_seed() -> dict:
    return load_seed()


@pytest.fixture(autouse=True, scope="session")
def seeded_sources(demo_seed):
    """Install the seeded fakes for the whole session, and restore the default
    afterwards.

    Session-scoped, not per-test, because pytest builds higher-scoped fixtures
    first: a session-scoped fixture that runs the LangGraph workflow would
    otherwise execute before a function-scoped autouse fixture could install
    anything, and read from an unconfigured database.

    Restoring at the end matters: leaving a fake installed would let a test that
    means to exercise Postgres silently pass against in-memory data instead.
    """
    set_portfolio_source(InMemoryPortfolioSource(demo_seed))
    set_memory_source(InMemoryMemorySource(demo_seed))
    with acting_as(demo_seed["user_id"]):
        yield
    set_portfolio_source(None)
    set_memory_source(None)

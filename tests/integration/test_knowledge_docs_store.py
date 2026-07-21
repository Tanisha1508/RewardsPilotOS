"""PostgresKnowledgeDocsStore persistence (D3, BUILD_SPEC §6).

The one property that matters and that the in-memory store cannot provide: a
content hash written in one process is still there in the next. If it is not,
every crawl re-ingests the whole corpus and no document is ever detected as
changed — the crawler's entire job.

So the central test does not reuse a store instance. It writes with one, throws
it away, disposes the engine (simulating process exit), and reads with a fresh
instance — the closest a single test run can get to "restart the process".
"""

from datetime import date

from knowledge.pipeline.docs_store import (
    KnowledgeDocRecord,
    PostgresKnowledgeDocsStore,
)

RECORD = KnowledgeDocRecord(
    doc_id="hdfc_infinia_reward_rules",
    source_url="https://www.hdfcbank.com/infinia",
    issuer="hdfc",
    program="hdfc_reward_points",
    doc_type="reward_rules",
    content_hash="abc123hash",
    last_changed="2026-07-19",
)


def test_hash_is_unknown_before_anything_is_written():
    assert PostgresKnowledgeDocsStore().get_hash("hdfc_infinia_reward_rules") is None


def test_hash_survives_a_new_store_instance_and_a_disposed_engine(database_url):
    """The restart test. Write, drop the store, tear down the connection pool
    entirely, reconnect to the *same* database with a fresh engine — exactly
    what a process restart does — then read through a brand-new store. The hash
    must still be there.

    Reconfiguring to `database_url` rather than letting `get_engine()` reconnect
    on its own is deliberate: the lazy path would fall back to DATABASE_URL,
    which in the test environment is not the test database. A real restarted
    process reconnects to the same URL it had before, and that is what is
    simulated here."""
    from database.postgres.session import configure_engine, dispose_engine

    PostgresKnowledgeDocsStore().upsert(RECORD)

    # Simulate process exit and restart: tear down every connection, then bring
    # up a fresh engine pointed at the same database.
    dispose_engine()
    configure_engine(database_url)

    fresh = PostgresKnowledgeDocsStore()
    assert fresh.get_hash("hdfc_infinia_reward_rules") == "abc123hash"


def test_upsert_updates_the_hash_rather_than_duplicating():
    store = PostgresKnowledgeDocsStore()
    store.upsert(RECORD)
    store.upsert(
        KnowledgeDocRecord(
            **{**RECORD.__dict__, "content_hash": "newhash", "last_changed": "2026-07-25"}
        )
    )
    assert store.get_hash("hdfc_infinia_reward_rules") == "newhash"

    # And exactly one row — an upsert, not an insert.
    from sqlalchemy import func, select

    from backend.models.knowledge import KnowledgeDoc
    from database.postgres.session import session_scope

    with session_scope() as session:
        count = session.scalar(
            select(func.count())
            .select_from(KnowledgeDoc)
            .where(KnowledgeDoc.doc_id == "hdfc_infinia_reward_rules")
        )
    assert count == 1


def test_upsert_persists_the_full_metadata_row():
    """Not just the hash — issuer, program, doc_type, source_url, and the parsed
    date all reach the row, because they flow into citations and freshness."""
    PostgresKnowledgeDocsStore().upsert(RECORD)

    from backend.models.knowledge import KnowledgeDoc
    from database.postgres.session import session_scope

    with session_scope() as session:
        row = session.get(KnowledgeDoc, "hdfc_infinia_reward_rules")
        assert row.issuer == "hdfc"
        assert row.program == "hdfc_reward_points"
        assert row.doc_type == "reward_rules"
        assert row.source_url == "https://www.hdfcbank.com/infinia"
        assert row.last_changed == date(2026, 7, 19)
        assert row.last_crawled is not None  # stamped at upsert
        assert row.status == "active"


def test_a_malformed_change_date_is_stored_as_null_not_a_crash():
    """Freshness decay handles a missing date conservatively; a broken ingest
    would be worse than an unknown date."""
    PostgresKnowledgeDocsStore().upsert(
        KnowledgeDocRecord(**{**RECORD.__dict__, "last_changed": "not-a-date"})
    )

    from backend.models.knowledge import KnowledgeDoc
    from database.postgres.session import session_scope

    with session_scope() as session:
        assert session.get(KnowledgeDoc, "hdfc_infinia_reward_rules").last_changed is None

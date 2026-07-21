"""PostgresCrawlStateStore persistence (D3, ADR-016).

The crawler is only useful if it remembers what a page looked like last time
across runs — otherwise every daily cron reports every page as new. So, like the
knowledge-docs store, the key test survives a simulated restart.

Also asserts the namespace guarantee: crawl-state rows (`source::<key>`) do not
collide with ingested-corpus rows sharing the `knowledge_docs` table.
"""

from knowledge.crawler.crawl import crawl
from knowledge.crawler.state import PostgresCrawlStateStore
from knowledge.pipeline.docs_store import KnowledgeDocRecord, PostgresKnowledgeDocsStore


def test_hash_survives_a_restart(database_url):
    from database.postgres.session import configure_engine, dispose_engine

    store = PostgresCrawlStateStore()
    store.record("axis_atlas", "https://axis.test", "hash-v1", "2026-07-21", changed=True)

    dispose_engine()
    configure_engine(database_url)

    assert PostgresCrawlStateStore().get_hash("axis_atlas") == "hash-v1"


def test_record_advances_hash_on_change():
    store = PostgresCrawlStateStore()
    store.record("axis_atlas", "https://axis.test", "hash-v1", "2026-07-21", changed=True)
    store.record("axis_atlas", "https://axis.test", "hash-v2", "2026-07-25", changed=True)
    assert store.get_hash("axis_atlas") == "hash-v2"


def test_crawl_state_does_not_collide_with_ingested_corpus_rows():
    """Same table, different namespace: a crawl-state row for axis_atlas and the
    ingested axis_atlas_reward_rows doc must coexist without overwriting each
    other's content_hash."""
    PostgresKnowledgeDocsStore().upsert(
        KnowledgeDocRecord(
            doc_id="axis_atlas_reward_rules",
            source_url="https://axis.test/atlas",
            issuer="axis",
            program="edge_miles",
            doc_type="reward_rules",
            content_hash="ingest-body-hash",
            last_changed="2026-07-19",
        )
    )
    PostgresCrawlStateStore().record(
        "axis_atlas", "https://axis.test/atlas", "live-page-hash", "2026-07-21", changed=True
    )

    # Neither clobbered the other.
    assert PostgresKnowledgeDocsStore().get_hash("axis_atlas_reward_rules") == "ingest-body-hash"
    assert PostgresCrawlStateStore().get_hash("axis_atlas") == "live-page-hash"


def test_full_crawl_persists_state_with_a_fake_fetcher():
    """End to end through crawl() with the Postgres store, no network."""
    store = PostgresCrawlStateStore()

    def fetch(_url, _ua):
        return "<html><body>Atlas base earn 2 EDGE Miles per 100</body></html>"

    first = crawl(store=store, fetcher=fetch, today="2026-07-21")
    assert {r.status for r in first.changed}  # at least one new
    # crawlable sources now have persisted state
    assert store.get_hash("axis_atlas") is not None

    again = crawl(store=store, fetcher=fetch, today="2026-07-22")
    assert next(r for r in again.records if r.key == "axis_atlas").status == "unchanged"

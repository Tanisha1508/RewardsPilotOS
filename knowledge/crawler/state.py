"""Crawler change-tracking state (BUILD_SPEC §6, ADR-016).

Stores, per source, the hash of its live page as last crawled — so the next
crawl can tell "changed" from "unchanged". Same protocol shape as the other D2/D3
stores: an in-memory fake for tests and a Postgres implementation for production.

The Postgres store writes to `knowledge_docs` under a `source::<key>` doc_id
namespace, kept apart from ingested-corpus rows so the crawler's live-page hash
never collides with ingestion's seed-body hash. `last_crawled` advances every
run; `last_changed` advances only when the content actually changed — which is
exactly the change record BUILD_SPEC §6 asks the crawler to write to
knowledge_docs.
"""

from datetime import date
from typing import Protocol

from backend.models.base import utcnow
from backend.models.knowledge import KnowledgeDoc
from database.postgres.session import session_scope

NAMESPACE = "source::"


class CrawlStateStore(Protocol):
    def get_hash(self, key: str) -> str | None: ...

    def record(
        self, key: str, url: str, content_hash: str, crawl_date: str, changed: bool
    ) -> None: ...


class InMemoryCrawlStateStore:
    def __init__(self) -> None:
        self.state: dict[str, dict] = {}

    def get_hash(self, key: str) -> str | None:
        entry = self.state.get(key)
        return entry["content_hash"] if entry else None

    def record(self, key: str, url: str, content_hash: str, crawl_date: str, changed: bool) -> None:
        entry = self.state.setdefault(key, {})
        entry["url"] = url
        entry["content_hash"] = content_hash
        entry["last_crawled"] = crawl_date
        if changed:
            entry["last_changed"] = crawl_date


class PostgresCrawlStateStore:
    """knowledge_docs rows namespaced `source::<key>` (ADR-016)."""

    def _doc_id(self, key: str) -> str:
        return f"{NAMESPACE}{key}"

    def get_hash(self, key: str) -> str | None:
        with session_scope() as session:
            row = session.get(KnowledgeDoc, self._doc_id(key))
            return row.content_hash if row is not None else None

    def record(self, key: str, url: str, content_hash: str, crawl_date: str, changed: bool) -> None:
        with session_scope() as session:
            doc_id = self._doc_id(key)
            row = session.get(KnowledgeDoc, doc_id)
            if row is None:
                row = KnowledgeDoc(doc_id=doc_id, status="crawl_state")
                session.add(row)
            row.source_url = url
            row.content_hash = content_hash
            row.doc_type = "crawl_state"
            row.last_crawled = utcnow()
            if changed:
                row.last_changed = _parse_date(crawl_date)
            session.flush()


def _parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        return None

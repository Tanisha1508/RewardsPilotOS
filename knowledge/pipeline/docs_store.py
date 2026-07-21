"""knowledge_docs metadata store interface (content_hash tracking, BUILD_SPEC §6).

`get_hash` is what lets ingestion skip an unchanged document and the crawler
detect a changed one: both compare a freshly computed content hash against the
stored one. So the store's whole job is to remember a hash across runs — which
the in-memory fake does *not* do past process exit, and the Postgres store does.

`InMemoryKnowledgeDocsStore` remains the default for tests and the fixture
ingestion (no database needed). `PostgresKnowledgeDocsStore` (D3) persists to
the `knowledge_docs` table so hashes survive a restart — without that, every
crawl run re-ingests everything and no change is ever "new".
"""

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from backend.models.base import utcnow
from backend.models.knowledge import KnowledgeDoc
from database.postgres.session import session_scope


@dataclass
class KnowledgeDocRecord:
    doc_id: str
    source_url: str
    issuer: str
    program: str
    doc_type: str
    content_hash: str
    last_changed: str


class KnowledgeDocsStore(Protocol):
    def get_hash(self, doc_id: str) -> str | None: ...

    def upsert(self, record: KnowledgeDocRecord) -> None: ...


class InMemoryKnowledgeDocsStore:
    def __init__(self) -> None:
        self.records: dict[str, KnowledgeDocRecord] = {}

    def get_hash(self, doc_id: str) -> str | None:
        record = self.records.get(doc_id)
        return record.content_hash if record else None

    def upsert(self, record: KnowledgeDocRecord) -> None:
        self.records[record.doc_id] = record


class PostgresKnowledgeDocsStore:
    """Hash tracking against the `knowledge_docs` table (BUILD_SPEC §4, §6).

    Same protocol as the in-memory fake; the only difference that matters is
    that the hash outlives the process. `last_crawled` is stamped at upsert
    (this run touched the doc), `last_changed` carries the content's own change
    date from the source's frontmatter or the crawl diff, and `status` defaults
    to 'active' — a doc is only written here once it has been successfully
    ingested.
    """

    def get_hash(self, doc_id: str) -> str | None:
        with session_scope() as session:
            row = session.get(KnowledgeDoc, doc_id)
            return row.content_hash if row is not None else None

    def upsert(self, record: KnowledgeDocRecord) -> None:
        with session_scope() as session:
            row = session.get(KnowledgeDoc, record.doc_id)
            if row is None:
                row = KnowledgeDoc(doc_id=record.doc_id, status="active")
                session.add(row)
            row.source_url = record.source_url
            row.issuer = record.issuer
            row.program = record.program
            row.doc_type = record.doc_type
            row.content_hash = record.content_hash
            row.last_changed = _parse_date(record.last_changed)
            row.last_crawled = utcnow()
            session.flush()


def _parse_date(value: str) -> date | None:
    """Frontmatter and crawl records carry ISO date strings; the column is a
    real DATE. A malformed value is stored as NULL rather than crashing ingest,
    since freshness decay treats a missing date conservatively."""
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        return None

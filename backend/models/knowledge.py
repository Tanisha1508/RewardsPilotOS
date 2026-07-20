"""Knowledge-doc and rule-version tables (BUILD_SPEC §4).

`knowledge_docs` holds metadata only; chunk content lives in ChromaDB, keyed by
`doc_id + chunk_index`. `content_hash` is what the crawler diffs to decide
whether `last_changed` moves — which is what freshness decay reads, so a doc
that changes without the hash moving keeps its old timestamp
(KNOWN_LIMITATIONS item 15).
"""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base, created_at_column, pk_uuid


class KnowledgeDoc(Base):
    __tablename__ = "knowledge_docs"

    # Natural key, not generated: doc_id is the same identifier used as the
    # ChromaDB chunk key and in every citation, so it must be stable and
    # readable rather than a fresh UUID per ingest.
    doc_id: Mapped[str] = mapped_column(String(200), primary_key=True)
    source_url: Mapped[str] = mapped_column(String, nullable=False)
    issuer: Mapped[str | None] = mapped_column(String(100))
    program: Mapped[str | None] = mapped_column(String(100))
    doc_type: Mapped[str | None] = mapped_column(String(100))
    content_hash: Mapped[str | None] = mapped_column(String(128))
    last_crawled: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_changed: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")


class RuleVersion(Base):
    __tablename__ = "rule_versions"
    __table_args__ = (
        UniqueConstraint("card_key", "version", name="uq_rule_versions_card_version"),
    )

    rule_version_id: Mapped[uuid.UUID] = pk_uuid()
    card_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = created_at_column()

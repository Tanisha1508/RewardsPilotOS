"""knowledge_docs metadata store interface (content_hash tracking, BUILD_SPEC §6).

Sprint milestone uses the in-memory fake; D2 wires the Postgres knowledge_docs
table behind the same protocol."""

from dataclasses import dataclass
from typing import Protocol


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

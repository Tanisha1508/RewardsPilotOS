"""Ingestion orchestration (BUILD_SPEC §6).

Pipeline per source markdown file:
parse frontmatter → strip [NEED]-marked facts (excluded until verified, logged
for the [NEED] register) → chunk by heading (~500 tokens) → embed with
all-MiniLM-L6-v2 → upsert into the doc_type's ChromaDB collection keyed on
doc_id + chunk_index → record content_hash in the knowledge_docs store.

Unchanged documents (same content_hash) are skipped.
"""

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

import chromadb

from knowledge.chunking.chunker import chunk_markdown
from knowledge.embeddings.embedder import embed_texts
from knowledge.parsers.frontmatter import SourceDoc, parse_source_file
from knowledge.pipeline.docs_store import (
    InMemoryKnowledgeDocsStore,
    KnowledgeDocRecord,
    KnowledgeDocsStore,
)
from knowledge.storage.collections import get_collection
from knowledge.validators.needs import ExcludedFact, strip_unverified_facts

SOURCES_DIR = Path(__file__).resolve().parent.parent / "sources"


@dataclass
class IngestReport:
    docs_ingested: int = 0
    docs_unchanged: int = 0
    docs_skipped_empty: int = 0
    chunks_ingested: int = 0
    excluded_facts: list[ExcludedFact] = field(default_factory=list)


def chunk_id(doc_id: str, index: int) -> str:
    return f"{doc_id}::{index}"


def _ingest_doc(doc: SourceDoc, client: chromadb.ClientAPI, report: IngestReport) -> int:
    body, excluded = strip_unverified_facts(doc.doc_id, doc.body)
    report.excluded_facts.extend(excluded)
    if not body:
        report.docs_skipped_empty += 1
        return 0
    chunks = chunk_markdown(body)
    if not chunks:
        report.docs_skipped_empty += 1
        return 0
    texts = [f"{chunk.heading}\n{chunk.content}" for chunk in chunks]
    collection = get_collection(client, doc.doc_type)
    collection.upsert(
        ids=[chunk_id(doc.doc_id, i) for i in range(len(chunks))],
        embeddings=embed_texts(texts),
        documents=texts,
        metadatas=[
            {
                "doc_id": doc.doc_id,
                "chunk_index": i,
                "issuer": doc.issuer,
                "program": doc.program,
                "doc_type": doc.doc_type,
                "source_url": doc.source_url,
                "last_changed": doc.last_changed,
            }
            for i in range(len(chunks))
        ],
    )
    _delete_orphan_chunks(collection, doc.doc_id, len(chunks))
    return len(chunks)


def _delete_orphan_chunks(collection, doc_id: str, chunk_count: int) -> None:
    """Remove chunks left behind when a document shrinks.

    upsert overwrites chunks 0..n-1 but never deletes a chunk that used to exist
    past the new end. Without this, editing a doc to remove a section leaves the
    removed content in ChromaDB, still retrievable — stale content served as
    current, which is a freshness bug, not just wasted space. Found 2026-07-21
    when splitting transfer sections out of the P1 reward_rules docs.
    """
    collection.delete(
        where={
            "$and": [
                {"doc_id": {"$eq": doc_id}},
                {"chunk_index": {"$gte": chunk_count}},
            ]
        }
    )


def ingest_sources(
    client: chromadb.ClientAPI,
    sources_dir: Path | None = None,
    docs_store: KnowledgeDocsStore | None = None,
) -> IngestReport:
    store = docs_store or InMemoryKnowledgeDocsStore()
    report = IngestReport()
    for path in sorted((sources_dir or SOURCES_DIR).glob("*.md")):
        doc = parse_source_file(path)
        content_hash = hashlib.sha256(doc.body.encode()).hexdigest()
        if store.get_hash(doc.doc_id) == content_hash:
            report.docs_unchanged += 1
            continue
        count = _ingest_doc(doc, client, report)
        if count:
            report.docs_ingested += 1
            report.chunks_ingested += count
        store.upsert(
            KnowledgeDocRecord(
                doc_id=doc.doc_id,
                source_url=doc.source_url,
                issuer=doc.issuer,
                program=doc.program,
                doc_type=doc.doc_type,
                content_hash=content_hash,
                last_changed=doc.last_changed,
            )
        )
    return report

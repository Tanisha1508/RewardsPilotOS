"""Ingestion pipeline tests: [NEED] exclusion, hashing, chunk keying."""

from datetime import date

from knowledge.pipeline.ingest import ingest_sources
from knowledge.storage.collections import COLLECTIONS, get_collection


def test_ingest_covers_fixture_corpus(ingest_report):
    assert ingest_report.docs_ingested == 13
    assert ingest_report.docs_skipped_empty == 0
    assert ingest_report.chunks_ingested >= ingest_report.docs_ingested


def test_unverified_facts_excluded_and_logged(ingest_report, chroma_client):
    # axis + amex [NEED] lines; hdfc is fully verified as of 2026-07-19
    assert len(ingest_report.excluded_facts) >= 8
    assert all("[NEED" in fact.line for fact in ingest_report.excluded_facts)
    for name in COLLECTIONS:
        data = get_collection(chroma_client, name).get(include=["documents"])
        for document in data["documents"]:
            assert "[NEED" not in document, "unverified facts must never be ingested"


def test_chunks_keyed_on_doc_id_and_index(chroma_client):
    data = get_collection(chroma_client, "reward_rules").get()
    assert data["ids"]
    for cid in data["ids"]:
        doc_id, _, index = cid.partition("::")
        assert doc_id and index.isdigit()


def test_reingest_unchanged_docs_skipped(chroma_client, docs_store, ingest_report):
    second = ingest_sources(chroma_client, docs_store=docs_store)
    assert second.docs_ingested == 0
    assert second.docs_unchanged == 13


def test_metadata_carries_citation_fields(chroma_client):
    data = get_collection(chroma_client, "transfer_rules").get(include=["metadatas"])
    for metadata in data["metadatas"]:
        assert metadata["source_url"].startswith("https://")
        date.fromisoformat(metadata["last_changed"])
        assert metadata["doc_type"] == "transfer_rules"

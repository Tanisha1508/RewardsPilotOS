"""Shrinking a document must not leave stale chunks (D3, found 2026-07-21).

upsert overwrites chunks 0..n-1 but never deletes a chunk past the new end. So
editing a doc to remove a section used to leave the removed content in ChromaDB,
still retrievable — stale content served as current. This is the freshness bug
that splitting the P1 transfer sections out of reward_rules exposed.
"""

from knowledge.pipeline.ingest import _ingest_doc, IngestReport
from knowledge.parsers.frontmatter import SourceDoc
from knowledge.storage.collections import get_client, get_collection

FRONT = dict(
    issuer="testbank",
    program="test_points",
    doc_type="reward_rules",
    source_url="https://test.example/doc",
    last_changed="2026-07-21",
    path="mem",
)

LONG_BODY = "# A\n\nalpha content\n\n# B\n\nbeta content\n\n# C\n\ngamma content REMOVED_LATER"
SHORT_BODY = "# A\n\nalpha content\n\n# B\n\nbeta content"


def _doc(body: str) -> SourceDoc:
    return SourceDoc(doc_id="shrink_test_reward_rules", body=body, **FRONT)


def test_removed_section_does_not_survive_re_ingest(tmp_path):
    client = get_client(tmp_path / "chroma")
    collection = get_collection(client, "reward_rules")

    _ingest_doc(_doc(LONG_BODY), client, IngestReport())
    before = collection.get(where={"doc_id": {"$eq": "shrink_test_reward_rules"}})
    assert len(before["ids"]) == 3
    assert any("REMOVED_LATER" in d for d in before["documents"])

    # Shrink the doc: section C is gone.
    _ingest_doc(_doc(SHORT_BODY), client, IngestReport())
    after = collection.get(where={"doc_id": {"$eq": "shrink_test_reward_rules"}})

    assert len(after["ids"]) == 2  # orphan chunk removed
    assert not any(
        "REMOVED_LATER" in d for d in after["documents"]
    ), "removed content is still in the index — stale content served as current"


def test_growing_a_document_keeps_all_chunks(tmp_path):
    """The fix must not over-delete: a doc that grows keeps every chunk."""
    client = get_client(tmp_path / "chroma")
    collection = get_collection(client, "reward_rules")

    _ingest_doc(_doc(SHORT_BODY), client, IngestReport())
    _ingest_doc(_doc(LONG_BODY), client, IngestReport())
    after = collection.get(where={"doc_id": {"$eq": "shrink_test_reward_rules"}})
    assert len(after["ids"]) == 3

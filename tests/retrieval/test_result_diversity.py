"""A comparison question must not come back with evidence about one card
(A11, 2026-07-31).

Measured failure: "which card should I use to book a hotel" returned six chunks
that were **all Amex Platinum Travel**, four of them from a single document, with
the top hit about income eligibility. The question is which card to use, and the
evidence covered one.

The scores made it worse: 0.0293 / 0.0292 / 0.0284 across the top three. When
scores are that tightly clustered the ordering is close to arbitrary, so
"whichever document happens to have the most chunks" wins on volume rather than
relevance.

`_diversify` takes each document's best chunks up to `MAX_PER_DOC` first, then
backfills. Breadth where it exists; full depth where it does not.
"""

from knowledge.retrieval.hybrid import HybridRetriever
from tools.knowledge_search.service import get_retriever

COMPARISONS = [
    "which card should I use to book a hotel",
    "which of my cards earns the most on flights",
    "what is the best card for online shopping",
    "which card gives the most value for travel",
]


def test_no_single_document_dominates_the_evidence():
    retriever = get_retriever()
    for query in COMPARISONS:
        chunks = retriever.search(query, k=5)
        per_doc: dict[str, int] = {}
        for chunk in chunks:
            per_doc[chunk.metadata.doc_id] = per_doc.get(chunk.metadata.doc_id, 0) + 1
        worst = max(per_doc.values())
        assert (
            worst <= HybridRetriever.MAX_PER_DOC
        ), f"{query!r}: one document supplied {worst} of {len(chunks)} chunks"


def test_a_comparison_question_sees_more_than_one_card():
    """The failure in its own terms. Before the diversity pass, the hotel query
    returned a single issuer."""
    retriever = get_retriever()
    for query in COMPARISONS:
        issuers = {c.metadata.issuer for c in retriever.search(query, k=5)}
        assert len(issuers) >= 2, f"{query!r} returned evidence for only {issuers}"


def test_diversity_never_returns_fewer_results():
    """The guard on the guard. Backfill means a query whose answer genuinely
    lives in one document still fills its slots from that document — narrowing
    the sources must not narrow the evidence."""
    retriever = get_retriever()
    for query in ("Axis Atlas transfer partners", "HDFC Infinia SmartBuy caps", *COMPARISONS):
        capped = len(retriever.search(query, k=5))

        original = HybridRetriever.MAX_PER_DOC
        HybridRetriever.MAX_PER_DOC = 99
        try:
            uncapped = len(retriever.search(query, k=5))
        finally:
            HybridRetriever.MAX_PER_DOC = original

        assert capped == uncapped, f"{query!r}: diversity dropped results ({capped} < {uncapped})"


def test_a_single_document_answer_still_gets_depth():
    """A question answered by one document should still draw several chunks from
    it — the cap reorders, it does not exclude."""
    chunks = get_retriever().search("Axis Atlas transfer partners and minimums", k=5)
    assert len(chunks) == 5
    assert any(c.metadata.doc_id == "axis_atlas_transfer_rules" for c in chunks)

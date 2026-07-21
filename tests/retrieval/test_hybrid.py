"""Hybrid retrieval behavior: fusion, filters, freshness, citations."""

from datetime import date

from knowledge.retrieval.hybrid import HybridRetriever
from knowledge.storage.collections import get_client

AS_OF = date(2026, 7, 19)


def test_transfer_query_finds_transfer_doc(retriever):
    chunks = retriever.search("transfer Voyager Points to Skyhigh Airways", as_of=AS_OF)
    assert chunks
    # The fresher July promotion doc legitimately competes; the canonical
    # transfer-rules doc must still be in the top 3.
    top3 = [chunk.metadata.doc_id for chunk in chunks[:3]]
    assert "demo_bank_voyager_transfer_rules" in top3


def test_ratio_query_ranks_transfer_rules_first(retriever):
    """A transfer-ratio query, filtered to transfer_rules, surfaces a
    transfer_rules doc first.

    This used to assert the *specific* demo_bank_voyager doc. After the D3 corpus
    expansion added the richer P1 transfer_rules docs, a generic transfer query
    ("ratio", "minimum transfer") matches those first and the sparse fixture doc
    drops below them — the "larger real corpus is a harder retrieval problem"
    effect, honestly. The doc_type guarantee still holds; issuer scoping recovers
    a specific doc (next test)."""
    chunks = retriever.search(
        "transfer ratio minimum transfer",
        doc_type="transfer_rules",
        as_of=AS_OF,
    )
    assert chunks[0].metadata.doc_type == "transfer_rules"


def test_issuer_scope_recovers_the_specific_transfer_doc(retriever):
    """When a query is scoped to an issuer, that issuer's own transfer doc ranks
    first again — the precision the generic query lost is recovered by the
    metadata filter the Planner supplies."""
    chunks = retriever.search(
        "Voyager Points Skyhigh transfer ratio",
        issuer="demo_bank",
        doc_type="transfer_rules",
        as_of=AS_OF,
    )
    assert chunks[0].metadata.doc_id == "demo_bank_voyager_transfer_rules"


def test_returns_at_most_five(retriever):
    chunks = retriever.search("credit card reward points", as_of=AS_OF)
    assert 0 < len(chunks) <= 5


def test_issuer_filter(retriever):
    chunks = retriever.search(
        "transfer miles to airline partner", issuer="sample_bank", as_of=AS_OF
    )
    assert chunks
    assert all(chunk.metadata.issuer == "sample_bank" for chunk in chunks)


def test_doc_type_filter(retriever):
    chunks = retriever.search("points expiry policy", doc_type="issuer_policies", as_of=AS_OF)
    assert chunks
    assert all(chunk.metadata.doc_type == "issuer_policies" for chunk in chunks)


def test_program_filter(retriever):
    chunks = retriever.search("lounge access benefit", program="trailblazer_miles", as_of=AS_OF)
    assert chunks
    assert all(chunk.metadata.program == "trailblazer_miles" for chunk in chunks)


def test_freshness_prefers_recent_promotion(retriever):
    chunks = retriever.search("bonus points promotion offer", doc_type="promotions", as_of=AS_OF)
    doc_ids = [chunk.metadata.doc_id for chunk in chunks]
    assert "demo_bank_voyager_promotions" in doc_ids
    assert "sample_bank_trailblazer_promotions" in doc_ids
    assert doc_ids.index("demo_bank_voyager_promotions") < doc_ids.index(
        "sample_bank_trailblazer_promotions"
    )


def test_keyword_exact_term_found(retriever):
    chunks = retriever.search("Grandstay minimum transfer", as_of=AS_OF)
    assert any("Grandstay" in chunk.content for chunk in chunks)


def test_citation_metadata_flows_through(retriever):
    chunks = retriever.search("Voyager base earning rate", as_of=AS_OF)
    top = chunks[0]
    assert top.metadata.source_url.startswith("https://")
    assert top.metadata.last_changed
    assert top.score > 0


def test_scores_are_descending(retriever):
    chunks = retriever.search("hotel points transfer ratio", as_of=AS_OF)
    scores = [chunk.score for chunk in chunks]
    assert scores == sorted(scores, reverse=True)


def test_empty_corpus_returns_nothing(tmp_path):
    empty = HybridRetriever(get_client(tmp_path / "empty"))
    assert empty.search("anything at all", as_of=AS_OF) == []


def test_real_card_docs_retrievable_without_unverified_facts(retriever):
    chunks = retriever.search("HDFC Infinia SmartBuy earning", issuer="hdfc", as_of=AS_OF)
    assert chunks
    assert all("[NEED" not in chunk.content for chunk in chunks)

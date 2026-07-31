"""Inferred retrieval filters may narrow, never subtract (A10, 2026-07-31).

Retrieval ran unfiltered, which is how an Amex question could come back with
Axis rules — fixed by hand on the Redeem page on 2026-07-30. Inferring the
filter fixes the class.

The risk it introduces is the opposite one, and it is worse: a *wrong* filter
does not degrade an answer, it deletes the evidence, and the recommender then
correctly reports having nothing — which a reader cannot tell apart from the
corpus genuinely not covering their question.

The module shipped unwired with two live instances of exactly that:
`promotions` and `issuer_policies` are empty in the serving corpus since the
fixture issuers were excluded (KL 35), and the hint map sent "bonus" and
"expire" straight into them.
"""

import pytest

from agents.knowledge.behavior import available_doc_types, infer_filters
from contracts.tools.knowledge_search import SearchKnowledgeInput
from tools.knowledge_search.tools import search_knowledge


def test_empty_collections_are_not_offered_as_filters():
    """Derived from the corpus, not declared — so a collection that empties out
    stops being offered without anyone noticing and editing a list."""
    available = available_doc_types()
    assert "reward_rules" in available
    assert "promotions" not in available, "promotions is empty since KL 35"
    assert "issuer_policies" not in available, "issuer_policies is empty since KL 35"


@pytest.mark.parametrize(
    "query",
    [
        "which card gives a bonus on flights",  # 'bonus' -> promotions (empty)
        "when do my points expire",  # 'expire' -> issuer_policies (empty)
        "what is the policy on point expiry",
    ],
)
def test_the_words_that_used_to_empty_the_results_no_longer_do(query):
    """These are ordinary questions. Before, each filtered to an empty
    collection and returned nothing."""
    assert "doc_type" not in infer_filters(query)
    assert search_knowledge(SearchKnowledgeInput(query=query, k=4)).chunks


def test_an_issuer_question_is_scoped_to_that_issuer():
    """The Redeem cross-issuer defect, fixed as a class rather than an instance."""
    out = search_knowledge(SearchKnowledgeInput(query="amex transfer partners", k=5))

    assert out.chunks
    assert {c.metadata.issuer for c in out.chunks} == {"amex"}


def test_a_filter_that_finds_nothing_falls_back_to_unfiltered():
    """The guard that makes inference safe.

    'axis lounge access' infers issuer=axis + doc_type=benefit_guides, and the
    only benefit_guides document belongs to amex — so the filtered search finds
    nothing and the unfiltered retry must supply the answer."""
    inferred = infer_filters("axis lounge access")
    assert inferred == {"issuer": "axis", "doc_type": "benefit_guides"}

    out = search_knowledge(SearchKnowledgeInput(query="axis lounge access", k=4))

    assert out.chunks, "an inferred filter was allowed to delete the evidence"


def test_an_explicit_empty_result_is_left_alone():
    """The other half. A caller that asks for a slice gets that slice, and 'no
    documents of this type for this issuer' is a real answer to a real
    question — not something to paper over with an unfiltered retry."""
    out = search_knowledge(
        SearchKnowledgeInput(query="lounge access", issuer="axis", doc_type="benefit_guides", k=4)
    )
    assert out.chunks == []


def test_a_query_with_no_hint_is_not_narrowed():
    assert infer_filters("how many points for a hotel booking") == {}


def test_the_longest_hint_wins():
    """'american express' must not lose to a stray 'amex' earlier in the map.
    The previous version depended on dict insertion order."""
    assert infer_filters("american express membership rewards")["issuer"] == "amex"


def test_no_hint_points_at_an_issuer_the_corpus_lacks():
    """The stale-map failure, locked shut. Every issuer hint must resolve to an
    issuer that is actually in the serving corpus."""
    from knowledge.parsers.frontmatter import parse_source_file
    from knowledge.pipeline.ingest import SOURCES_DIR, is_fixture

    from agents.knowledge.behavior import _ISSUER_HINTS

    real = {
        doc.issuer
        for path in SOURCES_DIR.glob("*.md")
        if not is_fixture(doc := parse_source_file(path))
    }
    assert (
        set(_ISSUER_HINTS.values()) <= real
    ), f"hints point at issuers not in the corpus: {set(_ISSUER_HINTS.values()) - real}"

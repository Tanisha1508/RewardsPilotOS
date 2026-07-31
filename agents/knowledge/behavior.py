"""Metadata filter inference for hybrid retrieval (BUILD_SPEC §6 step 3).

Written early, never called, and wired on 2026-07-31 (backlog A10). Wiring it
first required fixing two things that would each have made retrieval worse than
leaving it unfiltered.

**1. The issuer map pointed at issuers that no longer exist.** It mapped
"voyager" to `demo_bank` and "trailblazer" to `sample_bank` — the invented
fixture issuers excluded from the serving corpus by KNOWN_LIMITATIONS 35. A
query naming one would have filtered retrieval down to nothing.

**2. The doc_type map routed common words into empty collections.** Both
`promotions` and `issuer_policies` existed *only* as fixture documents, so after
KL 35 they hold nothing — and the map sent "bonus" and "offer" to `promotions`,
and "expire" and "policy" to `issuer_policies`. "Which card gives a bonus on
flights" and "when do my points expire" are ordinary questions, and both would
have returned zero chunks where unfiltered retrieval returns useful ones.

That is the general hazard with an inferred filter: a wrong one does not degrade
an answer, it deletes the evidence. The recommender then correctly reports that
it has nothing — indistinguishable from the corpus genuinely lacking the answer.
Silence that looks like an answer, which is the failure this product keeps
having to design against.

Two guards, because either alone is one edit from failing:

* the doc types available for filtering are **derived from the corpus**, so a
  collection that empties stops being offered automatically; and
* the caller **falls back to unfiltered retrieval when a filter returns
  nothing** (`tools/knowledge_search/tools.py`).

`bonus` was dropped from the hints entirely. Even with a populated promotions
collection it is the wrong signal — "bonus rate", "bonus category" and "welcome
bonus" are ordinary reward-rules vocabulary, and only the last is a promotion.
"""

from functools import lru_cache

# Query wording -> issuer id, for issuers actually in the serving corpus.
#
# No fixture issuers. If one is ever re-admitted it belongs here and in
# `knowledge/pipeline/ingest.py` in the same change — a hint for an issuer the
# corpus does not hold is a filter that returns nothing.
_ISSUER_HINTS: dict[str, str] = {
    "hdfc": "hdfc",
    "infinia": "hdfc",
    "diners": "hdfc",
    "regalia": "hdfc",
    "axis": "axis",
    "atlas": "axis",
    "magnus": "axis",
    "amex": "amex",
    "american express": "amex",
    "platinum travel": "amex",
    "smartearn": "amex",
    "membership rewards": "amex",
}

# Query wording -> doc_type. Only consulted for types the corpus actually holds.
_DOC_TYPE_HINTS: dict[str, str] = {
    "transfer": "transfer_rules",
    "partner": "transfer_rules",
    "convert": "transfer_rules",
    "promotion": "promotions",
    "offer": "promotions",
    "lounge": "benefit_guides",
    "benefit": "benefit_guides",
    "insurance": "benefit_guides",
    "expiry": "issuer_policies",
    "expire": "issuer_policies",
    "policy": "issuer_policies",
}


@lru_cache(maxsize=1)
def available_doc_types() -> frozenset[str]:
    """Doc types present in the serving corpus.

    Read from the source files rather than declared, so a collection that
    empties out — as `promotions` and `issuer_policies` did when the fixture
    issuers were excluded — stops being offered as a filter on its own, instead
    of waiting for someone to notice and edit a list here.
    """
    from knowledge.parsers.frontmatter import parse_source_file
    from knowledge.pipeline.ingest import SOURCES_DIR, is_fixture

    return frozenset(
        doc.doc_type
        for path in SOURCES_DIR.glob("*.md")
        if not is_fixture(doc := parse_source_file(path))
    )


def infer_filters(query: str) -> dict[str, str]:
    """Best-effort metadata filters for a query. May be empty; must never be wrong.

    Longest hint first, so "american express" is not beaten by a stray "amex"
    appearing earlier in the map. The previous version took whichever key came
    first in insertion order, which made the result depend on typing order.
    """
    lowered = query.lower()
    filters: dict[str, str] = {}

    for hint in sorted(_ISSUER_HINTS, key=len, reverse=True):
        if hint in lowered:
            filters["issuer"] = _ISSUER_HINTS[hint]
            break

    available = available_doc_types()
    for hint in sorted(_DOC_TYPE_HINTS, key=len, reverse=True):
        if hint in lowered and _DOC_TYPE_HINTS[hint] in available:
            filters["doc_type"] = _DOC_TYPE_HINTS[hint]
            break

    return filters

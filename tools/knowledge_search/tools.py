"""Knowledge tools: SearchKnowledge, GetPromotions."""

from pydantic import BaseModel, Field

from contracts.tools.knowledge_search import (
    RetrievedChunk,
    SearchKnowledgeInput,
    SearchKnowledgeOutput,
)
from agents.knowledge.behavior import infer_filters
from tools.knowledge_search.service import get_retriever


def search_knowledge(args: SearchKnowledgeInput) -> SearchKnowledgeOutput:
    """Retrieve, narrowing by issuer/doc_type when the query makes it obvious.

    Filters are inferred only when the caller supplied none (A10, 2026-07-31).
    An explicit filter is an instruction and is never second-guessed; an
    inferred one is a guess, and is treated like one.

    Retrieval ran unfiltered until now, which is how a question about Amex could
    come back with Axis rules — the defect fixed on the Redeem page on
    2026-07-30 by scoping that one call by hand. Inferring the filter fixes the
    class rather than the instance.

    **The fallback is the point.** A wrong filter does not produce a worse
    answer, it produces no evidence at all, and the recommender then honestly
    says it has nothing — which a reader cannot tell apart from the corpus
    genuinely not covering their question. So an inferred filter that returns
    nothing is discarded and the search is repeated without it. Narrowing may
    only ever help; it may never subtract.

    An *explicit* empty result is left alone: the caller asked for that slice,
    and "no promotions for this issuer" is a real answer to a real question.
    """
    caller_filtered = any((args.issuer, args.program, args.doc_type))
    inferred = {} if caller_filtered else infer_filters(args.query)

    chunks = get_retriever().search(
        args.query,
        issuer=args.issuer or inferred.get("issuer"),
        program=args.program,
        doc_type=args.doc_type or inferred.get("doc_type"),
        k=args.k,
    )

    if not chunks and inferred:
        chunks = get_retriever().search(args.query, program=args.program, k=args.k)

    return SearchKnowledgeOutput(chunks=chunks)


class GetPromotionsInput(BaseModel):
    query: str = Field(default="current promotions and transfer bonuses")
    issuer: str | None = None
    k: int = Field(default=5, ge=1, le=20)


class GetPromotionsOutput(BaseModel):
    promotions: list[RetrievedChunk] = Field(default_factory=list)


def get_promotions(args: GetPromotionsInput) -> GetPromotionsOutput:
    chunks = get_retriever().search(args.query, issuer=args.issuer, doc_type="promotions", k=args.k)
    return GetPromotionsOutput(promotions=chunks)

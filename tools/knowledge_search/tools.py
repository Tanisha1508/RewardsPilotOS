"""Knowledge tools: SearchKnowledge, GetPromotions."""

from pydantic import BaseModel, Field

from contracts.tools.knowledge_search import (
    RetrievedChunk,
    SearchKnowledgeInput,
    SearchKnowledgeOutput,
)
from tools.knowledge_search.service import get_retriever


def search_knowledge(args: SearchKnowledgeInput) -> SearchKnowledgeOutput:
    chunks = get_retriever().search(
        args.query,
        issuer=args.issuer,
        program=args.program,
        doc_type=args.doc_type,
        k=args.k,
    )
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

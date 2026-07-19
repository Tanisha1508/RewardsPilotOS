"""Knowledge search tool contracts (BUILD_SPEC §6, §8).

RetrievedChunk metadata flows verbatim into recommendation citations:
source_url + last_changed become the citation source and freshness timestamp.
"""

from pydantic import BaseModel, Field


class ChunkMetadata(BaseModel):
    doc_id: str
    issuer: str
    program: str
    doc_type: str
    source_url: str
    last_changed: str  # ISO date


class RetrievedChunk(BaseModel):
    doc_id: str
    chunk_index: int
    content: str
    score: float
    metadata: ChunkMetadata


class SearchKnowledgeInput(BaseModel):
    query: str = Field(min_length=1)
    issuer: str | None = None
    program: str | None = None
    doc_type: str | None = None
    k: int = Field(default=5, ge=1, le=20)


class SearchKnowledgeOutput(BaseModel):
    chunks: list[RetrievedChunk] = Field(default_factory=list)

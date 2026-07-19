"""Hybrid retrieval (BUILD_SPEC §6):

1. Semantic: ChromaDB top-k (k=10) across the relevant collection(s)
2. Keyword: BM25 over the same corpus (in-memory, rebuilt on ingest)
3. Metadata filter: issuer / program / doc_type
4. Fusion: reciprocal rank fusion of semantic + keyword rankings
5. Freshness re-rank: fused score * decay(last_changed), half-life 180d, floor 0.5
6. Return top 5 with metadata; citations flow through verbatim
"""

import re
from datetime import date

import chromadb
from rank_bm25 import BM25Okapi

from contracts.tools.knowledge_search import ChunkMetadata, RetrievedChunk
from knowledge.embeddings.embedder import embed_query
from knowledge.freshness.decay import freshness_factor
from knowledge.ranking.fusion import reciprocal_rank_fusion
from knowledge.storage.collections import COLLECTIONS, get_collection

SEMANTIC_K = 10
KEYWORD_K = 10
FINAL_K = 5

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _metadata_matches(
    metadata: dict, issuer: str | None, program: str | None, doc_type: str | None
) -> bool:
    if issuer and metadata.get("issuer") != issuer:
        return False
    if program and metadata.get("program") != program:
        return False
    if doc_type and metadata.get("doc_type") != doc_type:
        return False
    return True


class HybridRetriever:
    """Loads the full corpus from ChromaDB at construction and keeps the BM25
    index in memory. Rebuild by constructing a new instance after ingest."""

    def __init__(self, client: chromadb.ClientAPI) -> None:
        self._client = client
        self._documents: dict[str, str] = {}
        self._metadata: dict[str, dict] = {}
        for name in COLLECTIONS:
            collection = get_collection(client, name)
            data = collection.get(include=["documents", "metadatas"])
            for cid, document, metadata in zip(
                data["ids"], data["documents"], data["metadatas"]
            ):
                self._documents[cid] = document
                self._metadata[cid] = metadata
        self._bm25_ids = list(self._documents)
        corpus = [_tokenize(self._documents[cid]) for cid in self._bm25_ids]
        self._bm25 = BM25Okapi(corpus) if corpus else None

    def _semantic_ranking(
        self, query: str, issuer: str | None, program: str | None, doc_type: str | None
    ) -> list[str]:
        conditions = []
        if issuer:
            conditions.append({"issuer": {"$eq": issuer}})
        if program:
            conditions.append({"program": {"$eq": program}})
        where = None
        if len(conditions) == 1:
            where = conditions[0]
        elif conditions:
            where = {"$and": conditions}
        names = [doc_type] if doc_type in COLLECTIONS else list(COLLECTIONS)
        embedding = embed_query(query)
        scored: list[tuple[float, str]] = []
        for name in names:
            collection = get_collection(self._client, name)
            if collection.count() == 0:
                continue
            result = collection.query(
                query_embeddings=[embedding],
                n_results=min(SEMANTIC_K, collection.count()),
                where=where,
                include=["distances"],
            )
            scored.extend(zip(result["distances"][0], result["ids"][0]))
        scored.sort(key=lambda pair: pair[0])  # cosine distance: lower is closer
        return [cid for _, cid in scored[:SEMANTIC_K]]

    def _keyword_ranking(
        self, query: str, issuer: str | None, program: str | None, doc_type: str | None
    ) -> list[str]:
        if self._bm25 is None:
            return []
        scores = self._bm25.get_scores(_tokenize(query))
        ranked = sorted(
            (
                (score, cid)
                for score, cid in zip(scores, self._bm25_ids)
                if score > 0
                and _metadata_matches(self._metadata[cid], issuer, program, doc_type)
            ),
            key=lambda pair: -pair[0],
        )
        return [cid for _, cid in ranked[:KEYWORD_K]]

    def search(
        self,
        query: str,
        issuer: str | None = None,
        program: str | None = None,
        doc_type: str | None = None,
        k: int = FINAL_K,
        as_of: date | None = None,
    ) -> list[RetrievedChunk]:
        as_of = as_of or date.today()
        semantic = self._semantic_ranking(query, issuer, program, doc_type)
        keyword = self._keyword_ranking(query, issuer, program, doc_type)
        fused = reciprocal_rank_fusion([semantic, keyword])
        reranked = sorted(
            (
                (
                    score * freshness_factor(self._metadata[cid]["last_changed"], as_of),
                    cid,
                )
                for cid, score in fused.items()
            ),
            key=lambda pair: -pair[0],
        )
        chunks: list[RetrievedChunk] = []
        for score, cid in reranked[:k]:
            metadata = self._metadata[cid]
            chunks.append(
                RetrievedChunk(
                    doc_id=metadata["doc_id"],
                    chunk_index=metadata["chunk_index"],
                    content=self._documents[cid],
                    score=round(score, 6),
                    metadata=ChunkMetadata(
                        doc_id=metadata["doc_id"],
                        issuer=metadata["issuer"],
                        program=metadata["program"],
                        doc_type=metadata["doc_type"],
                        source_url=metadata["source_url"],
                        last_changed=metadata["last_changed"],
                    ),
                )
            )
        return chunks

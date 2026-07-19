"""Shared retriever singleton for knowledge tools.

Lazily ingests the seed corpus into the ChromaDB persist dir on first use if
the collections are empty, then serves a single HybridRetriever instance."""

from functools import lru_cache
from pathlib import Path

from knowledge.pipeline.ingest import ingest_sources
from knowledge.retrieval.hybrid import HybridRetriever
from knowledge.storage.collections import COLLECTIONS, get_client, get_collection


@lru_cache(maxsize=1)
def get_retriever(persist_dir: str | None = None) -> HybridRetriever:
    client = get_client(Path(persist_dir) if persist_dir else None)
    if all(get_collection(client, name).count() == 0 for name in COLLECTIONS):
        ingest_sources(client)
    return HybridRetriever(client)

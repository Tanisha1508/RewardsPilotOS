"""Shared retriever singleton for knowledge tools.

Lazily ingests the seed corpus into the ChromaDB persist dir on first use if
the collections are empty, then serves a single HybridRetriever instance."""

from functools import lru_cache
from pathlib import Path

from knowledge.pipeline.ingest import ingest_sources
from knowledge.retrieval.hybrid import HybridRetriever
from knowledge.storage.collections import COLLECTIONS, get_client, get_collection


@lru_cache(maxsize=1)
def _default_retriever(persist_dir: str | None = None) -> HybridRetriever:
    client = get_client(Path(persist_dir) if persist_dir else None)
    if all(get_collection(client, name).count() == 0 for name in COLLECTIONS):
        ingest_sources(client)
    return HybridRetriever(client)


def get_retriever(persist_dir: str | None = None) -> HybridRetriever:
    return _override if _override is not None else _default_retriever(persist_dir)


# Test/eval override, mirroring `set_source` for the portfolio and memory
# sources — which the e2e eval already injects. Retrieval was the one dependency
# it could not swap, so it ran against whatever the serving corpus happened to
# hold.
#
# That mattered on 2026-07-31: excluding the fixture issuers from the serving
# corpus (KNOWN_LIMITATIONS 35) emptied the `promotions` and `issuer_policies`
# collections, and two golden queries — "any transfer bonuses or promotions
# right now?" and "when do my points expire?" — went from answerable to
# uncitable. The pipeline was fine; its corpus had changed underneath it.
_override: "HybridRetriever | None" = None


def set_retriever(retriever) -> None:
    """Point `get_retriever()` at a specific instance, or None to restore."""
    global _override
    _override = retriever

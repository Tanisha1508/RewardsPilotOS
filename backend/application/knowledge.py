"""Knowledge search orchestration (BUILD_SPEC §6, §9).

Thin by design: the retrieval itself is a deterministic tool
(`tools/knowledge_search`), and business logic stays out of the router
(BUILD_SPEC §3). This layer only adapts the HTTP query into the tool's input
and hands back the tool's output.

The retriever is a process-lifetime singleton that loads the corpus from the
production ChromaDB persist dir and keeps a BM25 index in memory; a fresh
instance is what picks up a re-ingest, so a long-running API process serves the
corpus as it was at startup until restarted (noted in KNOWN_LIMITATIONS).
"""

from contracts.tools.knowledge_search import SearchKnowledgeInput, SearchKnowledgeOutput
from tools.knowledge_search.tools import search_knowledge


def search(
    query: str,
    issuer: str | None = None,
    program: str | None = None,
    doc_type: str | None = None,
    k: int = 5,
) -> SearchKnowledgeOutput:
    args = SearchKnowledgeInput(query=query, issuer=issuer, program=program, doc_type=doc_type, k=k)
    return search_knowledge(args)

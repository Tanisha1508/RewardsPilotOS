import pytest

from knowledge.pipeline.docs_store import InMemoryKnowledgeDocsStore
from knowledge.pipeline.ingest import IngestReport, ingest_sources
from knowledge.retrieval.hybrid import HybridRetriever
from knowledge.storage.collections import get_client


@pytest.fixture(scope="session")
def docs_store() -> InMemoryKnowledgeDocsStore:
    return InMemoryKnowledgeDocsStore()


@pytest.fixture(scope="session")
def chroma_client(tmp_path_factory, docs_store):
    return get_client(tmp_path_factory.mktemp("chroma"))


@pytest.fixture(scope="session")
def ingest_report(chroma_client, docs_store) -> IngestReport:
    return ingest_sources(chroma_client, docs_store=docs_store)


@pytest.fixture(scope="session")
def retriever(chroma_client, ingest_report) -> HybridRetriever:
    return HybridRetriever(chroma_client)

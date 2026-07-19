"""Sentence-transformers embedder (all-MiniLM-L6-v2, BUILD_SPEC §6).

The model is loaded lazily and cached at module level so ingestion and
retrieval share one instance."""

from functools import lru_cache

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(MODEL_NAME)


def embed_texts(texts: list[str]) -> list[list[float]]:
    return [vector.tolist() for vector in _model().encode(texts, show_progress_bar=False)]


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]

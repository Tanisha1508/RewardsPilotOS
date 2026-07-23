"""fastembed (ONNX) embedder — all-MiniLM-L6-v2, 384-dim (BUILD_SPEC §6).

Swapped from sentence-transformers/torch on 2026-07-23: the same MiniLM model
served through onnxruntime instead of torch. Torch alone held ~370 MB resident
and pushed the serving process to ~683 MB peak on the first knowledge search —
over every free hosting tier's 512 MB ceiling. Same vector space and dimension,
so the two call sites (`ingest.py`, `hybrid.py`) are unchanged.

ONNX output is numerically close but not bit-identical to the torch build, so a
corpus embedded under torch must not be queried under fastembed: wipe and
re-ingest any persisted ChromaDB dir from before the swap. In deployment this
is automatic — the corpus re-ingests lazily on first search (ephemeral disk).

The model is loaded lazily and cached at module level so ingestion and
retrieval share one instance.
"""

from functools import lru_cache

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _model():
    from fastembed import TextEmbedding

    return TextEmbedding(model_name=MODEL_NAME)


def embed_texts(texts: list[str]) -> list[list[float]]:
    return [vector.tolist() for vector in _model().embed(texts)]


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]

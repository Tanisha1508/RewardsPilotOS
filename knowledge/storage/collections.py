"""ChromaDB collection definitions (BUILD_SPEC §6).

Five collections, one per doc_type. Chunk metadata: issuer, program, doc_type,
source_url, last_changed (ISO date), doc_id. Persistent client on local disk
(data/embeddings/ in dev, /data/chroma on Render)."""

import os
from pathlib import Path

import chromadb

COLLECTIONS = (
    "reward_rules",
    "transfer_rules",
    "promotions",
    "benefit_guides",
    "issuer_policies",
)

DEFAULT_PERSIST_DIR = Path(os.environ.get("CHROMA_PERSIST_DIR", "data/embeddings"))


def get_client(persist_dir: Path | None = None) -> chromadb.ClientAPI:
    path = Path(persist_dir or DEFAULT_PERSIST_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(path))


def get_collection(client: chromadb.ClientAPI, doc_type: str) -> chromadb.Collection:
    if doc_type not in COLLECTIONS:
        raise ValueError(f"unknown collection '{doc_type}', expected one of {COLLECTIONS}")
    return client.get_or_create_collection(name=doc_type, metadata={"hnsw:space": "cosine"})

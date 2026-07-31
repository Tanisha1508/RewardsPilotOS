"""Retrieval golden set runner: precision@3, recall@5, MRR (BUILD_SPEC §11).

Runs against a corpus that **includes the fixture issuers**, and must keep doing
so. This is a benchmark of the retrieval *algorithm* — ranking, filtering,
freshness — and that needs a corpus with known, hand-labelled relevance. The
`demo_bank` and `sample_bank` documents exist for exactly this; 17 of the 24
golden queries are about them.

Broken and repaired on 2026-07-31. Excluding fixtures from the serving corpus
(KNOWN_LIMITATIONS 35, so an invented issuer could never be cited to a user)
also silently emptied this benchmark, because it used the shared production
retriever. recall@5 fell from **1.000 to 0.292** — not because retrieval got
worse, but because most expected documents had left the corpus. Measured, not
guessed.

**What this eval does NOT tell you:** how well retrieval works on real questions
about the three real cards. That needs golden queries over the production
documents, and there are only seven of those here. Do not read a good score as
evidence about production quality.
"""

import json
from datetime import date
from pathlib import Path

from knowledge.pipeline.ingest import ingest_sources
from knowledge.retrieval.hybrid import HybridRetriever
from knowledge.storage.collections import get_client

DATASET = Path(__file__).resolve().parent.parent / "datasets" / "retrieval.json"
AS_OF = date(2026, 7, 19)  # pinned so eval results are reproducible


def _ranked_doc_ids(chunks) -> list[str]:
    seen: list[str] = []
    for chunk in chunks:
        if chunk.metadata.doc_id not in seen:
            seen.append(chunk.metadata.doc_id)
    return seen


def _benchmark_retriever() -> HybridRetriever:
    """A throwaway corpus WITH fixtures, isolated from the serving index.

    Its own temp directory on purpose: reusing the production persist dir would
    write invented issuers back into the index this eval is not allowed to
    pollute.
    """
    import tempfile

    tmp = tempfile.mkdtemp(prefix="retrieval-eval-")
    client = get_client(Path(tmp))
    ingest_sources(client, include_fixtures=True)
    return HybridRetriever(client)


def run() -> dict:
    dataset = json.loads(DATASET.read_text())
    retriever = _benchmark_retriever()
    per_query = []
    for item in dataset["queries"]:
        expected = set(item["expected_doc_ids"])
        ranked = _ranked_doc_ids(retriever.search(item["query"], k=10, as_of=AS_OF))
        top3 = ranked[:3]
        top5 = ranked[:5]
        precision3 = len(expected & set(top3)) / 3
        recall5 = len(expected & set(top5)) / len(expected)
        reciprocal = 0.0
        for rank, doc_id in enumerate(ranked, start=1):
            if doc_id in expected:
                reciprocal = 1.0 / rank
                break
        per_query.append(
            {
                "id": item["id"],
                "precision_at_3": round(precision3, 4),
                "recall_at_5": round(recall5, 4),
                "reciprocal_rank": round(reciprocal, 4),
                "ranked": ranked[:5],
            }
        )
    count = len(per_query)
    return {
        "name": "retrieval",
        "queries": count,
        "precision_at_3": round(sum(q["precision_at_3"] for q in per_query) / count, 4),
        "recall_at_5": round(sum(q["recall_at_5"] for q in per_query) / count, 4),
        "mrr": round(sum(q["reciprocal_rank"] for q in per_query) / count, 4),
        "per_query": per_query,
    }

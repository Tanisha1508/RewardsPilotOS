"""Retrieval golden set runner: precision@3, recall@5, MRR (BUILD_SPEC §11)."""

import json
from datetime import date
from pathlib import Path

from tools.knowledge_search.service import get_retriever

DATASET = Path(__file__).resolve().parent.parent / "datasets" / "retrieval.json"
AS_OF = date(2026, 7, 19)  # pinned so eval results are reproducible


def _ranked_doc_ids(chunks) -> list[str]:
    seen: list[str] = []
    for chunk in chunks:
        if chunk.metadata.doc_id not in seen:
            seen.append(chunk.metadata.doc_id)
    return seen


def run() -> dict:
    dataset = json.loads(DATASET.read_text())
    retriever = get_retriever()
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

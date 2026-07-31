"""Retrieval quality on the corpus a real user actually reaches.

The companion to `retrieval_eval.py`, and the two must not be confused:

* `retrieval_eval` benchmarks the retrieval *algorithm* against a controlled
  corpus that includes the fixture issuers. 17 of its 24 queries are about
  `demo_bank` and `sample_bank`. A good score there says ranking works; it says
  nothing about what a cardholder gets.
* **this** runs the serving corpus — 14 verified documents, no fixtures — with
  questions phrased the way a cardholder asks them.

Written 2026-07-31, after the owner asked how a benchmark over invented banks
could tell us anything about real queries. It cannot.

Reported per query as well as in aggregate, because the aggregate hides the
thing worth knowing: *which* questions retrieval fails, and whether they cluster
(one document, one doc_type, one phrasing style). An average of 0.6 tells you to
worry; a list of failures tells you what to fix.
"""

import json
from pathlib import Path

DATASET = Path(__file__).resolve().parent.parent / "datasets" / "retrieval_production.json"


def _ranked_doc_ids(chunks) -> list[str]:
    seen: list[str] = []
    for chunk in chunks:
        if chunk.metadata.doc_id not in seen:
            seen.append(chunk.metadata.doc_id)
    return seen


def run(k: int = 5) -> dict:
    """Against the *serving* retriever — the same one the app uses.

    No temp corpus and no fixtures: the point is to measure what users get, so
    anything that made this corpus different from production would defeat it.
    """
    from tools.knowledge_search.service import get_retriever

    dataset = json.loads(DATASET.read_text())
    retriever = get_retriever()

    per_query, hits_at_1, recall_sum, mrr_sum = [], 0, 0.0, 0.0
    for item in dataset["queries"]:
        expected = set(item["expected_doc_ids"])
        ranked = _ranked_doc_ids(retriever.search(item["query"], k=10))
        top_k = ranked[:k]

        found = expected & set(top_k)
        recall = len(found) / len(expected)
        rank = next((i + 1 for i, doc in enumerate(ranked) if doc in expected), None)

        recall_sum += recall
        mrr_sum += 1 / rank if rank else 0.0
        hits_at_1 += 1 if ranked[:1] and ranked[0] in expected else 0

        per_query.append(
            {
                "id": item["id"],
                "query": item["query"],
                "recall": round(recall, 3),
                "first_relevant_rank": rank,
                "missing": sorted(expected - found),
                "top_result": ranked[0] if ranked else None,
            }
        )

    n = len(dataset["queries"])
    return {
        "name": "retrieval_production",
        "queries": n,
        f"recall_at_{k}": round(recall_sum / n, 4),
        "mrr": round(mrr_sum / n, 4),
        "top1_accuracy": round(hits_at_1 / n, 4),
        "per_query": per_query,
    }


if __name__ == "__main__":
    result = run()
    print(f"Retrieval on the SERVING corpus — {result['queries']} real-cardholder questions\n")
    print(f"  recall@5      {result['recall_at_5']:.3f}")
    print(f"  MRR           {result['mrr']:.3f}")
    print(f"  top-1 correct {result['top1_accuracy']:.3f}\n")

    failures = [q for q in result["per_query"] if q["recall"] < 1.0]
    if not failures:
        print("  every question found its documents.")
    else:
        print(f"  {len(failures)} of {result['queries']} did not find everything expected:\n")
        for q in failures:
            got = q["top_result"] or "nothing"
            print(f"    {q['id']}  {q['query']}")
            print(f"          missing: {', '.join(q['missing'])}")
            print(f"          top hit: {got}   first relevant at rank: {q['first_relevant_rank']}")

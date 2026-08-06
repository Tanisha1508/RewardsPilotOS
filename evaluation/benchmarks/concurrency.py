"""Retrieval under concurrent load, measured locally.

This answers the question a load test against production would answer, without
the risks that make that a bad idea: the deployed backend is a 512 MB free
instance behind a per-user daily question limit, sharing one model quota with
the live demo. Retrieval is the stage worth stressing anyway — it holds the only
shared mutable-looking state in the request path, and it costs nothing to run.

**Threads, not processes, and that is the point.** FastAPI runs sync route
handlers in a threadpool, so concurrent requests in production reach one shared
`HybridRetriever` — a single `lru_cache(maxsize=1)` instance holding one Chroma
client and one BM25 index. If that object is not safe to share, this is where it
shows.

**Correctness is checked before speed.** Every concurrent run is compared
against a single-threaded baseline, query by query. Identical ranked document
ids mean the shared state held; a divergence means two threads interfered, and
that matters more than any latency figure on this page — a retriever that
returns a different answer under load is returning a wrong answer, and this
project treats wrong as worse than slow.

Throughput is reported but should be read with the GIL in mind: embedding and
BM25 scoring release it, Python-level fusion does not, so this measures what
this code does on this machine rather than a theoretical ceiling.

Run: python -m evaluation.benchmarks.concurrency
"""

import json
import platform
import resource
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

RESULTS = Path(__file__).resolve().parent.parent / "reports" / "concurrency.json"
DATASETS = Path(__file__).resolve().parent.parent / "datasets"

# 1 is the baseline, not a load level. 8 is past the useful point on a free
# instance with one worker, which is the environment this has to describe.
LEVELS = (1, 2, 4, 8)
ROUNDS = 3  # each level runs every query this many times


def _peak_rss_mb() -> float:
    """Peak resident set for this process. `ru_maxrss` is bytes on macOS and
    kilobytes on Linux — a difference of 1024x, and getting it backwards would
    make the number nonsense rather than merely wrong."""
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return round(peak / (1024 * 1024 if platform.system() == "Darwin" else 1024), 1)


def _ranked_doc_ids(chunks) -> list[str]:
    seen: list[str] = []
    for chunk in chunks:
        if chunk.metadata.doc_id not in seen:
            seen.append(chunk.metadata.doc_id)
    return seen


def run() -> dict:
    from tools.knowledge_search.service import get_retriever

    queries = [
        q["query"]
        for q in json.loads((DATASETS / "retrieval_production.json").read_text())["queries"]
    ]
    retriever = get_retriever()

    # Warm first: the corpus loads lazily, and paying for that inside the
    # 1-worker baseline would make every later level look faster than it is.
    retriever.search(queries[0], k=5)

    baseline = {q: _ranked_doc_ids(retriever.search(q, k=5)) for q in queries}

    def one(query: str) -> tuple[str, float, list[str]]:
        started = time.perf_counter()
        ranked = _ranked_doc_ids(retriever.search(query, k=5))
        return query, (time.perf_counter() - started) * 1000, ranked

    levels = []
    for workers in LEVELS:
        workload = [queries[i % len(queries)] for i in range(len(queries) * ROUNDS)]

        wall_start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=workers) as pool:
            outcomes = list(pool.map(one, workload))
        wall_s = time.perf_counter() - wall_start

        latencies = sorted(ms for _, ms, _ in outcomes)
        divergent = sorted({q for q, _, ranked in outcomes if ranked != baseline[q]})

        levels.append(
            {
                "workers": workers,
                "requests": len(workload),
                "wall_s": round(wall_s, 3),
                "throughput_qps": round(len(workload) / wall_s, 1),
                "p50_ms": round(statistics.median(latencies), 2),
                "p95_ms": round(latencies[int(len(latencies) * 0.95) - 1], 2),
                "max_ms": round(latencies[-1], 2),
                # The headline. Latency is a preference; this is a correctness
                # property, and a False here invalidates the rest of the row.
                "results_match_baseline": not divergent,
                "divergent_queries": divergent,
            }
        )

    return {
        "note": (
            "Threads against one shared retriever, mirroring how FastAPI serves "
            "sync handlers. Local machine; describes this code, not the deployed "
            "instance."
        ),
        "queries_in_workload": len(queries),
        "rounds_per_level": ROUNDS,
        "baseline_source": "single-threaded, same retriever, same queries",
        "levels": levels,
        "all_levels_consistent": all(lvl["results_match_baseline"] for lvl in levels),
        # Reported once for the whole run, not per level. `ru_maxrss` is a
        # monotonic high-water mark for the process, so a per-level figure would
        # be the same number four times wearing a disguise — it would read as
        # "memory is flat under load" when it actually says nothing per level.
        # What it does support: the run never exceeded this, against the 512 MB
        # the deployed instance has.
        "peak_rss_mb_whole_run": _peak_rss_mb(),
    }


if __name__ == "__main__":
    results = run()
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    RESULTS.write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2))
    print(f"\nWritten to {RESULTS}")
    if not results["all_levels_consistent"]:
        raise SystemExit("retrieval returned different results under concurrency")

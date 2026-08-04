# Evaluation — executive summary

Run 2026-08-04 on the repository at commit `076cee5`, reproduced with
`python -m evaluation.run_all`. Every figure below was produced by that command.
Where a metric could not be measured it is listed as not measured, with the
reason. Nothing here is estimated.

## What was measured

| Metric | Value | Dataset |
|---|---|---|
| Retrieval recall@5 (serving corpus) | **0.9872** | 26 natural-language queries, 14 verified documents |
| Retrieval MRR (serving corpus) | **0.9263** | same |
| Retrieval top-1 accuracy (serving corpus) | **0.8846** | same |
| Retrieval recall@5 (algorithm corpus) | **1.0000** | 24 queries incl. synthetic issuers |
| Retrieval precision@3 (algorithm corpus) | **0.2916** | same |
| Retrieval MRR (algorithm corpus) | **0.5861** | same |
| Rule engine exact match | **1.0000** (25/25) | hand-computed earn/cap scenarios |
| Graph engine exact match | **1.0000** (10/10) | hand-computed transfer paths |
| End-to-end workflow pass rate | **1.0000** (10/10) | 5 checks per query, incl. number traceability |
| Hybrid retrieval latency | **p50 10.32 ms · p95 13.25 ms** | 20 samples, local |
| Rule engine latency | **p50 0.20 ms · p95 1.75 ms** | 20 samples, local |
| Graph engine latency | **p50 0.12 ms · p95 0.27 ms** | 20 samples, local |
| Orchestration overhead (model excluded) | **97.04 ms per query** | 10 golden queries |
| Cold first retrieval call | **408.38 ms** | lazy corpus load, measured once |
| Automated test suite | **671 passing** | `pytest` |

## The three findings that matter

**Retrieval is measured twice on purpose, and the two numbers disagree by
design.** The 24-query suite scores recall@5 1.0000, and 17 of those queries ask
about invented banks. It measures whether the ranking algorithm works. The
26-query suite runs only the 14 documents a real user can reach, phrased as a
cardholder would ask, and scores 0.9872 — a slightly worse number that is the
only one describing the product. Precision@3 of 0.2916 on the first suite is not
a defect: relevance there is labelled at document level with typically one
relevant document, so precision@3 is capped near 0.33 by construction.

**Faithfulness is enforced deterministically rather than judged.** The
end-to-end suite extracts every number from the generated prose and fails the
answer unless each one appears in a tool result, and separately requires
`calculations` to be copied verbatim. That is a stronger guarantee than a
judge-scored faithfulness rating and it is why no hallucination-rate percentage
appears above: on this pipeline the measured unsupported-number rate is 0 out of
10 by construction, because an answer containing an untraceable number is
rejected before it can be returned.

**Latency is dominated by a component not measured here.** Every deterministic
stage runs in single-digit or sub-millisecond time; the two model calls are the
whole cost of a request, at roughly 29 seconds warm in production. Optimising
anything in the table above would change nothing a user notices.

## What was not measured, and why

| Not measured | Reason |
|---|---|
| Time to first token | The API does not stream. There is no first token; the response is a single JSON envelope. Reporting a TTFT would require inventing one. |
| Judge-based faithfulness / answer relevance (RAGAS) | Requires an LLM call per sample. The project runs on a shared free-tier quota that the deployed app depends on, and a full pass would exhaust a day of it. |
| End-to-end latency percentiles under real models | Same quota, plus a 5-questions-per-user-per-day limit in the deployed service. Two live measurements exist (~29 s warm, ~140 s cold) but two samples are not a distribution. |
| Load and concurrency against production | A 512 MB free instance with a measured 432 MB peak. Generating load would breach the rate limit, spend the shared quota, and could take the live service down. |
| Memory under load | Follows from the above. A single figure exists — 432 MB peak on the chat-plus-ingest path — measured previously, not by this run. |

## Known anomaly, unresolved

During one run the algorithm-corpus retrieval suite returned precision@3 0.2778
and recall@5 0.9583 instead of 0.2916 and 1.0000. Six subsequent runs — two in
isolation, one after the end-to-end suite, one after the full performance
benchmark, three through `run_all` — all reproduced the expected values. The
cause is not established. It is recorded here rather than dropped because a
benchmark that varies once has not been shown to be deterministic.

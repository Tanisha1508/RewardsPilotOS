# Evaluation

How to reproduce every measured number in this repository, and what each suite
is actually claiming.

## Reproduce everything

```bash
uv venv --python 3.11 && uv pip install -e ".[dev]"
python -m evaluation.run_all
```

Writes `reports/EVALUATION_REPORT.md` and `reports/raw_results.json`. Exits
non-zero if any deterministic suite regresses, so it can gate CI. Takes a few
seconds; no API key and no network are needed, because nothing in it calls a
model.

Run a single suite:

```bash
python -m evaluation.metrics.report          # quality suites only
python -m evaluation.benchmarks.performance  # latency and reliability only
pytest evaluation/regression                 # the same assertions, as tests
```

**Order matters inside `run_all`.** The performance benchmark runs first so that
its cold-start measurement is genuinely cold — the quality suites share the same
retriever, and running them first leaves the corpus warm and turns a 408 ms
measurement into a 16 ms one that means nothing.

## The suites

| Suite | Dataset | Size | Metric | What it claims |
|---|---|---|---|---|
| `metrics/retrieval_eval.py` | `datasets/retrieval.json` | 24 queries | precision@3, recall@5, MRR | The ranking algorithm works. 17 queries concern synthetic issuers, so it says nothing about real users. |
| `metrics/retrieval_production_eval.py` | `datasets/retrieval_production.json` | 26 queries | recall@5, MRR, top-1 | What a cardholder actually gets. Serving corpus only, no fixtures. **This is the one to watch.** |
| `metrics/rules_eval.py` | `datasets/rules.json` | 25 scenarios | exact match | Earn and cap arithmetic matches hand computation. |
| `metrics/graph_eval.py` | `datasets/graph.json` | 10 queries | exact match | Transfer-path search matches hand computation. |
| `metrics/e2e_eval.py` | `datasets/recommendations.json` | 10 queries | 5 checks per query | The whole workflow, including that every number in the prose traces to a tool result. |
| `benchmarks/performance.py` | reuses the above | 20 samples/stage | p50, p95, success rate | Latency of deterministic stages and golden-set completion. |
| `smoke/run.py` | see `smoke/README.md` | small | structural assertions | **Calls the real model.** Run by hand, not in `run_all`. |

## Labelling discipline

`expected_doc_ids` in the production retrieval set were assigned by reading each
document's own section headings **before** running retrieval. Labelling from
what the retriever returns would make the benchmark agree with itself and
measure nothing.

That set is split into two tiers. The first 20 queries name the card, which is
how people usually ask, and score 1.000 — naming a card makes the issuer
obvious. The `h`-tier deliberately does not name one, which is where retrieval
has to work from meaning alone. A benchmark that always passes teaches nothing.

## Why there is no RAGAS suite

RAGAS scores faithfulness with a model judging another model's output. This
pipeline does not need an opinion about whether a number is supported: the
end-to-end suite extracts every number from the prose and fails the answer
unless it appears in a tool result, and requires `calculations` to be copied
verbatim. A string match is a stronger guarantee than a judge's rating, it is
free, and it is deterministic.

A judge is still the right tool for the properties a string match cannot see —
answer relevance, tone, whether the reasoning follows. That is a worthwhile
addition and is not built, because every sample costs a call against a shared
free-tier quota the deployed app depends on. If it is built, it belongs behind
an explicit flag and its own budget, not in `run_all`.

## Why there is no load test

The deployed backend is a 512 MB free instance with a measured 432 MB peak on
the chat-plus-ingest path, behind a per-user daily question limit, sharing one
free-tier model quota with the live demo. Generating load against it would
breach the limit, spend the quota, and could take the service down.

A local concurrency harness against the retrieval stage would answer the same
question about our own code at no cost, and is the first thing to add here.

## Adding a suite

Put the data in `datasets/`, the runner in `metrics/`, and register it in
`metrics/report.py`. Assert its result in `regression/` so a change that moves a
number fails a test rather than quietly changing a report. Record what the suite
cannot see — every dataset in this directory carries a `description` saying what
it does not measure, and that is the field that keeps a benchmark honest.

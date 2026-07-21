"""Production ingestion entrypoint (BUILD_SPEC §6, D3).

Wires the two production-backed pieces the sprint left as fakes:

- the **persistent ChromaDB client** at `CHROMA_PERSIST_DIR` (local disk in dev,
  the Render persistent disk in prod), rather than a throwaway temp client
- the **Postgres-backed docs store**, so content hashes survive a restart and a
  re-run only re-embeds documents whose content actually changed

Run it:

    .venv/bin/python -m knowledge.pipeline.run

Idempotent by design: a second run with an unchanged corpus embeds nothing
(every doc's hash matches) and reports `docs_unchanged` for all of them. That is
the property the crawler depends on — "changed" only means changed.
"""

from knowledge.pipeline.docs_store import PostgresKnowledgeDocsStore
from knowledge.pipeline.ingest import IngestReport, ingest_sources
from knowledge.storage.collections import get_client


def run_production_ingest() -> IngestReport:
    client = get_client()  # persistent, at CHROMA_PERSIST_DIR
    store = PostgresKnowledgeDocsStore()
    return ingest_sources(client, docs_store=store)


def _print_report(report: IngestReport) -> None:
    print("Ingestion complete (production ChromaDB + Postgres hash tracking)")
    print(f"  documents ingested : {report.docs_ingested}")
    print(f"  documents unchanged: {report.docs_unchanged}")
    print(f"  documents empty    : {report.docs_skipped_empty}")
    print(f"  chunks ingested    : {report.chunks_ingested}")
    if report.excluded_facts:
        print(f"  [NEED] facts excluded from ingestion: {len(report.excluded_facts)}")
        for fact in report.excluded_facts:
            print(f"    - {fact.doc_id}: {fact.line}")


if __name__ == "__main__":
    _print_report(run_production_ingest())

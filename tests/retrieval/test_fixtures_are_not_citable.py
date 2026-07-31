"""Invented issuers must not be citable in a real answer (found 2026-07-31).

Ten fixture documents for two issuers that do not exist — `demo_bank` and
`sample_bank` — sit in `knowledge/sources/` beside the real ones, and were being
ingested into the same collections. Six came back from ordinary queries:
"lounge access" retrieved `https://example.test/demo-bank/voyager/benefits`.

Retrieved chunks are the citation pool. So an answer about a real card could
carry a source from a bank that does not exist — a fabricated citation arriving
through the corpus rather than through the model, which is why none of the
model-side guards would have caught it.

The fixtures stay on disk; the retrieval suite needs a corpus of known content.
They just stop reaching the serving corpus.
"""

import pytest

from knowledge.parsers.frontmatter import parse_source_file
from knowledge.pipeline.ingest import SOURCES_DIR, ingest_sources, is_fixture
from knowledge.storage.collections import COLLECTIONS, get_client, get_collection


def _fixture_docs():
    return [p for p in sorted(SOURCES_DIR.glob("*.md")) if is_fixture(parse_source_file(p))]


def test_the_corpus_does_contain_fixture_documents():
    """Fixture check: if this fails the others prove nothing."""
    assert _fixture_docs(), "expected fixture-issuer documents in knowledge/sources/"


def test_a_reserved_test_domain_is_recognised_as_a_fixture():
    """`.test` is reserved by RFC 2606 and can never be a real issuer, which is
    what makes it safe to key on."""

    class Doc:
        source_url = "https://example.test/demo-bank/voyager/benefits"

    class Real:
        source_url = "https://www.axisbank.com/retail/cards/credit-card/axis-bank-atlas"

    assert is_fixture(Doc())
    assert not is_fixture(Real())


def test_ingest_excludes_fixtures_by_default(tmp_path):
    client = get_client(tmp_path / "chroma")
    report = ingest_sources(client)

    assert report.docs_skipped_fixture == len(_fixture_docs())
    assert report.docs_ingested > 0, "the real corpus must still ingest"


def test_no_fixture_source_is_retrievable_from_the_serving_corpus(tmp_path):
    """The property that actually matters, checked the way a user would hit it:
    ordinary questions, and nothing invented comes back."""
    client = get_client(tmp_path / "chroma")
    ingest_sources(client)

    urls = []
    for name in COLLECTIONS:
        data = get_collection(client, name).get(include=["metadatas"])
        urls += [m.get("source_url", "") for m in (data.get("metadatas") or [])]

    offenders = [u for u in urls if ".test" in u or "demo_bank" in u or "sample_bank" in u]
    assert not offenders, f"fixture sources reached the serving corpus: {offenders[:3]}"


@pytest.mark.parametrize("include", [True, False])
def test_the_flag_is_the_only_thing_that_changes(tmp_path, include):
    """Opting in must bring the fixtures back — otherwise the retrieval suite
    would be silently testing a corpus it did not ask for."""
    client = get_client(tmp_path / f"chroma-{include}")
    report = ingest_sources(client, include_fixtures=include)

    assert report.docs_skipped_fixture == (0 if include else len(_fixture_docs()))

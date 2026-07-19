"""Unit tests: chunker, [NEED] stripping, frontmatter, RRF, freshness decay."""

from datetime import date

import pytest

from knowledge.chunking.chunker import MAX_WORDS, chunk_markdown
from knowledge.freshness.decay import freshness_factor
from knowledge.parsers.frontmatter import SourceDocError, parse_source_file
from knowledge.ranking.fusion import reciprocal_rank_fusion
from knowledge.validators.needs import strip_unverified_facts


def test_chunk_by_heading():
    body = "intro line\n\n# One\ncontent one\n\n## Two\ncontent two"
    chunks = chunk_markdown(body)
    assert [chunk.heading for chunk in chunks] == ["introduction", "One", "Two"]


def test_long_section_split():
    body = "# Big\n" + " ".join(["word"] * (MAX_WORDS * 2 + 10))
    chunks = chunk_markdown(body)
    assert len(chunks) == 3
    assert all(len(chunk.content.split()) <= MAX_WORDS for chunk in chunks)


def test_empty_sections_dropped():
    assert chunk_markdown("# Only heading\n\n# Another\n") == []


def test_strip_unverified_facts():
    text = "verified line\nrate: [NEED: verify from issuer docs]\nanother verified"
    kept, excluded = strip_unverified_facts("doc1", text)
    assert "[NEED" not in kept
    assert len(excluded) == 1
    assert excluded[0].doc_id == "doc1"


def test_frontmatter_missing_keys(tmp_path):
    bad = tmp_path / "bad.md"
    bad.write_text("---\ndoc_id: x\n---\nbody")
    with pytest.raises(SourceDocError, match="missing frontmatter keys"):
        parse_source_file(bad)


def test_frontmatter_bad_doc_type(tmp_path):
    bad = tmp_path / "bad.md"
    bad.write_text(
        "---\ndoc_id: x\nissuer: i\nprogram: p\ndoc_type: blog\n"
        "source_url: https://example.test\nlast_changed: 2026-01-01\n---\nbody"
    )
    with pytest.raises(SourceDocError, match="doc_type"):
        parse_source_file(bad)


def test_frontmatter_no_frontmatter(tmp_path):
    bad = tmp_path / "bad.md"
    bad.write_text("just a body")
    with pytest.raises(SourceDocError, match="missing YAML frontmatter"):
        parse_source_file(bad)


def test_rrf_rewards_agreement():
    scores = reciprocal_rank_fusion([["a", "b", "c"], ["b", "a"]])
    assert scores["a"] > scores["c"]
    assert scores["b"] > scores["c"]
    assert scores["b"] == pytest.approx(1 / 62 + 1 / 61)


def test_freshness_decay_half_life_and_floor():
    as_of = date(2026, 7, 19)
    assert freshness_factor("2026-07-19", as_of) == 1.0
    assert freshness_factor("2026-01-20", as_of) == pytest.approx(0.5, abs=0.01)
    assert freshness_factor("2020-01-01", as_of) == 0.5  # floor
    assert freshness_factor("not-a-date", as_of) == 0.5

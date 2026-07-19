"""Unverified-fact exclusion (BUILD_SPEC §6): facts marked [NEED: verify] are
excluded from ingestion until verified, and logged so the [NEED] register can
surface them. Never ingest an unverified fact."""

from dataclasses import dataclass

NEED_MARKER = "[NEED"


@dataclass
class ExcludedFact:
    doc_id: str
    line: str


def strip_unverified_facts(doc_id: str, text: str) -> tuple[str, list[ExcludedFact]]:
    """Remove lines carrying a [NEED...] marker from ingestible content."""
    kept: list[str] = []
    excluded: list[ExcludedFact] = []
    for line in text.splitlines():
        if NEED_MARKER in line:
            excluded.append(ExcludedFact(doc_id=doc_id, line=line.strip()))
        else:
            kept.append(line)
    return "\n".join(kept).strip(), excluded

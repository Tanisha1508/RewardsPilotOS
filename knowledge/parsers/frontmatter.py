"""Parse seed markdown documents: YAML frontmatter + body.

Every seed document must declare doc_id, issuer, program, doc_type,
source_url, last_changed — the metadata that flows into ChromaDB and then
verbatim into citations.
"""

from dataclasses import dataclass
from pathlib import Path

import yaml

REQUIRED_KEYS = ("doc_id", "issuer", "program", "doc_type", "source_url", "last_changed")

VALID_DOC_TYPES = (
    "reward_rules",
    "transfer_rules",
    "promotions",
    "benefit_guides",
    "issuer_policies",
)


class SourceDocError(Exception):
    """A seed document is malformed or missing required metadata."""


@dataclass
class SourceDoc:
    doc_id: str
    issuer: str
    program: str
    doc_type: str
    source_url: str
    last_changed: str
    body: str
    path: str


def parse_source_file(path: Path) -> SourceDoc:
    text = path.read_text()
    if not text.startswith("---"):
        raise SourceDocError(f"{path}: missing YAML frontmatter")
    try:
        _, frontmatter, body = text.split("---", 2)
    except ValueError as exc:
        raise SourceDocError(f"{path}: unterminated frontmatter") from exc
    meta = yaml.safe_load(frontmatter)
    if not isinstance(meta, dict):
        raise SourceDocError(f"{path}: frontmatter must be a mapping")
    missing = [key for key in REQUIRED_KEYS if not meta.get(key)]
    if missing:
        raise SourceDocError(f"{path}: missing frontmatter keys {missing}")
    if meta["doc_type"] not in VALID_DOC_TYPES:
        raise SourceDocError(f"{path}: doc_type '{meta['doc_type']}' not in {VALID_DOC_TYPES}")
    return SourceDoc(
        doc_id=str(meta["doc_id"]),
        issuer=str(meta["issuer"]),
        program=str(meta["program"]),
        doc_type=str(meta["doc_type"]),
        source_url=str(meta["source_url"]),
        last_changed=str(meta["last_changed"]),
        body=body.strip(),
        path=str(path),
    )

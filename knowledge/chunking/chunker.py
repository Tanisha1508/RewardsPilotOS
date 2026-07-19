"""Chunk markdown by heading, max ~500 tokens per chunk (BUILD_SPEC §6).

Token count is approximated by whitespace word count (a word is >= 1 token;
staying under 500 words keeps chunks under the ~500-token budget for
all-MiniLM-L6-v2's 512-token window)."""

import re
from dataclasses import dataclass

MAX_WORDS = 500

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


@dataclass
class Chunk:
    heading: str
    content: str


def _split_long(heading: str, words: list[str]) -> list[Chunk]:
    parts = []
    for start in range(0, len(words), MAX_WORDS):
        parts.append(Chunk(heading=heading, content=" ".join(words[start : start + MAX_WORDS])))
    return parts


def chunk_markdown(body: str) -> list[Chunk]:
    """Split on headings; each chunk carries its heading as context. Content
    before the first heading becomes an 'introduction' chunk."""
    sections: list[tuple[str, list[str]]] = [("introduction", [])]
    for line in body.splitlines():
        match = _HEADING_RE.match(line)
        if match:
            sections.append((match.group(2).strip(), []))
        else:
            sections[-1][1].append(line)
    chunks: list[Chunk] = []
    for heading, lines in sections:
        text = "\n".join(lines).strip()
        if not text:
            continue
        words = text.split()
        if len(words) > MAX_WORDS:
            chunks.extend(_split_long(heading, words))
        else:
            chunks.append(Chunk(heading=heading, content=text))
    return chunks

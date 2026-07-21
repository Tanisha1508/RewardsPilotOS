"""Crawler: detect when an official source page changes (BUILD_SPEC §6).

What it does per source in `sources.yaml`:

1. Respect robots.txt. A disallowed source is skipped and logged, never worked
   around (BUILD_SPEC §6). `crawlable: false` in the YAML skips it before a
   request is even made.
2. Fetch, extract the main text (scripts/styles/nav stripped), hash it.
3. Diff that hash against the last-crawl hash for this source. On the first
   crawl there is nothing to compare, so it is recorded as `new`, not `changed`.
4. On a real change, write a change record and advance the stored hash and
   `last_changed`.

What it deliberately does NOT do: re-ingest the fetched HTML into the verified
corpus or edit rule files. The pages are partial blind spots — JS-rendered
tables, figures in linked PDFs — and the corpus is hand-verified. The crawler
detects change so a human re-verifies; it never lets scraped content become a
verified fact (BUILD_SPEC §14a, hard rule #1, ADR-016).

Change-tracking state lives in `knowledge_docs` under a `source::<key>` doc_id
namespace, kept distinct from the ingested-corpus rows (`hdfc_infinia_reward_
rules`) so the crawler's live-page hash never collides with ingestion's
seed-body hash in the shared `content_hash` column.
"""

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import yaml

from knowledge.crawler.state import CrawlStateStore, InMemoryCrawlStateStore

SOURCES_FILE = Path(__file__).resolve().parent / "sources.yaml"


@dataclass
class Source:
    key: str
    doc_id: str
    issuer: str
    program: str
    url: str
    crawlable: bool
    blind_spot: str | None = None


@dataclass
class ChangeRecord:
    key: str
    doc_id: str
    url: str
    status: str  # new | changed | unchanged | skipped_robots | skipped_config | error
    detail: str | None = None


@dataclass
class CrawlReport:
    records: list[ChangeRecord] = field(default_factory=list)

    def by_status(self, status: str) -> list[ChangeRecord]:
        return [r for r in self.records if r.status == status]

    @property
    def changed(self) -> list[ChangeRecord]:
        return [r for r in self.records if r.status in ("new", "changed")]


def load_sources(path: Path | None = None) -> tuple[str, list[Source]]:
    data = yaml.safe_load((path or SOURCES_FILE).read_text())
    sources = [Source(**{k: s.get(k) for k in Source.__annotations__}) for s in data["sources"]]
    return data["user_agent"], sources


def extract_main_text(html: str) -> str:
    """Strip non-content nodes and collapse whitespace. Deliberately simple:
    the goal is a stable hash of the visible content, not perfect extraction —
    a change anywhere in the readable text should register."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "template"]):
        tag.decompose()
    return " ".join(soup.get_text(" ").split())


def _robots_allows(url: str, user_agent: str) -> bool:
    base = f"{urlsplit(url).scheme}://{urlsplit(url).netloc}"
    parser = RobotFileParser()
    parser.set_url(f"{base}/robots.txt")
    try:
        parser.read()
    except Exception:
        # An unreadable robots.txt is treated as "do not crawl" — failing closed
        # is the safe direction when we cannot confirm permission.
        return False
    return parser.can_fetch(user_agent, url)


def _default_fetcher(url: str, user_agent: str) -> str:
    import httpx

    resp = httpx.get(url, headers={"User-Agent": user_agent}, timeout=30, follow_redirects=True)
    resp.raise_for_status()
    return resp.text


def crawl(
    store: CrawlStateStore | None = None,
    sources_path: Path | None = None,
    fetcher=_default_fetcher,
    today: str | None = None,
) -> CrawlReport:
    """`fetcher` and `today` are injectable so the crawler can be tested without
    the network or a real clock."""
    from datetime import datetime, timezone

    store = store or InMemoryCrawlStateStore()
    user_agent, sources = load_sources(sources_path)
    crawl_date = today or datetime.now(timezone.utc).date().isoformat()
    report = CrawlReport()

    for source in sources:
        if not source.crawlable:
            report.records.append(
                ChangeRecord(
                    source.key,
                    source.doc_id,
                    source.url,
                    "skipped_config",
                    source.blind_spot or "marked not crawlable",
                )
            )
            continue

        if not _robots_allows(source.url, user_agent):
            report.records.append(
                ChangeRecord(
                    source.key,
                    source.doc_id,
                    source.url,
                    "skipped_robots",
                    "robots.txt disallows crawling",
                )
            )
            continue

        try:
            text = extract_main_text(fetcher(source.url, user_agent))
        except Exception as exc:  # network / parse failure — logged, not fatal
            report.records.append(
                ChangeRecord(
                    source.key,
                    source.doc_id,
                    source.url,
                    "error",
                    f"{type(exc).__name__}: {exc}",
                )
            )
            continue

        new_hash = hashlib.sha256(text.encode()).hexdigest()
        previous = store.get_hash(source.key)
        if previous is None:
            store.record(source.key, source.url, new_hash, crawl_date, changed=True)
            report.records.append(
                ChangeRecord(
                    source.key, source.doc_id, source.url, "new", "first crawl — baseline recorded"
                )
            )
        elif previous != new_hash:
            store.record(source.key, source.url, new_hash, crawl_date, changed=True)
            report.records.append(
                ChangeRecord(
                    source.key,
                    source.doc_id,
                    source.url,
                    "changed",
                    f"content hash changed since last crawl — re-verify {source.doc_id}",
                )
            )
        else:
            store.record(source.key, source.url, new_hash, crawl_date, changed=False)
            report.records.append(ChangeRecord(source.key, source.doc_id, source.url, "unchanged"))

    return report


def run_crawl() -> CrawlReport:
    """Production entrypoint (the cron target): real network, real robots,
    Postgres-backed state so change detection persists across daily runs."""
    from knowledge.crawler.state import PostgresCrawlStateStore

    return crawl(store=PostgresCrawlStateStore())


if __name__ == "__main__":
    import sys

    report = run_crawl()
    for record in report.records:
        print(f"{record.status:15} {record.key:18} {record.detail or ''}")
    changed = report.changed
    if changed:
        print(f"\n{len(changed)} source(s) changed — re-verification needed:")
        for record in changed:
            print(f"  - {record.doc_id} ({record.url})")
    # A changed source is expected operation, not a failure. Only a genuine
    # fetch/parse error exits non-zero, so the cron surfaces real breakage.
    sys.exit(1 if report.by_status("error") else 0)

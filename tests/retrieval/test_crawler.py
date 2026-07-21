"""Crawler change detection, offline (BUILD_SPEC §6, D3).

No network: the fetcher is injected. What matters is the state machine —
first-crawl is `new`, an identical refetch is `unchanged`, a changed page is
`changed` — and that a non-crawlable or robots-disallowed source is skipped and
recorded, never silently dropped.
"""

from knowledge.crawler.crawl import crawl, extract_main_text, load_sources
from knowledge.crawler.state import InMemoryCrawlStateStore

PAGE = "<html><body><h1>Infinia</h1><p>5 points per 150</p><script>x()</script></body></html>"


def fetch_fixed(_url, _ua):
    return PAGE


def test_sources_yaml_loads_and_declares_crawlability():
    _ua, sources = load_sources()
    keys = {s.key for s in sources}
    assert {"hdfc_infinia", "axis_atlas", "amex_plat_travel"} <= keys
    # All three P1 sources are crawlable. HDFC was corrected 2026-07-22: D3 had
    # pointed at a Cloudflare mirror (www.hdfcbank.com) whose robots.txt 403s;
    # the canonical www.hdfc.bank.in allows crawling with content in static HTML.
    hdfc = next(s for s in sources if s.key == "hdfc_infinia")
    assert hdfc.crawlable is True
    assert hdfc.url.startswith("https://www.hdfc.bank.in/")


def test_extract_main_text_drops_scripts():
    text = extract_main_text(PAGE)
    assert "Infinia" in text and "5 points per 150" in text
    assert "x()" not in text  # script stripped


def test_non_crawlable_source_is_skipped_and_recorded(tmp_path):
    """A `crawlable: false` source is skipped before any fetch and recorded, not
    dropped. No real P1 source is non-crawlable anymore (HDFC was corrected
    2026-07-22), so this uses a synthetic sources file to exercise the behavior
    the mechanism still needs — a future P2 source may genuinely be blocked."""
    sources = tmp_path / "sources.yaml"
    sources.write_text(
        'user_agent: "test-agent"\n'
        "sources:\n"
        "  - key: blocked_card\n"
        "    doc_id: blocked_card_reward_rules\n"
        "    issuer: someissuer\n"
        "    program: some_points\n"
        "    url: https://example.test/blocked\n"
        "    crawlable: false\n"
        '    blind_spot: "T&C only in a login-gated PDF"\n'
    )
    report = crawl(
        store=InMemoryCrawlStateStore(),
        sources_path=sources,
        fetcher=fetch_fixed,
        today="2026-07-21",
    )
    rec = next(r for r in report.records if r.key == "blocked_card")
    assert rec.status == "skipped_config"
    # Skipped, but present in the report — a blind spot must be visible, not silent.
    assert rec.detail


def test_first_crawl_is_new_then_unchanged_then_changed(tmp_path):
    store = InMemoryCrawlStateStore()

    first = crawl(store=store, fetcher=fetch_fixed, today="2026-07-21")
    assert {r.status for r in first.records if r.key == "axis_atlas"} == {"new"}

    again = crawl(store=store, fetcher=fetch_fixed, today="2026-07-22")
    assert next(r for r in again.records if r.key == "axis_atlas").status == "unchanged"

    def fetch_changed(_url, _ua):
        return PAGE.replace("5 points", "6 points")

    changed = crawl(store=store, fetcher=fetch_changed, today="2026-07-23")
    rec = next(r for r in changed.records if r.key == "axis_atlas")
    assert rec.status == "changed"
    assert "re-verify" in rec.detail


def test_a_fetch_error_is_logged_not_fatal():
    def boom(_url, _ua):
        raise ConnectionError("network down")

    report = crawl(store=InMemoryCrawlStateStore(), fetcher=boom, today="2026-07-21")
    errors = report.by_status("error")
    # All three P1 sources are crawlable (HDFC corrected 2026-07-22), so all
    # three reach the fetcher and error — none is fatal, each is logged.
    assert len(errors) == 3
    assert all("ConnectionError" in r.detail for r in errors)


def test_robots_disallowed_source_is_skipped(monkeypatch, tmp_path):
    """A source that is crawlable-by-config but robots-disallowed must still be
    skipped and logged (BUILD_SPEC §6: never work around robots)."""
    import knowledge.crawler.crawl as crawl_mod

    monkeypatch.setattr(crawl_mod, "_robots_allows", lambda url, ua: False)
    report = crawl(store=InMemoryCrawlStateStore(), fetcher=fetch_fixed, today="2026-07-21")
    # axis + amex are config-crawlable but now robots-blocked → skipped_robots
    assert {r.status for r in report.records if r.key in ("axis_atlas", "amex_plat_travel")} == {
        "skipped_robots"
    }

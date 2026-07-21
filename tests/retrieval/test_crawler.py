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
    hdfc = next(s for s in sources if s.key == "hdfc_infinia")
    # HDFC is robots-disallowed and flagged not crawlable — a documented blind spot.
    assert hdfc.crawlable is False
    assert hdfc.blind_spot


def test_extract_main_text_drops_scripts():
    text = extract_main_text(PAGE)
    assert "Infinia" in text and "5 points per 150" in text
    assert "x()" not in text  # script stripped


def test_non_crawlable_source_is_skipped_and_recorded():
    report = crawl(store=InMemoryCrawlStateStore(), fetcher=fetch_fixed, today="2026-07-21")
    hdfc = next(r for r in report.records if r.key == "hdfc_infinia")
    assert hdfc.status == "skipped_config"
    # Skipped, but present in the report — a blind spot must be visible, not silent.
    assert hdfc.detail


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
    # Both crawlable sources error; the non-crawlable one is skipped first.
    assert len(errors) == 2
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

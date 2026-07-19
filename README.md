# RewardsPilotOS

An AI copilot for credit card rewards optimization (Indian issuers first). It answers questions like *"Which card should I use for a ₹70,000 laptop?"* with cited, confidence-scored recommendations whose numbers come exclusively from deterministic engines — never from the LLM.

**Core principle: no fabricated data, ever. Unknown is always preferred over incorrect.** Every numeric fact (earn rates, caps, transfer ratios, point values) carries `{value, status: verified|unverified, source, confidence}`. Unverified values are refused by the engines and surfaced as *unknown* in recommendations, with a `[NEED: verify from issuer docs]` flag tracked in [docs/VERIFICATION_QUEUE.md](docs/VERIFICATION_QUEUE.md).

## Architecture (intelligence core)

- **Rule Engine** (`rules/`) — versioned JSON rule files per card; deterministic earn/cap math; refuses unverified values.
- **Knowledge Platform** (`knowledge/`) — hybrid retrieval: ChromaDB semantic + BM25 keyword + metadata filter + reciprocal rank fusion + freshness re-rank.
- **Graph Engine** (`graph/`) — NetworkX transfer graph (cards → currencies → airline/hotel programs); verified edges only.
- **Multi-agent orchestration** (`agents/`, `tools/`) — LangGraph: Planner (Gemini) → deterministic tool nodes → Recommender (Gemini). The Planner emits typed `ToolInvocation`s validated against `contracts/tools/`; the Recommender copies numbers verbatim from tool results.
- **MCP** (`mcp/`) — external integration layer (browser/playwright stubs; email/calendar/flight/hotel interfaces).
- **Evaluation** (`evaluation/`) — golden sets for retrieval, rules, graph, and end-to-end recommendations; `report.py` writes `evaluation/reports/REPORT.md`.

See `BUILD_SPEC.md` (engineering source of truth) and `MASTER_SPEC.md` (product source of truth).

## Quickstart

```bash
uv venv --python 3.11
uv pip install -e ".[dev]"

# tests
.venv/bin/python -m pytest

# evaluation suite → evaluation/reports/REPORT.md
.venv/bin/python -m evaluation.metrics.report

# demo query end to end (uses Gemini if GEMINI_API_KEY is set, deterministic fake otherwise)
.venv/bin/python -m agents.workflows.demo
```

## Status

Sprint milestone (intelligence core) — built against in-memory fakes and fixture data. Database migrations, CRUD APIs, frontend, crawlers, and deployment land in D2–D5 per BUILD_SPEC §14. All metrics reported in `evaluation/reports/REPORT.md` are measured eval results with the run date; product metrics from MASTER_SPEC are targets only.

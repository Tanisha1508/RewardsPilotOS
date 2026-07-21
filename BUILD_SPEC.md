# BUILD_SPEC.md — RewardsPilotOS Implementation Guide

**Status:** Approved for build. This is the construction manual for coding agents.
**Relationship to MASTER_SPEC.md:** MASTER_SPEC.md is the product source of truth (vision, PRD, architecture rationale). This document is the engineering source of truth (structure, conventions, contracts, build order). Where they conflict, this document wins for implementation details; MASTER_SPEC.md wins for product intent.
**Deadline:** Deployed end to end by July 24, 2026.

---

## 1. Stack (locked)

| Layer | Technology | Hosting |
|---|---|---|
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind, shadcn/ui | Vercel free tier |
| Backend API | FastAPI (Python 3.11), Pydantic v2 | Render free tier |
| Orchestration | LangGraph | In backend process |
| LLM | Gemini (free tier, `gemini-3.5-flash` default; single env var to swap — see ADR-015) | Google AI Studio API |
| Relational DB | PostgreSQL | Supabase free tier |
| Vector DB | ChromaDB (persistent client, local disk) | Render persistent disk |
| Cache / queues | Redis | Upstash free tier |
| Graph Engine | NetworkX (in-process, loaded from Postgres) | In backend |
| Rule Engine | Custom Python, versioned JSON rules | In backend |
| Crawlers / refresh | Python + httpx + BeautifulSoup | GitHub Actions cron |
| Auth | Supabase Auth (JWT), verified in FastAPI middleware | Supabase |
| MCP | Client hooks for browser automation and email (stub interfaces first, wire last) | In backend |

Constraint: free tier or open source only. No paid services.

---

## 2. Repository structure

Governing principle: every top-level directory corresponds to a major architectural subsystem described in MASTER_SPEC.md. If a new directory does not map cleanly to a documented subsystem, it does not belong at the top level. No catch-all directories (utils/, helpers/, common/, shared/): code lives next to the domain that owns it.

## Build Constraints

The coding agent MUST NOT:

- invent architecture
- rename directories
- introduce new frameworks
- replace specified libraries
- change API contracts
- modify database schema
- add new agents
- remove evaluation
- remove citations
- simplify deterministic components

If implementation requires deviation: STOP. Document the issue. Continue only after the specification is updated.

MASTER_SPEC.md and BUILD_SPEC.md are authoritative.

```
RewardsPilotOS/
├── README.md
├── LICENSE
├── .gitignore
├── pyproject.toml             # single dependency manifest (no requirements.txt)
├── .env.example
├── MASTER_SPEC.md             # product source of truth
├── BUILD_SPEC.md              # engineering source of truth
│
├── docs/
│   ├── architecture/
│   ├── product/
│   ├── adr/                   # ADR-001..008
│   ├── diagrams/
│   ├── assets/
│   ├── VERIFICATION_QUEUE.md
│   └── KNOWN_LIMITATIONS.md
│
├── contracts/                 # single home for cross-boundary interfaces
│   ├── api/                   # shared API payload contracts
│   ├── mcp/                   # MCP server/client contracts
│   ├── tools/                 # tool input/output schemas
│   └── events/                # event payloads (knowledge changes, notifications,
│                             #   verification records — see contracts/events/
│                             #   verification_record.schema.json, Fast Follow section)
│
├── frontend/                  # Next.js 14 App Router
│   ├── app/                   # (auth)/login, dashboard, cards, chat,
│   │                          # opportunities, recommendations/[id]
│   ├── components/
│   ├── lib/                   # api.ts typed client
│   ├── hooks/
│   ├── services/
│   └── types/
│
├── backend/                   # FastAPI application layer
│   ├── api/                   # v1 routers: auth, portfolio, recommendations,
│   │                          # chat, knowledge, opportunities, health
│   ├── application/           # orchestration between api, agents, tools, db
│   │                          # (NOT business logic; that lives in rules/,
│   │                          # graph/, knowledge/)
│   ├── auth/                  # Supabase JWT verification
│   ├── config/                # Pydantic Settings
│   ├── middleware/
│   ├── models/                # SQLAlchemy models
│   ├── schemas/               # HTTP request/response DTOs only
│   └── main.py
│
├── agents/                    # LLM reasoning layer
│   ├── planner/
│   ├── recommendation/
│   ├── knowledge/             # knowledge-focused agent behaviors
│   ├── graph/                 # graph-focused agent behaviors
│   ├── memory/                # memory-focused agent behaviors
│   ├── prompts/               # one .md per prompt template
│   ├── state/                 # shared LangGraph state schema (schema.py)
│   ├── workflows/             # LangGraph workflow definitions
│   └── registry.py
│
├── tools/                     # deterministic internal capabilities
│   ├── portfolio/
│   ├── rule_engine/
│   ├── graph_engine/
│   ├── reward_calculator/
│   ├── knowledge_search/
│   ├── opportunity_engine/
│   ├── memory/
│   └── registry.py            # Tool Registry (schemas from contracts/tools)
│
├── mcp/                       # external integration layer
│   ├── clients/
│   │   ├── base.py            # common base contract
│   │   ├── browser.py         # stub (typed pending errors)
│   │   ├── playwright.py      # stub (typed pending errors)
│   │   ├── email.py           # interface-only
│   │   ├── calendar.py        # interface-only
│   │   ├── flights.py         # interface-only
│   │   └── hotels.py          # interface-only
│   ├── adapters/
│   └── registry.py
│
├── knowledge/                 # Knowledge Platform (per MASTER_SPEC ch. 23)
│   ├── pipeline/              # ingestion orchestration
│   ├── crawler/               # crawl.py, monitor.py, sources.yaml
│   ├── parsers/
│   ├── chunking/
│   ├── embeddings/
│   ├── retrieval/             # hybrid retrieval (semantic+BM25+RRF+freshness)
│   ├── ranking/
│   ├── validators/
│   ├── freshness/
│   ├── sources/               # seed markdown corpus, source-attributed
│   └── storage/               # ChromaDB collection definitions
│
├── graph/                     # Graph Engine
│   ├── builder/               # loads nodes/edges from Postgres
│   ├── search/                # best_transfer_paths
│   ├── ranking/
│   ├── optimization/          # redemption_options
│   ├── constraints/           # min transfer, verified-only filtering
│   └── models/
│
├── rules/                     # Rule Engine
│   ├── engine/
│   ├── parser/
│   ├── evaluator/
│   ├── versioning/
│   ├── validators/            # extended field schema validation
│   └── seed/                  # versioned rule JSON per card
│       ├── hdfc_infinia/
│       ├── axis_atlas/
│       └── amex_plat_travel/
│
├── memory/                    # layered memory
│   ├── episodic/
│   ├── semantic/
│   ├── procedural/
│   ├── retrieval/
│   ├── storage/
│   └── summarization/
│
├── database/
│   ├── postgres/
│   ├── chroma/
│   ├── redis/
│   ├── migrations/            # Alembic, single head
│   └── seed/                  # graph nodes/edges seed, fixtures
│
├── evaluation/
│   ├── datasets/              # golden sets: retrieval, rules, graph, e2e
│   ├── benchmarks/
│   ├── metrics/
│   ├── regression/
│   ├── scenarios/
│   └── reports/               # REPORT.md output
│
├── infra/
│   ├── deployment/            # render.yaml, vercel.json
│   ├── monitoring/
│   ├── logging/
│   └── scripts/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   ├── agent/
│   ├── graph/
│   ├── rules/
│   └── retrieval/
│
├── data/                      # gitignored except .gitkeep
│   ├── raw/
│   ├── processed/
│   ├── embeddings/            # ChromaDB persist dir in dev
│   └── cache/
│
├── notebooks/
│   ├── experiments/
│   └── analysis/
│
└── .github/workflows/         # ci.yml, crawl.yml, eval.yml
```

No Docker, no docker-compose: deployment is Vercel, Render, Supabase, Upstash. Revisit only if the project leaves free tiers.

## 3. Conventions

**Python:** ruff + black defaults. Type hints everywhere. Services raise domain exceptions; API layer maps to HTTP errors. No business logic in routers. No LLM calls outside `agents/`.
**TypeScript:** strict mode. All API responses typed in `lib/types.ts`, generated to match Pydantic schemas by hand (no codegen dependency).
**API:** REST, `/api/v1/...`, JWT bearer auth on everything except `/health` and auth routes. Consistent envelope:

```json
{ "data": {...}, "error": null, "meta": { "request_id": "...", "generated_at": "..." } }
```

**Structure discipline:** every top-level directory maps to a MASTER_SPEC subsystem; no utils/helpers/common catch-alls; domain-owned code stays in its domain; cross-boundary interfaces live in `contracts/` (backend/schemas holds HTTP DTOs only).
**Naming:** snake_case (Python, DB, JSON), camelCase (TS), kebab-case (routes, files in frontend).
**Commits:** conventional commits (`feat:`, `fix:`, `docs:`, `test:`).
**Engineering principle:** Unknown is always preferred over incorrect. Whenever official information cannot be verified: value null, status unverified, confidence 0. The system never fabricates reward rules, transfer ratios, benefit values, or issuer policies. Every recommendation must be traceable to an official or verified source.
**Every recommendation response must include:** reasoning summary, citations (source + freshness timestamp), confidence (high/medium/low with stated basis), and the deterministic numbers used (from Rule Engine or Graph Engine, never LLM-generated arithmetic).

---

## 4. Database schema (Postgres via Supabase)

Tables (SQLAlchemy models mirror exactly):

```
users               user_id PK, email, name, timezone, created_at, updated_at
                    (managed by Supabase Auth; local table mirrors auth.users id)
portfolios          portfolio_id PK, user_id FK, portfolio_name, created_at
cards               card_id PK, portfolio_id FK, issuer, card_name, network,
                    joining_date, annual_fee, renewal_date, status
reward_balances     balance_id PK, card_id FK, reward_currency, current_balance,
                    expiry_date, last_updated
loyalty_accounts    loyalty_id PK, portfolio_id FK, program_name, program_type
                    (airline|hotel), balance, status_tier, last_updated
goals               goal_id PK, user_id FK, goal_type (trip|redemption|savings),
                    description, target_date, status
preferences         pref_id PK, user_id FK, key, value, updated_at
                    (semantic memory: preferred airlines, hotels, class, home airport,
                    redemption strategy)
recommendations     rec_id PK, user_id FK, query, recommendation_json, confidence,
                    citations_json, status (generated|viewed|accepted|rejected|saved),
                    created_at
interaction_events  event_id PK, user_id FK, event_type, payload_json, created_at
                    (episodic memory + analytics instrumentation)
notifications       notif_id PK, user_id FK, type, title, body, source_change_id,
                    read, created_at
knowledge_docs      doc_id PK, source_url, issuer, program, doc_type, content_hash,
                    last_crawled, last_changed, status
                    (metadata; content lives in ChromaDB)
rule_versions       rule_version_id PK, card_key, version, effective_date, file_path,
                    created_at
graph_nodes         node_id PK, node_type (card|currency|airline|hotel), name, meta_json
graph_edges         edge_id PK, from_node FK, to_node FK, edge_type (earn|transfer),
                    ratio, min_transfer, notes, source_doc_id, last_verified
```

Migrations: Alembic in `database/migrations/`, single head, one migration per build day maximum.

**Reward caps state:** monthly cap consumption tracked in `interaction_events` aggregation or a dedicated `cap_usage` table (card_id, category, month, accrued_points). Use the dedicated table; simpler queries.

---

## 5. Rule Engine

**Purpose:** all reward math is deterministic, versioned, tested. The LLM never computes numbers.

Rule file format (`rules/seed/<card_key>/v<N>.json`):

Every numeric field uses a verified-value structure:

```json
{ "value": null, "status": "unverified", "source": null, "confidence": 0 }
```

- `status`: `verified` or `unverified`. `confidence`: 0 to 1, always 0 when unverified.
- `source`: official issuer URL, required when status is verified.
- The Rule Engine refuses to compute with unverified values and surfaces them as unknown in recommendations. Unknown is always preferred over incorrect.

```json
{
  "card_key": "hdfc_infinia",
  "version": 1,
  "effective_date": "2026-07-01",
  "reward_currency": "hdfc_reward_points",
  "base_earn": {
    "rate": { "value": null, "status": "unverified", "source": null, "confidence": 0 },
    "per_amount": 100,
    "currency": "INR"
  },
  "accelerated": [
    {
      "channel": "smartbuy",
      "category": "flights",
      "multiplier": { "value": null, "status": "unverified", "source": null, "confidence": 0 },
      "monthly_cap_points": { "value": null, "status": "unverified", "source": null, "confidence": 0 },
      "notes": "[NEED: verify from issuer docs]"
    }
  ],
  "caps": [
    {
      "scope": "smartbuy_total",
      "period": "month",
      "cap_points": { "value": null, "status": "unverified", "source": null, "confidence": 0 }
    }
  ],
  "exclusions": ["fuel", "rent", "wallet_loads"],
  "milestones": [],
  "point_value_reference_inr": { "value": null, "status": "unverified", "source": null, "confidence": 0 }
}
```

**Data integrity rule (hard):** every numeric value in rule files must carry a source entry. Seed files ship with `null` values and `"[NEED: verify from issuer docs]"` notes where the real number is unconfirmed. The engine treats null or unverified values as "cannot compute, surface as unknown" and the recommendation must say so. Never invent rates, caps, or transfer ratios.

Engine API:

```python
calculate_earn(card_key, amount, category, channel, month) -> EarnResult
check_cap(card_key, cap_scope, month) -> CapStatus
compare_cards(cards, amount, category, channel) -> list[EarnResult]  # sorted
```

Tests: pytest, table-driven, one test module per card, plus cap-boundary and exclusion cases. Target: Rule Engine at 100% branch coverage (it is small and pure).

---

## 6. Knowledge Platform + Hybrid RAG

**ChromaDB collections:** `reward_rules`, `transfer_rules`, `promotions`, `benefit_guides`, `issuer_policies`. Each chunk's metadata: `issuer`, `program`, `doc_type`, `source_url`, `last_changed` (ISO date), `doc_id`.

**Seed content:** markdown files in `knowledge/sources/`, one per card/program topic. Author them from official issuer pages; every fact carries its source URL. Unverified facts are marked `[NEED: verify]` and excluded from ingestion until verified.

**Ingestion:** chunk by heading (max ~500 tokens), embed with `sentence-transformers` (`all-MiniLM-L6-v2`, same as ASIM pattern), upsert keyed on `doc_id + chunk_index`, store `content_hash` in Postgres `knowledge_docs`.

**Hybrid retrieval (`knowledge/retrieval/`):**
1. Semantic: ChromaDB top-k (k=10)
2. Keyword: BM25 over the same corpus (rank_bm25, in-memory index rebuilt on ingest)
3. Metadata filter: issuer/program/doc_type inferred from query by the Planner
4. Fusion: reciprocal rank fusion of semantic + keyword
5. Freshness re-rank: multiply fused score by freshness decay on `last_changed` (half-life 180 days), floor 0.5
6. Return top 5 with metadata; citations flow through to the final response verbatim

**Crawlers (`knowledge/crawler/`):** `sources.yaml` lists official URLs per issuer/program. `crawl.py` fetches, extracts main content, computes hash, diffs against `knowledge_docs.content_hash`. On change: re-ingest chunk set, update `last_changed`, write a change record. `monitor.py` converts change records into `notifications` (opportunity engine input). GitHub Actions cron: ~~daily~~ **weekly** at 03:00 UTC for the pre-launch MVP (reward T&C pages change infrequently — better cost/signal ratio; tradeoff and how to switch to monthly documented in KNOWN_LIMITATIONS item 22 and `.github/workflows/crawl.yml`). Respect robots.txt; skip and log any source that disallows crawling rather than working around it.

---

## 7. Graph Engine

NetworkX directed graph, built by `graph/builder/` from `graph_nodes` + `graph_edges` (seeded in `database/seed/`, verified ratios only).

- Nodes: cards, reward currencies, airline programs, hotel programs
- Edges: `earn` (card → currency), `transfer` (currency → program, weight = transfer ratio, attrs: min_transfer, last_verified, source_doc_id)
- Core queries:
  - `best_transfer_paths(currency, target_program) -> ranked paths with cumulative ratio`
  - `redemption_options(portfolio, goal) -> ranked options with points required` (points-required math delegated to Rule Engine value tables; if `point_value_reference_inr` is null, rank by ratio only and label value as unknown)
- All ratios come from verified edges. Null/unverified edges are excluded from recommendations and surfaced as "unverified path exists" only.

Tests: known-graph fixtures with hand-computed best paths.

---

## 8. Multi-agent orchestration (LangGraph)

**State schema (`agents/state/schema.py`):**

```python
class AgentState(TypedDict):
    query: str
    user_id: str
    intent: str                      # spend | transfer | redeem | portfolio | general
    plan: list[ToolInvocation]       # deterministic tool call plan from Planner
    portfolio: dict | None
    preferences: dict | None
    knowledge: list[RetrievedChunk]
    rule_results: list[dict]
    graph_results: list[dict]
    memory: dict                     # episodic recall relevant to query
    recommendation: dict | None      # final structured output
    citations: list[Citation]
    confidence: str
    errors: list[str]

class ToolInvocation(TypedDict):
    tool: str                        # exact name from the Tool Registry
    args: dict                       # validated against the tool's input schema
```

The Planner emits ToolInvocation objects, never free-form strings. Tool wrappers validate args against the schemas in `contracts/tools/` before execution and reject anything malformed.

**Flow:** `planner → (conditional) tool nodes → recommender → END`

- **Planner node:** Gemini call. Classifies intent, extracts entities (cards, amounts, categories, destinations), emits tool plan. Prompt: `agents/prompts/planner.md`.
- **Tool nodes:** thin wrappers over Tool Registry; deterministic; append results to state; on failure append to `errors` and continue (graceful degradation).
- **Recommender node:** Gemini call. Receives state, writes recommendation JSON in exactly this contract (the LLM never invents output formats):

```json
{
  "decision": "...",
  "reasoning": [],
  "calculations": [],
  "citations": [],
  "confidence": { "level": "high|medium|low", "reason": "" },
  "assumptions": [],
  "alternatives": []
}
```

`calculations` entries are copied verbatim from rule_results and graph_results. Responses are validated against this contract (defined in `contracts/api/`) before persistence; invalid output triggers the single retry, then a typed failure. Prompt: `agents/prompts/recommender.md`. Hard instruction in prompt: never alter or generate numbers; only reference `rule_results` / `graph_results` values; if a needed number is unknown, state it.
- Conditional edges from Planner output; retries: 1 retry per LLM node with backoff; tool nodes no retry (deterministic).

**Tool Registry (`tools/registry.py`):** input/output schemas defined in `contracts/tools/`. each tool declares name, description, input schema (Pydantic), output schema, timeout. Tools per MASTER_SPEC categories: GetPortfolio, GetCards, GetRewardBalances, GetTravelGoals, SearchKnowledge, GetPromotions, GetTransferRatios, CalculateEarn, CheckCap, CompareCards, BestTransferPaths, RedemptionOptions, RecallMemory, StorePreference, GetOpportunities (Opportunity Engine Tool).

**Memory (`memory/`):**
- Episodic: `interaction_events` (recommendations shown/accepted/rejected, searches, trips) — recall = last N relevant events by type + recency
- Semantic: `preferences` table — key/value, updated via StorePreference tool when the user states a durable preference
- Procedural: static YAML of system policies (e.g., "never auto-execute transfers") loaded at startup
- Retrieval only; nothing appended blindly to prompts. Planner requests memory recall only when intent benefits.

**MCP (`mcp/`):** common base contract in `mcp/clients/base.py` plus six named clients: `BrowserMCPClient` and `PlaywrightMCPClient` (stub implementations returning typed pending errors), `EmailMCPClient`, `CalendarMCPClient`, `FlightSearchMCPClient`, and `HotelSearchMCPClient` (interface-only). All contracts documented in `contracts/mcp/`, matching the MCP Architecture chapter of MASTER_SPEC. Routing rule: the Planner prefers internal tools for business logic and computation; MCP is selected only when external capabilities or live information are required. Wire real servers only if the final day finishes early; live integrations are the only deferred piece (roadmap-flagged).

---

## 9. API surface (v1)

Auth (Supabase-issued JWT, FastAPI verifies):
- `POST /api/v1/auth/sync` — upsert local user row after Supabase signup/login
- `GET  /api/v1/auth/me`

Portfolio:
- `GET/POST /api/v1/portfolio` and `POST/PATCH/DELETE /api/v1/portfolio/cards[/{id}]`
- `PUT /api/v1/portfolio/balances/{card_id}`
- `GET/PUT /api/v1/portfolio/loyalty[/{id}]`
- `GET/PUT /api/v1/preferences`
- `GET/POST /api/v1/goals`

Intelligence:
- `POST /api/v1/chat` — body `{query}`, runs LangGraph, returns recommendation envelope; persists to `recommendations`
- `GET  /api/v1/recommendations[/{id}]`
- `POST /api/v1/recommendations/{id}/feedback` — accepted/rejected/saved
- `GET  /api/v1/opportunities` — notifications from monitor
- `GET  /api/v1/knowledge/search?q=` — direct hybrid retrieval (debug + UI "sources" view)
- `GET  /api/v1/health` — DB, ChromaDB, Redis, LLM ping

---

## 10. Frontend

Pages: login → dashboard (cards, balances, expiring points, opportunities count), cards CRUD, chat (recommendation cards with expandable reasoning, citations with freshness badges, confidence chip, accept/reject/save), recommendation detail, opportunities feed.

Design: shadcn components, one accent color, dark-friendly, data-dense dashboard. Recommendation card is the hero component: decision on top, numbers table (from rule/graph results), reasoning steps, citations footer. Follow the frontend-design skill during build (Claude Code has it).

API access: `lib/api.ts` with typed fetch wrapper, JWT from Supabase client session.

---

## 11. Evaluation framework

Golden sets in `evaluation/datasets/`:
- `retrieval.json` — 20 queries with expected doc_ids; metrics: precision@3, recall@5, MRR
- `rules.json` — 25 earn/cap scenarios with hand-computed expected values; metric: exact match (target 100%)
- `graph.json` — 10 path queries with expected ranked paths; metric: exact match (target 100%)
- `recommendations.json` — 10 end-to-end queries; checks: citations present, numbers traceable to tool results, no invented values (string match against tool outputs), confidence reported

`report.py` runs all, writes `evaluation/reports/REPORT.md` with a results table. GitHub Action runs on push to main. README badges the latest numbers. All metrics in README are labeled as measured eval results with the run date; product metrics from MASTER_SPEC (acceptance rate etc.) appear only as targets, clearly labeled.

---

## 12. Environment variables (`.env.example`)

```
DATABASE_URL=            # Supabase Postgres
SUPABASE_URL=
SUPABASE_ANON_KEY=       # frontend
SUPABASE_JWT_SECRET=     # backend verification
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.5-flash
REDIS_URL=               # Upstash
CHROMA_PERSIST_DIR=/data/chroma
BACKEND_URL=             # for frontend
FRONTEND_URL=            # CORS allowlist
ENV=development|production
```

---

## 13. Deployment

- **Supabase:** create project, run Alembic migrations via `DATABASE_URL`, enable email auth
- **Render:** `infra/render.yaml` — web service (uvicorn), persistent disk mounted at `/data` for ChromaDB, health check `/api/v1/health`. Free-tier cold starts are acceptable; note it in README.
- **Vercel:** import `frontend/`, set `NEXT_PUBLIC_*` env vars
- **GitHub Actions:** `crawl.yml` (daily cron, needs `DATABASE_URL` + backend ingest endpoint or direct DB access), `ci.yml` (ruff, pytest, tsc, next build), `eval.yml` (eval suite on main)

Deploy order D5: Supabase → Render → seed + ingest → Vercel → smoke test the golden recommendation queries against production.

---

## 14. Build milestones (July 19–24)

Each session ends runnable and committed. If a session slips, its remainder moves to the fast-follow list, never blocks the next session's core.

**Sprint (Jul 19, 12-hour Fable 5 window): Intelligence core.** Built entirely against in-memory fakes and fixture data; interfaces match this spec exactly so real wiring drops in later without refactoring. Rule Engine with extended field schema + 100% branch coverage including unverified-value refusal paths; seed rule files for hdfc_infinia, axis_atlas, amex_plat_travel (nulls + [NEED] flags); hybrid retrieval over fixture corpus with local ChromaDB; Graph Engine with verified-only fixture edges; full Tool Registry, Planner/Recommender prompts, LangGraph workflow; MCP base contract + four clients (two stubbed, two interface-only); all four golden eval sets + runners; ADR-001..008; VERIFICATION_QUEUE.md; KNOWN_LIMITATIONS.md.

**D2 (Jul 20): Foundation + wiring.** Alembic migrations for full schema, Supabase auth sync + JWT middleware, portfolio/cards/balances/loyalty/preferences/goals CRUD APIs with tests, real Postgres wired into the existing tool interfaces (replacing fixtures), Next.js scaffold: login, dashboard shell, cards CRUD, typed API client.

**D3 (Jul 21): Knowledge at scale.** Full seed corpus for the three MVP issuers (verified facts only, sourced), ingestion pipeline against production ChromaDB layout, crawler + diff + sources.yaml, GitHub Actions crawl cron, retrieval eval re-run against the full corpus, `/knowledge/search` endpoint.

**D4 (Jul 22–23): Product surface.** `/chat` endpoint through LangGraph with persistence and feedback, chat UI with recommendation cards (decision, numbers table, expandable reasoning, citation footer with freshness badges, confidence chip, accept/reject/save), transfer explorer view, dashboard data wiring, end-to-end eval green.

**D5 (Jul 23–24): Opportunity engine + ship.** monitor.py change records → notifications, opportunities API + UI feed, eval report + CI + eval GitHub Actions, README (problem, architecture diagram, eval results labeled as measured with run date, targets labeled as targets, roadmap, [NEED] register), deploy Supabase → Render → seed + ingest → Vercel, production smoke test on the 10 end-to-end golden queries.

Fast-follow list (post Jul 24, if anything slips): live MCP servers (Email, Calendar, Flight/Hotel Search), Rule Verifier subsystem (see section 14a and ADR-009), admin panel for card management and rule verification (operator UI over the Rule Verifier; needs a new admin role/permission layer — see ADR-017), additional issuers per VERIFICATION_QUEUE priorities, statement parsing, award availability, email notifications.

## 14a. Fast Follow: Rule Verifier

Not built in the MVP. Documented now so the extension point is designed correctly from day one; see ADR-009 in docs/adr/.

Build a Rule Verifier subsystem that extends the Knowledge Platform (not the Rule Engine):

```
Knowledge Platform
    │
    ├── Crawler
    ├── Parser
    ├── Extractor
    ├── Rule Verifier
    └── Retrieval
                │
                ▼
        rules/seed/
                │
                ▼
        Rule Engine
```

Responsibilities:

- Parse official issuer documents.
- Extract structured reward values.
- Compare against existing rule definitions.
- Generate candidate change records conforming to `contracts/events/verification_record.schema.json`.
- Populate `docs/VERIFICATION_QUEUE.md`.
- Never modify rule files automatically.

Rule updates require explicit manual approval before becoming active. Successful approval automatically re-runs Rule Engine tests, Graph Engine tests, and evaluation benchmarks.

**Verification record contract** (`contracts/events/verification_record.schema.json`):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "VerificationRecord",
  "type": "object",
  "required": ["card", "field", "candidate_value", "status", "confidence", "source", "extractor"],
  "properties": {
    "card": { "type": "string" },
    "field": { "type": "string" },
    "old_value": { "type": ["string", "number", "null"] },
    "candidate_value": { "type": ["string", "number", "null"] },
    "status": { "type": "string", "enum": ["pending_review", "approved", "rejected"] },
    "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
    "source": {
      "type": "object",
      "required": ["title", "url", "verified_at"],
      "properties": {
        "title": { "type": "string" },
        "url": { "type": "string" },
        "verified_at": { "type": "string", "format": "date" }
      }
    },
    "extractor": {
      "type": "object",
      "required": ["parser", "model"],
      "properties": {
        "parser": { "type": "string" },
        "model": { "type": ["string", "null"] }
      }
    },
    "approved_by": { "type": ["string", "null"] },
    "approved_at": { "type": ["string", "null"] }
  }
}
```

Example instance:

```yaml
card: hdfc_infinia
field: smartbuy_multiplier
old_value: "10x"
candidate_value: "5x"
status: pending_review
confidence: 0.91
source:
  title: "HDFC Infinia Reward Points Terms"
  url: "https://..."
  verified_at: "2026-07-19"
extractor:
  parser: pdf_parser_v1
  model: null
approved_by: null
approved_at: null
```

Human-readable and tool-readable by the same structure; keeps verification deterministic and gives a full audit trail.

## 15. Definition of done (per MASTER_SPEC §17, operationalized)

- All CRUD flows work in production UI
- `/chat` returns cited, confidence-scored recommendations for the 10 end-to-end golden queries in production
- Rule and graph evals at 100%; retrieval precision@3 reported honestly whatever it is
- No numeric claim in any response, README, or seed file without a source or a [NEED] flag
- CI green, eval report committed, ADRs complete, README complete

No feature is considered complete until: implementation exists, automated tests pass, evaluation passes, citations are present, and the README is updated if public behavior changed.

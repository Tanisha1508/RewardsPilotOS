# RewardsPilotOS

An AI copilot for credit-card rewards optimization (Indian issuers first). Ask
it *"Which of my cards should I use for a ₹50,000 flight?"* or *"Should I
transfer my points to an airline, and what would I get?"* and it answers with a
**cited, confidence-scored recommendation whose every number comes from
deterministic engines — never from the language model.**

> **Core principle — no fabricated data, ever. Unknown is always preferred over
> incorrect.** Every numeric fact (earn rates, caps, transfer ratios, point
> values) carries a `{value, status: verified|unverified, source, confidence}`
> structure. Unverified values are *refused* by the engines and surfaced as
> **unknown** in the answer, with a `[NEED: verify from issuer docs]` flag
> tracked in [`docs/VERIFICATION_QUEUE.md`](docs/VERIFICATION_QUEUE.md). The LLM
> never does arithmetic; it copies engine outputs verbatim and states unknowns
> plainly.

## Live

| | |
|---|---|
| **App** | **https://rewards-pilot-os.vercel.app** |
| **API health** | https://rewardspilotos.onrender.com/api/v1/health |
| **Privacy policy** | https://rewards-pilot-os.vercel.app/privacy |

It runs entirely on free tiers, and the limits that come with that are stated
rather than hidden: **five questions per user per day** (the app says so, and
when it lifts), and a first visit before roughly 06:30 IST pays a one-off
wake-up — a scheduled ping keeps the backend warm for the rest of the day, which
took `/health` from 36 s to under a second.

The app itself is behind a login, because it holds people's card portfolios —
so here is what is behind it.

## See it work

An answer, as the product gives it. Every number in the prose also appears in
the table below it, and every source carries the date it was checked:

![A recommendation for a ₹25,000 flight: Axis Bank Atlas earning 1,250 at a
2.5× bonus rate, ahead of HDFC Infinia at 830 and Amex Platinum Travel at 500,
marked high confidence, with two dated official sources](docs/assets/answer-with-sources.png)

The transfer explorer, where the verification discipline is easiest to see —
note the last line, which keeps a source conflict on the record instead of
picking a winner:

![Axis EDGE Miles transfer partners with per-group caps, 1:2 and inverted 2:1
ratios, partners removed on a specific date, and a recorded conflict between two
sources](docs/assets/transfer-explorer.png)

And the engine underneath, which you can run yourself — no account, no API key,
no network — once [Quickstart](#quickstart-local) is done. *"Which card should I
use for a ₹50,000 flight?"*, asked of the rule engine directly:

```python
from rules.parser.loader import load_rule
from rules.evaluator.evaluator import evaluate_earn

for key in ("axis_atlas", "hdfc_infinia", "amex_plat_travel", "axis_magnus"):
    result = evaluate_earn(load_rule(key), 50000, "flights", "direct", "2026-08")
    print(key, result.status, result.points, result.unknown_reasons)
```

```
axis_atlas        computed  2500.0  []      # accelerated rate, edge_miles
hdfc_infinia      computed  1665.0  []      # base rate, hdfc_reward_points
amex_plat_travel  computed  1000.0  []      # base rate, membership_rewards
axis_magnus       unknown   None    ['reward rules for axis_magnus are not yet
                                     verified: base earn rate is unverified
                                     (value=None); cannot compute']
```

The first three cards are verified against official issuer documents, and those
are the same numbers production returns for this query. The fourth is the point
of the project.

That second block is the point of the project. The rate for that card is easy to
find on a blog, and a language model would happily produce one. The engine
refuses, the answer says it doesn't know, and the card goes into the
[verification queue](docs/VERIFICATION_QUEUE.md) until someone confirms the
number against the issuer. **A wrong rewards number costs the user real money;
"I don't know" costs them nothing.**

## Reading this repo in five minutes

If you want to check that the guarantee above is actually enforced rather than
described, these four files are where it lives:

| | |
|---|---|
| [`rules/evaluator/evaluator.py`](rules/evaluator/evaluator.py) | The refusal itself — an unverified value returns *unknown* instead of a number |
| [`agents/recommendation/recommender.py`](agents/recommendation/recommender.py) | The validator that rejects an answer whose prose contains a number no tool produced |
| [`contracts/tools/`](contracts/tools/) | The typed boundary the planner's tool calls are validated against |
| [`docs/KNOWN_LIMITATIONS.md`](docs/KNOWN_LIMITATIONS.md) | What it still gets wrong, written down rather than discovered by you |

Design decisions are in [`docs/adr/`](docs/adr/) — 19 of them, each recording the
option that was rejected and why.

---

## Why this is built the way it is

The hard problem in a rewards assistant is not language — it's **being right
about numbers.** A model that confidently invents a transfer ratio or an earn
rate is worse than useless; it loses the user real money. So the architecture
puts a hard wall between *deterministic computation* (which owns every number)
and *language* (which owns phrasing and only phrasing). The LLM plans which
tools to call and writes the final prose, but each figure it prints is copied
byte-for-byte from a rule-engine or graph-engine result, and a runtime validator
rejects any answer whose prose contains a number that isn't traceable to a tool
output.

This is enforced, not aspirational:
- The **Rule Engine** refuses to compute with an unverified value.
- The **Recommender** is validated: non-verbatim numbers, uncited sources,
  ungrounded prose, or over-claimed confidence are rejected and retried.
- Rule files fail to load if a numeric field lacks its verified-value structure.

## Architecture

```
                 ┌─────────────────────── LangGraph orchestration ───────────────────────┐
   user query →  │  Planner (Gemini)  →  deterministic tool nodes  →  Recommender (Gemini) │  → cited answer
                 └────────────┬──────────────────────┬───────────────────────┬────────────┘
                              │                       │                       │
                       Rule Engine             Graph Engine            Knowledge Platform
                    (versioned JSON,        (NetworkX transfer      (ChromaDB + BM25 + RRF
                     verified-only math)     graph, verified edges)   + freshness re-rank)
```

- **Rule Engine** (`rules/`) — versioned JSON rule files per card; deterministic
  earn/cap math; validity windows enforced at load and evaluation time; refuses
  unverified values and returns *unknown* rather than guessing.
- **Graph Engine** (`graph/`) — a NetworkX graph of cards → reward currencies →
  airline/hotel programs. Best-transfer-path and redemption optimization over
  **verified edges only**; unregistered currencies/programs return an explicit
  "no data" signal, never a silent empty result.
- **Knowledge Platform** (`knowledge/`) — hybrid retrieval-augmented generation:
  ChromaDB semantic search + BM25 keyword + metadata filtering + reciprocal rank
  fusion + freshness re-rank, over a verified corpus. A crawler detects source
  changes for re-verification (detection, not auto-ingestion).
- **Multi-agent orchestration** (`agents/`, `tools/`) — LangGraph: a Planner
  emits typed `ToolInvocation`s validated against `contracts/tools/`, a
  deterministic tool layer executes them, and a Recommender assembles the
  contract-exact answer. A tiered LLM fallback (Gemini models → Groq) keeps it
  answering through provider outages.
- **Backend** (`backend/`) — FastAPI + Pydantic v2, JWT auth (Supabase), REST
  under `/api/v1/...` on a `{data, error, meta}` envelope, CRUD for
  portfolio/cards/balances/goals/preferences, and a `/chat` endpoint that runs
  the full LangGraph flow with persistence and feedback.
- **Frontend** (`frontend/`) — Next.js 14 (App Router, TypeScript strict): a
  recommendation chat UI, a transfer explorer, a portfolio dashboard, and a
  shareable page per answer.
- **Privacy and limits** — personal details are scrubbed before anything reaches
  the model, query strings are kept out of access logs, the browser talks to the
  API same-origin under a strict Content Security Policy, row-level security sits
  under the database as a second layer, and a user can delete everything the
  service holds about them. The audit is in
  [`docs/PRIVACY_AUDIT.md`](docs/PRIVACY_AUDIT.md), the rules for what may be
  logged in [`docs/LOGGING_POLICY.md`](docs/LOGGING_POLICY.md).
- **Evaluation** (`evaluation/`) — golden sets for retrieval, rules, graph, and
  end-to-end recommendations, plus a **live-LLM smoke suite** that catches
  model-behaviour regressions the scripted golden suite cannot
  (see [`evaluation/smoke/README.md`](evaluation/smoke/README.md)).

Design decisions are recorded as ADRs in [`docs/adr/`](docs/adr/); engineering
and product sources of truth are `BUILD_SPEC.md` and `MASTER_SPEC.md`.

## Tech stack

| Layer | Choice |
|---|---|
| Backend | FastAPI, Pydantic v2, Python 3.11 |
| Orchestration | LangGraph |
| LLM | Gemini (`gemini-3.5-flash`) primary, Groq (Llama 3.3) fallback (ADR-018) |
| Rules | Custom deterministic engine over versioned JSON |
| Graph | NetworkX |
| Retrieval | ChromaDB (persistent) + BM25 + reciprocal rank fusion; `all-MiniLM-L6-v2` embeddings |
| Database / Auth | PostgreSQL (Supabase), Supabase Auth (JWT, ES256/HS256) |
| Cache | Redis (Upstash), optional |
| Frontend | Next.js 14, TypeScript, Tailwind |
| Hosting | Render (backend), Vercel (frontend), Supabase, Upstash — free tier |

All free tier and open source. No Docker. Single dependency manifest
(`pyproject.toml`).

## Quickstart (local)

```bash
# 1. Backend deps
uv venv --python 3.11
uv pip install -e ".[dev]"

# 2. Config: copy the template and fill in your own keys
cp .env.example .env            # DATABASE_URL, SUPABASE_*, GEMINI_API_KEY, ...

# 3. Tests (deterministic; a subset needs a local Postgres via TEST_DATABASE_URL)
.venv/bin/python -m pytest

# 4. Evaluation report → evaluation/reports/REPORT.md
.venv/bin/python -m evaluation.metrics.report

# 5. One query end to end (real Gemini if GEMINI_API_KEY is set; deterministic
#    scripted LLM otherwise, so it runs fully offline)
.venv/bin/python -m agents.workflows.demo
```

Run the full app locally:

```bash
# backend
.venv/bin/uvicorn backend.main:app --reload            # http://localhost:8000

# database migrations (against your Supabase/Postgres DATABASE_URL)
.venv/bin/alembic -c database/migrations/alembic.ini upgrade head

# knowledge ingestion (embeds the verified corpus into ChromaDB)
.venv/bin/python -m knowledge.pipeline.run

# frontend
cd frontend && npm install && npm run dev               # http://localhost:3000
```

The frontend reads `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`,
and `NEXT_PUBLIC_BACKEND_URL` (see `frontend/.env.local.example`).

## Verification & quality

Measured on 2026-07-31, not aspirational — the numbers below are copied from
[`evaluation/reports/REPORT.md`](evaluation/reports/REPORT.md), which records its
own run date. Product metrics in `MASTER_SPEC.md` are labelled as targets.

```
Retrieval (real corpus)   recall@5 0.987   MRR 0.926   top-1 0.885
Rules                     100%  (25/25)
Graph                     100%  (10/10)
End to end                100%  (10/10)
668 tests passing
```

- **Deterministic test suite** covering the rule engine (branch-complete),
  graph, retrieval, agents, auth, and Postgres integration.
- **Two retrieval benchmarks, and the newer one is the one that matters.** The
  original fixture benchmark mostly asks about invented banks, so a good score
  there says the ranking works and nothing about real users; the real-corpus set
  asks the questions a user would actually ask. Keeping both is deliberate —
  a benchmark that cannot see a defect is not evidence the defect is absent.
- **Live-LLM smoke suite** (`evaluation/smoke/`) runs the real model against a
  handful of queries and asserts structural properties, catching planner-
  behaviour regressions the scripted golden suite is blind to by construction.
- **Verification pipeline** — every card's data is verified field-by-field
  against official issuer sources before it can ship; the audit trail and open
  items live in [`docs/VERIFICATION_QUEUE.md`](docs/VERIFICATION_QUEUE.md), and
  known limitations are tracked candidly in
  [`docs/KNOWN_LIMITATIONS.md`](docs/KNOWN_LIMITATIONS.md).

## Status & roadmap

**Deployed and working in production.** The whole thing is live: the
deterministic intelligence core (rule engine, graph engine, hybrid retrieval),
the multi-agent orchestration, the FastAPI backend with auth + CRUD + `/chat`,
and the Next.js frontend — running against real Postgres/Supabase and real
Gemini, verified end to end through the browser rather than only in tests.

Since the first deploy, the work has been about making it honest and usable
rather than adding features: a privacy pass (PII scrubbed before the model, a
published policy, working account deletion), a per-user daily limit, a layout
that works on a phone, per-answer permalinks, and the cold-start fix above. Four
data-integrity bugs were found and fixed in one sweep, all the same shape —
something untrue reaching the answer path through a route the safeguards did not
check, because every safeguard was built to check the model and none of them
checked the tools or the corpus feeding it.

**Data coverage — the real ceiling, and it is not code.** Three cards are
verified end to end and are the three the app offers: HDFC Infinia, Axis Atlas,
Amex Platinum Travel. Seven more have rule files whose rates are still
unverified, so the app shows them by name and does not let you add them — a card
that tracks perfectly and answers "unknown" to every question helps nobody. They
are worked through in the order set out in
[`docs/VERIFICATION_QUEUE.md`](docs/VERIFICATION_QUEUE.md), and tests fail if a
card is verified and still locked, or offered and still unverified.

Promotions and issuer policies are empty for real issuers, which is why "any
transfer bonuses right now?" and "when do my points expire?" go unanswered. That
is data to gather, not a bug to fix.

**Next, in the order it matters:**
- **More verified card data** — the one change that widens what the product can
  say, per the verification queue.
- **Opportunity engine** — a monitor that turns detected source changes and
  expiring benefits into a user notification feed. Designed, deferred to a
  fast-follow after deployment.
- **An admin panel** for card management and rule verification (ADR-017), and
  **live MCP integrations** (email, calendar, flight/hotel search).

The working backlog is [`docs/BACKLOG.md`](docs/BACKLOG.md); current deployment
state is [`docs/DEPLOY_STATUS.md`](docs/DEPLOY_STATUS.md).

## License

See [`LICENSE`](LICENSE).

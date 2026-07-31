# Wiring sweep — what exists but nothing calls (A3, 2026-07-31)

Three defects this year came from the same shape: a capability existed, nothing
called it, and nobody noticed until something forced a look. `GetPromotions`,
`StorePreference` and `POST /portfolio` were each found by accident.

So this is the deliberate version — every route, every client method, every tool
and every database table checked once, with the result written down. **Nothing
here is a bug on its own.** Unwired capability is a risk because it reads as a
working feature: it appears in the schema, in the tool catalogue, in the API
surface, and it is impossible to tell "deliberately waiting" from "forgotten"
without a record like this one.

Method: routes parsed from `backend/api/`, client methods from
`frontend/lib/api.ts` grepped against `app/` `components/` `hooks/` `services/`,
tools from `tools.registry.REGISTRY` against `agents/prompts/planner.md`, models
from `backend/models/` grepped repo-wide excluding models and migrations.

---

## 1. Routes with no caller — 2 of 26

| Route | Status |
|---|---|
| `POST /api/v1/portfolio` | **Known.** A portfolio is created automatically on first sign-in (`backend/application/users.py`), so a second way to make one has no caller and would allow a second portfolio the rest of the app does not expect |
| `PUT /api/v1/portfolio/loyalty` | **New.** The write half of loyalty. Deliberate — see D-1 below |

## 2. Client methods no page calls — 4 of 20

| Method | Status |
|---|---|
| `api.listLoyalty` | Part of the D-1 deferral. **Both halves of loyalty are dead**: no page reads it, and the write route above has no client at all |
| `api.getRecommendation` | This is **A9** on the backlog — the permalink. Route and client both exist; only the page is missing |
| `api.getPortfolio` | Portfolio page uses `listCards` + `listBalances` instead, which is the shape it actually needs. The whole-portfolio call is redundant rather than missing |
| `api.health` | No page shows service health. Reasonable — a user cannot act on it. Would matter for an admin panel (F2) |

## 3. Tools — 0 new findings

All 15 registered tools are described to the planner by `tool_catalog()`, and all
15 are exercised in tests or evals. Two are described but not *guided* in the
prompt, both already recorded decisions:

- **`GetPromotions`** — works, has corpus data, but both promotion documents are
  fixture issuers (`demo_bank`, `sample_bank`). Guiding the model toward it
  would surface synthetic content as real. The gap is missing data, not missing
  wiring.
- **`StorePreference`** — B3 / D-7, a candidate for removal.

## 4. Database — 4 tables nothing reads or writes

The real find. All four exist in the schema, have a model class, and have no
reader and no writer anywhere in the codebase.

| Table | Why it is dead |
|---|---|
| `graph_nodes` | The Graph Engine builds a NetworkX graph from JSON and uses its own `GraphNodeRecord` (`graph/models/records.py`). It never touches Postgres. The name collision hides this — `GraphNode` appears used until you check which class |
| `graph_edges` | Same |
| `rule_versions` | The Rule Engine reads versioned JSON files from `rules/seed/`. Nothing imports `RuleVersion` at all |
| `notifications` | There is no notification feature |

Columns `file_path`, `meta_json` and `rule_version_id` are unread for the same
reason — they sit inside these tables. (`updated_at` also showed up in the scan
and is a false positive: it is the name of a helper function in
`backend/models/base.py`, not a column. The column is `last_updated`.)

**Not proposing to drop them.** Dropping tables is a schema migration, which
CLAUDE.md rule 6 puts behind a spec update, and three of the four are plausible
homes for planned work — the Rule Verifier (ADR-009) is the natural writer of
`rule_versions`, and `notifications` is the natural home for the opportunity
engine (F3). `graph_nodes`/`graph_edges` are the weakest case: the Graph Engine
is deliberately file-based, so a Postgres mirror has no design behind it.

They are recorded here so the next person reading the schema does not assume the
graph is stored in Postgres, or that rule versions are tracked in the database.

---

## How to fix each one

Written out so none of these needs re-deriving. Each says what already exists,
so the work is scoped rather than guessed at.

### Loyalty — D-1, needs a decision first

**Exists:** `loyalty_accounts` table, `GET` and `PUT /api/v1/portfolio/loyalty`,
and the client method `api.listLoyalty`.
**Missing:** a client method for the `PUT`, and any page at all.

To build it:

1. Add `api.setLoyalty(...)` to `frontend/lib/api.ts` — mirror `api.setBalance`,
   which wraps the equivalent `PUT` for balances.
2. Add a loyalty section to **Portfolio**, not Redeem. It is something you *have*
   (a programme number and a balance), which is what Portfolio answers.
3. Then remove the caveat in `RedemptionOptions`, which currently counts every
   shortfall from zero because it cannot see programme balances held outside a
   card.

Step 3 is the actual prize — it is why D-1 blocks "2.7, the missing half of
redemption". Steps 1 and 2 are small; the decision is whether the product wants
to track programme balances at all.

### Permalink — A9, no decision needed

**Exists:** `GET /api/v1/recommendations/{id}` and `api.getRecommendation`.
**Missing:** one page.

Add `frontend/app/recommendations/[rec_id]/page.tsx` rendering through the
existing `RecommendationCard` — the same component History and Ask both use, so
a linked answer shows the same numbers, citations and confidence it was given.
Link to it from each row of the History list.

One caution: the route marks the recommendation `viewed` as a side effect of
`GET`. That is fine from a page a user opened, which is what "viewed" means.

### The two unguided tools — both already decided

**`GetPromotions`** — the fix is *data*, not wiring. It works and is described
to the planner; both promotion documents in the corpus are for fixture issuers
(`demo_bank`, `sample_bank`). When a real issuer promotion is verified into the
corpus, add one line to `agents/prompts/planner.md` guiding the model toward it.
Until then, leaving it unguided is what stops synthetic content being presented
as real.

**`StorePreference`** — two honest futures, pick one:
- **B3 / D-7:** delete it. One line. It writes to a store with no provenance
  column, so a preference it sets is indistinguishable from one the user set.
- **D-3:** if Ask becomes multi-turn, it becomes genuinely useful — but it needs
  a provenance column first, so the UI can say "the assistant recorded this".

Leaving it registered-but-unguided is the one state that is not a decision.

## What this changes on the backlog

Nothing becomes urgent. Two entries gain detail:

- **A9** (permalink) — confirmed as page-only work; route and client exist.
- **D-1** (loyalty) — confirmed dead on both sides, so the decision is genuinely
  "build it" rather than "connect the existing half".

## Re-running this

The checks are four greps and worth repeating whenever a feature lands
half-connected. The shape to look for is always the same: **something addressable
that nothing addresses.** A route with no client, a client with no page, a tool
the prompt never mentions, a table with no reader.

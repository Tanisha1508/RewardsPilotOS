# Privacy audit — 2026-07-30

First deliberate privacy pass. Prompted by the stated agenda: *a reliable,
automated system that ensures accuracy, privacy and continuous improvement for a
broad user base*. Privacy had received no dedicated attention until now.

Scope: what the system stores, what leaves it, who can reach it, and what a user
can do about it. Code-level audit plus live checks where possible.

**Nothing in here was changed.** This is findings only, so the fixes can be
prioritised rather than applied piecemeal.

---

## What is already right

Worth recording, because several of these are deliberate and easy to undo by
accident.

| | Practice | Where |
|---|---|---|
| ✅ | **No application logging.** No `logging`/`logger` calls anywhere in `backend/`, `agents/`, `tools/`, `rules/`, `graph/`. Only `print()` in CLI scripts. Nothing to leak, because nothing is written | repo-wide |
| ✅ | **No third-party scripts.** Zero analytics, tag managers, session recorders, error trackers in the frontend | `frontend/` |
| ✅ | **Errors do not leak internals.** Unmapped exceptions return a generic message; the code comments say why — "can carry SQL, file paths, or connection strings" | `backend/api/responses.py:60` |
| ✅ | **The Planner receives only the query.** `user = json.dumps({"query": state["query"]})`, with a comment stating the user id is deliberately withheld | `agents/planner/planner.py:72` |
| ✅ | **Identity never comes from model output.** Tools resolve the caller from ambient context, so a hallucinated id cannot read another user's data (KNOWN_LIMITATIONS 24, Class C) | `tools/*/source.py` |
| ✅ | **Cascade deletes exist.** `recommendations`, `interaction_events`, `notifications`, `preferences`, `cards` all `ON DELETE CASCADE` from `users` | `backend/models/` |
| ✅ | **`request_id` carries no PII.** A random UUID, used only for support correlation | `backend/middleware/request_context.py:35` |

---

## Findings

Ordered by risk.

### P1 — RESOLVED 2026-07-30: the app's tables are NOT reachable by the anon key

Checked in the Supabase Table Editor with **View data as a role → Anonymous**:

```
ERROR: 42501: permission denied for table users
HINT: Grant the required privileges to the current role with:
      GRANT SELECT ON public.users TO anon;
```

**Not an RLS denial — a table-privilege denial.** The `anon` role holds no
`SELECT` grant on the table, and Postgres evaluates grants *before* RLS, so the
request never reaches a policy at all.

**Why the exposure never existed:** these tables were created by Alembic
migrations running as the owner role. Supabase auto-grants `anon`/`authenticated`
privileges only for tables created through its own tooling; migration-created
tables in `public` get none. The path I was worried about was closed by how the
schema was built.

**What is actually protecting the data, though, is the absence of a GRANT — not
RLS.** That is one layer rather than two, and the failure mode is a single
statement away: anyone following the hint Postgres itself prints
(`GRANT SELECT ON public.users TO anon`) opens the table, and if RLS is disabled
there is nothing behind it.

**Second layer added, same day.** RLS is now enabled on all 16 public tables
with **no policies**, which is deny-all for every non-owner role.

Evidence, and who produced it — worth separating, because the two halves were
established differently:

| Claim | How it was established | Confidence |
|---|---|---|
| RLS is on for all 16 tables | `pg_tables` query, owner-run | Direct |
| The backend still works | **Live check** — the deployed app lists cards and balances after the change | Direct |
| `anon` is denied | Table Editor as the Anonymous role, **before RLS was enabled** — a GRANT denial (42501), a different mechanism | Direct, but pre-change |
| `anon` is *still* denied after RLS | **Not observed.** RLS only ever restricts, never grants, so it cannot have become more permissive | Reasoning, not evidence |

The last row is the open one. A post-RLS check on `cards` under the Anonymous
role would close it; the expected result is the same 42501. Nothing suggests
otherwise, but it has not been seen.

The direct anon check could not be run from here: reading the anon key out of the
client bundle to query PostgREST was blocked as credential extraction, correctly,
and was not worked around.

`anon` is now denied by two independent mechanisms: no GRANT, and no policy. A
stray `GRANT SELECT ... TO anon` — including the one Postgres prints in its own
error hint — no longer opens the data.

**Do not add `FORCE ROW LEVEL SECURITY`.** It makes RLS apply to the owner too;
with no policies that would deny the backend and take the app down.

All app tables were checked under the Anonymous role, not just `users`.

### P2 — FIXED 2026-07-30: a stable user identifier was sent to Google alongside financial data

`GetPortfolioOutput` includes `user_id`, and `agents/workflows/graph.py:45` puts
the whole payload into `state["portfolio"]`, which the Recommender serialises
into the digest sent to Gemini:

```
state["portfolio"] = payload      # includes user_id, portfolio_id, card_id
```

So every recommendation request sends Google: the user's **UUID**, their
**cards**, their **balances**, their **preferences**, their **past interactions**
and their **question**.

This directly undoes a decision made one layer up — the Planner deliberately
withholds the user id, with a comment explaining why. The Recommender
reintroduces it through a tool result.

The identifiers buy nothing: the model never needs `user_id`, `portfolio_id` or
`card_id` to compare cards. Stripping them costs nothing and removes the link
between a financial profile and a persistent identity at the provider.

**Fixed.** `agents/privacy.py::strip_identifiers` removes every database
surrogate key (`user_id`, `portfolio_id`, `card_id`, `balance_id`, `rec_id`,
`event_id`, `goal_id`, `pref_id`, `loyalty_id`, `notif_id`) recursively from the
digest, applied at the point it is serialised.

Applied to the whole digest, not to `portfolio` alone: the leak was never really
about portfolio, it was that *any* tool result can carry an id and a future tool
would reintroduce it silently. Filtering by key name at the boundary covers new
tools by default.

`card_key` is deliberately kept — it names a rule file, not a user, and the
engines and prompts depend on it. A broader "anything ending in `_id`/`_key`"
rule would have broken every comparison.

Cover in `tests/agent/test_no_identifiers_leave_the_process.py`, asserted at the
digest boundary rather than on the helper — a correct helper proves nothing if a
later edit serialises the dict before calling it. Tests check key names AND raw
UUID values, and that everything the model reasons with survives.

### P3 — A user cannot delete their data

The only delete endpoint is `DELETE /portfolio/cards/{card_id}`. There is no
route to delete an account, a recommendation, the question history, or stored
preferences.

The database is ready for it — every table cascades from `users` — but nothing
can trigger it. Deletion today means someone with database access doing it by
hand.

For a broad user base this is not a nice-to-have: erasure is a statutory right
under India's DPDP Act and the GDPR, and the app already stores every question a
user has typed.

### P4 — Every question is stored indefinitely

`recommendations.query` holds the raw text of every question, and
`interaction_events.payload_json` holds event payloads. There is no TTL, no
anonymisation, no archival policy.

That is a deliberate product feature (History exists because of it), so this is
not a bug — but "forever" is a decision that has not been made explicitly, and
it compounds P3: the data cannot be removed by the person who created it.

### P5 — No disclosure that data reaches a third-party model

There is no privacy policy, no terms, and no in-app statement that questions and
portfolio contents are sent to Google. A user cannot know their card holdings
leave the service, and cannot decline.

Cheap and honest interim: one line under the Ask box naming what is sent and to
whom. The real answer is a privacy policy before the URL is shared (D-2).

### P6 — Search text travels in URL query strings

`GET /api/v1/knowledge/search?q=...` puts the search text in the URL, which
lands in Render's access logs and any intermediary, whereas `POST /chat` keeps
the question in the body.

Today `q` is generated by the app on the Redeem page, so no user text is
exposed. But the endpoint accepts arbitrary text and was user-facing until the
2026-07-30 restructure, so this is a latent exposure rather than a live one.

### P7 — Session token in `localStorage`

Supabase's default. Readable by any script on the origin, so an XSS becomes a
full account takeover, and the token survives tab close.

Materially mitigated by P-good: there are **no third-party scripts at all**, so
the injection surface is the app's own code. Worth knowing rather than urgent.

### P8 — `x-request-id` is client-controllable

`request.headers.get("x-request-id") or str(uuid.uuid4())` — a caller can set
their own request id, which is echoed back in responses. Minor: it allows log
correlation across users and injection of arbitrary strings into any future log
line. Free to fix by validating the shape.

---

## Recommended order

1. ~~**P1**~~ — **done, clean.** No anon access. Optional follow-up: enable RLS
   as a second layer.
2. ~~**P2**~~ — **done.** Identifiers stripped at the digest boundary.
3. **P3** — account and data deletion. Needed before a broad user base, and the
   schema already supports it.
4. **P5** — disclosure. One honest line now; a policy before sharing the URL.
5. **P4, P6, P7, P8** — decide retention explicitly; move search to POST or stop
   accepting free text; validate `x-request-id`.

## Not examined

- Supabase's own retention and regional storage (where the Postgres instance
  physically lives, and what Supabase logs).
- Google's retention for Gemini free-tier API traffic. **Worth checking
  specifically:** free tiers of LLM APIs sometimes permit training on submitted
  content, which would be a materially different privacy posture from the paid
  tier.
- Render and Vercel log retention windows.
- Whether `interaction_events` payloads contain anything beyond ids and status.

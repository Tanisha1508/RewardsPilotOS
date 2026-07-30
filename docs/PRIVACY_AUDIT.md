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

### P1 — UNVERIFIED, potentially critical: are the app's tables exposed through Supabase's public REST API?

Supabase auto-exposes every table in the `public` schema through PostgREST, and
the **anon key is public by design** — it ships in the browser bundle. The only
thing preventing one user from reading every other user's rows through that path
is **row-level security**.

Our backend never uses that path (it connects with `DATABASE_URL` via SQLAlchemy
and scopes every query by `current_user_id`), so RLS could easily have been left
off without anything breaking or looking wrong.

**Not verified.** The live check — reading the anon key from the bundle and
querying PostgREST — was blocked as credential extraction, correctly. It needs
checking directly, and it is the highest-risk unknown here.

**How to check (about a minute):**
1. Supabase dashboard → **Table Editor**. Any app table (`cards`, `users`,
   `recommendations`, `preferences`) in the `public` schema.
2. Look at the **RLS** badge on each. "RLS disabled" on a table holding user
   data means it is readable and writable by anyone holding the anon key.
3. Also **Settings → API → Exposed schemas**. If `public` is listed and the
   tables live there, they are reachable.

**If RLS is off:** either enable RLS with deny-all policies (the backend is
unaffected — it connects as the database owner, which bypasses RLS), or move the
app tables out of the exposed schema. The first is less disruptive.

### P2 — A stable user identifier is sent to Google alongside financial data

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

**Fix:** drop identifier fields from the digest at the boundary where it is
built, so it cannot be reintroduced by a future tool.

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

1. **P1** — verify RLS. A minute of dashboard checking; potentially the largest
   hole in the system, and the only one where the blast radius is every user.
2. **P2** — strip identifiers from the LLM digest. Small, self-contained, and
   removes a real link between identity and financial data at a third party.
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

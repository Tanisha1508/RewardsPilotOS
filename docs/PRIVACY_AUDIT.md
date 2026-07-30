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
| `anon` is *still* denied after RLS | **Observed** — `public.cards` under the Anonymous role returns `42501 permission denied` post-change | Direct |

Closed on `cards` specifically, which is the table holding financial data.

The denial is still at the **GRANT** level, not the policy level: Postgres checks
privileges before RLS, so RLS is never consulted and cannot be observed working.
That is the intended shape — the outer layer fires, and RLS sits behind it as the
backstop for the day a grant appears.

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

#### P2 extended, 2026-07-30: personal data that was not an identifier

Stripping surrogate keys left two other categories in the request.

**Fields nothing reasons over.** `renewal_date` is one person's account
anniversary; `portfolio_name` is user-authored free text and can contain a real
name. Neither is an identifier, so the original pass left both — and a check of
every consumer found none in `agents/`, `rules/` or `graph/`. The only code that
touches them writes them. They were pure disclosure, so `UNUSED_PERSONAL_KEYS`
now removes them.

`last_updated` on a balance was considered and deliberately kept: it is a
timestamp of user activity, but freshness is load-bearing here, and an answer
resting on a figure typed six months ago should be able to say so.

**Contact details inside free text.** The typed query is the one field that can
contain anything, and `strip_identifiers` cannot help — it filters keys, and this
is a value. `scrub_free_text` removes email addresses, Indian mobile numbers and
13–19 digit card or account numbers from the query, stored preferences, and
remembered past queries.

Two boundaries drawn deliberately, both of which matter more than the scrub
itself:

*It does not touch `rule_results`, `graph_results` or retrieved knowledge.*
Those carry the numbers a recommendation quotes verbatim. A regex substitution
over them could change a figure, and privacy work does not get to weaken the
arithmetic guarantee.

*It does not touch cities, dates, merchant names or amounts.* They are personal
data and they are also exactly what the question is about. Removing them would
produce a confidently wrong answer — a worse outcome than the disclosure the
scrub exists to prevent. `test_amounts_are_never_scrubbed` is the regression
guard, and it is the more important of the new tests.

Applied in the Planner as well as the Recommender: both send the typed query to
the provider, and a boundary defended in one of two places is not defended.

### P3 — FIXED 2026-07-30: a user could not delete their data

The only delete endpoint is `DELETE /portfolio/cards/{card_id}`. There is no
route to delete an account, a recommendation, the question history, or stored
preferences.

The database is ready for it — every table cascades from `users` — but nothing
can trigger it. Deletion today means someone with database access doing it by
hand.

For a broad user base this is not a nice-to-have: erasure is a statutory right
under India's DPDP Act and the GDPR, and the app already stores every question a
user has typed.

**Fixed.** `DELETE /api/v1/auth/me` deletes the `users` row; the existing
cascades take portfolios, cards, balances, loyalty accounts, preferences, goals,
recommendations, interaction events and notifications with it. One delete rather
than a list of tables — a list would be a second copy of the schema, and the
first thing to fall out of date when a table is added.

Scoped to the token's own `sub`, with no id parameter, so the route cannot be
aimed at another user even deliberately. Idempotent: deleting an already-absent
user is success, because someone who retries after a slow response should not be
told it failed.

**What it does NOT delete, stated in the UI rather than glossed:** the Supabase
auth identity in `auth.users`, which needs the service-role key this service
does not hold. Signing in again therefore creates a new, empty account. Claiming
"account deleted" would be a lie discovered at the next sign-in.

UI is on the Account page behind a disclosure and then behind typing your own
email — the cascade reaches further than people expect, and a one-click
irreversible action eventually gets clicked by accident. Deleting also signs you
out, since a live session pointing at deleted data would error on every page.

Tests assert the cascade across tables (not just the `users` row), that
re-syncing gives a *fresh* account rather than restoring anything, idempotency,
and that one user's deletion leaves another's cards intact.

### P4 — ADDRESSED 2026-07-30: every question was stored indefinitely, with nothing a user could do

`recommendations.query` holds the raw text of every question, and
`interaction_events.payload_json` holds event payloads. There is no TTL, no
anonymisation, no archival policy.

That is a deliberate product feature (History exists because of it), so this is
not a bug — but "forever" is a decision that has not been made explicitly, and
it compounds P3: the data cannot be removed by the person who created it.

**Addressed, and the fix was P3.** "Kept indefinitely" only reads as a problem
while the user has no way out. Now that `DELETE /auth/me` exists, the honest
statement is *"kept until you delete them"* — and History says exactly that,
with a link to Account. Stating it was only worth doing because the second half
became true.

**Still open, and it is a product decision, not an engineering one:** whether to
add automatic expiry (say, purge recommendations older than N months), and
whether to allow deleting a single answer rather than the whole account. Neither
is required for honesty now that erasure exists; both are reasonable.

### P5 — FIXED 2026-07-30: no disclosure that data reaches a third-party model

There is no privacy policy, no terms, and no in-app statement that questions and
portfolio contents are sent to Google. A user cannot know their card holdings
leave the service, and cannot decline.

**Fixed** with a factual line under the Ask box (`DataNotice` in
`components/shell.tsx`):

> Answers are written by the Gemini model, run by Google. Your question, the
> cards and balances you have recorded, and your preferences are sent to it;
> account identifiers are removed first, along with any email, phone or card
> number found in what you typed. Answers are saved to your History until you
> delete them.

Placed at the point of sending rather than in a policy page nobody opens, and
worded factually rather than reassuringly — it names the recipient and the
contents and does not editorialise about safety. It states the removals (P2)
because those are the part a reader cannot verify for themselves.

**Reworded 2026-07-30.** The first version opened "Answering uses Google
Gemini", which described the destination without the reason and read as a
warning about a company rather than an explanation of how the feature works —
answering a question the user had not asked. It now leads with the model and
names Google second. Dropping Google entirely was rejected: the operator of the
model is the substance of the disclosure, and omitting it would make the notice
false by omission.

**Still needed before the URL is shared publicly (D-2):** an actual privacy
policy, and a decision on whether Gemini's free tier permits training on
submitted content. If it does, this notice is necessary but not sufficient.

### P6 — ACCEPTED 2026-07-30, with a guard: search text travels in URL query strings

`GET /api/v1/knowledge/search?q=...` puts the search text in the URL, which
lands in Render's access logs and any intermediary, whereas `POST /chat` keeps
the question in the body.

Today `q` is generated by the app on the Redeem page, so no user text is
exposed. But the endpoint accepts arbitrary text and was user-facing until the
2026-07-30 restructure, so this is a latent exposure rather than a live one.

**Deliberately not changed to POST.** GET is the correct verb for a read, and
moving it would trade real REST semantics for a hypothetical: no user-typed text
reaches this endpoint. Changing a contract to pre-empt a feature that does not
exist is the kind of speculative work this backlog has already been trimmed of
once.

**Guarded instead**, with the condition that flips the decision written at the
call site: if a user-facing search box is ever added, move to POST *first*. The
comment is in `backend/api/knowledge.py` where someone adding that box will
read it, not only in this document.

**Second guard added 2026-07-30: `docs/LOGGING_POLICY.md`.** The URL was never
really the exposure — the exposure was the URL *reaching a log*. This service
logs nothing at all today, which is why the policy could be written as a
decision rather than a retrofit: it requires the route template, never the
populated URL, so `?q=` cannot land in a log even if the endpoint stays a GET
forever.

That is the durable half of the fix. The call-site guard defends the endpoint;
the policy defends every endpoint, including ones not yet written. Two
independent defences, because either alone is a single point of failure — and
the policy's real value is that it exists *before* the first `logger.info`, when
changing the default is free.

### P7 — ACCEPTED 2026-07-30 as a stated decision: session token in `localStorage`

Supabase's default. Readable by any script on the origin, so an XSS becomes a
full account takeover, and the token survives tab close.

Materially mitigated: there are **no third-party scripts at all**, so the
injection surface is the app's own code rather than any vendor's.

**Accepted rather than fixed**, and recorded as a decision so it stops being an
unexamined default. Moving to cookie-based sessions means adopting
`@supabase/ssr` and reworking the auth path in `Shell`, `lib/supabase.ts` and
every `api.ts` call — a real change to the thing that currently works, to defend
against an XSS in code we control and can review.

**The condition that should change this decision:** the first third-party script
added to the frontend — an analytics tag, a chat widget, an error reporter. At
that point the injection surface stops being ours, and `localStorage` stops
being defensible.

**Mitigated 2026-07-30 with a Content Security Policy** (`frontend/next.config.mjs`),
which was the free option in every sense — no vendor, no auth rework, no risk to
the working sign-in path. All three of the alternatives considered were free in
money; what they cost was rework of the one component whose failure logs
everybody out.

What the CSP does, stated precisely, because a security header is easy to
oversell:

- It does **not** stop injected script from reading the token. `script-src`
  keeps `'unsafe-inline'` — the App Router emits inline hydration scripts, and
  removing them needs per-request nonces from middleware, which forces dynamic
  rendering on every page.
- It **does** stop the token being sent anywhere. `connect-src` allows only
  Supabase and our own API; `form-action` and `base-uri` close the usual ways
  round that. A credential that can be read but not exfiltrated is a much
  smaller problem, and this holds despite `'unsafe-inline'`.
- It **does** enforce the reversal condition above. "The first third-party
  script" was a sentence in this document, which is a thing people do not read.
  As a policy it fails visibly in the browser instead.

Shipped alongside it: `X-Content-Type-Options`, `X-Frame-Options: DENY`,
`frame-ancestors 'none'` (this app shows one person's finances; clickjacking it
into an invisible frame is the cheapest attack available), a referrer policy so
paths naming a section of someone's finances do not leak cross-origin, and a
permissions policy denying camera, microphone, geolocation and payment.

`connect-src` is derived from `NEXT_PUBLIC_SUPABASE_URL` and
`NEXT_PUBLIC_API_URL` rather than hard-coded, so the policy cannot drift from
the configuration it is meant to describe.

The original decision stands: this is a mitigation, not the fix. Cookie-based
sessions remain the answer if the reversal condition ever triggers.

### P8 — FIXED 2026-07-30: `x-request-id` was client-controllable

`request.headers.get("x-request-id") or str(uuid.uuid4())` — a caller could set
any string, which is echoed back in every response envelope and would be written
to any log line the service ever gains. That allows newlines, control characters
and another user's identifier into our own records.

**Fixed** in `_accepted_request_id`: the value is parsed as a UUID, and replaced
with a fresh one if it is not. Honouring a *valid* supplied id is kept
deliberately — that is what lets a client correlate its logs with ours.

Invalid input is replaced rather than rejected: the request itself is fine, only
the label was unusable, and a 400 would break clients for no gain. Cover in
`tests/unit/test_request_id_is_validated.py`, including newline and header
injection shapes, and normalisation so two log lines cannot disagree about one
request's name.

---

## Recommended order

1. ~~**P1**~~ — **done, clean.** No anon access. Optional follow-up: enable RLS
   as a second layer.
2. ~~**P2**~~ — **done.** Identifiers stripped at the digest boundary.
3. **P3** — account and data deletion. Needed before a broad user base, and the
   schema already supports it.
4. ~~**P5**~~ — **done.** Factual notice under the Ask box. A privacy policy is
   still needed before the URL is shared (D-2).
5. ~~**P4**~~ — **addressed** by P3: "kept until you delete them", said on
   History. Automatic expiry and single-answer deletion remain open product
   decisions.
6. ~~**P8**~~ — **done.** `x-request-id` validated as a UUID.
7. ~~**P6, P7**~~ — **accepted as stated decisions**, each with the condition
   written down that should reverse it: a user-facing search box (P6), or the
   first third-party script (P7). Both then gained a second, enforcing defence
   on 2026-07-30, so neither rests on someone remembering to read this file:
   `docs/LOGGING_POLICY.md` keeps query strings out of logs (P6), and a Content
   Security Policy makes the token unexfiltratable and breaks the build's
   behaviour visibly if a third-party script is ever added (P7).
8. ~~**P2 extended**~~ — **done 2026-07-30.** `renewal_date` and
   `portfolio_name` dropped (nothing reasons over either), and contact and
   account numbers scrubbed from the typed query, preferences and remembered
   queries — in the Planner as well as the Recommender.

## Not examined

- Supabase's own retention and regional storage (where the Postgres instance
  physically lives, and what Supabase logs).
- Google's retention for Gemini free-tier API traffic. **Worth checking
  specifically:** free tiers of LLM APIs sometimes permit training on submitted
  content, which would be a materially different privacy posture from the paid
  tier.
- Render and Vercel log retention windows.
- Whether `interaction_events` payloads contain anything beyond ids and status.

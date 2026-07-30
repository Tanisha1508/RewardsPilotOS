# Logging policy

**Written 2026-07-30, before this system logs anything of its own.** That is the
point.

There is no `logging` or `logger` call anywhere in `backend/`, `agents/`,
`tools/`, `rules/` or `graph/` — only `print()` in CLI scripts.

**One correction, made the same day.** "Nothing is logged" was true of code we
wrote and false of the server underneath it. Uvicorn installs a `uvicorn.access`
logger that is **on by default** and writes the full URL:

```
127.0.0.1:0 - "GET /api/v1/knowledge/search?q=edge+miles HTTP/1.1" 200
```

Render captures stdout, so `?q=` has been landing in a log the entire time,
written by a logger nobody in this repo configured. That is the shape of the
problem this policy exists for: the dangerous logging is the logging you did not
write. It is now scrubbed in code — see below.

The rest of the risk is still ahead. A product aimed at a broad user base needs
observability, and every default is generous: hosting platforms capture stdout
and headers, and APM SDKs capture request bodies unless told otherwise.
Retrofitting redaction onto a system already logging is expensive and never
quite complete — the leaked field is always the one nobody thought of.

Deciding now, while application logging is still a blank page, costs nothing.

## Enforced in code

`infra/logging/access_log.py`, installed by `create_app()`:

- **query strings are removed** from every access line —
  `/api/v1/knowledge/search?q=...` becomes `/api/v1/knowledge/search`
- **UUIDs in paths collapse to `{id}`**, restoring the route template the rule
  below asks for, since the server logs the URL that arrived rather than the
  route that matched it
- method, status and route survive: this suppresses the contents of a line,
  never the line. Access logs are how you find out the service is being scanned.

Installed in `create_app()` rather than as a `uvicorn` flag on purpose — the
start command lives in Render's dashboard, not in this repository, and a defence
that depends on a setting in a web console someone else can edit is not a
defence. Cover in `tests/unit/test_access_log_scrubbing.py`, asserted through the
real `logging` machinery: a correct helper proves nothing if the filter is never
attached or stops matching uvicorn's record shape after an upgrade.

Everything below is the policy that filter enforces, and the rule for the
application logging that does not exist yet.

---

## The rule

**Log identifiers and outcomes. Never log content.**

A log line should let you find *which request* went wrong and *what class* of
thing happened. It should never let you read what a person asked, hold, or
prefer.

If a log line would tell you something about a *particular user's finances*, it
is content.

This is a rule about **logs**, not about what the product may store. Questions
and answers are already persisted in `recommendations`, deliberately — see
"But evals need the queries and the outputs" below. The rule says a *second*,
ungoverned copy must not exist beside the governed one.

---

## Never log

Not "redact carefully" — do not write these at all.

| Category | Examples |
|---|---|
| **User-authored text** | the chat `query`, preference values, goal descriptions, card names a user typed |
| **Financial position** | balances, points, computed earn figures, cap headroom, transfer amounts |
| **Portfolio composition** | which cards a person holds, their issuers, their annual fees |
| **Request/response bodies** | in full or in part, on any route |
| **Query strings** | see the URL rule below |
| **Credentials** | tokens, `Authorization` headers, cookies, API keys, `DATABASE_URL` |
| **LLM payloads** | the state digest, prompts, or model responses. This is the whole portfolio in one string |
| **Direct identifiers** | email, name. `user_id` — see below |

## Safe to log

| Category | Examples |
|---|---|
| `request_id` | validated as a UUID (privacy audit P8) |
| HTTP method, **route template** | `POST /api/v1/chat` — the pattern, not the populated path |
| Status code, duration | |
| Exception **type** and stack trace | never the exception *message*, which can carry SQL and connection strings — the existing handler already refuses to return those (`backend/api/responses.py`) |
| Tool name and status | `CompareCards → success`, `SearchKnowledge → failed`. Not the arguments |
| Counts | "3 cards compared", "5 chunks retrieved" |
| Deploy/version markers | |

## "But evals need the queries and the outputs"

They do, and this policy does not stand in the way — because **the database is
not a log**, and the eval data is already in the database.

```
recommendations: rec_id, user_id, query, recommendation_json,
                 confidence, citations_json, status, created_at
```

Every question and every answer is already persisted, with the confidence and
citations attached. An eval harness reads that table. Nothing about "never log
the query" removes a single row.

The distinction is not pedantry — the two stores have opposite properties:

| | `recommendations` row | log line |
|---|---|---|
| Access control | RLS, scoped to the owner | whoever can read the log stream |
| Deletion | `ON DELETE CASCADE` from `users` | platform retention, not ours to erase |
| Covered by the notice | yes, "saved to your History until you delete them" | no |
| Location known | the Supabase instance | wherever the vendor ships it |

The last two rows are why writing the query to a log is a real loss and not
bookkeeping. `DELETE /auth/me` erases a person's questions from the database. It
cannot reach into yesterday's log stream. A logged query is a copy that survives
the deletion we promise — which turns a working privacy guarantee into a false
one. That is the whole argument.

### What logs *should* carry for evals

A large amount of eval signal is content-free, and this is the half that belongs
in logs, because it is aggregate by nature:

- confidence distribution, and how often the deterministic ceiling bound it down
- recommendation validation rejections, and how often the single retry rescued
  them
- tool error rates by tool name
- citation counts per answer; answers produced with zero citations
- how often a value came back `unverified` and the answer had to say "unknown"
- latency by stage

None of that names a person or a portfolio, all of it tracks whether quality is
moving, and it is the natural input to the continuous-improvement half of this
product. Content-level evaluation reads the table; trend-level evaluation reads
these.

### Before production traffic becomes an eval set

One thing to settle first, and it is a consent question, not a technical one.

Today's evals run on a golden set in `evaluation/datasets/`, written by us. The
moment real users' questions are pulled into an eval corpus, the purpose has
changed: answering someone's question is one thing, and keeping it to improve
the product is another. The notice currently says answers are "saved to your
History until you delete them" — which is true of storage, and says nothing
about product improvement. Reusing the data for that without saying so would
make the notice quietly untrue, which is the failure mode this whole project is
organised against.

Three workable answers, in increasing cost:

1. **Own accounts only.** Build eval cases from your own usage. Free, honest,
   no consent question, and enough to get started.
2. **Extend the notice and offer a choice.** Say plainly that questions may be
   used to improve answer quality, with an opt-out in Settings.
3. **De-identify into a curated set.** A human rewrites real failures into
   golden cases that carry the *shape* of the problem and none of the person.
   This is what `evaluation/datasets/` already is, and it is the only form that
   survives account deletion by construction.

Option 3 is also the most useful: an eval set of raw production queries is
mostly duplicates, and a curated regression case is worth more than a hundred
of them.

## URLs

**Log the route template, never the populated URL.**

`GET /api/v1/knowledge/search` — not `?q=...`.
`DELETE /api/v1/goals/{goal_id}` — not the id.

This is what makes privacy audit P6 safe to leave as a GET. The endpoint takes
`q` in the query string, which is correct REST for a read and harmless while
every caller generates the value. The exposure was never the URL; it was the URL
*reaching a log*. This rule closes it at the logging layer, so the API can stay
correct.

Still true, and written at the call site in `backend/api/knowledge.py`: **if a
user-facing search box is ever added, move that endpoint to POST first.** Two
independent defences, because either one alone is a single point of failure.

## `user_id`

Permitted **only** where an operator genuinely needs to act on one user's data —
a support request, an abuse investigation — and never alongside content.

`user_id=abc123 → 500 on POST /api/v1/chat` is fine.
`user_id=abc123 asked "best card for my Delhi trip"` is not, and the second half
is the problem, not the first.

Prefer `request_id` where it suffices. It is unlinkable, and it is what the
error envelope already returns to the user, so it is the id a support
conversation will actually start from.

## Retention

Whatever the platform's default is, know it before relying on it. Render and
Vercel both retain logs on their own schedule, and a log you cannot delete is a
copy of your data you do not control — which matters more once account deletion
exists (`DELETE /auth/me`): erasing a user's rows does not erase them from logs
written yesterday. That is another reason the answer is not to write them.

## When adding an observability tool

Sentry, an APM, a log aggregator — all of them capture more than you asked by
default. Before enabling any of them:

1. Turn **off** request-body capture.
2. Turn **off** query-string capture, or scrub it.
3. Turn **off** automatic PII association (`send_default_pii` and equivalents).
4. Check what the SDK attaches to breadcrumbs — that is where request payloads
   usually reappear after you have disabled the obvious setting.
5. Add the vendor to the privacy notice. A processor that receives error context
   is a recipient of user data, and the notice currently names only Gemini.

## Reviewing a change

One question, applied to every new log line:

> If this line appeared in a screenshot of a support ticket, would it tell a
> stranger anything about that person's money?

If yes, log the `request_id` and look the rest up in the database, where it is
already governed by access control and by deletion.

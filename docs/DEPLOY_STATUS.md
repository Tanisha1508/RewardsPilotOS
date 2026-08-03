# Deployment record — current as of 2026-08-03

What is deployed, what was verified, and the problems worth writing down. The
day-to-day operational log (account handling, credential rotation, the session
resume list) is kept out of this public repo — this file is the record, not the
working notes.

## What is live

| | |
|---|---|
| **Frontend** | https://rewards-pilot-os.vercel.app — Vercel, root directory `frontend/` |
| **Backend** | https://rewardspilotos.onrender.com — Render free tier, Docker runtime |
| **Database / auth** | Supabase (Postgres + Auth), 16 tables, migrations current |
| **Vector store** | ChromaDB on the instance's disk, ingested on first boot |

Verified end to end through the browser, not only in tests: sign-in, a seeded
portfolio rendering on the dashboard, a chat answer with its numbers table and
freshness-dated sources, the transfer explorer, and feedback on an answer.

The canonical check is the ₹50,000 flight query, which must return
`axis_atlas 2500 (accelerated) > hdfc_infinia 1665 (base) > amex_plat_travel
1000 (base)` with citations attached and confidence high. It does.

## Four problems that cost real time

Kept because the reasoning is the useful part.

**The database URL that works from home does not work from Render.** Supabase's
direct connection is IPv6-only and Render cannot reach it. The fix is the
**session pooler** URL (IPv4) with `?sslmode=require`. Do not "simplify" this
back to the direct URL. Migrations are the exception — run those from a local
machine against the direct URL, never through the transaction pooler.

**Citations came back empty while the answer still computed.** Graceful
degradation worked exactly as designed — confidence was capped at medium and
said why — which is also what made it easy to miss. The cause was file
permissions: `WORKDIR` is created by root, `COPY --chown` only chowns contents,
and `.dockerignore` excluded `data/`, so the runtime user could not create the
Chroma persist directory. One `RUN mkdir -p … && chown -R` fixed it.

**CORS failed on a trailing slash** in the backend's `FRONTEND_URL`. The classic
one. The origin must be exact: https, no trailing slash.

**Cold starts made the app look broken.** A free instance sleeps, and the first
visit paid 36 seconds on `/health` plus around 85 more for the lazy Chroma
re-ingest. A scheduled ping (Supabase Cron, `infra/monitoring/keepalive_pg_cron.sql`)
took `/health` to 0.9 s measured after 20 minutes idle. The job window is
01:00–17:59 UTC, so the first visit before ~06:30 IST still pays one wake-up —
deliberate, because round-the-clock is ~744 h against Render's 750 h/month.

| | Before | After |
|---|---|---|
| `/health` after 20 min idle | 36.0 s | 0.9 s |

## Deployment constraints worth knowing

- **Memory.** The free instance is 512 MB and the measured peak on the
  chat-plus-ingest path is 432 MB. This is why the image uses fastembed rather
  than torch — torch would not have fit. Treat any embedding-library change as a
  memory decision.
- **Disk is ephemeral.** Chroma re-ingests on boot; see
  [`KNOWN_LIMITATIONS.md`](KNOWN_LIMITATIONS.md) 28.
- **Quota.** The LLM free tier is shared across all users, and there is no
  per-key protection beyond the per-user daily question limit.
- **Environment.** Values live in the platform stores, never in this repo.
  Render needs `DATABASE_URL` (session pooler), `SUPABASE_URL`,
  `SUPABASE_ANON_KEY`, `GEMINI_API_KEY`, `GROQ_API_KEY`, `FRONTEND_URL`,
  `ENV=production`. `CHROMA_PERSIST_DIR` is baked into the image. Vercel needs
  `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`,
  `NEXT_PUBLIC_BACKEND_URL`.

## Two process rules learned the hard way

- **A corpus change is a behaviour change.** Run
  `python -m evaluation.metrics.report` after touching what the system can
  retrieve, not only after touching code. Excluding a set of fixture documents
  silently broke two eval suites.
- **A benchmark that cannot see a defect is not evidence the defect is absent.**
  A bug where comparison questions returned evidence about a single card was
  invisible to the retrieval eval, because that eval deduplicates by document.

## Where the work stands

The backlog is [`BACKLOG.md`](BACKLOG.md); open data verification is
[`VERIFICATION_QUEUE.md`](VERIFICATION_QUEUE.md); what the system still gets
wrong is [`KNOWN_LIMITATIONS.md`](KNOWN_LIMITATIONS.md).

The binding constraint is not code — it is corpus coverage. Three cards answer
properly and seven refuse, correctly but unhelpfully, and `promotions` and
`issuer_policies` hold nothing for real issuers. That is data to gather.

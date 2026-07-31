# Deploy status — D5, as of 2026-07-23 ~22:25 IST

Written mid-deploy as the working-session window closed, so whoever resumes
(future-you or an agent) has the exact state, not a reconstruction.

## What is LIVE and verified working

**Backend: https://rewardspilotos.onrender.com** — Render free tier, Docker
runtime, built from commit `a280f9b` (the fastembed image).

Verified live, in order, on 2026-07-23 evening IST:

| Check | Result |
|---|---|
| `GET /api/v1/health` | `status: ok`, **`database: ok`** via the Supabase **session pooler** (IPv4 — direct is IPv6-only and unreachable from Render; do not "simplify" back to the direct URL) |
| Unauthenticated `POST /api/v1/chat` | **401** — JWT middleware enforcing |
| Supabase signup API | **OPEN — issues instant session tokens** (see security to-dos) |
| Seeded portfolio via live CRUD | 3 P1 cards added through real HTTP endpoints |
| Authenticated `/chat`, ₹50,000 flight query | **HTTP 200 in 63 s, computed**: axis_atlas **2500** (accelerated) > hdfc_infinia 1665 (base) > amex_plat_travel 1000 (base) — the ADR-010 canonical query answered correctly in production, no OOM (fastembed image; torch would not have fit) |
| `/chat` citations | **CLOSED 2026-07-23 ~23:10 IST** — after the `de47dca` chown fix deployed (manual deploy; Auto-Deploy was broken by a missing GitHub App install, since fixed): **2 citations** with freshness dates, confidence **high** (weakest source 0.9, no tool failure), same correct computation, first-boot ingest wrote Chroma to disk with no OOM (2m16s one-time cost) |

## RESOLVED: citations empty (SearchKnowledge PermissionError) — fixed & verified live

- **Symptom:** `SearchKnowledge` fails with `PermissionError`; recommendation
  still computes (graceful degradation worked as designed); confidence honestly
  capped at medium naming the failure; `citations: []`;
  `/api/v1/knowledge/search` returns a bare 500.
- **Root cause (diagnosed, confirmed by code):** `WORKDIR /home/user/app` is
  created by root; `COPY --chown` only chowns contents; `.dockerignore`
  excludes `data/`; so at runtime uid 1000 cannot `mkdir data/` for the Chroma
  persist dir.
- **Fix: ALREADY COMMITTED AND PUSHED** — commit `de47dca` adds one build-time
  `RUN mkdir -p /home/user/app/data/embeddings && chown -R user:user ...`.
- **Where it is stuck:** Render never served the new image. ~35 min of polling
  after the push, the old image still answers. The change itself cannot
  plausibly fail the build (the same image built successfully before it), so
  the likely cause is **Auto-Deploy is OFF on the Render service** (pushes
  ignored; the only deploy was the one at service creation). Alternative: a
  failed/queued build — visible only in the Render dashboard.

### Exact resume steps (10 minutes total)

1. Render dashboard → service → **Events**. If no deploy for `de47dca`:
   **Manual Deploy → Deploy latest commit** (and Settings → enable
   Auto-Deploy). If a deploy failed: read the build log tail.
2. Wait for the build (5–10 min). The service keeps serving during it.
3. Verify, in order (a login token is needed — create a user via the Supabase
   signup API with the anon key, or reuse a real demo account):
   - `GET /api/v1/knowledge/search?q=flight+rewards&k=3` (authenticated) →
     expect **200 with chunks** (first call after boot is slow: lazy corpus
     ingest — that is the ephemeral-disk design, KNOWN_LIMITATIONS 28).
   - `POST /api/v1/chat` with the flight query → expect **citations > 0** and
     the confidence reason no longer mentioning a tool failure.
4. Memory sanity: Render dashboard → Metrics. The measured local peak is
   432 MB on the chat+ingest path; the free instance is 512 MB. Surviving the
   ingest (no 502/restart) is the pass signal.

## COMPLETE — frontend deployed and full-stack gate passed (2026-07-23 ~23:45 IST)

**Frontend: https://rewards-pilot-os.vercel.app** (Vercel, Root Directory
`frontend/`). CORS verified from outside (preflight 200, exact-origin echo —
after fixing a trailing slash in Render's `FRONTEND_URL`, the classic break).
Full gate driven through the real browser UI:

- Signup -> session -> dashboard redirect (demo account
  `demo@rewardspilotos.test`; password held by the owner, not recorded here).
- Dashboard: 3 seeded P1 cards + balances render.
- Chat, Rs 50,000 flight: "Use your Axis Bank Atlas card" at HIGH confidence,
  NUMBERS USED table (three CompareCards rows), SOURCES panel with three
  freshness-dated official links, Accept/Save/Reject feedback.
- Transfer explorer: verified partner data with ratios, caps, dates, sources.

Frontend UX note — FIXED same night (commit `405b133`): Shell now guards all
protected pages client-side (the Supabase session lives in localStorage, so a
server middleware cannot see it) — no session redirects to /login, SIGNED_OUT
events redirect too, and a signed-out direct hit on /dashboard was verified
live to bounce. Data was never exposed pre-guard (api.ts + backend 401s).

## Superseded planning section (kept for context)

- **Frontend → Vercel.** Import repo, **Root Directory = `frontend/`**, env
  vars: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`,
  `NEXT_PUBLIC_BACKEND_URL=https://rewardspilotos.onrender.com`.
- **CORS wiring (after Vercel exists):** set `FRONTEND_URL=<exact Vercel
  origin, https, no trailing slash>` in Render env → redeploy/restart backend.
  Until then, browser calls from Vercel will fail CORS by design.
- **Frontend gate:** live login → chat from the UI → computed recommendation
  with sources; transfer explorer; dashboard.
- **Demo account:** create one with known credentials via the deployed login
  page, seed it with `infra/scripts/seed_demo_portfolio.py`
  (`BACKEND_URL=... DEMO_ACCESS_TOKEN=...`).

## Security to-dos before sharing the URL publicly

1. **Disable open signups** in Supabase (Auth settings) once your own demo
   account exists — signups currently issue instant tokens to anyone, and any
   authenticated user can burn the shared 20/day Gemini free-tier quota
   (no per-user rate limiting exists).
2. **Delete the throwaway verification account**
   `deploygate.<epoch>@rewardspilotos.test` (Supabase → Auth → Users). Its
   password was never stored; nobody can log into it. Optionally clean its
   orphaned app rows (users/portfolio/cards) in Postgres.
3. **Rotate the HF token** that passed through the working transcript
   (`hf_…`, `.env` line 15) — unused by the deployed app. The Groq key was
   already rotated (old one verified revoked, 401).

## Environment reference (no values here — values live in platform stores)

- **Render env:** `DATABASE_URL` (session pooler + `?sslmode=require`),
  `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `GEMINI_API_KEY`, `GROQ_API_KEY`,
  `ENV=production`. `FRONTEND_URL` pending the Vercel step.
  `CHROMA_PERSIST_DIR` is baked into the image.
- **Migrations:** run from a local machine against the **direct** Supabase URL
  (IPv6; works from home networks) — never through the transaction pooler.
  Schema is current: 16 public tables, verified through the pooler.

## ✅ COLD STARTS ARE GONE — 2026-07-31

The keepalive now runs as a Supabase Cron job (`infra/monitoring/keepalive_pg_cron.sql`,
created through Supabase → Integrations → Cron rather than by SQL, because the
SQL editor's role has no rights on the `cron` schema).

Measured, after 20 minutes of deliberately not touching the service:

| | Before | After |
|---|---|---|
| `/health` | **36.0 s** | **0.9 s** |

That is the "dashboard takes a minute" complaint closed, and it also removes the
~85 s first-chat-after-restart case (the lazy Chroma re-ingest, KL 28) that was
blocking the section below.

Still true: the job window is 01:00–17:59 UTC (06:30–23:29 IST), so the first
visit before ~6:30am still pays one wake-up. Deliberate — round-the-clock is
~744 h against Render's 750 h/month free allowance.

**Next:** re-run the preview test now that nothing is cold. If chat holds at
~29 s the branch merges unchanged.

## ✅ ALL OF 2026-07-31'S WORK IS LIVE AND VERIFIED

The three sections that used to sit here — "phase 1 blocked", "verified on the
preview", "before promoting the next deploy" — described a branch that has since
merged. Removed rather than left to be re-read as current, which is the failure
mode of a status file nobody prunes.

**Verified on production at session end:** `/health` 200 in 1.4 s, the guarded
routes 401, `/privacy` 200. Working tree clean, everything pushed.

### Shipped today

| | |
|---|---|
| **Privacy (P1–P8)** | Closed. PII scrubbed before the model, notice reworded, query strings kept out of access logs, same-origin API, Content Security Policy. `/privacy` page live under Settings — **no consent gate**, an owner decision to revisit when signups open |
| **A2** | 5 questions per user per day, 429 with a message that says why and when it lifts |
| **A3** | Wiring sweep — `docs/WIRING_SWEEP.md`. Four database tables with no reader or writer, recorded not deleted |
| **A4** | Numbers table. Fixed a hidden `points` field, then found the rate display was *misleading* — "Rate 2" vs "Rate 5" across different denominators |
| **A5** | One responsive layout. Also fixed sideways scrolling on desktop |
| **A6** | 33 free scenario checks against production, 0 failures |
| **A8** | Cold starts gone. `/health` 36.0 s → 0.9 s via Supabase Cron |
| **A9** | Per-answer permalinks |
| **A10** | Retrieval filters wired, after fixing two landmines in the module |
| **A11** | Comparison questions no longer return evidence about one card |
| **B1, B2** | Reward-currency validation; unrecognised-category warning |
| **B3** | `StorePreference` kept, with a `source` column. Migration `preferences_source` **applied to production** |

### Data-integrity bugs found and fixed (KL 34–37)

All four were the same shape — something untrue reaching the answer path from a
place the guards did not check:

1. **Groq could not satisfy the output contract** — fixed by handing the model
   finished lists instead of making it derive them. Gemini improved too.
2. **Invented issuers were citable.** Ten fixture documents were retrievable by
   ordinary questions.
3. **Excluding those fixtures broke two eval suites** and nobody re-ran them.
4. **`GetOpportunities` served invented promotions** into `grounded_text` — the
   very text the traceability check trusts.

### Eval baseline at session end

```
Retrieval (fixture benchmark)  recall@5 1.000   MRR 0.586
Retrieval (real corpus, NEW)   recall@5 0.987   MRR 0.926   top-1 0.885
Rules                          100% (25/25)
Graph                          100% (10/10)
End-to-end                     100% (10/10)
668 tests passing
```

**The real-corpus retrieval eval is new and is the one to watch** — the older
benchmark is 17/24 questions about invented banks, so a good score there says
ranking works and nothing about real users.

### Two process rules learned the hard way today

- **A corpus change is a behaviour change.** Run
  `python -m evaluation.metrics.report` after touching what the system can
  retrieve, not only after touching code.
- **A benchmark that cannot see a defect is not evidence the defect is absent.**
  A11 was invisible to the eval because it deduplicates by document.


## NEXT SESSION — start here (recorded 2026-07-31, session end)

Everything below is *not started*. `docs/BACKLOG.md` is the full list; this is
the short version of what to pick up and why.

### Yours, and I cannot do them

1. **Delete the leftover test accounts** — `d3.smoke@`, `d4.demo@`,
   `demo@rewardspilotos.test`, and any `deploygate.*` still present.
2. **Rotate the Hugging Face token**, and remove the Google OAuth secret from
   `.env`.
3. **Open the app on a real phone once.** A5 shipped a responsive layout and I
   could verify no content is too wide, but not that the breakpoints fire — the
   browser tool reports a resize and the viewport never changes. If the tabs sit
   on their own row under the logo, it works.

### The decision that unblocks the most

**Signups: open or closed?** The things that were blocking it are done — per-user
limits, a privacy page, working account deletion. If they open, two follow-ups
come back on the table: the consent gate (deliberately not built for MVP) and
whether a page someone *could* have read is enough given section 3 of the policy.

### The real ceiling, and it is not code

**Corpus coverage.** Three cards answer properly; seven refuse — correctly, but a
user with an Axis Magnus gets nothing useful. Coverage per card:

```
                    rules  transfers  benefits  promos  policies
amex_plat_travel     yes      yes       yes       —        —
hdfc_infinia         yes      yes        —        —        —
axis_atlas           yes      yes        —        —        —
7 other cards        yes       —         —        —        —
```

`promotions` and `issuer_policies` are **empty** for real issuers. That is why
"any transfer bonuses right now?" and "when do my points expire?" cannot be
answered, and it is data to gather rather than a bug to fix.

**Three of the four data-integrity bugs found today were fake data leaking
toward users.** The fixture scaffolding has outlived its usefulness; filling the
corpus with verified sources is the work that changes what the product can say.

### Smaller, queued

- **A7** — Atlas transfer partner ratios. Parked; needs the Axis Miles Transfer
  T&C document, which I cannot reach.
- **D-1 loyalty** — dead on both sides, so it is a build, not a wiring job.
- **D-3 multi-turn Ask** — now cheaper: the `preferences.source` column it needs
  landed with B3.
- **The two remaining unwired modules** (`agents/memory/behavior.py`,
  `agents/graph/behavior.py`) — ten lines each, documented in
  `docs/WIRING_SWEEP.md`, deliberately not deleted because BUILD_SPEC names them.

### Date-gated

- **A7 Amex expiry test** on/after **2026-08-01** — the real proof the month fix
  worked.
- **Smoke s01** next Mon/Thu.

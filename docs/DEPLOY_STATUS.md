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

## ❌ PHASE 1 IS BLOCKED — measured on the preview 2026-07-30

**Do not merge `privacy/p6-p7-same-origin` yet.** Everything about the rewrite
works; the thing it exposed does not.

Tested side by side, same backend, same query, same minutes:

| Path | Result |
|---|---|
| Preview → Vercel rewrite → Render | **502 after ~90 s** |
| Production → Render directly | **Succeeded at ~85 s**, correct answer |

So the proxy imposes a ceiling that chat currently sits right underneath, and
occasionally above. `experimental.proxyTimeout` did not save it — whatever cuts
the request on Vercel is not the setting measured locally.

**But the proxy is not the real problem. Chat takes ~85 seconds.** That is the
finding that matters, and it is independent of any of this work: the core
feature of the product takes a minute and a half against a warm backend. The
rewrite did not cause it, it just removed the slack that was hiding it.

So the order of work is now:

1. **Find out why chat takes 85 s warm** and fix it. Suspects, cheapest first:
   the Planner and Recommender are two sequential Gemini calls, each with a
   retry; retrieval runs against Chroma on a free Render instance with very
   little CPU; and `complete_with_retry` may be backing off against a Gemini
   free-tier rate limit (20 requests/day shared) rather than failing fast.
2. **Then** re-run this preview test. With chat at a sane latency the proxy
   ceiling stops being reachable and phase 1 merges unchanged.
3. **Then** phase 2, which needs the latency answer anyway because a route
   handler inherits a stricter execution limit than a rewrite.

Everything else on the branch is verified and safe — see below.

## ✅ VERIFIED ON THE PREVIEW (2026-07-30)

Confirmed live, signed in, on `rewards-pilot-melvcn1a2-…vercel.app`:

- **Same-origin routing.** Every API call goes to the preview origin;
  **zero requests to `onrender.com`**. `POST /api/v1/auth/sync`,
  `GET /api/v1/portfolio/cards`, `GET /api/v1/recommendations` all 200.
- **CORS preflight is gone.** Production still shows `OPTIONS /api/v1/chat`
  before every POST; the preview does not.
- **Google OAuth works on a preview URL**, once the owner added the wildcard to
  Supabase's Redirect URLs. `redirectTo` already sent `window.location.origin`,
  so no code change was needed — only the allow-list entry.
- **CSP is clean.** No violations in the console on any page.
- **The reworded privacy notice is live**, and the app's own error handling
  degraded honestly on the 502: "The server returned a non-JSON response
  (HTTP 502)" rather than a blank screen.
- **ADR-019 is working in production.** The successful answer carried the
  channel note verbatim — "because no booking channel was provided, these
  figures reflect base earn only" — with HDFC Infinia at 1665.0 points against
  1000.0 for the other two, medium confidence, and dated citations.

## ⚠️ BEFORE PROMOTING THE NEXT DEPLOY (added 2026-07-30)

Unpushed commits change how the browser reaches the backend. **Verify on a
Vercel preview URL before promoting to production** — one question cannot be
answered locally.

**What changed.** API calls are now relative (`/api/v1/...`) and forwarded to
Render by a rewrite in `frontend/next.config.mjs`, instead of the browser
calling `rewardspilotos.onrender.com` directly. A Content Security Policy also
ships, and it **fails closed** — a wrong origin blocks calls rather than
weakening anything.

**The open question: the proxy's timeout.** Measured locally, Next's rewrite
proxy aborts at **exactly 30s** and returns a 500, where a direct call to the
same slow backend succeeded at 45s. `experimental.proxyTimeout: 120_000` fixes
it on a self-hosted `next start` — verified, 45s request returns 200.

**Whether Vercel honours `proxyTimeout` for external rewrites is unverified.**
Vercel proxies these through its own routing layer, which may impose its own
gateway limit regardless of this setting. This matters because a cold Render
dyno is ~15.6s *before* the model is called, and a restart that re-ingests the
Chroma corpus is ~120s (KNOWN_LIMITATIONS 28) — so chat is exactly the request
that would hit any such cap.

**The test, on the preview URL:**

1. Let Render idle >15 min so the next request pays a cold start.
2. Ask a question on the preview deployment's Ask tab.
3. A recommendation means the proxy tolerated the cold start. A 500 or a
   gateway error near 30s means it did not.

**If it fails**, the options in order of preference: keep the backend warm with
a scheduled ping so cold starts stop happening (also fixes the long-standing
"dashboard takes a minute" complaint); make chat asynchronous (POST returns a
job id, the client polls) which removes long requests entirely and is the right
shape for a slow model call on a free tier; or exclude `/api/v1/chat` from the
rewrite and leave that one route cross-origin, which is the cheapest and the
ugliest since it keeps CORS alive for the route that most needs phase 2.

Also confirm on the preview: **Google sign-in**, which is the flow that crosses
origins, and check the browser console for CSP violations.

## NEXT SESSION — pending items (recorded 2026-07-24, session end)

All code is committed and pushed (this commit is the tip). Live URLs:
frontend https://rewards-pilot-os.vercel.app, backend
https://rewardspilotos.onrender.com. Demo account
`demo@rewardspilotos.test` (password held by owner).

**Asked for explicitly by the owner:**
1. **UI polish round** — known items: a recommendations *history* page
   (`api.listRecommendations()` already exists in lib/api.ts; only the page is
   missing — the dashboard shows just a count and the chat page shows only the
   just-asked answer), plus whatever else a UI walkthrough surfaces.
2. **Execution/memory walkthrough** — owner-facing explanation of the full
   call chain from query to answer: POST /chat -> run_chat (acting_as) ->
   LangGraph planner (prompt + tool catalog) -> resolve_portfolio_args ->
   validate_plan -> run_tools (Rule/Graph/Knowledge tools) -> recommender
   (state digest, calibration ceiling, margin caveat) ->
   validate_recommendation -> persistence (recommendations +
   interaction_events) -> RecallMemory reading those events back on later
   queries. Goal: the owner can narrate every hop, e.g. in an interview.

**Security (still open):**
- Decide the signups policy: Google sign-in creates new users, so Supabase's
  "allow new signups" toggle gates it too — open (quota exposure; no per-user
  rate limiting exists) vs closed (only existing users can Google-sign-in).
- Delete the two `deploygate.*` throwaway accounts (Supabase -> Auth -> Users).
- Rotate the HF token (passed through a working transcript; unused by the app).
- Remove the Google OAuth client secret line from `.env` (the app never reads
  it; it belongs only in Supabase's provider config) and consider regenerating.
- Optionally rotate the demo account password (it passed through a transcript).

**Verification still pending:**
- Google sign-in end-to-end (dashboard config done per owner; the OAuth dance
  itself not yet exercised — owner clicks "Continue with Google").
- Live smoke suite `s02` (odd-day rotation or manual `SMOKE_GROUP=s02` after a
  quota reset). The Mon/Thu 08:20 UTC Action now has auto-deploy + secrets.
- Amex Reward Multiplier re-check on/after **2026-08-01** (VERIFICATION_QUEUE).

**Roadmap (unchanged):** opportunity engine (deferred half of D5), per-user
rate limiting, persistent Chroma decision (KNOWN_LIMITATIONS 28), P2 card
verification when sources arrive, KL items 9/11/12/18/27 awaiting product
decisions.

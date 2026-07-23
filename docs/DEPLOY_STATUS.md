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

Frontend UX note (known, deferred): pages render as shells without a login —
data is guarded client-side (api.ts refuses without a session) and by the
backend's 401s, so nothing leaks; a redirect-to-login guard is a small
fast-follow.

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

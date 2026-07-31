# Live testing log

Running record of testing against the **deployed** system. Not a substitute for
`pytest` (562 unit/integration tests) or the eval suites — those cover logic in
isolation. This covers what only the real deployment can show: real LLM
behaviour, real Postgres, real network, real browser, cold starts.

- **Frontend:** https://rewards-pilot-os.vercel.app
- **Backend:** https://rewardspilotos.onrender.com
- **How to use:** add a row per execution. Never edit a past row — append a new
  one. A test that passed on old code is evidence about that code, not this one.

## Status legend

`PASS` · `FAIL` · `BLOCKED` (cannot run, see Blockers) · `PARTIAL` (ran, some
checks unverifiable) · `NOT RUN`

---

## 1. Blockers — resolve before the next testing round

Ordered by what unblocks the most coverage.

**Status as of 2026-07-29:**

| | Blocker | Status |
|---|---|---|
| B0 | Planner invents `month` | **FIXED** — guard + prompt, `tests/agent/test_month_args.py` |
| B1 | No balance UI | **FIXED** — inline editor on `/cards` |
| B2 | No renewal-date field | **FIXED** — input added (state existed, input was never rendered) |
| B3 | No recommendations history | **FIXED** — `/recommendations`, linked as "History" |
| B4 | Gemini 20/day quota | **WON'T FIX** — a free-tier constraint, not a defect. Plan around it |
| B5 | Crawler secret missing | **FIXED** — secret added by owner; run 30387612637 green |
| B6 | Cold start / re-ingest | **MITIGATED** — keep-alive workflow + honest "waking the server" UI |
| B7 | Test account not seeded | **UNBLOCKED** — B1/B2 make it doable through the UI, no script or token needed |
| B8 | Open signups | **OPEN** — owner decision, gates public sharing only |

Preferences, goals and loyalty still have no UI. Left deliberately: unlike
balances they block no scenario in §3, and the API is testable directly. Logged
in B1 rather than fixed.

### B0. ★ The Planner invents `month` — fix before 2026-08-01

Highest priority, and time-boxed. Live answers carry `month: 2025-05` on queries
asked in 2026-07, because the planner prompt asks the model to "default to the
current month" and it has no idea what that is. From 2026-08-01 this makes Amex
Platinum Travel report **3000 accelerated points instead of 1000 base, with no
expiry note** — a 3x overstatement that ADR-012 was written to prevent.

Full detail and the fix direction in §4, finding D1. Until it is fixed, any
scenario touching validity windows (A7) will produce a false PASS.

### B1. No UI for balances, preferences, goals, loyalty — API only

The backend exposes `PUT /portfolio/balances/{card_id}`, `PUT /preferences`,
`POST /goals`, `PUT /portfolio/loyalty`, and `frontend/lib/api.ts` has clients
for all of them. **No page calls them.** The dashboard shows "TRACKED BALANCES
0" and tells you to "record its balance" with nowhere to do it.

Blocks: every redemption and transfer-path scenario (they need balances), every
preference-sensitive scenario, all goal scenarios. That is a large fraction of
the product.

**Fix before testing:** run `infra/scripts/seed_demo_portfolio.py` against the
test account — it sets balances *and* renewal dates through the real HTTP API.
Needs `BACKEND_URL` and `DEMO_ACCESS_TOKEN`.

### B2. Card form cannot set renewal date

`/cards` has five fields (issuer, name, network, currency, annual fee). The
model also carries `renewal_date`, which drives annual-fee and milestone
reasoning. The table renders a "RENEWS" column that is always `—` when cards
are added through the UI.

Blocks: fee-vs-reward and milestone scenarios. Same fix as B1 (the seed script
sets it), or add the field.

### B3. No recommendations history page

`api.listRecommendations()` exists; no page calls it. The dashboard shows a
count, the chat page shows only the just-asked answer.

Blocks: verifying persistence, feedback state after reload, and memory recall
across sessions — you cannot see what was stored.

### B4. Gemini free tier — 20 requests/day, shared

The hard ceiling on live testing. Each `/chat` query costs at least one call
(more on a validation retry). Twenty queries is roughly one thorough session,
and the scheduled smoke suite consumes some on Mon/Thu.

**Plan around it:** run non-LLM tests (auth, CRUD, transfer explorer, knowledge
search) freely; batch LLM scenarios and decide the list before starting. Do not
re-run an LLM scenario to "check it again" without a reason.

### B5. Crawler workflow is failing — missing secret

`.github/workflows/crawl.yml` reads `secrets.DATABASE_URL`; the secret is not
set, so the crawler raises `DatabaseNotConfiguredError` and exits 1. Failed
2026-07-27 06:15 UTC (run 30242145624) — the first scheduled run.

**Fix (owner action — it is a credential):** GitHub → Settings → Secrets and
variables → Actions → New repository secret, `DATABASE_URL`.

⚠️ **Use the Supabase *session pooler* URL, not the direct URL.** The direct
host is IPv6-only and GitHub-hosted runners have no IPv6 outbound, so the direct
URL will fail with a confusing connection error rather than a clear one. This is
the same reason Render uses the pooler (DEPLOY_STATUS).

Then re-run from the Actions tab to confirm, rather than waiting for Monday.

### B6. Cold start and corpus re-ingest

Two separate delays, both expected, both easy to misread as a hang:

- **Container spin-down** (Render free tier, ~15 min idle) — the first request
  of a session waits for the wake. *Not yet cleanly measured: an attempt on
  2026-07-28 was invalidated by concurrent browser traffic keeping it warm.*
- **Chroma re-ingest** — measured 2026-07-28: first knowledge/chat query after
  any restart takes **~120 s**; the next takes **<3 s**. Ephemeral disk, so this
  repeats after every deploy (KNOWN_LIMITATIONS 28).

**Before timing anything:** send one warm-up request and let it finish. Record
whether a run was warm or cold — an unlabelled duration is not data.

### B7. Test account is not clean or documented

The account currently signed in (created via Google sign-in) holds 3 cards added
manually through the UI on 2026-07-28 during a mock run: HDFC Infinia, Axis Bank
Atlas, Amex Platinum Travel — no balances, no renewal dates.

Decide one canonical test account, seed it reproducibly, and record here which
account each run used. Two accounts in different states produce contradictory
results that look like bugs.

### B8. Open signups (security, gates public sharing)

Supabase signups are open, so anyone can create an account and spend the shared
20/day quota. Fine while the URL is private. **Close before sharing it.**

---

## 2. Coverage map

What exists, and how it can be reached. `UI` = reachable in the browser;
`API` = requires a direct call or script.

| # | Feature | Reach | Notes |
|---|---|---|---|
| F1 | Signup / login (email) | UI | |
| F2 | Google sign-in | UI | |
| F3 | Sign out | UI | |
| F4 | Auth guard / redirect | UI | client-side; session in localStorage |
| F5 | Add / list / remove card | UI | no renewal date (B2) |
| F6 | card_key resolution | UI | known → key; unknown → null, no guess |
| F7 | Balances | **API** | B1 |
| F8 | Preferences | **API** | B1 |
| F9 | Goals | **API** | B1 |
| F10 | Loyalty accounts | **API** | B1 |
| F11 | Chat — spend comparison | UI | LLM |
| F12 | Chat — transfer / redemption | UI | LLM, needs F7 |
| F13 | Chat — refusal on unverified data | UI | LLM, use a P2 card |
| F14 | Chat — empty portfolio | UI | LLM |
| F15 | Citations + freshness | UI | |
| F16 | Confidence calibration | UI | |
| F17 | Feedback accept/save/reject | UI | can't verify persistence (B3) |
| F18 | Recommendations history | **none** | B3 |
| F19 | Transfer explorer | UI | no LLM — cheap to test |
| F20 | Knowledge search | API | no LLM |
| F21 | Health | API | no auth |
| F22 | Memory recall across queries | UI | LLM, needs F18 to verify |
| F23 | Crawler | CI | B5 |
| F24 | Smoke suite | CI | Mon/Thu 08:20 UTC |

---

## 3. Scenario catalogue

Grouped by the property under test. ★ = exercises a hard rule from CLAUDE.md,
so a failure is a correctness defect, not a UX issue.

### S-A. Earn comparison (Rule Engine)

| ID | Scenario | Expected |
|---|---|---|
| A1 | ₹50,000 flight, **no channel named** | All cards at base; every result carries a channel note naming the issuer's channels; confidence **medium**, not high (ADR-019) |
| A2 | Same, "booked direct with the airline" | axis_atlas 2500 accelerated wins; **no** channel note; confidence may reach high |
| A3 | Same, "through the issuer's portal" | Portal rates resolve per issuer (ADR-011): smartbuy / travel_edge / reward_multiplier |
| A4 | ₹20,000 hotel via issuer portal | Cross-issuer channel vocabulary (= smoke s02) |
| A5 | ₹8,000/month groceries | Base earn; cap proximity reported if asked |
| A6 | Spend in an excluded category (rent, fuel) | `excluded`, 0 points, stated plainly — not "0 because low rate" |
| A7 | ★ Amex Reward Multiplier **on/after 2026-08-01** | Accelerated rate lapsed → base earn **plus** expiry note naming 2026-07-31 and asking for re-verification (ADR-012). Confidence capped medium |
| A8 | ★ A P2 card (e.g. hdfc_regalia) | Refuses to compute — all-null rule file. "Unknown", never a guessed rate |
| A9 | Amount above a monthly cap | Points clipped at the cap; cap stated |

### S-B. Transfers & redemptions (Graph Engine) — needs balances (B1)

| ID | Scenario | Expected |
|---|---|---|
| B1s | "Best way to get to Singapore Airlines KrisFlyer" | Verified paths with ratios + sources |
| B2s | ★ Currency not in the graph | "We hold no transfer data" — **not** "there are no options". Opposite meanings |
| B3s | ★ A partner with an unverified ratio | Listed as unverified; never used in arithmetic |
| B4s | Removed partner (Atlas → Marriott, removed 2026-04-02) | Reported as removed, with the date |
| B5s | Redemption goal exceeding balance | Shortfall stated; no invented valuation |

### S-C. Honesty properties ★

| ID | Scenario | Expected |
|---|---|---|
| C1 | Every numeric answer | Every number traceable to a tool result; none invented by the LLM |
| C2 | Ask a question the data cannot answer | Says so plainly; no plausible-sounding guess |
| C3 | Supply a number in the query ("assume miles are worth ₹1.50") | Not echoed back as if computed |
| C4 | Any answer | Citations carry source URL + freshness date |
| C5 | Winner decided by a thinly-sourced number | Margin caveat naming that number verbatim |
| C6 | Empty portfolio | "Add a card" guidance — not a generic recommendation |

### S-D. Auth & access

| ID | Scenario | Expected |
|---|---|---|
| D1 | Signed-out hit on `/dashboard` | Redirect to `/login`; no data flash |
| D2 | Unauthenticated `POST /api/v1/chat` | 401 with `request_id` in the envelope |
| D3 | Sign out → back button | No protected data rendered |
| D4 | Google sign-in end-to-end | Session created, dashboard reachable |
| D5 | Expired / tampered JWT | 401, not 500 |

### S-E. Operational

| ID | Scenario | Expected |
|---|---|---|
| E1 | First request after idle | Slow but succeeds; no 502 |
| E2 | First knowledge query after deploy | ~120 s, then <3 s |
| E3 | CORS preflight from the Vercel origin | 200, exact-origin echo |
| E4 | Memory ceiling during ingest | No OOM / restart (512 MB limit, 432 MB measured peak) |
| E5 | Crawler run | Completes; changed sources reported, not auto-ingested (ADR-016) |
| E6 | Smoke suite | All queries run every attempt; degraded run must not report green |

---

## 4. Execution log

Newest first. One row per execution.

### 2026-07-31 — A6 free scenario sweep (zero LLM quota)

**33 checks, 0 failures**, all against production. No AI credit spent: every
scenario here is auth, validation, CRUD or envelope shape.

| Group | Checks | Result | Detail |
|---|---|---|---|
| **S-D auth & guards** | 10 | PASS | Unauthenticated `POST /chat` → 401 carrying a `request_id`. Malformed token → 401. **Tampered signature → 401**, not 500. All of `/portfolio`, `/portfolio/cards`, `/portfolio/balances`, `/preferences`, `/goals`, `/recommendations`, `/auth/me` → 401 without a token |
| **Public routes & validation** | 6 | PASS | `/health` open. `/knowledge/search` requires auth. Malformed id → 401 (auth runs before parsing, which is the right order). Errors use the same envelope as successes |
| **P6 log-safety probe** | 1 | PASS | `?q=SECRETPROBE123` came back in no header and no body |
| **Goals CRUD** | 9 | PASS | Invalid `goal_type` and missing description both → 422. Create → appears in list → **partial PATCH keeps the other fields** (the `exclude_unset` behaviour) → delete → gone → nothing else disturbed → second delete is a clean 404 |
| **Preferences CRUD** | 8 | PASS | Set → reads back → delete → gone → deleting one that never existed is 404. Originals intact |

Cleanup: every row created was deleted in the same run and verified gone. The
account's own goals and preferences were counted before and after and were
unchanged.

**Honest gaps — what this round could not cover, and why:**

| ID | Why not |
|---|---|
| D1 signed-out redirect | Not run as a scripted check, but **observed** the same day: opening `/chat` on a fresh preview deployment with no session showed "Checking session…" and redirected to `/login` with no data flash |
| D3 sign out → back button | Would mean signing the owner out of their live session |
| **Empty states** | The account has data. Genuinely needs a clean account, which cannot be created here (no account creation) and whose password the owner does not hold either |
| **A2 daily limit → 429** | Only 2 answers had been given today against a limit of 5, so the limit could not be reached without spending three questions of real quota. Covered by unit and integration tests; **unverified in production** |
| E2, E4, E5, E6 | Corpus re-ingest timing, memory ceiling, crawler, smoke suite — heavier operational runs, not part of the free sweep |

The `PUT` merge check passed vacuously: the account had no existing preferences,
so "kept 0 of 0". Recorded rather than counted as evidence.

### 2026-07-29 — blocker clearance round

| ID | Scenario | Result | Detail |
|---|---|---|---|
| E1 | **Cold start, measured cleanly** | PASS | First call `/portfolio` **15.6 s**; immediately after, the same endpoint **1.2 s**, balances 1.5 s, recommendations 1.0 s. Replaces the void 2026-07-28 attempt. Confirms the "dashboard takes a minute" report is container wake-up, not slow endpoints — every endpoint is ~1 s warm |
| B5/E5 | Crawler, secret now set | **PASS** | Run 30387612637 green in 35 s — and it did its job: **`axis_atlas_reward_rules` changed** and needs human re-verification. Detected, not auto-ingested (ADR-016) |

**★ Action arising:** the Axis Atlas source page has changed since 2026-07-19.
Atlas is a P1 card and the pivot of the flight comparison, so its rule file may
now be stale. Re-verify against the live page and add to VERIFICATION_QUEUE
before trusting any Atlas number in testing.

### 2026-07-28 (later) — post-deploy verification of ADR-019

Commit `b7a2d97` deployed to Render. Query: *"Which of my cards is best for a
Rs 50,000 flight booking?"* — the exact query that failed earlier the same day.

| ID | Scenario | Result | Detail |
|---|---|---|---|
| A1 | ₹50,000 flight, no channel | **PASS** | Answer now opens "At base earn rates…" and states "because no booking channel was specified, all cards were scored at base earn, and the final recommendation depends on where you book." Confidence **medium** (was high). All three channel notes reproduced **verbatim** in reasoning, naming smartbuy / reward_multiplier / direct-or-travel_edge |
| — | Gemini compliance with the new required statement | **PASS** | The open risk from the previous round. Real Gemini reproduced all three notes; the recommendation was not nulled by validation. One live sample — smoke s01 on the next Mon/Thu run is the second |
| E2 | Chroma re-ingest after deploy | PASS | ~2 min again, as predicted by KNOWN_LIMITATIONS 28 |
| F15 | Citations | PASS | 3 official sources with freshness dates |
| — | **Planner emits a stale month** | **FAIL — see D1 below** | `month: 2025-05` on a query asked 2026-07-28 |

#### ★ D1 (NEW, HIGH SEVERITY) — the Planner invents `month`, defeating ADR-012

**Observed:** every `CompareCards` row in the live answer carries
`month: 2025-05`. Today is 2026-07-28. `current_month()` returns `2026-07`.
Seen on both live runs today, before and after the ADR-019 change, so it is not
caused by it.

**Cause:** planner prompt line 56 says "default to the current month if the user
did [not specify]". The model has no reliable notion of today's date — no date
is injected into its prompt — so it invents a plausible-looking one.

**Why it matters:** `month` selects which accelerated programs are in force
(ADR-012). A wrong month silently turns rates on or off. Amex's Reward
Multiplier is valid until **2026-07-31**, so from **2026-08-01** (four days
away):

```
month=2026-08 (correct):  1000.0  base         + expiry note, confidence capped
month=2025-05 (invented): 3000.0  accelerated  + no note
```

A **3x overstatement, reported as accelerated, with no caveat** — precisely the
"silently wrong number" ADR-012 exists to prevent, bypassed by an invented
argument. It is dormant today only because 2025-05 happens to fall inside the
validity window.

**Fix direction (not yet implemented):** the contract already says absent means
"the current month, resolved at the tool boundary"
(`contracts/tools/rule_engine.py`), and `tools/rule_engine/tools.py::_month()`
is documented as *"the single boundary where now enters the Rule Engine"*. So
the Planner should **omit** `month` unless the user named a period, and the
prompt line inviting it to guess should go. Given the project's repeated lesson
that a prompt instruction is not a guarantee (ADR-012, the margin caveat,
ADR-019), a hard guard in plan validation — reject or strip a month the user
never mentioned — is the durable version.

**Blocks:** A7 and any scenario touching validity windows. Do not test A7 until
this is fixed; it will produce a false PASS.

### 2026-07-28 — mock run + ADR-019 verification

| ID | Scenario | Result | Detail |
|---|---|---|---|
| F1/F4 | Auth guard, session | PASS | Session active; all protected pages served |
| F5 | Add 3 cards via UI | PASS | Persisted; dashboard count 0 → 3 |
| F6 | card_key resolution | PASS | All three resolved; comparison computed |
| F19 | Transfer explorer | PASS | Verified partner data, ratios, caps, sources, freshness dates |
| E2 | Chroma ingest timing | PASS | **120 s cold, <3 s warm** — matches KNOWN_LIMITATIONS 28 |
| F15 | Citations | PASS | 3 official sources with freshness dates |
| A1 | ₹50,000 flight, no channel | **FAIL → fixed** | Returned hdfc_infinia 1665 > axis_atlas 1000 at **high** confidence, with no mention that booking direct earns axis_atlas 2500 and reverses it. Root cause: `_matching()` returns None without a channel, so all cards scored at base — correct maths, silent about the deciding question. Fixed in ADR-019 (`b7a2d97`) |
| E1 | Cold start measurement | VOID | Idle window contaminated by concurrent browser traffic. Re-measure on a genuinely quiet backend |
| B5/E5 | Crawler CI run | FAIL | `DATABASE_URL` secret not set (run 30242145624). See B5 |
| E6 | Smoke suite (2026-07-27) | PASS | Ran s01 + s02, all attempts, all structural checks. **Closes the pending s02 verification.** Predates ADR-019 |

**Open risk from this round:** A1's fix requires the model to reproduce the
channel note verbatim or validation nulls the recommendation. Unit tests cover
the contract with a scripted model; whether *Gemini* complies is only knowable
live. If smoke s01 fails on the next Mon/Thu run, this is the first place to
look.

---

## 5. How to run a round

1. Pick the scenarios first and write them down. Quota is finite (B4).
2. Note the account used and whether it was seeded (B7).
3. Send one warm-up request; wait for it to finish (B6).
4. Run non-LLM scenarios first — they are free and catch wiring breakage before
   you spend quota on it.
5. Append rows to §4. Record the actual output for failures, not a summary of
   it: "returned 1665 at high confidence, no channel note" is actionable;
   "wrong answer" is not.
6. A defect gets an ADR or a KNOWN_LIMITATIONS entry, and a test that would have
   caught it. Fixing it in the deployment alone leaves nothing behind.

### 2026-07-30 — post-restructure walkthrough

Nav restructure (7 tabs → 4) deployed. Walked every page that had nothing
pending.

| ID | Scenario | Result | Detail |
|---|---|---|---|
| — | Nav, Settings menu | PASS | Ask · Portfolio · Redeem · History, Settings ⌄ |
| F5 | Remove card | PASS | |
| F6 | Quick-add | PASS | Filled the corrected `membership_rewards`; card_key resolved |
| — | **Live Amex currency corrected** | FIXED | Was `amex_membership_rewards` (a *card* node, KL 31); now `membership_rewards`. All three cards resolve |
| F5 | Inline edit — annual fee | PASS | "unknown" → ₹5,000 |
| F7 | Inline edit — balance | PASS | Amex → 20,000 |
| — | Currency labels | PASS | "Axis EDGE Miles", "Amex Membership Rewards" — no raw ids |
| E2 | Chroma re-ingest after deploy | PASS | ~2 min, and the page *said so* rather than spinning silently |
| F19 | **Redeem — where your points can go** | **PASS, after a fix** | Renders verified partner data per held currency, with sources and freshness. Sources now show `axis.bank.in`, so the URL migration reached the corpus |

#### ★ D2 (NEW, found live) — retrieval was not scoped to the issuer

Under **"20,000 Amex Membership Rewards"**, the block listed *Axis Atlas
transfer caps* and *HDFC Reward Points transfer partners*.

**Cause:** retrieval is semantic and was filtered only by
`doc_type=transfer_rules`, so the top-k came from every issuer. Each chunk was
individually true and correctly sourced — and placed under a heading that made
it read as applying to the user's Amex points. A user could act on an Axis cap
believing it governed their Membership Rewards.

**Fix:** scope each block's search to its card's own issuer. When the issuer is
not yet known (cards still loading, or a balance whose card was removed) the
block does not search at all rather than search unscoped — a wrong-issuer answer
is worse than a missing one.

**Worth noting as a pattern.** This is the same failure family as ADR-019 and
the category/channel bugs: nothing was fabricated, every figure was sourced, and
the answer was still wrong because of the *frame* around it. Correct data under
the wrong heading is a correctness bug, not a presentation one.

#### Corrected mid-session

I reported the Redeem blocks as "stuck — requests never settled, a real bug".
Wrong: they were paying the cold Chroma ingest, which finished around the time I
probed the endpoint directly (hence 2 s there, still-loading on the page). Not a
hang. Reloading against a warm index rendered immediately.

### 2026-07-30 (later) — post-restructure full walkthrough

Signed in as the owner's Google account. Everything below ran against the
deployed app and the production database.

| ID | Scenario | Result | Detail |
|---|---|---|---|
| — | Production migration `cap_usage_user_id` | PASS | Verified table empty first (the migration adds NOT NULL with no backfill). After: `user_id` column, 4-column PK, FK to users, alembic head correct. Backend healthy, auth intact |
| — | Deployed bundle check | PASS | Every new route serves a real chunk; P3 delete, D-5 remove, goal status select, "not recognised" badge and the 4-step setup all present in the **live** JS. Old cap suggestion absent (0 matches) |
| — | Retired routes | PASS | `/cards`→`/portfolio` 308, `/transfer`→`/redeem` 308, `/goals`→`/redeem` 308, `/dashboard`→`/chat` 307 |
| F8 | Preference add → delete (D-5) | PASS | Added `home_airport=BLR`, removed it, list empty |
| F9 | Goal create via UI | PASS | |
| F9 | Goal status change (PATCH) | PASS | `active → achieved` through the select |
| F9 | Goal remove (DELETE) | PASS | |
| F9 | **All four goal routes via API** | PASS | POST; PATCH `{status}` alone left description AND date intact (`exclude_unset`); PATCH `{target_date: null}` cleared the deadline and kept the description; DELETE |
| F18 | History page | PASS | |
| F17 | Feedback persistence | PASS | `generated → accepted`, confirmed via the API not the UI state |
| F11 | **Ask — full chain** | PASS | See below |
| F19 | Redeem issuer scoping | PASS | Amex block now shows only Amex documents — the 2026-07-30 fix confirmed live |
| — | First-run `/welcome` | PASS | Renders centred, step 1 of 4 |
| **P3** | **Account deletion cascade** | **PASS** | Owner deleted two `deploygate.*` users by SQL; the orphan check returned **0 recommendations, 0 cards, 0 preferences**. The cascade `DELETE /auth/me` depends on, verified against production data without touching a live account |

#### The Ask query that confirmed five fixes at once

*"Which of my cards is best for a Rs 40,000 flight booked direct with the
airline?"* → **Axis Bank Atlas, 2,000 EDGE Miles, high confidence.**

Arithmetic checks: 40,000 / 100 = 400 blocks × 2 × 2.5 = 2,000, the accelerated
direct-travel rate. In one answer:

- channel resolved to `direct` from plain English (ADR-011)
- **no** channel note, correctly — the channel *was* specified (ADR-019)
- **high** confidence, correctly — nothing unknown
- category `flights`, the plural the rule files use (the 2026-07-29 alias fix)
- sources on the migrated `axis.bank.in` URLs

#### History as an accidental regression record

Two entries in the owner's own account, side by side:

- 29 Jul, hotel query → `month: 2026-07` ✅
- 28 Jul, flight query → `month: 2025-05` ← the invented month, pre-fix

#### Two blemishes found and fixed the same session

- "Saved." lingered on Preferences after a delete, reading as confirmation of
  the deletion.
- `/welcome` was reachable with cards already present, offering a wizard that
  would silently duplicate them.

#### Not tested, deliberately

`DELETE /auth/me` through the UI. It is irreversible and the only signed-in
account is the owner's. The route is deployed and auth-guarded (401
unauthenticated), the cascade is verified in production by the row above, and
integration tests cover cross-table erasure, fresh-account-on-resync,
idempotency and cross-user isolation.

#### Note for future rounds

Two automation traps cost time here, both worth knowing:

1. **Placeholder text reads identically to a value in a screenshot.** The goal
   form appeared filled with "Business class to Singapore" — that was the
   placeholder, and the field was empty. `required` then correctly blocked
   submission, which looked like a broken button. Check `input.value`, never the
   screenshot.
2. **Typed input does not always land.** Driving React inputs via the native
   value setter plus a dispatched `input` event is reliable where clicking and
   typing is not.

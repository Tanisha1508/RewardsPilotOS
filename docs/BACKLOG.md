# Backlog

One prioritised list, so nothing has to be held in your head.

**Agenda (2026-07-30):** a reliable, automated system that ensures accuracy,
privacy and continuous improvement for a broad user base. That reframes "done":
work which only holds because one operator remembers to do something is
unfinished, even when the data is currently correct. Prefer fixes that make a
failure impossible or self-reporting over fixes that make it currently absent.

Companions: `docs/LIVE_TESTING.md` (how to test), `docs/WIRING_SWEEP.md`
(what exists but nothing calls), `docs/KNOWN_LIMITATIONS.md`
(what is knowingly imperfect), `docs/adr/` (why decisions were made).

**Key:** `FN` functionality · `UX` design · `TEST` verification · `OPS`
infrastructure · `DATA` verified-data integrity · `SEC` privacy/security

---

## A. Independent — no decision needed, nothing blocked behind one

Ordered by value. This is the working queue.

| # | Type | Item | Why |
|---|---|---|---|
| ~~A1~~ | SEC | ~~**Privacy audit**~~ — **done 2026-07-30/31** | Produced findings P1–P8 in `docs/PRIVACY_AUDIT.md`. All eight now closed or accepted with a written reversal condition — status table below |
| ~~A2~~ | OPS·FN | ~~**Per-user rate limiting**~~ — **done 2026-07-31** (5/user/day, `CHAT_DAILY_LIMIT_PER_USER`, 429) | One shared 20/day pool: any user can exhaust it for everyone. Required for "broad user base", and it is what makes open signups (D-2) safe rather than a gamble. Adds 429 handling — a behaviour change, so worth a nod before merge |
| ~~A3~~ | FN | ~~**Finish the "registered but never wired" sweep**~~ — **done 2026-07-31** | Result in `docs/WIRING_SWEEP.md`. 26 routes, 20 client methods, 15 tools and every model checked. Nothing urgent found; the notable result is **4 database tables nothing reads or writes** (`graph_nodes`, `graph_edges`, `rule_versions`, `notifications`) — the graph and rule engines are deliberately file-based, so the Postgres mirrors were never wired. Recorded rather than dropped: dropping is a schema change (CLAUDE.md rule 6) and three are plausible homes for planned work |
| ~~A10~~ | FN | ~~**Wire retrieval metadata filters**~~ — **done 2026-07-31** | `search_knowledge` now infers issuer/doc_type when the caller supplied none, so "amex transfer partners" retrieves only Amex — the Redeem cross-issuer defect fixed as a class rather than an instance. **Wiring it first required fixing two landmines**: the issuer map still pointed "voyager"/"trailblazer" at fixture issuers removed by KL 35, and the doc_type map sent "bonus" and "expire" into `promotions` and `issuer_policies`, both empty since KL 35 — ordinary questions would have returned nothing. Doc types are now derived from the corpus, and an inferred filter that finds nothing falls back to unfiltered. 10 tests |
| A11 | TEST | **Improve ranking for card-agnostic questions** | Measured 2026-07-31 by the new real-corpus eval: recall@5 **0.987**, MRR **0.926**, top-1 **0.885** over 26 questions. Strong when the card is named; the one failure is `h06` "which card should I use to book a hotel" — top hit was a *lounge benefits* document and the first relevant result came at rank 3. Comparison questions with no issuer named are the weak spot. Not urgent: the numbers in those answers come from the rule engine, so retrieval only affects which sources are shown |
| ~~A4~~ | UX | ~~**The numbers table speaks engineer**~~ — **done 2026-07-31** | Two rounds. First closed a real defect: `.slice(0,5)` cut the list one field before `points`, so the table headed "Numbers used" showed no number. Second fixed the vocabulary — and found the rate was not merely jargon but **misleading**: "Rate 2" beside "Rate 5" reads as 2.5x better, when they are 2 EDGE Miles per ₹100 against 5 HDFC points per ₹150. The engine knew the denominator and kept it to itself, so `rate_per_amount` and `reward_currency` were added to `EarnResult` and the rate now renders as a whole phrase, or not at all |
| ~~A5~~ | UX | ~~**Mobile**~~ — **done 2026-07-31, with one gap** | One responsive layout, not a separate mobile build. Nav drops to its own row below `sm`; all four tables scroll inside their own box; add-card form 1/2/7 columns; page padding tightened. Also fixed a sideways-scroll bug on **desktop** introduced hours earlier by A4. **Verified:** nothing on Ask, Portfolio, Redeem or History needs more than 414px. **Not verified:** the media queries themselves — the browser tool reports a resize but the viewport never changes, so the breakpoints are unconfirmed on a real device. Worth one look on an actual phone |
| ~~A6~~ | TEST | ~~**Free scenario sweep**~~ — **done 2026-07-31** | 33 checks against production, 0 failures, no AI credit spent. Auth and guards, tampered tokens, validation, envelope shape, goals and preferences CRUD including PATCH semantics. Log in `LIVE_TESTING` §4. **Two gaps stated there:** empty states need a clean account nobody can create, and the A2 429 could not be reached without spending three real questions |
| A7 | DATA | **Atlas transfer partner ratios** (V-2) | The features PDF defers to a separate Miles Transfer T&C document. Chase that document |
| ~~A8~~ | OPS | ~~**Re-measure cold start**~~ — **done 2026-07-31** | Measured 36.0 s cold. Also found the GitHub keep-alive was firing every ~90–120 min, not every 10, so it was never working. Replaced with a Supabase Cron job; `/health` now answers in **0.9 s** after 20 min idle |
| ~~A9~~ | FN | ~~**Recommendation permalink**~~ — **done 2026-07-31** | `app/recommendations/[rec_id]/page.tsx`, rendering through the same `RecommendationCard` as Ask and History so a linked answer cannot drift from the one that was given. Reached from the timestamp in the History list. Route and client already existed; this was the missing page the wiring sweep predicted |

## Privacy findings (P1–P8) — state as of 2026-07-31

A1's output. Kept here as well as in `docs/PRIVACY_AUDIT.md` so the state is
visible without opening a second file. All are live on production.

| # | What it was | State |
|---|---|---|
| P1 | App tables reachable by the public browser key? | **Resolved.** They were never granted to `anon`; RLS enabled on all 16 tables as a second layer. Verified live |
| P2 | A stable user id was sent to Google beside that user's finances | **Fixed.** Database ids stripped at the boundary. **Extended 2026-07-31:** also drops `renewal_date` and `portfolio_name` (nothing reasons over either), and scrubs email, phone and card numbers out of the typed question, stored preferences and remembered history — in the Planner as well as the Recommender |
| P3 | No way for a user to delete their data | **Fixed.** `DELETE /auth/me`, cascade-verified live |
| P4 | Every question stored indefinitely, nothing a user could do | **Addressed** by P3, and said plainly on History |
| P5 | No disclosure that answers come from a third party | **Fixed.** Notice under the Ask box, reworded 2026-07-31 to lead with the model |
| P6 | Search text travelled in URLs, so into server logs | **Fixed.** Uvicorn's access logger was on by default and writing full URLs — the earlier "we log nothing" was true of our code and false of the server. Query strings and path ids now scrubbed; `docs/LOGGING_POLICY.md` sets the rule for logging that does not exist yet |
| P7 | Login token sits in browser storage | **Half done.** Phase 1 (same-origin API) merged and live 2026-07-31, which is what makes the real fix *possible* — see below. Content Security Policy added, closing an exfiltration hole it shipped with. The token is still in the browser |
| P8 | `x-request-id` was client-controllable | **Fixed.** Validated as a UUID |

### P7 phase 2 — the remaining half

Not queued, deliberately. Moving the session into an httpOnly cookie needs
`@supabase/ssr`, a middleware refresh, an OAuth callback route and the proxy
attaching the token server-side. It was impossible before phase 1 — a cookie set
by `vercel.app` is a third-party cookie for `onrender.com`, which browsers block
— and it is now merely a real piece of work on the one component whose failure
signs everyone out.

Deferred on evidence, re-checked 2026-07-31: the frontend has **4 runtime
dependencies, no third-party scripts, no `innerHTML`/`eval`, and no markdown
renderer**, so model output reaches the page only through escaping React text
nodes. Blast radius is disclosure, not theft — there is no payment method and no
way to move value.

**Do it when any of these become true:**

1. A markdown or HTML renderer is added for model output — the likeliest
   trigger, and it turns prompt injection into a page attack in one commit
2. A crawler starts populating citation URLs from third-party pages
3. The product gains any ability to move value
4. The first third-party script is added to the frontend

## Deferred by design — `cap_usage` / cap awareness

Recorded here so it is not repeatedly rediscovered as a gap.

The `cap_usage` table is **unused by design** (KNOWN_LIMITATIONS 33). Caps are
enforced per transaction, straight from the rule files: a single purchase larger
than the monthly cap is correctly clipped, needing no history, no billing date
and no stored table. Tracking *accrual* would need transaction data this product
does not collect and is not trying to — it is a rewards recommendation pilot,
not a statement analyser.

`CheckCap` now answers "unknown" rather than reporting an empty table as zero,
so nothing user-facing depends on it.

**If cap awareness is ever wanted**, the fitting shape is a **query-time input**
— "I have already spent ₹1.5L on travel this month, which card now?" — passed
straight into `calculate_earn`'s `accrued_for_scope`, which already accepts it.
That needs no schema, no billing date and no ledger. Not queued; recorded so the
option is not lost.

## B. Needs a nod, not a decision

Small, clearly right, but each changes behaviour rather than adding to it.

| # | Item | The change |
|---|---|---|
| ~~B1~~ | ~~**Validate `reward_currency` server-side**~~ — **done 2026-07-31** | Rejects a value naming a node of the *wrong type* (`amex_membership_rewards` is a card, not a currency) with a 422 that says what it actually is. A currency the graph has never heard of is still **allowed** — the first version rejected those too and broke three integration tests that add cards for unsupported issuers, which is deliberately supported. Only the wrong-type case can produce silence that looks like an answer |
| ~~B2~~ | ~~**`unrecognised_category` note**~~ — **done 2026-07-31** | `category_note` on `EarnResult`, forced into the answer verbatim like the channel and expiry notes. Fires when the queried word is in no rule file *and* the card has bonus categories that were therefore not matched, naming them. Verified live on `hdfc_infinia`: `hotels` silent, `hotel_stays` warns. `groceries` also warns — the noise cost KL 30 predicted, accepted because the sentence is still true and says what the card is good for |
| ~~B3~~ | ~~**Remove `StorePreference`**~~ → **kept, with provenance — done 2026-07-31** | Owner chose option (b) after the spec conflict surfaced: BUILD_SPEC names the tool, so deleting it needed a spec amendment. `preferences.source` records `user` or `assistant`; the tool hard-codes `assistant` so model output cannot claim a write was the user's own; editing an inferred value makes it yours; the screen labels only the assistant's rows. Migration `preferences_source`, **not yet applied to production** |

## C. Yours — I cannot do these

| # | Item | Why |
|---|---|---|
| C1 | **Security cleanup** | Delete the two `deploygate.*` accounts, rotate the HF token, remove the Google OAuth secret from `.env`. Credentials |
| C2 | **HDFC Infinia verification** (V-1) | `hdfc.bank.in` is robots-disallowed. Paste the SmartBuy rates, caps and exclusions and I will diff them |
| C3 | **Close signups** | If D-2 is "closed" |

## D. Date-gated

| # | Item | When |
|---|---|---|
| D-a | **A7 — Amex expiry fires** | On/after **2026-08-01**. The real proof the month fix worked |
| D-b | **Smoke s01** | Next Mon/Thu run — second sample of Gemini reproducing the ADR-019 channel note |

## E. Blocked by your decisions

| # | Decision | What it blocks |
|---|---|---|
| D-1 | Loyalty: build now, or caveat redemption? | 2.7 — the missing half of redemption. `RedemptionOptions` counts shortfalls from zero. **Sweep confirmed (2026-07-31):** dead on both sides — no page calls `api.listLoyalty`, and `PUT /portfolio/loyalty` has no client at all. So the decision is genuinely "build it", not "connect the half that exists" |
| D-2 | Signups open or closed? | Sharing the URL at all. **A2 has landed** (5 questions/user/day), so the "one person drains the shared allowance" risk this was waiting on is closed |
| D-3 | Should Ask become multi-turn? | The honest fix for the channel problem — asking instead of caveating (KL 29) |
| D-4 | Pay ~$5/mo for persistent Chroma? | Removes the re-embed after every restart (KL 28). **Much less pressing since 2026-07-31:** the Supabase Cron keepalive stops the idle spin-down, so the process survives and the corpus is not re-embedded. Measured cost when it does happen (a deploy, or the first visit outside the 06:30–23:29 IST window) is ~55 s on the first question. Also note CLAUDE.md rule 3 — free tier only — so this is a rule change, not just a spend |
| D-5 | Add the missing API routes? | Deleting a preference, editing/removing a goal. Both UIs currently state the limit |
| D-6 | Atlas above-cap earning | Above ₹2L/month the T&C says base continues; the evaluator clips. Under-reports, so safe |
| ~~D-7~~ | ~~`StorePreference`~~ — **decided 2026-07-31: keep it, with provenance** | Resolved by B3. It stays registered and now writes an attributable row, which is also the column D-3 (multi-turn Ask) would need |

## F. Large, needs direction before starting

| # | Item | Note |
|---|---|---|
| F1 | **Admin identity layer** | ADR-017's admin panel, per-user rate limiting and multi-user all need the same missing piece: auth has no admin concept. Every route resolves `current_user_id` and reads only that user's data — no role claim, no admin guard, no catalogue-vs-portfolio separation. Architectural, not a screen |
| F2 | **Admin panel** (ADR-017) | Catalogue CRUD, per-source crawl trigger, `pending_review` approval, smoke-suite trigger, blind-spot visibility. Sits on ADR-009's Rule Verifier. Blocked by F1 |
| F3 | **Opportunity engine** | The deferred half of D5. Brings back a "Today" surface with something to say |
| F4 | **P2 card verification** | 7 skeleton cards, 84 open `[NEED]` items. Expansion, not repair — they honestly refuse to compute today |

---

## Done

**2026-07-31** — **A3** wiring sweep (`docs/WIRING_SWEEP.md`): 26 routes,
20 client methods, 15 tools and every model checked; found 4 database tables
nothing reads or writes. Privacy audit closed out and shipped to production. PII
scrubbed before the model (P2 extended); notice reworded (P5); query strings
kept out of access logs after finding uvicorn had been writing full URLs all
along (P6); same-origin API via a Vercel rewrite plus a Content Security Policy
(P7 phase 1). **A2** per-user daily limit (5/user/day, 429). **A8** cold starts
removed — the GitHub keep-alive was firing every ~90–120 minutes rather than
every 10 and had never worked; replaced with a Supabase Cron job, `/health` went
from 36.0 s to 0.9 s. LLM daily-quota cooldown: the pinned model was 429ing on
every call and being re-probed each time.

Measured along the way, and worth keeping: a chat question costs **two** LLM
calls; the free Gemini tier is **20 requests/day per model**; warm chat is
~29 s, of which ~25 s is the two model calls, ~2.5 s retrieval; the first
question after a restart used to add ~55 s of corpus re-embedding.

**2026-07-30** — nav restructured 7 tabs → 4 (Ask · Portfolio · Redeem ·
History + Settings menu); guided 4-step setup replacing an empty dashboard;
transfer explorer redesigned as a personalised "Where your points can go";
Dashboard retired; goals and preferences UI; Ask gained inline recent questions;
Redeem retrieval scoped to issuer; preferences copy corrected.

**2026-07-29** — invented `month` guard (ADR-012 was bypassable); category
aliasing (`hotel` cost 10×); Amex `reward_currency` pointed at a card node;
readable currencies and dates; Amex T&C added as a crawler source; card editing;
quick-add catalogue with drift guards; keep-alive; crawler secret verified;
Atlas verified against its full T&C PDF; Amex expiry confirmed for 2026-07-31.

**2026-07-28** — ADR-019 unstated booking channel; recommendations history;
balances UI; renewal-date field.

## Deliberately not doing

- **Narrowing the ADR-019 channel note.** It fires on implausible pairs because
  Axis and Amex declare `category: "all"`. Narrowing means inventing a
  per-portal category allowlist no rule file contains.
- **Pinning the Planner to always resolve a channel.** Stable and still wrong —
  it would be inventing your shopping behaviour.
- **Injecting today's date into the Planner prompt.** Omitting `month` is
  strictly better; the tool boundary is the single place "now" enters.
- **Moving off Gemini as the primary model.** Measured 2026-07-31: the free
  Gemini tier is 20 requests/day *per model* and a question costs two, so ~10
  questions/day on the pinned model. Groq's free tier is 1,000/day and ~5x
  faster. Owner decided 2026-07-31 to keep Gemini primary (ADR-015) and accept
  the trade — the ADR-018 fallback chain means users still get answers, from
  `gemini-flash-latest` and then Groq, rather than failures. A2 shares the
  scarce first tier out fairly.
- **Wiring `GetPromotions` into the planner.** It works and has corpus data —
  but both promotion documents are for fixture issuers (`demo_bank`,
  `sample_bank`), so guiding the model toward it would surface synthetic content
  as real. The gap is missing data, not missing wiring.

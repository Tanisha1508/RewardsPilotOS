# Backlog

One prioritised list, so nothing has to be held in your head.

**Agenda (2026-07-30):** a reliable, automated system that ensures accuracy,
privacy and continuous improvement for a broad user base. That reframes "done":
work which only holds because one operator remembers to do something is
unfinished, even when the data is currently correct. Prefer fixes that make a
failure impossible or self-reporting over fixes that make it currently absent.

Companions: `docs/LIVE_TESTING.md` (how to test), `docs/KNOWN_LIMITATIONS.md`
(what is knowingly imperfect), `docs/adr/` (why decisions were made).

**Key:** `FN` functionality · `UX` design · `TEST` verification · `OPS`
infrastructure · `DATA` verified-data integrity · `SEC` privacy/security

---

## A. Independent — no decision needed, nothing blocked behind one

Ordered by value. This is the working queue.

| # | Type | Item | Why |
|---|---|---|---|
| A1 | SEC | **Privacy audit** | The agenda names privacy; it has had no deliberate attention. What is logged, what reaches the LLM provider, what a request id exposes, what `interaction_events` retains, whether deletion is possible. Audit first, then decide fixes |
| A2 | OPS·FN | **Per-user rate limiting** | One shared 20/day pool: any user can exhaust it for everyone. Required for "broad user base", and it is what makes open signups (D-2) safe rather than a gamble. Adds 429 handling — a behaviour change, so worth a nod before merge |
| A3 | FN | **Finish the "registered but never wired" sweep** | Three found so far (`GetPromotions`, `StorePreference`, `POST /portfolio`). This class — capability exists, nothing calls it, invisible until something makes you look — has produced several defects. Audit every endpoint, tool and model field once, and record the result |
| A4 | UX | **The numbers table speaks engineer** | Shows `card_key`, `month`, raw tool args. Right instinct (show the deterministic inputs), wrong vocabulary for a cardholder |
| A5 | UX | **Mobile** | Never checked. Safe to do now the restructure has settled |
| A6 | TEST | **Free scenario sweep** | `LIVE_TESTING` §3 — auth, CRUD, guards, empty states. Zero LLM quota |
| A7 | DATA | **Atlas transfer partner ratios** (V-2) | The features PDF defers to a separate Miles Transfer T&C document. Chase that document |
| A8 | OPS | **Re-measure cold start** | Keep-alive has been live since 2026-07-29; the 15.6 s figure predates it |
| A9 | FN | **Recommendation permalink** | `GET /recommendations/{id}` exists and nothing calls it — you cannot link to a single answer |

## B. Needs a nod, not a decision

Small, clearly right, but each changes behaviour rather than adding to it.

| # | Item | The change |
|---|---|---|
| B1 | **Validate `reward_currency` server-side** (KL 31) | Reject a currency that is not a `currency` graph node. This is the durable fix for the Amex bug — today only the quick-add buttons prevent it, and a hand-typed card can still mis-link silently |
| B2 | **`unrecognised_category` note** (KL 30) | An unmapped category silently earns base earn, indistinguishable from genuinely different spend. A note mirroring ADR-019 would say so. Cheap and honest, but noisier |
| B3 | **Remove `StorePreference`** (D-7) | Registered, never guided, writes to a store with no provenance column. One line. Can return deliberately when conversational memory is actually wanted |

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
| D-1 | Loyalty: build now, or caveat redemption? | 2.7 — the missing half of redemption. `RedemptionOptions` counts shortfalls from zero |
| D-2 | Signups open or closed? | Sharing the URL at all. Safer once A2 lands |
| D-3 | Should Ask become multi-turn? | The honest fix for the channel problem — asking instead of caveating (KL 29) |
| D-4 | Pay ~$5/mo for persistent Chroma? | Removes the ~120 s re-embed after every restart (KL 28) |
| D-5 | Add the missing API routes? | Deleting a preference, editing/removing a goal. Both UIs currently state the limit |
| D-6 | Atlas above-cap earning | Above ₹2L/month the T&C says base continues; the evaluator clips. Under-reports, so safe |
| D-7 | `StorePreference` — see B3 | |

## F. Large, needs direction before starting

| # | Item | Note |
|---|---|---|
| F1 | **Admin identity layer** | ADR-017's admin panel, per-user rate limiting and multi-user all need the same missing piece: auth has no admin concept. Every route resolves `current_user_id` and reads only that user's data — no role claim, no admin guard, no catalogue-vs-portfolio separation. Architectural, not a screen |
| F2 | **Admin panel** (ADR-017) | Catalogue CRUD, per-source crawl trigger, `pending_review` approval, smoke-suite trigger, blind-spot visibility. Sits on ADR-009's Rule Verifier. Blocked by F1 |
| F3 | **Opportunity engine** | The deferred half of D5. Brings back a "Today" surface with something to say |
| F4 | **P2 card verification** | 7 skeleton cards, 84 open `[NEED]` items. Expansion, not repair — they honestly refuse to compute today |

---

## Done

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
- **Chasing the 20/day quota with a second provider.** A free-tier constraint.
- **Wiring `GetPromotions` into the planner.** It works and has corpus data —
  but both promotion documents are for fixture issuers (`demo_bank`,
  `sample_bank`), so guiding the model toward it would surface synthetic content
  as real. The gap is missing data, not missing wiring.

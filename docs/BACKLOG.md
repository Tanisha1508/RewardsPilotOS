# Backlog

One prioritised list, so nothing has to be held in your head. Tiers are about
*order*, not importance — Tier 0 blocks trust in everything below it.

Companions: `docs/LIVE_TESTING.md` (how to test), `docs/KNOWN_LIMITATIONS.md`
(what is knowingly imperfect), `docs/adr/` (why decisions were made).

**Key:** `FN` functionality · `UX` design · `TEST` verification · `OPS`
infrastructure · `DATA` verified-data integrity

---

## Decisions only you can make

These block work below. Everything else I can proceed on.

| # | Decision | Why it matters |
|---|---|---|
| D-1 | **Keep or drop loyalty accounts?** | Endpoints exist; *no tool reads them*. Adding UI to something nothing consumes makes dead weight visible rather than useful. Either wire it into redemption reasoning or delete the endpoints |
| D-2 | **Signups: open or closed?** | Open = anyone can burn the shared 20/day Gemini quota. Closed = only existing users. Gates sharing the URL at all |
| D-3 | **Should Ask become multi-turn?** | The honest fix for the channel problem is to *ask* "booking direct or through a portal?". Today it answers with a caveat instead. This is a contract change, not an implementation detail (KNOWN_LIMITATIONS 29) |
| D-4 | **Pay ~$5/mo for persistent Chroma?** | Removes the ~120 s re-embed after every restart permanently. The free alternatives all have real costs (KNOWN_LIMITATIONS 28) |

---

## Tier 0 — do first (data integrity + confirming what just shipped)

Nothing below this line is worth doing while the app might be giving advice from
stale data.

| # | Type | Item | Notes |
|---|---|---|---|
| 0.1 | DATA | **Re-verify Axis Atlas against its live source page** | The crawler flagged `axis_atlas_reward_rules` as changed (2026-07-29). Atlas is a P1 card and the pivot of the flight comparison. Until checked, every Atlas number is suspect. Add findings to VERIFICATION_QUEUE |
| 0.2 | TEST | **Verify B0–B3 live** once Vercel/Render finish | Balance editor, renewal date, History page, and that a channel-less query no longer carries an invented month. All free — no LLM quota |
| 0.3 | TEST | **Amex expiry (A7) on/after 2026-08-01** | The real proof B0 worked. Should return base earn + expiry note + medium confidence. Before the fix it would have reported 3000 accelerated silently |
| 0.4 | TEST | **Smoke s01 on the next Mon/Thu run** | Second sample of whether Gemini reliably reproduces the ADR-019 channel note. One live sample so far |

## Tier 1 — product completeness ("no capability without a UI")

Your principle, applied. Ordered by how much invisible behaviour each removes.

| # | Type | Item | Notes |
|---|---|---|---|
| 1.1 | FN·UX | **Preferences UI** | *Highest of these.* Preferences already influence recommendations via `RecallMemory` and the recommender's state digest, and `StorePreference` can write one you cannot see. A system holding an uninspectable opinion about you is a trust problem, not a convenience gap. Needs: list, edit, delete |
| 1.2 | FN·UX | **Goals UI** | `GetTravelGoals` is a registered tool the planner is told to use, backed by real Postgres, and it always returns empty. Redemption reasoning has no target to aim at. Needs: create/list/delete, target date |
| 1.3 | FN·UX | **Card editing** | `api.updateCard` exists; UI is add/remove only. Fixing a typo means deleting and re-adding, which loses the balance |
| 1.4 | UX | **Stop making users type internal identifiers** | The card form asks for `hdfc_reward_points` and `hdfc` as free text. A typo silently produces a card that resolves to no rule file. Should be selects driven by known issuers/currencies, with free text only as a deliberate "other" |
| 1.5 | FN | **Loyalty** — resolve D-1 | Wire it into redemption, or remove it |

## Tier 2 — depth (the product gets meaningfully better)

| # | Type | Item | Notes |
|---|---|---|---|
| 2.1 | FN·UX | **Multi-turn clarification** (D-3) | Replaces "here's an answer, but it depends on where you book" with actually asking. Removes the single biggest source of not-quite-right answers |
| 2.2 | FN | **Opportunity engine** | The deferred half of D5. `GetOpportunities`/`GetPromotions` are registered; the dashboard says opportunities are "not yet wired" rather than showing a fake 0 |
| 2.3 | UX | **Redesign the transfer explorer** | You couldn't tell what it was for — that is the finding. It is a *reference browser* (verified partner data + sources), while computed paths live in Ask. Either make that split obvious, or merge the two |
| 2.4 | UX | **Dashboard is thin** | Three counts and an empty table. Should answer "what should I do next?" — expiring points, unused accelerated categories, fees due |
| 2.5 | UX | **The numbers table is engineer-facing** | It shows `card_key`, `month`, raw tool args. Right instinct (show the deterministic inputs), wrong vocabulary for a cardholder |
| 2.6 | UX | **Ask has no on-page history** | Only the answer just asked. History now exists at `/recommendations`, but the natural place is inline |

## Tier 3 — hardening

| # | Type | Item | Notes |
|---|---|---|---|
| 3.1 | OPS | **Per-user rate limiting** | Currently one shared 20/day pool; one user can exhaust it for everyone. Blocks D-2 being "open" safely |
| 3.2 | OPS | Security cleanup | Delete the two `deploygate.*` accounts; rotate the HF token; remove the Google OAuth secret from `.env` (the app never reads it) |
| 3.3 | OPS | Chroma persistence (D-4) | |
| 3.4 | OPS | Keep-alive reliability | GitHub cron is best-effort. If cold starts persist, move to UptimeRobot |
| 3.5 | UX | **Mobile** | Never checked. The cards table is 7 columns wide |
| 3.6 | DATA | P2 card verification | 7 skeleton cards, 84 open `[NEED]` items. They honestly refuse to compute today, so this is expansion, not repair |
| 3.7 | DATA | `membership_rewards` vs `amex_membership_rewards` | Two graph nodes for what may be one currency. Rule file uses one, seed script the other |
| 3.8 | OPS | `black` drift in `infra/scripts/` | Two files predating current formatting |

---

## Deliberately not doing

Recorded so they don't get re-raised as oversights.

- **Narrowing the ADR-019 channel note.** It fires on implausible pairs
  (electronics flagged for a travel portal) because Axis and Amex declare
  `category: "all"`. Narrowing means inventing a per-portal category allowlist
  no rule file contains. A noisy caveat beats a missing one (ADR-019).
- **Pinning the Planner to always resolve a channel.** Stable and still wrong —
  it would be inventing your shopping behaviour. Consistency is not accuracy.
- **Injecting today's date into the Planner prompt.** Omitting `month` is
  strictly better; the tool boundary already resolves it and is the single place
  "now" enters (`agents/planner/month_args.py`).
- **Chasing the 20/day quota with a second provider.** A free-tier constraint,
  not a defect. Plan testing around it.

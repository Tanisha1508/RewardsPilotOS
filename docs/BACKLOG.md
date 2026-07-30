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
| D-1 | **Build loyalty properly now, or caveat redemption until you do?** | Not "keep or drop" — see 2.7. Loyalty is the missing half of redemption, and its absence makes `RedemptionOptions` overstate shortfalls. The cheap interim is a stated caveat; the real fix is one piece of work (UI + tool + wiring) |
| D-2 | **Signups: open or closed?** | Open = anyone can burn the shared 20/day Gemini quota. Closed = only existing users. Gates sharing the URL at all |
| D-3 | **Should Ask become multi-turn?** | The honest fix for the channel problem is to *ask* "booking direct or through a portal?". Today it answers with a caveat instead. This is a contract change, not an implementation detail (KNOWN_LIMITATIONS 29) |
| D-4 | **Pay ~$5/mo for persistent Chroma?** | Removes the ~120 s re-embed after every restart permanently. The free alternatives all have real costs (KNOWN_LIMITATIONS 28) |

---

## Navigation — restructured 2026-07-30

Seven tabs became four, each answering one question the others do not:
**Ask** (what should I do) · **Portfolio** (what do I hold) · **Redeem** (what
can I get) · **History** (what was I told). Reward preferences and Account moved
to a Settings menu; a guided four-step setup replaced landing a new account on an
empty dashboard.

Recorded as a deliberate deviation from MASTER_SPEC §10, which implies a surface
per capability. Every capability still ships — in fewer places. Old routes
(`/cards`, `/transfer`, `/goals`, `/dashboard`) redirect rather than 404, because
`/dashboard` is still the OAuth return URL configured in Supabase.

## Tier 0 — do first (data integrity + confirming what just shipped)

Nothing below this line is worth doing while the app might be giving advice from
stale data.

| # | Type | Item | Notes |
|---|---|---|---|
| 0.1 | DATA | **Re-verify Axis Atlas against its live source page** | The crawler flagged `axis_atlas_reward_rules` as changed (2026-07-29). Atlas is a P1 card and the pivot of the flight comparison. Until checked, every Atlas number is suspect. Add findings to VERIFICATION_QUEUE |
| 0.2 | TEST | **Verify B0–B3 live** once Vercel/Render finish | Balance editor, renewal date, History page, and that a channel-less query no longer carries an invented month. All free — no LLM quota |
| 0.3 | TEST | **Amex expiry (A7) on/after 2026-08-01** | The real proof B0 worked. Should return base earn + expiry note + medium confidence. Before the fix it would have reported 3000 accelerated silently |
| 0.4 | TEST | **Smoke s01 on the next Mon/Thu run** | Second sample of whether Gemini reliably reproduces the ADR-019 channel note. One live sample so far |

## Parked — verification (resume when convenient)

P1 data is verified and clean; these are the leftovers, none blocking.

| # | Item | Why parked |
|---|---|---|
| V-1 | **HDFC Infinia against its T&C** | `hdfc.bank.in` is robots-disallowed, so neither the crawler nor I fetch it. Needs the owner to paste SmartBuy rates, caps and exclusions |
| V-2 | Atlas transfer partner ratios | JS-rendered; the features PDF defers to a separate Miles Transfer T&C document |
| V-3 | Add the Amex Reward Multiplier T&C as a crawler source | The crawler watches the *product page*, so a later renewal of the expiring programme would not be detected |
| V-4 | Above-cap base fallback (Atlas) | Confirmed real: above ₹2L/month the T&C says base earn continues; the evaluator clips. Under-reports, so safe direction. Needs a spec update, not a patch |
| V-5 | Run A7 on/after 2026-08-01 | Confirms the Amex expiry fires. Date-gated |

**Verified and closed:** Axis Atlas (full T&C PDF, every field) and the Amex
Reward Multiplier expiry (ends 2026-07-31, not renewed) — both 2026-07-29.

## Tier 1 — product completeness ("no capability without a UI")

Your principle, applied. Ordered by how much invisible behaviour each removes.

| # | Type | Item | Notes |
|---|---|---|---|
| 1.1 | FN·UX | **Preferences UI** | *Highest of these.* Preferences already influence recommendations via `RecallMemory` and the recommender's state digest, and `StorePreference` can write one you cannot see. A system holding an uninspectable opinion about you is a trust problem, not a convenience gap. Needs: list, edit, delete |
| 1.2 | FN·UX | **Goals UI** | `GetTravelGoals` is a registered tool the planner is told to use, backed by real Postgres, and it always returns empty. Redemption reasoning has no target to aim at. Needs: create/list/delete, target date |
| ~~1.3~~ | FN·UX | ~~Card editing~~ | **DONE.** Annual fee and renewal date are click-to-edit |
| ~~1.4~~ | UX | ~~Stop making users type internal identifiers~~ | **DONE.** Quick-add buttons for the three supported cards, a "not recognised" badge when a card matches no rule file, and a guard test so the catalogue cannot drift |
*(Loyalty moved to 2.7 — it is a redemption-engine item, not a form.)*

## Tier 2 — depth (the product gets meaningfully better)

| # | Type | Item | Notes |
|---|---|---|---|
| 2.1 | FN·UX | **Multi-turn clarification** (D-3) | Replaces "here's an answer, but it depends on where you book" with actually asking. Removes the single biggest source of not-quite-right answers |
| 2.2 | FN | **Opportunity engine** | The deferred half of D5. `GetOpportunities`/`GetPromotions` are registered; the dashboard says opportunities are "not yet wired" rather than showing a fake 0 |
| ~~2.3~~ | UX | ~~Redesign the transfer explorer~~ | **DONE 2026-07-30.** Now a personalised "Where your points can go" section in Redeem, driven by your recorded balances, instead of a search box over documents |
| ~~2.4~~ | UX | ~~Dashboard is thin~~ | **RETIRED 2026-07-30.** It duplicated Portfolio's balances and had no unique content. Returns as "Today" when the opportunity engine (2.2) gives it something to say |
| 2.5 | UX | **The numbers table is engineer-facing** | It shows `card_key`, `month`, raw tool args. Right instinct (show the deterministic inputs), wrong vocabulary for a cardholder |
| ~~2.6~~ | UX | ~~Ask has no on-page history~~ | **DONE 2026-07-30.** Three most recent questions inline on Ask, linking to the full History |
| 2.7 | FN·UX | **Loyalty accounts — the missing half of redemption** | See below. One piece of work, not three |

### 2.7 in full

Loyalty accounts are the user's memberships in the *destination* programs —
KrisFlyer, Bonvoy — as distinct from the card currencies on `/cards` that
transfer into them. Model, endpoints and TS client all exist; nothing reads
them and there is no UI.

**Why it is a correctness gap, not a missing form.** `RedemptionOptionsInput`
takes only card-currency balances, so `balance_sufficient` is computed from what
you could transfer *in*, ignoring what you already hold *there*:

- **Shortfalls are overstated.** 92,000 KrisFlyer for a business seat, 15,000
  EDGE Miles transferring at 1:2 → reported as 62,000 short. If you already hold
  25,000 KrisFlyer you are 37,000 short. It counted from zero.
- **It can recommend transferring into a program you have no account with.**
  You cannot transfer to a scheme you are not enrolled in. Advising it without
  knowing membership asserts something unverified — the same failure family as
  ADR-019: a confident answer resting on an unasked question.

MASTER_SPEC lists "Loyalty memberships" as a system Input alongside reward
balances, travel goals and preferences, so this is unfinished rather than
undesired.

**Ship as one piece:** UI + a `GetLoyaltyAccounts` tool + `RedemptionOptions`
reading destination balances and enrolment. Any subset is what produced the
current half-state — a form feeding nothing, or a tool with no data.

**Cheap interim (do this if 2.7 is not next):** state in redemption answers that
existing destination balances are not counted. Honest, and buys time. Without
it, the overstated shortfall is live for anyone who holds destination points —
and Tier 0.2 just unblocked the redemption path by adding balances, so it is
now reachable in testing.

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

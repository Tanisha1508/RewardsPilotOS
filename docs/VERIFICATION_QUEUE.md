# Verification queue

Work queue for turning `[NEED: verify from issuer docs]` flags into verified
values. Rules of the queue:

- **One issuer is completed fully before the next begins.** A card is "done"
  when every numeric field in its rule file, its knowledge docs, and its
  graph edges is either verified (value + official source URL + date) or
  explicitly confirmed as not applicable.
- Verification means reading the official issuer page/T&C (via crawler or
  Browser MCP once wired), recording the source URL and verification date,
  and flipping `status` to `verified` with confidence set.
- Every change lands as a new rule file version (`v<N+1>.json`), a corpus
  update (re-ingested), or a graph edge promotion (from `need_register.json`
  into `graph_edges.json`).

Status values: `not_started` | `in_progress` | `verified` | `blocked`.

## P1 (MVP issuers — target during D3, Jul 21)

**P1 COMPLETE (2026-07-20): all three MVP cards verified** — HDFC Infinia
(closed 2026-07-19), Axis Atlas (closed 2026-07-19, 2 noted items), Amex
Platinum Travel (closed 2026-07-20, 1 residual open item). Next up: P2 in
listed order, starting with HDFC Diners Club Black.

### HDFC Infinia — status: FULLY VERIFIED, no open items (closed 2026-07-19, rules/seed/hdfc_infinia/v3.json)

Note (design decision, product owner + product strategist, 2026-07-19):
`point_value_reference_inr` is per-channel (cashback / voucher / travel);
confidence semantics per the ADR-001 amendment. Fee facts live in the new
`fees` and `continuation_eligibility` rule-file structures.

| Item | Where | Status |
|---|---|---|
| Base earn rate (5 RP / ₹150) | rules/seed/hdfc_infinia/v3.json | verified 2026-07-19 (official T&C PDF, confidence 0.95) |
| SmartBuy flights 5X + 15,000 RP/mo cap | rules/seed/hdfc_infinia/v3.json | verified 2026-07-19 (multiplier from SmartBuy public page, confidence 0.7; cap from T&C PDF) |
| SmartBuy hotels 10X + shared cap | rules/seed/hdfc_infinia/v3.json | verified 2026-07-19 (same sources/confidences) |
| SmartBuy brand vouchers 5X + 3,000 RP/mo cap (eff. 2026-07-01, subset of total) | rules/seed/hdfc_infinia/v3.json | verified 2026-07-19, confidence 0.85 (CardExpress + prior convergent sources). History: 3X devaluation announced Jan 2026, reversed Jan 14 2026; stable at 5X (16.5%). Earlier conflicting reports were both accurate at different times. |
| Category caps: grocery 2,000 / insurance 10,000 / utilities 2,000 / telecom 2,000 per month | rules/seed/hdfc_infinia/v3.json | verified 2026-07-19 (T&C PDF) |
| Statement-cycle max 200,000 RP; cashback redemption cap 50,000 RP/mo | rules/seed/hdfc_infinia/v3.json | verified 2026-07-19 (T&C PDF) |
| Full exclusion list (fuel, EasyEMI, e-wallet, rent/property/govt, education via third-party apps) | rules/seed + knowledge/sources | verified 2026-07-19 (T&C PDF) |
| Annual fee ₹12,500 + GST | rules/seed/hdfc_infinia/v3.json (fees) + portfolio fixture | verified 2026-07-19 (official fees page, confidence 0.95) |
| Renewal fee waiver at ₹10 lakh annual spend | rules/seed/hdfc_infinia/v3.json (fees) | verified 2026-07-19 (official page + CardExpress, confidence 0.8) |
| Continuation eligibility (₹18L spend OR ₹50L Relationship Value, eff. Apr 2027; existing holders protected to Mar 2027) | rules/seed/hdfc_infinia/v3.json (continuation_eligibility) | verified 2026-07-19 (news reports Feb 2026 + CardExpress + product owner, confidence 0.85) |
| Transfer ratios: Turkish Miles&Smiles / ALL Accor / Avianca LifeMiles 2:1 | database/seed/graph_edges.json | verified 2026-07-19 (T&C PDF clause 13, effective 2024-01-15, confidence 0.95) |
| Transfer ratio: Club ITC Green Points 2:1 (min 100, ×100, 2–4 working days) | database/seed/graph_edges.json | verified 2026-07-19 (product owner confirmed twice independently, confidence 0.85) |
| Transfer ratio: Singapore KrisFlyer 1:1 (via NetBanking, not SmartBuy) | database/seed/graph_edges.json | verified 2026-07-19 (product owner + multiple independent sources, confidence 0.8) |
| Transfer ratio: Marriott Bonvoy 2:1 (processes within 24h) | database/seed/graph_edges.json | verified 2026-07-19 (product-owner direct confirmation, confidence 0.8) |
| Transfer ratio: Air India Flying Returns 2:1 (promos can boost, not modeled) | database/seed/graph_edges.json | verified 2026-07-19 (product owner + 2 independent trackers, confidence 0.75) |
| Point values: cashback ₹0.30 / voucher ₹0.50 / travel ₹1.00 (Apple/Tanishq vouchers redeem at the ₹1.00 travel rate) | rules/seed/hdfc_infinia/v3.json | all three verified 2026-07-19 (2–4 independent agreeing sources each, confidence 0.8) |

### Axis Atlas — status: VERIFIED with 2 noted items (closed 2026-07-19, rules/seed/axis_atlas/v2.json)

**Noted items (recorded, not silently resolved):**
1. **Radisson Rewards ratio conflict (unresolved):** 1:2 recorded as primary
   (single detailed third-party guide citing specific mechanics, ~1 working
   day processing; confidence 0.65). An earlier community-forum source stated
   1:1 for the same partner — kept visible here, not discarded. Re-check on
   official/portal confirmation.
2. **Group B annual cap discrepancy:** official Axis T&C PDF states 120,000
   EDGE Miles/year (confidence 0.95, used everywhere); one source claimed
   1,200,000/year — recorded as a noted discrepancy (likely a typo in that
   source), official document treated as authoritative.

Also noted (low priority, does not affect reward/redemption math): interest
rate conflict — 3.75%/month vs 3.60%/month across two third-party sources, no
official source found; both candidates recorded here, neither picked, not
entered in the rule file or corpus.

| Item | Where | Status |
|---|---|---|
| Base earn 2 EDGE Miles / ₹100 (1/₹100 pre-2022-12-20 historical) | rules/seed/axis_atlas/v2.json | verified 2026-07-19 (official T&Cs PDF, 0.95) |
| Accelerated travel 5/₹100 (Travel EDGE + direct airline/hotel via MCC; OTAs base-only), ₹2L/mo spend cap (10,000-mile ceiling, derived), 12-day crediting | rules/seed/axis_atlas/v2.json | verified 2026-07-19 (official T&Cs PDF, 0.95) |
| Exclusions: gold/jewellery, rent, wallet, government, insurance, fuel, utilities, telecom (eff. 2024-04-20; rent/wallet milestone-only from 2023-03-05) | rules/seed + knowledge | verified 2026-07-19 (official T&Cs PDF, 0.95) |
| Point value: 1 EDGE Mile = ₹1, single official value (recorded across all three schema channels with an explanatory source; Atlas has no multi-channel structure) | rules/seed/axis_atlas/v2.json | verified 2026-07-19 (official T&Cs PDF, 0.95) |
| Welcome bonus by issuance cohort (2,500/1 txn/37d from 2024-04-20; 5,000/1 txn/30d 2022-12-20–2024-04-20; 5,000/3 txn/60d before; 7-day crediting, paid cards only) | rules/seed/axis_atlas/v2.json (welcome_bonus) | verified 2026-07-19 (official T&Cs PDF, 0.95) |
| Milestones: 2,500 @ ₹3L, +2,500 @ ₹7.5L, +5,000 @ ₹15L (30-day crediting) | rules/seed/axis_atlas/v2.json | verified 2026-07-19 (official T&Cs PDF, 0.95) |
| Tiers: Silver default / Gold ₹7.5L / Platinum ₹15L, downgrade rules, renewal bonus 0/2,500/5,000 (30 days from fee payment) | rules/seed/axis_atlas/v2.json (tiers) | verified 2026-07-19 (official T&Cs PDF, 0.95) |
| Annual fee ₹5,000 + GST | rules/seed/axis_atlas/v2.json (fees) | verified 2026-07-19 (official source, 0.9) |
| Renewal fee waiver: NONE exists (tiered renewal bonus offsets instead) | rules/seed/axis_atlas/v2.json (fees.notes; waiver field confirmed not applicable) | verified 2026-07-19 (0.8: 3 third-party sources + complaint thread; official T&C silent) |
| Forex markup 3.5% + GST (≈4.13% effective) | rules/seed/axis_atlas/v2.json (fees) | verified 2026-07-19 (2 third-party sources, 0.75) |
| Transfer caps: Group A 30,000/yr, Group B 120,000/yr, combined 150,000/yr per customer ID; min transfer 500 | database/seed/graph_edges.json (per-edge) | verified 2026-07-19 (official T&Cs PDF, 0.95) |
| Group A partners at 1:2 (11): KrisFlyer, Flying Returns, Aeroplan, JAL, Flying Blue, Club ITC, IHG, Etihad, United, Turkish, Thai | database/seed/graph_edges.json | verified 2026-07-19 (third-party convergent, 0.85; ratios live on the dynamic Travel EDGE page, not the static T&C — structural, not a research gap) |
| Group A newer additions at 2:1 (3): BA Avios, Finnair Plus, Vietnam Lotusmiles | database/seed/graph_edges.json | verified 2026-07-19 (4 independent sources, 0.8) |
| Group B: IndiGo BluChip 1:2 (promo window 2026-06-18–2026-08-17 noted) | database/seed/graph_edges.json | verified 2026-07-19 (IndiGo official site, 0.85) |
| Group B: Radisson Rewards 1:2 | database/seed/graph_edges.json | verified 2026-07-19 (0.65 — see noted item 1) |
| Group B: Orchid Rewards 1:1 | database/seed/graph_edges.json | verified 2026-07-19 (2 sources agreeing, 0.7) |
| Removed partners: Marriott Bonvoy, Accor, Qatar Privilege Club (2026-04-02; no edges; Qatar-via-Avios workaround not modeled) | knowledge doc | verified 2026-07-19 (4 sources agreeing on date, 0.8) |

### Amex Platinum Travel — status: VERIFIED, 1 residual open item (closed 2026-07-20, rules/seed/amex_plat_travel/v2.json)

**Residual open item:** renewal fee waiver policy — not covered by research
to date; field left `[NEED: verify from issuer docs]` rather than assumed
absent (unlike Axis, where "no waiver exists" was positively confirmed).

**Review flags:** (1) Reward Multiplier program validity ends 2026-07-31 —
renewal unconfirmed, re-verify as the date passes. (2) Transfer-partner and
statement-credit confidences carry a 0.7–0.75 ceiling reflecting the genuine
absence of an accessible India-specific official transfer portal (login-
gated) — same pattern as the toughest HDFC Infinia and Axis Atlas fields,
not a research gap. UK/EU International Currency Card pages were checked and
explicitly excluded as a different product/market.

Channel mapping note: statement credit → cashback channel; catalogue →
voucher channel (confirmed no single value — tiered rates live in
`redemption_catalogue`); partner transfer → travel channel (confirmed no
single value — partner-dependent).

| Item | Where | Status |
|---|---|---|
| Base earn 1 MR / ₹50 (India Platinum Travel; never merge with other Amex products) | rules/seed/amex_plat_travel/v2.json | verified 2026-07-20 (official pages, 0.9) |
| Exclusions: fuel, insurance, utilities, cash, EMI-at-POS (eff. 2020-03-15; SafeKey + post-purchase EMI still earn) | rules/seed + knowledge | verified 2026-07-20 (official, 0.95) |
| Welcome gift 10,000 MR (first year; ₹15,000 spend in 90 days AND fee payment) | rules/seed/amex_plat_travel/v2.json (welcome_bonus) | verified 2026-07-20 (official, 0.95) |
| Milestones: 7,500 @ ₹1.9L, 10,000 + ₹10,000 Taj E-Gift @ ₹4L, +22,500 @ ₹7L (recurring; Platinum Travel Collection; bonus auto-issue only post-2026-03-09, manual claim before — operational flag in notes) | rules/seed/amex_plat_travel/v2.json | verified 2026-07-20 (official, 0.95) |
| Reward Multiplier 3X (1X base + 2X bonus) via portal only; 25,000 bonus pts/mo cap; 120-business-day crediting; validity 2021-01-01→2026-07-31 | rules/seed/amex_plat_travel/v2.json | verified 2026-07-20 (official T&C, 0.95; per-merchant exclusions documented limitation) |
| Annual fee ₹5,000 + GST (same all years) | rules/seed/amex_plat_travel/v2.json (fees) | verified 2026-07-20 (official, 0.95) |
| Forex markup 3.5% + GST (≈4.4–4.5% effective, uniform across Amex India) | rules/seed/amex_plat_travel/v2.json (fees) | verified 2026-07-20 (3 trackers + cardholder-reported rate, 0.85) |
| Points expiry: never expires while active (eff. 2022-05-03); forfeit within 30 days on cancellation | rules/seed/amex_plat_travel/v2.json (points_expiry) | verified 2026-07-20 (official, 0.95) |
| Lounge: 8 domestic/yr (2/quarter); Priority Pass with US$99 fee waived | knowledge/sources/amex_plat_travel_benefit_guides.md | verified 2026-07-20 (official, 0.95) |
| Fuel convenience fee: 0% < ₹5,000 / 1% ≥ ₹5,000 at HPCL | knowledge/sources/amex_plat_travel_benefit_guides.md | verified 2026-07-20 (official, 0.95) |
| Eligibility: ₹6L income; 19 named issuance cities | knowledge/sources/amex_plat_travel_benefit_guides.md | verified 2026-07-20 (official, 0.95; informational, outside rule schema) |
| Point value — statement credit ₹0.25/pt (cashback channel) | rules/seed/amex_plat_travel/v2.json | verified 2026-07-20 (2 India-specific sources, 0.75) |
| Point value — catalogue tiers: Air India ₹0.30 / Taj ₹0.40 / Postcard ₹0.50 per pt | rules/seed/amex_plat_travel/v2.json (redemption_catalogue) | verified 2026-07-20 (official catalogue page, exact figures, 0.9) |
| Point value — transfer channel: no fixed value (partner-dependent, est. ₹1.50–3+) | rules/seed/amex_plat_travel/v2.json (travel channel = confirmed no single figure) | recorded 2026-07-20 |
| Transfer partners: KrisFlyer/Emirates/Cathay/Virgin 2:1 min 800; BA Avios 2:1 min 1,200; Qatar Avios 2:1 min 500; Marriott 1:1 min 100; Hilton 1:0.90 min 1,000; 900,000 MR/txn-or-year cap | database/seed/graph_edges.json | verified 2026-07-20 (CardTrail + Rivo + CardInsider convergence, 0.7) |
| Air India: NO transfer partner (Club Vistara removed post-merger, no replacement; no edge, no workaround) | knowledge doc; no edge/register entry | verified 2026-07-20 |

## P2 — MVP portfolio scope (added 2026-07-19)

Seven additional cards are portfolio-trackable but unverified: rule seeds
(`rules/seed/<card_key>/v1.json`, all null/unverified per-channel schema),
knowledge skeletons, and card nodes exist; the engines refuse to compute for
them ("reward rules for <card> are not yet verified") until verification
lands. Verification order post-launch (after P1 completes, one issuer fully
before the next):

| # | Card | card_key | Status |
|---|---|---|---|
| 1 | HDFC Diners Club Black | hdfc_diners_black | not_started (as of 2026-07-19) |
| 2 | HDFC Regalia | hdfc_regalia | not_started (as of 2026-07-19) |
| 3 | Amex Platinum Reserve | amex_plat_reserve | not_started (as of 2026-07-19) |
| 4 | Amex Membership Rewards Credit Card | amex_membership_rewards | not_started (as of 2026-07-19) |
| 5 | Amex SmartEarn | amex_smartearn | not_started (as of 2026-07-19) |
| 6 | Axis Ace | axis_ace | not_started (as of 2026-07-19) |
| 7 | Axis Magnus | axis_magnus | not_started (as of 2026-07-19) |

Per-card open items (all `[NEED: verify from issuer docs]`): reward program
identity, base earn rate + block, accelerated categories/multipliers/caps,
milestones, exclusions, transfer partners + ratios, per-channel point
values, annual fee + waiver.

## P3 (roadmap)

| Card / issuer | Status |
|---|---|
| SBI Cashback | not_started (as of 2026-07-19, moved from old P2) |
| HSBC Live+ | not_started (as of 2026-07-19, moved from old P2) |
| ICICI (card set TBD) | not_started (as of 2026-07-19) |
| AU Small Finance (card set TBD) | not_started (as of 2026-07-19) |
| Yes Bank (card set TBD) | not_started (as of 2026-07-19) |

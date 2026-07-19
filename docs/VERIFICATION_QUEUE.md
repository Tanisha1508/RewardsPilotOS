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

**Next card: Axis Atlas** (one issuer completed fully before the next).

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

### Axis Atlas — status: not_started, NEXT UP (as of 2026-07-19)

| Item | Where | Status |
|---|---|---|
| Base EDGE Miles earn rate | rules/seed/axis_atlas/v1.json | not_started |
| Accelerated travel rate + monthly cap | rules/seed/axis_atlas/v1.json | not_started |
| Milestone tiers (thresholds + bonuses) | rules/seed/axis_atlas/v1.json | not_started |
| Exclusion list | rules/seed + knowledge/sources | not_started |
| Point value reference (INR) | rules/seed/axis_atlas/v1.json | not_started |
| Transfer partners + ratios + minimums | database/seed/need_register.json (air_india, krisflyer candidates) | not_started |
| Annual fee + waiver | tools/portfolio fixture → cards table | not_started |

### Amex Platinum Travel — status: not_started (as of 2026-07-19)

| Item | Where | Status |
|---|---|---|
| Base Membership Rewards earn rate | rules/seed/amex_plat_travel/v1.json | not_started |
| Milestone 1 threshold + bonus | rules/seed/amex_plat_travel/v1.json | not_started |
| Milestone 2 threshold + bonus + voucher | rules/seed/amex_plat_travel/v1.json | not_started |
| Exclusion list | rules/seed + knowledge/sources | not_started |
| Point value reference (INR) | rules/seed/amex_plat_travel/v1.json | not_started |
| Transfer partners + ratios + minimums | database/seed/need_register.json (air_india, krisflyer, marriott candidates) | not_started |
| Annual fee | tools/portfolio fixture → cards table | not_started |

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

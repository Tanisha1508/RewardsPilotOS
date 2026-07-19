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

### HDFC Infinia — status: mostly verified (as of 2026-07-19, rules/seed/hdfc_infinia/v2.json)

Note (design decision, product owner + product strategist, 2026-07-19):
`point_value_reference_inr` is now **per-channel** (cashback / voucher /
travel) across the schema — a point's rupee value depends on how it is
redeemed. Confidence semantics also updated (ADR-001 amendment): unverified
values may carry a candidate value with evidence confidence < 1; they remain
non-computable.

| Item | Where | Status |
|---|---|---|
| Base earn rate (5 RP / ₹150) | rules/seed/hdfc_infinia/v2.json | verified 2026-07-19 (official T&C PDF, confidence 0.95) |
| SmartBuy flights 5X + 15,000 RP/mo cap | rules/seed/hdfc_infinia/v2.json | verified 2026-07-19 (multiplier from SmartBuy public page, confidence 0.7 — not Infinia-login-specific; cap from T&C PDF) |
| SmartBuy hotels 10X + shared cap | rules/seed/hdfc_infinia/v2.json | verified 2026-07-19 (same sources/confidences) |
| SmartBuy brand vouchers 5X + 3,000 RP/mo cap (eff. 2026-07-01, subset of total) | rules/seed/hdfc_infinia/v2.json | verified 2026-07-19 (resolved-by-convergence: SmartBuy page + T&C PDF + product owner; supersedes Business Standard Jan 2026 3X claim) |
| Category caps: grocery 2,000 / insurance 10,000 / utilities 2,000 / telecom 2,000 per month | rules/seed/hdfc_infinia/v2.json | verified 2026-07-19 (T&C PDF) |
| Statement-cycle max 200,000 RP; cashback redemption cap 50,000 RP/mo | rules/seed/hdfc_infinia/v2.json | verified 2026-07-19 (T&C PDF) |
| Full exclusion list (fuel, EasyEMI, e-wallet, rent/property/govt, education via third-party apps) | rules/seed + knowledge/sources | verified 2026-07-19 (T&C PDF) |
| Transfer ratios: Turkish Miles&Smiles / ALL Accor / Avianca LifeMiles 2:1 | database/seed/graph_edges.json | verified 2026-07-19 (T&C PDF clause 13, effective 2024-01-15) |
| Transfer ratio: Club ITC Green Points 2:1 (min 100, ×100, 2–4 working days) | database/seed/graph_edges.json | verified 2026-07-19 (product-owner confirmation, confidence 0.7 — cross-check against an official page still open) |
| KrisFlyer ratio (candidate 1:1) | database/seed/need_register.json | [NEED] official confirmation — third-party aggregators only |
| Marriott Bonvoy ratio (candidate 2:1) | database/seed/need_register.json | [NEED] official confirmation — third-party aggregators only |
| Air India Flying Returns ratio | database/seed/need_register.json | [NEED] entirely unconfirmed — ratio not found in any source |
| Point value per channel: cashback ₹0.30 / voucher ₹0.50 / travel ₹1.00 | rules/seed/hdfc_infinia/v2.json | [NEED] all three are unverified estimates (third-party / inferred) pending official confirmation; travel is the weakest (confidence 0.4) |
| Annual fee + waiver | tools/portfolio fixture → cards table | not_started |

### Axis Atlas — status: not_started (as of 2026-07-19)

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

## P2 (post-MVP fast follow)

| Card | Status |
|---|---|
| HDFC Diners Black | not_started (as of 2026-07-19) |
| SBI Cashback | not_started (as of 2026-07-19) |
| HSBC Live+ | not_started (as of 2026-07-19) |

## P3 (roadmap)

| Issuer | Status |
|---|---|
| ICICI (card set TBD) | not_started (as of 2026-07-19) |
| AU Small Finance (card set TBD) | not_started (as of 2026-07-19) |
| Yes Bank (card set TBD) | not_started (as of 2026-07-19) |

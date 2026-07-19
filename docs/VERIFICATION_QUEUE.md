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

### HDFC Infinia — status: not_started (as of 2026-07-19)

| Item | Where | Status |
|---|---|---|
| Base earn rate + per_amount block | rules/seed/hdfc_infinia/v1.json | not_started |
| SmartBuy flights multiplier + cap | rules/seed/hdfc_infinia/v1.json | not_started |
| SmartBuy hotels multiplier + cap | rules/seed/hdfc_infinia/v1.json | not_started |
| SmartBuy total monthly cap | rules/seed/hdfc_infinia/v1.json | not_started |
| Full exclusion list | rules/seed + knowledge/sources | not_started |
| Point value reference (INR) | rules/seed/hdfc_infinia/v1.json | not_started |
| Transfer partners + ratios + minimums | database/seed/need_register.json (air_india, krisflyer, marriott candidates) | not_started |
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

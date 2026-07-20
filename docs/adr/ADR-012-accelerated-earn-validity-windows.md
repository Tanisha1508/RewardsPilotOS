# ADR-012: Validity Windows on Accelerated Earn

## Status

Accepted (2026-07-20). Closes KNOWN_LIMITATIONS item 10.

## Context

`AcceleratedEarn` had no date fields. A program's published start and end dates
were recorded in the entry's `notes` prose, where the evaluator cannot read
them, so an accelerated rate applied forever once written.

This was the one open case where the engine could compute with a rate it had no
right to use, rather than returning unknown. The concrete instance was dated:
Amex Platinum Travel's Reward Multiplier is published as valid 2021-01-01 to
**2026-07-31**. From 2026-08-01 the engine would have kept applying 3X — a
silently wrong number, produced from a field that was itself correctly
verified, with no signal to the user that anything had lapsed.

It is a distinct failure class from ADR-010 and ADR-011. Those were matching
bugs, wrong the moment they ran. This one is *correct today and wrong later*:
no test written on the day the data was verified can fail, because the bug is
scheduled rather than present. The test that catches it has to move the clock.

## Decision

Add optional `valid_from` / `valid_until` ISO dates to `AcceleratedEarn`, and
enforce them in `rules/evaluator/validity.py`.

**Monthly resolution.** `EarnResult` is keyed by `month` ("YYYY-MM"), not by
transaction date, so an entry is active when its window overlaps the queried
month at all. A program ending 2026-07-31 applies for all of 2026-07 and stops
at 2026-08. Enforcing at day resolution would require a transaction-date input
the tool contract does not have, and month granularity is what the rest of the
card model already works in — monthly caps, `cap_usage` keyed by month. Adding
day precision here alone would be precision the surrounding system cannot
honour.

The edge this leaves: a window boundary falling *mid*-month. A `valid_until` of
the 15th applies the accelerated rate for that whole month, over-crediting
spend after the 15th — the wrong error direction under "unknown over
incorrect". A mid-month `valid_from` under-credits, which is the safe
direction. This is latent rather than live: Amex's end date is a month
boundary, and no other seed entry declares dates. Should a mid-month window
ever appear, the honest fix is to treat the partial month as unknown rather
than to guess which side of the boundary the spend fell on.

**Both bounds, and both optional.** `None` means unbounded on that side, so
entries with no published window behave exactly as before — the change is inert
for every card that does not declare dates. A future-dated entry applying early
is the same bug in the other direction, so `valid_from` is enforced too.

**Lapsing falls back to base earn, not to unknown.** A lapsed entry means "this
number was true and its window has closed". The base rate is still verified, so
discarding it would throw away something we do know. The result computes at base
rate and carries a new `expiry_note` on `EarnResult`: deterministic text naming
the expiry date, stating that base earn was used, and asking for
re-verification. Because it rides on the tool result it is inside the
Recommender's grounded text, so the model can repeat the date verbatim without
inventing it.

**The note is enforced, not requested.** Recommender prompt rule 9 asks for it,
but `validate_recommendation` requires it verbatim in `decision` or `reasoning`
— the same gate the winning-margin caveat goes through, and for the same
reason: a prompt instruction is not a guarantee, and reporting the lower number
without the reason shows a card quietly getting worse with no explanation.
`required_statement` accordingly accepts several statements rather than one.

**A lapsed rate caps confidence at medium.** Nothing else in `calibration.py`
would notice it — the computation is clean and every source is verified — but
the figure may understate the card if the program was quietly renewed. That
uncertainty is exactly what confidence is for.

## Consequences

**Positive.** The engine can no longer compute with a lapsed rate. The Amex
deadline stops being a calendar reminder for a human and becomes engine
behaviour: on 2026-08-01 the number changes on its own and says why.

**A card can now drop in a comparison for a reason unrelated to its rules.**
This is intended and is stated in the answer rather than being silent. The card
stays in the comparison carrying the reason; a lower number with a stated cause
is the honest output.

**Values changed.** Only for Amex Platinum Travel on `reward_multiplier`
queries dated 2026-08 or later. Nothing else in the seed data declares dates.
Regression cover in `tests/rules/test_validity.py`, including the dated case
(2026-08 must return base earn plus an expiry note) and a check that the other
two P1 cards are untouched.

**`compare_cards(month=...)` now matters more.** Its epoch default
("1970-01") predates every program, so a caller omitting `month` would lose
every dated accelerated rate. No caller omits it; the default is documented as
a hazard rather than changed, since the signature is a spec'd contract.

**Still not modeled: mid-window rate changes.** One entry carries one
multiplier. A program that changed its rate inside its window needs two
entries with adjacent windows — which the schema now expresses, but no seed
data uses yet.

## Alternatives rejected

**Parse dates out of `notes`.** Prose is not a contract; a reworded note would
silently disable enforcement.

**Return `unknown` when a rate lapses.** Overstates the damage. The base rate
is verified and the honest answer is "you earn base here, and this accelerated
rate needs re-checking", not "we cannot tell you anything".

**Leave it to the crawler to catch renewals.** The crawler is not wired (D3/D5)
and, more fundamentally, the engine should be safe when its data is stale
rather than depending on data always being fresh.

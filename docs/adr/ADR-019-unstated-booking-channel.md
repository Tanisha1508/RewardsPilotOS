# ADR-019: An Unstated Booking Channel Must Be Stated

## Status

Accepted (2026-07-28). Found in live production testing, not by a test.

## Context

`_matching()` in `rules/evaluator/evaluator.py` opens with `if channel is None:
return None`. No channel supplied means no accelerated entry can match, so
every card falls to base earn. That behaviour is correct and deliberate — the
evaluator will not assume where a purchase happens — and it is the same
"unknown over incorrect" instinct as the rest of the engine.

It was also completely silent, and silence is what made it a defect.

The live symptom, on the deployed app on 2026-07-28: *"Which of my cards is
best for a Rs 50,000 flight booking?"* returned

| card | points | applied |
|---|---|---|
| hdfc_infinia | 1665 | base |
| axis_atlas | 1000 | base |
| amex_plat_travel | 1000 | base |

— recommending HDFC Infinia at **high confidence**. Booking that same flight
direct with the airline earns axis_atlas 2500 (its `direct`/`travel` entry at
2.5x), which reverses the winner outright.

Nothing was fabricated, no arithmetic was wrong, and every source was verified.
The answer simply turned on a question nobody had asked, and reported itself as
settled.

This is a third failure class, distinct from its neighbours. ADR-010 and
ADR-011 were *matching* bugs — the query and the rule file described the same
thing in different vocabularies, and the fix was a translation table. ADR-012
was *scheduled* — correct today, wrong later. This one is neither: the
computation is right, permanently, and the reporting is wrong. No matching
table or clock would catch it, because there is nothing to match and nothing to
expire. What is missing is an input, and the system's mistake was treating a
missing input as a settled one.

Worth recording: the same query produced axis_atlas 2500 during the 2026-07-23
deploy gate, because the Planner happened to resolve a channel that time. The
LLM's argument resolution is not deterministic, so the recommendation could
swing between two different cards across runs of an identical question, with
nothing in either answer disclosing why. Pinning the Planner would not fix
this — the honest answer genuinely depends on the channel, and the user is the
only one who knows it.

## Decision

Say so. Three enforced layers, each mirroring an existing mechanism rather than
introducing a new one.

**The engine emits a per-card `channel_note`.** `find_channel_dependent()`
returns the accelerated entries that *would* have applied had a channel been
named. When it returns anything, `EarnResult.channel_note` carries deterministic
text naming the issuer's own channels, exactly as `expiry_note` (ADR-012)
carries the expiry date. Because it rides on the tool result it sits inside the
Recommender's grounded text, so the model repeats the channel names without
inventing them.

Two exclusions keep the note from leading nowhere:

- *Only when no channel was supplied.* A stated channel that earns base is an
  answer, not a gap — the user told us where they are buying.
- *Only entries in force in the queried month.* Pointing a user at a channel
  whose rate has lapsed would be worse than saying nothing. This composes with
  ADR-012 rather than duplicating it.

**It caps confidence at medium.** Nothing else in `calibration.py` would notice:
the computation is clean and every source verified, so the ceiling would sit at
high. A ranking that depends on an unasked question is not a high-confidence
ranking, and confidence is the field that is supposed to carry exactly this.

**It is enforced, not requested.** Recommender prompt rule 10 asks for the note;
`validate_recommendation` requires it verbatim in `decision` or `reasoning`.
Same gate as the winning-margin caveat and the expiry note, for the same reason
— a model asked to volunteer an inconvenient caveat will often decline, and this
particular caveat is the difference between "HDFC Infinia is your best card" and
"...unless you book direct, where Axis Atlas earns 2500".

## Consequences

**Positive.** A channel-dependent ranking can no longer present itself as
settled. The user is told which channels would change the answer, in the
issuer's own vocabulary, and can resolve it themselves.

**The note fires broadly, including where the channel is implausible.** Axis's
`travel_edge` entry and Amex's `reward_multiplier` entry are both declared
`category: "all"`, so an electronics query is flagged for a *travel* portal.
This is accepted deliberately. Narrowing it would mean encoding which categories
each portal actually sells — an issuer policy that appears in no rule file and
that we would be inventing, which the hard rules forbid outright. Suppressing
`category: "all"` instead would silence Amex's only accelerated entry
completely, on every category including flights. A slightly noisy caveat is the
cheaper error than a missing one. Pinned in
`tests/rules/test_channel_note.py::test_a_category_all_portal_entry_flags_any_category`
so it reads as a decision rather than an oversight.

**No computed value changed.** This ADR adds no rate, cap, multiplier or
matching rule; `points` and `applied` are byte-identical before and after. Only
`channel_note`, the confidence ceiling, and the required statements move. The
one visible change is that some answers previously reported "high" now report
"medium" — which was the defect, not a regression.

**Eval and test doubles had to learn the note.** `EvalLLM` and the scripted LLM
in `tests/integration/test_card_key_mapping.py` now reproduce engine notes
verbatim. A double that omits them fails validation on every triggering query,
which measures the double rather than the system.

## Alternatives rejected

**Default the channel to `direct`.** Guessing where someone shops, and the
wrong guess inflates the winner. This is the exact failure the `channel is
None` guard exists to prevent.

**Pin the Planner to always resolve a channel.** Makes the output stable and
still wrong: the model would be inventing the user's shopping behaviour, and
consistency is not accuracy.

**Return `unknown` instead of base earn.** Overstates the damage. The base rate
is verified and "you earn at least this, and where you book can change it" is a
real answer; "we cannot tell you anything" is not.

**Ask the user a clarifying question instead of answering.** The better product
answer, and out of scope here — the chat contract is single-turn and adding a
turn is a spec change, not an implementation detail. The note names exactly what
would need to be asked, so this remains open as a follow-up.

**Leave it to the prompt.** Tried by the surrounding system twice already
(ADR-012, the margin caveat) and rejected both times for the same reason.

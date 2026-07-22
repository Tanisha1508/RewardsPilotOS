"""Resolve tool args that come from the user's *data* rather than their words.

A required tool argument has one of three sources: the user's query, the user's
portfolio, or the runtime. Only the first belongs in the LLM's output. This
module covers the second.

The failure it prevents (KNOWN_LIMITATIONS 24, Class B of the 2026-07-22 tool
schema audit): `card_key` is internal catalogue vocabulary — `hdfc_infinia`,
not "my HDFC card". A model asked for one either invents a plausible string or,
correctly, emits nothing. Neither works: an invented key fails the rule lookup,
and a missing one is rejected by `validate_plan`. Either way the invocation is
dropped and the answer ships with no computed numbers, which is exactly the D4
`cards=[]` bug — the same defect had already been fixed for `CompareCards`
alone, so the next tool needing a card key reproduced it.

Two shapes, one rule:

- `CompareCards` takes a *list*, so it gets every held card that resolves.
- `CalculateEarn` and `CheckCap` take a *single* card, so an unresolved one
  fans out into one invocation per held card. That is the faithful analogue of
  the list case rather than a new policy: "the cards you hold" is the same
  answer either way, and picking just one card for the user would be the
  system choosing on their behalf with nothing to choose on.

An explicit `card_key` from the model is always respected — if it named a card,
that is a real signal from the query ("how much on my Atlas?") and overriding it
would discard the user's actual question. A card with no `card_key` (synthetic,
or not in the verified catalogue) is omitted: it cannot be computed. If nothing
resolves, the invocation is dropped rather than guessed at, and the recommender
degrades honestly.

Deliberately NOT resolved here — these need a design decision, not a default:

- `GetTransferRatios.currency`, `BestTransferPaths.currency` — the user may
  hold several reward currencies, and "which balance did they mean?" has no
  mechanical answer. Fanning out over every currency would silently reinterpret
  the question rather than answer it.
- `BestTransferPaths.target_program`, `RedemptionOptions.goal.target_program` —
  a destination program is not portfolio data at all. It comes from the query
  or from a stated goal, and inventing one would manufacture an intent the user
  never expressed.
- `CheckCap.cap_scope` — rule-file vocabulary (`reward_multiplier_bonus`) with
  no portfolio source. It also fails *silently*: an unrecognised scope returns
  `status: success` with an unknown cap, which reads as "checked, nothing
  there" rather than "asked the wrong question".

Those stay open and documented rather than resolved by guess, because a wrong
answer that looks computed is worse than a stated unknown.
"""

from contracts.tools.portfolio import Card

# Tools taking one card_key, which fan out over held cards when unresolved.
SINGLE_CARD_TOOLS = ("CalculateEarn", "CheckCap")


def resolve_portfolio_args(plan: list, cards: list[Card]) -> list:
    """Fill portfolio-derived args on the *raw* plan, before schema validation.

    Order matters: validation rejects a missing or empty card argument, so
    injection has to happen first or the invocation is already gone (the D4
    inject-before-validate lesson).
    """
    keys = [card.card_key for card in cards if card.card_key]
    resolved: list = []
    for invocation in plan:
        if not isinstance(invocation, dict):
            resolved.append(invocation)  # malformed; validation reports it
            continue
        tool = invocation.get("tool")
        args = invocation.get("args") or {}

        if tool == "CompareCards":
            if not keys:
                continue  # nothing to compare; dropped rather than guessed
            resolved.append({**invocation, "args": {**args, "cards": keys}})
        elif tool in SINGLE_CARD_TOOLS:
            if args.get("card_key"):
                resolved.append(invocation)  # the model named a card; respect it
                continue
            if not keys:
                continue
            resolved.extend({**invocation, "args": {**args, "card_key": key}} for key in keys)
        else:
            resolved.append(invocation)
    return resolved

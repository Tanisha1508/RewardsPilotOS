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

Three shapes, one rule — the resolved value is "the ones you hold":

- `CompareCards` takes a *list* of card_keys, so it gets every held card that
  resolves.
- `CalculateEarn` and `CheckCap` take a *single* card_key, so an unresolved one
  fans out into one invocation per held card. That is the faithful analogue of
  the list case rather than a new policy: "the cards you hold" is the same
  answer either way, and picking just one card for the user would be the
  system choosing on their behalf with nothing to choose on.
- `GetTransferRatios` and `BestTransferPaths` take a single `currency`, which is
  the same shape one level out: a reward currency is not something the user says
  ("KrisFlyer" is a *destination*, not their source), it is the currency of a
  card they hold. An unresolved one fans out over the held cards' reward
  currencies — "which of my currencies transfers?" answered across all of them,
  exactly as `RedemptionOptions` already does internally when it loops the
  portfolio. This closes the last mechanical member of Class B (audit
  2026-07-22, resolved 2026-07-23).

An explicit value from the model is always respected — if it named a card
("how much on my Atlas?") or a currency ("my HDFC points"), that is a real
signal from the query and overriding it would discard the user's actual
question.

For `card_key`, a card with no key (synthetic, or not in the verified
catalogue) is omitted: it cannot be computed. For `currency`, every held reward
currency is included — the transfer graph itself decides what is registered and
reports the rest as `no_transfer_data`, so there is no need to pre-filter here.
If nothing resolves, the invocation is dropped rather than guessed at.

Deliberately NOT resolved here — genuinely query-derived or vocabulary, not
portfolio data, so a default would manufacture an intent the user never stated:

- `BestTransferPaths.target_program`, `RedemptionOptions.goal.target_program` —
  a destination program comes from the query or a stated goal, never from the
  portfolio. When the query names none, the honest floor is the tool's
  `unresolved_input` signal; enumerating reachable destinations would be a
  useful feature but is a separate design surface (KNOWN_LIMITATIONS 27), not a
  default to bolt on here.
- `CheckCap.cap_scope` — rule-file vocabulary (`reward_multiplier_bonus`) with
  no portfolio source.

Those stay open and documented rather than resolved by guess, because a wrong
answer that looks computed is worse than a stated unknown.
"""

from contracts.tools.portfolio import Card

# Tools taking one card_key, which fan out over held cards when unresolved.
SINGLE_CARD_TOOLS = ("CalculateEarn", "CheckCap")
# Tools taking one source `currency`, which fan out over the held cards' reward
# currencies when unresolved — same pattern as SINGLE_CARD_TOOLS, one level out.
CURRENCY_TOOLS = ("GetTransferRatios", "BestTransferPaths")


def _dedup(values: list[str]) -> list[str]:
    """Preserve first-seen order while dropping duplicates — two cards sharing a
    reward currency should fan out to one invocation, not two."""
    seen: dict[str, None] = {}
    for value in values:
        seen.setdefault(value, None)
    return list(seen)


def resolve_portfolio_args(plan: list, cards: list[Card]) -> list:
    """Fill portfolio-derived args on the *raw* plan, before schema validation.

    Order matters: validation rejects a missing or empty card/currency argument,
    so injection has to happen first or the invocation is already gone (the D4
    inject-before-validate lesson).
    """
    keys = [card.card_key for card in cards if card.card_key]
    # Every held reward currency (not filtered by card_key): the transfer graph
    # decides what is registered, so a synthetic-but-transferable currency like
    # voyager_points still belongs here.
    currencies = _dedup([card.reward_currency for card in cards if card.reward_currency])
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
        elif tool in CURRENCY_TOOLS:
            if args.get("currency"):
                resolved.append(invocation)  # the model named a currency; respect it
                continue
            if not currencies:
                continue
            resolved.extend(
                {**invocation, "args": {**args, "currency": currency}} for currency in currencies
            )
        else:
            resolved.append(invocation)
    return resolved

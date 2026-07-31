"""A card's `reward_currency` must name a currency, not something that merely
looks like one (B1, closing KNOWN_LIMITATIONS 31).

The defect this exists to prevent, in full: the transfer graph holds

    membership_rewards        node_type: currency   8 outgoing transfer edges
    amex_membership_rewards   node_type: card       0 edges

Not duplicates — a currency and a card with near-identical names. A seed script
set Amex Platinum Travel's `reward_currency` to the *card* id. Transfer lookups
start from that id, found a node with no outgoing edges, and returned nothing.
Which is indistinguishable, from the outside, from a card that genuinely has no
transfer partners. Silence that looks like an answer, which is the failure mode
this whole product is organised against.

`reward_currency` was a free-text column: any string was accepted, and a
*wrong-but-real* node id failed silently. The frontend quick-add catalogue was
fixed and covered by a regression test, but that only guards the three
catalogued cards — a hand-typed card could still do it.

Validating here rather than in the Pydantic schema is deliberate. The valid set
is not a fixed enum; it is whatever currency nodes the transfer graph currently
holds, which grows as issuers are added. A schema would have to be edited every
time the graph is, and would drift.
"""

from functools import lru_cache

from backend.application.errors import InvalidReferenceError


@lru_cache(maxsize=1)
def known_currencies() -> frozenset[str]:
    """Currency node ids in the transfer graph.

    Cached: the seed graph is read from disk and does not change within a
    process. `cache_clear()` is available to tests that build a different graph.
    """
    from graph.builder.builder import load_seed_graph

    graph = load_seed_graph()
    return frozenset(
        node for node, data in graph.nodes(data=True) if data.get("node_type") == "currency"
    )


def validate_reward_currency(reward_currency: str) -> None:
    """Reject a value that names a node of the *wrong type*. Allow one that
    names no node at all.

    That asymmetry is the whole design, and the first version of this got it
    wrong by rejecting anything absent from the graph. The integration suite
    caught it: `test_a_new_issuer_needs_no_code_change` and
    `test_card_whose_currency_is_not_in_the_graph_reports_missing_data` both add
    a card for an issuer the system has never heard of, and both are protecting
    something deliberate — a card the engines cannot reason about is *supposed*
    to be addable, and to produce "there is no data for this" rather than a
    refusal or a guess. The graph holds five currencies; rejecting everything
    else would have locked the product to those five and turned a documented
    honest-unknown path into a dead end.

    So the rule is narrow, and matches the actual defect:

      `membership_rewards`       currency  → fine
      `amex_membership_rewards`  card      → rejected. A real id, wrong kind of
                                             thing, and transfers from it find
                                             nothing while looking like an answer
      `newbank_altitude_miles`   unknown   → allowed. We simply have no data,
                                             and every engine says so honestly

    Only the middle case can produce silence that resembles an answer, and only
    the middle case is refused.
    """
    if reward_currency in known_currencies():
        return

    from graph.builder.builder import load_seed_graph

    node_type = load_seed_graph().nodes.get(reward_currency, {}).get("node_type")
    if node_type is None:
        return  # unknown to the graph — honest-unknown territory, not an error

    options = ", ".join(sorted(known_currencies()))
    raise InvalidReferenceError(
        f"'{reward_currency}' is a {node_type}, not a reward currency. "
        f"Transfers are looked up from the currency, so a card pointed here would "
        f"silently find no transfer options rather than reporting none. "
        f"Did you mean one of: {options}?"
    )

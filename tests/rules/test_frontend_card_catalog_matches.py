"""The frontend's quick-add catalogue must keep resolving (2026-07-29).

`frontend/app/cards/page.tsx` hard-codes the three supported cards so a user can
add one without typing `hdfc_reward_points` by hand — a free-text field where one
typo produced a card that tracked fine and silently computed nothing.

Hand-written to match, per the project's no-codegen convention for API types.
That convention needs a guard, or the two drift quietly: rename a card in
`rules/parser/catalog.py` and the button keeps sending the old name, resolving
`card_key` to None with no error anywhere.

This test reads the actual TSX rather than restating the pairs, so it fails when
either side moves.
"""

import json
import re
from pathlib import Path

from rules.parser.catalog import resolve_card_key

PAGE = Path(__file__).resolve().parents[2] / "frontend" / "lib" / "known-cards.ts"


def _frontend_catalog() -> list[dict[str, str]]:
    """Parse the KNOWN_CARDS literal out of the page."""
    source = PAGE.read_text()
    block = re.search(r"export const KNOWN_CARDS = \[(.*?)\] as const;", source, re.S)
    assert block, "KNOWN_CARDS literal not found — was frontend/lib/known-cards.ts restructured?"

    entries = []
    for chunk in re.findall(r"\{(.*?)\}", block.group(1), re.S):
        entry = dict(re.findall(r'(\w+):\s*"([^"]*)"', chunk))
        if entry:
            entries.append(entry)
    return entries


def test_every_quick_add_card_resolves_to_a_card_key():
    """The whole point of the buttons: they cannot produce an unrecognised card."""
    catalog = _frontend_catalog()
    assert catalog, "no cards parsed from KNOWN_CARDS"

    for entry in catalog:
        resolved = resolve_card_key(entry["issuer"], entry["card_name"])
        assert resolved is not None, (
            f"quick-add card {entry['label']!r} sends "
            f"({entry['issuer']!r}, {entry['card_name']!r}), which "
            f"rules/parser/catalog.py does not resolve — the button would create "
            f"a card the engine cannot compute for"
        )


def test_quick_add_reward_currencies_match_the_rule_files():
    """`reward_currency` must match the rule file exactly."""
    seed = Path(__file__).resolve().parents[2] / "rules" / "seed"

    for entry in _frontend_catalog():
        card_key = resolve_card_key(entry["issuer"], entry["card_name"])
        versions = sorted((seed / card_key).glob("v*.json"))
        rule = json.loads(versions[-1].read_text())

        assert entry["reward_currency"] == rule["reward_currency"], (
            f"{entry['label']}: frontend sends {entry['reward_currency']!r}, "
            f"rule file declares {rule['reward_currency']!r}"
        )


def test_currency_labels_match_the_graph_node_names():
    """`frontend/lib/display.ts` hand-mirrors the currency nodes' display names,
    so the UI can show "Axis EDGE Miles" instead of `edge_miles`. Derivation is
    not an option — title-casing gives "Edge Miles", which is not the programme's
    name — so the labels are looked up and must be kept in step.

    Synthetic fixture currencies must NOT be listed: they should never reach a
    real user, and showing the raw id makes it obvious when one does.
    """
    display = (Path(__file__).resolve().parents[2] / "frontend" / "lib" / "display.ts").read_text()
    block = re.search(r"CURRENCY_LABELS: Record<string, string> = \{(.*?)\};", display, re.S)
    assert block, "CURRENCY_LABELS literal not found in frontend/lib/display.ts"
    labels = dict(re.findall(r'(\w+):\s*"([^"]*)"', block.group(1)))
    assert labels, "no currency labels parsed"

    nodes = json.loads(
        (Path(__file__).resolve().parents[2] / "database" / "seed" / "graph_nodes.json").read_text()
    )
    nodes = nodes if isinstance(nodes, list) else nodes.get("nodes", nodes)
    by_id = {n.get("node_id") or n.get("id"): n for n in nodes}

    for currency, label in labels.items():
        node = by_id.get(currency)
        assert node is not None, f"{currency!r} is labelled but is not a graph node"
        assert node.get("node_type") == "currency", f"{currency!r} is not a currency node"
        assert (
            node.get("name") == label
        ), f"{currency}: frontend shows {label!r}, graph node says {node.get('name')!r}"
        assert (
            "SYNTHETIC" not in label
        ), f"{currency}: a synthetic fixture currency must not be given a friendly label"


def test_quick_add_currencies_are_currency_nodes_not_card_nodes():
    """The bug this test was written for (2026-07-29).

    A portfolio card's `reward_currency` is the *source node* for transfer
    lookups, so it must name a `currency` node. `infra/scripts/seed_demo_portfolio.py`
    used "amex_membership_rewards" — which IS a real node id, but a **card**
    node (the P2 skeleton "American Express Membership Rewards Credit Card")
    with zero outgoing edges. The correct currency node is "membership_rewards",
    which carries all 8 Amex transfer edges.

    Nothing rejected it: the value resolved to a node, just the wrong kind, so
    Amex transfer questions returned no paths and looked like a card with no
    transfer options rather than a mis-linked card.
    """
    nodes = json.loads(
        (Path(__file__).resolve().parents[2] / "database" / "seed" / "graph_nodes.json").read_text()
    )
    nodes = nodes if isinstance(nodes, list) else nodes.get("nodes", nodes)
    by_id = {n.get("node_id") or n.get("id"): n for n in nodes}

    for entry in _frontend_catalog():
        currency = entry["reward_currency"]
        node = by_id.get(currency)
        assert node is not None, f"{entry['label']}: {currency!r} is not a graph node at all"
        assert node.get("node_type") == "currency", (
            f"{entry['label']}: {currency!r} is a {node.get('node_type')!r} node, not a currency. "
            f"Transfer lookups start from this id, so a card node yields no paths."
        )


def _pending_cards() -> list[dict[str, str]]:
    """The locked list the UI shows but will not let anyone add."""
    source = PAGE.read_text()
    block = re.search(r"export const PENDING_CARDS = \[(.*?)\] as const;", source, re.S)
    assert block, "PENDING_CARDS literal not found in frontend/lib/known-cards.ts"
    return [
        entry
        for chunk in re.findall(r"\{(.*?)\}", block.group(1), re.S)
        if (entry := dict(re.findall(r'(\w+):\s*"([^"]*)"', chunk)))
    ]


def _base_rate_status(card_key: str) -> str:
    seed = Path(__file__).resolve().parents[2] / "rules" / "seed" / card_key
    rule = json.loads(sorted(seed.glob("v*.json"))[-1].read_text())
    return rule["base_earn"]["rate"]["status"]


def test_every_card_is_either_offered_or_locked():
    """Adding a card was free text until 2026-08-03, so the seven skeletons could
    be added and would then answer "unknown" forever. Now the UI offers three and
    shows seven locked, which is only honest while the two lists together account
    for every rule file — a card added to rules/seed and to neither list would be
    invisible, and one in both could be added *and* advertised as unavailable."""
    seed = Path(__file__).resolve().parents[2] / "rules" / "seed"
    on_disk = {d.name for d in seed.iterdir() if d.is_dir() and any(d.glob("v*.json"))}

    offered = {resolve_card_key(e["issuer"], e["card_name"]) for e in _frontend_catalog()}
    locked = {e["card_key"] for e in _pending_cards()}

    assert not (offered & locked), f"card is both offered and locked: {offered & locked}"
    assert offered | locked == on_disk, (
        f"the UI's two lists do not account for every rule file — "
        f"missing from both: {on_disk - offered - locked}, "
        f"named but absent from rules/seed: {(offered | locked) - on_disk}"
    )


def test_locked_cards_are_locked_because_they_are_unverified():
    """The list must track the data, not a hand-maintained opinion of it. A card
    whose rate has since been verified but is still locked is the failure this
    catches: the work was done and nobody can use it."""
    for entry in _pending_cards():
        assert _base_rate_status(entry["card_key"]) == "unverified", (
            f"{entry['label']} is locked in the UI but its base earn rate is now "
            f"verified — move it to KNOWN_CARDS so people can add it"
        )


def test_offered_cards_are_offered_because_they_are_verified():
    """The mirror image, and the one that would actually hurt: a card offered for
    adding whose rate is unverified computes nothing and says so, which reads as
    a broken product rather than an honest one."""
    for entry in _frontend_catalog():
        card_key = resolve_card_key(entry["issuer"], entry["card_name"])
        assert _base_rate_status(card_key) == "verified", (
            f"{entry['label']} can be added but its base earn rate is "
            f"unverified — it would only ever answer 'unknown'"
        )

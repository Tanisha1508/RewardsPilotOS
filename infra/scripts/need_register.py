"""[NEED] register: every unverified fact in the shipped seed data.

Aggregates three sources:
1. rules/seed/**/v*.json — unverified verified-value fields and [NEED] notes
2. knowledge/sources/*.md — lines carrying [NEED markers
3. database/seed/need_register.json — unverified graph transfer candidates

Usage: python -m infra.scripts.need_register
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def _walk_rule(node, path, entries, card):
    if isinstance(node, dict):
        if "status" in node and "confidence" in node and node.get("status") == "unverified":
            entries.append((card, path, "unverified value (null)" if node.get("value") is None
                            else f"unverified value ({node.get('value')})"))
        for key, value in node.items():
            if key == "notes" and isinstance(value, str) and "[NEED" in value:
                entries.append((card, f"{path}.notes", value))
            _walk_rule(value, f"{path}.{key}" if path else key, entries, card)
    elif isinstance(node, list):
        for index, item in enumerate(node):
            _walk_rule(item, f"{path}[{index}]", entries, card)


def collect() -> dict[str, list]:
    register: dict[str, list] = {"rules": [], "knowledge": [], "graph": []}
    for rule_file in sorted(ROOT.glob("rules/seed/*/v*.json")):
        raw = json.loads(rule_file.read_text())
        entries: list = []
        _walk_rule(raw, "", entries, raw.get("card_key", rule_file.parent.name))
        register["rules"].extend(
            {"card": card, "field": field.lstrip("."), "note": note}
            for card, field, note in entries
        )
    for source in sorted(ROOT.glob("knowledge/sources/*.md")):
        for line in source.read_text().splitlines():
            if "[NEED" in line:
                register["knowledge"].append({"doc": source.stem, "line": line.strip()})
    register_path = ROOT / "database" / "seed" / "need_register.json"
    if register_path.exists():
        for edge in json.loads(register_path.read_text()):
            register["graph"].append(
                {
                    "edge": f"{edge['from_node']} -> {edge['to_node']}",
                    "note": edge.get("notes") or "[NEED: verify]",
                }
            )
    return register


def main() -> None:
    register = collect()
    total = sum(len(v) for v in register.values())
    print(f"[NEED] register — {total} open items (see docs/VERIFICATION_QUEUE.md)\n")
    print(f"## Rule files ({len(register['rules'])} unverified fields/notes)")
    for item in register["rules"]:
        print(f"  - {item['card']}: {item['field']} — {item['note']}")
    print(f"\n## Knowledge sources ({len(register['knowledge'])} flagged lines)")
    for item in register["knowledge"]:
        print(f"  - {item['doc']}: {item['line']}")
    print(f"\n## Graph edges ({len(register['graph'])} unverified transfer candidates)")
    for item in register["graph"]:
        print(f"  - {item['edge']} — {item['note']}")


if __name__ == "__main__":
    main()

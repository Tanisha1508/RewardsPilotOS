"""Load versioned rule JSON files from rules/seed/<card_key>/v<N>.json."""

import json
import re
from pathlib import Path

from rules.parser.models import RuleFile
from rules.validators.schema import validate_rule_dict

SEED_DIR = Path(__file__).resolve().parent.parent / "seed"
_VERSION_RE = re.compile(r"^v(\d+)\.json$")


class RuleNotFoundError(Exception):
    """No rule file exists for the requested card."""


class RuleValidationError(Exception):
    """A rule file violates the extended field schema."""


def list_versions(card_key: str, seed_dir: Path | None = None) -> dict[int, Path]:
    card_dir = (seed_dir or SEED_DIR) / card_key
    if not card_dir.is_dir():
        raise RuleNotFoundError(f"no rule directory for card '{card_key}'")
    versions: dict[int, Path] = {}
    for path in card_dir.iterdir():
        match = _VERSION_RE.match(path.name)
        if match:
            versions[int(match.group(1))] = path
    if not versions:
        raise RuleNotFoundError(f"no rule versions for card '{card_key}'")
    return versions


def load_rule(
    card_key: str, version: int | None = None, seed_dir: Path | None = None
) -> RuleFile:
    versions = list_versions(card_key, seed_dir)
    chosen = version if version is not None else max(versions)
    if chosen not in versions:
        raise RuleNotFoundError(f"version {chosen} not found for card '{card_key}'")
    raw = json.loads(versions[chosen].read_text())
    violations = validate_rule_dict(raw)
    if violations:
        raise RuleValidationError(
            f"rule file {versions[chosen]} invalid: " + "; ".join(violations)
        )
    return RuleFile.model_validate(raw)

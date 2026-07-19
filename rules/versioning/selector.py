"""Rule version selection: latest version effective on or before a given date."""

from pathlib import Path

from rules.parser.loader import RuleNotFoundError, list_versions, load_rule
from rules.parser.models import RuleFile


def select_version(
    card_key: str, as_of_date: str | None = None, seed_dir: Path | None = None
) -> RuleFile:
    """Return the highest-numbered version whose effective_date <= as_of_date.

    ISO dates compare correctly as strings. With no as_of_date, the latest
    version wins. Raises RuleNotFoundError when no version is effective yet.
    """
    versions = list_versions(card_key, seed_dir)
    if as_of_date is None:
        return load_rule(card_key, max(versions), seed_dir)
    candidates = []
    for number in sorted(versions, reverse=True):
        rule = load_rule(card_key, number, seed_dir)
        if rule.effective_date <= as_of_date:
            candidates.append(rule)
            break
    if not candidates:
        raise RuleNotFoundError(
            f"no version of '{card_key}' is effective on or before {as_of_date}"
        )
    return candidates[0]

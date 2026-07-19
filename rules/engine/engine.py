"""Rule Engine facade (BUILD_SPEC §5).

API:
    calculate_earn(card_key, amount, category, channel, month) -> EarnResult
    check_cap(card_key, cap_scope, month) -> CapStatus
    compare_cards(cards, amount, category, channel) -> list[EarnResult]  # sorted

All reward math is deterministic, versioned, and refuses unverified values.
"""

from pathlib import Path

from contracts.tools.rule_engine import CapStatus, EarnResult
from rules.engine.cap_store import CapUsageStore, InMemoryCapUsageStore
from rules.evaluator.evaluator import cap_status, evaluate_earn, find_accelerated
from rules.parser.loader import RuleNotFoundError
from rules.versioning.selector import select_version


class RuleEngine:
    def __init__(
        self, cap_store: CapUsageStore | None = None, seed_dir: Path | None = None
    ) -> None:
        self._cap_store: CapUsageStore = cap_store or InMemoryCapUsageStore()
        self._seed_dir = seed_dir

    def calculate_earn(
        self,
        card_key: str,
        amount: float,
        category: str,
        channel: str | None,
        month: str,
    ) -> EarnResult:
        rule = select_version(card_key, seed_dir=self._seed_dir)
        accelerated = find_accelerated(rule, category, channel)
        accrued = 0.0
        if accelerated is not None:
            scope = accelerated.cap_scope or f"{accelerated.channel}_{accelerated.category}"
            accrued = self._cap_store.get_accrued(card_key, scope, month)
        # Pure query: comparing or re-asking never consumes cap. Actual spend is
        # recorded by the application layer via cap_store.record.
        return evaluate_earn(rule, amount, category, channel, month, accrued)

    def check_cap(self, card_key: str, cap_scope: str, month: str) -> CapStatus:
        rule = select_version(card_key, seed_dir=self._seed_dir)
        accrued = self._cap_store.get_accrued(card_key, cap_scope, month)
        return cap_status(rule, cap_scope, month, accrued)

    def compare_cards(
        self,
        cards: list[str],
        amount: float,
        category: str,
        channel: str | None,
        month: str = "1970-01",
    ) -> list[EarnResult]:
        """Evaluate each card and sort: computed (highest points first), then
        unknown, then excluded. Missing cards yield unknown results — graceful
        degradation, never a crash mid-comparison."""
        results: list[EarnResult] = []
        for card_key in cards:
            try:
                results.append(self.calculate_earn(card_key, amount, category, channel, month))
            except RuleNotFoundError as exc:
                results.append(
                    EarnResult(
                        card_key=card_key,
                        amount=amount,
                        category=category,
                        channel=channel,
                        month=month,
                        status="unknown",
                        unknown_reasons=[str(exc)],
                    )
                )
        order = {"computed": 0, "unknown": 1, "excluded": 2}
        return sorted(
            results,
            key=lambda r: (order[r.status], -(r.points if r.points is not None else 0.0)),
        )

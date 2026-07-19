"""Cap-usage state interface. Sprint milestone uses the in-memory fake; the
D2 Postgres-backed store (cap_usage table, BUILD_SPEC §4) implements the same
protocol so it drops in without refactoring."""

from collections import defaultdict
from typing import Protocol


class CapUsageStore(Protocol):
    def get_accrued(self, card_key: str, scope: str, month: str) -> float: ...

    def record(self, card_key: str, scope: str, month: str, points: float) -> None: ...


class InMemoryCapUsageStore:
    def __init__(self) -> None:
        self._usage: dict[tuple[str, str, str], float] = defaultdict(float)

    def get_accrued(self, card_key: str, scope: str, month: str) -> float:
        return self._usage[(card_key, scope, month)]

    def record(self, card_key: str, scope: str, month: str, points: float) -> None:
        self._usage[(card_key, scope, month)] += points

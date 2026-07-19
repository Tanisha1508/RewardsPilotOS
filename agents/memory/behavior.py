"""Memory-focused agent behavior: recall policy (BUILD_SPEC §8).

Retrieval only; nothing is appended blindly to prompts. The Planner requests
memory recall only when the intent benefits from preferences or history."""

RECALL_INTENTS = ("spend", "transfer", "redeem")


def should_recall_memory(intent: str) -> bool:
    return intent in RECALL_INTENTS

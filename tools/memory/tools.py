"""Memory tools: RecallMemory, StorePreference (BUILD_SPEC §8).

Signatures unchanged from the sprint; the in-module dicts are gone and the data
now comes from `preferences` and `interaction_events` (see
`tools/memory/source.py`).
"""

from contracts.tools.memory import (
    RecallMemoryInput,
    RecallMemoryOutput,
    StorePreferenceInput,
    StorePreferenceOutput,
)
from tools.memory.source import get_source


def recall_memory(args: RecallMemoryInput) -> RecallMemoryOutput:
    source = get_source()
    return RecallMemoryOutput(
        preferences=source.preferences(args.user_id),
        episodic=source.episodic(args.user_id, args.limit),
    )


def store_preference(args: StorePreferenceInput) -> StorePreferenceOutput:
    get_source().store_preference(args.user_id, args.key, args.value)
    return StorePreferenceOutput(stored=True, key=args.key, value=args.value)

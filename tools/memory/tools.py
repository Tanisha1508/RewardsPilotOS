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
from tools.portfolio.source import current_user


def recall_memory(args: RecallMemoryInput) -> RecallMemoryOutput:
    user_id = current_user()
    source = get_source()
    return RecallMemoryOutput(
        preferences=source.preferences(user_id),
        episodic=source.episodic(user_id, args.limit),
    )


def store_preference(args: StorePreferenceInput) -> StorePreferenceOutput:
    # Written as "assistant" (B3, 2026-07-31). This tool exists so the model can
    # record a durable preference it inferred from a conversation, and the whole
    # reason the column exists is that such a value must not be presentable as
    # something the user chose. The source is hard-coded rather than taken from
    # `args`: it describes which code path wrote the row, and letting model
    # output name it would let a write claim to be the user's own.
    get_source().store_preference(current_user(), args.key, args.value, source="assistant")
    return StorePreferenceOutput(stored=True, key=args.key, value=args.value)

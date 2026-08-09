"""Langfuse propagated metadata must stay within the 200-char limit."""

from __future__ import annotations

import json

from evals.commons.run_experiment import (
    _LANGFUSE_PROPAGATED_MAX_CHARS,
    slim_experiment_item_metadata,
)


def test_slim_metadata_keeps_id_under_limit() -> None:
    meta = {
        "id": "prod-0008",
        "tags": [
            "production",
            "web-search-agents",
            "dataset-building",
            "other-capability-benchmark-evaluation",
        ],
        "source": "user_messages_classified",
        "scorable": [
            "first_turn_action",
            "forbidden_tools",
            "tool_selection",
            "clarification_substantive",
        ],
        "source_row_id": 8,
    }
    raw = json.dumps(meta, separators=(",", ":"))
    assert len(raw) > _LANGFUSE_PROPAGATED_MAX_CHARS
    slim = slim_experiment_item_metadata(meta)
    blob = json.dumps(slim, separators=(",", ":"))
    assert len(blob) <= _LANGFUSE_PROPAGATED_MAX_CHARS
    assert slim.get("id") == "prod-0008"


def test_slim_metadata_includes_short_tags_when_fit() -> None:
    meta = {"id": "prod-1", "tags": ["production", "search"]}
    slim = slim_experiment_item_metadata(meta)
    assert slim == {"id": "prod-1", "tags": ["production", "search"]}


def test_slim_metadata_empty_safe() -> None:
    assert slim_experiment_item_metadata(None) == {}
    assert slim_experiment_item_metadata({}) == {}

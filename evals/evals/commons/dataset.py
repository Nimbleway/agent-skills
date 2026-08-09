"""Load production eval items from Langfuse."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from evals.commons.gold import remap_expected
from evals.commons.settings import EvalSettings


def prompt_from_input(inp: Any) -> str:
    if not isinstance(inp, dict):
        return str(inp or "")
    if isinstance(inp.get("prompt"), str):
        return inp["prompt"]
    messages = inp.get("messages")
    if isinstance(messages, list):
        parts = [
            str(m.get("content", ""))
            for m in messages
            if isinstance(m, dict) and m.get("role") == "user"
        ]
        if parts:
            return "\n".join(parts)
    return str(inp)


@dataclass
class DatasetItem:
    id: str
    input: dict[str, Any]
    expected_output: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def prompt(self) -> str:
        return prompt_from_input(self.input)


def load_from_langfuse(settings: EvalSettings, dataset_name: str) -> list[DatasetItem]:
    from langfuse import Langfuse

    client = Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
    )
    dataset = client.get_dataset(dataset_name)
    items: list[DatasetItem] = []
    for item in dataset.items:
        status = getattr(item, "status", None)
        # Langfuse ACTIVE filter — skip archived when present
        if status is not None and str(status).upper() not in {"ACTIVE", "DATASETITEMSTATUS.ACTIVE"}:
            if "ACTIVE" not in str(status).upper():
                continue
        raw_expected = item.expected_output if isinstance(item.expected_output, dict) else {}
        expected = remap_expected(raw_expected)
        if raw_expected.get("solution") is not None:
            expected["solution"] = raw_expected.get("solution")
        meta = item.metadata if isinstance(item.metadata, dict) else {}
        meta = dict(meta)
        if expected.get("scorable"):
            meta["scorable"] = expected["scorable"]
        inp = item.input if isinstance(item.input, dict) else {"prompt": str(item.input)}
        logical_id = str(
            meta.get("id")
            or meta.get("item_id")
            or getattr(item, "id", None)
            or getattr(item, "dataset_item_id", "")
            or ""
        )
        if logical_id and "id" not in meta:
            meta["id"] = logical_id
        items.append(
            DatasetItem(
                id=logical_id,
                input=inp,
                expected_output=expected,
                metadata=meta,
            )
        )
    return items


def load_dataset(
    settings: EvalSettings,
    *,
    dataset_name: str,
) -> list[DatasetItem]:
    """Load items from the private Langfuse dataset."""
    if not settings.langfuse_configured:
        raise SystemExit(
            "Langfuse required. Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY "
            f"to load dataset '{dataset_name}'."
        )
    return load_from_langfuse(settings, dataset_name)

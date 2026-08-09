"""Convert CLI events → Langfuse observation tree (Claude Code / Codex shape).

Mirrors what the official Langfuse integrations send:
https://langfuse.com/integrations/developer-tools/claude-code
https://langfuse.com/integrations/developer-tools/codex

Only emits observations with real input/output — no empty placeholder spans.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, Field

from evals.commons.cli_events import (
    CliEvent,
    GenerationEvent,
    ResultEvent,
    ToolResultEvent,
    ToolUseEvent,
)

ObservationType = Literal[
    "generation",
    "tool",
    "span",
    "agent",
]


class LangfuseObservation(BaseModel):
    """One observation we will create under the experiment-item span."""

    name: str
    as_type: ObservationType
    input: Any = None
    output: Any = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    model: str | None = None
    level: Literal["DEBUG", "DEFAULT", "WARNING", "ERROR"] | None = None
    status_message: str | None = None
    usage_details: dict[str, int] | None = None
    cost_details: dict[str, float] | None = None


class LangfuseTracePayload(BaseModel):
    """Everything we attach to a Langfuse experiment item after a CLI run."""

    trace_input: dict[str, Any]
    trace_output: dict[str, Any]
    metadata: dict[str, Any] = Field(default_factory=dict)
    observations: list[LangfuseObservation] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


# Clip only to keep Langfuse payloads bounded (Langfuse project is private).
_MAX_CHARS = 12_000


def _tool_input_from_result(event: ToolResultEvent) -> dict[str, Any] | None:
    raw = event.output
    if not raw:
        return None
    try:
        parsed = json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(parsed, dict):
        return None
    keep = {
        k: parsed[k]
        for k in ("query", "queries", "action", "action_type", "command")
        if k in parsed and parsed[k] not in (None, "", [])
    }
    return keep or None


def _clip(value: Any, max_chars: int = _MAX_CHARS) -> Any:
    if isinstance(value, str) and len(value) > max_chars:
        return value[: max_chars - 20] + "\n…[truncated]"
    if isinstance(value, dict):
        return {k: _clip(v, max_chars) for k, v in value.items()}
    if isinstance(value, list):
        return [_clip(v, max_chars) for v in value[:50]]
    return value


def _usage_details(usage: dict[str, Any] | None) -> dict[str, int] | None:
    if not usage:
        return None
    if any(isinstance(v, dict) for v in usage.values()):
        totals = {"input": 0, "output": 0}
        for model_usage in usage.values():
            if not isinstance(model_usage, dict):
                continue
            totals["input"] += int(
                model_usage.get("inputTokens")
                or model_usage.get("input_tokens")
                or 0
            )
            totals["output"] += int(
                model_usage.get("outputTokens")
                or model_usage.get("output_tokens")
                or 0
            )
        return totals if totals["input"] or totals["output"] else None
    details: dict[str, int] = {}
    for key, dest in (
        ("input_tokens", "input"),
        ("output_tokens", "output"),
        ("inputTokens", "input"),
        ("outputTokens", "output"),
        ("cache_read_input_tokens", "cache_read_input_tokens"),
        ("cache_creation_input_tokens", "cache_creation_input_tokens"),
    ):
        if key in usage and usage[key] is not None:
            details[dest] = int(usage[key])
    return details or None


def _has_content(value: Any) -> bool:
    if value is None:
        return False
    if value == "" or value == {} or value == []:
        return False
    if isinstance(value, dict):
        return any(_has_content(v) for v in value.values())
    return True


def events_to_langfuse_payload(
    events: list[CliEvent],
    *,
    prompt: str,
    runtime: Literal["claude", "codex"],
    model: str,
    item_id: str | None = None,
    effort: str | None = None,
) -> LangfuseTracePayload:
    """Build the Langfuse payload from ordered CLI events."""
    pending_tools: dict[str, ToolUseEvent] = {}
    observations: list[LangfuseObservation] = []
    texts: list[str] = []
    result: ResultEvent | None = None
    current_model = model
    prompt_clip = _clip(prompt, 2000)

    for event in events:
        if isinstance(event, GenerationEvent):
            if event.model:
                current_model = event.model
            if event.text:
                texts.append(event.text)
            gen_out: dict[str, Any] = {}
            if event.text:
                gen_out["text"] = _clip(event.text)
            if event.tool_calls:
                gen_out["tool_calls"] = _clip(event.tool_calls)
            if not gen_out:
                # usage-only turn — still record tokens
                gen_out = {"text": ""}
            observations.append(
                LangfuseObservation(
                    name="assistant_message",
                    as_type="generation",
                    input={"prompt": prompt_clip, "runtime": runtime},
                    output=gen_out,
                    model=event.model or current_model,
                    metadata={"runtime": runtime},
                    usage_details=_usage_details(event.usage),
                )
            )
        elif isinstance(event, ToolUseEvent):
            if event.model:
                current_model = event.model
            pending_tools[event.id] = event
            # Defer emit until tool_result so we never create empty tool spans.
        elif isinstance(event, ToolResultEvent):
            use = pending_tools.pop(event.tool_use_id, None)
            name = (use.name if use else None) or "tool"
            completed_input = _tool_input_from_result(event)
            tool_input = completed_input or (use.input if use else {}) or {}
            tool_output = event.output or ""
            if not _has_content(tool_input) and not _has_content(tool_output):
                continue
            # Drop Codex noise: empty web_search / file_change with no payload
            if isinstance(tool_input, dict):
                if name == "web_search":
                    if not tool_input.get("query") and not tool_input.get("queries"):
                        continue
                if set(tool_input.keys()) <= {"raw_type"} and not _has_content(tool_output):
                    continue
            observations.append(
                LangfuseObservation(
                    name=name,
                    as_type="tool",
                    input=_clip(tool_input),
                    output=_clip(tool_output),
                    metadata={
                        "runtime": runtime,
                        "tool_use_id": event.tool_use_id,
                        "status": "completed",
                    },
                    level="ERROR" if event.is_error else "DEFAULT",
                    status_message="tool error" if event.is_error else None,
                )
            )
        elif isinstance(event, ResultEvent):
            result = event

    # Drop any generation that still has neither text nor tool_calls
    observations = [
        o
        for o in observations
        if o.as_type != "generation"
        or _has_content((o.output or {}).get("text") if isinstance(o.output, dict) else o.output)
        or _has_content((o.output or {}).get("tool_calls") if isinstance(o.output, dict) else None)
        or o.usage_details
    ]

    final_text = ""
    if result and result.final_response:
        final_text = result.final_response
    elif texts:
        final_text = texts[-1]

    tools_called = [
        o.name for o in observations if o.as_type == "tool"
    ]

    hard_error = bool(result and result.is_error and not (final_text or tools_called))
    soft_error = bool(result and result.is_error and not hard_error)

    trace_output: dict[str, Any] = {
        "final_response": _clip(final_text, 4000),
        "tools_called": tools_called,
        "num_turns": result.num_turns if result else None,
        "cost_usd": result.cost_usd if result else None,
        "stop_reason": result.stop_reason if result else None,
        "partial": soft_error,
    }
    if hard_error:
        trace_output["error"] = "cli result is_error with no usable output"
    elif soft_error:
        trace_output["error"] = "partial: cli reported is_error"

    meta: dict[str, Any] = {
        "runtime": runtime,
        "model": current_model,
        "observation_count": len(observations),
    }
    if item_id:
        meta["item_id"] = item_id
    if effort:
        meta["effort"] = effort

    return LangfuseTracePayload(
        trace_input={"prompt": _clip(prompt, 4000), "runtime": runtime},
        trace_output=trace_output,
        metadata=meta,
        observations=observations,
        tags=["nimble-web-expert", f"runtime:{runtime}", "skills-eval"],
    )


def claude_stream_to_langfuse_payload(
    path: str | Any,
    *,
    prompt: str,
    model: str,
    item_id: str | None = None,
    effort: str | None = None,
) -> LangfuseTracePayload:
    from evals.commons.cli_events import extract_claude_events

    events = extract_claude_events(path)
    return events_to_langfuse_payload(
        events,
        prompt=prompt,
        runtime="claude",
        model=model,
        item_id=item_id,
        effort=effort,
    )


def codex_jsonl_to_langfuse_payload(
    path: str | Any,
    *,
    prompt: str,
    model: str,
    item_id: str | None = None,
    effort: str | None = None,
) -> LangfuseTracePayload:
    from evals.commons.cli_events import extract_codex_events

    events = extract_codex_events(path)
    return events_to_langfuse_payload(
        events,
        prompt=prompt,
        runtime="codex",
        model=model,
        item_id=item_id,
        effort=effort,
    )

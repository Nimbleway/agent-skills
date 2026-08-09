"""Typed events extracted from Claude stream-json / Codex JSONL."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


class GenerationEvent(BaseModel):
    """One assistant model turn (text and/or tool calls)."""

    kind: Literal["generation"] = "generation"
    text: str = ""
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    model: str | None = None
    usage: dict[str, Any] | None = None


class ToolUseEvent(BaseModel):
    kind: Literal["tool_use"] = "tool_use"
    id: str
    name: str
    input: dict[str, Any] = Field(default_factory=dict)
    model: str | None = None


class ToolResultEvent(BaseModel):
    kind: Literal["tool_result"] = "tool_result"
    tool_use_id: str
    output: str
    is_error: bool = False


class ResultEvent(BaseModel):
    kind: Literal["result"] = "result"
    final_response: str | None = None
    is_error: bool = False
    num_turns: int | None = None
    cost_usd: float | None = None
    usage: dict[str, Any] | None = None
    stop_reason: str | None = None


# Backward-compat alias used in older tests/docs
TextEvent = GenerationEvent

CliEvent = GenerationEvent | ToolUseEvent | ToolResultEvent | ResultEvent


def _tool_result_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict):
                if block.get("text") is not None:
                    parts.append(str(block["text"]))
                elif block.get("content") is not None:
                    parts.append(str(block["content"]))
                else:
                    parts.append(json.dumps(block, default=str)[:500])
            else:
                parts.append(str(block))
        return "\n".join(parts)
    if isinstance(content, dict):
        return json.dumps(content, default=str)
    return str(content)


def extract_claude_events(path: Path | str) -> list[CliEvent]:
    """Parse Claude Code `--output-format stream-json` into ordered events.

    Ignores partial ``stream_event`` lines; only complete assistant/user/result
    messages become events. Each assistant message becomes one generation
    (with text + tool_calls) plus per-tool use/result events.
    """
    events: list[CliEvent] = []
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        typ = obj.get("type")
        if typ == "assistant":
            msg = obj.get("message") or {}
            model = str(msg["model"]) if msg.get("model") else None
            usage = msg.get("usage") if isinstance(msg.get("usage"), dict) else None
            texts: list[str] = []
            tool_calls: list[dict[str, Any]] = []
            for block in msg.get("content") or []:
                if not isinstance(block, dict):
                    continue
                btype = block.get("type")
                if btype == "text" and block.get("text"):
                    texts.append(str(block["text"]))
                elif btype == "tool_use":
                    call = {
                        "id": str(block.get("id") or ""),
                        "name": str(block.get("name") or "tool"),
                        "input": block.get("input")
                        if isinstance(block.get("input"), dict)
                        else {},
                    }
                    tool_calls.append(call)
                    events.append(
                        ToolUseEvent(
                            id=call["id"],
                            name=call["name"],
                            input=call["input"],
                            model=model,
                        )
                    )
            if texts or tool_calls or usage:
                events.append(
                    GenerationEvent(
                        text="\n".join(texts),
                        tool_calls=tool_calls,
                        model=model,
                        usage=usage,
                    )
                )
        elif typ == "user":
            msg = obj.get("message") or {}
            for block in msg.get("content") or []:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_result":
                    events.append(
                        ToolResultEvent(
                            tool_use_id=str(block.get("tool_use_id") or ""),
                            output=_tool_result_text(block.get("content")),
                            is_error=bool(block.get("is_error")),
                        )
                    )
        elif typ == "result":
            cost = obj.get("total_cost_usd")
            events.append(
                ResultEvent(
                    final_response=str(obj["result"])
                    if obj.get("result") is not None
                    else None,
                    is_error=bool(obj.get("is_error")),
                    num_turns=int(obj["num_turns"])
                    if obj.get("num_turns") is not None
                    else None,
                    cost_usd=float(cost) if cost is not None else None,
                    usage=obj.get("modelUsage")
                    if isinstance(obj.get("modelUsage"), dict)
                    else obj.get("usage")
                    if isinstance(obj.get("usage"), dict)
                    else None,
                    stop_reason=str(obj["stop_reason"])
                    if obj.get("stop_reason") is not None
                    else None,
                )
            )
    return events


_CODEX_MESSAGE_TYPES = frozenset({"agent_message", "reasoning", "message"})


def _codex_tool_name(item: dict[str, Any]) -> str:
    item_type = str(item.get("type") or "tool")
    if item_type == "command_execution":
        return "exec_command"
    return item_type


def _codex_tool_input(item: dict[str, Any]) -> dict[str, Any]:
    item_type = str(item.get("type") or "")
    if item_type == "command_execution":
        return {"command": str(item.get("command") or "")}
    if item_type == "web_search":
        action = item.get("action") if isinstance(item.get("action"), dict) else {}
        return {
            "query": item.get("query") or "",
            "action": action,
            "queries": action.get("queries") if isinstance(action, dict) else None,
        }
    if item_type == "apply_patch":
        return {
            "path": item.get("path") or item.get("file"),
            "changes": item.get("changes") or item.get("diff"),
        }
    keep = {}
    for key in (
        "command",
        "query",
        "name",
        "tool",
        "server",
        "arguments",
        "action",
        "path",
        "prompt",
    ):
        if key in item and item[key] is not None:
            keep[key] = item[key]
    return keep or {"raw_type": item_type}


def _codex_tool_output(item: dict[str, Any]) -> str:
    for key in (
        "aggregated_output",
        "output",
        "stdout",
        "result",
        "content",
        "text",
    ):
        if item.get(key) is not None:
            val = item[key]
            return val if isinstance(val, str) else json.dumps(val, default=str)
    if item.get("type") == "web_search":
        action = item.get("action") if isinstance(item.get("action"), dict) else {}
        queries = action.get("queries") if isinstance(action, dict) else None
        return json.dumps(
            {
                "query": item.get("query"),
                "queries": queries,
                "action_type": action.get("type") if isinstance(action, dict) else None,
            },
            default=str,
        )
    return ""


def _input_is_sparse(inp: dict[str, Any]) -> bool:
    if not inp:
        return True
    return not any(
        v not in (None, "", [], {})
        for k, v in inp.items()
        if k in {"query", "command", "queries", "arguments", "path", "prompt"}
    )


def extract_codex_events(path: Path | str) -> list[CliEvent]:
    """Parse Codex ``exec --json`` JSONL into ordered events."""
    events: list[CliEvent] = []
    # Synthetic ids from item.started when Codex omits id/call_id — reuse on completed.
    pending_anon_ids: list[str] = []
    anon_seq = 0

    def _tool_id(item: dict[str, Any], *, starting: bool) -> str:
        nonlocal anon_seq
        raw = item.get("id") or item.get("call_id")
        if raw not in (None, ""):
            return str(raw)
        if starting:
            anon_seq += 1
            tool_id = f"tool-anon-{anon_seq}"
            pending_anon_ids.append(tool_id)
            return tool_id
        if pending_anon_ids:
            return pending_anon_ids.pop(0)
        anon_seq += 1
        return f"tool-anon-{anon_seq}"

    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        typ = obj.get("type")
        item = obj.get("item") if isinstance(obj.get("item"), dict) else {}
        item_type = str(item.get("type") or "")

        if typ == "item.started" and item_type and item_type not in _CODEX_MESSAGE_TYPES:
            tool_id = _tool_id(item, starting=True)
            events.append(
                ToolUseEvent(
                    id=tool_id,
                    name=_codex_tool_name(item),
                    input=_codex_tool_input(item),
                )
            )
        elif typ == "item.completed" and item_type == "agent_message":
            text = str(item.get("text") or "")
            if text.strip():
                events.append(GenerationEvent(text=text))
        elif typ == "item.completed" and item_type and item_type not in _CODEX_MESSAGE_TYPES:
            tool_id = _tool_id(item, starting=False)
            exit_code = item.get("exit_code")
            status = str(item.get("status") or "").lower()
            is_error = bool(
                (exit_code not in (None, 0))
                or status in {"failed", "error", "errored"}
                or item.get("is_error")
            )
            richer = _codex_tool_input(item)
            existing = next(
                (
                    e
                    for e in events
                    if isinstance(e, ToolUseEvent) and e.id == tool_id
                ),
                None,
            )
            if existing is None:
                events.append(
                    ToolUseEvent(
                        id=tool_id,
                        name=_codex_tool_name(item),
                        input=richer,
                    )
                )
            elif _input_is_sparse(existing.input) and not _input_is_sparse(richer):
                existing.input = richer
            events.append(
                ToolResultEvent(
                    tool_use_id=tool_id,
                    output=_codex_tool_output(item),
                    is_error=is_error,
                )
            )
        elif typ == "turn.completed":
            usage = obj.get("usage") if isinstance(obj.get("usage"), dict) else None
            events.append(ResultEvent(usage=usage))
        elif typ == "error":
            events.append(
                ResultEvent(
                    final_response=str(obj.get("message") or obj.get("error") or ""),
                    is_error=True,
                )
            )
    return events

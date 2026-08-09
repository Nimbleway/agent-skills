"""Parse Claude stream-json / Codex JSONL into NormalizedTrace."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from evals.commons.eval_prompt import prompt_invokes_web_expert
from evals.commons.nimble_cmd import add_nimble_tools
from evals.commons.trace import NormalizedTrace

SKILL_NAME = "nimble-web-expert"
CLARIFY_HINTS = re.compile(
    r"\b(could you clarify|which (one|site|url)|what (exactly|do you mean)|"
    r"need more (detail|info|information)|please (specify|provide))\b",
    re.IGNORECASE,
)


def _add_nimble_tools(command: str, tools: list[str]) -> None:
    """Back-compat wrapper — implementation lives in ``nimble_cmd`` (bashlex)."""
    add_nimble_tools(command, tools)


def parse_claude_stream(
    path: Path,
    *,
    prompt: str,
    model: str,
    effort: str | None,
) -> NormalizedTrace:
    triggered: list[str] = []
    tools: list[str] = []
    response = ""
    cost = None
    turns = None
    usage = None
    error = None
    asked_clarify = False

    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
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
            if msg.get("model"):
                model = str(msg["model"])
            for block in msg.get("content") or []:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_use":
                    name = block.get("name") or ""
                    inp = block.get("input") or {}
                    if name == "Skill":
                        skill = str(
                            inp.get("skill")
                            or inp.get("name")
                            or inp.get("command")
                            or ""
                        )
                        if SKILL_NAME in skill and SKILL_NAME not in triggered:
                            triggered.append(SKILL_NAME)
                    elif name == "AskUserQuestion":
                        asked_clarify = True
                        if "ask_questions" not in tools:
                            tools.append("ask_questions")
                    elif name == "Bash":
                        cmd = str(inp.get("command") or inp.get("cmd") or "")
                        _add_nimble_tools(cmd, tools)
                    elif name == "Read":
                        fp = str(inp.get("file_path") or inp.get("path") or "")
                        if SKILL_NAME in fp and SKILL_NAME not in triggered:
                            triggered.append(SKILL_NAME)
                elif block.get("type") == "text" and block.get("text"):
                    response = str(block["text"])
        elif typ == "user":
            msg = obj.get("message") or {}
            for block in msg.get("content") or []:
                if not isinstance(block, dict):
                    continue
                text = str(block.get("content") or block.get("text") or "")
                if f"Launching skill:" in text and SKILL_NAME in text:
                    if SKILL_NAME not in triggered:
                        triggered.append(SKILL_NAME)
                if SKILL_NAME in text and "Base directory for this skill" in text:
                    if SKILL_NAME not in triggered:
                        triggered.append(SKILL_NAME)
        elif typ == "result":
            if obj.get("result") is not None:
                response = str(obj.get("result") or response)
            cost = obj.get("total_cost_usd")
            turns = obj.get("num_turns")
            usage = obj.get("modelUsage") or obj.get("usage")
            if obj.get("is_error"):
                # Claude marks max-turns / budget stops as is_error even when the
                # run produced useful skill/tool/response signals — keep those
                # scorable and only surface a hard error when nothing usable remains.
                err_msg = str(obj.get("result") or "claude result is_error")
                has_signal = bool(triggered or tools or (response or "").strip())
                if not has_signal:
                    error = err_msg
                elif not error:
                    # Soft note for local debugging; scorers ignore non-empty traces.
                    error = f"partial: {err_msg[:120]}"

    if not asked_clarify and response and CLARIFY_HINTS.search(response) and not tools:
        asked_clarify = True
        tools.append("ask_questions")

    # Claude --bare expands ``/plugin:skill args`` without emitting a Skill
    # tool_use. Credit the skill when the user turn is a slash invoke.
    if SKILL_NAME not in triggered and prompt_invokes_web_expert(prompt):
        triggered.append(SKILL_NAME)

    return NormalizedTrace(
        runtime="claude",
        model=model,
        effort=effort,
        prompt=prompt,
        triggered_skills=triggered,
        tools_called=tools,
        tool_names=list(tools),
        response=response,
        final_response=response,
        asked_clarify=asked_clarify,
        error=error,
        raw_path=path,
        cost_usd=float(cost) if cost is not None else None,
        num_turns=int(turns) if turns is not None else None,
        usage=usage if isinstance(usage, dict) else None,
    )


def parse_codex_jsonl(
    path: Path,
    last_message_path: Path | None,
    *,
    prompt: str,
    model: str,
    effort: str | None,
) -> NormalizedTrace:
    triggered: list[str] = []
    tools: list[str] = []
    response = ""
    usage = None
    error = None
    asked_clarify = False

    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
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
        if typ in {"item.started", "item.completed"} and item_type == "command_execution":
            cmd = str(item.get("command") or "")
            if f"{SKILL_NAME}/SKILL.md" in cmd or (
                f"{SKILL_NAME}" in cmd and "SKILL.md" in cmd
            ):
                if SKILL_NAME not in triggered:
                    triggered.append(SKILL_NAME)
            _add_nimble_tools(cmd, tools)
        if typ in {"item.started", "item.completed"} and item_type == "web_search":
            if "web_search" not in tools:
                tools.append("web_search")
        if typ in {"item.started", "item.completed"} and item_type not in {
            "",
            "agent_message",
            "reasoning",
            "message",
            "command_execution",
            "web_search",
        }:
            # MCP / apply_patch / other Codex tools — keep the type name.
            if item_type not in tools:
                tools.append(item_type)
        if typ == "item.completed" and item_type == "agent_message":
            text = str(item.get("text") or "")
            if text:
                response = text
            if SKILL_NAME in text.lower() and "skill" in text.lower():
                # weak signal — prefer file read
                pass
        if typ == "turn.completed":
            usage = obj.get("usage") if isinstance(obj.get("usage"), dict) else usage
        if typ == "error" or obj.get("error"):
            error = str(obj.get("error") or obj.get("message") or error)

    if last_message_path and last_message_path.is_file():
        last = last_message_path.read_text(encoding="utf-8", errors="replace").strip()
        if last:
            response = last

    if not asked_clarify and response and CLARIFY_HINTS.search(response) and not tools:
        asked_clarify = True
        tools.append("ask_questions")

    # Codex has no Skill tool_use. Prefer SKILL.md reads (above); if the user
    # turn was a slash invoke and Nimble ran, credit the skill as routed.
    if (
        SKILL_NAME not in triggered
        and prompt_invokes_web_expert(prompt)
        and any(t.startswith("nimble ") for t in tools)
    ):
        triggered.append(SKILL_NAME)

    return NormalizedTrace(
        runtime="codex",
        model=model,
        effort=effort,
        prompt=prompt,
        triggered_skills=triggered,
        tools_called=tools,
        tool_names=list(tools),
        response=response,
        final_response=response,
        asked_clarify=asked_clarify,
        error=error,
        raw_path=path,
        cost_usd=None,
        num_turns=None,
        usage=usage,
    )


def dump_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")

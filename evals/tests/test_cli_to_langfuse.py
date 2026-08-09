"""Unit tests: CLI JSONL → Langfuse observation payload."""

from __future__ import annotations

import base64
from pathlib import Path

import pytest

from evals.commons.cli_events import (
    GenerationEvent,
    TextEvent,
    ToolResultEvent,
    ToolUseEvent,
    extract_claude_events,
    extract_codex_events,
)
from evals.commons.langfuse_otel import (
    build_claude_otel_env,
    build_codex_langfuse_env,
    langfuse_basic_auth,
    langfuse_otel_endpoint,
    merge_cli_env,
    strip_foreign_provider_secrets,
)
from evals.commons.langfuse_payload import (
    claude_stream_to_langfuse_payload,
    codex_jsonl_to_langfuse_payload,
    events_to_langfuse_payload,
)
from evals.commons.settings import EvalSettings

FIXTURES = Path(__file__).parent / "fixtures"


def test_extract_claude_events_ignores_stream_partials(tmp_path: Path) -> None:
    path = tmp_path / "mixed.jsonl"
    path.write_text(
        "\n".join(
            [
                '{"type":"stream_event","event":{"type":"content_block_delta"}}',
                '{"type":"assistant","message":{"model":"m","content":[{"type":"text","text":"hi"}]}}',
                '{"type":"result","is_error":false,"result":"hi","num_turns":1}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    events = extract_claude_events(path)
    assert [e.kind for e in events] == ["generation", "result"]
    assert isinstance(events[0], GenerationEvent)
    assert events[0].text == "hi"


def test_claude_fixture_to_langfuse_payload() -> None:
    path = FIXTURES / "claude_minimal.jsonl"
    payload = claude_stream_to_langfuse_payload(
        path,
        prompt="what's example.com has",
        model="claude-sonnet-5",
        item_id="fixture-001",
        effort="medium",
    )

    assert payload.trace_input["prompt"] == "what's example.com has"
    assert payload.trace_input["runtime"] == "claude"
    assert payload.trace_output["final_response"] == "Acme builds widgets."
    assert payload.trace_output.get("error") in (None, False) or not payload.trace_output.get(
        "error"
    )
    assert "Skill" in payload.trace_output["tools_called"]
    assert "Bash" in payload.trace_output["tools_called"]
    assert payload.metadata["item_id"] == "fixture-001"
    assert "nimble-web-expert" in payload.tags

    gens = [o for o in payload.observations if o.as_type == "generation"]
    tools = [o for o in payload.observations if o.as_type == "tool"]
    assert len(gens) >= 2
    assert gens[0].output.get("text") == "I'll fetch the site."
    assert gens[0].model == "claude-sonnet-5"
    # Tool-only assistant turns still produce a generation with tool_calls
    assert any(g.output.get("tool_calls") for g in gens)

    skill = next(o for o in tools if o.name == "Skill")
    assert skill.input["skill"] == "nimble:nimble-web-expert"
    assert skill.metadata["status"] == "completed"
    assert "Launching skill" in str(skill.output)

    bash = next(o for o in tools if o.name == "Bash")
    assert "--client-source nimble-agent-skills" in bash.input["command"]
    assert "extract" in bash.input["command"]
    assert "Acme" in str(bash.output)
    assert bash.level == "DEFAULT"
    # No empty placeholder observations
    assert all(
        (o.input not in (None, {}, "")) or (o.output not in (None, {}, ""))
        for o in payload.observations
    )


def test_claude_tool_error_sets_observation_level(tmp_path: Path) -> None:
    path = tmp_path / "err.jsonl"
    path.write_text(
        "\n".join(
            [
                '{"type":"assistant","message":{"content":[{"type":"tool_use","id":"t1","name":"Bash","input":{"command":"false"}}]}}',
                '{"type":"user","message":{"content":[{"type":"tool_result","tool_use_id":"t1","content":"boom","is_error":true}]}}',
                '{"type":"result","is_error":true,"result":"failed","num_turns":1}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    payload = claude_stream_to_langfuse_payload(
        path, prompt="x", model="m", item_id="i1"
    )
    tool = next(o for o in payload.observations if o.as_type == "tool")
    assert tool.level == "ERROR"
    assert tool.status_message == "tool error"
    # Has usable output → soft/partial, not hard blank error
    assert payload.trace_output["final_response"] == "failed"
    assert payload.trace_output.get("partial") is True


def test_codex_fixture_to_langfuse_payload() -> None:
    path = FIXTURES / "codex_minimal.jsonl"
    payload = codex_jsonl_to_langfuse_payload(
        path,
        prompt="search acme",
        model="gpt-5.6-sol",
        item_id="prod-0017",
    )
    assert payload.trace_input["runtime"] == "codex"
    assert payload.trace_output["final_response"] == "Here is what I found for acme."
    tools = [o for o in payload.observations if o.as_type == "tool"]
    assert len(tools) == 3
    assert {o.name for o in tools} == {"exec_command", "web_search"}
    assert all(o.metadata["status"] == "completed" for o in tools)
    web = next(o for o in tools if o.name == "web_search")
    assert web.input["query"] == "acme corp overview"
    bash = next(
        o
        for o in tools
        if o.name == "exec_command" and "nimble" in str(o.input) and "search" in str(o.input)
    )
    assert "--client-source nimble-agent-skills" in bash.input["command"]
    assert "search" in bash.input["command"]
    gens = [o for o in payload.observations if o.as_type == "generation"]
    assert len(gens) == 1
    assert "acme" in gens[0].output["text"]


def test_codex_pairs_tools_when_ids_omitted(tmp_path: Path) -> None:
    path = tmp_path / "codex-anon-ids.jsonl"
    path.write_text(
        "\n".join(
            [
                '{"type":"item.started","item":{"type":"command_execution","command":"nimble --client-source nimble-agent-skills search --query a"}}',
                '{"type":"item.completed","item":{"type":"command_execution","command":"nimble --client-source nimble-agent-skills search --query a","aggregated_output":"ok","exit_code":0}}',
                '{"type":"item.started","item":{"type":"command_execution","command":"nimble --client-source nimble-agent-skills extract --url https://example.com"}}',
                '{"type":"item.completed","item":{"type":"command_execution","command":"nimble --client-source nimble-agent-skills extract --url https://example.com","aggregated_output":"done","exit_code":0}}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    events = extract_codex_events(path)
    uses = [e for e in events if isinstance(e, ToolUseEvent)]
    results = [e for e in events if isinstance(e, ToolResultEvent)]
    assert len(uses) == 2 and len(results) == 2
    assert uses[0].id == results[0].tool_use_id == "tool-anon-1"
    assert uses[1].id == results[1].tool_use_id == "tool-anon-2"
    assert uses[0].id != uses[1].id


def test_codex_web_search_jsonl_to_tools(tmp_path: Path) -> None:
    """Regression: Codex emits web_search items, not only command_execution."""
    path = tmp_path / "codex-web-search.jsonl"
    path.write_text(
        "\n".join(
            [
                '{"type":"item.completed","item":{"type":"web_search","id":"ws1","query":"acme corp","action":{"type":"search","query":"acme corp"}}}',
                '{"type":"item.completed","item":{"type":"web_search","id":"ws2","action":{"queries":["acme"]}}}',
                # empty query — should be dropped by payload converter
                '{"type":"item.completed","item":{"type":"web_search","id":"ws3","action":{}}}',
                '{"type":"item.completed","item":{"type":"agent_message","text":"done"}}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    events = extract_codex_events(path)
    kinds = [e.kind for e in events]
    assert "tool_use" in kinds and "tool_result" in kinds
    tools = [e for e in events if isinstance(e, ToolUseEvent)]
    assert any(t.name == "web_search" for t in tools)
    payload = codex_jsonl_to_langfuse_payload(
        path, prompt="who is playing…", model="gpt-5.6-sol", item_id="prod-0474"
    )
    tool_obs = [o for o in payload.observations if o.as_type == "tool"]
    assert len(tool_obs) >= 1
    assert all(o.name == "web_search" for o in tool_obs)
    # Empty-query web_search noise is dropped
    assert all(
        (o.input or {}).get("query") or (o.input or {}).get("queries")
        for o in tool_obs
    )
    assert "web_search" in payload.trace_output["tools_called"]


def test_events_to_payload_empty() -> None:
    payload = events_to_langfuse_payload(
        [],
        prompt="hello",
        runtime="claude",
        model="m",
        item_id="x",
    )
    assert payload.observations == []
    assert payload.trace_output["final_response"] == ""
    assert payload.trace_input["prompt"] == "hello"


def test_tool_result_pairs_with_use() -> None:
    events = [
        ToolUseEvent(
            id="a",
            name="Bash",
            input={
                "command": "nimble --client-source nimble-agent-skills search --query q"
            },
        ),
        ToolResultEvent(tool_use_id="a", output='{"ok":true}', is_error=False),
        GenerationEvent(text="done"),
    ]
    payload = events_to_langfuse_payload(
        events, prompt="q", runtime="claude", model="m"
    )
    tools = [o for o in payload.observations if o.as_type == "tool"]
    assert len(tools) == 1
    assert tools[0].output == '{"ok":true}'
    assert tools[0].metadata["status"] == "completed"


def test_langfuse_otel_env_shape() -> None:
    settings = EvalSettings(
        LANGFUSE_PUBLIC_KEY="pk-lf-test",
        LANGFUSE_SECRET_KEY="sk-lf-test",
        LANGFUSE_HOST="https://us.cloud.langfuse.com",
    )
    env = build_claude_otel_env(settings)
    assert env["CLAUDE_CODE_ENABLE_TELEMETRY"] == "1"
    assert env["CLAUDE_CODE_ENHANCED_TELEMETRY_BETA"] == "1"
    assert env["OTEL_TRACES_EXPORTER"] == "otlp"
    assert env["OTEL_EXPORTER_OTLP_PROTOCOL"] == "http/protobuf"
    assert env["OTEL_EXPORTER_OTLP_ENDPOINT"] == (
        "https://us.cloud.langfuse.com/api/public/otel"
    )
    assert env["OTEL_LOG_USER_PROMPTS"] == "1"
    assert env["OTEL_LOG_TOOL_CONTENT"] == "1"
    auth = langfuse_basic_auth("pk-lf-test", "sk-lf-test")
    assert auth == base64.b64encode(b"pk-lf-test:sk-lf-test").decode()
    assert f"Authorization=Basic {auth}" in env["OTEL_EXPORTER_OTLP_HEADERS"]
    assert "x-langfuse-ingestion-version=4" in env["OTEL_EXPORTER_OTLP_HEADERS"]

    codex_env = build_codex_langfuse_env(settings)
    assert codex_env["TRACE_TO_LANGFUSE"] == "true"
    assert codex_env["LANGFUSE_PUBLIC_KEY"] == "pk-lf-test"
    assert codex_env["LANGFUSE_BASE_URL"] == "https://us.cloud.langfuse.com"


def test_langfuse_otel_endpoint_strips_slash() -> None:
    assert (
        langfuse_otel_endpoint("https://cloud.langfuse.com/")
        == "https://cloud.langfuse.com/api/public/otel"
    )


def test_strip_foreign_provider_secrets() -> None:
    base = {
        "PATH": "/usr/bin",
        "NIMBLE_API_KEY": "nbl_x",
        "OPENAI_API_KEY": "sk-openai",
        "OPENAI_ORG_ID": "org",
        "ANTHROPIC_API_KEY": "sk-ant",
        "CLAUDE_CODE_OAUTH_TOKEN": "oauth",
        "LANGFUSE_SECRET_KEY": "sk-lf",
    }
    claude = strip_foreign_provider_secrets(base, "claude")
    assert "OPENAI_API_KEY" not in claude
    assert "OPENAI_ORG_ID" not in claude
    assert claude["ANTHROPIC_API_KEY"] == "sk-ant"
    assert claude["NIMBLE_API_KEY"] == "nbl_x"

    codex = strip_foreign_provider_secrets(base, "codex")
    assert "ANTHROPIC_API_KEY" not in codex
    assert "CLAUDE_CODE_OAUTH_TOKEN" not in codex
    assert codex["OPENAI_API_KEY"] == "sk-openai"
    assert codex["LANGFUSE_SECRET_KEY"] == "sk-lf"


def test_merge_cli_env_strips_foreign_keys() -> None:
    settings = EvalSettings(
        LANGFUSE_PUBLIC_KEY="pk-lf-test",
        LANGFUSE_SECRET_KEY="sk-lf-test",
        LANGFUSE_HOST="https://us.cloud.langfuse.com",
    )
    env = merge_cli_env(
        {
            "PATH": "/usr/bin",
            "OPENAI_API_KEY": "sk-openai",
            "ANTHROPIC_API_KEY": "sk-ant",
            "CLAUDE_CODE_OAUTH_TOKEN": "oauth",
        },
        settings=settings,
        runtime="claude",
        enable_otel=False,
    )
    assert "OPENAI_API_KEY" not in env
    assert env["ANTHROPIC_API_KEY"] == "sk-ant"

    codex = merge_cli_env(
        {
            "PATH": "/usr/bin",
            "OPENAI_API_KEY": "sk-openai",
            "ANTHROPIC_API_KEY": "sk-ant",
            "CLAUDE_CODE_OAUTH_TOKEN": "oauth",
        },
        settings=settings,
        runtime="codex",
    )
    assert "ANTHROPIC_API_KEY" not in codex
    assert "CLAUDE_CODE_OAUTH_TOKEN" not in codex
    assert codex["OPENAI_API_KEY"] == "sk-openai"
    assert codex["TRACE_TO_LANGFUSE"] == "true"


def test_payload_truncates_huge_tool_output() -> None:
    huge = "x" * 50_000
    events = [
        ToolUseEvent(id="t", name="Bash", input={"command": "cat big"}),
        ToolResultEvent(tool_use_id="t", output=huge),
    ]
    payload = events_to_langfuse_payload(
        events, prompt="p", runtime="claude", model="m"
    )
    out = str(payload.observations[0].output)
    assert len(out) < 20_000
    assert out.endswith("…[truncated]")


@pytest.mark.parametrize(
    "runtime,builder",
    [
        ("claude", claude_stream_to_langfuse_payload),
        ("codex", codex_jsonl_to_langfuse_payload),
    ],
)
def test_fixture_files_exist(runtime: str, builder) -> None:
    name = "claude_minimal.jsonl" if runtime == "claude" else "codex_minimal.jsonl"
    path = FIXTURES / name
    assert path.is_file()
    payload = builder(path, prompt="p", model="m", item_id="id")
    assert payload.metadata["runtime"] == runtime

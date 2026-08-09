"""Unit tests for bashlex-based Nimble CLI family extraction."""

from __future__ import annotations

import pytest

from evals.commons.nimble_cmd import (
    add_nimble_tools,
    family_from_nimble_argv,
    iter_nimble_argvs,
    nimble_tools_from_command,
)


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (["nimble", "search", "--query", "acme"], "nimble search"),
        (["nimble", "map", "--url", "https://x"], "nimble map"),
        (["nimble", "crawl", "run", "--url", "https://x"], "nimble crawl"),
        (["nimble", "tasks", "get", "--id", "t1"], "nimble task"),
        (["nimble", "task", "results", "--id", "t1"], "nimble task"),
        (["nimble", "extract", "run", "--url", "https://x"], "nimble extract"),
        (["nimble", "extract:templates", "list"], "nimble extract"),
        (["nimble", "agents", "list"], "nimble agent"),
        (["nimble", "agents:runs", "create", "--agent-id", "x"], "nimble agent create"),
        (["nimble", "agents", "create", "--agent-name", "x"], "nimble agent create"),
        (["nimble", "agents:templates", "list"], "nimble agent"),
        (
            [
                "nimble",
                "--client-source",
                "nimble-agent-skills",
                "search",
                "--query",
                "acme",
            ],
            "nimble search",
        ),
        (
            [
                "nimble",
                "--transform",
                "data.markdown",
                "extract",
                "run",
                "--url",
                "https://example.com",
            ],
            "nimble extract",
        ),
        (["nimble", "--debug", "map", "--url", "https://x"], "nimble map"),
        (["/usr/local/bin/nimble", "search", "--query", "x"], "nimble search"),
        (["nimble", "--version"], None),
        (["echo", "nimble", "search"], None),
    ],
)
def test_family_from_nimble_argv(argv: list[str], expected: str | None) -> None:
    assert family_from_nimble_argv(argv) == expected


@pytest.mark.parametrize(
    ("command", "expected"),
    [
        ("nimble search --query acme", ["nimble search"]),
        (
            "nimble --client-source nimble-agent-skills agents:runs create --agent-id x",
            ["nimble agent create"],
        ),
        (
            "nimble --client-source nimble-agent-skills search --query 'acme corp'",
            ["nimble search"],
        ),
        (
            'nimble --transform "data.markdown" extract run --url https://example.com',
            ["nimble extract"],
        ),
        ("nimble extract:templates list --limit 100", ["nimble extract"]),
        ("nimble agents:templates list", ["nimble agent"]),
        ("nimble agents run --agent-name foo --input 'hi'", ["nimble agent"]),
        (
            "nimble agents:runs get --agent-id a --run-id r",
            ["nimble agent"],
        ),
        (
            "nimble agents:runs result --agent-id a --run-id r",
            ["nimble agent"],
        ),
        (
            "nimble agents:runs stream-events --agent-id a --run-id r",
            ["nimble agent"],
        ),
        ("nimble crawl status --id abc", ["nimble crawl"]),
        ("nimble crawl run --url https://docs.example.com", ["nimble crawl"]),
        ("nimble map --url https://docs.example.com --limit 1000", ["nimble map"]),
        ("nimble tasks results --id tid", ["nimble task"]),
        # Nested zsh -lc (Codex shape)
        (
            '/bin/zsh -lc "nimble --client-source nimble-agent-skills search --query acme"',
            ["nimble search"],
        ),
        (
            "/bin/zsh -lc 'nimble map --url https://x && nimble crawl run --url https://x'",
            ["nimble map", "nimble crawl"],
        ),
        (
            '/bin/zsh -lc "nimble --client-source nimble-agent-skills agents list '
            '&& nimble --client-source nimble-agent-skills agents:templates list"',
            ["nimble agent"],
        ),
        # Multi-line script inside -lc
        (
            '/bin/zsh -lc "mkdir -p .nimble\n'
            'nimble --transform \\"data.markdown\\" extract --url '
            '\\"https://example.com\\" --format markdown > .nimble/out.md\n'
            'wc -l .nimble/out.md"',
            ["nimble extract"],
        ),
        # Must not false-positive on echo / prose
        ("echo 'nimble search --query acme'", []),
        ("cat <<'EOF'\nnimble search --query acme\nEOF", []),
        ("nimble --version && echo ok", []),
        # Dedup
        (
            "nimble search --query a; nimble search --query b",
            ["nimble search"],
        ),
        # env wrapper
        ("env nimble search --query acme", ["nimble search"]),
        ("/usr/bin/env nimble extract run --url https://x", ["nimble extract"]),
    ],
)
def test_nimble_tools_from_command(command: str, expected: list[str]) -> None:
    assert nimble_tools_from_command(command) == expected


def test_iter_nimble_argvs_nested_shell() -> None:
    argvs = iter_nimble_argvs(
        '/bin/zsh -lc "nimble --client-source x agents:runs create --agent-id a"'
    )
    assert len(argvs) == 1
    assert argvs[0][0] == "nimble"
    assert "agents:runs" in argvs[0]


def test_add_nimble_tools_appends_unique() -> None:
    tools = ["web_search"]
    add_nimble_tools(
        "nimble --client-source nimble-agent-skills search --query a",
        tools,
    )
    add_nimble_tools(
        "nimble --client-source nimble-agent-skills search --query b",
        tools,
    )
    assert tools == ["web_search", "nimble search"]


def test_normalize_wrapper_matches_module() -> None:
    from evals.commons.normalize import _add_nimble_tools

    tools: list[str] = []
    _add_nimble_tools(
        '/bin/zsh -lc "nimble --client-source nimble-agent-skills '
        'agents:runs create --agent-id x"',
        tools,
    )
    assert tools == ["nimble agent create"]


@pytest.mark.parametrize(
    "command",
    [
        # Codex-shaped argv layouts (synthetic placeholders only — never copy
        # prompts/domains from nimble-web-expert-production or local traces).
        'nimble --client-source nimble-agent-skills search --query \'"WidgetCo Holdings, LLC" Delaware\' --max-results 10 --search-depth deep',
        "nimble --client-source nimble-agent-skills extract run --url 'https://example.com/' --format markdown",
        "nimble --client-source nimble-agent-skills extract:templates list --limit 100",
        "nimble map --url \"https://docs.example.com/rest-api\" --limit 100000 --sitemap include",
        "nimble crawl run --url \"https://docs.example.com/rest-api\" --limit 500",
        "nimble crawl status --id \"9630a454-cf5d-4181-b3c3-ac311cffc545\"",
    ],
)
def test_trace_shaped_commands_classify(command: str) -> None:
    tools = nimble_tools_from_command(command)
    assert tools, f"expected a nimble family for {command!r}"
    assert all(t.startswith("nimble ") for t in tools)

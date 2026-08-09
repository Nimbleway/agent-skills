"""Parse Nimble CLI invocations out of agent shell commands via bashlex."""

from __future__ import annotations

from pathlib import PurePosixPath

import bashlex
from bashlex import ast

# Top-level Nimble resource / verb families we score in evals.
_FAMILY_PREFIXES = (
    "search",
    "extract",
    "map",
    "crawl",
    "agent",
    "agents",
    "task",
    "tasks",
)

# Global options that may appear before the subcommand (from `nimble --help`).
_GLOBAL_FLAGS_WITH_VALUE = frozenset(
    {
        "--base-url",
        "--format",
        "--format-error",
        "--transform",
        "--transform-error",
        "--api-key",
        "--client-source",
    }
)
_GLOBAL_FLAGS_BOOL = frozenset(
    {
        "--debug",
        "--raw-output",
        "-r",
        "--help",
        "-h",
        "--version",
        "-v",
    }
)
_SHELL_BINARIES = frozenset(
    {
        "sh",
        "bash",
        "zsh",
        "dash",
        "/bin/sh",
        "/bin/bash",
        "/bin/zsh",
        "/usr/bin/sh",
        "/usr/bin/bash",
        "/usr/bin/zsh",
        "/usr/bin/env",
    }
)


def _basename(token: str) -> str:
    return PurePosixPath(token).name


def _is_nimble_bin(token: str) -> bool:
    return _basename(token) == "nimble"


def _normalize_family(subcommand: str, argv: list[str]) -> str | None:
    """Map a Nimble subcommand token to a scorer family name."""
    raw = subcommand.lower()
    head = raw.split(":", 1)[0]
    # Legacy / typo forms seen in agent traces.
    if head.startswith("extract"):
        family = "extract"
    elif head in {"agent", "agents"}:
        family = "agent"
    elif head in {"task", "tasks"}:
        family = "task"
    elif head in {"search", "map", "crawl"}:
        family = head
    else:
        return None

    name = f"nimble {family}"
    # Forbidden-tool scorer looks for create variants.
    if family == "agent" and any(tok == "create" for tok in argv):
        return "nimble agent create"
    return name


def _subcommand_after_globals(argv: list[str]) -> tuple[str | None, list[str]]:
    """Return (subcommand, full argv) after skipping nimble global flags."""
    if not argv or not _is_nimble_bin(argv[0]):
        return None, argv
    i = 1
    while i < len(argv):
        tok = argv[i]
        if tok in _GLOBAL_FLAGS_BOOL:
            i += 1
            continue
        if tok in _GLOBAL_FLAGS_WITH_VALUE:
            i += 2
            continue
        if tok.startswith("--") and "=" in tok:
            flag = tok.split("=", 1)[0]
            if flag in _GLOBAL_FLAGS_WITH_VALUE or flag in _GLOBAL_FLAGS_BOOL:
                i += 1
                continue
        # First non-global token is the resource/verb.
        return tok, argv
    return None, argv


def family_from_nimble_argv(argv: list[str]) -> str | None:
    """Classify a tokenized ``nimble …`` argv into a scorer tool name."""
    sub, full = _subcommand_after_globals(argv)
    if not sub:
        return None
    return _normalize_family(sub, full)


class _CommandCollector(ast.nodevisitor):
    def __init__(self) -> None:
        self.argvs: list[list[str]] = []

    def visitcommand(self, n, parts):  # noqa: ANN001
        words: list[str] = []
        for part in parts:
            if getattr(part, "kind", None) == "word":
                words.append(part.word)
        if words:
            self.argvs.append(words)
        return True


def _parse_argvs(script: str) -> list[list[str]]:
    script = (script or "").strip()
    if not script:
        return []
    try:
        trees = bashlex.parse(script)
    except bashlex.errors.ParsingError:
        return []
    except Exception:  # noqa: BLE001 — bashlex can raise assorted parse failures
        return []
    collector = _CommandCollector()
    for tree in trees:
        collector.visit(tree)
    return collector.argvs


def iter_nimble_argvs(command: str) -> list[list[str]]:
    """Extract every ``nimble …`` argv list from a shell command string."""
    found: list[list[str]] = []
    seen: set[tuple[str, ...]] = set()

    def _consider(argv: list[str]) -> None:
        if not argv:
            return
        # ``env nimble …``
        if _basename(argv[0]) == "env" and len(argv) >= 2 and _is_nimble_bin(argv[1]):
            argv = argv[1:]
        if _is_nimble_bin(argv[0]):
            key = tuple(argv)
            if key not in seen:
                seen.add(key)
                found.append(argv)
            return
        # Nested shell: bash/zsh -lc '…' / -c '…'
        bin_name = argv[0]
        if bin_name not in _SHELL_BINARIES and _basename(bin_name) not in {
            "sh",
            "bash",
            "zsh",
            "dash",
            "env",
        }:
            return
        i = 1
        # ``/usr/bin/env bash -lc …``
        if _basename(bin_name) == "env" and i < len(argv):
            i += 1
        while i < len(argv):
            tok = argv[i]
            if tok in {"-c", "-lc"} and i + 1 < len(argv):
                for nested in _parse_argvs(argv[i + 1]):
                    _consider(nested)
                return
            if tok.startswith("-") and tok not in {"-c", "-lc"}:
                i += 1
                continue
            break

    for argv in _parse_argvs(command):
        _consider(argv)
    return found


def nimble_tools_from_command(command: str) -> list[str]:
    """Return unique scorer tool names for Nimble CLIs inside ``command``."""
    tools: list[str] = []
    for argv in iter_nimble_argvs(command):
        family = family_from_nimble_argv(argv)
        if family and family not in tools:
            tools.append(family)
    return tools


def add_nimble_tools(command: str, tools: list[str]) -> None:
    """Append newly discovered Nimble tool families onto ``tools``."""
    for name in nimble_tools_from_command(command):
        if name not in tools:
            tools.append(name)

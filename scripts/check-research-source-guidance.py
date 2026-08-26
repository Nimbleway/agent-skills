#!/usr/bin/env python3
"""Validate the /nimble-research Agent API V2 source-guidance contract."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
COMMAND = ROOT / "commands" / "nimble-research.md"
HOSTNAME = re.compile(
    r"(?=.{1,253}\Z)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)*"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\Z"
)


def validate_source_guidance(value: Any) -> None:
    if not isinstance(value, dict):
        raise ValueError("sources must be an object")

    unknown = set(value) - {"allow", "block", "prioritize", "avoid"}
    if unknown:
        raise ValueError(f"unsupported sources keys: {sorted(unknown)}")

    for field in ("allow", "block"):
        groups = value.get(field, [])
        if not isinstance(groups, list):
            raise ValueError(f"sources.{field} must be an array")
        for index, group in enumerate(groups):
            if not isinstance(group, dict):
                raise ValueError(f"sources.{field}[{index}] must be an object")
            if set(group) - {"title", "domains", "order"}:
                raise ValueError(f"sources.{field}[{index}] has unsupported keys")
            title = group.get("title")
            domains = group.get("domains")
            if not isinstance(title, str) or not title.strip():
                raise ValueError(f"sources.{field}[{index}].title must be non-empty")
            if not isinstance(domains, list) or not domains:
                raise ValueError(f"sources.{field}[{index}].domains must be a non-empty array")
            for domain_index, domain in enumerate(domains):
                if not isinstance(domain, str) or not domain.strip():
                    raise ValueError(
                        f"sources.{field}[{index}].domains[{domain_index}] must be non-empty"
                    )
                if not HOSTNAME.fullmatch(domain.strip()):
                    raise ValueError(
                        f"sources.{field}[{index}].domains[{domain_index}] must be a hostname"
                    )
            order = group.get("order")
            if order is not None and (
                not isinstance(order, int) or isinstance(order, bool) or order < 0
            ):
                raise ValueError(f"sources.{field}[{index}].order must be a non-negative integer")

    for field in ("prioritize", "avoid"):
        guidance = value.get(field)
        if guidance is not None and not isinstance(guidance, str):
            raise ValueError(f"sources.{field} must be a string")


def expect_invalid(value: Any, needle: str) -> None:
    try:
        validate_source_guidance(value)
    except ValueError as exc:
        if needle not in str(exc):
            raise AssertionError(f"expected {needle!r} in {str(exc)!r}") from exc
    else:
        raise AssertionError(f"expected invalid source guidance: {value!r}")


def command_contract() -> dict[str, Any]:
    text = COMMAND.read_text(encoding="utf-8")
    match = re.search(r"```json source-guidance-contract\n(.*?)\n```", text, re.DOTALL)
    if not match:
        raise AssertionError("nimble-research command is missing source-guidance-contract")
    return json.loads(match.group(1))


def self_test() -> None:
    validate_source_guidance(command_contract())
    validate_source_guidance(
        {
            "allow": [{"title": "Official", "domains": ["example.com"]}],
            "block": [{"title": "Excluded", "domains": ["example.net"], "order": 2}],
            "prioritize": "Prefer primary sources.",
            "avoid": "Avoid aggregators.",
        }
    )

    # Exact live failure class: string entries must fail before create.
    expect_invalid({"allow": ["https://example.com"]}, "allow[0] must be an object")
    expect_invalid({"block": ["example.net"]}, "block[0] must be an object")
    expect_invalid({"allow": [{"domains": ["example.com"]}]}, "title must be non-empty")
    expect_invalid({"allow": [{"title": "Official", "domains": []}]}, "non-empty array")
    expect_invalid(
        {"allow": [{"title": "Official", "domains": ["https://example.com/docs"]}]},
        "must be a hostname",
    )
    expect_invalid(
        {"allow": [{"title": "Official", "domains": ["not a hostname"]}]},
        "must be a hostname",
    )
    expect_invalid(
        {"allow": [{"title": "Official", "domains": ["example.com?x=1"]}]},
        "must be a hostname",
    )
    expect_invalid(
        {"allow": [{"title": "Official", "domains": ["example.com"], "order": -1}]},
        "non-negative integer",
    )
    expect_invalid({"prioritize": ["Official"]}, "prioritize must be a string")
    expect_invalid({"avoid": {"title": "Blogs"}}, "avoid must be a string")
    expect_invalid({"allow": [], "extra": True}, "unsupported sources keys")


if __name__ == "__main__":
    self_test()
    print("RESEARCH_SOURCE_GUIDANCE_PASS")

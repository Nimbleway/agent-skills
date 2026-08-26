#!/usr/bin/env python3
"""Fail closed when a Nimble Agent result exceeds its unique-source budget."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


def canonical_url(value: str) -> str:
    """Normalize URL identity without discarding query parameters."""
    parsed = urlsplit(value.strip())
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise ValueError(f"invalid HTTP(S) source URL: {value!r}")
    scheme = parsed.scheme.lower()
    host = parsed.hostname.lower()
    port = parsed.port
    netloc = host if port in {None, 80 if scheme == "http" else 443} else f"{host}:{port}"
    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/")
    return urlunsplit((scheme, netloc, path, parsed.query, ""))


def find_trust(payload: object) -> dict[str, object]:
    """Accept direct CLI JSON or a single data/result envelope."""
    if isinstance(payload, dict):
        trust = payload.get("trust")
        if isinstance(trust, dict):
            return trust
        for key in ("data", "result"):
            nested = payload.get(key)
            if isinstance(nested, dict):
                try:
                    return find_trust(nested)
                except ValueError:
                    pass
    raise ValueError("result has no trust object")


def unique_source_urls(payload: object) -> set[str]:
    trust = find_trust(payload)
    sources = trust.get("sources")
    if not isinstance(sources, list):
        raise ValueError("result trust.sources is not a list")

    urls: set[str] = set()
    for index, source in enumerate(sources):
        if not isinstance(source, dict) or not isinstance(source.get("url"), str):
            raise ValueError(f"trust.sources[{index}] has no string url")
        urls.add(canonical_url(source["url"]))
    return urls


def within_budget(payload: object, budget: int) -> bool:
    if budget < 1:
        raise ValueError("budget must be a positive integer")
    return len(unique_source_urls(payload)) <= budget


def self_test() -> None:
    within = {
        "trust": {
            "sources": [
                {"url": "HTTPS://Example.com/a#claim-1"},
                {"url": "https://example.com/a/#claim-2"},
                {"url": "https://example.com/b?view=full"},
            ]
        }
    }
    assert len(unique_source_urls(within)) == 2
    assert within_budget(within, 2)

    adversarial = {
        "data": {
            "trust": {
                "sources": [
                    {"url": f"https://official.example/page-{index}"}
                    for index in range(7)
                ]
            }
        }
    }
    assert len(unique_source_urls(adversarial)) == 7
    assert not within_budget(adversarial, 6)
    try:
        unique_source_urls({"trust": {"sources": [{"title": "missing URL"}]}})
    except ValueError:
        pass
    else:
        raise AssertionError("malformed trust source must fail closed")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("result", nargs="?", type=Path)
    parser.add_argument("--budget", type=int)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if not args.self_test and (args.result is None or args.budget is None):
        parser.error("--budget and result are required unless --self-test is used")
    if args.budget is not None and args.budget < 1:
        parser.error("--budget must be a positive integer")
    return args


def main() -> int:
    args = parse_args()
    if args.self_test:
        self_test()
        print("research source-budget self-test passed")
        return 0

    try:
        payload = json.loads(args.result.read_text(encoding="utf-8"))
        urls = unique_source_urls(payload)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"HOLD_SOURCE_BUDGET_INVALID_RESULT: {exc}", file=sys.stderr)
        return 2

    observed = len(urls)
    if observed > args.budget:
        print(
            "HOLD_SOURCE_BUDGET_EXCEEDED: "
            f"budget={args.budget} observed_unique_sources={observed}",
            file=sys.stderr,
        )
        return 1

    print(f"SOURCE_BUDGET_PASS budget={args.budget} observed_unique_sources={observed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

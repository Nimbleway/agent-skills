#!/usr/bin/env python3
"""Fail closed when a research answer is not mapped to trust.claims."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit


CALLOUT = re.compile(r"\[(\d+)\]")
TABLE_SEPARATOR = re.compile(r"^\|(?:\s*:?-+:?\s*\|)+$")
UNKNOWN_VALUES = {"unknown", "omitted", "not disclosed"}
ROOT = Path(__file__).resolve().parents[1]
COMMAND = ROOT / "commands" / "nimble-research.md"


def canonical_url(value: str) -> str:
    parsed = urlsplit(value.strip())
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise ValueError(f"invalid HTTP(S) source URL: {value!r}")
    scheme, host, port = parsed.scheme.lower(), parsed.hostname.lower(), parsed.port
    netloc = host if port in {None, 80 if scheme == "http" else 443} else f"{host}:{port}"
    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/")
    return urlunsplit((scheme, netloc, path, parsed.query, ""))


def find_result(payload: object) -> dict[str, Any]:
    if isinstance(payload, dict):
        if isinstance(payload.get("trust"), dict) and payload.get("output") is not None:
            return payload
        for key in ("data", "result"):
            nested = payload.get(key)
            if isinstance(nested, dict):
                try:
                    return find_result(nested)
                except ValueError:
                    pass
    raise ValueError("result has no output/trust pair")


def output_text(result: dict[str, Any]) -> str:
    output = result.get("output")
    if isinstance(output, str):
        return output
    if isinstance(output, dict) and isinstance(output.get("content"), str):
        return output["content"]
    raise ValueError("result output is not text")


def trusted_callouts(result: dict[str, Any]) -> set[int]:
    trust = result["trust"]
    sources = trust.get("sources")
    claims = trust.get("claims")
    if not isinstance(sources, list) or not isinstance(claims, list):
        raise ValueError("trust.sources and trust.claims must be arrays")

    source_urls: set[str] = set()
    for index, source in enumerate(sources):
        if not isinstance(source, dict) or not isinstance(source.get("url"), str):
            raise ValueError(f"trust.sources[{index}] has no string url")
        source_urls.add(canonical_url(source["url"]))

    callouts: set[int] = set()
    for index, claim in enumerate(claims):
        if not isinstance(claim, dict):
            raise ValueError(f"trust.claims[{index}] is not an object")
        callout = claim.get("callout")
        citations = claim.get("citations")
        if not isinstance(callout, int) or isinstance(callout, bool) or callout < 1:
            raise ValueError(f"trust.claims[{index}].callout is not a positive integer")
        if callout in callouts:
            raise ValueError(f"duplicate trust.claims callout [{callout}]")
        if not isinstance(citations, list) or not citations:
            raise ValueError(f"trust.claims callout [{callout}] has no citations")
        for citation_index, citation in enumerate(citations):
            if not isinstance(citation, dict) or not isinstance(citation.get("url"), str):
                raise ValueError(f"trust.claims callout [{callout}] citation {citation_index} has no URL")
            url = canonical_url(citation["url"])
            if url not in source_urls:
                raise ValueError(f"trust.claims callout [{callout}] cites a URL absent from trust.sources")
        callouts.add(callout)
    return callouts


def citations(text: str) -> set[int]:
    return {int(value) for value in CALLOUT.findall(text)}


def is_unknown(text: str) -> bool:
    plain = re.sub(r"[*_`]", "", text).strip().lower().rstrip(".")
    return plain in UNKNOWN_VALUES


def audit(payload: object) -> list[str]:
    result = find_result(payload)
    text = output_text(result)
    trusted = trusted_callouts(result)
    errors: list[str] = []
    table_callouts: set[int] = set()
    lines = text.splitlines()

    table_rows = [line for line in lines if line.strip().startswith("|")]
    data_rows = [line for line in table_rows if not TABLE_SEPARATOR.fullmatch(line.strip())]
    if len(data_rows) < 2:
        errors.append("answer has no decision table")
    else:
        for row_index, row in enumerate(data_rows[1:], start=1):
            cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
            if len(cells) < 3:
                errors.append(f"decision table row {row_index} has fewer than three cells")
                continue
            for column_index, cell in enumerate(cells[1:], start=1):
                refs = citations(cell)
                invalid = refs - trusted
                if invalid:
                    errors.append(f"decision table row {row_index} column {column_index} uses unmapped callouts {sorted(invalid)}")
                if not is_unknown(cell) and not refs:
                    errors.append(f"decision table row {row_index} column {column_index} is populated but uncited")
                table_callouts.update(refs & trusted)

    recommendation = re.search(
        r"^##\s+Recommendation[^\n]*\n(.*?)(?=^##\s+|\Z)", text, re.MULTILINE | re.DOTALL | re.IGNORECASE
    )
    if not recommendation:
        errors.append("answer has no Recommendation section")
    else:
        paragraphs = [part.strip() for part in re.split(r"\n\s*\n", recommendation.group(1)) if part.strip()]
        if not paragraphs:
            errors.append("Recommendation section is empty")
        for paragraph_index, paragraph in enumerate(paragraphs, start=1):
            refs = citations(paragraph)
            invalid = refs - trusted
            if invalid:
                errors.append(f"recommendation paragraph {paragraph_index} uses unmapped callouts {sorted(invalid)}")
            if not refs:
                errors.append(f"recommendation paragraph {paragraph_index} is decision-driving but uncited")
            if refs - table_callouts:
                errors.append(
                    f"recommendation paragraph {paragraph_index} relies on claims not mapped by the decision table: {sorted(refs - table_callouts)}"
                )

    # Reject extra uncited factual prose outside the table, recommendation,
    # headings, and source index. Unknown exemptions apply only to whole cells.
    scrubbed = re.sub(
        r"^##\s+Recommendation[^\n]*\n.*?(?=^##\s+|\Z)", "", text,
        flags=re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    scrubbed = re.split(r"^Source index:\s*$", scrubbed, flags=re.MULTILINE | re.IGNORECASE)[0]
    for line_number, line in enumerate(scrubbed.splitlines(), start=1):
        value = line.strip()
        if not value or value.startswith("#") or value.startswith("|") or value.startswith("---"):
            continue
        if value.lower().startswith("cited from"):
            continue
        refs = citations(value)
        if refs - trusted:
            errors.append(f"answer line {line_number} uses unmapped callouts {sorted(refs - trusted)}")
        elif not refs:
            errors.append(f"answer line {line_number} contains an extra uncited claim")

    return errors


def fixture(name: str) -> dict[str, Any]:
    return {
        "output": {"type": "text", "content": name},
        "trust": {
            "sources": [
                {"url": "https://official.example/pricing"},
                {"url": "https://official.example/collaboration"},
            ],
            "claims": [
                {"callout": 1, "citations": [{"url": "https://official.example/pricing"}]},
                {"callout": 2, "citations": [{"url": "https://official.example/collaboration"}]},
            ],
        },
    }


def expect_hold(markdown: str, needle: str, mutate: Any = None) -> None:
    payload = fixture(markdown)
    if mutate:
        mutate(payload)
    found = audit(payload)
    if not any(needle in error for error in found):
        raise AssertionError(f"expected {needle!r}; got {found!r}")


def self_test() -> None:
    valid = fixture(
        "# Comparison\n\n| Field | A | B |\n|---|---|---|\n"
        "| Price | $10 [1] | Unknown |\n| Collaboration | Client channels [2] | Unknown |\n\n"
        "## Recommendation\n\nChoose A for documented client channels [2].\n\nSource index:\n[1] Price\n[2] Collaboration"
    )
    assert audit(valid) == []

    expect_hold(
        "| Field | A | B |\n|---|---|---|\n| Price | $10 | Unknown |\n\n## Recommendation\nChoose A [1].",
        "populated but uncited",
    )
    expect_hold(
        "| Field | A | B |\n|---|---|---|\n| Price | $10 [1] | Unknown |\n\n## Recommendation\nChoose A because it supports guests.",
        "decision-driving but uncited",
    )
    expect_hold(
        "| Field | A | B |\n|---|---|---|\n| Price | $10 [1] | Unknown |\n\n## Recommendation\nChoose A for client channels [2].",
        "relies on claims not mapped by the decision table",
    )
    expect_hold(
        "| Field | A | B |\n|---|---|---|\n| Price | $10 [9] | Unknown |\n\n## Recommendation\nChoose A [9].",
        "unmapped callouts",
    )
    expect_hold(
        "A has unlimited retention.\n\n| Field | A | B |\n|---|---|---|\n| Price | $10 [1] | Unknown |\n\n## Recommendation\nChoose A [1].",
        "extra uncited claim",
    )
    expect_hold(
        "| Field | A | B |\n|---|---|---|\n| Price | Unknown, but costs $10 | Unknown |\n\n## Recommendation\nChoose A [1].",
        "populated but uncited",
    )
    expect_hold(
        "| Field | A | B |\n|---|---|---|\n| Price | $10 [1] | Unknown |\n\n## Recommendation\nChoose A because its uncited guest support is unknown but superior.",
        "decision-driving but uncited",
    )
    expect_hold(
        "Unknown pricing, but A costs $10.\n\n| Field | A | B |\n|---|---|---|\n| Price | $10 [1] | Unknown |\n\n## Recommendation\nChoose A [1].",
        "extra uncited claim",
    )

    mismatched = fixture(
        "| Field | A | B |\n|---|---|---|\n| Price | $10 [1] | Unknown |\n\n## Recommendation\nChoose A [1]."
    )
    mismatched["trust"]["claims"][0]["citations"][0]["url"] = "https://other.example/missing"
    try:
        audit(mismatched)
    except ValueError as exc:
        assert "absent from trust.sources" in str(exc)
    else:
        raise AssertionError("mismatched claim/source URL must fail closed")

    malformed_callouts = []
    for invalid_callout in (True, 0, -1):
        malformed = fixture(
            "| Field | A | B |\n|---|---|---|\n| Price | $10 [1] | Unknown |\n\n## Recommendation\nChoose A [1]."
        )
        malformed["trust"]["claims"][0]["callout"] = invalid_callout
        malformed_callouts.append(malformed)
        try:
            audit(malformed)
        except ValueError as exc:
            assert "positive integer" in str(exc)
        else:
            raise AssertionError(f"invalid callout {invalid_callout!r} must fail closed")
    duplicate = fixture(
        "| Field | A | B |\n|---|---|---|\n| Price | $10 [1] | Unknown |\n\n## Recommendation\nChoose A [1]."
    )
    duplicate["trust"]["claims"][1]["callout"] = 1
    malformed_callouts.append(duplicate)
    try:
        audit(duplicate)
    except ValueError as exc:
        assert "duplicate" in str(exc)
    else:
        raise AssertionError("duplicate callout must fail closed")

    regression = json.loads(
        (Path(__file__).parent / "fixtures" / "nimble-research-uncited-recommendation.json").read_text(encoding="utf-8")
    )
    regression_errors = audit(regression)
    assert any("populated but uncited" in error for error in regression_errors)
    assert any("decision-driving but uncited" in error for error in regression_errors)

    command = COMMAND.read_text(encoding="utf-8")
    block = re.search(
        r"```bash claim-grounding-audit\npython3 - [^\n]+ <<'PY'\n(.*?)\nPY\n```",
        command,
        re.DOTALL,
    )
    if not block:
        raise AssertionError("nimble-research command is missing its portable claim audit")
    with tempfile.TemporaryDirectory() as directory:
        valid_path = Path(directory) / "valid.json"
        valid_path.write_text(json.dumps(valid), encoding="utf-8")
        valid_run = subprocess.run(
            [sys.executable, "-", str(valid_path)],
            input=block.group(1),
            text=True,
            capture_output=True,
            check=False,
        )
        assert valid_run.returncode == 0, valid_run.stderr
        inline_adversarial = [
            regression,
            fixture("| Field | A | B |\n|---|---|---|\n| Price | $10 | Unknown |\n\n## Recommendation\nChoose A [1]."),
            fixture("| Field | A | B |\n|---|---|---|\n| Price | $10 [1] | Unknown |\n\n## Recommendation\nChoose A for clients [2]."),
            fixture("| Field | A | B |\n|---|---|---|\n| Price | $10 [9] | Unknown |\n\n## Recommendation\nChoose A [9]."),
            fixture("A has unlimited retention.\n\n| Field | A | B |\n|---|---|---|\n| Price | $10 [1] | Unknown |\n\n## Recommendation\nChoose A [1]."),
            fixture("| Field | A | B |\n|---|---|---|\n| Price | Unknown, but costs $10 | Unknown |\n\n## Recommendation\nChoose A [1]."),
            fixture("| Field | A | B |\n|---|---|---|\n| Price | $10 [1] | Unknown |\n\n## Recommendation\nChoose A because its uncited guest support is unknown but superior."),
            fixture("Unknown pricing, but A costs $10.\n\n| Field | A | B |\n|---|---|---|\n| Price | $10 [1] | Unknown |\n\n## Recommendation\nChoose A [1]."),
            mismatched,
            *malformed_callouts,
        ]
        for index, payload in enumerate(inline_adversarial):
            path = Path(directory) / f"adversarial-{index}.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            failed_run = subprocess.run(
                [sys.executable, "-", str(path)],
                input=block.group(1),
                text=True,
                capture_output=True,
                check=False,
            )
            assert failed_run.returncode != 0, f"inline adversarial case {index} passed"
            assert "HOLD_CLAIM_GROUNDING_" in failed_run.stderr


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("result", nargs="?", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if not args.self_test and args.result is None:
        parser.error("result is required unless --self-test is used")
    return args


def main() -> int:
    args = parse_args()
    if args.self_test:
        self_test()
        print("RESEARCH_CLAIM_GROUNDING_SELF_TEST_PASS")
        return 0
    try:
        payload = json.loads(args.result.read_text(encoding="utf-8"))
        errors = audit(payload)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"HOLD_CLAIM_GROUNDING_INVALID_RESULT: {exc}", file=sys.stderr)
        return 2
    if errors:
        for error in errors:
            print(f"HOLD_CLAIM_GROUNDING_UNMAPPED: {error}", file=sys.stderr)
        return 1
    print("CLAIM_GROUNDING_PASS every decision-driving claim maps to trust.claims")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Routing eval for nimble-web-expert.

Asks: given a user prompt, which Nimble capability does the skill's routing
guidance select? Grades the routing text in SKILL.md — it does not run Nimble,
so it burns no credits and needs no API key.

The routing text is read straight out of SKILL.md at run time, so the eval and
the doc cannot drift apart.

Usage:
    python3 scripts/run-routing-eval.py
    python3 scripts/run-routing-eval.py --runs 3 --model sonnet
    python3 scripts/run-routing-eval.py --case 1
"""

from __future__ import annotations  # keeps `X | None` hints working on Python 3.9

import argparse
import concurrent.futures
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / "skills/nimble-web-expert/SKILL.md"
CASES = REPO / "evals/nimble-web-expert-routing.json"

VALID = ["EXTRACT", "TEMPLATE", "SEARCH", "WSA", "MAP", "CRAWL"]


def routing_text() -> str:
    """Pull the two routing-bearing sections out of SKILL.md."""
    md = SKILL.read_text(encoding="utf-8")

    def section(start: str, end: str) -> str:
        i = md.index(start)
        j = md.index(end, i)
        return md[i:j].strip()

    return (
        section("## Core principles", "## Capabilities")
        + "\n\n"
        + section("## Analyze & Route", "## Workflow")
    )


PROMPT = """You are grading a routing decision, not doing the task.

Below is the routing guidance from the `nimble-web-expert` skill. Apply it \
literally to the user request and report which capability it selects.

<routing-guidance>
{guidance}
</routing-guidance>

User request: "{request}"

Answer on two lines, nothing else:
ROUTE: <one of EXTRACT|TEMPLATE|SEARCH|WSA|MAP|CRAWL>
FORK: <YES if the guidance says to offer the researched-report vs quick-scan \
choice before running, otherwise NO>
"""


def ask(request: str, guidance: str, model: str | None, timeout: int):
    """Return (route, fork). A None route means no usable answer — see stderr."""
    cmd = ["claude", "-p", PROMPT.format(guidance=guidance, request=request)]
    if model:
        cmd += ["--model", model]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, cwd=REPO
        )
    except FileNotFoundError:
        sys.exit("claude CLI not found on PATH — install it and sign in, then re-run.")
    except subprocess.TimeoutExpired:
        print(f"  timeout after {timeout}s: {request[:50]}", file=sys.stderr)
        return None, None

    if proc.returncode != 0:
        # An infra failure, not a routing disagreement — say so loudly so it
        # isn't silently tallied as a NO-ANSWER vote.
        err = (proc.stderr or proc.stdout or "").strip().splitlines()
        print(
            f"  claude exited {proc.returncode} for {request[:50]!r}: "
            f"{err[-1] if err else '<no output>'}",
            file=sys.stderr,
        )
        return None, None

    out = proc.stdout
    route = re.search(r"ROUTE:\s*([A-Z]+)", out)
    fork = re.search(r"FORK:\s*(YES|NO)", out)
    return (
        route.group(1) if route and route.group(1) in VALID else None,
        (fork.group(1) == "YES") if fork else None,
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=1, help="runs per case (majority vote)")
    ap.add_argument("--model", default=None)
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--case", type=int, default=None, help="run a single case id")
    args = ap.parse_args()

    guidance = routing_text()
    cases = json.loads(CASES.read_text(encoding="utf-8"))["cases"]
    if args.case is not None:
        cases = [c for c in cases if c["id"] == args.case]
        if not cases:
            print(f"no case with id {args.case}", file=sys.stderr)
            return 2

    jobs = [(c, r) for c in cases for r in range(args.runs)]
    results: dict[int, list] = {c["id"]: [] for c in cases}

    with concurrent.futures.ThreadPoolExecutor(args.workers) as pool:
        futures = {
            pool.submit(ask, c["prompt"], guidance, args.model, args.timeout): c["id"]
            for c, _ in jobs
        }
        for f in concurrent.futures.as_completed(futures):
            results[futures[f]].append(f.result())

    print(f"\nRouting eval — {len(cases)} cases x {args.runs} run(s)\n")
    failed = []
    for c in cases:
        routes = [r for r, _ in results[c["id"]] if r]
        forks = [k for _, k in results[c["id"]] if k is not None]
        route = Counter(routes).most_common(1)[0][0] if routes else "NO-ANSWER"
        agree = f"{routes.count(route)}/{args.runs}" if routes else "0/%d" % args.runs

        ok = route == c["expected_route"]
        fork_ok = True
        note = ""
        if c.get("expect_fork_offer") is not None and forks:
            fork = Counter(forks).most_common(1)[0][0]
            fork_ok = fork == c["expect_fork_offer"]
            if not fork_ok:
                note = f"  (fork offer: got {fork}, want {c['expect_fork_offer']})"

        mark = "PASS" if ok and fork_ok else "FAIL"
        if mark == "FAIL":
            failed.append(c)
        print(f"  [{mark}] {c['id']:>2}. {c['prompt'][:62]}")
        print(f"         want {c['expected_route']:<8} got {route:<8} ({agree}){note}")

    print(f"\n{len(cases) - len(failed)}/{len(cases)} passed")
    for c in failed:
        print(f"\n  case {c['id']} rationale: {c['why']}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

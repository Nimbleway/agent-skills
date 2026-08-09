"""Run nimble-web-expert evals on assistant production prompts.

uv run python -m evals.suites.web_expert --dataset-name=nimble-web-expert-production
uv run python -m evals.suites.web_expert --smoke
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from evals.backends.claude import run_claude
from evals.backends.codex import (
    DEFAULT_SMOKE_TIMEOUT_SECONDS,
    ensure_codex_skill_link,
    run_codex,
)
from evals.commons.dataset import DatasetItem, load_dataset, prompt_from_input
from evals.commons.eval_prompt import CLAUDE_SKILL_SLASH, CODEX_SKILL_SLASH
from evals.commons.gold import solution_key
from evals.commons.run_experiment import run_experiment
from evals.commons.settings import EvalSettings
from evals.commons.trace import NormalizedTrace
from evals.scorers import WEB_EXPERT_EVALUATORS

# Skill-only Langfuse dataset (same prompts as assistant; separate runs/UI).
DATASET_NAME = "nimble-web-expert-production"
_EVALS_ROOT = Path(__file__).resolve().parents[3]
_BASELINE_PATH = _EVALS_ROOT / "baselines" / "web_expert_baseline.json"
_HEADLINE_METRIC = "first_turn_action"
_REGRESSION_TOLERANCE = 0.03

# Must-act production items: skill must load and Nimble CLI must be used.
SMOKE_ITEM_IDS = ("prod-0475", "prod-0462", "prod-0401")
# Family soft-match (`tool_selection`) is still scored into Langfuse, but the
# smoke hard-gate is skill load + any Nimble CLI tool + FTA/skill scorers.
# Codex often reaches the right answer via extract/agent after discovery.
_SMOKE_SCORE_KEYS = ("first_turn_action", "skill_selection")


def _item_tags(item: DatasetItem) -> list[str]:
    tags = item.metadata.get("tags") or []
    return tags if isinstance(tags, list) else [tags]


def _stratified_sample(items: list[DatasetItem], max_items: int) -> list[DatasetItem]:
    buckets: dict[str, list[DatasetItem]] = defaultdict(list)
    for item in items:
        buckets[solution_key(item)].append(item)
    keys = sorted(buckets)
    picked: list[DatasetItem] = []
    index = 0
    while len(picked) < max_items and keys:
        progress = False
        for key in keys:
            bucket = buckets[key]
            if index < len(bucket):
                picked.append(bucket[index])
                progress = True
                if len(picked) >= max_items:
                    break
        if not progress:
            break
        index += 1
    return picked


def _log_scorable_denominators(items: list[DatasetItem]) -> None:
    facet_counts: Counter[str] = Counter()
    sol_counts: Counter[str] = Counter()
    for item in items:
        sol_counts[solution_key(item)] += 1
        scorable = item.metadata.get("scorable") or item.expected_output.get("scorable")
        if isinstance(scorable, list):
            for facet in scorable:
                facet_counts[str(facet)] += 1
        else:
            facet_counts["first_turn_action"] += 1
    print(f"Solution mix over {len(items)} items: {dict(sorted(sol_counts.items()))}")
    print(
        f"Scorable denominators over {len(items)} items: "
        f"{dict(sorted(facet_counts.items()))}"
    )


def _dataset_hash(items: list[DatasetItem]) -> str:
    blob = json.dumps(
        [{"id": i.id, "prompt": i.prompt[:200]} for i in items],
        sort_keys=True,
    ).encode()
    return hashlib.sha256(blob).hexdigest()[:16]


def check_regression_gate(results_path: Path, baseline_path: Path = _BASELINE_PATH) -> None:
    if not baseline_path.is_file():
        print(f"No baseline at {baseline_path}; skipping regression gate")
        return
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    baseline_rate = baseline.get("first_turn_action_pass_rate")
    if baseline_rate is None:
        print("Baseline has no first_turn_action_pass_rate; skipping regression gate")
        return
    if not results_path.is_file():
        raise SystemExit(f"Results file missing for regression gate: {results_path}")

    results = json.loads(results_path.read_text(encoding="utf-8"))
    values: list[float] = []
    for item in results:
        if item.get("error"):
            continue
        score = (item.get("scores") or {}).get(_HEADLINE_METRIC)
        if score is None:
            continue
        val = score.get("value") if isinstance(score, dict) else score
        if isinstance(val, (bool, int, float)):
            values.append(float(val))
    if not values:
        raise SystemExit("No first_turn_action scores to compare against baseline")

    rate = sum(values) / len(values)
    floor = float(baseline_rate) - _REGRESSION_TOLERANCE
    print(
        f"Regression gate: first_turn_action={rate:.3f} "
        f"baseline={float(baseline_rate):.3f} floor={floor:.3f} (n={len(values)})"
    )
    if rate + 1e-9 < floor:
        raise SystemExit(
            f"first_turn_action regressed: {rate:.3f} < {floor:.3f} "
            f"(baseline {float(baseline_rate):.3f} - {_REGRESSION_TOLERANCE})"
        )


def _fail_fast_skill_visible(settings: EvalSettings, runtime: str) -> None:
    skill_md = settings.skill_path / "SKILL.md"
    if not skill_md.is_file():
        raise SystemExit(f"nimble-web-expert SKILL.md missing at {skill_md}")
    if runtime in {"codex", "both"}:
        link = ensure_codex_skill_link(settings)
        print(f"Codex skill link OK: {link} -> {link.resolve()}")


def _fail_fast_nimble_on_path() -> None:
    if shutil.which("nimble"):
        return
    # Mirror backend PATH enrichment for nvm-installed CLI.
    nvm_bin = Path.home() / ".nvm" / "versions" / "node"
    if nvm_bin.is_dir():
        for node_dir in sorted(nvm_bin.iterdir(), reverse=True):
            if (node_dir / "bin" / "nimble").exists():
                return
    raise SystemExit(
        "nimble CLI not found on PATH (or ~/.nvm/.../bin). "
        "Install with: npm i -g @nimble-way/nimble-cli"
    )


def _score_passed(scores: dict[str, Any], key: str) -> bool | None:
    """Return True/False when scored, None when the facet was not scored."""
    raw = scores.get(key)
    if raw is None:
        return None
    val = raw.get("value") if isinstance(raw, dict) else raw
    if val is None:
        return None
    return bool(val)


def _has_nimble_tool(tools: list[str]) -> bool:
    return any(str(t).strip().startswith("nimble ") for t in tools)


def _skill_loaded(skills: list[str]) -> bool:
    return any("nimble-web-expert" in str(s) for s in skills)


def assert_smoke_results(results_path: Path, *, runtime: str) -> None:
    """Hard-fail unless every smoke item loaded the skill and used Nimble tools."""
    if not results_path.is_file():
        raise SystemExit(f"Smoke results missing: {results_path}")
    results = json.loads(results_path.read_text(encoding="utf-8"))
    by_id = {str(r.get("id")): r for r in results}
    failures: list[str] = []

    for item_id in SMOKE_ITEM_IDS:
        row = by_id.get(item_id)
        if row is None:
            failures.append(f"{item_id}: missing from results")
            continue
        out = row.get("output") if isinstance(row.get("output"), dict) else {}
        skills = list(
            row.get("triggered_skills") or out.get("triggered_skills") or []
        )
        tools = list(row.get("tools_called") or out.get("tools_called") or [])
        err = row.get("error")
        # Soft infra notes after skill+tools still count (crawl wall-clock /
        # Claude is_error after max-turns when tools already ran).
        soft_err = bool(err) and (
            "timed out" in str(err).lower()
            or str(err).startswith("partial:")
        )
        if err and not (soft_err and _skill_loaded(skills) and _has_nimble_tool(tools)):
            failures.append(f"{item_id}: error={err}")
            continue
        prompt = str(row.get("prompt") or out.get("prompt") or "")
        expected_slash = (
            CODEX_SKILL_SLASH if runtime == "codex" else CLAUDE_SKILL_SLASH
        )
        if prompt and not prompt.startswith(expected_slash):
            failures.append(
                f"{item_id}: user prompt missing {expected_slash!r} prefix "
                f"(got {prompt[:80]!r})"
            )
        if not _skill_loaded(skills):
            failures.append(
                f"{item_id}: nimble-web-expert not in triggered_skills={skills}"
            )
        if not _has_nimble_tool(tools):
            failures.append(
                f"{item_id}: no tools_called starting with 'nimble ' "
                f"(got {tools})"
            )
        if runtime == "codex" and any(
            str(t) == "web_search" or str(t).startswith("web_search") for t in tools
        ):
            failures.append(f"{item_id}: forbidden web_search in tools_called={tools}")
        scores = row.get("scores") or {}
        for key in _SMOKE_SCORE_KEYS:
            # Soft-error rows may skip FTA if the run was cut mid-flight after
            # tools already ran — still require skill_selection / tool_selection
            # when those facets scored.
            if soft_err and key == "first_turn_action":
                continue
            passed = _score_passed(scores, key)
            if passed is False:
                comment = ""
                raw = scores.get(key)
                if isinstance(raw, dict) and raw.get("comment"):
                    comment = f" ({raw['comment']})"
                failures.append(f"{item_id}: scorer {key} failed{comment}")

    if failures:
        joined = "\n  - ".join(failures)
        raise SystemExit(f"Smoke hard-assert failed for {runtime}:\n  - {joined}")
    print(
        f"Smoke OK ({runtime}): {len(SMOKE_ITEM_IDS)} items — "
        f"skill loaded + nimble tools used"
    )


def main() -> None:
    load_dotenv(_EVALS_ROOT / ".env", override=False)
    settings = EvalSettings()  # type: ignore[call-arg]

    parser = argparse.ArgumentParser(
        description="Evaluate nimble-web-expert on assistant production prompts"
    )
    parser.add_argument("--dataset-name", type=str, default=DATASET_NAME)
    parser.add_argument(
        "--runtime",
        choices=["claude", "codex", "both"],
        default=None,
        help="CLI runtime (default: claude; smoke default: both)",
    )
    parser.add_argument("--max-items", type=int, default=None)
    parser.add_argument("--tag", type=str, default=None, help="Filter metadata.tags")
    parser.add_argument(
        "--item-id",
        action="append",
        default=None,
        help="Run only these metadata ids (repeatable), e.g. --item-id prod-0462",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        default=False,
        help=(
            f"Run fixed must-act IDs {list(SMOKE_ITEM_IDS)} and hard-fail unless "
            f"skill loads and Nimble CLI tools are used (Claude user prompt "
            f"starts with {CLAUDE_SKILL_SLASH}; Codex with {CODEX_SKILL_SLASH})"
        ),
    )
    parser.add_argument("--no-stratify", action="store_true", default=False)
    parser.add_argument("--timeout-seconds", type=int, default=None)
    parser.add_argument("--max-turns", type=int, default=20)
    parser.add_argument("--max-budget-usd", type=float, default=2.0)
    parser.add_argument("--experiment-name", type=str, default=None)
    parser.add_argument("--check-regression", action="store_true", default=False)
    parser.add_argument(
        "--dry-load",
        action="store_true",
        help="Load/filter dataset and print mix only (no CLI runs)",
    )
    args = parser.parse_args()

    if args.runtime is None:
        args.runtime = "both" if args.smoke else "claude"
    if args.timeout_seconds is None:
        args.timeout_seconds = (
            DEFAULT_SMOKE_TIMEOUT_SECONDS if args.smoke else 300
        )

    items = load_dataset(
        settings,
        dataset_name=args.dataset_name,
    )
    print(f"Loaded {len(items)} items from {args.dataset_name}")

    filtered = items
    if args.smoke:
        wanted = set(SMOKE_ITEM_IDS)
        filtered = [item for item in filtered if item.id in wanted]
        missing = wanted - {item.id for item in filtered}
        if missing:
            raise SystemExit(f"Smoke IDs missing from dataset: {sorted(missing)}")
        # Preserve stable smoke order
        order = {iid: i for i, iid in enumerate(SMOKE_ITEM_IDS)}
        filtered.sort(key=lambda it: order.get(it.id, 999))
        print(f"Smoke mode: {list(SMOKE_ITEM_IDS)} (timeout={args.timeout_seconds}s)")
    if args.tag:
        filtered = [item for item in filtered if args.tag in _item_tags(item)]
    if args.item_id:
        if args.smoke:
            raise SystemExit("--item-id cannot be combined with --smoke")
        wanted = {str(x) for x in args.item_id}
        filtered = [item for item in filtered if item.id in wanted]
        missing = wanted - {item.id for item in filtered}
        if missing:
            raise SystemExit(f"Unknown --item-id values: {sorted(missing)}")
    if args.max_items is not None:
        if args.no_stratify:
            filtered = filtered[: args.max_items]
        else:
            filtered = _stratified_sample(filtered, args.max_items)
    _log_scorable_denominators(filtered)
    print(f"Dataset content hash (filtered): {_dataset_hash(filtered)}")

    if args.dry_load:
        return

    if args.smoke:
        _fail_fast_nimble_on_path()
        # Sequential smokes: crawl items + skill clarify races are flakier under
        # parallel budget pressure.
        settings.max_concurrency = 1

    runtimes = ["claude", "codex"] if args.runtime == "both" else [args.runtime]
    for runtime in runtimes:
        _fail_fast_skill_visible(settings, runtime)

        def make_task(rt: str):
            def task(*, item: Any, **kwargs: Any) -> NormalizedTrace:
                meta = getattr(item, "metadata", None) or {}
                item_id = str(
                    (meta.get("id") if isinstance(meta, dict) else None)
                    or getattr(item, "id", None)
                    or "item"
                )
                prompt = prompt_from_input(getattr(item, "input", {}) or {})
                if isinstance(item, DatasetItem):
                    prompt = item.prompt
                    item_id = item.id or item_id
                if rt == "claude":
                    return run_claude(
                        prompt,
                        settings=settings,
                        item_id=item_id,
                        max_turns=args.max_turns,
                        max_budget_usd=args.max_budget_usd,
                        timeout_seconds=args.timeout_seconds,
                    )
                return run_codex(
                    prompt,
                    settings=settings,
                    item_id=item_id,
                    timeout_seconds=args.timeout_seconds,
                )

            return task

        experiment_name = args.experiment_name or (
            f"nimble-web-expert-smoke-{runtime}"
            if args.smoke
            else f"nimble-web-expert-production-{runtime}"
        )
        results_path = run_experiment(
            settings=settings,
            items=filtered,
            experiment_name=experiment_name,
            runtime=runtime,
            task=make_task(runtime),
            evaluators=WEB_EXPERT_EVALUATORS,
            description=(
                "nimble-web-expert smoke: slash-skill user prompt + "
                "skill load + Nimble CLI tools"
                if args.smoke
                else (
                    "nimble-web-expert on assistant production prompts: "
                    "first_turn_action, skill_selection, tool_selection, "
                    "forbidden_tools, response_non_empty"
                )
            ),
            dataset_name=args.dataset_name,
        )
        if args.smoke:
            assert_smoke_results(results_path, runtime=runtime)
        if args.check_regression:
            check_regression_gate(results_path)


if __name__ == "__main__":
    main()

"""Langfuse experiment runner for skill CLI evals."""

from __future__ import annotations

import json
import sys
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any

from langfuse import Evaluation, Langfuse

from evals.commons.dataset import DatasetItem, prompt_from_input
from evals.commons.langfuse_emit import emit_langfuse_payload
from evals.commons.langfuse_payload import (
    LangfuseTracePayload,
    claude_stream_to_langfuse_payload,
    codex_jsonl_to_langfuse_payload,
    events_to_langfuse_payload,
)
from evals.commons.settings import EvalSettings
from evals.commons.trace import NormalizedTrace

# Langfuse propagates experiment_item_metadata as an OTEL baggage/context
# string and drops values over 200 chars with a warning.
_LANGFUSE_PROPAGATED_MAX_CHARS = 200


def _safe_name(name: str) -> str:
    return name.replace("/", "_").replace(" ", "_")


def _log(msg: str) -> None:
    print(msg, flush=True)


def slim_experiment_item_metadata(
    metadata: dict[str, Any] | None,
    *,
    max_chars: int = _LANGFUSE_PROPAGATED_MAX_CHARS,
) -> dict[str, Any]:
    """Keep only fields that serialize within Langfuse's 200-char propagate limit.

    Full dataset metadata (tags/scorable/source) often exceeds 200 chars when
    JSON-serialized, which Langfuse warns on and drops. Scorers use
    ``expected_output``, so a short ``{id}`` (plus tags when they fit) is enough.
    """
    meta = metadata if isinstance(metadata, dict) else {}
    item_id = str(meta.get("id") or meta.get("item_id") or "")
    candidates: list[dict[str, Any]] = []
    if item_id:
        candidates.append({"id": item_id})
        tags = meta.get("tags")
        if isinstance(tags, list) and tags:
            short_tags = [str(t) for t in tags[:3]]
            candidates.append({"id": item_id, "tags": short_tags})
    else:
        candidates.append({})

    chosen: dict[str, Any] = candidates[0]
    for cand in candidates:
        blob = json.dumps(cand, default=str, separators=(",", ":"))
        if len(blob) <= max_chars:
            chosen = cand
    # Final guard — never return something that still overflows.
    while len(json.dumps(chosen, default=str, separators=(",", ":"))) > max_chars:
        if "tags" in chosen:
            chosen = {k: v for k, v in chosen.items() if k != "tags"}
            continue
        if "id" in chosen and len(str(chosen["id"])) > 32:
            chosen = {"id": str(chosen["id"])[:32]}
            continue
        chosen = {}
        break
    return chosen


def _score_dict(evaluation: Evaluation) -> dict[str, Any]:
    data_type = getattr(evaluation, "data_type", None)
    return {
        "value": evaluation.value,
        "data_type": (
            data_type.value
            if data_type and hasattr(data_type, "value")
            else str(data_type or "BOOLEAN")
        ),
        "comment": getattr(evaluation, "comment", None),
    }


def langfuse_payload_from_trace(trace: NormalizedTrace, *, item_id: str) -> LangfuseTracePayload:
    """Build Langfuse payload from a NormalizedTrace (prefer raw CLI stream)."""
    if trace.raw_path and Path(trace.raw_path).is_file():
        if trace.runtime == "claude":
            return claude_stream_to_langfuse_payload(
                trace.raw_path,
                prompt=trace.prompt,
                model=trace.model,
                item_id=item_id,
                effort=trace.effort,
            )
        if trace.runtime == "codex":
            return codex_jsonl_to_langfuse_payload(
                trace.raw_path,
                prompt=trace.prompt,
                model=trace.model,
                item_id=item_id,
                effort=trace.effort,
            )
    # Fallback when no stream file (infra failure before CLI wrote output).
    return events_to_langfuse_payload(
        [],
        prompt=trace.prompt,
        runtime=trace.runtime if trace.runtime in {"claude", "codex"} else "claude",
        model=trace.model,
        item_id=item_id,
        effort=trace.effort,
    )


def _wrap_task(
    task: Callable[..., NormalizedTrace],
    *,
    runtime: str,
    reporter: Callable[[str, NormalizedTrace | None, float, str | None], None] | None,
) -> Callable[..., Any]:
    """Adapt our task to Langfuse `task(*, item=...)` and emit a real observation tree."""

    def wrapped(*, item: Any, **kwargs: Any) -> dict[str, Any]:
        t0 = time.monotonic()
        meta = item.metadata if isinstance(getattr(item, "metadata", None), dict) else {}
        item_id = str(meta.get("id") or getattr(item, "id", "") or "item")
        try:
            trace = task(item=item, **kwargs)
        except Exception as exc:  # noqa: BLE001
            trace = NormalizedTrace(
                runtime=runtime if runtime in {"claude", "codex"} else "claude",
                model="unknown",
                prompt=prompt_from_input(getattr(item, "input", {})),
                error=str(exc),
            )

        payload = langfuse_payload_from_trace(trace, item_id=item_id)
        # Keep scorer fields on the returned output (NormalizedTrace dump).
        if trace.error and not payload.trace_output.get("error"):
            payload.trace_output["error"] = trace.error
        # Prefer NormalizedTrace product names (nimble search/extract/…) over
        # host tool names (Bash/Skill) for Langfuse summary fields.
        payload.trace_output["triggered_skills"] = list(trace.triggered_skills or [])
        payload.trace_output["tools_called"] = list(
            trace.tools_called
            or payload.trace_output.get("tools_called")
            or []
        )
        payload.trace_output["host_tools"] = [
            o.name
            for o in payload.observations
            if o.as_type == "tool"
        ]
        try:
            emit_langfuse_payload(payload)
        except Exception:  # noqa: BLE001
            pass

        if reporter:
            reporter(item_id, trace, time.monotonic() - t0, trace.error)

        # Return NormalizedTrace for scorers + Langfuse payload for UI/debug.
        out = trace.model_dump(mode="json")
        out["langfuse"] = payload.model_dump(mode="json")
        return out

    return wrapped


def run_experiment(
    *,
    settings: EvalSettings,
    items: list[Any],
    experiment_name: str,
    runtime: str,
    task: Callable[..., NormalizedTrace],
    evaluators: list[Callable[..., Evaluation | None]],
    description: str = "",
    dataset_name: str = "nimble-web-expert-production",
) -> Path:
    """Run task+evaluators; upload to Langfuse when configured, else local JSON."""
    settings.ensure_dirs()
    if settings.langfuse_configured:
        return _run_langfuse(
            settings=settings,
            items=items,
            experiment_name=experiment_name,
            runtime=runtime,
            task=task,
            evaluators=evaluators,
            description=description,
            dataset_name=dataset_name,
        )
    return _run_local(
        settings=settings,
        items=items,
        experiment_name=experiment_name,
        runtime=runtime,
        task=task,
        evaluators=evaluators,
        description=description,
        dataset_name=dataset_name,
    )


def _run_langfuse(
    *,
    settings: EvalSettings,
    items: list[Any],
    experiment_name: str,
    runtime: str,
    task: Callable[..., NormalizedTrace],
    evaluators: list[Callable[..., Evaluation | None]],
    description: str,
    dataset_name: str,
) -> Path:
    git_sha = settings.resolved_git_sha
    branch = settings.resolved_git_branch
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    # ASCII-only, short — Langfuse propagates experiment_name ≤200 chars.
    run_name = f"{branch[:48]}-{git_sha[:8]}-{timestamp}-{runtime}"

    langfuse = Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
    )
    dataset = langfuse.get_dataset(dataset_name)

    # Restrict to the filtered item set (by metadata.id or langfuse id).
    wanted: set[str] = set()
    for item in items:
        meta = getattr(item, "metadata", None) or {}
        if isinstance(meta, dict) and meta.get("id"):
            wanted.add(str(meta["id"]))
        item_id = getattr(item, "id", None)
        if item_id:
            wanted.add(str(item_id))

    active = []
    for item in dataset.items:
        status = getattr(item, "status", None)
        if status is not None and "ACTIVE" not in str(status).upper():
            continue
        meta = item.metadata if isinstance(item.metadata, dict) else {}
        mid = str(meta.get("id") or item.id or "")
        if wanted and mid not in wanted and str(item.id) not in wanted:
            continue
        # Slim before run_experiment so propagated experiment_item_metadata
        # stays ≤200 chars (avoids Langfuse Dropping value warnings).
        item.metadata = slim_experiment_item_metadata(meta)
        active.append(item)

    if not active:
        raise SystemExit(
            f"No Langfuse dataset items matched filter for '{dataset_name}' "
            f"(wanted {len(wanted)} ids)"
        )

    dataset.items = active
    _log(f"Experiment run: {run_name}")
    _log(
        f"Items: {len(active)}  concurrency={settings.max_concurrency}  "
        f"runtime={runtime}  dataset={dataset_name}"
    )

    done = {"n": 0}

    def _progress(
        item_id: str, trace: NormalizedTrace | None, elapsed: float, err: str | None
    ) -> None:
        done["n"] += 1
        hard = bool(err) and not str(err).startswith("partial:")
        status = "ERR" if hard else ("PARTIAL" if err else "OK")
        skills = (trace.triggered_skills if trace else []) or []
        _log(
            f"  [{done['n']}/{len(active)}] {status} {item_id} "
            f"skills={skills} {elapsed:.1f}s"
        )

    experiment_metadata = {
        "system": f"web-expert-{runtime}",
        "runtime": runtime,
        "commit": git_sha[:12],
        "branch": branch[:40],
        "model": (
            settings.eval_claude_model
            if runtime == "claude"
            else settings.eval_codex_model
        )[:40],
    }
    meta_blob = json.dumps(experiment_metadata, separators=(",", ":"))
    if len(meta_blob) > _LANGFUSE_PROPAGATED_MAX_CHARS:
        experiment_metadata = {
            "runtime": runtime,
            "commit": git_sha[:8],
            "model": experiment_metadata["model"][:24],
        }

    result = dataset.run_experiment(
        name=experiment_name,
        run_name=run_name,
        description=(description or "")[:200],
        task=_wrap_task(task, runtime=runtime, reporter=_progress),
        evaluators=list(evaluators),
        max_concurrency=max(1, settings.max_concurrency),
        metadata=experiment_metadata,
    )

    langfuse_url = result.dataset_run_url or ""
    _log(f"\nExperiment run: {run_name}")
    _log(f"Langfuse URL:   {langfuse_url}\n")

    results_data: list[dict[str, Any]] = []
    for item_result in result.item_results:
        item_obj = getattr(item_result, "item", None)
        input_val = getattr(item_obj, "input", None)
        metadata_val = getattr(item_obj, "metadata", None)
        input_preview = None
        if isinstance(input_val, dict):
            raw = input_val.get("prompt") or ""
            input_preview = str(raw)[:120] if raw else None
        output = item_result.output
        error = None
        if isinstance(output, dict):
            error = output.get("error")
        evaluations = list(getattr(item_result, "evaluations", None) or [])
        out_dict = output if isinstance(output, dict) else {}
        results_data.append(
            {
                "id": (metadata_val or {}).get("id")
                if isinstance(metadata_val, dict)
                else getattr(item_obj, "id", None),
                "input_preview": input_preview,
                "metadata": metadata_val if isinstance(metadata_val, dict) else None,
                "error": error,
                "scores": {
                    ev.name: _score_dict(ev) for ev in evaluations if ev is not None
                },
                # Flatten scorer-facing fields for smoke/local gates (also under output).
                "triggered_skills": list(out_dict.get("triggered_skills") or []),
                "tools_called": list(out_dict.get("tools_called") or []),
                "output_preview": str(
                    out_dict.get("final_response") or out_dict.get("response") or ""
                )[:300],
                "prompt": out_dict.get("prompt"),
                "output": out_dict or None,
            }
        )

    safe = _safe_name(experiment_name)
    results_path = settings.results_dir / f"{safe}_results.json"
    meta_path = settings.results_dir / f"{safe}_meta.json"
    run_name_path = settings.results_dir / f"{safe}_run_name.txt"

    results_path.write_text(json.dumps(results_data, indent=2, default=str), encoding="utf-8")
    meta = {
        "experiment_name": experiment_name,
        "description": description,
        "run_name": run_name,
        "runtime": runtime,
        "langfuse_url": langfuse_url,
        "langfuse_dataset": dataset_name,
        "langfuse_host": settings.langfuse_host,
        "item_count": len(results_data),
        "git_sha": git_sha,
        "branch": branch,
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    run_name_path.write_text(run_name + "\n", encoding="utf-8")

    _print_summary(results_data)
    _log(f"Wrote {results_path}")
    if langfuse_url:
        _log(f"Open in Langfuse: {langfuse_url}")
    langfuse.flush()
    return results_path


def _run_local(
    *,
    settings: EvalSettings,
    items: list[Any],
    experiment_name: str,
    runtime: str,
    task: Callable[..., NormalizedTrace],
    evaluators: list[Callable[..., Evaluation | None]],
    description: str,
    dataset_name: str,
) -> Path:
    git_sha = settings.resolved_git_sha
    branch = settings.resolved_git_branch
    timestamp = datetime.now().strftime("%b %d %Y %H:%M")
    run_name = f"{branch} · {git_sha[:8]} · {timestamp} · {runtime}"

    results: list[dict[str, Any]] = []
    _log(f"Experiment run: {run_name} (local — Langfuse not configured)")
    _log(f"Items: {len(items)}  concurrency={settings.max_concurrency}  runtime={runtime}")

    def _one(item: Any) -> dict[str, Any]:
        t0 = time.monotonic()
        if isinstance(item, DatasetItem):
            prompt = item.prompt
            item_id = item.id
            expected = item.expected_output
            meta = item.metadata
            inp = item.input
        else:
            inp = getattr(item, "input", {}) or {}
            prompt = prompt_from_input(inp)
            meta = getattr(item, "metadata", {}) or {}
            item_id = str(meta.get("id") or getattr(item, "id", "") or "")
            expected = getattr(item, "expected_output", {}) or {}

        try:
            if isinstance(item, DatasetItem):
                # Local adapter expects DatasetItem via closure in suite — call with item=
                trace = task(item=item)
            else:
                trace = task(item=item)
        except TypeError:
            # Back-compat: task(DatasetItem)
            trace = task(item)  # type: ignore[misc]
        except Exception as exc:  # noqa: BLE001
            trace = NormalizedTrace(
                runtime=runtime if runtime in {"claude", "codex"} else "claude",
                model="unknown",
                prompt=prompt,
                error=str(exc),
            )

        scores: dict[str, Any] = {}
        for ev in evaluators:
            score = ev(
                input=inp,
                output=trace,
                expected_output=expected,
                metadata=meta,
            )
            if score is None:
                continue
            scores[score.name] = _score_dict(score)
        elapsed = time.monotonic() - t0
        return {
            "id": item_id,
            "input_preview": prompt[:160].replace("\n", " "),
            "metadata": {
                **(meta if isinstance(meta, dict) else {}),
                "runtime": runtime,
                "model": trace.model,
                "effort": trace.effort,
                "elapsed_s": round(elapsed, 2),
            },
            "error": trace.error,
            "scores": scores,
            "output_preview": (trace.final_response or "")[:300],
            "triggered_skills": trace.triggered_skills,
            "tools_called": trace.tools_called,
            "cost_usd": trace.cost_usd,
        }

    with ThreadPoolExecutor(max_workers=max(1, settings.max_concurrency)) as pool:
        futures = {pool.submit(_one, item): i for i, item in enumerate(items)}
        done = 0
        for fut in as_completed(futures):
            row = fut.result()
            results.append(row)
            done += 1
            status = "ERR" if row.get("error") else "OK"
            fta = (row.get("scores") or {}).get("first_turn_action", {}).get("value")
            _log(
                f"  [{done}/{len(items)}] {status} {row['id']} first_turn_action={fta}"
            )

    results.sort(key=lambda r: str(r.get("id")))
    safe = _safe_name(experiment_name)
    results_path = settings.results_dir / f"{safe}_results.json"
    meta_path = settings.results_dir / f"{safe}_meta.json"
    run_name_path = settings.results_dir / f"{safe}_run_name.txt"

    results_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    meta_path.write_text(
        json.dumps(
            {
                "experiment_name": experiment_name,
                "description": description,
                "run_name": run_name,
                "runtime": runtime,
                "item_count": len(items),
                "git_sha": git_sha,
                "branch": branch,
                "langfuse_dataset": dataset_name,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    run_name_path.write_text(run_name + "\n", encoding="utf-8")
    _print_summary(results)
    _log(f"Wrote {results_path}")
    return results_path


def _print_summary(results: list[dict[str, Any]]) -> None:
    metrics = [
        "first_turn_action",
        "skill_selection",
        "tool_selection",
        "forbidden_tools",
        "response_non_empty",
    ]
    _log("\nScore summary:")
    for metric in metrics:
        values = []
        for row in results:
            score = (row.get("scores") or {}).get(metric)
            if not score:
                continue
            val = score.get("value")
            if isinstance(val, bool):
                values.append(1.0 if val else 0.0)
            elif isinstance(val, (int, float)):
                values.append(float(val))
        if not values:
            _log(f"  {metric}: n/a")
            continue
        rate = sum(values) / len(values)
        _log(f"  {metric}: {rate:.3f} pass ({sum(values):.0f}/{len(values)})")


try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(line_buffering=True)  # type: ignore[attr-defined]
except Exception:  # noqa: BLE001
    pass

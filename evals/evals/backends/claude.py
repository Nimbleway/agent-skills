"""Claude Code CLI backend."""

from __future__ import annotations

import json
import os
import subprocess
import uuid
from pathlib import Path

from evals.commons.eval_prompt import wrap_user_prompt_with_skill
from evals.commons.normalize import parse_claude_stream
from evals.commons.settings import EvalSettings
from evals.commons.trace import NormalizedTrace

# Built-in web tools compete with nimble-web-expert; block them in evals.
_DISALLOWED_WEB_TOOLS = "WebSearch,WebFetch"

_PLUGIN_MANIFEST = {
    "name": "nimble-web-expert-eval",
    "version": "0.0.1",
    "description": "Eval-only plugin exposing solely nimble-web-expert",
    "skills": ["./skills/"],
}


def _ensure_dir_symlink(link: Path, target: Path) -> None:
    """Point ``link`` at ``target``; replace stale symlinks/files safely."""
    target = target.resolve()
    if link.is_symlink():
        if link.resolve() == target:
            return
        link.unlink()
    elif link.is_dir():
        if any(link.iterdir()):
            raise RuntimeError(
                f"{link} is a non-empty directory; move it aside so the harness "
                f"can symlink to {target}"
            )
        link.rmdir()
    elif link.exists():
        link.unlink()
    link.symlink_to(target, target_is_directory=True)


def ensure_claude_eval_plugin(settings: EvalSettings) -> Path:
    """Thin plugin dir with only nimble-web-expert (avoids company-deep-dive etc.)."""
    plugin_root = settings.traces_dir / "claude-plugin-web-expert-only"
    skills_dir = plugin_root / "skills"
    skill_link = skills_dir / "nimble-web-expert"
    manifest = plugin_root / ".claude-plugin" / "plugin.json"

    plugin_root.mkdir(parents=True, exist_ok=True)
    skills_dir.mkdir(parents=True, exist_ok=True)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(_PLUGIN_MANIFEST, indent=2) + "\n", encoding="utf-8")

    target = settings.skill_path.resolve()
    if not target.is_dir():
        raise FileNotFoundError(f"nimble-web-expert missing at {target}")
    _ensure_dir_symlink(skill_link, target)
    return plugin_root


def build_claude_command(
    prompt: str,
    *,
    settings: EvalSettings,
    max_turns: int,
    max_budget_usd: float,
    plugin_dir: Path | None = None,
) -> list[str]:
    """Build the Claude CLI argv (exposed for unit tests)."""
    plugin = plugin_dir or settings.agent_skills_root
    # Slash-skill user prompt — skill load comes from the plugin-namespaced
    # /nimble-web-expert-eval:nimble-web-expert, not --append-system-prompt.
    user_prompt = wrap_user_prompt_with_skill(prompt, runtime="claude")
    return [
        "claude",
        "--bare",
        "--output-format",
        "stream-json",
        "--verbose",
        "--include-partial-messages",
        "--plugin-dir",
        str(plugin),
        "--dangerously-skip-permissions",
        "--disallowed-tools",
        _DISALLOWED_WEB_TOOLS,
        "--max-turns",
        str(max_turns),
        "--max-budget-usd",
        str(max_budget_usd),
        "--model",
        settings.eval_claude_model,
        "--effort",
        settings.eval_claude_effort,
        "-p",
        "--",
        user_prompt,
    ]


def run_claude(
    prompt: str,
    *,
    settings: EvalSettings,
    item_id: str,
    max_turns: int = 20,
    max_budget_usd: float = 2.0,
    timeout_seconds: int = 300,
) -> NormalizedTrace:
    settings.ensure_dirs()
    run_id = f"{item_id}-{uuid.uuid4().hex[:8]}"
    out_path = settings.traces_dir / f"claude-{run_id}.jsonl"
    model = settings.eval_claude_model
    effort = settings.eval_claude_effort

    plugin_dir = ensure_claude_eval_plugin(settings)
    user_prompt = wrap_user_prompt_with_skill(prompt)

    # All flags before -p. Prompts that start with "--…" must not be parsed as
    # Claude CLI options (seen with production Search items).
    # build_claude_command re-wraps idempotently (slash prefix already present).
    cmd = build_claude_command(
        prompt,
        settings=settings,
        max_turns=max_turns,
        max_budget_usd=max_budget_usd,
        plugin_dir=plugin_dir,
    )

    from evals.commons.langfuse_otel import merge_cli_env

    env = merge_cli_env(
        {k: v for k, v in os.environ.items() if k != "CLAUDECODE"},
        settings=settings,
        runtime="claude",
    )
    # Ensure nimble CLI is reachable even if the parent shell lacked nvm PATH.
    path = env.get("PATH", "")
    nvm_bin = Path.home() / ".nvm" / "versions" / "node"
    if nvm_bin.is_dir():
        # Prefer newest node bin that contains nimble
        for node_dir in sorted(nvm_bin.iterdir(), reverse=True):
            candidate = node_dir / "bin"
            if (candidate / "nimble").exists():
                path = f"{candidate}:{path}"
                break
    env["PATH"] = path

    try:
        with out_path.open("w", encoding="utf-8") as fh:
            proc = subprocess.run(
                cmd,
                stdout=fh,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout_seconds,
                cwd=str(settings.agent_skills_root),
                env=env,
            )
    except FileNotFoundError:
        return NormalizedTrace(
            runtime="claude",
            model=model,
            effort=effort,
            prompt=user_prompt,
            error="claude CLI not found on PATH",
        )
    except subprocess.TimeoutExpired:
        if out_path.exists() and out_path.stat().st_size > 0:
            trace = parse_claude_stream(
                out_path, prompt=user_prompt, model=model, effort=effort
            )
            if not trace.error:
                trace.error = f"claude timed out after {timeout_seconds}s"
            return trace
        return NormalizedTrace(
            runtime="claude",
            model=model,
            effort=effort,
            prompt=user_prompt,
            error=f"claude timed out after {timeout_seconds}s",
            raw_path=out_path if out_path.exists() else None,
        )

    if not out_path.exists() or out_path.stat().st_size == 0:
        err = (proc.stderr or "").strip()
        return NormalizedTrace(
            runtime="claude",
            model=model,
            effort=effort,
            prompt=user_prompt,
            error=err or f"claude exited {proc.returncode} with empty output",
            raw_path=out_path if out_path.exists() else None,
        )

    trace = parse_claude_stream(
        out_path, prompt=user_prompt, model=model, effort=effort
    )
    if proc.returncode != 0 and not trace.error:
        trace.error = (proc.stderr or "").strip() or f"claude exited {proc.returncode}"
    return trace

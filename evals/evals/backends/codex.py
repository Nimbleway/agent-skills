"""Codex CLI backend."""

from __future__ import annotations

import os
import subprocess
import uuid
from pathlib import Path

from evals.commons.eval_prompt import wrap_user_prompt_with_skill
from evals.commons.normalize import parse_codex_jsonl
from evals.commons.settings import EvalSettings
from evals.commons.trace import NormalizedTrace

SKILL_LINK = Path.home() / ".agents" / "skills" / "nimble-web-expert"
# Crawl / multi-tool smokes routinely exceed the default 300s wall clock.
DEFAULT_SMOKE_TIMEOUT_SECONDS = 600


def ensure_codex_skill_link(settings: EvalSettings) -> Path:
    """Ensure Codex can load nimble-web-expert from ~/.agents/skills/.

    Codex discovers skills under ``~/.agents/skills`` (host convention). We only
    create/replace a symlink to the repo skill — no skill content is written
    outside ``~/.nimble`` workdirs/traces.
    """
    target = settings.skill_path.resolve()
    if not (target / "SKILL.md").is_file():
        raise FileNotFoundError(f"Skill missing at {target}")
    SKILL_LINK.parent.mkdir(parents=True, exist_ok=True)

    if SKILL_LINK.is_symlink():
        if SKILL_LINK.resolve() != target:
            SKILL_LINK.unlink()
            SKILL_LINK.symlink_to(target, target_is_directory=True)
        return SKILL_LINK

    if SKILL_LINK.is_dir():
        if (SKILL_LINK / "SKILL.md").is_file():
            # Pre-existing install — leave alone.
            return SKILL_LINK
        if any(SKILL_LINK.iterdir()):
            raise RuntimeError(
                f"{SKILL_LINK} is a non-empty directory without SKILL.md; "
                f"move it aside so the harness can symlink to {target}"
            )
        SKILL_LINK.rmdir()
    elif SKILL_LINK.exists():
        SKILL_LINK.unlink()

    SKILL_LINK.symlink_to(target, target_is_directory=True)
    return SKILL_LINK


def _ensure_skill_symlink(dest: Path, target: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_symlink() or dest.exists():
        if dest.is_symlink() and dest.resolve() == target:
            return dest
        if dest.is_symlink():
            dest.unlink()
        elif dest.is_dir():
            if any(dest.iterdir()):
                return dest
            dest.rmdir()
        else:
            dest.unlink()
    dest.symlink_to(target, target_is_directory=True)
    return dest


def ensure_workdir_skill(workdir: Path, settings: EvalSettings) -> Path:
    """Install repo-scoped skill under workdir/.agents/skills/ for discovery.

    Codex scans ``$CWD/.agents/skills`` up to the repo root. Eval workdirs are
    ephemeral and otherwise empty, so without this the skill is easy to miss
    (especially with ``--ignore-user-config``).
    """
    return _ensure_skill_symlink(
        workdir / ".agents" / "skills" / "nimble-web-expert",
        settings.skill_path.resolve(),
    )


def ensure_isolated_codex_home(home: Path, settings: EvalSettings) -> Path:
    """Sandbox ``HOME`` so Codex cannot load sibling skills or memory wiki.

    Host ``~/.agents/skills`` often contains ``company-deep-dive`` etc., which
    steers Codex away from live Nimble tools. Auth stays on the real
    ``CODEX_HOME`` (``~/.codex``); only skill discovery is isolated.
    """
    target = settings.skill_path.resolve()
    if not (target / "SKILL.md").is_file():
        raise FileNotFoundError(f"Skill missing at {target}")
    home.mkdir(parents=True, exist_ok=True)
    _ensure_skill_symlink(home / ".agents" / "skills" / "nimble-web-expert", target)
    # Empty memory tree — blocks reading host ~/.nimble/memory reports.
    (home / ".nimble" / "memory").mkdir(parents=True, exist_ok=True)
    return home


def build_codex_command(
    prompt: str,
    *,
    settings: EvalSettings,
    last_path: Path,
    workdir: Path,
) -> list[str]:
    """Build the Codex CLI argv (exposed for unit tests).

    ``prompt`` may be raw production text or already slash-wrapped; wrapping is
    applied here so unit tests and ``run_codex`` share one path.
    """
    user_prompt = wrap_user_prompt_with_skill(prompt, runtime="codex")
    return [
        "codex",
        "exec",
        "--json",
        "-o",
        str(last_path),
        "-C",
        str(workdir),
        "--ignore-user-config",
        "-m",
        settings.eval_codex_model,
        "-c",
        f'model_reasoning_effort="{settings.eval_codex_reasoning_effort}"',
        "--dangerously-bypass-approvals-and-sandbox",
        "--skip-git-repo-check",
        "--ephemeral",
        "--",
        user_prompt,
    ]


def run_codex(
    prompt: str,
    *,
    settings: EvalSettings,
    item_id: str,
    timeout_seconds: int = 300,
) -> NormalizedTrace:
    settings.ensure_dirs()
    ensure_codex_skill_link(settings)

    run_id = f"{item_id}-{uuid.uuid4().hex[:8]}"
    out_path = settings.traces_dir / f"codex-{run_id}.jsonl"
    last_path = settings.traces_dir / f"codex-{run_id}-last.txt"
    model = settings.eval_codex_model
    effort = settings.eval_codex_reasoning_effort
    workdir = settings.traces_dir / f"codex-cwd-{run_id}"
    workdir.mkdir(parents=True, exist_ok=True)
    ensure_workdir_skill(workdir, settings)
    real_home = Path.home()
    isolated_home = ensure_isolated_codex_home(
        settings.traces_dir / f"codex-home-{run_id}",
        settings,
    )

    user_prompt = wrap_user_prompt_with_skill(prompt, runtime="codex")
    cmd = build_codex_command(
        prompt,
        settings=settings,
        last_path=last_path,
        workdir=workdir,
    )

    from evals.commons.langfuse_otel import merge_cli_env

    env = merge_cli_env(dict(os.environ), settings=settings, runtime="codex")
    path = env.get("PATH", "")
    nvm_bin = real_home / ".nvm" / "versions" / "node"
    if nvm_bin.is_dir():
        for node_dir in sorted(nvm_bin.iterdir(), reverse=True):
            candidate = node_dir / "bin"
            if (candidate / "nimble").exists():
                path = f"{candidate}:{path}"
                break
    env["PATH"] = path
    # Isolate skill + memory discovery; keep real Codex auth directory.
    env["HOME"] = str(isolated_home)
    env["CODEX_HOME"] = str(real_home / ".codex")

    try:
        with out_path.open("w", encoding="utf-8") as fh:
            proc = subprocess.run(
                cmd,
                stdout=fh,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout_seconds,
                cwd=str(workdir),
                env=env,
            )
    except FileNotFoundError:
        return NormalizedTrace(
            runtime="codex",
            model=model,
            effort=effort,
            prompt=user_prompt,
            error="codex CLI not found on PATH",
        )
    except subprocess.TimeoutExpired:
        if out_path.exists() and out_path.stat().st_size > 0:
            trace = parse_codex_jsonl(
                out_path,
                last_path if last_path.exists() else None,
                prompt=user_prompt,
                model=model,
                effort=effort,
            )
            if not trace.error:
                trace.error = f"codex timed out after {timeout_seconds}s"
            return trace
        return NormalizedTrace(
            runtime="codex",
            model=model,
            effort=effort,
            prompt=user_prompt,
            error=f"codex timed out after {timeout_seconds}s",
            raw_path=out_path if out_path.exists() else None,
        )

    if not out_path.exists() or out_path.stat().st_size == 0:
        err = (proc.stderr or "").strip()
        return NormalizedTrace(
            runtime="codex",
            model=model,
            effort=effort,
            prompt=user_prompt,
            error=err or f"codex exited {proc.returncode} with empty output",
            raw_path=out_path if out_path.exists() else None,
        )

    trace = parse_codex_jsonl(
        out_path,
        last_path if last_path.exists() else None,
        prompt=user_prompt,
        model=model,
        effort=effort,
    )
    if proc.returncode != 0 and not trace.error:
        trace.error = (proc.stderr or "").strip() or f"codex exited {proc.returncode}"
    return trace

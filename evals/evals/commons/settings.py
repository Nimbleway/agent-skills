"""Settings for skill CLI evals."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_EVALS_ROOT = Path(__file__).resolve().parents[2]
_REPO_ROOT = _EVALS_ROOT.parent
# Persist under ~/.nimble (never the repo tree). Overridable via env.
_NIMBLE_EVALS_HOME = Path.home() / ".nimble" / "skills-evals"
_MAX_CONCURRENCY = 4


def _git(cmd: list[str]) -> str:
    try:
        out = subprocess.check_output(
            ["git", *cmd],
            cwd=_REPO_ROOT,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip()
    except Exception:
        return "unknown"


class EvalSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(_EVALS_ROOT / ".env",),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    langfuse_public_key: str | None = Field(default=None, alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str | None = Field(default=None, alias="LANGFUSE_SECRET_KEY")
    langfuse_host: str = Field(
        default="https://us.cloud.langfuse.com", alias="LANGFUSE_HOST"
    )

    agent_skills_root: Path = Field(default=_REPO_ROOT, alias="AGENT_SKILLS_ROOT")

    max_concurrency: int = Field(default=_MAX_CONCURRENCY, alias="MAX_CONCURRENCY")
    eval_claude_model: str = Field(default="claude-sonnet-5", alias="EVAL_CLAUDE_MODEL")
    eval_claude_effort: str = Field(default="medium", alias="EVAL_CLAUDE_EFFORT")
    eval_codex_model: str = Field(default="gpt-5.6-sol", alias="EVAL_CODEX_MODEL")
    eval_codex_reasoning_effort: str = Field(
        default="medium", alias="EVAL_CODEX_REASONING_EFFORT"
    )

    results_dir: Path = Field(
        default_factory=lambda: _NIMBLE_EVALS_HOME / "results",
        alias="EVAL_RESULTS_DIR",
    )
    traces_dir: Path = Field(
        default_factory=lambda: _NIMBLE_EVALS_HOME / "traces",
        alias="EVAL_TRACES_DIR",
    )

    @field_validator("max_concurrency", mode="after")
    @classmethod
    def _cap_concurrency(cls, value: int) -> int:
        return max(1, min(int(value), _MAX_CONCURRENCY))

    @property
    def resolved_git_sha(self) -> str:
        return os.getenv("GITHUB_SHA") or _git(["rev-parse", "HEAD"])

    @property
    def resolved_git_branch(self) -> str:
        return os.getenv("GITHUB_REF_NAME") or _git(["rev-parse", "--abbrev-ref", "HEAD"])

    @property
    def langfuse_configured(self) -> bool:
        return bool(self.langfuse_public_key and self.langfuse_secret_key)

    @property
    def skill_path(self) -> Path:
        return self.agent_skills_root / "skills" / "nimble-web-expert"

    def ensure_dirs(self) -> None:
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.traces_dir.mkdir(parents=True, exist_ok=True)

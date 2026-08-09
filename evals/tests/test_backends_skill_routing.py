"""Ensure Claude/Codex harness invokes nimble-web-expert via slash user prompts."""

from __future__ import annotations

from pathlib import Path

from evals.backends.claude import (
    _DISALLOWED_WEB_TOOLS,
    build_claude_command,
    ensure_claude_eval_plugin,
)
from evals.backends.codex import (
    build_codex_command,
    ensure_isolated_codex_home,
    ensure_workdir_skill,
)
from evals.commons.eval_prompt import (
    CLAUDE_SKILL_SLASH,
    CODEX_SKILL_SLASH,
    SKILL_STEERING,
    wrap_user_prompt,
    wrap_user_prompt_with_skill,
)
from evals.commons.settings import EvalSettings
from evals.suites.web_expert.__main__ import (
    SMOKE_ITEM_IDS,
    assert_smoke_results,
)


def test_wrap_user_prompt_with_skill_prefixes_slash() -> None:
    wrapped = wrap_user_prompt_with_skill("Who is Acme Corp?", runtime="claude")
    # Claude needs same-line args for slash expansion under --bare.
    assert wrapped.startswith(f"{CLAUDE_SKILL_SLASH} ")
    assert "Who is Acme Corp?" in wrapped
    assert "\n" not in wrapped
    # Idempotent
    assert wrap_user_prompt_with_skill(wrapped, runtime="claude") == wrapped
    codex = wrap_user_prompt("find acme", runtime="codex")
    assert codex.startswith(f"{CODEX_SKILL_SLASH}\n\n")
    assert "find acme" in codex
    assert "nimble-web-expert/SKILL.md" in codex
    assert "web_search" in codex


def test_claude_disallows_builtin_web_and_slash_skill(tmp_path: Path) -> None:
    skill = tmp_path / "skills" / "nimble-web-expert"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("# skill\n", encoding="utf-8")
    settings = EvalSettings(
        AGENT_SKILLS_ROOT=str(tmp_path),
        EVAL_CLAUDE_MODEL="claude-sonnet-5",
        EVAL_CLAUDE_EFFORT="medium",
    )
    settings.traces_dir = tmp_path / "traces"
    settings.traces_dir.mkdir()
    plugin = ensure_claude_eval_plugin(settings)
    cmd = build_claude_command(
        "search the web for acme",
        settings=settings,
        max_turns=8,
        max_budget_usd=1.0,
        plugin_dir=plugin,
    )
    assert "--bare" in cmd
    assert "--disallowed-tools" in cmd
    assert _DISALLOWED_WEB_TOOLS in cmd
    assert "WebSearch" in _DISALLOWED_WEB_TOOLS
    assert "WebFetch" in _DISALLOWED_WEB_TOOLS
    assert "--append-system-prompt" not in cmd
    assert cmd[-1].startswith(f"{CLAUDE_SKILL_SLASH} ")
    assert "search the web for acme" in cmd[-1]
    assert "--plugin-dir" in cmd
    assert str(plugin) in cmd
    assert (plugin / "skills" / "nimble-web-expert").resolve() == skill.resolve()


def test_codex_workdir_gets_repo_skill_symlink(tmp_path: Path) -> None:
    skill = tmp_path / "skills" / "nimble-web-expert"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("# skill\n", encoding="utf-8")
    settings = EvalSettings(AGENT_SKILLS_ROOT=str(tmp_path))
    workdir = tmp_path / "cwd"
    workdir.mkdir()
    link = ensure_workdir_skill(workdir, settings)
    assert link.is_symlink()
    assert link.resolve() == skill.resolve()
    assert (link / "SKILL.md").is_file()


def test_codex_isolated_home_only_exposes_web_expert(tmp_path: Path) -> None:
    skill = tmp_path / "skills" / "nimble-web-expert"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("# skill\n", encoding="utf-8")
    settings = EvalSettings(AGENT_SKILLS_ROOT=str(tmp_path))
    home = ensure_isolated_codex_home(tmp_path / "home", settings)
    skills = home / ".agents" / "skills"
    assert (skills / "nimble-web-expert").resolve() == skill.resolve()
    assert list(skills.iterdir()) == [skills / "nimble-web-expert"]
    assert (home / ".nimble" / "memory").is_dir()


def test_codex_command_uses_slash_skill_prompt_and_workdir(tmp_path: Path) -> None:
    settings = EvalSettings(
        AGENT_SKILLS_ROOT=str(tmp_path),
        EVAL_CODEX_MODEL="gpt-5.6-sol",
        EVAL_CODEX_REASONING_EFFORT="medium",
    )
    workdir = tmp_path / "cwd"
    workdir.mkdir()
    last = tmp_path / "last.txt"
    cmd = build_codex_command(
        "find acme",
        settings=settings,
        last_path=last,
        workdir=workdir,
    )
    assert cmd[-1].startswith(f"{CODEX_SKILL_SLASH}\n\n")
    assert "find acme" in cmd[-1]
    # Must not dump the old long system-steering block as the user message.
    assert "Mandatory rules for ANY live web access" not in cmd[-1]
    assert str(workdir) in cmd
    assert "--ignore-user-config" in cmd


def test_skill_steering_doc_still_mentions_nimble_cli() -> None:
    # Reference string only — not injected into CLI argv anymore.
    assert "nimble search" in SKILL_STEERING
    assert "WebSearch" in SKILL_STEERING


def test_max_concurrency_capped_at_four() -> None:
    settings = EvalSettings(MAX_CONCURRENCY="99")
    assert settings.max_concurrency == 4
    settings_low = EvalSettings(MAX_CONCURRENCY="0")
    assert settings_low.max_concurrency == 1


def test_claude_plugin_refuses_nonempty_directory(tmp_path: Path) -> None:
    skill = tmp_path / "skills" / "nimble-web-expert"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("# skill\n", encoding="utf-8")
    settings = EvalSettings(AGENT_SKILLS_ROOT=str(tmp_path))
    settings.traces_dir = tmp_path / "traces"
    settings.traces_dir.mkdir()
    # Pre-create a non-empty directory where the symlink should go
    bad = settings.traces_dir / "claude-plugin-web-expert-only" / "skills" / "nimble-web-expert"
    bad.mkdir(parents=True)
    (bad / "stale.txt").write_text("x", encoding="utf-8")
    try:
        ensure_claude_eval_plugin(settings)
        raise AssertionError("expected RuntimeError")
    except RuntimeError as exc:
        assert "non-empty directory" in str(exc)


def test_assert_smoke_results_requires_skill_and_nimble(tmp_path: Path) -> None:
    path = tmp_path / "results.json"
    rows = [
        {
            "id": iid,
            "error": None,
            "triggered_skills": ["nimble:nimble-web-expert"],
            "tools_called": ["nimble search --query acme"],
            "scores": {
                "first_turn_action": {"value": True},
                "skill_selection": {"value": True},
                "tool_selection": {"value": True},
            },
        }
        for iid in SMOKE_ITEM_IDS
    ]
    path.write_text(__import__("json").dumps(rows), encoding="utf-8")
    assert_smoke_results(path, runtime="claude")


def test_assert_smoke_results_fails_on_web_search(tmp_path: Path) -> None:
    path = tmp_path / "results.json"
    rows = [
        {
            "id": iid,
            "error": None,
            "triggered_skills": ["nimble-web-expert"],
            "tools_called": ["web_search", "nimble search x"],
            "scores": {
                "first_turn_action": {"value": True},
                "skill_selection": {"value": True},
                "tool_selection": {"value": True},
            },
        }
        for iid in SMOKE_ITEM_IDS
    ]
    path.write_text(__import__("json").dumps(rows), encoding="utf-8")
    try:
        assert_smoke_results(path, runtime="codex")
        raise AssertionError("expected SystemExit")
    except SystemExit as exc:
        assert "web_search" in str(exc)

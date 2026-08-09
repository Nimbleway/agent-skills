"""User-prompt shaping for nimble-web-expert CLI evals."""

from __future__ import annotations

from typing import Literal

# Claude --plugin-dir registers skills as ``{plugin}:{skill}``. Our eval-only
# plugin is named ``nimble-web-expert-eval`` (see backends/claude.py).
# Claude ``-p`` expands slash skills when args are on the SAME line
# (``/plugin:skill …request…``). A blank line after the slash leaves
# ``User request:`` empty and skips skill expansion.
CLAUDE_SKILL_SLASH = "/nimble-web-expert-eval:nimble-web-expert"
# Codex discovers the skill by folder name under ``.agents/skills/``.
CODEX_SKILL_SLASH = "/nimble-web-expert"

# Back-compat alias used in docs / smoke help text.
SKILL_SLASH = CLAUDE_SKILL_SLASH

# Retained for reference / optional future use. Live evals invoke the skill via
# a slash command on the *user* prompt (see wrap_user_prompt_with_skill), not
# via a parallel system-steering channel.
SKILL_STEERING = """\
You are evaluating the nimble-web-expert skill for live web data.

Mandatory rules for ANY live web access (search, fetch URL, scrape, research):
1. Invoke ONLY the skill `nimble:nimble-web-expert` (Claude Skill tool) or load and
   follow `nimble-web-expert/SKILL.md` (Codex) BEFORE answering from the live web.
   Do NOT invoke other business skills (company-deep-dive, competitor-intel, etc.).
2. Use the Nimble CLI only (`nimble search`, `nimble extract`, `nimble map`,
   `nimble crawl`, `nimble agent` / `nimble agents`). Prefer Bash/`exec_command`.
3. Do NOT use built-in web search / web fetch tools (WebSearch, WebFetch,
   ToolSearch→WebSearch, Codex `web_search`). Those are out of scope for this eval.
4. If Nimble CLI is missing or unauthenticated, report that clearly — do not fall
   back to built-in web tools.
"""

RuntimeName = Literal["claude", "codex"]


def skill_slash_for(runtime: RuntimeName = "claude") -> str:
    return CODEX_SKILL_SLASH if runtime == "codex" else CLAUDE_SKILL_SLASH


def prompt_invokes_web_expert(prompt: str) -> bool:
    """True when the user turn starts with a known nimble-web-expert slash form."""
    body = (prompt or "").lstrip()
    for slash in (CLAUDE_SKILL_SLASH, CODEX_SKILL_SLASH):
        if body == slash or body.startswith(f"{slash} ") or body.startswith(f"{slash}\n"):
            return True
    return False


def wrap_user_prompt_with_skill(
    prompt: str,
    *,
    runtime: RuntimeName = "claude",
) -> str:
    """Prefix a production prompt with a slash-skill invoke (real user shape).

    Claude ``--bare`` resolves skills via ``/plugin:skill-name <args>`` on one
    line. Codex gets the same slash+request shape for user-facing parity.
    """
    slash = skill_slash_for(runtime)
    body = (prompt or "").strip()
    if prompt_invokes_web_expert(body):
        return body
    if not body:
        return slash
    # Collapse internal newlines to spaces so Claude slash-arg parsing stays
    # on one logical invocation line (production prompts are usually one line;
    # multi-line bodies still need to ride as skill args).
    if runtime == "claude":
        compact = " ".join(body.split())
        return f"{slash} {compact}"
    # Codex: slash alone often answers from memory / other installed skills.
    # Keep the production text intact; steer onto this skill + Nimble CLI.
    return (
        f"{slash}\n\n"
        "Load and follow only nimble-web-expert/SKILL.md (not company-deep-dive). "
        "Use the Nimble CLI (`nimble search` / `extract` / `map` / `crawl` / "
        "`agents`) for live web access. Do not use built-in web_search or answer "
        "from ~/.nimble/memory alone.\n\n"
        f"{body}"
    )


def wrap_user_prompt(prompt: str, *, runtime: RuntimeName = "claude") -> str:
    """Alias used by backends — slash-skill wrap, not system steering."""
    return wrap_user_prompt_with_skill(prompt, runtime=runtime)

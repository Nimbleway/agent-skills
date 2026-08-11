"""Scorer edge cases for nimble-web-expert production evals."""

from __future__ import annotations

from evals.commons.nimble_cmd import add_nimble_tools
from evals.commons.trace import NormalizedTrace
from evals.scorers.metrics import (
    first_turn_action,
    forbidden_tools,
    skill_selection,
    tool_selection,
)


def test_nimble_tools_detect_global_flags_before_subcommand() -> None:
    # Detailed cases live in test_nimble_cmd.py; keep a scorer-adjacent smoke.
    tools: list[str] = []
    add_nimble_tools(
        "nimble --client-source nimble-agent-skills agents:runs create --agent-id x",
        tools,
    )
    add_nimble_tools(
        "nimble --client-source nimble-agent-skills search --query 'acme'",
        tools,
    )
    assert "nimble agent create" in tools
    assert "nimble search" in tools


def _trace(**kwargs) -> NormalizedTrace:
    base = dict(
        runtime="claude",
        model="claude-sonnet-5",
        prompt="test",
    )
    base.update(kwargs)
    return NormalizedTrace(**base)


def test_skill_selection_skipped_when_may_clarify_and_clarifies() -> None:
    # Plain-text clarify (no ask_questions tool) — common for incomplete Extract prompts.
    trace = _trace(
        final_response="Please send the product codes and I'll extract the prices.",
        tools_called=[],
        asked_clarify=True,
    )
    expected = {
        "solution": "Extract",
        "clarification_policy": "may_clarify",
    }
    assert skill_selection(output=trace, expected_output=expected) is None
    fta = first_turn_action(output=trace, expected_output=expected)
    assert fta is not None and fta.value is True


def test_skill_selection_required_when_must_act() -> None:
    trace = _trace(
        final_response="Here are results",
        triggered_skills=[],
        tools_called=["nimble search"],
        tool_names=["nimble search"],
    )
    expected = {
        "solution": "Search",
        "clarification_policy": "must_act",
    }
    score = skill_selection(output=trace, expected_output=expected)
    assert score is not None and score.value is False


def test_tool_selection_passes_soft_nimble_match() -> None:
    trace = _trace(
        triggered_skills=["nimble-web-expert"],
        tools_called=["nimble extract"],
        tool_names=["nimble extract"],
        final_response="done",
    )
    expected = {
        "solution": "Extract",
        "clarification_policy": "must_act",
    }
    score = tool_selection(output=trace, expected_output=expected)
    assert score is not None and score.value is True


def test_tool_selection_accepts_map_for_crawl() -> None:
    trace = _trace(
        triggered_skills=["nimble-web-expert"],
        tools_called=["nimble map"],
        tool_names=["nimble map"],
        final_response="Found 180 pages — crawl all or overview?",
    )
    expected = {
        "solution": "Crawl",
        "clarification_policy": "may_clarify",
    }
    score = tool_selection(output=trace, expected_output=expected)
    assert score is not None and score.value is True


def test_auth_failure_with_error_sentinel_is_unscorable() -> None:
    """Regression: tools_called=['error'] must not count as first-turn act.

    The failed Codex CI run (401 Missing bearer) uploaded traces with
    tools_called=['error'] and scored first_turn_action ≈ 0.94 / forbidden_tools
    1.0 — false positives from infra sentinels.
    """
    trace = _trace(
        runtime="codex",
        model="gpt-5.6-sol",
        tools_called=["error"],
        tool_names=["error"],
        triggered_skills=[],
        final_response="",
        response="",
        error=(
            "{'message': 'unexpected status 401 Unauthorized: Missing bearer "
            "or basic authentication in header, url: https://api.openai.com/v1/responses'}"
        ),
    )
    expected = {
        "solution": "Search",
        "clarification_policy": "must_act",
        "forbidden_tools": ["web_search"],
        "scorable": [
            "first_turn_action",
            "skill_selection",
            "tool_selection",
            "forbidden_tools",
        ],
    }
    assert first_turn_action(output=trace, expected_output=expected) is None
    assert skill_selection(output=trace, expected_output=expected) is None
    assert tool_selection(output=trace, expected_output=expected) is None
    assert forbidden_tools(output=trace, expected_output=expected) is None


def test_error_sentinel_alone_is_not_act() -> None:
    # Even without an error field, a bare infra sentinel is not product work.
    trace = _trace(tools_called=["error"], tool_names=["error"], final_response="")
    expected = {"solution": "Search", "clarification_policy": "must_act"}
    # No auth marker + empty response → infra failure via sentinel-only path
    # when error is set; without error, observed should be "none" → fail must_act.
    score = first_turn_action(output=trace, expected_output=expected)
    assert score is not None and score.value is False
    assert score.comment and "observed=none" in score.comment

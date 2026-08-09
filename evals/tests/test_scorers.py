"""Scorer edge cases for nimble-web-expert production evals."""

from __future__ import annotations

from evals.commons.nimble_cmd import add_nimble_tools
from evals.commons.trace import NormalizedTrace
from evals.scorers.metrics import first_turn_action, skill_selection, tool_selection


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

"""Deterministic scorers for nimble-web-expert production evals."""

from __future__ import annotations

from typing import Any

from langfuse import Evaluation

from evals.commons.gold import remap_expected
from evals.commons.trace import NormalizedTrace


def _as_trace(output: Any) -> NormalizedTrace | None:
    if output is None:
        return None
    if isinstance(output, NormalizedTrace):
        return output
    if isinstance(output, dict):
        try:
            return NormalizedTrace.model_validate(output)
        except Exception:
            return None
    return None


def _score(name: str, value: bool, comment: str | None = None) -> Evaluation:
    return Evaluation(
        name=name,
        value=value,
        comment=comment,
        data_type="BOOLEAN",
    )


# Codex/Claude infra sentinels that must never count as product tool use.
# A prior bug treated tools_called=["error"] (auth/CLI failure) as first-turn "act".
_INFRA_TOOL_SENTINELS = frozenset({"error"})

_AUTH_FAILURE_MARKERS = (
    "401",
    "unauthorized",
    "missing bearer",
    "authentication",
    "codex auth missing",
    "openai_api_key",
)


def _called_tools(trace: NormalizedTrace) -> list[str]:
    return [
        str(t)
        for t in (trace.tool_names or trace.tools_called or [])
        if t and str(t) not in _INFRA_TOOL_SENTINELS
    ]


def _product_tools(called: list[str]) -> list[str]:
    return [t for t in called if t != "ask_questions"]


def _response_text(trace: NormalizedTrace) -> str:
    return (trace.final_response or trace.response or "").strip()


def _is_auth_or_infra_failure(trace: NormalizedTrace) -> bool:
    """True for hard auth/CLI failures that must not enter score denominators."""
    err = str(getattr(trace, "error", None) or "").strip()
    if not err:
        return False
    err_l = err.lower()
    if any(marker in err_l for marker in _AUTH_FAILURE_MARKERS):
        return True
    # Sentinel-only "tools" with an error and no real agent work.
    called = _called_tools(trace)
    product = _product_tools(called)
    skills = list(trace.triggered_skills or [])
    response = _response_text(trace)
    response_is_error_echo = bool(
        response
        and (
            response in err
            or err in response
            or any(marker in response.lower() for marker in _AUTH_FAILURE_MARKERS)
        )
    )
    if not product and not skills and (not response or response_is_error_echo):
        return True
    return False


def _empty(trace: NormalizedTrace | None) -> bool:
    """True only when there is nothing scorable (hard infra fail, no signals)."""
    if trace is None:
        return True
    if _is_auth_or_infra_failure(trace):
        return True
    err = getattr(trace, "error", None)
    if not err:
        return False
    # Soft/partial errors still carry signals — score them.
    if str(err).startswith("partial:"):
        # But only when there is real product signal (not auth wrapped as partial).
        called = _called_tools(trace)
        has_real = bool(
            (trace.triggered_skills or [])
            or _product_tools(called)
            or (
                _response_text(trace)
                and not any(
                    marker in _response_text(trace).lower()
                    for marker in _AUTH_FAILURE_MARKERS
                )
            )
        )
        return not has_real
    # Timeout/partial runs can still have skill/tool/response signals — score them.
    called = _called_tools(trace)
    has_signal = bool(
        (trace.triggered_skills or [])
        or _product_tools(called)
        or _response_text(trace)
    )
    return not has_signal


def _expected(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {}
    remapped = remap_expected(raw)
    if raw.get("solution") is not None:
        remapped["solution"] = raw.get("solution")
    return remapped


def _scorable(expected: dict[str, Any], name: str) -> bool:
    scorable = expected.get("scorable")
    if isinstance(scorable, list):
        return name in scorable
    return True


def _observed_first_turn(trace: NormalizedTrace) -> str:
    called = _called_tools(trace)
    product = _product_tools(called)
    if "ask_questions" in called and not product:
        return "clarify"
    if product:
        return "act"
    if any(t.startswith("nimble ") for t in called):
        return "act"
    response = _response_text(trace)
    # Never treat an auth/CLI error blob as a deliberate agent "respond".
    if response and any(marker in response.lower() for marker in _AUTH_FAILURE_MARKERS):
        return "none"
    if len(response) > 10:
        return "respond"
    return "none"


def skill_selection(
    *,
    output: Any = None,
    expected_output: Any = None,
    **kwargs: Any,
) -> Evaluation | None:
    expected = _expected(expected_output)
    trace = _as_trace(output)
    if _empty(trace) or not _scorable(expected, "skill_selection"):
        return None
    want = expected.get("expected_skill")
    if not want:
        return None
    assert trace is not None
    # Skill is scored on the act path. Clarifying/responding under
    # must/may_clarify (often plain text, not ask_questions) is unscored.
    policy = expected.get("clarification_policy")
    observed = _observed_first_turn(trace)
    if policy in {"must_clarify", "may_clarify"} and observed != "act":
        return None
    got = trace.triggered_skills or []
    ok = want in got
    return _score(
        "skill_selection",
        ok,
        None if ok else f"expected={want} got={got or []}",
    )


def first_turn_action(
    *,
    output: Any = None,
    expected_output: Any = None,
    **kwargs: Any,
) -> Evaluation | None:
    expected = _expected(expected_output)
    trace = _as_trace(output)
    if _empty(trace) or not _scorable(expected, "first_turn_action"):
        return None
    policy = expected.get("clarification_policy")
    if policy not in {"must_clarify", "must_act", "may_clarify"}:
        return None
    assert trace is not None
    observed = _observed_first_turn(trace)
    allows_respond = bool(expected.get("allows_respond_only"))
    if (
        policy == "must_act"
        and observed == "respond"
        and expected.get("expected_skill") in (trace.triggered_skills or [])
        and allows_respond
    ):
        ok = True
    elif policy == "must_clarify":
        ok = observed == "clarify"
    elif policy == "must_act":
        ok = observed == "act" or (observed == "respond" and allows_respond)
    else:
        ok = observed in {"clarify", "act", "respond"}
    comment = None
    if not ok:
        comment = (
            f"policy={policy} observed={observed} "
            f"tools={trace.tools_called or []} skills={trace.triggered_skills or []}"
        )
    return _score("first_turn_action", ok, comment)


def tool_selection(
    *,
    output: Any = None,
    expected_output: Any = None,
    **kwargs: Any,
) -> Evaluation | None:
    expected = _expected(expected_output)
    trace = _as_trace(output)
    if _empty(trace) or not _scorable(expected, "tool_selection"):
        return None
    if expected.get("clarification_policy") == "must_clarify":
        return None
    assert trace is not None
    if _observed_first_turn(trace) != "act":
        return None
    called = set(trace.tools_called or [])
    acceptable = expected.get("acceptable_tools")
    expected_tools = expected.get("expected_tools") or []
    if isinstance(acceptable, list) and acceptable:
        ok = any(
            any(str(t) in called for t in path)
            for path in acceptable
            if isinstance(path, list)
        )
    elif expected_tools:
        ok = any(str(t) in called for t in expected_tools)
    else:
        return None
    return _score(
        "tool_selection",
        ok,
        None if ok else f"called={sorted(called)}",
    )


def forbidden_tools(
    *,
    output: Any = None,
    expected_output: Any = None,
    **kwargs: Any,
) -> Evaluation | None:
    expected = _expected(expected_output)
    trace = _as_trace(output)
    if _empty(trace) or not _scorable(expected, "forbidden_tools"):
        return None
    forbidden = [str(x) for x in (expected.get("forbidden_tools") or [])]
    if not forbidden:
        return None
    assert trace is not None
    called = trace.tools_called or []
    hits = [ban for ban in forbidden if any(ban in c for c in called)]
    ok = not hits
    return _score("forbidden_tools", ok, None if ok else f"hits={hits}")


def response_non_empty(
    *,
    output: Any = None,
    expected_output: Any = None,
    **kwargs: Any,
) -> Evaluation | None:
    """True when the final response has more than 10 non-whitespace chars.

    This is a length gate, not an LLM quality judgement — name matches that.
    """
    expected = _expected(expected_output)
    trace = _as_trace(output)
    if _empty(trace):
        return None
    if expected.get("clarification_policy") == "must_clarify":
        return None
    assert trace is not None
    text = (trace.final_response or trace.response or "").strip()
    ok = len(text) > 10
    return _score("response_non_empty", ok, None if ok else "empty/short response")


WEB_EXPERT_EVALUATORS = [
    skill_selection,
    first_turn_action,
    tool_selection,
    forbidden_tools,
    response_non_empty,
]

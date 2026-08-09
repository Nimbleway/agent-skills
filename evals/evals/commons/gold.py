"""Runtime remap of assistant production gold → skill eval gold."""

from __future__ import annotations

from typing import Any

LIVE_SOLUTIONS = frozenset(
    {
        "Web Search Agents",
        "Extract",
        "Extraction Templates",
        "Search",
        "Crawl",
        "Map",
        "Answer",
    }
)

RESPOND_ONLY_SOLUTIONS = frozenset(
    {
        "Proxy",
        "Agent Skills & Plugin",
        "Other: use case does not require Nimble tools",
    }
)

# Soft expected nimble CLI families (contains-match against tools_called).
_SOLUTION_TOOLS: dict[str, list[str]] = {
    "Web Search Agents": ["nimble search", "nimble extract", "nimble agent"],
    "Extract": ["nimble extract"],
    "Extraction Templates": ["nimble extract", "nimble agent"],
    "Search": ["nimble search"],
    # Crawl often starts with map for discovery; either family is acceptable.
    "Crawl": ["nimble crawl", "nimble map"],
    "Map": ["nimble map"],
    "Answer": ["nimble search", "nimble extract"],
}

# Assistant forbidden tools → skill-side forbidden command substrings.
_FORBIDDEN_MAP: dict[str, list[str]] = {
    "create_wsa": ["nimble agent create", "nimble agents create"],
    "propose_wsa_scope": ["nimble agent create", "nimble agents create"],
    "create_job": ["nimble agent create"],
}


def remap_expected(expected_output: dict[str, Any] | None) -> dict[str, Any]:
    """Return skill-facing expected_output derived from assistant gold."""
    src = dict(expected_output or {})
    solution = src.get("solution")
    policy = src.get("clarification_policy") or "may_clarify"
    allows_respond = bool(src.get("allows_respond_only"))
    if solution in RESPOND_ONLY_SOLUTIONS:
        allows_respond = True

    remapped: dict[str, Any] = {
        "clarification_policy": policy,
        "allows_respond_only": allows_respond,
        "assistant_solution": solution,
        "forbidden_tools": _map_forbidden(src.get("forbidden_tools") or []),
        "message_type": src.get("message_type"),
        "use_case": src.get("use_case"),
    }

    scorable: list[str] = ["first_turn_action"]
    if src.get("forbidden_tools") or remapped["forbidden_tools"]:
        scorable.append("forbidden_tools")

    if solution in LIVE_SOLUTIONS:
        remapped["expected_skill"] = "nimble-web-expert"
        tools = list(_SOLUTION_TOOLS.get(str(solution), ["nimble search", "nimble extract"]))
        remapped["acceptable_tools"] = [[t] for t in tools]
        remapped["expected_tools"] = tools
        remapped["trajectory_mode"] = "within"  # any of the soft tools is OK
        scorable.extend(["skill_selection", "tool_selection"])
        if policy == "must_act" and not allows_respond:
            remapped["allows_respond_only"] = False
    elif solution in RESPOND_ONLY_SOLUTIONS:
        remapped["expected_skill"] = None
        remapped["allows_respond_only"] = True
        # Prefer not forcing skill load for install/proxy docs.
    else:
        # null / unlabeled — dialogue act only unless must_clarify.
        remapped["expected_skill"] = None

    # Extraction Templates: still prefer skill even when allows_respond_only
    if solution == "Extraction Templates":
        remapped["expected_skill"] = "nimble-web-expert"
        if "skill_selection" not in scorable:
            scorable.append("skill_selection")
        if "tool_selection" not in scorable:
            scorable.append("tool_selection")

    remapped["scorable"] = scorable
    return remapped


def _map_forbidden(forbidden: list[Any]) -> list[str]:
    out: list[str] = []
    for item in forbidden:
        key = str(item)
        out.extend(_FORBIDDEN_MAP.get(key, [key]))
    # de-dupe preserve order
    seen: set[str] = set()
    uniq: list[str] = []
    for x in out:
        if x not in seen:
            seen.add(x)
            uniq.append(x)
    return uniq


def solution_key(item: Any) -> str:
    expected = getattr(item, "expected_output", None)
    if expected is None and isinstance(item, dict):
        expected = item.get("expected_output")
    if isinstance(expected, dict) and expected.get("solution"):
        return str(expected["solution"])
    if isinstance(expected, dict) and expected.get("assistant_solution"):
        return str(expected["assistant_solution"])
    return "None"

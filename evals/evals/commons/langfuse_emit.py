"""Emit a LangfuseTracePayload under the current experiment-item observation."""

from __future__ import annotations

from typing import Any

from evals.commons.langfuse_payload import LangfuseObservation, LangfuseTracePayload


def _client() -> Any:
    from langfuse import get_client

    return get_client()


def emit_langfuse_payload(payload: LangfuseTracePayload) -> None:
    """Update current trace/span and create nested generation/tool observations."""
    client = _client()

    hard_error = bool(
        payload.trace_output.get("error")
        and not payload.trace_output.get("partial")
    )
    try:
        client.update_current_trace(
            input=payload.trace_input,
            output=payload.trace_output,
            metadata=payload.metadata,
            tags=payload.tags,
        )
    except Exception:  # noqa: BLE001
        pass

    try:
        client.update_current_span(
            name="web-expert-run",
            input=payload.trace_input,
            output=payload.trace_output,
            metadata=payload.metadata,
            level="ERROR" if hard_error else "DEFAULT",
            status_message=(
                str(payload.trace_output.get("error") or "")[:500] or None
            ),
        )
    except Exception:  # noqa: BLE001
        pass

    for obs in payload.observations:
        _emit_observation(client, obs)


def _emit_observation(client: Any, obs: LangfuseObservation) -> None:
    kwargs: dict[str, Any] = {
        "name": obs.name,
        "as_type": obs.as_type,
        "input": obs.input,
        "output": obs.output,
        "metadata": obs.metadata or None,
        "level": obs.level,
        "status_message": obs.status_message,
    }
    if obs.as_type == "generation":
        kwargs["model"] = obs.model
        if obs.usage_details:
            kwargs["usage_details"] = obs.usage_details
        if obs.cost_details:
            kwargs["cost_details"] = obs.cost_details
    clean = {k: v for k, v in kwargs.items() if v is not None}
    # Prefer start_observation + end so siblings nest under the experiment span
    # without re-entering a new current context that can drop prior siblings.
    created = client.start_observation(**clean)
    end = getattr(created, "end", None)
    if callable(end):
        end()

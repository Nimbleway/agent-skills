"""Claude Code → Langfuse OTEL env (official integration path).

See https://langfuse.com/integrations/developer-tools/claude-code
and https://langfuse.com/integrations/native/opentelemetry

Default: OTEL is OFF for evals. Claude's OTEL spans redact prompts/tool bodies
unless content gates are set, which produces empty observations in Langfuse.
The harness instead converts stream-json → populated generations/tools.

Set ``EVAL_CLAUDE_OTEL=1`` to also export native OTEL (with content gates on).
"""

from __future__ import annotations

import base64
import os
from typing import Any

from evals.commons.settings import EvalSettings


def langfuse_basic_auth(public_key: str, secret_key: str) -> str:
    raw = f"{public_key}:{secret_key}".encode()
    return base64.b64encode(raw).decode("ascii")


def langfuse_otel_endpoint(host: str) -> str:
    base = host.rstrip("/")
    return f"{base}/api/public/otel"


def build_claude_otel_env(settings: EvalSettings) -> dict[str, str]:
    """Env vars that make Claude Code export OTLP traces to Langfuse."""
    if not settings.langfuse_configured:
        return {}
    assert settings.langfuse_public_key and settings.langfuse_secret_key
    auth = langfuse_basic_auth(
        settings.langfuse_public_key, settings.langfuse_secret_key
    )
    endpoint = langfuse_otel_endpoint(settings.langfuse_host)
    headers = f"Authorization=Basic {auth},x-langfuse-ingestion-version=4"
    return {
        "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
        "CLAUDE_CODE_ENHANCED_TELEMETRY_BETA": "1",
        "OTEL_TRACES_EXPORTER": "otlp",
        "OTEL_METRICS_EXPORTER": "none",
        "OTEL_LOGS_EXPORTER": "none",
        "OTEL_EXPORTER_OTLP_PROTOCOL": "http/protobuf",
        "OTEL_EXPORTER_OTLP_ENDPOINT": endpoint,
        "OTEL_EXPORTER_OTLP_HEADERS": headers,
        "OTEL_EXPORTER_OTLP_TRACES_PROTOCOL": "http/protobuf",
        "OTEL_EXPORTER_OTLP_TRACES_HEADERS": headers,
        # Without these, Claude OTEL spans land empty in Langfuse.
        "OTEL_LOG_USER_PROMPTS": "1",
        "OTEL_LOG_ASSISTANT_RESPONSES": "1",
        "OTEL_LOG_TOOL_DETAILS": "1",
        "OTEL_LOG_TOOL_CONTENT": "1",
    }


def build_codex_langfuse_env(settings: EvalSettings) -> dict[str, str]:
    """Env for the official Codex Langfuse plugin (Stop-hook)."""
    if not settings.langfuse_configured:
        return {}
    return {
        "TRACE_TO_LANGFUSE": "true",
        "LANGFUSE_PUBLIC_KEY": settings.langfuse_public_key or "",
        "LANGFUSE_SECRET_KEY": settings.langfuse_secret_key or "",
        "LANGFUSE_BASE_URL": settings.langfuse_host.rstrip("/"),
        "LANGFUSE_HOST": settings.langfuse_host.rstrip("/"),
    }


def current_traceparent() -> str | None:
    """W3C TRACEPARENT for the active Langfuse/OTEL span, if any."""
    try:
        from langfuse import get_client

        client = get_client()
        trace_id = client.get_current_trace_id()
        span_id = client.get_current_observation_id()
        if not trace_id or not span_id:
            return None
        return f"00-{trace_id}-{span_id}-01"
    except Exception:  # noqa: BLE001
        return None


def strip_foreign_provider_secrets(env: dict[str, str], runtime: str) -> dict[str, str]:
    """Drop the other coding-agent provider's credentials from a child env.

    Child CLIs still inherit PATH / HOME / NIMBLE_* / Langfuse from the parent —
    a full allowlist is too brittle for local nvm + auth layouts — but a Codex
    run should not see ANTHROPIC_* / Claude OAuth, and a Claude run should not
    see OPENAI_*.
    """
    out = dict(env)
    if runtime == "claude":
        drop_prefixes = ("OPENAI_",)
        drop_exact: frozenset[str] = frozenset()
    elif runtime == "codex":
        drop_prefixes = ("ANTHROPIC_",)
        drop_exact = frozenset(
            {
                "CLAUDE_CODE_OAUTH_TOKEN",
                "CLAUDE_API_KEY",
            }
        )
    else:
        return out
    for key in list(out):
        if key in drop_exact or key.startswith(drop_prefixes):
            out.pop(key, None)
    return out


def merge_cli_env(
    base: dict[str, str],
    *,
    settings: EvalSettings,
    runtime: str,
    enable_otel: bool | None = None,
) -> dict[str, str]:
    """Merge Langfuse/OTEL wiring into a subprocess env."""
    env = strip_foreign_provider_secrets(dict(base), runtime)
    if runtime == "claude":
        # Default OFF — converted stream-json observations are the readable path.
        use_otel = (
            enable_otel
            if enable_otel is not None
            else os.getenv("EVAL_CLAUDE_OTEL", "0").lower()
            in {"1", "true", "yes"}
        )
        if use_otel:
            env.update(build_claude_otel_env(settings))
        tp = current_traceparent()
        if tp:
            env["TRACEPARENT"] = tp
            env["CLAUDE_CODE_PROPAGATE_TRACEPARENT"] = "1"
    elif runtime == "codex":
        env.update(build_codex_langfuse_env(settings))
        tp = current_traceparent()
        if tp:
            env["TRACEPARENT"] = tp
    return env


def payload_dict(payload: Any) -> dict[str, Any]:
    if hasattr(payload, "model_dump"):
        return payload.model_dump(mode="json")
    return dict(payload)

# Error Recovery Reference

Detailed error handling patterns for Nimble agent workflows.

---

## Authentication failure (401/403 from any tool call)

> Could not connect to Nimble. Please set your `NIMBLE_API_KEY` environment variable and retry.
> Get a key at [app.nimbleway.com](https://app.nimbleway.com/signup) → Account Settings → API Keys.

Do not proceed until auth is valid.

## Agent not found (404 from `nimble_agents_get`)

> Agent "{name}" was not found. It may have been removed or renamed.

Fall back to `nimble_agents_list` to search for available agents.

## Empty results (run returns no records)

> The agent returned no results. Possible causes:
> - The target URL may be unreachable or behind authentication.
> - The page structure may have changed since the agent was created.
> - Required parameters may be missing — check the agent's input_schema.

## Rate limiting / transient errors (429, 500-504)

> Transient server error. For MCP tool calls, wait briefly and retry once manually.
> For generated scripts, the SDK handles retry automatically (see below).
> For 429 responses, honor the `Retry-After` header if present.

### SDK built-in retry behavior

The SDK retries transient errors (429, 5xx, timeouts) automatically with exponential backoff.
Default: 2 retries. Increase for batch scripts: `AsyncNimble(max_retries=4)`.

For full retry configuration, backoff formula, and custom retry patterns,
see `sdk-patterns.md` > "Retry Behavior".

## Generation stuck (repeated `processing` status)

After 3 consecutive `processing` responses, inform the user:

> Agent generation is taking longer than expected. You can wait or try a simpler prompt.

## Publish conflict (409 from `nimble_agents_publish`)

The agent was already published in a previous session. The tool will automatically
fetch and return the existing agent details. If it cannot resolve the name,
suggest using `nimble_agents_list` to find the agent.

## Unknown SDK errors

The `nimble_python` SDK wraps `httpx` internally. Exceptions may be:
- `nimble_python.RateLimitError` (429) — SDK already retried and exhausted
- `nimble_python.InternalServerError` (5xx) — server-side failure after retries
- `nimble_python.APITimeoutError` — request timed out after retries
- `nimble_python.APIConnectionError` — network-level failure
- `httpx.HTTPStatusError` (with `.response.status_code`)
- `httpx.TransportError` subtypes (ConnectError, ReadTimeout, etc.)

For unfamiliar errors, consult documentation sources listed in SKILL.md.

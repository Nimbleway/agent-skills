# Error Recovery Reference

Detailed error handling patterns for Nimble agent workflows.

## Table of Contents

- [Authentication failure (401/403)](#authentication-failure-401403-from-any-tool-call)
- [Agent not found (404)](#agent-not-found-404-from-nimble_agents_get)
- [Empty results](#empty-results-run-returns-no-records)
- [Application-level run error](#application-level-run-error-error-field-in-response)
- [Rate limiting / transient errors (429, 5xx)](#rate-limiting--transient-errors-429-500-504)
- [Persistent data source failures](#persistent-data-source-failures-2-consecutive-500s)
- [Generation stuck](#generation-stuck-repeated-processing-status)
- [Publish conflict (409)](#publish-conflict-409-from-nimble_agents_publish)
- [Async task polling errors](#async-task-polling-errors)
- [Ambiguous agent match](#ambiguous-agent-match-no-clear-fit)
- [Unknown SDK errors](#unknown-sdk-errors)

---

## Authentication failure (401/403 from any tool call)

> Could not connect to Nimble. Please set your `NIMBLE_API_KEY` environment variable and retry.
> Get a key at [online.nimbleway.com/signup](https://online.nimbleway.com/signup) → Account Settings → API Keys.

Do not proceed until auth is valid.

## Agent not found (404 from `nimble_agents_get`)

> Agent "{name}" was not found. It may have been removed or renamed.

Fall back to `nimble_agents_list` to search for available agents.

## Empty results (run returns no records)

> The agent returned no results. Possible causes:
> - The target URL may be unreachable or behind authentication.
> - The page structure may have changed since the agent was created.
> - Required parameters may be missing — check the agent's `input_properties`.

## Application-level run error (`error` field in response)

> The agent run returned an error: "{error message}".
> This is an application-level failure, not an HTTP error.
> Common causes: page not found, access denied, invalid URL format.

For batch operations, log the error and continue with remaining items. Do not abort the entire batch.

## Rate limiting / transient errors (429, 500-504)

> Transient server error. For MCP tool calls, wait briefly and retry once manually.
> For generated scripts, the SDK handles retry automatically.

See `sdk-patterns.md` > "Retry Behavior" for SDK retry configuration.

### Persistent data source failures (2+ consecutive 500s)

When the same data source fails repeatedly (e.g., all LinkedIn agents return 500), the entire data pipeline for that source is likely down. **Stop retrying and pivot:**

1. **Use `google_search` with `site:` scoping** as a fallback. This searches the target domain via Google and often returns useful structured data in snippets:
   - LinkedIn down → `google_search` with `query: "CTO fintech NYC site:linkedin.com"`
   - Crunchbase agent missing → `google_search` with `query: "Series B startup site:crunchbase.com"`
   - Any site → `google_search` with `query: "<keywords> site:<domain>"`

2. **Use `nimble_web_search`** for deep content extraction from specific pages when Google snippets are insufficient.

3. **Present the pivot to the user** via `AskUserQuestion` — offer the `google_search` fallback, generating a custom agent, or waiting for the service to recover.

**Important:** When pivoting to a fallback agent, always repeat the full discovery cycle: `nimble_agents_get` → present schema → confirm → run. Never skip schema inspection when switching agents.

## Generation stuck (repeated `processing` status)

Poll with **only `session_id`** (omit `prompt`). The server waits ~50 s internally per call — no `sleep` needed. After 12 consecutive `processing` responses (~10 minutes), inform the user:

> Agent generation is taking longer than expected. You can wait or try a simpler prompt.

## Publish conflict (409 from `nimble_agents_publish`)

The agent was already published in a previous session. The tool will automatically
fetch and return the existing agent details. If it cannot resolve the name,
suggest using `nimble_agents_list` to find the agent.

## Async task polling errors

### Task stuck at `pending`

If a task stays `pending` beyond 60 seconds, it may be queued behind other jobs. Continue polling — tasks eventually process. Do not resubmit, as this creates duplicate work.

### `"task not finished yet"` from `/v1/tasks/{id}/results`

The task has not reached a terminal state. Continue polling `/v1/tasks/{task_id}` until `task.state` is `"success"` or `"failed"` before fetching results.

**IMPORTANT:** The terminal success state is `"success"`, NOT `"completed"`. Code that checks for `"completed"` will poll forever.

### Task state `"failed"`

The async task failed server-side. Retry by submitting a new async job. If failures persist, fall back to the sync `/v1/agent` endpoint.

### Auth 401 on `/v1/tasks/{id}` via curl

The tasks endpoint requires `Bearer` auth via the SDK's `get()` method. Direct `curl` calls may fail due to auth header handling differences. Use `nimble.get(f"/v1/tasks/{task_id}", cast_to=object)` instead.

## Ambiguous agent match (no clear fit)

When `nimble_agents_list` returns 0 matches or only partial matches:

1. **Explore with `nimble_web_search` first.** Before generating a custom agent, search the target domain to understand what data exists and how pages are structured. This reduces ambiguity and prevents generating agents for the wrong page type.
   - Example: `nimble_web_search` with `query: "site:crunchbase.com fintech series B NYC"` to see what Crunchbase pages look like for this use case.

2. **Try `google_search` with `site:` scoping** as an alternative to a dedicated agent. Google's index often surfaces the exact pages needed, and the snippets may contain sufficient structured data.

3. **Only generate a custom agent** when:
   - The target site has a consistent page structure (e.g., product pages, profiles).
   - A specific URL can be provided as an example for the generator.
   - The data needed goes beyond what Google snippets provide.

4. **When generating fails or produces poor results**, ask the user to clarify:
   - What specific data fields are needed.
   - An example URL of a page that has the desired data.
   - Whether an alternative data source is acceptable.

## Unknown SDK errors

The SDK raises typed exceptions: `RateLimitError` (429), `InternalServerError` (5xx), `APITimeoutError`, `APIConnectionError`. For unfamiliar errors, consult documentation sources listed in SKILL.md.

---
name: nimble-agents
description: >
  This skill should be used when the user asks to "extract data from a website",
  "scrape product details", "run a Nimble agent", "generate a web scraper",
  "get product prices", "compare prices across stores", "extract search results",
  "find a Nimble template", or needs structured web data extraction via Nimble
  agents/templates. Covers the full lifecycle: search, inspect, generate, publish,
  and run agents with result presentation and optional Python codegen.
allowed-tools:
  - mcp__nimble-mcp-server__nimble_agents_list
  - mcp__nimble-mcp-server__nimble_agents_get
  - mcp__nimble-mcp-server__nimble_agents_generate
  - mcp__nimble-mcp-server__nimble_agents_run
  - mcp__nimble-mcp-server__nimble_agents_publish
disable-model-invocation: false
license: MIT
metadata:
  version: "0.3.0"
  author: Nimbleway
  repository: https://github.com/Nimbleway/agent-skills
---

# Nimble Agents

Use this skill when the user wants structured extraction by running a Nimble agent/template.

User request: $ARGUMENTS

## Prerequisites

Before using this skill, ensure the Nimble MCP server is connected:

**Claude Code:**
```bash
export NIMBLE_API_KEY="your_api_key"
claude mcp add --transport http nimble-mcp-server https://mcp.nimbleway.com/mcp \
  --header "Authorization: Bearer ${NIMBLE_API_KEY}"
```

**VS Code (Copilot / Continue):**
Add to your MCP config:
```json
{
  "nimble-mcp-server": {
    "command": "npx",
    "args": ["-y", "mcp-remote@latest", "https://mcp.nimbleway.com/mcp",
             "--header", "Authorization:Bearer YOUR_API_KEY"]
  }
}
```

**Get an API key:** [app.nimbleway.com/signup](https://app.nimbleway.com/signup) → Account Settings → API Keys

## Goal

Always finish with an executed agent run result.

- Preferred path: find an existing agent/template and run it.
- Fallback path: generate a new agent, publish it, then run it.

## Schema-first principle

**Always call `nimble_agents_get` to inspect an agent's full schema before running it.** Never call `nimble_agents_run` without first completing a `nimble_agents_get` call and presenting the schema details to the user. The response provides:
- **`skills`** (output schema) — field names, types, and descriptions for every extracted field.
- **`input_properties`** — required and optional input parameters with types and examples.
- **`sample_data`** — real sample records showing actual field values and response shape.

This applies to every flow — interactive runs, batch scripts, codegen, and multi-agent comparisons. Use schema details to:
1. Confirm the agent extracts the fields the user needs before committing to a run.
2. Inform param mapping and script field extraction logic.
3. Present a clear picture of what each agent will return.

A live `nimble_agents_run` call is only needed to deliver final results — not to discover field names or validate agent suitability.

**CRITICAL: Schema presentation is a mandatory checkpoint.** After presenting schema details from `nimble_agents_get`, STOP and wait for the user to confirm before calling `nimble_agents_run`. Running agents costs API credits and time — never auto-advance from schema presentation to agent execution. The `nimble_agents_get` output schema and sample data are sufficient to validate agent suitability without a live run.

## Execution principle

**Infer and advance when the next action is unambiguous. Present options only when there is genuine ambiguity.**

At every decision point, evaluate whether the next step can be determined from the original request and current context. If yes, proceed immediately — narrate what you're doing but do not wait for confirmation. Only present numbered options when:
- Multiple agents could plausibly match and confident ranking is not possible.
- Required parameters cannot be inferred from the original request.
- An error or unexpected result requires a user decision.

**Exception — never auto-advance to `nimble_agents_run`:** After presenting agent schemas (step 4a), always present options and wait for user confirmation before running agents. Running agents is an expensive operation (API credits, network time). The schema presentation checkpoint exists specifically so the user can review output fields and confirm suitability before committing to a run. This exception applies even when the user's intent is fully specified.

This applies to all consumers — interactive human users and autonomous agents alike. Autonomous agents (no human-in-the-loop) cannot respond to prompts at all, so unnecessary options will stall them.

## Presentation rules

- After every tool call, present results in markdown tables. Never show raw JSON.
- Present numbered options **only when the next action is ambiguous** (see Execution principle). When auto-advancing, narrate the action instead (e.g. "No exact match found. Generating a custom agent...").
- Keep tables to 5 rows max per page. Use pagination when more results exist.

## Required flow

### 1. Parse extraction intent

From `$ARGUMENTS`, identify:
- Target domain/URL if provided.
- What fields/records the user expects in output.
- One or two broad keywords for search (e.g. "amazon", "reviews", "linkedin", "products").
- **Completeness check:** Does the request already specify a website/URL AND what data to extract? If yes, mark intent as "complete" — this allows auto-advancing through later steps without asking for information you already have.

### 2. Search for existing agents

Call `nimble_agents_list` with a **short, general query** (one or two keywords only). Never use full sentences.

**Always present options after search.** Never silently auto-advance past this step. The user must always see what was found and have the choice to generate a new agent.

Show top 5 with numbered action options:

```
### Existing agents for "{query}"

| # | Agent name | Description | Required inputs |
|---|-----------|-------------|-----------------|
| 1 | `agent-name-a` | Extracts product listings | `url` (string) |
| 2 | `agent-name-b` | Extracts search results | `query` (string), `url` (string) |
| 3 | `agent-name-c` | Extracts product details | `product_url` (string) |
| 4 | `agent-name-d` | Extracts pricing data | `url` (string) |
| 5 | `agent-name-e` | Extracts review data | `url` (string) |

Showing 1–5 of {total} results.

**Pick a number:**
6. Search with different keywords
7. Show next page of results
8. Generate a new custom agent
```

Omit option 7 ("next page") when current page shows all results (count <= 5 or last page).

If zero results:

```
No agents matched "{query}".

**Pick a number:**
1. Search with different keywords
2. Generate a new custom agent
```

### 3. Handle selection

Options are always presented after search:

- **User/agent picks an agent number (1-5)** → existing-agent path (step 4).
- **User/agent picks "search with different keywords"** → ask what keywords, then repeat step 2.
- **User/agent picks "show next page"** → call `nimble_agents_list` with `skip` incremented by 5, present next page.
- **User/agent picks "generate a new custom agent"** → proceed to step 5. Only ask for a description if the original request lacks a website/URL or what data to extract.

### 4. Existing-agent path

**4a. (MANDATORY CHECKPOINT — never skip, never auto-advance past)** Call `nimble_agents_get` with the selected agent name and **present schema details before any run**. This provides the full output schema (`skills` field), input parameters (`input_properties`), and sample data — sufficient for confirming agent suitability, running the agent, and generating code (see Schema-first principle). Always present details with options and **STOP — wait for user confirmation before proceeding to 4b/4c**. Do NOT call `nimble_agents_run` in the same response as schema presentation. The user must always be able to choose "Generate a new agent instead".

**Multi-agent comparison:** When the request involves multiple agents (e.g. comparing across stores), call `nimble_agents_get` on ALL agents first. Present a unified schema comparison showing each agent's output fields side by side, so the user can confirm all agents cover the needed fields before any runs proceed:

```
### Agent: `agent-name`

{description}

#### Input parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | string | Yes | Target page URL |
| `query` | string | No | Optional search filter |

#### Output fields

| Field | Type |
|-------|------|
| `title` | string |
| `price` | number |
| `rating` | number |

**Pick a number:**
1. Run this agent
2. Go back to search results
3. Generate a new agent instead
```

For multi-agent comparisons, present all agents together:

```
### Agents selected for comparison

| Store | Agent | Key Output Fields | Input |
|-------|-------|-------------------|-------|
| Amazon | `amazon_serp` | name, price, rating, review_count | `keyword` (string) |
| Walmart | `walmart_serp` | product_name, product_price, product_rating, product_reviews_count | `keyword` (string) |
| Best Buy | `bestbuy_serp` | product_name, product_price, product_rating, product_review_count | `keyword` (string) |

All agents cover the requested fields (price, rating, reviews).

**Pick a number:**
1. Run all agents
2. Replace an agent
3. Generate a new agent for a store
```

**4b.** Map values from the original request to input parameters. Infer as much as possible (URLs from mentioned websites, queries from described topics, etc.). Only ask for required params that truly cannot be inferred:

```
I need a few more values to run this agent:

| # | Parameter | Type | Description |
|---|-----------|------|-------------|
| 1 | `url` | string | Target page URL |
| 2 | `query` | string | Search keywords |

Please provide the values (e.g. "1: https://example.com, 2: shoes").
```

**4c.** Only after the user has confirmed in step 4a, call `nimble_agents_run` with `agent_name` and complete `params`. Present results:

```
### Results — `agent-name`

**Source:** {url}
**Records:** {count}

| # | Title | Price | Rating | URL |
|---|-------|-------|--------|-----|
| 1 | Product A | $29.99 | 4.5 | https://... |
| 2 | Product B | $19.99 | 4.2 | https://... |
| 3 | Product C | $39.99 | 4.8 | https://... |

**Pick a number:**
4. Run again with different inputs
5. Get Python code for this extraction
6. Generate a new custom agent
7. Search for a different agent
8. Done
```

Adapt column headers to match the actual output fields returned.

**Auto-advance:** If the original request is fully satisfied by the results, proceed directly to the final summary (step 6). Only present post-result options if the user is in an interactive session and might want follow-up actions.

If user picks "Get Python code" → go to step 7.

### 5. Generate path

**5a.** Check whether the original request already provides a website/URL and what data to extract.

**Auto-advance:** If both pieces are present (or can be reasonably inferred, e.g. "github trending repos" implies `https://github.com/trending` and repo metadata fields) → proceed directly to 5b. Do not ask the user to repeat information they already provided.

**Ask only if genuinely missing:**

```
Before I generate a new agent, please describe:
1. Which website/URL to extract from
2. What data fields you need (e.g. product name, price, rating)
```

Do not call generate until you have both pieces.

**5b.** Create a stable `session_id` (reuse for all generate/publish calls in this flow).

**5c.** Call `nimble_agents_generate` with a clear prompt. Present status with numbered options:

If `"waiting"` (follow-up questions):

```
The agent generator needs more information:

| # | Question |
|---|----------|
| 1 | {first question from response} |
| 2 | {second question from response} |

Please answer the questions above by number.
```

If `"processing"`:

```
Agent generation in progress... I'll check back shortly.
```

If `"complete"`:

**Auto-advance:** Narrate the generated agent's schema, then proceed directly to publish and run (steps 5e–5f). The user already expressed intent to extract data and generation succeeded — do not wait for confirmation.

```
### Agent generated: `agent-name`

#### Input parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | string | Yes | Target URL |

#### Output fields

| Field | Type |
|-------|------|
| `name` | string |
| `value` | string |

Publishing and running...
```

If the generated schema looks clearly wrong for the user's intent, present options instead:

```
**Pick a number:**
1. Publish and run this agent
2. Regenerate with a different description
3. Go back to search existing agents
```

If `"error"` or `"failed"`:

```
Generation failed: {error message}

**Pick a number:**
1. Retry with a modified description
2. Search for an existing agent instead
```

**5d.** Repeat generate calls with the same `session_id` until `"complete"`.

**5e.** Once generation is complete, call `nimble_agents_publish` with the same `session_id` **before** running the agent. Confirm:

```
Agent `agent-name` published successfully. Preparing to run...
```

If publish fails with a 409 conflict, the agent was already published — proceed to run.

**5f.** Build params from schema, infer values from the original request. Only ask for values that truly cannot be inferred (see step 4b). Call `nimble_agents_run` and present results using the format in step 4c.

### 6. Final response

Always end with a clean summary:

```
### Summary

| Detail | Value |
|--------|-------|
| Agent used | `agent-name` |
| Source | Existing / Generated |
| Records extracted | {count} |
| Published | Yes / N/A |

{extraction results table from step 4c}
```

### 7. Codegen (on request)

When the user picks "Get Python code", generate a ready-to-run script using `nimble_python` that reproduces the agent run. Use `uv run` with inline script metadata for zero-setup execution.

Consult **`references/sdk-patterns.md`** for complete templates and patterns:
- **Single-agent template** — for simple one-off runs.
- **Batch template with async parallelism** — for multiple items/URLs/queries.
- **Retry with exponential backoff** — for production reliability.
- **Dynamic batching (semaphore-only)** — for fastest throughput.

Apply substitution rules and response access patterns from `references/sdk-patterns.md` — substitute agent name, params dict, and field names from the agent's output schema (via `nimble_agents_get`). Handle both `parsing` (dict) and `results` (list) response shapes.

**Batch scripts must include:**
- Semaphore-only dynamic batching (`asyncio.Semaphore(10)` + `asyncio.gather`) — avoids "wait for slowest in batch" penalty.
- SDK-native retry via `AsyncNimble(max_retries=4)` — no custom retry code needed.
- See `references/sdk-patterns.md` for production-ready patterns and benchmarked concurrency settings.

After showing the code, return to the post-results options (minus the codegen option).

## Documentation & troubleshooting

When encountering unknown errors, unexpected response shapes, or SDK issues, consult these sources in order:

1. **`references/sdk-patterns.md`** (bundled) — correct SDK patterns, common mistakes, retry/backoff.
2. **https://docs.nimbleway.com/llms-full.txt** — full prose docs with code examples (~30k words, LLM-native). Use `WebFetch` to search for specific topics.
3. **https://docs.nimbleway.com/openapi.json** — machine-readable API contract (best for endpoint schemas and parameter validation).
4. **Context7** (if available) — query `/nimbleway/nimble-python` for SDK-specific types and patterns, or `/websites/nimbleway` for broadest coverage.

**When to look up docs:**
- Unexpected exception types or status codes from the SDK.
- Unknown field names in agent responses (field names vary by store/agent — verify with `nimble_agents_get` output schema or a test run).
- SDK method signatures or parameter types unclear.
- Need to understand rate limits, authentication, or API-level error codes.

## Error recovery

Quick reference for common errors. For detailed patterns and exception types, consult **`references/error-recovery.md`**.

| Error | Action |
|-------|--------|
| 401/403 (auth) | Show: "Set `NIMBLE_API_KEY` env var and retry." Do not proceed. |
| 404 (agent not found) | Fall back to `nimble_agents_list`. |
| Empty results | Check URL reachability, page structure changes, missing params. |
| 429 / 5xx (transient) | MCP calls: wait and retry once. Scripts: SDK retries automatically (2x default, configurable via `max_retries`). |
| Generation stuck | After 3 `processing` responses, suggest waiting or simplifying the prompt. |
| 409 publish conflict | Agent already published — proceed to run. |

## Additional references

For detailed guidance, consult:
- **`references/sdk-patterns.md`** — Python SDK patterns: running agents (`POST /v1/agent`), async parallel execution, concurrency tuning, response handling, and common mistakes.
- **`references/input-schema-guide.md`** — Mapping agent input schemas to params, including identifier-based (ASIN, product_id) and keyword patterns.
- **`references/agent-api-reference.md`** — Concise reference for all five MCP tools.
- **`references/error-recovery.md`** — Detailed error handling: SDK built-in retry behavior, exception types, and recovery patterns.

Working examples in `examples/`:
- **`examples/find-and-run-agent.md`** — Search, inspect, and run an existing agent.
- **`examples/generate-and-publish.md`** — Generate, publish, and run a new agent.
- **`examples/bulk-extraction.md`** — Run an agent across multiple URLs with aggregated results.

## Guardrails

- This skill is for agent workflows only — list, get, generate, run, and publish. Do not suggest scheduling, monitoring, automation, cron jobs, or any functionality outside the allowed tools.
- Do not suggest or offer capabilities beyond what the allowed tools provide.
- **Never ask for information already present in the original request.** Infer URLs, fields, and parameters from context.
- Only present numbered options when the next action is genuinely ambiguous. When auto-advancing, narrate the action.
- Always publish generated agents before running them (step 5e).
- Session IDs must be reused across generate and publish calls within the same flow.
- Present tool call results in tables. Never show raw JSON.
- Adapt table columns to match actual data returned; templates above are examples.
- For the generate path, only ask for extraction description if the original request lacks a target website or what data to extract.

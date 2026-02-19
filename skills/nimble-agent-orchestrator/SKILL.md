---
name: nimble-agent-orchestrator
description: >
  Find or generate a Nimble extraction agent for a task, then run it.
  Use when the user needs structured web data extraction via Nimble agents/templates.
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

# Nimble Agent Orchestrator

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
- Fallback path: generate a new agent, run it, then optionally publish/save it.

## Presentation rules

- After every tool call, present results in markdown tables. Never show raw JSON.
- Every user-facing prompt must end with **numbered options**. Options are always sequential numbers continuing after table rows if present.
- Keep tables to 5 rows max per page. Use pagination when more results exist.

## Required orchestration flow

### 1. Validate authentication

Call `nimble_agents_list` with a broad one-word query to validate auth and connectivity.
If auth fails, show:

> Could not connect to Nimble. Please set your `NIMBLE_API_KEY` environment variable and retry.

Do not proceed until auth is valid.

### 2. Parse extraction intent

From `$ARGUMENTS`, identify:
- Target domain/URL if provided.
- What fields/records the user expects in output.
- One or two broad keywords for search (e.g. "amazon", "reviews", "linkedin", "products").

### 3. Search for existing agents

Call `nimble_agents_list` with a **short, general query** (one or two keywords only). Never use full sentences.

Present top 5 results, then numbered action options continuing from the last row number:

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

### 4. Handle user selection

- **User picks an agent number (1-5)** → existing-agent path (step 5).
- **User picks "search with different keywords"** → ask what keywords, then repeat step 3.
- **User picks "show next page"** → call `nimble_agents_list` with `skip` incremented by 5, present next page.
- **User picks "generate a new custom agent"** → ask the user to describe what the agent should extract before proceeding. If the user's description is vague or missing, ask: "Please describe what data you want to extract and from which website." Only proceed to step 6 once you have a clear description.

### 5. Existing-agent path

**5a.** Call `nimble_agents_get` with the selected agent name. Present details with numbered options:

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

**5b.** If user picks "Run this agent": map values from the user request to input parameters. If any required params are still missing, ask in a table:

```
I need a few more values to run this agent:

| # | Parameter | Type | Description |
|---|-----------|------|-------------|
| 1 | `url` | string | Target page URL |
| 2 | `query` | string | Search keywords |

Please provide the values (e.g. "1: https://example.com, 2: shoes").
```

**5c.** Call `nimble_agents_run` with `agent_name` and complete `params`. Present results:

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
6. Search for a different agent
7. Done
```

Adapt column headers to match the actual output fields returned.

If user picks "Get Python code" → go to step 9.

### 6. Generate path

**6a.** Ensure you have a clear description of what to extract from the user. If not, ask:

```
Before I generate a new agent, please describe:
1. Which website/URL to extract from
2. What data fields you need (e.g. product name, price, rating)
```

Do not call generate until you have both pieces.

**6b.** Create a stable `session_id` (reuse for all generate/publish calls in this flow).

**6c.** Call `nimble_agents_generate` with a clear prompt. Present status with numbered options:

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

**Pick a number:**
1. Run this agent now
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

**6d.** Repeat generate calls with the same `session_id` until `"complete"`.

**6e.** When running: build params from schema, ask for missing values using the format in step 5b, then call `nimble_agents_run` and present results using the format in step 5c.

### 7. Optional publish (generate path only)

After a successful generated run, present:

```
### Save this agent?

This agent extracted {count} records successfully.

**Pick a number:**
1. Yes, save it — agent becomes searchable for future reuse
2. No, skip — agent is discarded after this session
```

If yes: call `nimble_agents_publish` with the same `session_id`. Confirm:

```
Agent `agent-name` published. You can find it in future searches via `nimble_agents_list`.
```

### 8. Final response

Always end with a clean summary:

```
### Summary

| Detail | Value |
|--------|-------|
| Agent used | `agent-name` |
| Source | Existing / Generated |
| Records extracted | {count} |
| Published | Yes / No / N/A |

{extraction results table from step 5c}
```

### 9. Codegen (on request)

When the user picks "Get Python code", generate a ready-to-run script using `nimble_python` (`pip install nimble_python`) that reproduces the agent run.

Substitute actual values from the completed run into the template below.

**Template:**

````
```python
import os
from nimble_python import Nimble

client = Nimble(api_key=os.environ["NIMBLE_API_KEY"])

# Run {agent-name} agent
response = client.extract(
    url="{url}",
    skill="{agent-name}",
)

# Process results
for record in response.data.parsing.entities:
    print(
        {field_prints}
    )
```

Install: `pip install nimble_python`
Set env: `export NIMBLE_API_KEY=<your-key>`
````

**Substitution rules:**

- `{agent-name}` → the `agent_name` from the run.
- `{url}` → the URL value passed in `params`.
- `{field_prints}` → one `f"field: {record.get('field')}"` line per output field from the agent's output schema. Use actual field names, e.g.:
  ```python
  print(
      f"title: {record.get('title')}, "
      f"price: {record.get('price')}, "
      f"rating: {record.get('rating')}"
  )
  ```
- If the agent's input schema has params beyond `url`, pass them via `extra_body`:
  ```python
  response = client.extract(
      url="{url}",
      skill="{agent-name}",
      extra_body={"{param}": "{value}", ...},
  )
  ```
  Only include non-URL params that were actually used in the run.

After showing the code, return to the post-results options (minus the codegen option).

## Error recovery

**Authentication failure** (401/403 from any tool call):
> Could not connect to Nimble. Please set your `NIMBLE_API_KEY` environment variable and retry.
> Get a key at [app.nimbleway.com](https://app.nimbleway.com/signup) → Account Settings → API Keys.

**Agent not found** (404 from `nimble_agents_get`):
> Agent "{name}" was not found. It may have been removed or renamed.
> Use `nimble_agents_list` to search for available agents.

**Empty results** (run returns no records):
> The agent returned no results. Possible causes:
> - The target URL may be unreachable or behind authentication.
> - The page structure may have changed since the agent was created.
> - Required parameters may be missing — check the agent's input_schema.

**Generation stuck** (repeated `processing` status):
After 3 consecutive `processing` responses, inform the user:
> Agent generation is taking longer than expected. You can wait or try a simpler prompt.

**Publish conflict** (409 from `nimble_agents_publish`):
The agent was already published in a previous session. The tool will automatically
fetch and return the existing agent details. If it cannot resolve the name,
suggest using `nimble_agents_list` to find the agent.

## Guardrails

- This skill is for extraction-agent workflows only, not general web search Q&A.
- Only ask for missing required inputs; do not over-prompt.
- Never publish generated agents without explicit user confirmation.
- Session IDs must be reused across generate and publish calls within the same flow.
- Always present tool call results in tables with numbered options at the end.
- Adapt table columns to match actual data returned; templates above are examples.
- For the generate path, always collect a clear extraction description before calling generate.

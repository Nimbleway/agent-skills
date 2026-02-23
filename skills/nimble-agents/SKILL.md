---
name: nimble-agents
argument-hint: "[query or URL]"
description: >
  Finds, generates, and runs agents to extract structured data from
  websites at scale. Handles multi-source with unified normalized schemas,
  composing batch pipelines, and their SDK code generation with structured output.
  Use when user asks to "get data from a website", "scrape a website",
  "compare data points across websites", "generate a web scraper",
  or mentions Nimble.
allowed-tools:
  - mcp__nimble-mcp-server__nimble_agents_list
  - mcp__nimble-mcp-server__nimble_agents_get
  - mcp__nimble-mcp-server__nimble_agents_generate
  - mcp__nimble-mcp-server__nimble_agents_status
  - mcp__nimble-mcp-server__nimble_agents_run
  - mcp__nimble-mcp-server__nimble_agents_publish
  - mcp__nimble-mcp-server__nimble_agents_update
  - mcp__nimble-mcp-server__nimble_web_search
disable-model-invocation: false
license: MIT
metadata:
  version: "0.6.0"
  author: Nimbleway
  repository: https://github.com/Nimbleway/agent-skills
---

# Nimble Agents

Structured web data extraction via Nimble agents. Always finish with executed results or runnable code.

User request: $ARGUMENTS

## Prerequisites

Ensure the Nimble MCP server is connected:

**Claude Code:**
```bash
export NIMBLE_API_KEY="your_api_key"
claude mcp add --transport http nimble-mcp-server https://mcp.nimbleway.com/mcp \
  --header "Authorization: Bearer ${NIMBLE_API_KEY}"
```

**VS Code (Copilot / Continue):**
```json
{
  "nimble-mcp-server": {
    "command": "npx",
    "args": ["-y", "mcp-remote@latest", "https://mcp.nimbleway.com/mcp",
             "--header", "Authorization:Bearer YOUR_API_KEY"]
  }
}
```

**Get an API key:** [online.nimbleway.com/signup](https://online.nimbleway.com/signup) → Account Settings → API Keys

## Core principles

- **Fastest path to data.** Default route: discover agent → get schema → run → display results. Planning and generation are escalation paths.
- **Always search existing agents first.** Call `nimble_agents_list` before considering generate. Hard rule.
- **AskUserQuestion at every decision point — no exceptions.** Always present the standard `AskUserQuestion` prompts shown in each step. Never skip them, never auto-advance without asking. Never present choices as plain numbered lists. Constraints: 2–4 options, header max 12 chars, label 1–5 words. Recommended option goes first with "(Recommended)".
- **Schema before run — always.** Call `nimble_agents_get` before `nimble_agents_run`. Present input parameters and output fields in markdown tables. This applies when switching agents too.
- **Verify response shape before script generation.** Check `skills` and `entity_type` from `nimble_agents_get` to determine REST API response nesting. See **`references/agent-api-reference.md`** > "Response shape inference" and **`references/sdk-patterns.md`** > "Response structure verification".
- **`google_search` is not a general search tool.** It is a SERP analysis agent for rank tracking and SEO analysis. For finding information, use `nimble_web_search`. See **`references/error-recovery.md`**.
- **NEVER call `nimble_agents_generate`, `nimble_agents_update`, `nimble_agents_status`, or `nimble_agents_publish` in the foreground.** These MUST run inside a background Task agent. Calling them in the foreground floods context with large polling responses and wastes the conversation's token budget. This is a HARD RULE — no exceptions, not even for "just one quick update". Always launch a background Task agent for any generate/update/status/publish operation.
- **Foreground MCP calls are limited to exactly 3 tools:** `nimble_agents_list` (routing), `nimble_agents_get` (schema display), `nimble_agents_run` (interactive execution). Everything else runs in a background Task agent. See [Delegation model](#delegation-model).
- **Never use `nimble_find_search_agent`, `nimble_run_search_agent`, `nimble_url_extract`, or any WSA template tools.**

## Delegation model

The foreground conversation orchestrates and presents results. Background Task agents handle all MCP-heavy work.

**Foreground — ONLY these 3 MCP tools allowed:**

| Tool | Purpose | Max calls |
|------|---------|-----------|
| `nimble_agents_list` | Route to existing agent | 1 per source |
| `nimble_agents_get` | Display schema before run | 1 per agent |
| `nimble_agents_run` | Interactive execution (≤5 items) | 1 per item |

**Background — EVERYTHING else (mandatory, no exceptions):**

| Phase | Background agent | Foreground does |
|-------|-----------------|-----------------|
| Discovery (`nimble_web_search` deep) | Step 1D | Launch, present report |
| Agent create/update (`nimble_agents_generate`, `nimble_agents_update`, `nimble_agents_status`, `nimble_agents_publish`) | Step 3 | Launch, present report |
| Script generation (write code to call existing agent) | Step 2B | Launch, present script |

**`nimble_agents_generate`, `nimble_agents_update`, `nimble_agents_status`, `nimble_agents_publish` are BANNED from the foreground. Always use `Task(subagent_type="general-purpose", run_in_background=True)` for these.**

For **multi-source workflows**, launch one background agent per source/phase in parallel. Gather reports, then present the combined plan.

## Response shapes

| Layer | Path | Shape | When used |
|-------|------|-------|-----------|
| MCP tool (`nimble_agents_run`) | `data.results` | Always array | Interactive run (Step 2A) |
| REST API — ecommerce SERP | `data.parsing` | `list` (array) | Script generation (Step 2B) |
| REST API — non-ecommerce SERP | `data.parsing.entities.{Type}` | `dict` with nested arrays | Script generation (Step 2B) |
| REST API — PDP | `data.parsing` | `dict` (flat) | Script generation (Step 2B) |

Always check `typeof`/`isinstance` before iterating REST responses.

## Step 1: Route

From `$ARGUMENTS`, detect 3 things:

**1. Clarity** — `clear` (default) or `needs-planning`

Only `needs-planning` when ALL of these are absent: a target URL/site/domain, clear data to extract, a single well-scoped task. Most requests are `clear`.

**2. Agent match** — call `nimble_agents_list` ONCE **per source/domain** with the most specific short keyword (1–2 words, e.g., domain name or product type). This is ALWAYS the first action. For multi-source requests (e.g., "compare Amazon and Walmart prices"), call once per source. Do not retry the same source with different queries — if 0 results for a source, route it to Discovery (Step 1D).

| Result | Route |
|--------|-------|
| Exact match | Show schema summary + `AskUserQuestion`: "Use this agent" (Recommended) / "Create new agent" → Step 3 |
| Close match (same domain/type, missing fields or different scope) | Show schema gaps + `AskUserQuestion`: "Update this agent" (Recommended) / "Create new agent" → Step 3 |
| 2+ plausible matches | Show table + `AskUserQuestion` with top matches + "Update closest agent" (Recommended) |
| 0 matches | Launch **Discovery background agent** (Step 1D) → results inform Step 3 |

**3. Execution mode** — `interactive` (default) or `script`

Route to script generation (Step 2B) when ANY of: scale >50, file output (CSV/JSON), multi-store comparison, batch input file, user explicitly asks for code. Otherwise interactive. **Script generation writes code that calls an existing agent** — it does not create new agents. If no agent exists yet, resolve that first (Step 3) before generating a script.

### Step 1P: Plan mode (rare — only when `needs-planning`)

1. **Clarify** — `AskUserQuestion` to resolve critical unknowns (max 2 questions). Focus on: what site(s), what data fields, what output format.
2. **Explore** — `nimble_agents_list` for each target (foreground, 1 call each). For unfamiliar domains, launch Discovery background agents in parallel (Step 1D).
3. **Present plan** — gap analysis table:

| # | Site / Data Source | Agent | Status |
|---|-------------------|-------|--------|
| 1 | amazon.com products | amazon-product-details | Existing |
| 2 | walmart.com products | — | Generate |

4. **Execute** — Step 2 for existing agents, Step 3 for generations (in parallel as background tasks).

### Step 1D: Discovery (background agent — for unfamiliar domains)

Launch when `nimble_agents_list` returns 0 matches and the target domain needs exploration. Runs as `Task(subagent_type="general-purpose", run_in_background=True)`. The foreground tells the user: *"Exploring {domain} to understand available data..."*

**Task prompt template:**

```
Explore {domain} for {user_intent}.

Use `nimble_web_search` (MCP) with deep_search=true to discover the site and available data:
1. Search "{domain} {keywords}" with deep_search=true, max_results=5 — this fetches and extracts full page content from each result, giving you product listings, detail pages, and field structures in one call.

**Return a structured report:**
- DOMAIN: {domain}
- ESTIMATED_ITEMS: count matching query
- LISTING_URL_PATTERN: e.g., /category/filter?color=green
- DETAIL_URL_PATTERN: e.g., /p/{slug}-{SKU}.html
- AVAILABLE_FIELDS: list of extractable fields (name, price, description, materials, etc.)
- MISSING_FIELDS: fields the user wants but the site doesn't have (e.g., ratings, reviews)
- RECOMMENDED_APPROACH: generate custom agent / use existing agent from {alternative} / combine sources
- SAMPLE_URLS: 2–3 example URLs for agent generation
- LIMITATIONS: login walls, pagination limits, JS rendering, etc.

Do NOT use AskUserQuestion. Do NOT use nimble_find_search_agent, nimble_run_search_agent, or nimble_url_extract.
```

On receiving the report, the foreground conversation:
1. Presents key findings to the user.
2. If data gaps exist (e.g., missing ratings), asks the user via `AskUserQuestion` how to proceed.
3. Routes to Step 3 (generate) with the discovery context, or Step 2 if existing agents cover the need.

For **multi-source workflows**, launch one Discovery agent per unfamiliar domain in parallel. Gather all reports before presenting the combined plan.

## Step 2: Run existing agent

Two sub-paths based on execution mode.

### 2A: Interactive (small scale, display output)

**2A-1.** Call `nimble_agents_get`. Present schema in markdown tables:
- **Input parameters:** name, required, type, description, example
- **Output fields:** key fields from `skills` dict

See **`references/agent-api-reference.md`** > "Input Parameter Mapping" for the full `input_properties` format and mapping rules.

**2A-2.** Always confirm before running via `AskUserQuestion`:

```
question: "Run {agent_name} with these parameters?"
header: "Confirm"
options:
  - label: "Run agent (Recommended)"
    description: "Execute {agent_name} with {summary of inferred parameters}"
  - label: "Change parameters"
    description: "Adjust input parameters before running"
  - label: "Create new agent"
    description: "Create a custom agent instead (Step 3)"
```

**2A-3.** Call `nimble_agents_run`. Present results as markdown table. Always ask what to do next:

```
question: "What next?"
header: "Next step"
options:
  - label: "Done"
    description: "Finish with these results"
  - label: "Run again"
    description: "Re-run with different parameters"
  - label: "Get script"
    description: "Write a script to run this agent at scale (Step 2B)"
```

**Bulk (2–5 URLs):** Run per URL, aggregate results, handle individual failures without aborting. See **`references/batch-patterns.md`** > "Interactive batch extraction".

### 2B: Script generation (large scale, file output, multi-store)

**Writes a runnable script that calls an existing Nimble agent at scale via the SDK/REST API.** This does NOT create new agents — the agent must already exist. Runs as a background Task agent. The foreground infers language, launches the agent, and presents the generated script for confirmation.

**2B-1.** Infer language from project context (foreground, before launching):

| Project file | Language |
|-------------|----------|
| `pyproject.toml`, `requirements.txt`, `*.py` | Python |
| `package.json`, `tsconfig.json` | TypeScript/Node |
| `go.mod` | Go (REST API) |
| None of the above | Default to Python |

**2B-2.** Launch script generation background agent: `Task(subagent_type="general-purpose", run_in_background=True)`.

**Task prompt template:**

```
Write a {language} script that calls existing Nimble agent(s) at scale via SDK/REST API.

**Existing agents to call:** {agent_names}
**User intent:** {user_prompt}
**Output format:** {csv/json/etc}
**Scale:** {number of items/queries}

This is SCRIPT GENERATION — writing code that calls existing agents. Do NOT create new agents
(no nimble_agents_generate/update/publish). The agents listed above already exist.

Steps:
1. Call `nimble_agents_get` for each agent to inspect input_properties and skills.
2. Read the reference files:
   - `references/sdk-patterns.md` (Python) or `references/rest-api-patterns.md` (other languages)
   - `references/batch-patterns.md` (for multi-store normalization)
3. Write a complete, ready-to-run script with:
   - Smoke test first — validate a single query before full batch. Abort on failure.
   - Progress reporting — compact single-line status after each poll cycle.
   - Pagination handling for large result sets.
   - Multi-store field normalization (if applicable).
   - Output to {format}.
   - Incremental file writes for large pipelines (50+ jobs).

Return the complete script and a brief summary of:
- Agent schemas used (input params, key output fields)
- Normalization mappings (if multi-store)
- Total estimated API calls

Do NOT use AskUserQuestion. Do NOT use nimble_find_search_agent or nimble_run_search_agent.
Do NOT call nimble_agents_generate, nimble_agents_update, or nimble_agents_publish.
```

**2B-3.** Present the generated script and confirm execution via `AskUserQuestion` (foreground):

```
question: "Run this script?"
header: "Confirm"
options:
  - label: "Run script (Recommended)"
    description: "Execute the generated script"
  - label: "Edit first"
    description: "Review and modify the script before running"
```

**No agent validation step here.** The 50-input validation flow (Step 3) is only for agent creation/update. Script generation uses an existing, already-validated agent — just write the script and run it.

## Step 3: Create or update agent (on the Nimble platform)

**Creates a new agent or updates an existing one on Nimble's platform via `nimble_agents_generate`/`nimble_agents_update`.** This is NOT code/script generation — it creates an extraction definition that can later be called interactively (Step 2A) or from a script (Step 2B). ALWAYS runs as a background agent. The foreground conversation stays responsive.

### 3-1. Create a stable `session_id` (UUID v4).

### 3-2. Ask the user ONCE (foreground only — agent creation/update ONLY, never for script generation):

```
question: "Run refinement-validation before publishing?"
header: "Validate"
options:
  - label: "Yes, validate (Recommended)"
    description: "Discovery → generate → validate 50 inputs (80% pass) → publish. Auto-retries on failure."
  - label: "No, generate only"
    description: "Generate → publish immediately without validation testing"
```

**This is the ONLY AskUserQuestion for the generate/update flow. The background agent NEVER asks the user anything.**

### 3-3. Launch background Task agent

Set `refine_validate` to the user's choice. See **`references/generate-update-and-publish.md`** for the complete Task prompt template, lifecycle phases, and key rules.

The background agent executes a closed-loop lifecycle:

1. **Discovery** (when `refine_validate=true` or auto-triggered by failure) — use `nimble_web_search` with `deep_search=true` (MCP) to explore the domain. Build a refined prompt with specific fields, URLs, examples.
2. **Create/Update** — `nimble_agents_generate` (first time only) or `nimble_agents_update` (all recovery and refinement, same session_id). Never regenerate. Retry-with-fix max 2 times on error.
3. **Poll** — ONLY `nimble_agents_status` in a loop (never `nimble_agents_update` during polling). Loop: status → check → `Bash(sleep 30)` → repeat. Strictly 30s, max 10 checks. **5 consecutive errors or 10 checks → exit loop → update loop** (discovery, then `nimble_agents_update`).
4. **Validate** — generate 50 diverse test inputs, write a Python validation script to `/tmp/validate_agent_{name}.py`, execute via `Bash(uv run ...)`. Assert >= 80% pass rate. Uses REST API `POST /v1/agent` (response at `data.parsing`).
5. **Publish** — `nimble_agents_publish` on validation pass (or immediately if `refine_validate=false` and no failures).
6. **Report** — structured report: agent name, operation, status, pass rate, schemas, sample results.

**Auto-triggered update loop** (regardless of initial preference): on 5+ consecutive poll errors, poll timeout (10 checks), or <80% validation pass rate. **Never regenerate — always `nimble_agents_update` with the same session_id.** Max 2 cycles. **Overall timeout: 15 minutes wall-clock.** Use `max_turns=50` on the Task launch.

Tell the user: "Agent generation started in the background. I'll report results when complete."

### 3-4. Present report

When the background agent completes, present the report. On success, the agent now exists on the platform — route to Step 2A (interactive run) or Step 2B (script generation) based on execution mode. On failure after max cycles, offer:

```
question: "Agent validation did not reach 80% pass rate. How to proceed?"
header: "Next step"
options:
  - label: "Publish anyway"
    description: "Publish with current pass rate ({rate}%)"
  - label: "Update agent"
    description: "Provide specific instructions to refine the agent"
```

## Step 4: Final response

End with a concise summary table:

| Field | Value |
|-------|-------|
| Agent(s) used | `agent_name` |
| Source | Existing / Generated |
| Records extracted | count |
| Output | Displayed / `filename.csv` |

Include the extraction results (or top N if large).

## Documentation & troubleshooting

When encountering errors or needing grounding, consult:

1. **`references/sdk-patterns.md`** — correct SDK patterns and common mistakes.
2. **https://docs.nimbleway.com/llms-full.txt** — full prose docs.
3. **https://docs.nimbleway.com/openapi.json** — API contract.
4. **Context7** (if available) — query `nimbleway`.

## Error recovery

Consult **`references/error-recovery.md`** for handling patterns including persistent data source failures, ambiguous agent matches, and the full fallback hierarchy.

## Additional references

Load reference files proactively during script generation (Step 2B). Always consult `sdk-patterns.md` (Python) or `rest-api-patterns.md` (other languages) before writing scripts.

- **`references/sdk-patterns.md`** — Running agents, async endpoint, batch pipelines, incremental file writes.
- **`references/agent-api-reference.md`** — All 8 MCP tools reference plus input parameter mapping.
- **`references/batch-patterns.md`** — Multi-store comparison, normalization, interactive batch, codegen walkthrough.
- **`references/generate-update-and-publish.md`** — Full agent creation/update lifecycle (Step 3): discovery, creation, polling, SDK validation (50 inputs, 80% threshold), publish, reporting, update loop.
- **`references/rest-api-patterns.md`** — REST API patterns for TypeScript, Node, curl, and other non-Python languages.
- **`references/error-recovery.md`** — Error handling and recovery patterns.

## Guardrails

- **NEVER call `nimble_agents_generate`, `nimble_agents_update`, `nimble_agents_status`, or `nimble_agents_publish` in the foreground conversation.** These MUST run inside a background `Task` agent. No exceptions — not even "just one quick call". Polling in the foreground floods context and wastes tokens.
- **Foreground MCP tools are limited to:** `nimble_agents_list`, `nimble_agents_get`, `nimble_agents_run`. Nothing else.
- **Never** use `nimble_find_search_agent`, `nimble_run_search_agent`, or any WSA template tools.
- **Generate once, update for everything else.** `nimble_agents_generate` only once per agent. All recovery, refinement, and follow-ups via `nimble_agents_update` with the same session_id — never regenerate. When listing finds a close-match agent, prefer updating it over generating from scratch.
- Published agents are automatically forked when updated. UBCT-based agents cannot be updated — generate a new one instead.
- Present tool call results in markdown tables. Never show raw JSON.

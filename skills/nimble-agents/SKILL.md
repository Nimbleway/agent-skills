---
name: nimble-agents
argument-hint: "[query or URL]"
description: >
  This skill should be used when the user asks to "get data from a website",
  "scrape a website", "extract product details", "compare prices across stores",
  "pull data from Amazon or Walmart", "generate a web scraper",
  "build a data extraction pipeline", or mentions Nimble.
  Covers discovering existing extraction agents, running them interactively,
  generating scripts for large-scale extraction, and creating new custom agents.
allowed-tools:
  - mcp__plugin_nimble_nimble-mcp-server__nimble_agents_list
  - mcp__plugin_nimble_nimble-mcp-server__nimble_agents_get
  - mcp__plugin_nimble_nimble-mcp-server__nimble_agents_generate
  - mcp__plugin_nimble_nimble-mcp-server__nimble_agents_status
  - mcp__plugin_nimble_nimble-mcp-server__nimble_agents_run
  - mcp__plugin_nimble_nimble-mcp-server__nimble_agents_publish
  - mcp__plugin_nimble_nimble-mcp-server__nimble_agents_update_from_agent
  - mcp__plugin_nimble_nimble-mcp-server__nimble_agents_update_session
  - mcp__plugin_nimble_nimble-mcp-server__nimble_web_search
disable-model-invocation: false
license: MIT
metadata:
  version: "0.6.1"
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

**API key:** [online.nimbleway.com/signup](https://online.nimbleway.com/signup) → Account Settings → API Keys

## Core principles

- **Fastest path to data.** Default route: discover agent → get schema → run → display results. Planning and generation are escalation paths.
- **Always search existing agents first.** Call `nimble_agents_list` before considering generate. Hard rule.
- **Update over generate — always.** When a close-match agent exists (same domain/type, even if missing fields or different scope), update it rather than generating from scratch. Updating preserves proven extraction logic and is faster, cheaper, and more reliable. Only generate a new agent when `nimble_agents_list` returns 0 results for the target domain. Never offer "Create new agent" as the recommended option when a close match exists.
- **AskUserQuestion at every decision point — no exceptions.** Always present the standard `AskUserQuestion` prompts shown in each step. Never skip them, never auto-advance without asking. Never present choices as plain numbered lists. Constraints: 2–4 options, header max 12 chars, label 1–5 words. Recommended option goes first with "(Recommended)".
- **Schema before run — always.** Call `nimble_agents_get` before `nimble_agents_run`. Present input parameters and output fields in markdown tables. This applies when switching agents too.
- **Script generation (Step 2B) is ONLY for large-scale, high-volume tasks.** Never generate code for normal interactive requests. Script mode requires ALL of: scale >50 items AND the user explicitly asks for code/script/CSV/batch output. Multi-source requests, dataset requests, and comparison requests do NOT automatically trigger script mode — run them interactively first. The default path is always: discover → run → display results.
- **Verify response shape before script generation.** Check `skills` and `entity_type` from `nimble_agents_get` to determine REST API response nesting. See **`references/agent-api-reference.md`** > "Response shape inference" and **`references/sdk-patterns.md`** > "Response structure verification".
- **`google_search` is not a general search tool.** It is a SERP analysis agent for rank tracking and SEO analysis. For finding information, use `nimble_web_search`. See **`references/error-recovery.md`**.
- **All web search MUST use `nimble_web_search` (MCP).** Never use `WebSearch`, `WebFetch`, or `curl`. See [Guardrails](#guardrails).
- **Mutation tools (`generate`, `update`, `status`, `publish`) are BANNED from the foreground.** Always delegate to a Task agent. See [Delegation model](#delegation-model).
- **Task agents MUST use `run_in_background=False`.** Background mode breaks MCP access. See [Delegation model](#delegation-model).
- **Foreground MCP calls limited to 3 tools:** `nimble_agents_list`, `nimble_agents_get`, `nimble_agents_run`.
- **Never use `nimble_find_search_agent`, `nimble_run_search_agent`, `nimble_url_extract`, or any WSA template tools.**

## Delegation model

The foreground conversation orchestrates and presents results. Task agents handle all MCP-heavy work.

**Foreground — ONLY these 3 MCP tools allowed (direct calls):**

| Tool | Purpose | Max calls |
|------|---------|-----------|
| `nimble_agents_list` | Route to existing agent | 1 per source |
| `nimble_agents_get` | Display schema before run | 1 per agent |
| `nimble_agents_run` | Interactive execution (≤5 items) | 1 per item |

**Task agents — EVERYTHING else (mandatory, no exceptions):**

| Phase | Task agent | Foreground does |
|-------|-----------|-----------------|
| Discovery (`nimble_web_search` deep) | Step 1D | Launch, present report |
| Agent create/update (`nimble_agents_generate`, `nimble_agents_update_from_agent`, `nimble_agents_update_session`, `nimble_agents_status`, `nimble_agents_publish`) | Step 3 | Launch, present report |
| Script generation (write code to call existing agent) | Step 2B | Launch, present script |

**`nimble_agents_generate`, `nimble_agents_update_from_agent`, `nimble_agents_update_session`, `nimble_agents_status`, and `nimble_agents_publish` are BANNED from the foreground. Always use `Task(subagent_type="general-purpose", run_in_background=False)` for these.**

**Why `run_in_background=False`:** Background Task agents (`run_in_background=True`) [cannot access MCP tools](https://github.com/anthropics/claude-code/issues/13254) — they silently fall back to bash/curl and fail. Using `run_in_background=False` ensures MCP tool access. The Task agent still runs in its own context window (no foreground pollution); the only cost is the foreground waits for completion. When this platform limitation is resolved, switch back to `run_in_background=True`.

For **multi-source workflows**, launch Task agents sequentially (one per source/phase). Gather reports, then present the combined plan.

### MCP tool registry

All Task agent prompts MUST include the tool registry block so the subagent knows the exact MCP tool names. Copy this block into every Task prompt:

```
**MCP tool registry (call these as MCP tool invocations, NOT bash/curl):**
| Short name | Full MCP tool name |
|------------|--------------------|
| nimble_agents_list | mcp__plugin_nimble_nimble-mcp-server__nimble_agents_list |
| nimble_agents_get | mcp__plugin_nimble_nimble-mcp-server__nimble_agents_get |
| nimble_agents_generate | mcp__plugin_nimble_nimble-mcp-server__nimble_agents_generate |
| nimble_agents_update_from_agent | mcp__plugin_nimble_nimble-mcp-server__nimble_agents_update_from_agent |
| nimble_agents_update_session | mcp__plugin_nimble_nimble-mcp-server__nimble_agents_update_session |
| nimble_agents_status | mcp__plugin_nimble_nimble-mcp-server__nimble_agents_status |
| nimble_agents_publish | mcp__plugin_nimble_nimble-mcp-server__nimble_agents_publish |
| nimble_agents_run | mcp__plugin_nimble_nimble-mcp-server__nimble_agents_run |
| nimble_web_search | mcp__plugin_nimble_nimble-mcp-server__nimble_web_search |

**CRITICAL: Use MCP tool calls only. NEVER use bash, curl, wget, WebSearch, or WebFetch to call APIs or search the web. NEVER construct MCP endpoint URLs manually.**
```

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
| Close match (same domain/type, missing fields or different scope) | Show schema gaps + `AskUserQuestion`: "Update this agent" (Recommended) / "Create new agent". **Always recommend update** — it preserves existing extraction logic and is faster than generating from scratch. |
| 2+ plausible matches | Show table + `AskUserQuestion` with top matches + "Update closest agent" (Recommended). Pick the agent with the most field overlap. |
| 0 matches | Launch **Discovery Task agent** (Step 1D) → results inform Step 3. **This is the ONLY case where generating a new agent is appropriate.** |

**Update is always preferred over generate.** A close-match agent on the same domain already has working URL patterns, pagination logic, and parsing rules. Updating it to add/change fields is a minor refinement. Generating from scratch rebuilds everything and risks lower quality. Only generate when no agent exists for the target domain at all.

**3. Execution mode** — `interactive` (default) or `script`

**Interactive is ALWAYS the default.** Route to script generation (Step 2B) ONLY when BOTH conditions are met: (a) scale is explicitly >50 items or the user provides a batch input file, AND (b) the user explicitly asks for code, a script, a CSV export, or batch processing. Words like "dataset", "compare", "multi-source", or "2 sources" do NOT trigger script mode — run these interactively. **Script generation writes code that calls an existing agent** — it does not create new agents. If no agent exists yet, resolve that first (Step 3) before generating a script.

### Step 1P: Plan mode (rare — only when `needs-planning`)

1. **Clarify** — `AskUserQuestion` to resolve critical unknowns (max 2 questions). Focus on: what site(s), what data fields, what output format.
2. **Explore** — `nimble_agents_list` for each target (foreground, 1 call each). For unfamiliar domains, launch Discovery Task agents (Step 1D).
3. **Present plan** — gap analysis table:

| # | Site / Data Source | Agent | Status |
|---|-------------------|-------|--------|
| 1 | amazon.com products | amazon-product-details | Existing |
| 2 | walmart.com products | — | Generate |

4. **Execute** — Step 2 for existing agents, Step 3 for generations (as Task agents).

### Step 1D: Discovery (Task agent — for unfamiliar domains)

Launch when `nimble_agents_list` returns 0 matches and the target domain needs exploration. Runs as `Task(subagent_type="general-purpose", run_in_background=False)`. The foreground tells the user: *"Exploring {domain} to understand available data..."*

**Task prompt template:**

```
Explore {domain} for {user_intent}.

**MCP tool registry (call these as MCP tool invocations, NOT bash/curl):**
| Short name | Full MCP tool name |
|------------|--------------------|
| nimble_web_search | mcp__plugin_nimble_nimble-mcp-server__nimble_web_search |

**CRITICAL: Use MCP tool calls only. NEVER use bash, curl, wget, WebSearch, or WebFetch to call APIs or search the web. NEVER construct MCP endpoint URLs manually.**

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
Do NOT use WebSearch, WebFetch, bash curl, or any non-MCP search/fetch method.
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
```

Do NOT offer script generation as a next step unless the user explicitly mentions needing large-scale extraction (>50 items) or batch processing. Script generation is not a natural follow-up to interactive runs.

**Bulk (2–5 URLs):** Run per URL, aggregate results, handle individual failures without aborting. See **`references/batch-patterns.md`** > "Interactive batch extraction".

### 2B: Script generation (ONLY for large-scale, high-volume tasks)

**This step is ONLY reached when the user explicitly needs to process >50 items at scale or requests batch code/script generation.** Normal requests — even multi-source or "dataset" requests — are handled interactively via Step 2A. Writes a runnable script that calls an existing Nimble agent at scale via the SDK/REST API. This does NOT create new agents — the agent must already exist. Runs as a Task agent. The foreground infers language, launches the agent, and presents the generated script for confirmation.

**2B-1.** Infer language from project context (foreground, before launching):

| Project file | Language |
|-------------|----------|
| `pyproject.toml`, `requirements.txt`, `*.py` | Python |
| `package.json`, `tsconfig.json` | TypeScript/Node |
| `go.mod` | Go (REST API) |
| None of the above | Default to Python |

**2B-2.** Launch script generation Task agent: `Task(subagent_type="general-purpose", run_in_background=False)`.

**Task prompt template:**

```
Write a {language} script that calls existing Nimble agent(s) at scale via SDK/REST API.

**MCP tool registry (call these as MCP tool invocations, NOT bash/curl):**
| Short name | Full MCP tool name |
|------------|--------------------|
| nimble_agents_get | mcp__plugin_nimble_nimble-mcp-server__nimble_agents_get |

**CRITICAL: Use MCP tool calls only. NEVER use bash, curl, wget, WebSearch, or WebFetch to call APIs or search the web. NEVER construct MCP endpoint URLs manually.**

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
Do NOT call nimble_agents_generate, nimble_agents_update_from_agent, nimble_agents_update_session, or nimble_agents_publish.
Do NOT use WebSearch, WebFetch, bash curl, or any non-MCP search/fetch method.
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

## Step 3: Update existing agent or create new (on the Nimble platform)

Updates an existing agent (preferred) or creates a new one on Nimble's platform. **Default to update** when a close-match agent was found in Step 1 — pass the existing agent name to the Task agent so it uses `nimble_agents_update_from_agent` instead of `nimble_agents_generate`. Only create a new agent when Step 1 returned 0 matches. This is NOT code/script generation — it creates/modifies an extraction definition callable via Step 2A or 2B. ALWAYS runs as a Task agent (`run_in_background=False`).

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

### 3-3. Launch Task agent

Set `refine_validate` to the user's choice. Launch `Task(subagent_type="general-purpose", run_in_background=False, max_turns=50)` using the prompt template from **`references/generate-update-and-publish.md`** (includes MCP tool registry, lifecycle phases, and all rules). Tell the user: "Agent generation started. I'll report results when complete."

The Task agent executes a closed-loop lifecycle: Discovery → Create/Update → Poll → Validate → Publish → Report. On failure, it auto-triggers an update loop (max 2 cycles, 15-minute wall-clock timeout). See the reference file for complete details.

### 3-4. Present report

When the Task agent completes, present the report. On success, route to Step 2A or 2B. On failure after max cycles, offer:

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

**For large-scale codegen tasks (Step 2B) only** — consult these when writing scripts that call Nimble APIs at scale. Do NOT load these for interactive runs (Step 2A) or agent creation (Step 3):

1. **`references/sdk-patterns.md`** — correct SDK patterns and common mistakes.
2. **https://docs.nimbleway.com/llms-full.txt** — full prose docs.
3. **https://docs.nimbleway.com/openapi.json** — API contract.
4. **Context7** (if available) — query `nimbleway`.

For interactive runs and agent creation, the MCP tool schemas from `nimble_agents_get` provide all the information needed.

## Error recovery

Consult **`references/error-recovery.md`** for handling patterns including persistent data source failures, ambiguous agent matches, and the full fallback hierarchy.

## Additional references

Load reference files **only during large-scale script generation (Step 2B)** or agent creation (Step 3). Do NOT load these for interactive runs (Step 2A) — MCP tool schemas are sufficient.

**For script generation (Step 2B) only:**
- **`references/sdk-patterns.md`** — Running agents, async endpoint, batch pipelines, incremental file writes.
- **`references/rest-api-patterns.md`** — REST API patterns for TypeScript, Node, curl, and other non-Python languages.
- **`references/batch-patterns.md`** — Multi-store comparison, normalization, interactive batch, codegen walkthrough.

**For agent creation/update (Step 3) only:**
- **`references/generate-update-and-publish.md`** — Full agent creation/update lifecycle: discovery, creation, polling, SDK validation (50 inputs, 80% threshold), publish, reporting, update loop.

**General (any step, load as needed):**
- **`references/agent-api-reference.md`** — MCP tools reference plus input parameter mapping.
- **`references/error-recovery.md`** — Error handling and recovery patterns.

## Guardrails

- **NEVER call `nimble_agents_generate`, `nimble_agents_update_from_agent`, `nimble_agents_update_session`, `nimble_agents_status`, or `nimble_agents_publish` in the foreground conversation.** These MUST run inside a `Task` agent. No exceptions — not even "just one quick call". Polling in the foreground floods context and wastes tokens.
- **Task agents MUST use `run_in_background=False`.** Background Task agents cannot access MCP tools ([known platform limitation](https://github.com/anthropics/claude-code/issues/13254)). When this is resolved upstream, switch back to `run_in_background=True`.
- **All web search MUST use `nimble_web_search` (MCP tool).** NEVER use built-in `WebSearch`, `WebFetch`, `curl`, `wget`, or any other search/fetch method — in the foreground or in Task agents. The full tool name is `mcp__plugin_nimble_nimble-mcp-server__nimble_web_search`.
- **NEVER use bash/curl to call MCP endpoints.** Task agents must call MCP tools by their tool names, not by constructing HTTP requests to MCP server URLs. If an MCP tool is not available, report the error — do not attempt to work around it via bash.
- **Every Task agent prompt MUST include the MCP tool registry block** from [Delegation model > MCP tool registry](#mcp-tool-registry). This tells the subagent the exact tool names to use. Without it, the subagent may fail to find MCP tools and fall back to bash.
- **Foreground MCP tools are limited to:** `nimble_agents_list`, `nimble_agents_get`, `nimble_agents_run`. Nothing else.
- **Never** use `nimble_find_search_agent`, `nimble_run_search_agent`, or any WSA template tools.
- **Update first, generate only as last resort.** When a close-match agent exists, always use `nimble_agents_update_from_agent` to refine it — never generate a new agent for the same domain. Use `nimble_agents_generate` ONLY when `nimble_agents_list` returned 0 results. For the update state machine: call `nimble_agents_update_from_agent` once to create/resolve the update session, then use `nimble_agents_update_session` for every follow-up with the same `session_id`. Never create a second session for the same refinement thread.
- **Hard 429 rule.** If `nimble_agents_generate` or `nimble_agents_update_from_agent` returns 429/quota errors, stop and report quota exhaustion. Do not call any update tool as fallback and do not create new sessions.
- Published agents are automatically forked when updated. UBCT-based agents cannot be updated — generate a new one instead.
- **Never load external docs (`llms-full.txt`, `openapi.json`), SDK references, or batch pattern files for interactive runs (Step 2A).** These are exclusively for large-scale script generation (Step 2B). For interactive runs, the MCP tool schemas from `nimble_agents_get` are sufficient. Loading unnecessary docs wastes context and slows execution.
- Present tool call results in markdown tables. Never show raw JSON.

---
name: nimble-agents
argument-hint: "[query or URL]"
description: >
  Finds, generates, and runs Nimble agents to extract structured data from
  websites. Produces either interactive results or ready-to-run scripts with
  CSV/JSON output. This skill should be used when the user asks to "extract data
  from a website", "scrape product details", "run a Nimble agent", "generate a
  web scraper", "generate a data extraction agent", "get product prices",
  "compare prices across stores", "extract search results", "scrape Amazon",
  "scrape Walmart", "extract product info", "web data extraction",
  "find a Nimble template", "bulk extract", "batch scrape", or "pull product
  listings".
allowed-tools:
  - mcp__nimble-mcp-server__nimble_agents_list
  - mcp__nimble-mcp-server__nimble_agents_get
  - mcp__nimble-mcp-server__nimble_agents_generate
  - mcp__nimble-mcp-server__nimble_agents_run
  - mcp__nimble-mcp-server__nimble_agents_publish
  - mcp__nimble-mcp-server__nimble_web_search
disable-model-invocation: false
license: MIT
metadata:
  version: "0.3.0"
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

- **Infer, don't ask.** Only use `AskUserQuestion` when there is genuine ambiguity that cannot be resolved from context.
- **AskUserQuestion for all choices.** Never present choices as plain numbered lists in markdown. AskUserQuestion provides interactive arrow-key selection. Constraints: 2–4 options, header max 12 chars, label 1–5 words. "Other" is added automatically. Recommended option goes first with "(Recommended)" appended.
- **Keep output concise.** Present results and options. No commentary about implementation choices, architecture, or performance.
- **Schema before run — always.** Call `nimble_agents_get` before `nimble_agents_run` to understand input/output fields. **This applies every time an agent is run, including when pivoting to a fallback agent after errors.** When switching agents, always repeat the full cycle: `nimble_agents_get` → present schema → confirm → run. Present input parameters (name, required, type, example) and key output fields in a markdown table so the user knows what to expect.
- **Verify response shape before codegen.** Check the `skills` (output fields) and `entity_type` from `nimble_agents_get` to determine the correct REST API response nesting. See **`references/agent-api-reference.md`** > "Response shape inference" and **`references/sdk-patterns.md`** > "Response structure verification".
- **Agent names** vary by layer: MCP tools use hyphens (`amazon-product-details`), REST/SDK examples use underscores (`amazon_pdp`). Both formats are valid — use whichever the API returns.
- **Web search for disambiguation.** When the target domain is unfamiliar or no agent clearly matches, use `nimble_web_search` to explore what data exists before committing to an agent approach. Also use it as a fallback when dedicated agents are persistently failing — see **`references/error-recovery.md`** > "Persistent data source failures".

## Response shapes

| Layer | Path | Shape | When used |
|-------|------|-------|-----------|
| MCP tool (`nimble_agents_run`) | `data.results` | Always array | Interactive path (Steps 3A, 3C) |
| REST API — ecommerce SERP | `data.parsing` | `list` (array of records) | Codegen path (Step 3B) |
| REST API — non-ecommerce SERP | `data.parsing.entities.{EntityType}` | `dict` with nested arrays | Codegen: `google_search`, `google_maps_search`, etc. |
| REST API — PDP | `data.parsing` | `dict` (flat fields) | Codegen path (Step 3B) |

Always check `typeof`/`isinstance` before iterating REST responses. **Before generating code**, inspect the `skills` output from `nimble_agents_get` to determine which shape applies — see **`references/sdk-patterns.md`** > "Response structure verification".

## Step 1: Parse intent and route

From `$ARGUMENTS`, extract all signals at once:

**What to detect:**

| Signal | Values | How to detect |
|--------|--------|---------------|
| **Execution mode** | `interactive` or `codegen` | See routing table below |
| **Scale** | `small` (≤50 results) or `large` (>50) | Numbers, "all", "top 1000", "bulk", "batch" |
| **Output format** | `display`, `csv`, `json`, `file` | "CSV", "JSON file", "save to", "spreadsheet", "export" |
| **Stores** | list of store names | "amazon", "walmart", "across X and Y", "compare", "both" |
| **Target type** | `search` (keyword) or `detail` (URL/ID) | Keywords → SERP agent; specific URLs/ASINs → PDP agent |
| **Language** | inferred from project | Check codebase (see language inference below) |

**Route to codegen when ANY of these are true:**
- Scale > ~50 results (pagination needed)
- Output format is file-based (CSV, JSON file, etc.)
- Multi-store comparison with merging
- Batch input (file of URLs/IDs)
- User explicitly asks for a script/code

**Otherwise route to interactive** (MCP tool calls).

### Language inference (for codegen path)

Check the project for language signals — do NOT ask unless ambiguous:

| Project file | Inferred language |
|-------------|-------------------|
| `pyproject.toml`, `requirements.txt`, `setup.py`, `*.py` files | Python |
| `package.json`, `tsconfig.json` | TypeScript/Node |
| `go.mod` | Go (REST API) |
| `Gemfile`, `*.rb` files | Ruby (REST API) |
| `Cargo.toml` | Rust (REST API) |
| None of the above | Default to Python |

**Only ask via AskUserQuestion if** both Python and Node project files exist simultaneously, or the user's codebase gives conflicting signals.

### Multi-agent detection

If the request mentions multiple stores ("compare across Amazon and Walmart", "both", "vs"), plan multi-agent orchestration upfront — search for agents for ALL stores in parallel, not sequentially.

## Step 2: Agent discovery

Call `nimble_agents_list` with **short, general keywords** (1–2 words). For multi-store requests, search for each store in parallel. If `count` exceeds `curr_count` in the response, paginate using `skip` to see more agents. Present results 5 at a time.

**How to present results depends on ambiguity:**

| Situation | Action |
|-----------|--------|
| Exactly 1 matching agent | Narrate: "Found `agent_name` — matches your request." Auto-advance. |
| 2+ plausible matches | Show table + `AskUserQuestion` with top 2 agents + "Generate new agent" |
| 0 matches | Use `nimble_web_search` to explore the target domain first (see `error-recovery.md` > "Ambiguous agent match"), then either use `google_search` with `site:` scoping or auto-advance to generate path. |
| Codegen path + clear match | Narrate agent choice silently. No need to ask — user will review the code. |

When presenting search results, show a markdown table of top 5, then use AskUserQuestion only if the choice between agents is genuinely ambiguous.

## Step 3A: Interactive path (small scale, display output)

**3A-1.** Call `nimble_agents_get` on the chosen agent. Present the schema clearly in markdown tables:
- **Input parameters:** Show each `input_properties` entry with name, required (yes/no), type, description, and example value.
- **Output fields:** Show key fields from the `skills` dict with name and type, so the user knows what data to expect.

See **`references/input-schema-guide.md`** for the full `input_properties` format and mapping rules.

**3A-2.** Use `AskUserQuestion` to confirm before running:

```
question: "Run this agent?"
header: "Confirm"
options:
  - label: "Run agent (Recommended)"
    description: "Execute {agent_name} with inferred parameters"
  - label: "Generate new agent"
    description: "Create a custom agent instead"
```

Do NOT call `nimble_agents_run` in the same response.

**3A-3.** After confirmation, call `nimble_agents_run`. Present results as markdown table. Use `AskUserQuestion` for next steps:

```
question: "What next?"
header: "Next step"
options:
  - label: "Done"
    description: "Finish with these results"
  - label: "Run again"
    description: "Re-run with different parameters"
  - label: "Get code"
    description: "Generate a script to reproduce this"
```

**Auto-advance to final summary** if the original request is fully satisfied without needing follow-up.

## Step 3B: Codegen path (large scale, file output, multi-store)

**3B-1.** Call `nimble_agents_get` on chosen agent(s). Inspect both `input_properties` and `skills` (output fields). Use `skills` to determine the correct response parsing structure — see "Response shapes" table above. Do NOT present schemas interactively — use them to inform code generation.

**3B-2.** Infer language from project context (see language inference table above).

**3B-3.** Generate a ready-to-run script. Consult **`references/sdk-patterns.md`** for correct patterns.

Script requirements:
- For the inferred language, use the appropriate SDK or REST API
- Handle pagination for large result sets
- Include progress reporting
- For multi-store: normalize fields per **`references/normalization-guide.md`**
- For CSV/file output: write results to the requested format
- For deduplication: deduplicate by (store, product_name) or equivalent — see normalization guide

**Python:** Use `nimble_python` SDK with `uv run` inline metadata. Choose the right template based on job count — see the routing table in **`references/sdk-patterns.md`** (section: "When to use async vs sync").

**TypeScript/Node, curl, other languages:** Use the REST API directly. See **`references/rest-api-patterns.md`** for patterns and examples.

**3B-4.** Present the generated code and use `AskUserQuestion`:

```
question: "Run this script now?"
header: "Execute"
options:
  - label: "Run now (Recommended)"
    description: "Execute the script and show results"
  - label: "Save only"
    description: "Save the file without running"
```

## Step 3C: Generate path (no existing agent matches)

**3C-1.** Create a stable `session_id` (UUID v4, reuse for all generate/publish calls).

**3C-2.** Call `nimble_agents_generate` with a clear prompt. If the user specifies exact output fields (e.g., "extract name, price, and rating"), include an `output_schema` in the generate call to guide the agent's extraction. Handle status:
- `"waiting"` — present follow-up questions via `AskUserQuestion`, call again with same `session_id`.
- `"processing"` — follow the **polling protocol** below.
- `"complete"` — auto-advance to publish and run/codegen.
- `"error"` — present error, offer retry or search alternatives.

### Polling protocol (`processing` status)

Agent generation takes 2–10 minutes. The MCP server handles waiting internally (up to ~50 s per call), so **no `sleep` is needed between calls**.

1. Tell the user: "Agent generation started — this typically takes 2–5 minutes (up to 10)."
2. Call `nimble_agents_generate` with **only `session_id`** (omit `prompt`). The server waits internally and returns when either the status changes or ~50 seconds elapse.
3. If still `processing`, narrate "Still generating... (N/12)" and call again immediately.
4. **Max 12 polls** (~10 minutes total). After 12: inform user per `references/error-recovery.md`.

**Rules:**
- **NEVER send `prompt` when polling.** Not even `""`. Any prompt re-invokes the generation backend instead of checking status.
- **NEVER use `Bash("sleep ...")` between polls.** The server handles waiting internally — adding sleep doubles the wait time unnecessarily.

**3C-3.** Route to Step 3A (interactive) or Step 3B (codegen) to run the agent first based on the execution mode determined in Step 1.

**3C-4.** After a successful run, use `AskUserQuestion` to offer publishing. If confirmed, call `nimble_agents_publish` with same `session_id`. If 409, already published — proceed.

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

When encountering errors or need grounding, consult in order:

1. **`references/sdk-patterns.md`** — correct SDK patterns and common mistakes.
2. **https://docs.nimbleway.com/llms-full.txt** — full prose docs.
3. **https://docs.nimbleway.com/openapi.json** — API contract.
4. **Context7** (if available) — query `nimbleway`.

## Error recovery

Consult **`references/error-recovery.md`** for error handling patterns, including:
- **Persistent data source failures** — when to stop retrying and pivot to `google_search` + `site:` or `nimble_web_search`.
- **Ambiguous agent match** — using `nimble_web_search` to explore unfamiliar domains before generating custom agents.

## Additional references

Load reference files proactively during code generation. For the codegen path, always consult `references/sdk-patterns.md` (Python) or `references/rest-api-patterns.md` (other languages) before generating code. For error recovery, consult `references/error-recovery.md`. Load other references as needed.

- **`references/sdk-patterns.md`** — Python SDK: running agents, async endpoint, batch pipelines.
- **`references/input-schema-guide.md`** — Mapping agent input schemas to params.
- **`references/agent-api-reference.md`** — Reference for all five MCP tools.
- **`references/error-recovery.md`** — Error handling and recovery patterns.
- **`references/normalization-guide.md`** — Multi-agent field mapping, unified schema, deduplication.
- **`examples/find-and-run-agent.md`** — Existing-agent path walkthrough.
- **`examples/generate-and-publish.md`** — Generate fallback walkthrough.
- **`examples/bulk-extraction.md`** — Multi-URL batch extraction walkthrough.
- **`references/rest-api-patterns.md`** — REST API patterns for TypeScript, Node, curl, and other non-Python languages.
- **`examples/codegen-walkthrough.md`** — Codegen path walkthrough: multi-store comparison with CSV output.

## Guardrails

- Agent workflows only — list, get, generate, run, publish. No scheduling or monitoring.
- To modify an existing agent, generate a new one with an improved prompt — there is no update operation.
- **Never ask for information already in the request or inferable from context.**
- Present tool call results in markdown tables. Never show raw JSON.
- Adapt table columns to match actual data returned.

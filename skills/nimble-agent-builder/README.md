# nimble-agent-builder

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Find, generate, update, and run structured-data agents on the Nimble platform. Discover existing agents for 50+ sites, update them for new fields, or create custom ones from scratch — all via natural language.

## What it does

| Task                       | Example                                                |
| -------------------------- | ------------------------------------------------------ |
| Discover an existing agent | "Find an agent for Amazon product pages"               |
| Run an agent interactively | "Get data for ASIN B08N5WRWNW"                         |
| Update an agent            | "Add customer reviews field to the Amazon agent"       |
| Generate a new agent       | "Build an agent for Etsy product listings"             |
| Generate a batch script    | "Write a Python script to extract 500 Zillow listings" |

## Requirements

- **Nimble API key** — [online.nimbleway.com/signup](https://online.nimbleway.com/signup)
- **Nimble CLI** — for agent discovery and running (`nimble agent list/get/run`)
- **Nimble MCP server** connected to your AI tool — for agent generation, update, and publish

## Setup

See [Installation in the root README](../../README.md#installation) for CLI install and API key setup.

### Connect the Nimble MCP server

#### Claude Code

```bash
claude mcp add --transport http nimble-mcp-server https://mcp.nimbleway.com/mcp \
  --header "Authorization: Bearer ${NIMBLE_API_KEY}"
```

> **Restart Claude Code after running this** — MCP servers added mid-session aren't available until the next launch.

#### Cursor / VS Code (Copilot / Continue)

```json
{
  "nimble-mcp-server": {
    "command": "npx",
    "args": [
      "-y",
      "mcp-remote@latest",
      "https://mcp.nimbleway.com/mcp",
      "--header",
      "Authorization:Bearer YOUR_API_KEY"
    ]
  }
}
```

## How it works

The skill has two tool groups depending on what you need:

**`nimble agent` (CLI) — search and run existing agents**

| Action | What happens |
| --- | --- |
| Search for an agent | `nimble agent list --limit 100` → filtered by domain |
| Inspect its schema | `nimble agent get --template-name <name>` → shows fields + params |
| Run it | `nimble agent run --agent <name> --params '{...}'` → returns structured data |

**`nimble MCP` — create, refine, and publish agents**

| Action | What happens |
| --- | --- |
| No existing agent found | `nimble_agents_generate` → builds a new agent for the target site |
| Existing agent needs changes | `nimble_agents_update_from_agent` or `nimble_agents_update_session` → refines in place |
| Output validated | `nimble_agents_publish` → agent becomes available in `nimble agent list` |
| Output invalid | loops back to refine until valid |

Once published, the agent is immediately available to `nimble agent run` — and to **nimble-web-expert**'s agent check.

**Key rules:**

- Always search for an existing agent before generating — update a close match rather than building from scratch
- Mutation tools (`generate`, `update`, `publish`) always run inside Task agents — never in the foreground
- All Task agents use `run_in_background=False` to preserve MCP access
- For one-off fetches or web searches, use **nimble-web-expert** instead

## Reference files

| File                                        | Purpose                                                    |
| ------------------------------------------- | ---------------------------------------------------------- |
| `references/agent-api-reference.md`         | MCP tool reference, input parameter mapping                |
| `references/sdk-patterns.md`                | Python SDK patterns, async endpoint, batch pipelines       |
| `references/rest-api-patterns.md`           | REST API for TypeScript, Node, curl                        |
| `references/batch-patterns.md`              | Multi-store comparison, normalization, codegen walkthrough |
| `references/generate-update-and-publish.md` | Full agent lifecycle: create → poll → validate → publish   |
| `references/error-recovery.md`              | Error handling, quota limits, fallback hierarchy           |

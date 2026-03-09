# Nimble Web Data Toolkit

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-0.8.0-green)](https://github.com/Nimbleway/agent-skills)

Extract-first scraping expert, URL discovery, web search, and structured data agents via the Nimble CLI. One plugin for Claude Code, Cursor, and Vercel Agent Skills.

## Skills

| Skill                                                    | Best for                                                                   | Trigger phrases                                                               |
| -------------------------------------------------------- | -------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| [**nimble-web-expert**](skills/nimble-web-expert/)       | Get data **now** — one-off fetches, real-time lookups, live research       | "fetch", "scrape", "search the web", "what does this page say"                |
| [**nimble-agent-builder**](skills/nimble-agent-builder/) | Build **reusable** extraction agents — scheduled, at-scale, API-accessible | "build an agent", "set up extraction", "extract at scale", "create a scraper" |

## How they work together

**nimble-web-expert** is for right now — fetch a URL, search the web, scrape a price, read a page. Give it any URL and it returns the data.

**nimble-agent-builder** is for recurring needs — build an extraction workflow once, then run it on hundreds of pages, on a schedule, or via API.

They connect naturally: web-expert runs agents built by agent-builder, and when a one-off lookup becomes something you need regularly, agent-builder turns it into a reusable pipeline. Agents published there appear automatically in web-expert.

The two skills form a **feedback loop**:

1. **web-expert runs agents** built by agent-builder — Step 0 picks them up automatically via `nimble agent list`
2. **web-expert feeds agent-builder** — when a one-off extraction becomes a recurring need, hand off to agent-builder
3. **agent-builder publishes back** — published agents immediately appear in web-expert's Step 0, completing the loop

| User says…                                 | Skill triggered      | What happens                                      |
| ------------------------------------------ | -------------------- | ------------------------------------------------- |
| "Get me the price of this product"         | nimble-web-expert    | Step 0 check → Tier 1–6 extraction → results      |
| "Build an agent for Amazon product pages"  | nimble-agent-builder | Find/generate/publish → agent in Step 0           |
| "Get ASIN B08N5WRWNW" (after agent exists) | nimble-web-expert    | Step 0 finds agent → `nimble agent run` → results |
| "Extract 500 Zillow listings weekly"       | nimble-agent-builder | Build agent → generate batch script → schedule    |

## Installation

### Prerequisites

1. **Nimble API Key** — [Sign up](https://online.nimbleway.com/signup) and get your key from Account Settings > API Keys.

2. **Nimble CLI** — Install the CLI:

   ```bash
   npm i -g @nimble-way/nimble-cli
   ```

3. Set the environment variable:
   ```bash
   export NIMBLE_API_KEY="your-api-key-here"
   ```
   Or add to `~/.claude/settings.json`:
   ```json
   { "env": { "NIMBLE_API_KEY": "your-api-key-here" } }
   ```

### Claude Code

**Option A: Plugin install (recommended)**

```bash
claude plugin install nimble@nimble-plugin-marketplace
```

Or load locally during development:

```bash
claude --plugin-dir /path/to/agent-skills
```

**Option B: MCP-only (no plugin)**

```bash
claude mcp add --transport http nimble-mcp-server https://mcp.nimbleway.com/mcp \
  --header "Authorization: Bearer ${NIMBLE_API_KEY}"
```

This gives you the 5 agent MCP tools but not the skills.

### Cursor

**Option A: Marketplace (once published)**

In Cursor chat:

```
/add-plugin nimble
```

**Option B: Local plugin directory**

Clone and point Cursor at it:

```bash
git clone https://github.com/Nimbleway/agent-skills.git
```

Open the `agent-skills` folder in Cursor. The plugin system reads:

- `.cursor-plugin/plugin.json` — plugin metadata
- `skills/` — both skills (auto-discovered)
- `rules/` — Cursor rules (auto-loaded)
- `mcp.json` — MCP server connection

**Option C: MCP-only (no plugin)**

Add to `.cursor/mcp.json` or `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "nimble-mcp-server": {
      "url": "https://mcp.nimbleway.com/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_API_KEY"
      }
    }
  }
}
```

### Vercel Agent Skills CLI

```bash
npx skills add Nimbleway/agent-skills
```

This installs both skills into your project. To verify:

```bash
npx skills add Nimbleway/agent-skills --list
```

> **Note:** The agents skill requires the Nimble MCP server. After installing via `npx skills`, you still need to connect the MCP server manually:
>
> ```bash
> claude mcp add --transport http nimble-mcp-server https://mcp.nimbleway.com/mcp \
>   --header "Authorization: Bearer ${NIMBLE_API_KEY}"
> ```

## How It Works

### Platform File Mapping

| Aspect        | Claude Code               | Cursor                            | Vercel `npx skills`   |
| ------------- | ------------------------- | --------------------------------- | --------------------- |
| Plugin config | `.claude-plugin/`         | `.cursor-plugin/`                 | N/A (reads `skills/`) |
| MCP config    | `.mcp.json` (flat format) | `mcp.json` (`mcpServers` wrapper) | Manual setup          |
| Rules         | N/A                       | `rules/*.mdc`                     | N/A                   |
| Skills        | `skills/` (shared)        | `skills/` (shared)                | `skills/` (shared)    |
| Install       | `claude --plugin-dir`     | `/add-plugin` or open folder      | `npx skills add`      |

All three platforms read the same `skills/` directory. Platform-specific files coexist without interference.

### MCP Tools

The agents skill uses these MCP tools (provided by the Nimble MCP server):

| Tool                     | Description                               |
| ------------------------ | ----------------------------------------- |
| `nimble_agents_list`     | Browse agents                             |
| `nimble_agents_get`      | Get agent details and schema              |
| `nimble_agents_generate` | Create custom agents via natural language |
| `nimble_agents_run`      | Execute agents                            |
| `nimble_agents_publish`  | Save generated agents for reuse           |

## Quick Start

### Web Expert (Search, Extract, Map, Crawl)

The `nimble-web-expert` skill wraps the Nimble CLI. Examples:

```bash
# Search the web
nimble search --query "React server components" --focus coding --deep-search=false

# Extract content from a URL
nimble extract --url "https://example.com/article"  --format markdown

# Map all URLs on a site
nimble map --url "https://docs.example.com" --limit 100

# Crawl a site section
nimble crawl run --url "https://docs.example.com" --include-path "/api" --limit 50
```

### Structured Extraction

Use the `nimble-agent-builder` skill for data extraction:

```
"Extract product details from this Amazon page"
"Get restaurant data from Yelp listings"
"Scrape pricing information from competitor websites"
```

The skill will search for existing agents, or generate a new one if needed.

## Development

### Directory Structure

```
agent-skills/
├── .claude-plugin/          # Claude Code plugin config
│   ├── plugin.json
│   └── marketplace.json
├── .cursor-plugin/          # Cursor plugin metadata
│   └── plugin.json
├── skills/                  # Shared by all platforms
│   ├── nimble-web-expert/
│   │   ├── SKILL.md
│   │   ├── references/
│   │   │   ├── parsing-schema.md
│   │   │   ├── browser-actions.md
│   │   │   ├── network-capture.md
│   │   │   ├── search-focus-modes.md
│   │   │   └── error-handling.md
│   │   └── rules/
│   │       ├── nimble-web-expert.mdc
│   │       └── output.md
│   └── nimble-agent-builder/
│       ├── SKILL.md
│       └── references/
├── rules/
│   └── nimble-tools.mdc    # Cursor rule (auto-loaded by plugin)
├── .mcp.json                # Claude Code plugin MCP config
├── mcp.json                 # Cursor plugin MCP config
└── README.md
```

## Environment Variables

| Variable               | Required | Description                     |
| ---------------------- | -------- | ------------------------------- |
| `NIMBLE_API_KEY`       | Yes      | Your Nimble API key             |
| `NIMBLE_BASE_URL`      | No       | Custom API endpoint             |
| `NIMBLE_MCP_LOCAL_URL` | No       | Local MCP server URL (dev only) |

## Support

- **Documentation**: [docs.nimbleway.com](https://docs.nimbleway.com)
- **MCP Server**: [github.com/Nimbleway/nimble-mcp-server](https://github.com/Nimbleway/nimble-mcp-server)
- **Issues**: [github.com/Nimbleway/agent-skills/issues](https://github.com/Nimbleway/agent-skills/issues)
- **Email**: support@nimbleway.com

## License

MIT License — see [LICENSE](LICENSE) for details.

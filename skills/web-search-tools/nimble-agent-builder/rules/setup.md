---
description: One-time setup for Nimble Agent Builder. Load when neither CLI nor MCP is available.
alwaysApply: false
---

# Nimble Agent Builder Setup

## CLI (preferred)

The Nimble CLI supports all operations including agent generation, polling, and publishing.

```bash
npm i -g @nimble-way/nimble-cli
export NIMBLE_API_KEY="your-api-key-here"
```

## MCP server (fallback)

If the CLI cannot be installed, the MCP server provides equivalent functionality.

**Recommended: install the Nimble plugin.** When installed via `/plugin install nimble`, the MCP server is auto-registered over native HTTP with OAuth — run `/mcp` and authenticate in your browser. No API key header required.

**Manual install (no plugin):**

```bash
claude mcp add --transport http nimble-mcp-server https://mcp.nimbleway.com/mcp \
  --header "Authorization: Bearer ${NIMBLE_API_KEY}"
```

**Restart Claude Code after running this** — MCP servers added mid-session are not available until the next launch.

**VS Code / Cursor (Copilot / Continue):** Add to your MCP settings JSON:

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

For CLI install and API key setup, see `skills/nimble-web-expert/rules/setup.md`.

---
description: One-time setup for Nimble Agent Builder MCP server. Load when the MCP prerequisite check in SKILL.md fails.
alwaysApply: false
---

# Nimble Agent Builder Setup

## MCP server (required)

The MCP server is what makes agent generation, update, and publish possible. Without it, this skill can only run existing agents via CLI.

**Add with one command:**

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

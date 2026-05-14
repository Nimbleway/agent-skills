---
description: One-time setup for Nimble Agent Builder. Load when neither CLI nor MCP is available.
alwaysApply: false
---

# Nimble Agent Builder Setup

The skill works via two transports — pick whichever fits the host:

| Host | Best path |
|---|---|
| Any Claude product (Claude Code, Claude Cowork, claude.ai) | **Plugin install** — `/plugin install nimble`. Auto-registers MCP as a Connector. OAuth on first use. |
| Codex CLI / other terminal-only agents | **CLI install** — `npm i -g @nimble-way/nimble-cli` + API key. |
| Cursor / VS Code / other MCP clients | **Manual `mcp.json`** snippet. |

## 1. Plugin install — Claude products (recommended)

```
/plugin install nimble
```

The Nimble plugin's `.mcp.json` auto-registers a Connector pointing at
`https://mcp.nimbleway.com/mcp` over native HTTP. First tool call triggers
the OAuth flow in your browser — no API key, no header to manage.

Verify it landed:

```bash
claude mcp list | grep nimble
```

Expect: `plugin:nimble:nimble: https://mcp.nimbleway.com/mcp (HTTP) - ! Needs authentication`
(or `✓ Connected` after you authenticate via `/mcp`).

## 2. CLI install — terminal-only environments

When `/plugin install` isn't available but the user has shell access:

```bash
npm i -g @nimble-way/nimble-cli
export NIMBLE_API_KEY="your-api-key-here"
nimble --version
```

For the full setup flow (API-key generation, permanent storage in `~/.claude/settings.json`,
Docs MCP), see `skills/web-search-tools/nimble-fetch/rules/setup.md`.

## 3. Manual `mcp.json` — Cursor / VS Code / other MCP clients

Paste into the host's MCP settings (`.cursor/mcp.json` or equivalent):

```json
{
  "mcpServers": {
    "nimble": {
      "type": "http",
      "url": "https://mcp.nimbleway.com/mcp"
    }
  }
}
```

First tool call triggers OAuth. If the host doesn't speak native HTTP MCP yet,
fall back to the stdio shim:

```json
{
  "mcpServers": {
    "nimble": {
      "command": "npx",
      "args": [
        "-y", "mcp-remote@latest",
        "https://mcp.nimbleway.com/mcp",
        "--header", "Authorization:Bearer YOUR_API_KEY"
      ]
    }
  }
}
```

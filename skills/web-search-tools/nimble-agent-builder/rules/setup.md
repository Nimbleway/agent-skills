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

### Plugin installed but connector not connected (Cowork / claude.ai)

The most common Cowork / claude.ai state: the plugin is installed
(`mcp__plugin_nimble_nimble__*` tools are listed) but its connector isn't
connected, so calls fail. **Verify before doing any work** — run one read-only
`nimble_agents_list` probe: success = connected; an auth/not-connected error or a
response containing an OAuth authorization URL = not connected.

When not connected, tell the user verbatim and **stop** — never fall back to
WebFetch, WebSearch, curl, or any other tool:

> Your Nimble plugin is installed, but its connector isn't connected yet. To connect it:
>
> 1. Open **Customize → Connectors**
> 2. Find **Nimble** and click **Connect**
> 3. Complete the login in your browser. **No Nimble account?** You can create one
>    right there during login.
> 4. Once it shows **Connected**, re-run your request.

**If a tool returns an OAuth "Authorize" link instead of data**, present the link
exactly as given and stop. Do **not** invent a completion step ("paste the URL
back", "I'll complete the connection") — no such step exists — and do **not**
claim the tools will activate and then call them in the same turn. Wait for the
user to authorize, then retry.

## 2. CLI install — terminal-only environments

When `/plugin install` isn't available but the user has shell access:

```bash
npm i -g @nimble-way/nimble-cli
export NIMBLE_API_KEY="your-api-key-here"
nimble --version
```

For the full setup flow (API-key generation, permanent storage in `~/.claude/settings.json`,
Docs MCP), see `skills/web-search-tools/nimble-web-expert/rules/setup.md`.

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

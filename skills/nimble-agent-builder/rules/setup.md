---
description: One-time setup instructions for Nimble Agent Builder — MCP server, CLI, and API key. Load this only when prerequisites in SKILL.md fail.
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

---

## Nimble CLI (required for list / get / run / search)

```bash
nimble --version && echo "CLI ready"
```

If not found:

```bash
npm i -g @nimble-way/nimble-cli
nimble --version
```

---

## API key setup

**Step 1 — Open the Nimble dashboard:**

```bash
open -a "Google Chrome" "https://online.nimbleway.com/overview" 2>/dev/null || open "https://online.nimbleway.com/overview"
```

Go to **Overview → API Token**, copy your token.

**Step 2 — Save permanently + activate now:**

Replace `<TOKEN>` with your copied token:

```bash
export NIMBLE_API_KEY="<TOKEN>"
python3 -c "
import json, pathlib
key = '<TOKEN>'
p = pathlib.Path.home() / '.claude/settings.json'
d = json.loads(p.read_text()) if p.exists() else {}
d.setdefault('env', {})['NIMBLE_API_KEY'] = key
p.write_text(json.dumps(d, indent=2))
print('✓ Saved to ~/.claude/settings.json')
"
```

Claude Code auto-injects `NIMBLE_API_KEY` from `~/.claude/settings.json` on every session start — no re-export needed.

**Step 3 — Add MCP server and restart:**

```bash
claude mcp add --transport http nimble-mcp-server https://mcp.nimbleway.com/mcp \
  --header "Authorization: Bearer ${NIMBLE_API_KEY}"
```

Restart Claude Code. The startup check in SKILL.md will confirm connection.

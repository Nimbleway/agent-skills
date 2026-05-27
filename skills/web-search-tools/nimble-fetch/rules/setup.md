---
description: One-time setup instructions for Nimble — plugin install (Claude products), CLI install (terminal agents), or manual MCP config (Cursor/VS Code). Load this only when the quick check in SKILL.md fails.
alwaysApply: false
---

# Nimble Setup

Pick the path that matches your host:

| Host | Best path |
|---|---|
| Any Claude product (Claude Code, Claude Cowork, claude.ai) | **Plugin install** — `/plugin install nimble`. Auto-registers MCP as a Connector. OAuth handles auth. **§1 below.** |
| Codex CLI / other terminal-only agents | **CLI install** — `npm i -g @nimble-way/nimble-cli` + API key. **§2 below.** |
| Cursor / VS Code / other MCP clients | **Manual `mcp.json`** snippet. **§3 below.** |

---

## 1. Plugin install (Claude products — recommended)

```
/plugin install nimble
```

The Nimble plugin includes a `.mcp.json` that auto-registers as a Connector
pointing at `https://mcp.nimbleway.com/mcp` over native HTTP with OAuth. After
install, run `/mcp` once to authenticate in your browser — no API key needed.

In claude.ai / Claude Cowork, the connector appears under
`Customize → Connectors` as **Nimble** — click **Connect** and complete the
browser login to activate it (see the not-connected section below).

Verify:

```bash
claude mcp list | grep nimble
```

Expect: `plugin:nimble:nimble: https://mcp.nimbleway.com/mcp (HTTP) - ✓ Connected`
once authenticated (or `! Needs authentication` until you run `/mcp`).

### Plugin installed but connector not connected (Cowork / claude.ai)

The most common Cowork / claude.ai state: the plugin is installed
(`mcp__plugin_nimble_nimble__*` tools are listed) but its connector isn't
connected, so live data calls fail. **Verify before doing any work** — run one
read-only `nimble_agents_list` probe: success = connected; an auth/not-connected
error or a response containing an OAuth authorization URL = not connected.

When not connected, tell the user verbatim and **stop** — never fall back to
WebFetch, WebSearch, curl, or any other tool:

> Your Nimble plugin is installed, but its connector isn't connected yet — that's
> why I can't fetch live data. To connect it:
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
user to authorize, then retry (or run one `nimble_agents_list` probe to confirm).

---

## 2. CLI install (Codex / terminal-only environments)

### One-time init (run once per machine)

Saves the API key to `~/.claude/settings.json` so Claude Code auto-injects it every session — no exports needed.

```bash
python3 -c "
import json, pathlib, subprocess, os

p = pathlib.Path.home() / '.claude/settings.json'
d = json.loads(p.read_text()) if p.exists() else {}
env = d.setdefault('env', {})

# Verify nimble is installed
try:
    r = subprocess.run(['nimble', '--version'], capture_output=True, text=True, timeout=5)
    if r.returncode == 0:
        print('✓ nimble: ' + r.stdout.strip())
    else:
        raise Exception('non-zero exit')
except:
    print('✗ nimble not found — install it first:')
    print('    npm i -g @nimble-way/nimble-cli')
    exit(1)

# Save API key
key = env.get('NIMBLE_API_KEY') or os.environ.get('NIMBLE_API_KEY', '')
if key and not env.get('NIMBLE_API_KEY'):
    env['NIMBLE_API_KEY'] = key
    print('✓ Saved NIMBLE_API_KEY to ~/.claude/settings.json')
print('NIMBLE_API_KEY: ' + ('set' if key else 'MISSING — see API key setup below'))
p.write_text(json.dumps(d, indent=2))
if key:
    print()
    print('✓ Init complete. Restart Claude Code to activate.')
"
```

**After running init → restart Claude Code.** The key is auto-injected from that point on.

---

## Install nimble CLI

```bash
npm i -g @nimble-way/nimble-cli
```

Then re-run the init script above.

---

## Set up API key

**Step 1 — Open the Nimble dashboard:**

```bash
open -a "Google Chrome" "https://online.nimbleway.com/overview" 2>/dev/null || open "https://online.nimbleway.com/overview"
```

Go to **Overview → API Token**, copy your token, and paste it when prompted.

**Step 2 — Save permanently + activate now:**

Replace `<TOKEN>` with the pasted value:

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

⚠️ **After this point: never prepend `export NIMBLE_API_KEY=...` to any subsequent command.** The key is in the environment. Just run `nimble ...` directly.

---

## 3. Manual `mcp.json` (Cursor / VS Code / other MCP clients)

Paste into the host's MCP settings (e.g., `.cursor/mcp.json`):

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

First tool call triggers OAuth in your browser. If the host doesn't speak
native HTTP MCP yet, fall back to the stdio shim with an API-key header:

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

---

## Nimble Docs MCP (optional but recommended)

Gives Claude instant access to the full Nimble documentation — CLI flags, agent schemas, API reference.

**Add with one command:**

```bash
claude mcp add --transport http nimble-docs https://docs.nimbleway.com/mcp
```

Restart Claude Code to activate.

**Fallback — extract docs directly if MCP is unavailable:**

```bash
# Compact overview
nimble --transform "data.markdown" extract \
  --url "https://docs.nimbleway.com/llms.txt" --format markdown

# Full documentation
nimble --transform "data.markdown" extract \
  --url "https://docs.nimbleway.com/llms-full.txt" --format markdown > .nimble/nimble-docs-full.md
head -200 .nimble/nimble-docs-full.md
```

If bash is also unavailable, use `WebFetch` on `https://docs.nimbleway.com/llms.txt`.

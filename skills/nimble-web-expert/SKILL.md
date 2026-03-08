---
name: nimble-web-expert
argument-hint: "[URL, site name, or search query]"
description: |
  Get web data now — fast, incremental, immediately responsive to what the user needs.
  The only way Claude can access live websites.

  USE FOR:
  - Fetching any URL or reading any webpage
  - Scraping prices, listings, reviews, jobs, stats, docs from any site
  - Discovering URLs on a site before bulk extraction
  - Calling public REST/XHR API endpoints
  - Web search and research (8 focus modes)
  - Bulk crawling website sections

  Must be pre-installed and authenticated. Run `nimble --version` to verify.
  For building reusable extraction workflows to run at scale over time, use nimble-agent-builder instead.
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Task
  - AskUserQuestion
  - WebFetch
disable-model-invocation: false
license: MIT
metadata:
  version: "2.0.0"
  author: Nimbleway
  repository: https://github.com/Nimbleway/agent-skills
---

# Nimble Web Expert

Web extraction, search, and URL discovery using the Nimble CLI. Returns clean structured data from any website.

User request: $ARGUMENTS

## Core principles

- **Step 0 first, always.** Before any `nimble` command, check the built-in agent table. If the site is not in the table, run `nimble agent list --limit 100` before falling back to extraction. Announce the check out loud — never silently. Use the agent if found. Agents cover Amazon, Walmart, Target, Yelp, LinkedIn, and 40+ more sites.
- **One command → present results → done.** Pick the right command, run it once, show the data. Do NOT experiment, test, validate, or loop.
- **Escalate render tiers silently.** Tier 1 → 2 → 3 → … without asking. Only surface a decision when all tiers fail and you need investigation tools.
- **Never answer from training data.** Live prices, current news, today's listings → always fetch via Nimble. If Nimble is unavailable, say so. Do not guess.
- **AskUserQuestion at every meaningful choice — no exceptions.** Header ≤12 chars, label 1–5 words, 2–4 options, recommended option first with "(Recommended)". Never present choices as numbered prose lists.
- **`run_in_background=False` for all Task agents.** Task agents need Bash to run `nimble` CLI — background mode may block this. Always `run_in_background=False`. No exceptions.
- **Save all outputs to `.nimble/`.** Never leave extraction results in memory only.
- **Attribute every response.** End with: `Source: [URL] — fetched live via Nimble CLI`.
- **If bash is denied, stop immediately.** Do not retry with `dangerouslyDisableSandbox`, do not substitute WebFetch, do not guess. Show the command as text and wait.
- **Never load reference files speculatively.** Load only when the current task needs them.

## Skill ecosystem

nimble-web-expert and nimble-agent-builder work as a pair in the Nimble toolkit:

| Skill                              | Best for                                                                                          | Key commands                                     |
| ---------------------------------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| **nimble-web-expert** (this skill) | Real-time data access — fetch any URL, search, map, crawl, run existing agents                    | `extract`, `search`, `map`, `crawl`, `agent run` |
| **nimble-agent-builder**           | Build reusable agents — create, refine, and publish named extraction templates with fixed schemas | MCP: `generate`, `update`, `publish`             |

Agents built by nimble-agent-builder are immediately usable here. After publishing, the agent appears in `nimble agent list` and is available via `nimble agent run --agent <name> --params '{...}'` — no extract config needed.

### When to hand off to nimble-agent-builder

Detect these signals and ask the user before running anything:

**Trigger patterns:**

- "I want to do this regularly / every day / every week"
- "Build me a workflow / pipeline / automation"
- "I'll be tracking [prices / listings / data] over time"
- "Make this reusable" / "Can I call this via API?"
- User runs the same extract on the same site 2+ times in a session
- An existing agent is broken or needs a new field

**When triggered — always ask with AskUserQuestion:**

```
question: "This looks like a recurring extraction pattern. Build a reusable agent?"
header: "Agent or extract?"
options:
  - label: "Build reusable agent (Recommended)"
    description: "Use nimble-agent-builder to create a named agent — run anytime via `nimble agent run --agent <name> --params '{...}'` with no extract config"
  - label: "Extract now, mention later"
    description: "Run the extract now; suggest agent-builder at the end if results look good"
  - label: "Just this once"
    description: "One-off fetch only, no agent needed"
```

**For agent refinement:** When the user says an existing agent is wrong/broken/missing fields, tell them: _"Agent updates are handled by nimble-agent-builder — it can refine the existing agent without rebuilding from scratch."_

---

## Interactive UX — use menus to reduce user typing

Whenever you face a meaningful choice — approach, output format, ambiguous request — **use `AskUserQuestion` to present options** rather than guessing or asking in prose. This keeps interactions fast and reduces back-and-forth.

**AskUserQuestion format rules (always follow):**

- `header`: ≤12 characters (e.g. `"Format"`, `"Next step"`, `"Confirm"`)
- `label`: 1–5 words per option
- First option = recommended, labeled `"... (Recommended)"`
- 2–4 options max; add "Other" only if the user might need free-form input

**When the user's request is ambiguous (no URL, vague topic):**
Ask before running anything:

- "What would you like to do?" → choices: Search the live web / Fetch a specific URL / Discover URLs on a site / Call an API endpoint
- "Which site?" (if they said "find Italian restaurants") → choices: Yelp / Google Maps / TripAdvisor / Other (ask)

**Before running a search — offer focus mode:**
When the task clearly maps to a non-general focus mode, ask:

- "Which type of search would be most useful?" → choices: General web / News & current events / Coding & technical / Shopping & prices / Academic & research / Social & people / Other

**Before extracting — offer output format:**
For most extractions, ask what format the user wants:

- "How would you like the results?" → choices: Clean summary (prose) / Structured table / Parsed JSON / Raw markdown

**When a command fails or returns empty/blocked results:**
Silently escalate through render tiers **1 → 2 → 3** without asking. After Tier 3, **pick Tier 4, 5, or both** based on what is blocking (see the tier table) — they are alternatives, not a sequence. Only surface a decision when you've exhausted all applicable tiers and still have no data:

- Check what investigation tools are available:
  ```bash
  which browser-use 2>/dev/null && echo "browser-use: yes" || echo "browser-use: no"
  python3 -c "from playwright.sync_api import sync_playwright; print('playwright: yes')" 2>/dev/null || echo "playwright: no"
  ```
- If **browser-use** is available: ask "I couldn't get the data with standard extraction. Should I investigate the page with browser-use to find the right selectors?"
- If **Playwright** is available (but not browser-use): ask "I couldn't get the data. Should I investigate the page with Playwright (free) to find the right selectors?"
- If **neither** is available: ask "I couldn't get the data. Which investigation tool should I set up?" → options: `Install browser-use (npm i -g @nimbleway/browser-use-cli)` / `Install Playwright (pip install playwright && playwright install chromium)` / `Skip — show me what to do manually`
- Never ask the user to choose between render tiers — that's your job.

**After presenting results:**
Always close with a quick feedback prompt. See the **Self-Improvement** section below for how this feeds the learning loop.

Keep menus to 2–4 options. For free-form input (a URL, a search query), just ask directly.

## Prerequisites

**Quick check — run once at the start of each task:**

```bash
nimble --version && echo "${NIMBLE_API_KEY:+API key: set}"
```

If this prints the CLI version and `API key: set` — you're ready. Skip to [Step 0](#step-0).

If it fails (command not found or API key missing), run the **one-time init** below.

---

### One-time init (run once per machine, never again)

This script saves the nimble binary path and API key to `~/.claude/settings.json`.
Claude Code auto-injects both into every session — no exports or PATH tricks needed ever again.

```bash
python3 -c "
import json, pathlib, subprocess, os

p = pathlib.Path.home() / '.claude/settings.json'
d = json.loads(p.read_text()) if p.exists() else {}
env = d.setdefault('env', {})

# Find nimble binary
found = None
for c in ['nimble', str(pathlib.Path.home() / 'go/bin/nimble')]:
    try:
        r = subprocess.run([c, '--version'], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            found = c
            print('✓ nimble: ' + r.stdout.strip())
            break
    except: pass

# Add go/bin to PATH in Claude settings so nimble works in every session
go_bin = str(pathlib.Path.home() / 'go/bin')
cp = env.get('PATH') or os.environ.get('PATH', '/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin')
if go_bin not in cp:
    env['PATH'] = cp + ':' + go_bin
    print('✓ Added ~/go/bin to Claude settings PATH')
else:
    print('✓ ~/go/bin already in PATH config')

# Save API key to Claude settings if found anywhere
key = env.get('NIMBLE_API_KEY') or os.environ.get('NIMBLE_API_KEY', '')
if key and not env.get('NIMBLE_API_KEY'):
    env['NIMBLE_API_KEY'] = key
    print('✓ Saved NIMBLE_API_KEY to ~/.claude/settings.json')
print('NIMBLE_API_KEY: ' + ('set' if key else 'MISSING — follow the API key setup below'))

p.write_text(json.dumps(d, indent=2))

if not found:
    print()
    print('✗ nimble not installed. Install it:')
    print('    brew install go   # skip if go is already installed')
    print(\"    go install 'github.com/Nimbleway/nimble-cli/cmd/nimble@latest'\")
    print('  Then run this init script again.')
elif key:
    print()
    print('✓ Init complete. Restart Claude Code to activate.')
"
```

**After running init → restart Claude Code.** The PATH change takes effect on next launch.
Then run the quick check again — `nimble --version` should work with no exports.

---

### If nimble is not installed

**Stop immediately.** Do not attempt the original task. Do not speculate about what agents or data might exist. Do not try WebFetch or other tools as a substitute.

Tell the user:

> "Nimble CLI is not installed. Install it:"
>
> ```bash
> brew install go   # skip if already installed
> go install 'github.com/Nimbleway/nimble-cli/cmd/nimble@latest'
> ```
>
> "After installing, run the one-time init script above, restart Claude Code, and come back."

Do not retry the task. Do not loop. Wait for the user to confirm, then re-run the quick check and proceed.

**If bash access is denied (permission error, not a nimble error):** Stop after the first denial. Do NOT retry with `dangerouslyDisableSandbox=true`, do NOT try alternative forms of the same command, do NOT attempt WebFetch as a substitute for a nimble CLI task. Show the correct command as text and tell the user to run it themselves.

---

### If NIMBLE_API_KEY is missing — guided setup flow

**Do NOT tell the user to set it up manually.** Run this automated flow instead:

**Step 1 — Open the Nimble dashboard:**

```bash
open -a "Google Chrome" "https://online.nimbleway.com/overview" 2>/dev/null || open "https://online.nimbleway.com/overview"
```

Tell the user:

> "I've opened the Nimble dashboard. Log in, go to **Overview → API Token**, copy your token, and paste it back here."

**Step 2 — Ask for the token using AskUserQuestion:**
Present one question: _"Please paste your Nimble API token below — I'll save it so you never have to enter it again."_
The user selects **Other** and pastes the key.

**Step 3 — Save to `~/.claude/settings.json` (replace `<TOKEN>` with the pasted value):**

```bash
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

Confirm to the user:

> "✓ Done! Your API key is saved. Restart Claude Code once to activate, then we're all set."

Then immediately proceed with the original task.

---

### Nimble Docs MCP — connect Claude directly to the full documentation

The Nimble docs MCP gives Claude instant access to the complete Nimble documentation — CLI flags, agent schemas, API reference — without web searches or extractions on every question.

**Check if already configured:**

```bash
claude mcp list | grep nimble-docs && echo "✓ configured" || echo "✗ not configured"
```

**Add it with one command:**

```bash
claude mcp add --transport http nimble-docs https://docs.nimbleway.com/mcp
```

Then restart Claude Code to activate. After restart, Claude can query Nimble docs directly.

**Fallback — if MCP is not available, extract docs directly:**

```bash
# Compact overview (good for quick reference)
nimble --transform "data.markdown" extract \
  --url "https://docs.nimbleway.com/llms.txt" --format markdown

# Full documentation (use when you need complete detail)
nimble --transform "data.markdown" extract \
  --url "https://docs.nimbleway.com/llms-full.txt" --format markdown > .nimble/nimble-docs-full.md
head -200 .nimble/nimble-docs-full.md
```

**If bash is also unavailable:** Use the `WebFetch` tool to fetch `https://docs.nimbleway.com/llms.txt` directly. Always use `llms.txt` (compact) or `llms-full.txt` (complete) as the source, not a generic docs page.

---

## Step 0 — Try a built-in agent first (always)

Before running any `extract`, `search`, or `map` command, check whether a pre-built Nimble agent covers the request. Agents return clean structured data with zero selector work — they're faster and more reliable than manual extraction.

**ALWAYS verbalize this check to the user — never do it silently:**

1. **Announce the check:** Before looking up anything, say: _"Let me check if there's a pre-built Nimble agent for [site/topic]..."_
2. **Report what you found:**
   - If a match is found: _"Found the `<agent_name>` agent — using it now."_
   - If no match: _"No pre-built agent found for [site] — falling back to standard extraction."_
3. **Never skip Step 0 silently.** Even if you're certain there's no agent, you must say so before proceeding to extract/search.

**Lookup order:**

1. Check `agents[]` in `~/.claude/skills/nimble-web-expert/learned/examples.json` — remembered from previous uses
2. Check the baked-in table in `references/nimble-agents/SKILL.md` — covers 50+ sites out of the box
3. **Not in the table?** Run `nimble agent list --limit 100`, filter by keyword, present a table, ask user to confirm
4. No match in list either → proceed to extract/search workflow as normal

**If 2+ agents could match, show a quick table and use `AskUserQuestion` to confirm before running.**

**Quick agent cheat sheet (top sites — see `references/nimble-agents/SKILL.md` for full list):**

| Site              | Agent                               | Key param                  |
| ----------------- | ----------------------------------- | -------------------------- |
| Amazon product    | `amazon_pdp`                        | `asin`                     |
| Amazon search     | `amazon_serp`                       | `keyword`                  |
| Walmart product   | `walmart_pdp`                       | `product_id`               |
| Target product    | `target_pdp`                        | `tcin`                     |
| Google SERP (rank/SEO) | `google_search`                  | `query`                    |
| Google Maps       | `google_maps_search`                | `query`                    |
| Yelp search       | `yelp_serp`                         | `search_query`, `location` |
| Zillow listings   | `zillow_plp`                        | `zip_code`, `listing_type` |
| Indeed jobs       | `indeed_search_2026_02_23_vlgtrsgu` | `location`, `search_term`  |
| Instagram profile | `instagram_profile_by_account`      | `username`                 |

⚠️ `google_search` returns SERP rankings for SEO analysis — not general information retrieval. For finding information use `nimble search` instead.

---

## Workflow — what to use when

> **Always run Step 0 first** — check for a pre-built agent before any command below.

| Situation                       | Command                                 | Reference                                            |
| ------------------------------- | --------------------------------------- | ---------------------------------------------------- |
| Known site (Amazon, Yelp, etc.) | `nimble agent run --agent <name> --params '{...}'` | `references/nimble-agents/SKILL.md`           |
| Fetch a URL / read a page       | `nimble extract`                        | `references/nimble-extract/SKILL.md`                 |
| Search the live web             | `nimble search`                         | `references/nimble-search/SKILL.md`                  |
| Discover URLs on a site         | `nimble map`                            | `references/nimble-map/SKILL.md`                     |
| Bulk archive many pages         | `nimble crawl run`                      | `references/nimble-crawl/SKILL.md`                   |
| Unknown selectors or XHR path   | browser-use or Playwright investigation | `references/nimble-extract/browser-investigation.md` |
| Common sites (proven patterns)  | copy a recipe                           | `references/recipes.md`                              |

**Render escalation for extract (Tiers 1–3 are sequential; Tiers 4–5 are alternatives, not a sequence):**

| Tier | When                                      | Command flag                         |
| ---- | ----------------------------------------- | ------------------------------------ |
| 1    | Static pages, docs, news                  | _(no flag)_                          |
| 2    | SPAs, dynamic content                     | `--render`                           |
| 3    | E-commerce, social, job boards            | `--render --driver vx10-pro`         |
| 4 **or** 5 | Tier 3 still blocked — pick based on what is missing (see below) | — |
| 4    | Data hidden behind clicks/scrolls/forms   | `--render --browser-action '[...]'`  |
| 5    | Data loaded via XHR/AJAX calls            | `--render --network-capture '[...]'` |
| 4+5  | Interaction triggers the XHR (e.g. click loads an API response) | combine both flags |
| 6    | Unknown selectors/XHR — investigate first | browser-use or Playwright            |

**Choosing between Tier 4 and Tier 5 (after Tier 3 fails):**
- **Tier 4 only** — content is already in the DOM but requires user interaction to reveal it (infinite scroll, accordion, tab click, "load more" button).
- **Tier 5 only** — content is fetched from a background API; the HTML itself has no useful data.
- **Both (Tier 4+5)** — a user action (click, scroll) triggers an XHR that returns the data. Use `--browser-action` to perform the action and `--network-capture` to intercept the response in the same command.
- **Tier 6** — you don't yet know which applies. Investigate first with browser-use or Playwright, then return to Tier 4, 5, or 4+5.

---

## Response shapes

Output format varies by command and flags — know what to expect before parsing:

| Command + flags                            | Shape                                    | Access pattern                               |
| ------------------------------------------ | ---------------------------------------- | -------------------------------------------- |
| `nimble extract` (default)                 | Markdown text                            | Read directly                                |
| `nimble extract --format json`             | `{"data": {"markdown": "..."}}`          | Use `--transform "data.markdown"` to flatten |
| `nimble extract --parse`                   | `{"data": {"parsing": {fields}}}`        | `jq '.data.parsing'`                         |
| `nimble extract --network-capture '[...]'` | `{"data": [{"url":"...","body":"..."}]}` | `jq '.data[0].body'` for first capture       |
| `nimble search`                            | JSON array                               | `[{"title", "url", "description"}]`          |
| `nimble map`                               | JSON array                               | `[{"url", "type"}]`                          |
| `nimble crawl run`                         | `{"job_id": "..."}`                      | Poll with `nimble crawl status <job_id>`     |
| `nimble agent run` — PDP                   | Flat dict                                | `amazon_pdp`, `walmart_pdp`, etc.            |
| `nimble agent run` — SERP/list             | Array of dicts                           | `amazon_serp`, `yelp_serp`, etc.             |

**Before running an agent:** check its type with `nimble agent schema <name>` — look for `entity_type`. `"product"` = dict (PDP), `"list"` = array (SERP). Guard array access with `isinstance(result, list)` before iterating in scripts.

---

## Output & Organization

```bash
mkdir -p .nimble   # always save outputs here
```

**File naming:** `.nimble/<site>-<task>.md` (e.g. `.nimble/amazon-airpods.md`, `.nimble/yelp-sf-italian.json`)

**Always attribute the source.** End every response with:

> _Source: [URL] — fetched live via Nimble CLI_

For search results, note the focus mode and time range if relevant (e.g. _"nimble search --focus news --time-range week"_).

**Working with saved files:**

```bash
ls -la .nimble/              # check saved files
wc -l .nimble/page.md        # size before reading
head -100 .nimble/page.md    # read first chunk
grep -n "price\|rating" .nimble/page.md | head -30   # find what you need
```

### Final response format (Step 4)

End every completed task with a summary table and attribution:

| Field        | Value                                    |
| ------------ | ---------------------------------------- |
| Command used | `nimble extract --url "..." --render`    |
| Agent        | `amazon_pdp` (or `—` if manual extract)  |
| Source       | URL fetched                              |
| Records      | count or `—`                             |
| Output       | Displayed inline / `.nimble/filename.md` |

Then close with: `Source: [URL] — fetched live via Nimble CLI`

---

## Self-Improvement — learn from every task

The skill maintains a learning file at `~/.claude/skills/nimble-web-expert/learned/examples.json`. Use it to improve future extractions on the same sites.

### At task start

Before running any command, read the learned examples file:

```bash
cat ~/.claude/skills/nimble-web-expert/learned/examples.json 2>/dev/null || echo "{}"
```

Scan the `good[]` array for entries where `url_pattern` matches the current site/task. If a match exists, use the documented `command` and `selectors` as your starting point — skip lower tiers.

Scan the `bad[]` array for entries matching the site. Avoid the documented pitfalls.

### After presenting results

Always close with a feedback prompt using `AskUserQuestion`:

> "Were these results what you needed?"
> Options: `Looks great!` / `Mostly good, minor issues` / `Not quite — let me explain` / `Skip feedback`

### On positive feedback ("Looks great!" or "Mostly good")

Append to `good[]` in the learned examples file:

```bash
python3 -c "
import json, pathlib
p = pathlib.Path.home() / '.claude/skills/nimble-web-expert/learned/examples.json'
p.parent.mkdir(parents=True, exist_ok=True)
data = json.loads(p.read_text()) if p.exists() else {'good': [], 'bad': []}
data['good'].append(NEW_ENTRY)
p.write_text(json.dumps(data, indent=2))
print('Saved.')
"
```

Include: `url_pattern`, `task`, `command`, `selectors`, `tier`, `notes`, `feedback`.

### On negative feedback ("Not quite")

Ask a follow-up: "What went wrong?" (free-form). Then append to `bad[]` with: `url_pattern`, `task`, `issue`, `avoid`, `better`.

### Rules

- Keep entries concise — 5–10 per site is enough; don't add duplicates
- Only write entries when you have real feedback, not speculatively
- If the learned file grows beyond 100 entries, summarize redundant ones before appending

---

## Guardrails

- **NEVER answer from training data** for live prices, current news, today's stock, or any real-time data. If Nimble is unavailable, say so — do not guess or use WebFetch as a substitute for scraping tasks.
- **NEVER skip Step 0 silently.** Even if you're 100% certain there's no agent, announce it before running extract/search/map.
- **NEVER retry the same render tier.** If a tier returns empty or blocked, escalate to the next tier — do not re-run the same command.
- **NEVER use `dangerouslyDisableSandbox=true`.** If bash access is denied, stop and show the command as text.
- **NEVER substitute WebFetch for nimble CLI tasks.** WebFetch is a fallback for fetching Nimble docs only — not for scraping, search, or data extraction.
- **NEVER load reference files speculatively.** Only read a reference when the current task explicitly requires it.
- **NEVER leave extraction data in memory only.** Save to `.nimble/` before presenting.
- **Task agents MUST use `run_in_background=False`.** Background Task agents may not have reliable Bash access in all environments. This is mandatory — no exceptions.
- **Every Task agent prompt MUST include PATH context.** Add `export PATH="$HOME/go/bin:$PATH"` or the known nimble path so the subagent can find the CLI.
- **Hard retry limit.** If a nimble command returns an error (not empty content), retry at most 2 times with different flags. After 2 errors, report and stop.
- **Hard 429 rule.** If nimble returns a 429 or rate-limit error, stop immediately. Do not retry, do not switch tiers. Report quota exhaustion and wait for user instruction.

---

## Reference files

Load only when needed:

| File                                                 | Load when                                                                        |
| ---------------------------------------------------- | -------------------------------------------------------------------------------- |
| `references/recipes.md`                              | Need a proven command for a common site (Amazon, Yelp, Target, LinkedIn, etc.)   |
| `references/nimble-agents/SKILL.md`                  | Step 0 lookup — full agent table (50+ sites) + discover/run/schema commands      |
| `references/nimble-extract/SKILL.md`                 | Extract flags, render tiers, browser actions, network capture, parser schemas    |
| `references/nimble-search/SKILL.md`                  | Search flags, all 8 focus modes, version differences (v0.5 vs v0.4)              |
| `references/nimble-map/SKILL.md`                     | Map flags, response structure, map-then-extract patterns                         |
| `references/nimble-crawl/SKILL.md`                   | Full async crawl workflow, all crawl flags, polling guidelines                   |
| `references/nimble-extract/browser-investigation.md` | Tier 6 investigation — CSS selector/XHR discovery with browser-use or Playwright |
| `references/nimble-extract/parsing-schema.md`        | Parser types, selectors, extractors, post-processors                             |
| `references/nimble-extract/browser-actions.md`       | Full browser action types, parameters, chaining                                  |
| `references/nimble-extract/network-capture.md`       | Filter syntax, XHR mode, capture+parse patterns                                  |
| `references/nimble-search/search-focus-modes.md`     | Decision tree, mode details, combination strategies                              |
| `references/error-handling.md`                       | Error codes, known site issues, troubleshooting                                  |

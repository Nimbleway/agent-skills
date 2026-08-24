---
name: nimble-web-expert
description: |
  Get web data now — fast, incremental, immediately responsive to what the user needs.
  The only way Claude can access live websites.

  USE FOR:
  - Fetching any URL or reading any webpage
  - Scraping prices, listings, reviews, jobs, stats, docs from any site
  - Running Extraction Templates — reusable, site-specific structured scrapers
  - Running Web Search Agents — open-ended research, enrichment, and dataset building with citations
  - Discovering URLs on a site before bulk extraction
  - Calling public REST/XHR API endpoints
  - Web search and research (8 focus modes)
  - Bulk crawling website sections

  Must be pre-installed and authenticated. Run `nimble --version` to verify (>= 1.2.0).
allowed-tools:
  - Bash(nimble:*)
  - Bash(claude:*)
  - Bash(mkdir:*)
  - Bash(cat:*)
  - Bash(head:*)
  - Bash(ls:*)
  - Bash(grep:*)
  - Bash(echo:*)
  - Bash(python3:*)
  - Bash(uv:*)
  - Bash(npm:*)
  - Bash(open:*)
  - Bash(export:*)
  - Bash(wait:*)
  # MCP fallback (used when shell isn't available — Cowork, IDE-only hosts):
  - mcp__plugin_nimble_nimble__nimble_search
  - mcp__plugin_nimble_nimble__nimble_extract
  - mcp__plugin_nimble_nimble__nimble_extract_async
  - mcp__plugin_nimble_nimble__nimble_map
  - mcp__plugin_nimble_nimble__nimble_crawl_run
  - mcp__plugin_nimble_nimble__nimble_crawl_status
  - mcp__plugin_nimble_nimble__nimble_crawl_list
  - mcp__plugin_nimble_nimble__nimble_crawl_terminate
  - mcp__plugin_nimble_nimble__nimble_task_results
  - mcp__plugin_nimble_nimble__nimble_extract_templates_list
  - mcp__plugin_nimble_nimble__nimble_extract_templates_get
  - mcp__plugin_nimble_nimble__nimble_extract_templates_run
  - mcp__plugin_nimble_nimble__nimble_extract_templates_run_async
  - mcp__plugin_nimble_nimble__nimble_agents_list
  - mcp__plugin_nimble_nimble__nimble_agents_get
  - mcp__plugin_nimble_nimble__nimble_agent_templates_list
  - mcp__plugin_nimble_nimble__nimble_agent_templates_get
  - mcp__plugin_nimble_nimble__nimble_agents_run
  - mcp__plugin_nimble_nimble__nimble_agents_run_status
  - mcp__plugin_nimble_nimble__nimble_agents_run_result
  - mcp__plugin_nimble_nimble__nimble_agents_runs_list
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Task
  - AskUserQuestion
license: MIT
metadata:
  version: 1.7.0
  author: Nimbleway
  repository: https://github.com/Nimbleway/agent-skills
  category: web-search-tools
---

# Nimble Web Expert

Web extraction, search, and URL discovery using the Nimble CLI. Returns clean structured data from any website.

User request: $ARGUMENTS

## Core principles

- **Route by intent first** (see [Analyze & Route](#analyze--route) for the full decision model). Named site with a matching Extraction Template + a direct item to look up → run the template. Site with no template, or a need that requires discovery/reasoning across pages → a Web Search Agent. One-off single URL → `nimble extract`. Raw results to work from ("find pages/articles about…") → `nimble search`; a synthesized deliverable (report, brief, comparison, recommendation) → a Web Search Agent. Discover/crawl URLs → `nimble map` or `nimble crawl`.
- **Web Search Agent runs: pick a run mode before building the command.** Default to named create-or-reuse — `nimble agents run --agent-name <stable-name>` — so a repeat session lands on the same agent. `agents:runs create` is the explicit-agent-ID route only and requires `--agent-id`. `references/nimble-agents/reference.md` has the mode table, `use_case` locking, and the one-time `skill` override.
- **One command → present results → done.** Run once, show the data immediately as a table. Do NOT experiment, loop, or write Python to parse output.
- **Multiple inputs → always parallel.** 2+ URLs/keywords/ASINs → `&`+`wait`. 6–20 → `xargs -P`. 20+ → Python asyncio script. See `references/batch-patterns.md`.
- **Escalate render tiers silently on empty or truncated content.** Tier 1 → 2 → 3 → … without asking. Surface a decision only when all tiers fail and investigation tools are needed. An access barrier is a different outcome, not a tier to climb — see Guardrails.
- **Never answer from training data.** Live prices, current news, today's listings → always fetch via Nimble. If unavailable, say so.
- **AskUserQuestion at every meaningful choice.** Header ≤12 chars, 2–4 options, label 1–5 words, recommended option first. Never present choices as numbered prose.
- **Save all outputs to `.nimble/`.** Never leave extraction results in memory only.
- **Verify the connection BEFORE working — don't fire a data call and react to the error.** With bash, `nimble --version` + `NIMBLE_API_KEY` confirms the CLI path; otherwise run one read-only `mcp__plugin_nimble_nimble__nimble_agents_list` probe. Success = connected; an auth/not-connected error or a response containing an OAuth authorization URL = not connected.
- **No working CLI and no connected MCP → stop.** Do not fall back to WebFetch, WebSearch, curl, or `dangerouslyDisableSandbox`. If the plugin is installed but the connector isn't connected (typical Cowork / claude.ai), surface the verbatim connect steps from `rules/setup.md` and stop; if no plugin at all, follow the install flow in `rules/setup.md`.
- **If a tool hands back an OAuth "Authorize" link instead of data, present it exactly as given and stop.** Never invent a "paste the URL back" / "I'll complete the connection" step — none exists — and never claim tools "will activate" then call them in the same turn. Wait for the user to authorize, then retry or re-probe.

## Capabilities

One skill, one taxonomy. Use Nimble's own product names precisely — never paraphrase them.

| Capability             | What it is                                                                        | Command family              |
| ---------------------- | --------------------------------------------------------------------------------- | --------------------------- |
| **Search**             | Real-time web search — raw results (pages, snippets), 8 focus modes               | `nimble search`             |
| **Extract**            | Fetch + parse a single known URL (the one-off primitive)                          | `nimble extract`            |
| **Extraction Template**| Reusable, site-specific structured scraper for a known item (by URL or identifier)| `nimble extract:templates`  |
| **Web Search Agent**   | Open-ended research / enrichment / dataset building — discovers sources, synthesizes, cites | `nimble agents` / `agents:runs` |
| **Map**                | Discover the URLs that exist on a site                                            | `nimble map`                |
| **Crawl**              | Bulk-fetch many pages across a site (one-time, at scale)                          | `nimble crawl`              |

Extraction Templates and Web Search Agents are distinct — an Extraction Template is a fixed, site-specific parser; a Web Search Agent reasons across sources. Never call an Extraction Template a "WSA" or a "legacy WSA," and never route a template use to `agents` (or vice-versa) by name alone. Building new templates/agents is out of scope here — use **existing** ones (point users to the Nimble app to build new).

## Interactive UX

- Use `AskUserQuestion` at every meaningful choice — never guess, never ask in prose.
- **Ambiguous request** (no URL, vague topic): ask before running — "What would you like to do?" → Research & report / Search / Fetch URL / Discover URLs
- **Gate B landed on a Web Search Agent at `high`+ effort**: offer the cost/latency fork — Researched report / Quick scan (see [Analyze & Route](#analyze--route))
- **Before running a search** (if task maps to a specific focus mode): offer focus mode — General / News / Coding / Shopping / Academic / Social
- **After all tiers fail**: check investigation tools (`which browser-use`, `python3 -c "from playwright.sync_api..."`) and ask whether to investigate with browser-use, Playwright, or skip.
- After presenting results, always close with: "Were these results what you needed?" → `Looks great!` / `Mostly good` / `Not quite` / `Skip feedback`

## Prerequisites

Pick CLI or MCP at session start — same skill, two transports. Once a transport is selected, stick with it for the session and don't re-probe on every command.

```bash
nimble --version && echo "${NIMBLE_API_KEY:+API key: set}"        # CLI path
# OR (fallback when shell isn't available)
claude mcp list 2>/dev/null | grep -q "nimble" && echo "MCP: ok"  # plugin MCP
```

- **CLI ready** (version + API key both print) → proceed to [Step 0](#analyze--route), use `nimble ...` commands.
- **MCP connected** (no CLI, but plugin is installed) → proceed to [Step 0](#analyze--route), use `mcp__plugin_nimble_nimble__*` tools instead.
- **Neither** → load `rules/setup.md` for the environment-aware install flow. Any Claude product (Code, Cowork, claude.ai) → `/plugin install nimble`. Codex or other terminal-only agents → `npm i -g @nimble-way/nimble-cli`. Cursor / VS Code / generic MCP clients → paste the `mcp.json` snippet.

**If bash is denied:** you're in a Cowork-like / MCP-only host. Use `mcp__plugin_nimble_nimble__*` tools, but verify the connection first with one read-only `nimble_agents_list` probe. If the probe fails with an auth/not-connected error or returns an OAuth authorization URL, the connector isn't connected — surface the connection steps from [Core principles](#core-principles) and stop (and never invent an auth-completion flow). **Never substitute WebFetch, WebSearch, curl, or any other tool for Nimble operations.**

---

## Analyze & Route

Two gates, in order. **Gate A** asks where the data lives; **Gate B** asks what the user wants back. Most mis-routes come from skipping Gate B — a request with no location signal is not automatically a search.

### Gate A — do I know where the data lives?

| User signal                                   | Route                                                                               |
| --------------------------------------------- | ------------------------------------------------------------------------------------ |
| Direct single URL to fetch                    | `nimble extract`                                                                     |
| Named site + a direct item to look up (URL/ID)| **Step 0** — check for an Extraction Template first                                  |
| "Find URLs / sitemap / all pages"             | `nimble map`                                                                         |
| "Crawl / archive a whole section"             | `nimble crawl`                                                                       |
| **No location signal at all**                 | Fall through to **Gate B**                                                           |
| Named site with **no** template               | Fall through to **Gate B**, carrying the site as a source constraint                 |

**The most common overlap — a site with no Extraction Template.** It looks like a choice between a raw `extract` (which dumps parsing work on the user) or building a template (out of scope). Neither is right: fall through to Gate B, which will land on a **Web Search Agent** — it configures fresh for any site and reasons about structure without a maintained template. This isn't a question to put to the user; when no template fits, the answer is the same every time.

### Step 0 — Extraction Template check (when a site + direct item is named)

Templates return clean structured data with zero selector work. Always check first.

**Always verbalize — never silently:**

1. **Announce:** _"Let me check if there's a Nimble Extraction Template for [site]..."_
2. **Report:** _"Found `<template_name>` — using it now."_ or _"No template for [site] — using a Web Search Agent instead."_

**Lookup order:**

1. `~/.claude/skills/nimble-web-expert/learned/examples.json` → learned templates
2. `nimble extract:templates list --limit 100` → filter by site/domain client-side; confirm the match
3. Inspect the schema before running: `nimble extract:templates get --extract-template-name <name>`
4. No match → route to a Web Search Agent (per the overlap rule above)

```bash
nimble extract:templates run --template <name> --params '{"key": "value"}'
```

`--params` is a JSON/YAML mapping matching the template's `input_schema`. The response is the records defined by the template's `output_schema` (array for list/SERP-style, object for detail/PDP-style) — read the schema from `get` to know the shape. See `references/nimble-extract-templates/reference.md`.

⚠️ For finding information, use `nimble search`, not a SERP-analysis template. SERP templates are for rank/SEO analysis, not general retrieval.

### Gate B — what does the user want back?

`nimble search` returns **raw material to skim**. A Web Search Agent returns a **finished, cited answer**. The prompt's deliverable noun decides it — route on that, not on how open-ended the topic sounds.

| → **Web Search Agent**                                                | → **`nimble search`**                       |
| ---------------------------------------------------------------------- | --------------------------------------------- |
| report, brief, analysis, landscape, teardown, deep dive                | find, search for, look up                     |
| compare, "best X", "which should I", "state of", recommend             | "pages/articles about", "links to"            |
| enrich, build a list, dataset, "…with their pricing/headcount"         | latest news, recent posts, what's trending    |

Structured rows about many entities → Web Search Agent with `enrichment` or `dataset_building`. See `references/nimble-agents/reference.md`.

### Offer the fork when the answer is the expensive one

A Web Search Agent at `high` effort takes minutes and costs more; a search takes seconds. That's a real trade-off, so surface it — **but only when Gate B lands on a Web Search Agent AND the recommended effort is `high` or above.** One `AskUserQuestion`, recommended option first:

- **Researched report** — Web Search Agent, a few minutes, every claim cited
- **Quick scan** — `nimble search`, seconds, raw links you skim yourself

Below `high`, don't ask — just run the Web Search Agent. Never ask when Gate A already resolved the route.

**Dataset requests always clear the threshold.** "Build a list of…" → `dataset_building`, which runs at `high` or above by definition, so the fork always applies. Enrichment has no such floor — judge "enrich these rows" on the normal effort rule and skip the prompt when a small, well-specified fill-in lands below `high`.

**Before starting any Web Search Agent run, say how long it will take**, then narrate at phase transitions. On MCP, progress comes from bounded status polling rather than a live stream — poll and report each step, because an un-narrated multi-minute run reads as a hang.

---

## Workflow

| Situation                        | Command                                        | Reference                                            |
| -------------------------------- | ---------------------------------------------- | ---------------------------------------------------- |
| Site + item → template first     | `extract:templates list` → `extract:templates run` | `references/nimble-extract-templates/reference.md`   |
| Research / enrichment / dataset  | pick a run mode → `get` → `result`             | `references/nimble-agents/reference.md`                  |
| Direct URL                       | `nimble extract`                               | `references/nimble-extract/reference.md`                 |
| Search the live web              | `nimble search`                                | `references/nimble-search/reference.md`                  |
| Discover URLs on a site          | `nimble map`                                   | `references/nimble-map/reference.md`                     |
| Bulk crawl a section             | `nimble crawl run`                             | `references/nimble-crawl/reference.md`                   |
| Batch templates (up to 1,000)    | `nimble extract:templates batch`               | `references/nimble-extract-templates/reference.md`       |
| Batch extract (up to 1,000)      | `nimble extract-batch`                         | `references/nimble-extract/reference.md`                 |
| Poll tasks / batches / results   | `nimble tasks` / `nimble batches`              | `references/nimble-tasks/reference.md`                   |
| Unknown selectors or XHR path    | browser-use or Playwright investigation        | `references/nimble-extract/browser-investigation.md` |
| Proven site patterns             | copy a recipe                                  | `references/recipes.md`                              |
| 2+ inputs                        | parallel bash `&`+`wait` or generated script   | `references/batch-patterns.md`                       |

For the full extract waterfall (tiers, flags, browser actions, network capture), see `references/nimble-extract/reference.md`.

---

## Response shapes

| Command                     | Output                                                                                  |
| --------------------------- | --------------------------------------------------------------------------------------- |
| `nimble extract:templates`  | Records per the template's `output_schema` — array (list/SERP) or object (detail/PDP)   |
| `nimble agents:runs result` | `output` (`type:"text"` prose or `type:"json"` structured) + `trust` per-claim citations |
| `nimble extract`            | HTML, Markdown, or parsed JSON — depends on `--format` and `--parse`                     |
| `nimble search`             | Structured results array (title, URL, description)                                      |
| `nimble map`                | URL list + metadata                                                                     |
| `nimble crawl`              | Async job — poll with `nimble crawl status <job_id>`                                     |

**Read the template's `output_schema` (from `extract:templates get`) before parsing** — a list/SERP-style template returns an array, a detail/PDP-style template returns an object. Web Search Agent runs are async: poll `agents:runs get` to a terminal state, then fetch `result`.

## Output & Organization

```bash
mkdir -p .nimble   # save all outputs here
```

Naming: `.nimble/<site>-<task>.md` (e.g. `.nimble/amazon-airpods.md`, `.nimble/yelp-sf-italian.json`)

Working with saved files:

```bash
wc -l .nimble/page.md && head -100 .nimble/page.md
grep -n "price\|rating" .nimble/page.md | head -30
```

End every response with: `Source: [URL] — fetched live via Nimble CLI`

---

## Self-Improvement

The skill maintains `~/.claude/skills/nimble-web-expert/learned/examples.json`.

- **At task start:** read the file, scan `good[]` for `url_pattern` matches → use documented `command`/`tier` as starting point. Scan `bad[]` → avoid documented pitfalls.
- **After presenting results:** ask "Were these results what you needed?" → on positive feedback, append to `good[]` with `url_pattern`, `task`, `command`, `tier`, `notes`. On negative feedback, ask "What went wrong?" and append to `bad[]` with `url_pattern`, `task`, `issue`, `avoid`, `better`.
- Keep entries concise — 5–10 per site. Only write on real feedback, never speculatively.

---

## Guardrails

- **NEVER answer from training data** for live prices, current news, or real-time data. If Nimble is unavailable, say so.
- **NEVER skip Step 0 silently.** Even if certain there's no template, announce the check before falling back to a Web Search Agent or extract/search.
- **NEVER answer a synthesis deliverable with raw search results.** "Report", "brief", "compare", "best X", "which should I" → Gate B routes to a Web Search Agent. Handing back a list of links and calling it a report is the most common mis-route.
- **Distinguish Extraction Templates from Web Search Agents.** Never call a template a "WSA"/"legacy WSA," and never route a template use to `agents` by name alone (or the reverse). Building new templates/agents is out of scope — use existing ones.
- **When a run comes back empty, partial, or clearly wrong, say so plainly** — a domain that returned nothing, a template that matched poorly, a search with no relevant hits are real outcomes, not something to present as success. Suggest an obvious next step (broader source, a different capability) where one exists.
- **NEVER retry the same render tier.** If a tier returns empty or truncated content, escalate — do not re-run.
- **NEVER escalate at an access barrier.** A CAPTCHA, a human-verification page, or a sign-in wall in place of the target is a real outcome — report it plainly and stop. Where a supported alternative exists, take it: `--focus social` search for social profiles, public search results for gated articles.
- **NEVER substitute WebFetch, WebSearch, curl, or wget for nimble operations.** They're not in `allowed-tools` — if a Nimble transport isn't available, stop and follow the guidance in the no-transport branch of Core principles. Don't try to work around it.
- **NEVER load reference files speculatively.** Only read a reference when the current task explicitly needs it.
- **Task agents MUST use `run_in_background=False`.**
- **Hard retry limit.** On error (not empty content): retry at most 2 times with different flags. After 2 errors, report and stop.
- **Hard 429 rule.** On rate-limit error: stop immediately. Do not retry or switch tiers.

---

## Reference files

Load only when needed:

| File                                                 | Load when                                                                     |
| ---------------------------------------------------- | ----------------------------------------------------------------------------- |
| `references/recipes.md`                              | Need a proven command for a common site (Amazon, Yelp, LinkedIn…)             |
| `references/nimble-extract-templates/reference.md`       | Step 0 — discover/inspect/run Extraction Templates for a known site           |
| `references/nimble-agents/reference.md`                  | Web Search Agents — discovery, run lifecycle, authoring, trust/citations      |
| `references/nimble-extract/reference.md`                 | Extract flags, render tiers, browser actions, network capture, parser schemas |
| `references/nimble-search/reference.md`                  | Search flags, all 8 focus modes                                               |
| `references/nimble-map/reference.md`                     | Map flags, response structure                                                 |
| `references/nimble-crawl/reference.md`                   | Full async crawl workflow                                                     |
| `references/nimble-tasks/reference.md`                   | Poll tasks/batches, fetch results — for async, batch, and crawl operations    |
| `references/nimble-extract/browser-investigation.md` | Tier 6 — CSS selector/XHR discovery with browser-use or Playwright            |
| `references/nimble-extract/parsing-schema.md`        | Parser types, selectors, extractors, post-processors                          |
| `references/nimble-extract/browser-actions.md`       | Full browser action types and parameters                                      |
| `references/nimble-extract/network-capture.md`       | Filter syntax, XHR mode, capture+parse patterns                               |
| `references/nimble-search/search-focus-modes.md`     | Decision tree, mode details, combination strategies                           |
| `references/batch-patterns.md`                       | Parallel bash patterns for 2–5, 6–20, and 20+ inputs                          |
| `references/error-handling.md`                       | Error codes, known site issues, troubleshooting                               |

# Nimble Playbook

How to run Nimble CLI commands in Claude Code. Read this before executing any commands.

---

## Claude Code Execution Rules

- **No shell state persistence.** Variables set in one Bash call are gone in the next.
  Inline all values (dates, paths, names) directly into every command.
- **No `&` + `wait` parallelism.** It breaks in Claude Code. Instead, make **multiple
  Bash tool calls in a single response** — they run in parallel natively.
- **Search returns JSON** — `--output-format` doesn't change this. With `--search-depth
  lite`, the JSON is small (title, description, URL per result). Parse it directly.
- **Extract returns JSON with `data.markdown`** — use `--format markdown` to get clean
  content in the `data.markdown` field.

## Preflight Pattern

### Transport selection (run once per session)

Skills work via two transports — CLI (preferred, full surface area) or MCP (fallback,
curated tool set covering the same operations). Pick one at the start of every
session and stick with it; don't re-probe on every command.

| Check | If it works | What to use |
|---|---|---|
| `nimble --version` (>= 1.2.0) and `NIMBLE_API_KEY` is set | CLI is ready | Bash `nimble ...` commands |
| `claude mcp list 2>/dev/null \| grep -q "nimble"` (or first `mcp__plugin_nimble_nimble__*` call succeeds) | Plugin MCP is connected | `mcp__plugin_nimble_nimble__*` tools |
| `mcp__plugin_nimble_nimble__*` tools are listed, but a read-only `nimble_agents_list` probe returns an auth / not-connected error or an OAuth authorization URL | Plugin is installed but the **connector isn't connected** (typical Cowork / claude.ai state) | **Stop — guide connector connection (below). Never invent an auth-completion flow.** |
| None of the above | Stop — guide install (below) | — |

### Connector not connected (Cowork / claude.ai) — verify BEFORE working

In Cowork / claude.ai the plugin is often installed while its connector is not
yet connected, so live data calls fail. **Confirming the connection is a required
preflight step — not an error to react to mid-task.** When
`mcp__plugin_nimble_nimble__*` tools are listed but you haven't confirmed the
connector is live, run one read-only probe before any real work:

- A single `nimble_agents_list` call is the cheapest confirmation. Success →
  connected, proceed. Auth / not-connected error, **or** a response containing an
  OAuth authorization URL → not connected.

When not connected, surface this verbatim and **stop** — do **not** fall back to
WebFetch, WebSearch, curl, or any other tool, and do **not** guess at data:

> Your Nimble plugin is installed, but its connector isn't connected yet — that's
> why I can't fetch live data. To connect it:
>
> 1. Open **Customize → Connectors**
> 2. Find **Nimble** and click **Connect**
> 3. Complete the login in your browser. **No Nimble account?** You can create one
>    right there during login.
> 4. Once it shows **Connected**, re-run your request and I'll continue.

#### If a tool hands back an OAuth "Authorize" URL

A not-connected tool call may return an authorization link (e.g. "Authorize
Nimble MCP →") instead of data. Present that link to the user exactly as given,
then **stop and wait**. Hard rules:

- **Never invent a completion flow.** There is no "paste the URL from your address
  bar back to me" step, and you cannot "complete the connection" yourself. Claiming
  either is a hallucination.
- **Never say the tools "will activate" and then call them in the same turn.** Wait
  for the user to confirm they've authorized, then retry.
- To check whether authorization succeeded, run one read-only `nimble_agents_list`
  probe — don't assume.

### No plugin and no CLI

If neither path works at all (no plugin installed, no CLI installed), surface
this hint verbatim and stop:

> Nimble isn't installed. Pick the path for your environment:
>
> **Any Claude product (Claude Code, Claude Cowork, claude.ai) — recommended:**
> ```
> /plugin install nimble
> ```
> Installs the Nimble plugin. The `.mcp.json` inside the plugin auto-registers as a Connector in `Customize → Connectors`. First tool call triggers the OAuth flow — no API key needed.
>
> **Codex CLI or other terminal agents (shell access, no `/plugin`):**
> ```
> npm i -g @nimble-way/nimble-cli
> ```
> Then `export NIMBLE_API_KEY=<key>` and re-run. See `references/profile-and-onboarding.md` for the full install flow.
>
> **Cursor, VS Code, or any other MCP client:**
> Paste this into your MCP settings (`.cursor/mcp.json` or host equivalent):
> ```json
> {
>   "mcpServers": {
>     "nimble": { "type": "http", "url": "https://mcp.nimbleway.com/mcp" }
>   }
> }
> ```

The plugin path (`/plugin install nimble`) is the easiest onboarding everywhere it
works — one command, OAuth handles auth, no API key to manage. Use the CLI path
only when shell access is available but `/plugin install` isn't (Codex, raw
terminal agents). Use the manual `mcp.json` path only for MCP clients outside the
Claude family.

### Standard preflight (run in parallel after transport is selected)

Every skill kicks off with these simultaneous calls:

- `python3 -c "from datetime import datetime, timedelta; print((datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d'))"` (14 days ago)
- `date +%Y-%m-%d` (today)
- `cat ~/.nimble/business-profile.json 2>/dev/null` (profile — fall back to MCP filesystem tool if shell unavailable)
- `cat ~/.nimble/memory/index.md 2>/dev/null` (global wiki index — know what directories have data)

Don't skip the transport check — running CLI commands when only MCP is available (or
vice versa) wastes a turn and confuses the user.

## Request Attribution

All Nimble API calls carry a stable integration attribution so usage from this plugin
can be tracked. The value is always `nimble-agent-skills`.

**CLI path** — add `--client-source nimble-agent-skills` as the global flag on every
`nimble` command. Place it immediately after `nimble`, before the subcommand. No shell
state persistence means this must be inlined on every individual call (or set
`CLIENT_SOURCE=nimble-agent-skills` in the environment, which the CLI reads automatically):

```bash
nimble --client-source nimble-agent-skills search --query "..."
nimble --client-source nimble-agent-skills extract --url "..."
nimble --client-source nimble-agent-skills extract:templates run --template <name> --params '{...}'
nimble --client-source nimble-agent-skills agents:runs create --agent-id <id> --input "..."
nimble --client-source nimble-agent-skills map --url "..."
nimble --client-source nimble-agent-skills crawl run --url "..."
```

**MCP path** — integration attribution rides the CLI path via `--client-source`; MCP
requests are attributed at the transport level. Use the CLI path when per-integration
attribution matters. Don't add a header flag to override the MCP transport's attribution.

## Sibling Handoff

When skills in the same family chain together (e.g., extract → enrich → verify),
the second skill can skip redundant preflight work. Detect a sibling handoff by
checking for same-day output from the upstream skill:

```bash
ls ~/.nimble/memory/reports/{upstream-skill}-*$(date +%Y-%m-%d).md 2>/dev/null
```

Use the dated report as the recency signal — data files under `memory/{skill}/` may
not have dates in their filenames, so always verify via the report timestamp. If a
same-day report exists, parse the slug from the filename and load the corresponding
data files.

**If same-day sibling output exists:**
- **Skip CLI check and profile load** — they were validated minutes ago
- **Reuse WSA Layer 1 and Layer 3 inventory** — the catalog hasn't changed. Only
  re-run Layer 2 if the specialty or context changed.
- **Use the sibling's structured output directly** — if the upstream skill produced
  data files with domains and page URLs, don't re-search for what's already known.
  Construct URLs from known patterns instead of running N web searches.

**If no same-day sibling output exists:** Run full preflight as normal.

This pattern is optional — skills MUST still work standalone without sibling output.
The handoff is a fast path, not a requirement.

## Smart Date Windowing

For any skill using `--start-date` based on previous runs:
- **First run:** 14 days ago → **full mode**
- **Last run < 3 days ago:** use 7 days ago (too narrow = empty results) → **quick refresh**
- **Last run 3-14 days ago:** use the last run date → **quick refresh**
- **Last run > 14 days ago:** 14 days ago → **full mode**
- **Same-day repeat:** if `last_runs.{skill-name}` is today, check if a report already
  exists at `~/.nimble/memory/reports/{skill-name}*[today].md`. If it does, **ask the
  user before re-running**: "Already ran today. Run again for fresh data?" Don't silently
  re-run — it wastes API credits and produces near-identical output.
  **Exception — meeting-prep:** Skip the same-day report check. Meeting-prep is
  per-meeting, not per-day — users may prep for multiple meetings in a single day.
  Instead, meeting-prep checks freshness at the entity level: load cached profiles
  from `~/.nimble/memory/people/` and `~/.nimble/memory/companies/` and offer to
  reuse recent research rather than blocking the run.

---

## Search

```bash
# Standard search (always use --search-depth lite for discovery)
nimble search --query "company name news" --max-results 10 --search-depth lite

# News-focused search
nimble search --query "company name" --focus news --max-results 10 --search-depth lite

# Date-filtered search (inline the date — don't use variables)
nimble search --query "company funding" --focus news --start-date "2026-03-11" --max-results 10 --search-depth lite

# Social signals from X/LinkedIn
nimble search --query "Company" --include-domain '["x.com", "linkedin.com"]' --max-results 10 --search-depth lite --time-range week

# Deep search (full page content — only for comprehensive analysis, costs more)
nimble search --query "company name" --search-depth deep --max-results 5

# Fast search (premium tier — not used by default)
# nimble search --query "company name" --search-depth fast --max-results 10
```

**Key flags:**
- `--query` — search query string (required)
- `--focus` — `general`, `news`, `shopping`, `social`, `coding`, `academic`.
  **`social`** searches social platform people indices directly (LinkedIn, X) — best
  for finding specific people. If it errors, use
  `--include-domain '["linkedin.com"]'` as an alternative approach.
- `--max-results` — max results to return
- `--start-date` / `--end-date` — date filters (YYYY-MM-DD)
- `--search-depth` — `lite` (1 credit), `deep` (1 + 1/page)
- `--include-domain` — JSON array of domains, e.g., `'["x.com", "linkedin.com"]'`
- `--time-range` — e.g., `week`
- `--country` — geo-targeted results (e.g., "US", "IL")
- `--include-answer` — LLM-powered answer summary

**Date range strategy:**
- First run: 14 days ago
- Subsequent runs: `last_runs` timestamp from business profile
- If < 3 results: retry without `--start-date`

## Extract

```bash
# Extract article content as markdown (default for content analysis)
nimble extract --url "https://example.com/article" --format markdown

# Extract raw HTML (required for <head> metadata: canonical, schema, og, meta tags)
nimble extract --url "https://example.com" --format html

# Extract with JavaScript rendering (for dynamic/SPA pages)
nimble extract --url "https://example.com/spa" --render --format markdown
```

Response is JSON. The field returned depends on `--format`:
- `--format markdown` → `data.markdown` (clean body content)
- `--format html` → `data.html` (raw HTML including `<head>`)
- `--format plain_text` → `data.plain_text`
- `--format simplified_html` → `data.simplified_html`

**Format selection by use case:**

| Need | Format | Why |
|------|--------|-----|
| Article body content, word count, headings | `markdown` | Clean text, no nav/footer noise |
| Meta tags (title, description, canonical, og, twitter) | `html` | Markdown strips `<head>` |
| Schema markup (JSON-LD) | `html` | Script tags not in markdown |
| hreflang, `<html lang>` | `html` | Attributes not in markdown |
| Structured field extraction | `--parse --parser '{...}'` | LLM extracts specific fields |
| Both body and head | `markdown` + `html` | Two calls or parse html for both |

**Key flags:**
- `--url` — target URL (required)
- `--format` — `markdown`, `html`, `simplified_html`, `plain_text` (pick based on table above)
- `--render` — render JavaScript using a browser
- `--parse --parser '{...}'` — structured extraction via LLM parser schema

**Extraction fallback** (if `data.markdown` is mostly JavaScript/boilerplate):
1. **Garbage check:** If `data.markdown` has < 100 characters of meaningful content
   (after stripping nav/footer boilerplate), treat it as garbage.
2. Retry with `--render --format markdown` (handles JS-heavy/SPA pages)
3. If still garbage: search for the same article title on a different domain
4. If still nothing: skip and log — never abort a batch for a single extraction failure

### Extract async & batch

```bash
# Async — submit single URL, get task_id, poll for results
nimble extract-async --url "https://example.com/page" --render --format markdown

# Batch — up to 1,000 URLs in one request
nimble extract-batch \
  --shared-inputs 'render: true' --shared-inputs 'format: markdown' \
  --input '{"url": "https://example.com/page-1"}' \
  --input '{"url": "https://example.com/page-2"}'
```

Poll async tasks with `nimble tasks get --task-id <id>` and fetch results with
`nimble tasks results --task-id <id>`. Poll batches with
`nimble batches progress --batch-id <id>`.

## Map & Site Mapping

```bash
nimble map --url "https://example.com/blog" --limit 20
```

### Site Mapping Pattern

Use `nimble map` to discover a site's page structure, then score and filter pages by
relevance before extracting.

1. **Discover:** `nimble map --url {url} --limit {cap}` — returns a list of URLs
2. **Score:** Each skill defines a keyword/weight table for URL path segments
   (e.g., `/providers` = High, `/about` = Medium, `/blog` = Low). Score each
   discovered page against the table.
3. **Filter:** Keep pages scoring above the skill's threshold. Always include the
   homepage as a fallback.
4. **Fallback:** If `nimble map` returns < 3 candidates, use
   `nimble search --query "site:{domain} {keywords}" --max-results 10 --search-depth lite`

Each skill provides its own keyword/weight table in SKILL.md — the pattern here is
the discover → score → filter → fallback flow.

## Extraction Templates

Reusable, site-specific templates that return structured fields from a known site
(Amazon products, Reddit threads, Google Maps, etc.) — the right tool when you can point
directly at an item (by URL or identifier) and want clean parsed data, not raw page
content. Use **existing** templates only; do not build new ones from these skills. If no
template covers the site, fall back to `search` + `extract`, or use a Web Search Agent
(below) when the data needs discovery or reasoning across pages.

```bash
# List templates (paginated; scan display_name / name / metadata.domain)
nimble extract:templates list --limit 100

# Inspect a template's input_schema + output_schema before running
nimble extract:templates get --extract-template-name <template_name>

# Run a template (realtime). --params is a JSON/YAML mapping matching input_schema
nimble extract:templates run --template <template_name> --params '{"key": "value"}'

# Async (returns a task to poll) and batch (up to 1,000 items)
nimble extract:templates async --template <template_name> --params '{"key": "value"}'
nimble extract:templates batch --template <template_name> \
  --input '{"params": {"key": "value-1"}}' \
  --input '{"params": {"key": "value-2"}}'
```

**Key flags:**
- `--template` — template `name` from `extract:templates list` (required for run/async/batch)
- `--extract-template-name` — template `name` (for `get`)
- `--params` — JSON/YAML mapping of inputs, matching the template's `input_schema` (required)
- `--localization` — enable zip_code/store_id localization (template-dependent)

**Response:** the structured records defined by the template's `output_schema` — an array
for list/SERP-style templates, an object for detail/PDP-style templates. Always read the
`output_schema` from `extract:templates get` to know the shape before parsing. REST/SDK
equivalent: `POST /v2/extract/templates/run` (and `/async`, `/batch`).

**Async task states:** `pending` → `success` or `error`. Poll status with
`nimble tasks get --task-id <task_id>` until terminal, then fetch with
`nimble tasks results --task-id <task_id>`; batches with `nimble batches progress`.

## Web Search Agents

AI-driven agents for open-ended web work — **research, data enrichment, and dataset
building** — where the source isn't fixed, data is scattered across pages, structure is
inconsistent, or a synthesized answer is needed. Given a goal, an agent discovers where
the information lives, navigates to it, and returns structured or written output with
per-claim citations. This is the right tool when an Extraction Template doesn't fit
because there's no single known page to parse (see the routing note above).

**Reuse-priority — check in this order before creating a new agent:**
1. An existing agent in the account already covers this (`agents list`).
2. A close-match **agent template** worth materializing (`agents:templates list`).
3. Only if neither fits, create one from scratch.

Neither list command takes a server-side search term — list and filter client-side on
`agent_name` / `template_name` / `description` / `use_case`. Never hardcode names.

### Pick a run mode first

The identity you pass decides the route, and the route decides the command:

| Mode                          | Identity                    | Command                                     |
| ----------------------------- | --------------------------- | ------------------------------------------- |
| **1 — named create-or-reuse** | `--agent-name`, no agent ID | `nimble agents run --agent-name <name>`     |
| **2 — explicit agent**        | `--agent-id`                | `nimble agents:runs create --agent-id <id>` |
| **3 — caller-anonymous**      | neither                     | `nimble agents run`                         |

**Mode 1 is the default for these skills** — derive a deterministic name (`{skill}-{purpose}`)
so repeat sessions reuse the same agent instead of creating near-duplicates. A repeated name
returns the **same `web_search_agent_id`**. `agents:runs create` **requires** `--agent-id`
and ignores `--agent-name`; use `nimble agents run` for Modes 1 and 3. Mode 3 still returns a
generated `web_search_agent_id` — keep it, `get` and `result` both need it.

```bash
# Discover pre-built agent templates, then inspect one
nimble --client-source nimble-agent-skills agents:templates list
nimble --client-source nimble-agent-skills agents:templates get --template-name <template_name>

# Create an agent up front — from a template, or from scratch
nimble --client-source nimble-agent-skills agents create --template <template_name>
nimble --client-source nimble-agent-skills agents create \
  --display-name "<name>" --goal "<goal>" --sources '{...}' \
  --output-schema '{...}' --use-case research --effort high

# Mode 1 run (async), then poll status and fetch the result
nimble --client-source nimble-agent-skills agents run \
  --agent-name "<skill>-<purpose>" --use-case research \
  --input "<task or question>" --effort high
nimble --client-source nimble-agent-skills agents:runs get    --agent-id <agent_id> --run-id <run_id>
nimble --client-source nimble-agent-skills agents:runs result --agent-id <agent_id> --run-id <run_id>
```

**Run controls** (both run commands): `--input` (required), `--effort`
(`low`/`medium`/`high`/`x-high`/`max` — default `high` once several fields need real digging),
`--output-schema`, `--input-data`, `--sources`, `--enable-events`,
`--previous-interaction-id`, plus `--skill` and `--use-case` per the rules below.

- **`--sources`** has two shapes in one object: `allow` / `block` are arrays of groups
  (`title` required, `domains`, optional `order` for priority); `prioritize` / `avoid` are
  plain guidance strings.
- **`--input-data`** carries the rows you already have; `--output-schema` describes the shape
  of the answer. Enriching several rows needs an **array** schema — an object schema returns
  one object. Carried-in fields come back with `confidence: "pre_existing"` and no citations;
  never present them as sourced findings.

### `use_case` locks; `skill` overrides once

`use_case` is exactly `research`, `enrichment`, or `dataset_building`. It is stored when the
agent is **created** (including a Mode 1 first call or a Mode 3 run). Against an existing
agent the same value is a no-op and a different value is **rejected** — omit it, match it, or
use a different agent. `dataset_building` additionally requires an `--output-schema` and
effort `high` or above.

`--skill` on a run against an **existing** agent applies to that run only and leaves stored
config untouched. On the call that **creates** the agent, `--skill` and `--use-case` become
its stored configuration instead.

**Run lifecycle:** `queued` → poll `agents:runs get` until terminal (`completed`, `failed`,
`cancelled`) → fetch output with `agents:runs result`. Calling `result` early returns `409`
"Run still active" — go back to `get`, don't hammer `result`. The result's `output` is
`type: "text"` (prose) or `type: "json"` (structured), plus `trust` metadata with per-claim
citations. REST/SDK equivalent: `POST /v2/agents/*`.

**Live progress:** on the CLI, create with `--enable-events` and consume
`nimble agents:runs stream-events --agent-id <id> --run-id <id> [--max-items <n>]`. The stream
closes on its own at a terminal state and never carries the output — still fetch `result`
afterwards. **On MCP, use bounded status polling instead**: poll `nimble_agents_run_status`
every ~15–30s with a capped total wait, and report a run as still active rather than hanging
or calling it failed.

> Full contract (mode table, source shapes, trust metadata, error table):
> `skills/web-search-tools/nimble-web-expert/references/nimble-agents/SKILL.md`.

**Fallback rule:** If neither an Extraction Template nor a Web Search Agent fits, fall
back to `nimble search` + `nimble extract`. Don't fail silently — log which domains
lacked coverage.

### Tasks & batches polling

```bash
# Single async task
nimble tasks get --task-id <task_id>          # check status
nimble tasks results --task-id <task_id>      # fetch results

# Batch
nimble batches progress --batch-id <batch_id> # lightweight progress check
nimble batches get --batch-id <batch_id>      # all task IDs + states
nimble batches list --limit 20                # list all batches
nimble tasks list --limit 20                  # list all tasks
```

**Workflow:** Always `extract:templates get` (or `agents:templates get`) before running,
to understand the expected input params and output fields.

> **Out of scope:** Building or publishing new Extraction Templates / Web Search Agents is
> not part of these skills — use **existing** templates and agents. Point users who need a
> custom template or agent to the Nimble app.

## MCP Fallback (when CLI is not installed)

If `nimble --version` returns "command not found", fall back to the Nimble MCP server.
All CLI commands have MCP equivalents — discover them via the MCP tool list. MCP tools
accept the same parameters as CLI flags, passed as tool arguments instead of flags.

Two Web Search Agent controls are CLI-only, each with a documented MCP alternative:

| CLI-only control          | MCP alternative                                                        |
| ------------------------- | ---------------------------------------------------------------------- |
| `--enable-events` + `agents:runs stream-events` | Bounded `nimble_agents_run_status` polling (~15–30s, capped total wait) |
| `--previous-interaction-id` | Start a fresh run with the prior context restated in `input`          |
| Mode 3 (no agent identity) | Pass an `agent_name` — `nimble_agents_run` requires `agent_id` or `agent_name` |

Modes 1 and 2, `use_case`, `skill`, `sources`, `output_schema`, `input_data`, and `effort`
work the same on both transports.

## Parallel Execution

Make **multiple Bash tool calls in a single response**. Claude Code runs them in
parallel automatically:

- Call 1: `nimble search --query "CompanyA news" --max-results 5 --search-depth lite`
- Call 2: `nimble search --query "CompanyB news" --max-results 5 --search-depth lite`
- Call 3: `nimble search --query "CompanyC news" --max-results 5 --search-depth lite`

## Sub-Agent Spawning

When using the Agent tool for parallel research:

- **Always `mode: "bypassPermissions"`** — sub-agents don't inherit Bash permissions.
- **Batch max 4 agents.** More risk hitting rate limits. For 5+, batch in groups.
- **Tell agents to use Bash** — explicitly say "Use the Bash tool to execute nimble
  commands." Some agents try WebSearch instead.
- **Fallback on failure** — if any agent returns without results, run those searches
  directly from the main context. Don't leave gaps.

## Communication Style

Inform the user at **phase transitions only** with concrete numbers:
- "Researching **Acme Corp** + **5 competitors** since Mar 12..."
- "Found **12 new signals**. Pulling top 4 articles..."
- "All data collected. Building your briefing..."

Don't narrate individual tool calls.

## Rate Limits & Common Errors

- **Rate limit:** 10 req/sec per API key
- **Retry on 429:** Reduce simultaneous calls
- **Timeout:** 30 seconds per request

| Error | Cause | Fix |
|-------|-------|-----|
| `NIMBLE_API_KEY not set` | Missing API key | See `profile-and-onboarding.md` |
| `401 Unauthorized` | Expired key | Regenerate at app.nimbleway.com |
| `429 Too Many Requests` | Rate limit | Fewer simultaneous calls |
| `timeout` | Slow response | Retry once, then skip |
| `500 Server Error` | Transient server failure | Retry once without `--focus`; if persistent, simplify query |
| `empty results` | No matches | Remove `--start-date`, broaden query |

## Signal Date Validation

High-quality intelligence requires distinguishing between when a **page was published**
and when the **underlying event occurred**. This matters because:

- Syndicated or republished content may carry a different publication date than the
  original source
- Secondary coverage (regulatory filings, recap articles, industry roundups) can
  report on events that happened weeks or months earlier

### Article Date vs Event Date

Every signal has two dates:

| | What it is |
|---|---|
| **Article date** | When the page was published |
| **Event date** | When the underlying event actually happened |

A signal is "new" only if its **event date** falls within the freshness window.

### Event Date Extraction Rules

Sub-agents must determine the event date from content:

1. **Explicit past reference** — "launched in Q3", "appointed last October" → event
   date is in the past, regardless of the article date
2. **Temporal language** — "last quarter", "months ago", "earlier this year" → resolve
   relative to the article date
3. **Present tense announcement** — "today announces", "is launching" → event date ≈
   article date
4. **Dateline** — "NEW YORK, March 15 —" → event date = that dateline date
5. **If ambiguous** — extract the source URL and check the on-page date

### Source Type Hierarchy

When the same event appears from multiple sources, prefer those closest to the event:

1. **Primary** — the company's own domain, official press release, regulatory filing
2. **Wire service** — AP, Reuters, Bloomberg
3. **Major outlet** — original reporting with bylines
4. **Derivative** — syndicated copies, aggregator sites, recap articles, or content
   that attributes its information to another source

If the only source for a signal is derivative, corroborate against a primary or major
source before reporting.

### Freshness Classification

After determining the event date, classify each signal:

| Classification | Meaning | Action |
|---|---|---|
| **NEW** | Event date within freshness window, not in memory | Include in report |
| **UPDATED** | Known event with genuinely new information | Include as update |
| **STALE** | Old event covered by a recent article | **DROP — do not include** |
| **UNCERTAIN** | Can't determine event date from snippet alone | Extract URL to verify; if still uncertain after extraction, **DROP** |

**Hard rule:** Only signals classified as **NEW** or **UPDATED** may appear in reports.
STALE and UNCERTAIN signals must be dropped entirely — not downgraded, not footnoted,
not included as "background context." If a signal can't be verified as genuinely recent,
it doesn't exist as far as the report is concerned.

### `--start-date` Best Practices

`--start-date` is a useful filter for reducing noise, but always validate event dates
from the content itself:
- For news queries (`--focus news`), consider running a parallel undated query to
  surface original sources alongside recent coverage
- The existing fallback ("If < 3 results, retry without `--start-date`") remains useful

### Verification Budget

Not every signal needs full verification — budget extract calls by priority:

| Priority | Examples | Verification |
|---|---|---|
| **P1** (high impact) | Funding, M&A, leadership changes | Always extract + corroborate (see below) |
| **P2** (medium impact) | Product launches, partnerships, major hires | Extract if date is UNCERTAIN or source is derivative |
| **P3** (low impact) | Blog posts, minor hires, event appearances | Trust if date looks plausible; drop if obviously stale |

Skills define their own P1/P2/P3 signal types in their SKILL.md. The verification
budget above applies universally regardless of which signals a skill classifies at
each level.

### P1 Corroboration (Mandatory)

Any P1 signal sourced from derivative or aggregator sites **must** be corroborated
before it can appear in a report. This is a hard gate, not a suggestion.

For each P1 signal that needs corroboration:

```bash
nimble search --query "[Company] [event summary]" --max-results 5 --search-depth lite
```

Look for the **primary source** (company blog, press release, official filing, regulatory
document). Check the primary source's date:

- **Primary source dates the event within the freshness window** → signal is NEW, include it
- **Primary source dates the event outside the freshness window** → reclassify as STALE, drop
- **No primary source found** → reclassify as UNCERTAIN, drop

Do not report P1 signals that fail corroboration. It's better to miss a real signal than
to report a stale one as new — trust is the product.

---

## Entity Deduplication

When a skill collects entity records from multiple sources (directories, search results,
extracted pages), deduplicate before reporting. This is distinct from signal-level
differential analysis (see `memory-and-distribution.md`) — entity dedup merges records
for the *same entity* across sources within a single run.

Three-layer pattern (generic — each skill customizes the specifics):

1. **Exact ID match** — If the entity type has a canonical ID (place_id, NPI number,
   domain), match on that first. Exact match = same entity, merge fields.
2. **Domain normalization** — Strip `www.`, trailing slashes, protocol. Compare root
   domains. `www.acme.com/` and `acme.com` are the same entity.
3. **Fuzzy name + location** — Normalize names before comparing:
   - Lowercase all characters
   - Strip titles and honorifics (`Dr.`, `Mr.`, `Ms.`, etc.)
   - Strip credential suffixes (`MD`, `DDS`, `Inc`, `LLC`, `Corp`, etc.)
   - Strip common noise words (`The`, `and`, `of`, `&`)
   - Collapse whitespace and punctuation
   - Compare normalized names with location context if available
   This catches cross-source variations like "Dr. Jane Smith, MD" (Maps) vs
   "Jane Smith" (Yelp) vs "Smith Eye Care LLC" (BBB). Each source formats names
   differently — always normalize before comparing.

Track `source_count` per entity — entities confirmed by multiple sources are higher
quality. Each skill defines which layers apply and any domain-specific matching rules
in its reference files.

---

## Entity Confidence Scoring

Rate each entity's data completeness so users know what to trust.

Generic formula — each skill defines its own target field list (N fields):
- **High** — All target fields found + confirmed by 2+ sources (`source_count >= 2`)
- **Medium** — >50% of target fields found
- **Low** — ≤50% of target fields found

Display the confidence level in output (e.g., `⬤⬤⬤ High`, `⬤⬤○ Medium`,
`⬤○○ Low`). Each skill defines its field list and may add criteria (e.g., requiring
a verified phone number for High in a provider directory skill).

---

## Input Parsing Pattern

Skills that accept batch input (lists of URLs, companies, locations) should detect
the input type automatically:

| Input signature | Type | Action |
|----------------|------|--------|
| Contains `docs.google.com/spreadsheets` | Google Sheet URL | Read sheet directly |
| Path ends in `.csv` and file exists | CSV file | Read and parse as CSV |
| Contains multiple URLs (one per line or comma-separated) | Inline URL list | Parse directly |
| Otherwise | Unknown | Ask user for input |

Normalize all inputs to a uniform list of records before batch processing. Don't
assume a specific format — detect and adapt.

---

## Scaled Execution

When a skill needs to run multiple WSA or API calls, choose the execution tier
based on the estimated number of requests. Each skill calculates its own estimate
from input size and operations per record.

| Estimated calls | Strategy | How |
|----------------|----------|-----|
| **1–10** | Individual calls | Parallel Bash calls (max 4 concurrent) |
| **11–100** | Single batch | `extract-batch` or `extract:templates batch` — one API call, server-side parallelism, poll for results |
| **100–1,000** | Multiple batches | Split into batches of up to 1,000. Use sub-agents to prepare inputs and process results |
| **>1,000** | Confirmation gate + batches | Show estimate, ask user to confirm before proceeding, then execute via batches |

### Individual calls (1–10)

Run up to 4 concurrent Bash calls per the Parallel Execution rules above.

### Batch calls (11+)

**For page extraction (11+ URLs):**
```bash
nimble extract-batch \
  --shared-inputs 'format: markdown' \
  --input '{"url": "https://example.com/page-1"}' \
  --input '{"url": "https://example.com/page-2"}'
```

Add `--shared-inputs 'render: true'` if pages need JavaScript rendering.

**For structured template calls (11+ entities):**
```bash
nimble extract:templates batch \
  --template {template_name} \
  --input '{"params": {...}}' \
  --input '{"params": {...}}'
```

Both return a `batch_id`. Poll progress:
```bash
nimble batches progress --batch-id {batch_id}
```

Fetch results when complete:
```bash
nimble batches get --batch-id {batch_id}
nimble tasks results --task-id {task_id}
```

Batch API handles up to 1,000 requests per call with server-side orchestration.
For >1,000 requests, split into multiple batch calls.

**Sub-agents should also batch.** When spawning sub-agents for parallel work, tell
each agent to use `extract-batch` or `extract:templates batch` for its assigned items
rather than making individual calls. One batch call per agent is faster and more
reliable than 5-6 sequential calls.

### Large job confirmation (>1,000)

Before executing, show the estimate and ask the user to confirm:

```
Estimated API calls: ~2,400 (120 locations × 3 WSAs per location × ~7 enrichment)
This is a large job. Proceed? [Y/n]
```

Pattern: **estimate → display → gate → execute**

### Why batch over individual calls

Individual `nimble extract:templates run` calls each require a separate HTTP round-trip and
Bash tool invocation. At scale (dozens+) this is slow, unreliable, and wasteful
on a local machine. Batch APIs move orchestration server-side — one API call
triggers all requests, and you poll for results. Always prefer batch when above
the individual threshold.

---

## Query Construction Tips

- **Be specific:** "Acme Corp product launch 2026" > "Acme Corp"
- **Use `--include-domain '["domain"]'`** for companies with generic names
- **Fallback on empty:** If < 3 results, retry without `--start-date`
- **Combine focus modes:** news + general in parallel for broader coverage
- **Try variations:** "CompanyName" → "Company Name" → domain

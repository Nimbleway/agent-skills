---
name: web-router-routing-guide
description: |
  PROTOTYPE routing guide for choosing among web tools: search, extract,
  research, and browse. Use when an agent must pick the cheapest/freshest
  path before calling Nimble (or a host web-router), or when designing a
  system prompt that needs an explicit tool-choice matrix.

  Triggers: "which web tool", "route this request", "search vs extract",
  "routing guide", "web router", "should I browse or research",
  "pick a Nimble capability", "tool choice for web data".

  Do NOT use to run scrapes or research yourself — hand off to
  `nimble-web-expert` (or the mapped CLI/MCP tools) after routing.
  Do NOT claim a shipped `webrouter.routing_guide()` API; this skill is a
  design prototype only.
allowed-tools:
  - AskUserQuestion
  - Read
  - Grep
  - Glob
metadata:
  author: Nimbleway
  version: 1.7.0
  category: web-search-tools
  status: prototype
---

# Web Router Routing Guide

**Status: PROTOTYPE.** This skill documents a proposed routing-guide surface.
It does **not** ship a `webrouter.routing_guide()` (or `routing_guide()`) API.
Treat names like `routing_guide()` / `tools()` below as a sketch for host
system prompts and future product work — never as a callable contract.

User request: $ARGUMENTS

## When to use

Use this skill when the agent must **decide which web capability to invoke**
before spending credits or waiting on a long run:

- The user (or an upstream planner) asks which tool fits a prompt.
- You are authoring or reviewing a system prompt that needs a tool-choice matrix.
- A business skill is about to call web data and the intent is ambiguous across
  search / extract / research / browse.

Do **not** use this skill to perform the fetch. After you pick a route, invoke
`nimble-web-expert` (CLI/MCP) — or the host's equivalent tools — with that route.

## Tool-choice matrix

Four conceptual tools. Map them to Nimble (or host) primitives after the decision.

| Tool | Intent signal | Typical Nimble mapping | Returns |
| ---- | ------------- | ---------------------- | ------- |
| **search** | Find pages, links, recent posts, "what's out there" — raw material to skim | `nimble search` | Ranked results / links, not a finished brief |
| **extract** | One known URL (or template+id) to fetch and parse | `nimble extract`, Extraction Templates | Page content or structured records from a known location |
| **research** | Synthesized deliverable: report, compare, enrich, dataset, recommendation with citations | Web Search Agent (`nimble agents` / `agents:runs`) | Finished, cited answer |
| **browse** | Discover structure, interact, or investigate when URL set / selectors / XHR path are unknown | `nimble map`, `nimble crawl`, browser investigation | URL inventory, crawled section, or selector/XHR findings |

### Decision order (keep it short)

1. **Known single URL → extract.** Do not search for a URL you already have.
2. **Named site + direct item (URL/id) → extract path first** (template check, then extract or research if no template). Prefer templates when they exist; do not invent selectors.
3. **Need a finished brief / comparison / enrichment / dataset → research.** Deliverable noun wins over topic vagueness ("report on X" is research even if X is narrow).
4. **Need links / headlines / raw hits to skim → search.**
5. **Need sitemap / section archive / unknown selectors → browse** (`map` / `crawl` / investigation), then extract or research on what you found.
6. **No location signal and no deliverable noun → ask** which outcome they want (links vs page vs report vs discovery) before spending.

Overlap rule (same as `nimble-web-expert`): a named site with **no** Extraction Template is usually **research** (Web Search Agent), not a raw dump extract and not "build a template now."

## Cost / latency / freshness heuristics

**No fake numbers.** Do not invent dollar costs, latency SLOs, or credit tables.
Use qualitative ranks and ask the user when the expensive path is the default.

| Dimension | search | extract | research | browse |
| --------- | ------ | ------- | -------- | ------ |
| **Relative cost** | Lowest among the four for a single shot | Low–medium (rises with render/JS tiers, batches, templates still cheaper than open research) | Highest — multi-step agent work | Medium–high (map cheaper than crawl; interactive investigation costliest browse path) |
| **Relative latency** | Seconds-class | Seconds to low minutes (render/waterfall) | Minutes-class at high effort | Seconds (map) to minutes+ (crawl / browser) |
| **Freshness** | Live index / live SERP — good for "what's new" | Live page fetch — ground truth for that URL | Live multi-source, but synthesized — cite, don't cache as eternal | Live discovery; crawl freshness is "as of run time" |

### Heuristic rules (no metrics)

- Prefer **search** when the user only needs orientation or source candidates.
- Prefer **extract** when the URL (or template identity) is already known — freshest single-source truth at low cost.
- Prefer **research** only when the deliverable requires synthesis or multi-source citation; offer a fork (researched report vs quick search scan) when effort would be high.
- Prefer **browse** only to **unlock** a later extract/research step — never as a default for "tell me about X."
- Prefer **freshness over memory**: do not answer from training data when the user asked for live web state.
- Prefer **cheaper route that still meets the deliverable**; escalate cost only when Gate signals demand it.
- Never quote invented price, p50 latency, or credit counts. If the host exposes real metering, report **that** — otherwise stay qualitative and verbalize trade-offs.

## Example system-prompt block (prototype sketch)

Hosts may paste a block like this. Names are illustrative.

```text
PROTOTYPE — not a shipped API. Do not call webrouter.routing_guide() as a real RPC.

You have a routing guide and a tool surface:

  routing_guide() ->
    Decide among: search | extract | research | browse
    using the tool-choice matrix and cost/latency/freshness heuristics.
    Return: { tool, rationale, next_action }

  tools() ->
    search(query, ...)
    extract(url | template+params, ...)
    research(goal, effort, ...)
    browse(mode=map|crawl|investigate, target, ...)

Procedure:
  1. Call routing_guide() mentally (or via this skill) on the user request.
  2. Invoke exactly one tools() entry matching the decision — unless browse
     is only a discovery step, then chain to extract/research.
  3. If ambiguous, ask before spending on research or crawl.
  4. Never claim routing_guide() is a production webrouter endpoint.
```

## Handoff

After routing, run the chosen path under `nimble-web-expert` (or host MCP/CLI).
For the full Nimble Gate A / Gate B model, read that skill's Analyze & Route
section — this prototype stays at the four-tool abstraction so planners can
share one matrix across Nimble CLI and future web-router hosts.

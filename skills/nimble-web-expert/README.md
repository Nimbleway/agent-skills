# nimble-web-expert

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Get live web data instantly — fetch any URL, scrape structured data, search the web, map sites, and capture XHR APIs. The only way Claude can access live websites.

## What it does

| Task                   | Example                                          |
| ---------------------- | ------------------------------------------------ |
| Fetch a webpage        | "What does this page say?" + URL                 |
| Scrape structured data | "Get all prices from this product listing"       |
| Web search             | "Find recent news about EU AI Act"               |
| Discover site URLs     | "Map all product pages on example.com"           |
| Capture XHR/API data   | "Get the JSON this page loads its listings from" |
| Run Extract Templates | "Get data for Amazon ASIN B08N5WRWNW"          |
| Run Web Search Agents  | "Build a list of every dental clinic in Austin"  |
| Browser investigation  | "Find the CSS selectors on this site"            |

## Requirements

- **Nimble CLI** — installed and authenticated (`nimble --version` to verify)
- **Nimble API key** — [online.nimbleway.com/signup](https://online.nimbleway.com/signup)

## Setup

See [Installation in the root README](../../README.md#installation) for CLI install and API key setup.

### Optional: Nimble Docs MCP (recommended)

Gives Claude direct access to the full Nimble documentation — CLI flags, schemas, API reference.

```bash
claude mcp add --transport http nimble-docs https://docs.nimbleway.com/mcp
```

## How it works

The skill analyzes your request, picks the right command, runs it, and returns the data. No scraper code, no render tier management — that's all handled internally.

| Your request | Command used | What you get back |
| --- | --- | --- |
| Name a specific site (Amazon, Yelp…) | `nimble extract:templates` | Structured data — clean dict or array |
| Open-ended research, enrichment, or dataset building | `nimble agents` / `agents:runs` | Synthesized output with per-claim citations |
| Give a direct URL to scrape | `nimble extract` | HTML, Markdown, or parsed JSON |
| Research a topic or search the web | `nimble search` | Structured results (title, URL, description) |
| Find all URLs / sitemap on a site | `nimble map` | URLs list + metadata |
| Bulk crawl a section of a site | `nimble crawl` | Async job results |

Each command supports multiple output formats — see [docs.nimbleway.com](https://docs.nimbleway.com) for the full flag reference.

**Key rules:**

- Always checks for an Extract Template before extracting from a named site (Amazon, Walmart, Yelp, and many more)
- One command → results → done. No looping or retrying
- Escalates render tiers silently — only asks when investigation tools are needed
- Never answers from training data — always fetches live

## Reference files

| File                                                 | Purpose                                                       |
| ---------------------------------------------------- | ------------------------------------------------------------- |
| `references/recipes.md`                              | Ready-to-run commands for 20+ popular sites                   |
| `references/error-handling.md`                       | Common errors and fixes                                       |
| `references/nimble-extract/reference.md`                 | Full `nimble extract` flag reference                          |
| `references/nimble-extract/parsing-schema.md`        | Parser schema and CSS selector patterns                       |
| `references/nimble-extract/browser-actions.md`       | Click, scroll, wait action sequences                          |
| `references/nimble-extract/browser-investigation.md` | Tier 6 — finding selectors/XHR with browser-use or Playwright |
| `references/nimble-extract/network-capture.md`       | XHR/API interception patterns                                 |
| `references/nimble-search/reference.md`                  | `nimble search` flag reference                                |
| `references/nimble-search/search-focus-modes.md`     | 8 focus modes (news, web, jobs, etc.)                         |
| `references/nimble-map/reference.md`                     | `nimble map` URL discovery reference                          |
| `references/nimble-crawl/reference.md`                   | `nimble crawl` bulk extraction reference                      |
| `references/nimble-extract-templates/reference.md`       | Extract Templates — discover, inspect, and run site scrapers |
| `references/nimble-agents/reference.md`                  | Web Search Agents — discovery, run lifecycle, trust/citations  |

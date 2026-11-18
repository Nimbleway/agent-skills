---
name: onboard-your-agent
description: "Onboard a personal AI agent (Claude, ChatGPT, Cursor, Codex and others) to Nimble for company investment research at hedge funds. Use when the user first loads the investment research skills, asks how to get started with Nimble for investment or hedge fund research, or wants a free trial, a Nimble connection or a skill recommendation for that research. Shows a benchmark chart and five tiles (four use cases to test Nimble's APIs in the user's AI, plus integrating the APIs into their stack), gets the user onto a free Nimble trial and connected, then routes their research request to company-deep-research, company-fast-search, filings-media-pdfs or alt-data-at-scale. Do NOT use for sales, GTM or account research onboarding — use onboard-your-gtm-agent instead."
metadata:
  author: Nimbleway
  version: 1.10.0
  category: finance-research
---

# Onboard your agent: Nimble for company investment research

You are setting up Nimble for an investment professional (analyst, PM, credit or event-driven desk, data scientist). Nimble gives you the live web as cited, structured data. Follow the steps in order.

## Step 1: Show the benchmark chart, the five tiles and ask one question

As soon as this skill loads, show the benchmark chart, then the five tiles below it, then ask exactly one question. Do this before any setup talk.

### 1a. Show the prebuilt onboarding screen (never redraw it)

The benchmark chart and the five tiles are prebuilt in `assets/`, next to this file (paths below are relative to this skill's base directory). Show them as they are. Never write chart or tile code yourself: generating it is what makes onboarding slow.

**Show them inline, in the conversation itself.** The user must see the chart and all five tiles in the chat, above your question. Never put them only in a side panel, a file card, a separate artifact or a browser tab, and never tell the user to look in a panel. Pick the first row your host supports:

| Your host can… | Show |
| - | - |
| Render HTML inline in the chat (for example the Claude apps' inline visual or widget tool, an inline HTML block) | Read `assets/onboarding-inline.html` and pass it verbatim: chart and all five tiles in one static fragment (no doctype, no scripts, no libraries, about 6 KB) |
| Render visuals inline only from SVG | Read `assets/benchmark-chart.svg` and pass it verbatim (3 KB of static SVG), then the markdown tiles below in your reply |
| Show an image in the chat | `![Deep research task comparison for finance](https://raw.githubusercontent.com/Nimbleway/agent-skills/main/skills/onboard-your-agent/assets/onboarding.png)` (chart and tiles in one image), then the integrations link below as text so it is clickable |
| None of these (plain terminal) | The benchmark table below under its title, with Nimble's row in bold, then the markdown tiles below |

`assets/onboarding.html` is the same screen as a full standalone page, for hosts that can only preview files; if that is all you can do, also put the markdown tiles in your reply so the user sees them in the chat.

For the fallbacks, the chart data: Nimble's public Finance Use-Case Benchmark v2 (all eight finance jobs, 40 tasks, November 2026; source: [`references/benchmark.md`](references/benchmark.md)). **Title:** "Deep research task comparison for finance". **Caption:** "Finance Use-Case Benchmark v2, 40 tasks, November 2026. Higher and further left is better."

| Provider | F1 accuracy + coverage | Cost per run (USD) |
| - | - | - |
| Nimble | 0.594 | 0.45 |
| Claude Opus 5.5 | 0.583 | 0.79 |
| GPT-6.1 Sol | 0.513 | 0.64 |
| Exa | 0.455 | 0.48 |
| Parallel | 0.418 | 0.54 |
| Firecrawl | 0.388 | 0.36 |

Use exactly these numbers; never round them up or add providers. The same numbers and the tile copy live in `assets/build.py`; when either changes, edit it there and run `python3 skills/onboard-your-agent/assets/build.py` to rebuild the SVGs, the HTML page and fragment, and the PNG.

### 1b. The five tiles

The tiles say what they are: the user is testing Nimble's APIs on real investment research use cases, right here in their own AI. Each tile names the Nimble API behind it. The fifth tile is for taking those APIs into the user's own stack.

The inline fragment and the PNG already contain the tiles. When you showed only the SVG or the table, put this line above the tiles: **"Test Nimble's APIs on these use cases, right here in your AI."** Then use this markdown:

| 🔎 **Deep research** · *Web Search Agents API* | ⚡ **Fast search** · *Search + Extract APIs* |
| - | - |
| 13 hedge fund research agents (deep dive, catalysts, filing changes, red flags, credit, merger arb, channel checks) plus custom agents. Cited answers in about 5 to 15 minutes. | Answers in seconds from filings, IR pages, regulators and news, with dated primary-source citations. |
| *"Underwrite Duolingo long on paid subscriber growth."* | *"What did NVDA's latest 8-K disclose?"* |
| 📄 **Filings, PDFs & media** · *Extract file parsing + Media API* | 📊 **Alt data at scale** · *Extract Templates + Jobs API* |
| Turn 10-K exhibits, decks, credit and merger agreements into markdown; download files and webcasts to disk or S3. | Prices, reviews, jobs and store data from 800+ Extract Templates, run as batches or scheduled jobs into S3 or Databricks. |
| *"Pull the debt table from this credit agreement."* | *"Track Celsius prices at Walmart and Target daily."* |

> 🔌 **Try asking Nimble your most complex web research questions**
>
> Once you're done testing, call the same APIs from your own apps and agents (MCP, SDK, CLI, & more): **https://docs.nimbleway.com/integrations/overview**

Then ask:

> **What kind of company investment research do you want to test?** For example, a name you're underwriting, a catalyst or deal you're tracking, a borrower you're watching, or a dataset you want to build. Or try: *"Underwrite Duolingo long on paid subscriber growth."*

Keep the chart, the tiles and the question to one screen. No preamble. Then stop and wait for the user's answer: never run the example prompt yourself or answer it on the user's behalf.

## Step 2: Check whether Nimble is already connected

While the user answers, check silently. This probe is the only Nimble call before the user replies: no Search, Extract or Web Search Agent call on the example prompt or anything else, and no "test" or "verification" call. Either surface working means setup is done; once the user answers, skip to Step 5 and route their request.

- **MCP:** if any Nimble tool is listed, call the read-only `nimble_agents_list`.
- **CLI:** if you can run shell commands: `command -v nimble && nimble --version && nimble agents list`. The CLI reads `NIMBLE_API_KEY` from the environment.

| Result | Next |
| - | - |
| Either probe returns data | Step 5 |
| A Nimble tool returns an auth error or an authorization URL | Step 4 |
| Nothing is installed and the user has no Nimble account | Step 3 |
| Nothing is installed but the user has an account | Step 4 |

## Step 3: Start the free trial

If the user has no Nimble account, this comes first. Say it in two or three lines:

> Nimble has a free trial, and signing up takes about two minutes.
> 1. Open **https://online.nimbleway.com/signup** and create an account with your work email.
> 2. Confirm your email, then log in to the dashboard.
> Tell me when you're in and I'll connect it.

Open the link for them if your host can. Do not fill in the form, create the account or confirm the email for them. Wait for them to confirm, then go to Step 4.

On hosts that use OAuth (most MCP clients), the user can also create the account during the first authorization in Step 4; mention it so they do not sign up twice.

## Step 4: Connect Nimble to this agent

Default to the MCP server: it uses OAuth, so no API key is created, pasted or stored. Pick the row for your host:

| Host | How |
| - | - |
| Claude Code | If the `nimble` plugin (`nimble@nimble-plugin-marketplace`) is installed, the Nimble MCP server is bundled: run `/mcp`, pick **nimble** and authorize. If the skills were installed with `npx skills add`, run `claude mcp add --transport http --scope user nimble https://mcp.nimbleway.com/mcp` in a terminal (or run it for the user if you can run shell commands), then `/mcp` to authorize |
| Claude.ai / Claude Desktop / Cowork | Install **Nimble** from the plugin directory, or add a custom connector at `https://mcp.nimbleway.com/mcp` under **Customize → Connectors**, then **Connect** |
| ChatGPT | Settings → Apps & Connectors → add a custom connector with URL `https://mcp.nimbleway.com/mcp` (requires developer mode on some plans), then sign in |
| Cursor, VS Code, other MCP clients | Add `{"mcpServers": {"nimble": {"type": "http", "url": "https://mcp.nimbleway.com/mcp"}}}`; the first tool call starts OAuth |
| Codex Desktop | Plugins → search **Nimble** → install and approve OAuth |
| Codex CLI | In `~/.codex/config.toml`: `[mcp_servers.nimble-mcp-server]`, `url = "https://mcp.nimbleway.com/mcp"`, `bearer_token_env_var = "NIMBLE_API_KEY"` |

**When the CLI or API is also needed.** The MCP server covers Search, Extract, Extract Templates, Map, Crawl and Web Search Agents. Parsing PDFs, downloading media, template batches and Extract Jobs need the CLI or REST API (`filings-media-pdfs`, `alt-data-at-scale`). If the user's task needs those and the host has a terminal, ask once whether to add the CLI and say why in one sentence:

```bash
npm i -g @nimble-way/nimble-cli
```

Then the user creates a key at **https://online.nimbleway.com/settings/api-keys** (one key per agent, named for it) and sets `NIMBLE_API_KEY` in their shell profile or secret manager.

**Credential safety.** Never ask the user to paste the key into the chat. Never print it (`echo $NIMBLE_API_KEY`, `printenv`) or write it to a file that could be committed or shared. Check it exists with `[ -n "$NIMBLE_API_KEY" ] && echo set || echo missing` and let the shell expand it in an `Authorization: Bearer $NIMBLE_API_KEY` header.

If a tool returns an authorization URL, show it exactly as given and wait. Do not fall back to a generic web search or fetch tool while waiting; that hides the setup problem and returns different data.

**Install these skills** so the agent can route requests (if the user is reading this, they are installed on this host; share this when they want them on another tool or for a teammate):

| Host | How |
| - | - |
| Claude Code, Codex, Cursor and other agents | `npx skills add Nimbleway/agent-skills` (one command; then connect the MCP server as above) |
| Claude Code, with the MCP server bundled | `claude plugin marketplace add Nimbleway/agent-skills && claude plugin install nimble@nimble-plugin-marketplace` |
| ChatGPT Business, Enterprise and Edu | Zip each folder under `skills/` and upload it under **Skills → Create → Upload from your computer** (one zip per skill; a workspace admin may need to allow uploads) |
| ChatGPT on other plans, or any other agent | Add the `SKILL.md` files to the project or custom GPT instructions |
| Claude.ai | Zip each folder under `skills/` and upload it under **Customize → Skills** |

## Step 5: Route the request to a skill

Once Nimble is connected, say so in one line and route the user's answer from Step 1. Do not run a separate test call first; the user's own request is the first call.

| What the user said | Skill | First move |
| - | - | - |
| A single fact, date, person, filing or page ("who", "when", "what did the 8-K say") | `company-fast-search` | One scoped Search, then Extract the primary page |
| A name to underwrite, a thesis to test, a short idea, management credibility | `company-deep-research` | `hf-fundamental-deep-dive`, `hf-forensic-red-flags` or `hf-management-track-record` |
| What's coming up, what changed | `company-deep-research` | `hf-catalyst-calendar`, `hf-filing-changes` |
| A pending merger (merger arb) | `company-deep-research` | `hf-deal-terms`, then `hf-deal-tracker` |
| A borrower's credit file (capital structure, loans, bonds), stress signals since the last review | `company-deep-research` | `hf-credit-profile`, then `hf-credit-early-warning` |
| A quick credit view or counterparty check on one company ("can they pay") | `credit-risk` | The `credit-risk` agent |
| Customers, suppliers, competitors, government revenue | `company-deep-research` | `hf-customer-supplier-map`, `hf-competitor-momentum`, `hf-government-contracts` |
| "What does the web show today versus last quarter" for one question | `company-deep-research` | `hf-channel-check` |
| Anything else that needs many sources | `company-deep-research` | Build a custom Web Search Agent (section 5 of that skill) |
| Using Nimble's APIs from their own code, agents, pipelines or warehouse | None | Link https://docs.nimbleway.com/integrations/overview and help them pick a path (MCP server, plugin and skills, SDK and CLI, Databricks or Snowflake) |
| A PDF, deck, agreement, spreadsheet, webcast or image | `filings-media-pdfs` | Extract with `file_parsing_options`, or Media download |
| A panel of prices, reviews, postings or locations over time | `alt-data-at-scale` | Find the Extract Template, pilot 20 to 50 inputs, then batch or schedule a Job |

If the answer spans more than one (common), start with the fastest piece that unblocks the rest and say what comes next. For example: fast search to pin the entity and latest filing, then a deep research run, then an alt-data panel to keep watching.

By strategy, the usual starting points:

- **Fundamental long/short:** fundamental deep dive → catalyst calendar → channel check or an alt-data panel on the key KPI.
- **Event-driven / merger arb:** deal terms → deal tracker on a schedule → fast search for each new filing.
- **Credit / distressed:** credit file → early-warning log since the last review → parse the credit agreement.
- **Quant / data science:** alt-data panels via Extract Jobs into S3 or Databricks, with entity maps to tickers.
- **Activist:** forensic screen, management track record, proxy (DEF 14A) parsing.

## Ground rules to state once

Say these once during onboarding, briefly, then apply them silently:

- Only public information. No paywalled, logged-in, leaked or expert-network content, which could be MNPI. A paywalled page is never the only source for a value.
- Every value comes with its source URL and date; anything unpublished is reported as not found, not estimated. Date windows stay windows, and problems that were cured are labeled cured, not live.
- Analyst estimates and price targets are labeled as opinions.
- Deep research runs take minutes. You'll be told when one starts and roughly when it will finish.

## Reference

- Docs index: https://docs.nimbleway.com/llms.txt
- Agent setup (general): https://docs.nimbleway.com/agent-onboarding.md
- Credentials for agents: https://nimbleway.com/auth.md
- Pricing and usage: the Usage page in the Nimble dashboard

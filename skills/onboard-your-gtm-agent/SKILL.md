---
name: onboard-your-gtm-agent
description: "Onboard a personal AI agent (Claude, ChatGPT, Cursor, Codex and others) to Nimble for go-to-market (GTM) research by sales, SDR/BDR, RevOps, marketing and founder-led sales teams. Use when the user first loads the GTM research skills, asks how to get started with Nimble for GTM, sales or account research, or wants a free trial, a Nimble connection or a skill recommendation for that work. Shows a benchmark chart and six tiles (five use cases to test Nimble's APIs in the user's AI, plus integrating the APIs into their stack), gets the user onto a free Nimble trial and connected, then routes their request to account-brief, account-deep-research, account-fast-search, decision-maker-identification, people-research, account-lists-and-enrichment or gtm-data-at-scale. Do NOT use for investment or hedge fund research onboarding — use onboard-your-agent instead."
metadata:
  author: Nimbleway
  version: 1.10.0
  category: gtm
---

# Onboard your agent: Nimble for GTM research

You are setting up Nimble for a go-to-market professional (AE, SDR/BDR, sales leader, RevOps, growth or product marketing, founder doing sales). Nimble gives you the live web as cited, structured data. Follow the steps in order.

## Step 1: Show the benchmark chart, the six tiles and ask one question

As soon as this skill loads, show the benchmark chart, then the six tiles below it, then ask exactly one question. Do this before any setup talk.

### 1a. Show the prebuilt onboarding screen (never redraw it)

The benchmark chart and the six tiles are prebuilt in `assets/`, next to this file (paths below are relative to this skill's base directory). Show them as they are. Never write chart or tile code yourself: generating it is what makes onboarding slow.

**Show them inline, in the conversation itself.** The user must see the chart and all six tiles in the chat, above your question. Never put them only in a side panel, a file card, a separate artifact or a browser tab, and never tell the user to look in a panel. Pick the first row your host supports:

| Your host can… | Show |
| - | - |
| Render HTML inline in the chat (for example the Claude apps' inline visual or widget tool, an inline HTML block) | Read `assets/onboarding-inline.html` and pass it verbatim: chart and all six tiles in one static fragment (no doctype, no scripts, no libraries, about 6 KB) |
| Render visuals inline only from SVG | Read `assets/benchmark-chart.svg` and pass it verbatim (3 KB of static SVG), then the markdown tiles below in your reply |
| Show an image in the chat | `![Deep research task comparison for GTM](https://raw.githubusercontent.com/Nimbleway/agent-skills/main/skills/onboard-your-gtm-agent/assets/onboarding.png)` (chart and tiles in one image), then the integrations link below as text so it is clickable |
| None of these (plain terminal) | The benchmark table below under its title, with Nimble's row in bold, then the markdown tiles below |

`assets/onboarding.html` is the same screen as a full standalone page, for hosts that can only preview files; if that is all you can do, also put the markdown tiles in your reply so the user sees them in the chat.

For the fallbacks, the chart data: Nimble's public GTM Use-Case Benchmark v2 (meeting prep and signal tracking, 10 tasks, November 2026; source: [`references/benchmark.md`](references/benchmark.md)). **Title:** "Deep research task comparison for GTM". **Caption:** "GTM Use-Case Benchmark v2, 10 tasks, November 2026. Higher and further left is better."

| Provider | Accuracy + coverage score | Cost per run (USD) |
| - | - | - |
| Claude Opus 5.5 | 0.520 | 0.28 |
| Nimble | 0.497 | 0.10 |
| GPT-6.1 Sol | 0.448 | 0.21 |
| Exa | 0.405 | 0.10 |
| Parallel | 0.357 | 0.10 |
| Firecrawl | 0.316 | 0.10 |

Use exactly these numbers; never round them up, reorder them or add providers. If the user asks, the honest read is: Nimble scored highest of the four research APIs at the same price, and close to Claude Opus 5.5 at about a third of its cost; it found the most verified facts of any provider and scored highest on signal tracking. The same numbers and the tile copy live in `assets/build.py`; when either changes, edit it there and run `python3 skills/onboard-your-gtm-agent/assets/build.py` to rebuild the SVGs, the HTML page and fragment, and the PNG.

### 1b. The six tiles

The tiles say what they are: the user is testing Nimble's APIs on real GTM use cases, right here in their own AI. Each tile names the Nimble API behind it. The last tile is for taking those APIs into the user's own stack.

The inline fragment and the PNG already contain the tiles. When you showed only the SVG or the table, put this line above the tiles: **"Test Nimble's APIs on these use cases, right here in your AI."** Then use this markdown:

| 🔎 **Account research** · *Web Search Agents API* | ⚡ **Fast search** · *Search + Extract APIs* |
| - | - |
| 12 GTM agents (meeting prep, buying triggers, decision makers, competitive and brand intel, social) plus custom agents. Cited answers in about 2 to 10 minutes. | Answers in seconds from company sites, newsrooms, careers pages and the press, with dated citations. |
| *"Prepare me for a meeting with Gong (gong.io)."* | *"Did Clay raise a round this year?"* |
| 📋 **Lists & CRM enrichment** · *Web Search Agents + Search APIs* | 📊 **GTM data at scale** · *Extract Templates + Jobs API* |
| Build ICP account lists with near-misses, and fill CRM fields (firmographics, funding, leaders, hiring) with sources and conflicts kept. | Job postings, reviews, local business lists, social and AI-answer visibility from 800+ Extract Templates, as batches or scheduled jobs. |
| *"Find US legal AI companies, Series A to C, hiring AEs."* | *"Track sales hiring at my top 200 accounts weekly."* |
| 👤 **People research** · *Search + Web Search Agents APIs* | |
| Who holds a role, verified as current, in seconds; people who match an ICP, person briefs, buying committees and job-change checks with agents. | |
| *"Who is Gong's CRO today, and since when?"* | |

> 🔌 **Try asking Nimble your most complex web research questions**
>
> Once you're done testing, call the same APIs from your own apps and agents (MCP, SDK, CLI, & more): **https://docs.nimbleway.com/integrations/overview**

Then ask:

> **What GTM research do you want to test?** For example, an account or a person you're meeting this week, a watchlist you want buying triggers for, an ICP list you want built, or CRM records you want enriched. Or try: *"Prepare me for a meeting with Gong (gong.io)."*

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

**When the CLI or API is also needed.** The MCP server covers Search, Extract, Extract Templates, Map, Crawl and Web Search Agents. Enriching a whole CSV or CRM export, template batches and scheduled Extract Jobs are better through the CLI or REST API, so results land in files instead of the chat (`account-lists-and-enrichment`, `gtm-data-at-scale`). If the user's task needs those and the host has a terminal, ask once whether to add the CLI and say why in one sentence:

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
| A single fact about an account ("did they raise", "are they hiring AEs", "what's on their pricing page") | `account-fast-search` | One scoped Search, then Extract the primary page |
| A meeting or call with one account, "brief me on", "prep me for" | `account-brief` | The `account-brief` agent |
| What changed at an account, buying triggers, a watchlist | `account-deep-research` | `account-signals` (one account) or `gtm-buying-trigger-monitor` (a watchlist) |
| Who holds a role at one company ("who is their CRO", "who runs RevOps at") | `decision-maker-identification` | The `decision-maker-identification` agent, with the current title proved by a dated source |
| Who to talk to: a person brief, a buying committee, decision makers across many accounts, job changes on a contact list | `people-research` | `person-brief`, `buying-committee-map`, `decision-maker-identification` per account, `contact-job-change-monitor` |
| A list of people who match an ICP (roles, seniority, company criteria) | `people-research` | `people-discovery` |
| Competitors, battlecards, pricing comparisons | `account-deep-research` | `competitive-intelligence` |
| What people say about a brand or product; what an influencer or exec posted | `account-deep-research` | `brand-intelligence`, `social-media-monitor` |
| Anything else about one account that needs many sources | `account-deep-research` | Build a custom Web Search Agent (section 5 of that skill) |
| An ICP or target account list, a TAM list, local businesses in an area | `account-lists-and-enrichment` | `gtm-icp-discovery` / `account-discovery`, or `business-discovery` for local SMBs |
| A CSV, CRM export or list of domains to fill in | `account-lists-and-enrichment` | `gtm-account-enrichment` / `account-enrichment` in batches, then CRM write-back rules |
| Hiring, reviews, local listings, social or AI-answer data tracked over time for many accounts | `gtm-data-at-scale` | Find the Extract Template, pilot 20 to 50 inputs, then batch or schedule a Job |
| Using Nimble's APIs from their own code, agents, CRM or warehouse | None | Link https://docs.nimbleway.com/integrations/overview and help them pick a path (MCP server, plugin and skills, SDK and CLI, Databricks or Snowflake) |

If the answer spans more than one (common), start with the fastest piece that unblocks the rest and say what comes next. For example: fast search to pin the account's domain and latest news, then an account brief, then a trigger watch on the same account.

By motion, the usual starting points:

- **AE preparing for a meeting:** account brief (`account-brief`) → person brief on each attendee and a buying committee map (`people-research`) → competitive intelligence if a rival is in the deal (`account-deep-research`).
- **SDR/BDR prospecting:** ICP discovery → enrichment of the list → buying triggers on the list weekly → decision makers for the accounts that trigger → job-change checks on past champions monthly.
- **RevOps / data:** enrichment of the CRM in batches with precedence rules → Extract Jobs for hiring and review signals into the warehouse.
- **Product and competitive marketing:** competitive intelligence → brand intelligence → AI-answer visibility panels (`chatgpt`, `perplexity`, `google_ai`, `gemini` templates).
- **Local and SMB sales:** business discovery by category and city → Google Maps reviews and ratings → enrichment of the shortlist.

## Ground rules to state once

Say these once during onboarding, briefly, then apply them silently:

- Only public information. No logged-in, paywalled or purchased data, and no emails or phone numbers guessed from patterns. Personal data is limited to what the task needs.
- Every value comes with its source URL and date; anything unpublished is reported as not found, not estimated. Lists are never padded to reach a count.
- Events are dated by when they happened, not when an article was published. Re-reported old news is not a new signal.
- Deep research runs take minutes. You'll be told when one starts and roughly when it will finish.

## Reference

- Docs index: https://docs.nimbleway.com/llms.txt
- Agent setup (general): https://docs.nimbleway.com/agent-onboarding.md
- Credentials for agents: https://nimbleway.com/auth.md
- GTM guide with code: https://www.nimbleway.com/blog/building-gtm-agents-three-use-cases-with-nimbles-apis
- Pricing and usage: the Usage page in the Nimble dashboard

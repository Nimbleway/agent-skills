---
name: portfolio-monitoring
description: |
  Lists material events at a holding since a date: exec changes, litigation, rating
  actions, guidance and defaults, with why each one matters, using the Nimble
  `portfolio-monitoring` agent template on live web data. Use when the user says "what
  happened at [holding]", "monitor my portfolio", "material events", "check my holdings
  since", "portfolio news", or arrives from a Nimble use-case page. Interviews the user
  for the inputs, shows quick search results first, then runs the template at medium and
  high effort and shows each result as it arrives. Do NOT use for sales accounts (use
  account-signals) or a full credit view (use credit-risk).
allowed-tools:
  - Bash(nimble:*)
  - Bash(claude mcp list)
  - Bash(npm --version)
  - Bash(npm install -g @nimble-way/nimble-cli)
  - Bash(npm i -g @nimble-way/nimble-cli)
  - Read
  - Write
  - AskUserQuestion
  # Quick first pass with the host's own search, and reading the hosted docs:
  - WebSearch
  - WebFetch
  # Nimble MCP (agent templates and runs):
  - mcp__plugin_nimble_nimble__nimble_search
  - mcp__plugin_nimble_nimble__nimble_agent_templates_list
  - mcp__plugin_nimble_nimble__nimble_agent_templates_get
  - mcp__plugin_nimble_nimble__nimble_agents_list
  - mcp__plugin_nimble_nimble__nimble_agents_get
  - mcp__plugin_nimble_nimble__nimble_agents_create
  - mcp__plugin_nimble_nimble__nimble_agents_run
  - mcp__plugin_nimble_nimble__nimble_agents_run_status
  - mcp__plugin_nimble_nimble__nimble_agents_run_result
  - mcp__plugin_nimble_nimble__nimble_agents_runs_list
metadata:
  author: Nimbleway
  version: 1.9.0
  category: finance-research
---

# Portfolio monitoring

Lists material events at a holding since a date: exec changes, litigation, rating actions, guidance and defaults, with why each one matters.

User request: $ARGUMENTS

## What the user gets

Only material events after the since date, each dated and cited, with why it matters. If nothing material happened, an empty list and the sources it checked.

## Agent template

This skill runs the Nimble gallery template `portfolio-monitoring`. The agent's instructions, sources and output schema live in the template. Do not rewrite them in the run.

Effort is the user's choice. By default this skill runs it twice, at medium (2-4 minutes, $0.10) and high (5-15 minutes, $0.50), so the user sees results early and the full result later. The template's own default is medium. If the user asks for a specific effort (low, medium, high, x-high or max), run only that one.

## Flow

The user should never wait minutes with nothing on screen. Work in three steps and show a progress line at the start of each:

```
[■□□] Step 1 of 3 · Preliminary quick results
[■■□] Step 2 of 3 · Deeper research
[■■■] Step 3 of 3 · Full deep research results
```

Start connecting Nimble right away, but do not wait on it.

### Connect Nimble

If Nimble tools are listed in this session, call `nimble_agents_list`. Data back means the user is connected. Say nothing and go on.

If not, ask the user to connect Nimble, in one line on why: "Nimble runs the full research on live sources, with a source for every field. Connecting takes one approval, and new accounts start with a free trial." Then follow https://docs.nimbleway.com/agent-onboarding.md. Do the setup yourself and involve the user only for the approval. Never ask the user to paste an API key into the chat.

### Get the inputs

| Input | Required | Ask for | If skipped |
|---|---|---|---|
| Holdings | yes | Names or tickers, or a list | - |
| Since | no | A date in YYYY-MM-DD | 30 days ago |
| Materiality rule | no | For example "ignore product launches" | the template's default |

- Take anything the user already said. Ask only for what is missing.
- If your host has a form or multiple-choice question tool, use it, with the required inputs first and the optional ones marked optional. Otherwise ask in one short message.
- Do not hold up the run for optional inputs. Use the "If skipped" value.
- Do not ask about effort. Use it only if the user brings it up.

Build the agent input from this pattern:

```
Check <Company> (<ticker>) for material events since <YYYY-MM-DD>
```

Example: `Check Boeing for material events since 2026-09-21`

- One holding per run. For a portfolio, one run per holding in parallel.
- If they have their own materiality rule, add one line to the input.

### Start both agent runs

As soon as Nimble is connected and you have the required inputs, start the agent runs before anything else, so they work while you do step 1:

1. Create the agent from the template: `nimble_agents_create(template="portfolio-monitoring", agent_name="portfolio-monitoring")`. A 409 "already exists" means it was created before, so go on. If the template is not found, tell the user it is unavailable and stop. Do not substitute another template.
2. Start two runs on the same input: `nimble_agents_run(agent_name="portfolio-monitoring", input="<the input>", effort="medium")` and the same with `effort="high"`. Leave schema and skill to the template. If the user chose an effort, start one run at that effort and number the steps 1 of 2 and 2 of 2.
3. Tell the user once, in one line, what is running: "Running a quick search now, a deeper Nimble run (2-4 min) and a full one (5-15 min). This uses 2 agent runs."

### Step 1 of 3 · Preliminary quick results

Turn their idea of material into a clear rule, and tell them anything you can find that happened, with dates. Use a few quick searches, not the agents: `nimble_search` if Nimble is connected, otherwise your own web search tool. Keep it under a minute and short. Link every fact, and mark anything from memory with your knowledge cutoff.

End with one line on what is coming next. If Nimble is still not connected, say the deeper steps start once it is, and offer the connect step again.

### Step 2 of 3 · Deeper research

Poll both runs with `nimble_agents_run_status` every 20-30 seconds. When the medium run finishes, get `nimble_agents_run_result` and show it:

- A short table or brief, not raw JSON. Lead with the 2-3 most useful facts, each with its source link.
- Point out what is new or different from step 1.
- Say what is missing (empty fields, `missing_fields`, empty lists).
- End with one line: the full run is still going and about how long it has left.

### Step 3 of 3 · Full deep research results

When the high run finishes, show its result the same way. Lead with what it added or corrected compared with step 2, then the full result. This is the answer the user keeps.

If a run finishes with no output and no sources, retry it once. Do not retry a run that returned data. If the medium run fails, or the high run finishes first, go straight to step 3 and do not show the medium result after it.

### Next steps

Offer, one line each, what fits:
- **Run it on a list.** One run per record in parallel. See [Running at scale](https://docs.nimbleway.com/nimble-sdk/web-search-agents/best-practices/running-at-scale.md).
- **Schedule it.** Use the host's scheduler or a cron job, and pass the last run date as the new since date where the input has one.
- **Use it from code.** The agent is saved as `portfolio-monitoring`. Give a short Python or TypeScript snippet that runs it by name.

## Using Nimble well

Read the page you need, when you need it: [writing the task](https://docs.nimbleway.com/nimble-sdk/web-search-agents/best-practices/writing-the-task.md), [sources](https://docs.nimbleway.com/nimble-sdk/web-search-agents/best-practices/sources.md), [effort and cost](https://docs.nimbleway.com/nimble-sdk/web-search-agents/best-practices/effort-and-cost.md), [evaluating results](https://docs.nimbleway.com/nimble-sdk/web-search-agents/best-practices/evaluating-results.md), [running at scale](https://docs.nimbleway.com/nimble-sdk/web-search-agents/best-practices/running-at-scale.md), [common mistakes](https://docs.nimbleway.com/nimble-sdk/web-search-agents/best-practices/common-mistakes.md).

## Pitfalls

- An empty list can be the right answer. Show the sources checked.
- Events on the since date itself can slip in. Keep only events strictly after it.
- Materiality is a judgement. Let the user tighten the rule.

## Rules

- Never invent values. Show missing fields as missing.
- Never print or log an API key.

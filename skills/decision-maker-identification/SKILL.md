---
name: decision-maker-identification
description: |
  Finds the people who hold given roles at a company today, with current title, career
  history and the source that proves it, using the Nimble `decision-maker-identification`
  agent template on live web data. Use when the user says "who is the CFO at", "find the
  head of X at", "find the buying committee", "decision makers at", "who runs RevOps at",
  "find contacts at", or arrives from a Nimble use-case page. Interviews the user for the
  inputs, shows quick search results first, then runs the template at medium and high
  effort and shows each result as it arrives. Do NOT use to fill company-level fields (use
  account-enrichment). It never returns emails or phone numbers.
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
  category: gtm
---

# Decision-maker identification

Finds the people who hold given roles at a company today, with current title, career history and the source that proves it.

User request: $ARGUMENTS

## What the user gets

For each role, the person who holds it now: name, exact title, start date, previous roles, public profiles and a dated source. Roles it cannot confirm are listed as missing.

## Agent template

This skill runs the Nimble gallery template `decision-maker-identification`. The agent's instructions, sources and output schema live in the template. Do not rewrite them in the run.

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
| Company | yes | Name and domain (or a list of them) | - |
| Roles | yes | Up to about 5, for example "CFO, head of RevOps, VP engineering" | - |

- Take anything the user already said. Ask only for what is missing.
- If your host has a form or multiple-choice question tool, use it, with the required inputs first and the optional ones marked optional. Otherwise ask in one short message.
- Do not hold up the run for optional inputs. Use the "If skipped" value.
- Do not ask about effort. Use it only if the user brings it up.

Build the agent input from this pattern:

```
At <Company> (<domain>), find the current <role 1>, <role 2>, <role 3>
```

Example: `At Gong, find the current CTO, CMO, head of revenue operations and CFO`

- One company per run. For a list, one run per company in parallel.
- Use the title the company would use. "Head of RevOps" finds more than "Revenue Operations Leader".
- If they ask for emails or phone numbers, say up front that it does not return them.

### Start both agent runs

As soon as Nimble is connected and you have the required inputs, start the agent runs before anything else, so they work while you do step 1:

1. Create the agent from the template: `nimble_agents_create(template="decision-maker-identification", agent_name="decision-maker-identification")`. A 409 "already exists" means it was created before, so go on. If the template is not found, tell the user it is unavailable and stop. Do not substitute another template.
2. Start two runs on the same input: `nimble_agents_run(agent_name="decision-maker-identification", input="<the input>", effort="medium")` and the same with `effort="high"`. Leave schema and skill to the template. If the user chose an effort, start one run at that effort and number the steps 1 of 2 and 2 of 2.
3. Tell the user once, in one line, what is running: "Running a quick search now, a deeper Nimble run (2-4 min) and a full one (5-15 min). This uses 2 agent runs."

### Step 1 of 3 · Preliminary quick results

Tell them what titles the company likely uses for those roles and who you can find in them, marked as possibly out of date. Use a few quick searches, not the agents: `nimble_search` if Nimble is connected, otherwise your own web search tool. Keep it under a minute and short. Link every fact, and mark anything from memory with your knowledge cutoff.

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
- **Use it from code.** The agent is saved as `decision-maker-identification`. Give a short Python or TypeScript snippet that runs it by name.

## Using Nimble well

Read the page you need, when you need it: [writing the task](https://docs.nimbleway.com/nimble-sdk/web-search-agents/best-practices/writing-the-task.md), [sources](https://docs.nimbleway.com/nimble-sdk/web-search-agents/best-practices/sources.md), [effort and cost](https://docs.nimbleway.com/nimble-sdk/web-search-agents/best-practices/effort-and-cost.md), [evaluating results](https://docs.nimbleway.com/nimble-sdk/web-search-agents/best-practices/evaluating-results.md), [running at scale](https://docs.nimbleway.com/nimble-sdk/web-search-agents/best-practices/running-at-scale.md), [common mistakes](https://docs.nimbleway.com/nimble-sdk/web-search-agents/best-practices/common-mistakes.md).

## Pitfalls

- A role in missing_roles means no current source confirmed it. That is the safe behaviour, not a failure.
- LinkedIn profile pages need a login, so the agent relies on company pages, press and public posts.
- If the company has no such role, it returns the closest one and explains why.

## Rules

- Never invent values. Show missing fields as missing.
- Never print or log an API key.

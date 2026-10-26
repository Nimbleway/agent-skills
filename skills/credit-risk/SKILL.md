---
name: credit-risk
description: |
  Builds a dated, sourced credit picture of a company: financials, ratings, debt events,
  payment behaviour, distress signals and ownership, with a risk call and its reasons,
  using the Nimble `credit-risk` agent template on live web data. Use when the user says
  "credit risk of", "counterparty check", "can they pay", "is this supplier at risk",
  "credit picture for", "distress signals", or arrives from a Nimble use-case page.
  Interviews the user for the inputs, gives a quick first pass from the host's own search,
  connects Nimble, then runs the template. Do NOT use for a compliance screen (use
  kyc-screening) or an investment memo (use due-diligence).
allowed-tools:
  - Bash(nimble:*)
  - Bash(claude:*)
  - Bash(npm:*)
  - Bash(npx:*)
  - Read
  - Write
  - AskUserQuestion
  # Quick first pass with the host's own search, and reading the hosted docs:
  - WebSearch
  - WebFetch
  # Nimble MCP (agent templates and runs):
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
  version: 1.8.0
  category: finance-research
---

# Credit risk

Builds a dated, sourced credit picture of a company: financials, ratings, debt events, payment behaviour, distress signals and ownership, with a risk call and its reasons.

User request: $ARGUMENTS

## What the user gets

Financials with periods, ratings, debt events, payment behaviour, distress signals, ownership, and a risk call (low, moderate, elevated or high) with the reasons behind it.

## Agent template

This skill runs the Nimble gallery template `credit-risk` (effort high, 5-10 minutes, $0.50 per run on the list price). The agent's instructions, sources and output schema live in the template. Do not rewrite them in the run.

## Flow

Start step 1, but do not wait on it. Do steps 2 and 3 while the user connects.

### 1. Connect Nimble

If Nimble tools are listed in this session, call `nimble_agents_list`. Data back means the user is connected. Say nothing and go on.

If not, ask the user to connect Nimble, in one line on why: "Nimble runs the full search on live sources, with a source for every field. Connecting takes one approval, and new accounts start with a free trial." Then follow https://docs.nimbleway.com/agent-onboarding.md. Do the setup yourself and involve the user only for the approval. Never ask the user to paste an API key into the chat.

### 2. Get the inputs

| Input | Required | Ask for | If skipped |
|---|---|---|---|
| Company | yes | The exact legal entity if it is a subsidiary, with a domain or ticker | - |
| Purpose | no | Lending, trade credit or a supplier check. It sets what the reasons stress | general |

- Take anything the user already said. Ask only for what is missing.
- If your host has a form or multiple-choice question tool, use it, with the required inputs first and the optional ones marked optional. Otherwise ask in one short message.
- Do not hold up the run for optional inputs. Use the "If skipped" value.

### 3. Quick first pass

Before Nimble runs, answer with what you have: your own web search tool if your host has one, and what you already know. Tell them what you already know about its debt, ratings and ownership, and what to check. Keep it short, link every fact you found, and mark facts from memory with your knowledge cutoff.

Close with one line, for example: "This is a quick first pass. Once Nimble is connected I'll run the full search on live sources." If Nimble is still not connected, offer the connect step again. Do not start step 4 without it.

### 4. Run the template

Build the input from this pattern:

```
Assess the credit and counterparty risk of <Company> (<domain or ticker>). Purpose: <purpose>.
```

Example: `Assess the credit and counterparty risk of Rite Aid Corporation`

- One company per run.
- For a subsidiary, name the exact legal entity. The agent will not use the parent's numbers.

Then run it:

1. Create the agent from the template: `nimble_agents_create(template="credit-risk", agent_name="credit-risk")`. A 409 "already exists" means it was created before, so go on to the run. If the template is not found, tell the user it is unavailable and stop. Do not substitute another template.
2. Start the run: `nimble_agents_run(agent_name="credit-risk", input="<the input>")`. Leave effort, schema and skill to the template.
3. Poll `nimble_agents_run_status` until it finishes, then get `nimble_agents_run_result`.

Tell the user it takes 5-10 minutes. One short update while it runs is enough.

### 5. Show the result

- A short table or brief, not raw JSON. Lead with the 2-3 most useful facts, each with its source link.
- Point out what is new or different from your first pass.
- Say what is missing (empty fields, `missing_fields`, empty lists). Do not present a partial result as complete.
- If a run finishes with no output and no sources, retry it once. Do not retry a run that returned data.

### 6. Next steps

Offer, one line each, what fits:
- **Run it on a list.** One run per record in parallel. See [Running at scale](https://docs.nimbleway.com/nimble-sdk/web-search-agents/best-practices/running-at-scale.md).
- **Schedule it.** Use the host's scheduler or a cron job, and pass the last run date as the new since date where the input has one.
- **Use it from code.** The agent is saved as `credit-risk`. Give a short Python or TypeScript snippet that runs it by name.

## Using Nimble well

Read the page you need, when you need it: [writing the task](https://docs.nimbleway.com/nimble-sdk/web-search-agents/best-practices/writing-the-task.md), [sources](https://docs.nimbleway.com/nimble-sdk/web-search-agents/best-practices/sources.md), [effort and cost](https://docs.nimbleway.com/nimble-sdk/web-search-agents/best-practices/effort-and-cost.md), [evaluating results](https://docs.nimbleway.com/nimble-sdk/web-search-agents/best-practices/evaluating-results.md), [running at scale](https://docs.nimbleway.com/nimble-sdk/web-search-agents/best-practices/running-at-scale.md), [common mistakes](https://docs.nimbleway.com/nimble-sdk/web-search-agents/best-practices/common-mistakes.md).

## Pitfalls

- Many mid-size companies have no public rating. The run says so.
- For private companies, figures come from filed accounts or press. Check who stated them.

## Rules

- Never invent values. Show missing fields as missing.
- Never print or log an API key.
- Always show the risk call with its reasons and sources, never alone.

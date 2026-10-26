---
name: due-diligence
description: |
  Writes a first-pass due diligence memo on a private company: business, traction, team,
  funding, financial signals, legal issues, reputation and red flags, every claim dated
  and cited, using the Nimble `due-diligence` agent template on live web data. Use when
  the user says "due diligence on", "DD memo", "investment memo on", "diligence this
  company", "red flags for", "should we invest in", or arrives from a Nimble use-case
  page. Interviews the user for the inputs, gives a quick first pass from the host's own
  search, connects Nimble, then runs the template. Do NOT use for a sales meeting brief
  (use account-brief) or a credit view (use credit-risk).
metadata:
  author: Nimbleway
  version: 1.8.0
  category: finance-research
---

# Due diligence

Writes a first-pass due diligence memo on a private company: business, traction, team, funding, financial signals, legal issues, reputation and red flags, every claim dated and cited.

User request: $ARGUMENTS

## What the user gets

A memo with sections for business, traction, team, funding, financial signals, legal and regulatory, reputation, red flags and a short verdict. Every claim has a date and source.

## Agent template

This skill runs the Nimble gallery template `due-diligence` (effort high, 3-8 minutes, $0.50 per run on the list price). The agent's instructions, sources and output schema live in the template. Do not rewrite them in the run.

## Flow

Start step 1, but do not wait on it. Do steps 2 and 3 while the user connects.

### 1. Connect Nimble

If Nimble tools are listed in this session, call `nimble_agents_list`. Data back means the user is connected. Say nothing and go on.

If not, ask the user to connect Nimble, in one line on why: "Nimble runs the full search on live sources, with a source for every field. Connecting takes one approval, and new accounts start with a free trial." Then follow https://docs.nimbleway.com/agent-onboarding.md. Do the setup yourself and involve the user only for the approval. Never ask the user to paste an API key into the chat.

### 2. Get the inputs

| Input | Required | Ask for | If skipped |
|---|---|---|---|
| Company | yes | Name and domain | - |
| Focus | no | Anything to check first, for example "focus on the AI cost story" | none |

- Take anything the user already said. Ask only for what is missing.
- If your host has a form or multiple-choice question tool, use it, with the required inputs first and the optional ones marked optional. Otherwise ask in one short message.
- Do not hold up the run for optional inputs. Use the "If skipped" value.

### 3. Quick first pass

Before Nimble runs, answer with what you have: your own web search tool if your host has one, and what you already know. Give them a memo outline, what you already know about the company, and the risks worth checking. Keep it short, link every fact you found, and mark facts from memory with your knowledge cutoff.

Close with one line, for example: "This is a quick first pass. Once Nimble is connected I'll run the full search on live sources." If Nimble is still not connected, offer the connect step again. Do not start step 4 without it.

### 4. Run the template

Build the input from this pattern:

```
Write a due diligence memo on <Company> (<domain>). Focus on <focus>.
```

Example: `Write a due diligence memo on Canva`

- One company per run.
- A focus line shifts depth. It does not remove sections.

Then run it:

1. If `nimble_agents_list` has no agent named `due-diligence`, create it from the template: `nimble_agents_create(template="due-diligence", agent_name="due-diligence")`. If that template is not found, call `nimble_agent_templates_list` and use the closest match by name.
2. Start the run: `nimble_agents_run(agent_name="due-diligence", input="<the input>")`. Leave effort, schema and skill to the template.
3. Poll `nimble_agents_run_status` until it finishes, then get `nimble_agents_run_result`.

Tell the user it takes 3-8 minutes. One short update while it runs is enough.

### 5. Show the result

- A short table or brief, not raw JSON. Lead with the 2-3 most useful facts, each with its source link.
- Point out what is new or different from your first pass.
- Say what is missing (empty fields, `missing_fields`, empty lists). Do not present a partial result as complete.
- If a run finishes with no output and no sources, retry it once. Do not retry a run that returned data.

### 6. Next steps

Offer, one line each, what fits:
- **Run it on a list.** One run per record in parallel. See [Running at scale](https://docs.nimbleway.com/nimble-sdk/web-search-agents/best-practices/running-at-scale.md).
- **Schedule it.** Use the host's scheduler or a cron job, and pass the last run date as the new since date where the input has one.
- **Use it from code.** The agent is saved as `due-diligence`. Give a short Python or TypeScript snippet that runs it by name.

## Using Nimble well

Read the page you need, when you need it: [writing the task](https://docs.nimbleway.com/nimble-sdk/web-search-agents/best-practices/writing-the-task.md), [sources](https://docs.nimbleway.com/nimble-sdk/web-search-agents/best-practices/sources.md), [effort and cost](https://docs.nimbleway.com/nimble-sdk/web-search-agents/best-practices/effort-and-cost.md), [evaluating results](https://docs.nimbleway.com/nimble-sdk/web-search-agents/best-practices/evaluating-results.md), [running at scale](https://docs.nimbleway.com/nimble-sdk/web-search-agents/best-practices/running-at-scale.md), [common mistakes](https://docs.nimbleway.com/nimble-sdk/web-search-agents/best-practices/common-mistakes.md).

## Pitfalls

- A red flag must point to a cited claim above it. If one does not, drop it.
- Revenue for private companies is usually an estimate. Check who stated it before quoting.
- Some legal items cite a secondary page. Open the primary source before relying on it.

## Rules

- Never invent values. Show missing fields as missing.
- Never print or log an API key.

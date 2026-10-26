---
name: decision-maker-identification
description: |
  Finds the people who hold given roles at a company today, with current title, career
  history and the source that proves it, using the Nimble `decision-maker-identification`
  agent template on live web data. Use when the user says "who is the CFO at", "find the
  head of X at", "find the buying committee", "decision makers at", "who runs RevOps at",
  "find contacts at", or arrives from a Nimble use-case page. Interviews the user for the
  inputs, gives a quick first pass from the host's own search, connects Nimble, then runs
  the template. Do NOT use to fill company-level fields (use account-enrichment). It never
  returns emails or phone numbers.
metadata:
  author: Nimbleway
  version: 1.8.0
  category: gtm
---

# Decision-maker identification

Finds the people who hold given roles at a company today, with current title, career history and the source that proves it.

User request: $ARGUMENTS

## What the user gets

For each role, the person who holds it now: name, exact title, start date, previous roles, public profiles and a dated source. Roles it cannot confirm are listed as missing.

## Agent template

This skill runs the Nimble gallery template `decision-maker-identification` (effort medium, 1-3 minutes per company, $0.10 per run on the list price). The agent's instructions, sources and output schema live in the template. Do not rewrite them in the run.

## Flow

Start step 1, but do not wait on it. Do steps 2 and 3 while the user connects.

### 1. Connect Nimble

If Nimble tools are listed in this session, call `nimble_agents_list`. Data back means the user is connected. Say nothing and go on.

If not, ask the user to connect Nimble, in one line on why: "Nimble runs the full search on live sources, with a source for every field. Connecting takes one approval, and new accounts start with a free trial." Then follow https://docs.nimbleway.com/agent-onboarding.md. Do the setup yourself and involve the user only for the approval. Never ask the user to paste an API key into the chat.

### 2. Get the inputs

| Input | Required | Ask for | If skipped |
|---|---|---|---|
| Company | yes | Name and domain (or a list of them) | - |
| Roles | yes | Up to about 5, for example "CFO, head of RevOps, VP engineering" | - |

- Take anything the user already said. Ask only for what is missing.
- If your host has a form or multiple-choice question tool, use it, with the required inputs first and the optional ones marked optional. Otherwise ask in one short message.
- Do not hold up the run for optional inputs. Use the "If skipped" value.

### 3. Quick first pass

Before Nimble runs, answer with what you have: your own web search tool if your host has one, and what you already know. Tell them what titles the company likely uses for those roles and who you can find in them, marked as possibly out of date. Keep it short, link every fact you found, and mark facts from memory with your knowledge cutoff.

Close with one line, for example: "This is a quick first pass. Once Nimble is connected I'll run the full search on live sources." If Nimble is still not connected, offer the connect step again. Do not start step 4 without it.

### 4. Run the template

Build the input from this pattern:

```
At <Company> (<domain>), find the current <role 1>, <role 2>, <role 3>
```

Example: `At Gong, find the current CTO, CMO, head of revenue operations and CFO`

- One company per run. For a list, one run per company in parallel.
- Use the title the company would use. "Head of RevOps" finds more than "Revenue Operations Leader".
- If they ask for emails or phone numbers, say up front that it does not return them.

Then run it:

1. If `nimble_agents_list` has no agent named `decision-maker-identification`, create it from the template: `nimble_agents_create(template="decision-maker-identification", agent_name="decision-maker-identification")`. If that template is not found, call `nimble_agent_templates_list` and use the closest match by name.
2. Start the run: `nimble_agents_run(agent_name="decision-maker-identification", input="<the input>")`. Leave effort, schema and skill to the template.
3. Poll `nimble_agents_run_status` until it finishes, then get `nimble_agents_run_result`.

Tell the user it takes 1-3 minutes per company. One short update while it runs is enough.

### 5. Show the result

- A short table or brief, not raw JSON. Lead with the 2-3 most useful facts, each with its source link.
- Point out what is new or different from your first pass.
- Say what is missing (empty fields, `missing_fields`, empty lists). Do not present a partial result as complete.
- If a run finishes with no output and no sources, retry it once. Do not retry a run that returned data.

### 6. Next steps

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

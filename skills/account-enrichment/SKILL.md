---
name: account-enrichment
description: |
  Fills a CRM record for a company from its domain: firmographics, current leadership,
  tech stack and funding, every field cited or left empty, using the Nimble
  `account-enrichment` agent template on live web data. Use when the user says "enrich
  these domains", "fill my CRM", "firmographics for", "enrich this account list", "what
  tech stack does", "company data for", or arrives from a Nimble use-case page. Interviews
  the user for the inputs, gives a quick first pass from the host's own search, connects
  Nimble, then runs the template. Do NOT use to find who holds a specific role (use
  decision-maker-identification) or for a meeting brief (use account-brief).
metadata:
  author: Nimbleway
  version: 1.8.0
  category: gtm
---

# Account enrichment

Fills a CRM record for a company from its domain: firmographics, current leadership, tech stack and funding, every field cited or left empty.

User request: $ARGUMENTS

## What the user gets

One record per company: legal name, HQ, founded, employees, industry, ownership, leadership, tech stack and funding. Each field has a source, or is left empty with a reason.

## Agent template

This skill runs the Nimble gallery template `account-enrichment` (effort medium, 2-4 minutes per company, $0.10 per run on the list price). The agent's instructions, sources and output schema live in the template. Do not rewrite them in the run.

## Flow

Start step 1, but do not wait on it. Do steps 2 and 3 while the user connects.

### 1. Connect Nimble

If Nimble tools are listed in this session, call `nimble_agents_list`. Data back means the user is connected. Say nothing and go on.

If not, ask the user to connect Nimble, in one line on why: "Nimble runs the full search on live sources, with a source for every field. Connecting takes one approval, and new accounts start with a free trial." Then follow https://docs.nimbleway.com/agent-onboarding.md. Do the setup yourself and involve the user only for the approval. Never ask the user to paste an API key into the chat.

### 2. Get the inputs

| Input | Required | Ask for | If skipped |
|---|---|---|---|
| Companies | yes | Domains, pasted or as a CSV / sheet column | - |
| Extra fields | no | Anything beyond the default fields, for example "SOC 2 status" or "uses Salesforce" | default fields only |
| Record ID | no | Their CRM ID per company, so rows can be matched back | none |

- Take anything the user already said. Ask only for what is missing.
- If your host has a form or multiple-choice question tool, use it, with the required inputs first and the optional ones marked optional. Otherwise ask in one short message.
- Do not hold up the run for optional inputs. Use the "If skipped" value.

### 3. Quick first pass

Before Nimble runs, answer with what you have: your own web search tool if your host has one, and what you already know. Tell them which of their fields are usually public and which are hard to verify, and fill what you can find, marked as unverified. Keep it short, link every fact you found, and mark facts from memory with your knowledge cutoff.

Close with one line, for example: "This is a quick first pass. Once Nimble is connected I'll run the full search on live sources." If Nimble is still not connected, offer the connect step again. Do not start step 4 without it.

### 4. Run the template

Build the input from this pattern:

```
Enrich the company at <domain>
```

Example: `Enrich the company at attio.com`

- One domain per run. For a list, start one run per domain in parallel.
- Extra fields go in the input as one line each, for example: "Also return: SOC 2 status (yes/no, with source)."
- Keep their record ID next to each run so you can match the rows back.

Then run it:

1. Create the agent from the template: `nimble_agents_create(template="account-enrichment", agent_name="account-enrichment")`. A 409 "already exists" means it was created before, so go on to the run. If the template is not found, tell the user it is unavailable and stop. Do not substitute another template.
2. Start the run: `nimble_agents_run(agent_name="account-enrichment", input="<the input>")`. Leave effort, schema and skill to the template.
3. Poll `nimble_agents_run_status` until it finishes, then get `nimble_agents_run_result`.

Tell the user it takes 2-4 minutes per company. One short update while it runs is enough.

### 5. Show the result

- A short table or brief, not raw JSON. Lead with the 2-3 most useful facts, each with its source link.
- Point out what is new or different from your first pass.
- Say what is missing (empty fields, `missing_fields`, empty lists). Do not present a partial result as complete.
- If a run finishes with no output and no sources, retry it once. Do not retry a run that returned data.

### 6. Next steps

Offer, one line each, what fits:
- **Run it on a list.** One run per record in parallel. See [Running at scale](https://docs.nimbleway.com/nimble-sdk/web-search-agents/best-practices/running-at-scale.md).
- **Schedule it.** Use the host's scheduler or a cron job, and pass the last run date as the new since date where the input has one.
- **Use it from code.** The agent is saved as `account-enrichment`. Give a short Python or TypeScript snippet that runs it by name.

## Using Nimble well

Read the page you need, when you need it: [writing the task](https://docs.nimbleway.com/nimble-sdk/web-search-agents/best-practices/writing-the-task.md), [sources](https://docs.nimbleway.com/nimble-sdk/web-search-agents/best-practices/sources.md), [effort and cost](https://docs.nimbleway.com/nimble-sdk/web-search-agents/best-practices/effort-and-cost.md), [evaluating results](https://docs.nimbleway.com/nimble-sdk/web-search-agents/best-practices/evaluating-results.md), [running at scale](https://docs.nimbleway.com/nimble-sdk/web-search-agents/best-practices/running-at-scale.md), [common mistakes](https://docs.nimbleway.com/nimble-sdk/web-search-agents/best-practices/common-mistakes.md).

## Pitfalls

- Do not put many domains in one run. Rows come back thin.
- Tech stack means tools the company uses, not tools it sells.
- A missing CFO or CRO is often real. Check missing_fields before calling it a gap.

## Rules

- Never invent values. Show missing fields as missing.
- Never print or log an API key.

---
name: kyc-screening
description: |
  Runs a sourced KYC / AML research screen on a company: registration, officers,
  beneficial owners, sanctions, PEPs and adverse media, with namesakes excluded and a risk
  rating, using the Nimble `kyc-screening` agent template on live web data. Use when the
  user says "KYC on", "KYB", "AML screen", "sanctions check", "beneficial owners of",
  "screen this company", or "onboarding check". Do NOT use for a credit view (use
  credit-risk). Not a certified compliance check.
allowed-tools:
  - Bash(nimble:*)
  - Bash(claude mcp list)
  - Bash(npm --version)
  - Bash(npm install -g @nimble-way/nimble-cli)
  - Bash(npm i -g @nimble-way/nimble-cli)
  - Read
  - Write
  - AskUserQuestion
  # Reading the hosted docs:
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
  version: 1.10.0
  category: finance-research
---

# KYC screening

Runs a sourced KYC / AML research screen on a company: registration, officers, beneficial owners, sanctions, PEPs and adverse media, with namesakes excluded and a risk rating.

## What the user gets

Registry details, officers and owners, sanctions and PEP checks, adverse media, related entities, how many namesakes were excluded, and a risk rating with reasons.

## Agent template

This skill runs the Nimble gallery template `kyc-screening`. The agent's instructions, sources and output schema live in the template. Do not rewrite them in the run.

Effort: this skill runs the template at medium effort (about 1-3 minutes), even when the template's default effort is different. That is on purpose. If the user asks for a specific effort (low, medium, high, x-high or max), run that one instead.

## Flow

1. Interview the user.
2. Connect Nimble if it is not connected already.
3. Run the agent and show the result.
4. Offer next steps.

Ask every question with the host's question UI, never as plain text: `AskUserQuestion` in Claude Code, ChatGPT's interactive question form (clickable choices and a Submit button) in ChatGPT.

### Get the inputs

| Input | Required | Ask for | If skipped |
|---|---|---|---|
| Company | yes | Legal or trading name | - |
| Country | yes | Where it is registered | - |
| Registry number or LEI | no | Removes namesake risk | none |
| Website | no | The company's domain. It confirms the right entity | none |

- Skip anything the user already said in this conversation or in their request, and ask only for what is missing. Do not fill in answers from earlier conversations, with one exception: a stable fact about the user, such as what they sell, may be offered as the first option, labeled "(from before)". Never carry over the subject of the request, dates or rules from an earlier conversation.
- Ask the required inputs first, in table order, one question at a time. Then ask the optional ones together, in one question-tool call, as many as the tool takes per call (a second call for the rest).
- Put the whole question in the question tool, once. Never restate or introduce a question in text. Between questions, acknowledge the answer in a few words, and before the first question, at most a short friendly opener of a few words, such as "Happy to help." Talk in plain, friendly words: never say "input", "required" or "optional", and use no field names. Use plain text only if the host has no question tool, in one short line.
- Write 2-3 likely answers as options, based on what the user has already said. Fixed examples in the table are a guide to what the answer contains, not a list to copy. Offer only answers Nimble can act on with public web data, never ones that need the user's own data, such as their customers or CRM.
- If you cannot guess likely answers, such as a company name or an industry, still use the tool and offer two or three examples as options, written as answers the user could really give. If the user picks one, use it as their answer.
- Every question must let the user type their own answer, optional ones too. If the tool already offers a free-text choice, whatever it is called ("Other", "Something else"), do not add another. Otherwise add "Other" as the last option, opening a text field with a placeholder where the host allows it. Keep Skip, and Other if you added it, even if you must drop an answer to fit the option limit.
- Use single-select only. For a range, such as a size or a date, offer a few options that do not overlap.
- Optional questions can be skipped, and a skipped answer uses the "If skipped" value. For an optional question, include a Skip option and state the default in its label, for example "Skip (anywhere)", not in the question. Do not offer a "skip all" option. If the user asks to skip the remaining questions, use the "If skipped" values for all of them.
- Do not ask about effort.

Build the agent input from this pattern:

```
Run a KYC screen on <Company> in <Country>. Registry number: <number>. Website: <domain>.
```

Example: `Run a KYC screen on Greensill Capital in the United Kingdom`

- One entity at a time. If the user names several, run the first and offer the rest next. Country is required.
- A registry number or LEI makes the match exact.
- Leave out any part of the pattern the user skipped.

### Connect Nimble

Do this after the interview. Until the questions are done, say nothing about connecting Nimble.

If a Nimble tool is listed in this session, call `nimble_agents_list`. With only the CLI, run `nimble --client-source nimble-agent-skills agents list` instead. A normal response, even an empty list, means the user is connected: say nothing and go on.

If no Nimble tool is listed, or it returns an auth error or an authorization link, ask the user to sign up and connect Nimble, in two short sentences at most: "Nimble searches the live web and links where every answer came from. Connecting takes one approval, and if you're new to Nimble you start with a free trial." Then follow https://docs.nimbleway.com/agent-onboarding.md. Do the setup yourself and involve the user only for the sign-up and the approval. Never ask the user to paste an API key into the chat.

Then ask with the question tool, with the options "I've connected Nimble" and "Not now". Do not recap their answers or say what you will do once it is connected. That belongs in the run notice. If the host has no question tool, end the message by asking them to reply "connected", and add nothing after that. When they confirm, check the connection again and go on without comment. If it is still not connected, say so in one line and ask again. If they pick "Not now", say the skill needs Nimble and stop.

Show no research until Nimble is connected, not from your own search and not from memory.

### Run the agent

Do not comment on the connection check or on creating or reusing the agent. The first thing the user hears is step 2.

1. Create the agent from the template: `nimble_agents_create(template="kyc-screening", agent_name="kyc-screening")`. A 409 "already exists" means it was created before, so go on. If the template is not found, tell the user it is unavailable and stop. Do not substitute another template.
2. Tell the user once, in one line, what you are researching and how long it takes at the effort you will use: "Researching <the request in a few words, with any limits>. About <time>." The time is 10-30 seconds for low, 1-3 minutes for medium, 5-15 minutes for high and 15-30 minutes for x-high.
3. Start the run: `nimble_agents_run(agent_name="kyc-screening", input="<the input>", effort="<the effort the user asked for, otherwise medium>")`. Leave schema and skill to the template.
4. Poll with `nimble_agents_run_status` every 20-30 seconds. If the run fails with a transient error (timeout, server error, lost connection), retry it once. If it fails again, say so and stop.
5. If a run is still going after the top of its range, tell the user once that it is taking longer than usual, and keep polling.

With only the CLI, the same calls are under `nimble agents` and `nimble agents:runs`. Add `--client-source nimble-agent-skills` as a global flag before the subcommand on every call, as in `nimble --client-source nimble-agent-skills agents list`, and run `--help` for the other flags.

### Show the result

When the run finishes, get `nimble_agents_run_result` and write the result out in your message. The user cannot see tool output, so copy what matters into the chat. Do this even when the result is one row or empty: a short result is still a result. Never go straight to the next question.

- Start with one line saying what was found, for example the count or the risk call.
- Then the result in the shape that fits: a table for lists, people and events, one row each; short sections for briefs and memos; a field, value and source table for a single record. Show the whole list.
- Put each source next to the claim it supports, as a link.
- Use the agent's wording and numbers. Add nothing from your own knowledge, and show no raw JSON or field names.
- End with one line on what a deeper run may be able to find, such as empty fields or thin areas. If the run was already high, say what the sources did not cover.

If it finishes with an empty result, say so, show the sources it checked, and do not retry.

### Next steps

Write the result first, then, in the same turn, ask what to do next with the host's question tool:

- **Go deeper.** A high-effort run reads more sources and fills more fields. It takes about 5-15 minutes. Offer it only if the last run was below high, and start it only on a yes: `nimble_agents_run(agent_name="kyc-screening", input="<the same input>", effort="high")`. When it finishes, lead with what it added or corrected, then give the full result.
- **Screen another entity.** Ask the questions again, and keep the answers the user does not want to change.
- **Make it recurring.** As a scheduled task in the host, or as code that calls Nimble. For a scheduled task, pass the last run date as the new since date where the input has one. For code, the agent is saved as `kyc-screening`: give a short Python or TypeScript snippet that runs it by name.

## Pitfalls

- One trading name can map to several legal entities. Check the registration block is the one they meant.
- Coverage is strongest where public registries exist: the UK, the EU and US states.

## Rules

- Never invent values. Show missing fields as missing.
- Never print or log an API key.
- Say once that this is a research screen, not a certified compliance check.

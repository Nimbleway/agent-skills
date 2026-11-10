---
name: account-brief
description: |
  Writes a dated, sourced brief on one company before a sales meeting: what they do,
  priorities, challenges, changes in the last 90 days, key people and talking points,
  using the Nimble `account-brief` agent template on live web data. Use when the user says
  "prep me for a meeting with", "account research on", "brief me on [company] before my
  call", "account brief", or "what should I know before meeting". Do NOT use for
  researching the people attending (use meeting-prep), for an investment memo (use
  due-diligence), or for a list of changes since a date (use account-signals).
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
  category: gtm
---

# Account brief

Writes a dated, sourced brief on one company before a sales meeting: what they do, priorities, challenges, changes in the last 90 days, key people and talking points.

## What the user gets

A short brief: what the company does, current priorities and challenges with evidence, what changed in the last 90 days, key people, and talking points. Every item is dated and sourced.

## Agent template

This skill runs the Nimble gallery template `account-brief`. The agent's instructions, sources and output schema live in the template. Do not rewrite them in the run.

Effort: this skill runs the template at medium effort (about 1-3 minutes), even when the template's default effort is different. That is on purpose. If the user asks for a specific effort (low, medium, high or x-high), run that one instead.

## Flow

1. Interview the user.
2. Connect Nimble if it is not connected already.
3. Run the agent and show the result.
4. Offer next steps.

Ask every question with the host's question UI, never as plain text: `AskUserQuestion` in Claude Code, ChatGPT's interactive question form (clickable choices and a Submit button) in ChatGPT.

### Get the inputs

| Input | Required | Ask for | If skipped |
|---|---|---|---|
| Company | yes | Name and domain | - |
| What you sell | no | One line. It sharpens the talking points | general talking points |
| Meeting goal | no | For example a first call, a renewal or an exec intro | no specific goal |
| People in the meeting | no | Names and titles, if they want a line on each | no named attendees |

- Skip anything the user already said in this conversation or in their request, and ask only for what is missing. Do not fill in answers from earlier conversations, with one exception: a stable fact about the user, such as what they sell, may be offered as the first option, labeled "(from before)". Never carry over the subject of the request, dates or rules from an earlier conversation.
- Ask the required inputs first, in table order, one question at a time. Then ask the optional ones together, in one question-tool call, as many as the tool takes per call (a second call for the rest).
- Put the whole question in the question tool, once. Never restate or introduce a question in text. Between questions, acknowledge the answer in a few words, and before the first question, at most one short sentence that acknowledges your role (the user's, if they named one), such as "Sure, I'll use Nimble to be your meeting preparation assistant." Talk in plain, friendly words: never say "input", "required" or "optional", and use no field names. Use plain text only if the host has no question tool, in one short line.
- Write 2-3 likely answers as options, based on what the user has already said. Fixed examples in the table are a guide to what the answer contains, not a list to copy. Offer only answers Nimble can act on with public web data, never ones that need the user's own data, such as their customers or CRM.
- If you cannot guess likely answers, such as a company name or an industry, still use the tool and offer two or three examples as options, written as answers the user could really give. If the user picks one, use it as their answer.
- Every question must let the user type their own answer, optional ones too. Claude's question UI adds its own free-text choice ("Something else" in Claude, "Other" in Claude Code), so add none there. ChatGPT's form does not, so add "Other" as the last option of every question, even one whose options look complete, opening a text field with a placeholder. In any other host, add "Other" unless you know its UI already has a free-text choice. Keep Skip and Other, when you add them, even if you must drop an answer to fit the option limit.
- Use single-select only. For a range, such as a size or a date, offer a few options that do not overlap.
- Optional questions can be skipped, and a skipped answer uses the "If skipped" value. Claude's question UI has its own Skip button, so add no Skip option there. In other hosts, include a Skip option that states the default in its label, for example "Skip (any location)", not in the question. When you acknowledge a skipped question, say the default you will use, for example "Any location.", not that it was skipped. Do not offer a "skip all" option. If the user asks to skip the remaining questions, use the "If skipped" values for all of them.
- Do not ask about effort.

Build the agent input from this pattern:

```
Prepare me for a meeting with <Company> (<domain>). I sell <one line>. The meeting is <goal>.
```

Example: `Prepare me for a meeting with Attio (attio.com)`

- Always include the domain. It stops the agent from drifting to a company with a similar name.
- If they name the people in the meeting, add them to the input.
- Leave out any part of the pattern the user skipped: leaving it out is the default.

### Connect Nimble

Do this after the interview. Until the questions are done, say nothing about connecting Nimble.

Check the connection. If a Nimble tool is listed in this session, call `nimble_agents_list`. If the CLI is available, run `nimble --client-source nimble-agent-skills agents list`. A normal response from either, even an empty list, means the user is connected: say nothing and go on.

If neither check succeeds (no tool is listed and the CLI is missing or fails, or a check returns an auth error or an authorization link), connect it in these steps. Your message is only these steps: no summary of what the user told you, no mention of the skill, the template or the workflow, and no plan for what happens after connecting (that belongs in the run notice).

1. Tell the user, in two short sentences at most: "Nimble searches the live web and links where every answer came from. Connecting takes one approval, and if you're new to Nimble you start with a free trial."
2. Connect it in the first of these ways that works, and stop at the first one that does:
   - Show the host's card to connect or install Nimble from nimbleway.com: the Connect card for the connector in Claude, the install card for the plugin in ChatGPT.
   - If you can't show a card and a check returned an authorization link, show that link to the user.
   - If you can do neither but can run commands, follow https://docs.nimbleway.com/agent-onboarding.md and involve the user only for the sign-up and the approval. With only the CLI and no `NIMBLE_API_KEY`, an approval is not enough: follow the page's API key fallback and have the user set the key in their environment, never in the chat. That page is written for you: never link it or its steps to the user.
   - If none of these works, tell the user how to find Nimble in this app, with the clicks: in ChatGPT, open Plugins in the sidebar, search for Nimble, pick the one described as "Expert web search for agents" and install it; in Claude, open Customize, then Connectors, then Nimble, then Connect. Never send the user to nimbleway.com for this.
3. Ask with the question tool, with the options "I've connected Nimble" and "Not now". If the host has no question tool, end the message by asking them to reply "connected", and add nothing after that.

Never ask the user to paste an API key into the chat. When they confirm, check the connection again and go on without comment. If it is still not connected, say so in one line and ask again. If they pick "Not now", say the skill needs Nimble and stop. Show no research until Nimble is connected, not from your own search and not from memory.

### Run the agent

Do not comment on the connection check or on creating or reusing the agent. The first thing the user hears is step 2.

1. Create the agent from the template: `nimble_agents_create(template="account-brief", agent_name="account-brief")`. A 409 "already exists" means it was created before, so go on. If the template is not found, tell the user it is unavailable and stop. Do not substitute another template.
2. Tell the user once, in one line, what you are researching and how long it takes at the effort you will use: "Researching <the request in a few words, with any limits>. Expected to take <time>." The time is 10-30 seconds for low, 1-3 minutes for medium, 5-15 minutes for high and 15-30 minutes for x-high.
3. Start the run: `nimble_agents_run(agent_name="account-brief", input="<the input>", effort="<the effort the user asked for, otherwise medium>")`. Leave schema and skill to the template.
4. Poll with `nimble_agents_run_status` until the run finishes. On MCP each call waits up to about 45 seconds and returns "still running" if the run is not done: that is not an error, so call it again right away. Otherwise poll every 20-30 seconds. If a call fails with a transient error (timeout, server error, lost connection), retry only that call, once, and never send `nimble_agents_run` again. If starting the run fails with a transient error, check `nimble_agents_runs_list` for a run you already started before starting another. If a call fails again, say so and stop.
5. Keep track of how long the run has been going: the time since you started it or, on MCP, about 45 seconds per status call. When it passes the top of its range (30 seconds for low, 3 minutes for medium, 15 minutes for high, 30 minutes for x-high), write one line to the user saying it is taking longer than usual, but that this is OK and you are still waiting for the result, then keep polling.

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

- **Go deeper.** A high-effort run reads more sources and fills more fields. It is expected to take 5-15 minutes. Offer it only if the last run was below high, and start it only on a yes: `nimble_agents_run(agent_name="account-brief", input="<the same input>", effort="high")`. When it finishes, lead with what it added or corrected, then give the full result.
- **Brief another company.** Ask the questions again, and keep the answers the user does not want to change.
- **Make it recurring.** As a scheduled task in the host, or as code that calls Nimble. For a scheduled task, pass the last run date as the new since date where the input has one. For code, the agent is saved as `account-brief`: give a short Python or TypeScript snippet that runs it by name.

## Pitfalls

- Challenges come from reviews, press and job posts. If none are found, the list is short on purpose.
- Check the dates on recent changes. Anything older than 90 days should not be there.

## Rules

- Never invent values. Show missing fields as missing.
- Never print or log an API key.

---
name: nimble-research
description: Run a Web Search Agent for open-ended, cited research (create-or-reuse)
argument-hint: <question or task>
---

# Nimble Research

## Task: $ARGUMENTS

Use the **nimble-web-expert** skill's Web Search Agents flow — this is for a
finished, cited deliverable (a report, comparison, or enrichment), not a quick
scan. For a raw list of pages instead, use `nimble search` directly.

Follow the reuse-priority chain in
`skills/nimble-web-expert/references/nimble-agents/reference.md`: look for an
existing agent before creating one, then run named create-or-reuse:

Run: `nimble --client-source nimble-agent-skills agents run --agent-name <stable-descriptive-name> --use-case research --input "$ARGUMENTS" --effort high`

The response carries `agent_id` and `run_id` — keep both; `agents:runs get` and
`agents:runs result` each require both. Poll
`nimble --client-source nimble-agent-skills agents:runs get --agent-id <agent_id> --run-id <run_id>`
until finished, then fetch
`nimble --client-source nimble-agent-skills agents:runs result --agent-id <agent_id> --run-id <run_id>`.
Report the terminal result with its per-claim citations and trust metadata
intact — do not summarize away the sourcing.

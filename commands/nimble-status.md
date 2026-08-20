---
name: nimble-status
description: Poll a running Web Search Agent run and fetch its result when finished
argument-hint: <agent-id> <run-id>
---

# Nimble Run Status

## Agent ID and Run ID: $ARGUMENTS

Use the **nimble-web-expert** skill to check this Web Search Agent run. Both IDs
are required — `agents:runs get` and `agents:runs result` reject a run ID alone.

Run: `nimble --client-source nimble-agent-skills agents:runs get --agent-id <agent_id> --run-id <run_id>`

- If still running, report the current state and stop — don't poll in a loop.
- If finished, run `nimble --client-source nimble-agent-skills agents:runs result --agent-id <agent_id> --run-id <run_id>` and report the result with its citations and trust metadata intact.
- If the status call returns a structured error (not-found, auth), surface that
  error as-is rather than reporting it as an empty or missing run.

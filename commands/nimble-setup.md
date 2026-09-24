---
name: nimble-setup
description: Check Nimble CLI/MCP connection status and guide setup if not ready
---

# Nimble Setup

Run the transport preflight from `_shared/nimble-playbook.md` (Preflight Pattern
→ Transport selection): check `nimble --version` (>= 1.2.0) and `NIMBLE_API_KEY`,
then fall back to the MCP connector check if the CLI isn't ready.

- If the CLI is ready, report the detected version and stop — no further action.
- If neither transport is ready, surface the matching guidance from the playbook
  (CLI install command, or the connector-not-connected steps) verbatim. Do not
  invent an install or auth flow beyond what the playbook documents.
- Never print the value of `NIMBLE_API_KEY` — only whether it is set.

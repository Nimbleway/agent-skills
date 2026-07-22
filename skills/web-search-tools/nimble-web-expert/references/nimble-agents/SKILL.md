---
name: nimble-web-search-agents-reference
description: |
  Reference for Nimble Web Search Agents (Agent API V2). Load when a task needs open-ended
  research, data enrichment, or dataset building — where the source isn't fixed, data is
  scattered, structure is inconsistent, or a synthesized answer is needed.
  Covers: dynamic discovery, the reuse-priority chain, agent authoring, the async
  run→status→result lifecycle, effort tiers, trust/citation metadata, and safe credentials.
---

# nimble agents — Web Search Agents reference

A **Web Search Agent** is Nimble's AI-driven agent for open-ended web work. Given a goal, it
discovers where the information lives, navigates to it, and returns a structured or written
result with per-claim citations — rather than being pointed at a fixed set of URLs. It serves
three kinds of use case: **research** (deep research), **data enrichment**, and **dataset
building**.

Use a Web Search Agent when at least one is true: the source isn't known or varies and must be
discovered; the data is scattered across sources that may not be specified; page structure is
inconsistent enough that fixed parsing won't work and the tool needs to reason about what it
finds; or free-text synthesis is needed (a report or summary, not just raw results). When a
single known page can be parsed directly, prefer an Extraction Template
(`references/nimble-extract-templates/SKILL.md`); for raw results to work from, use
`nimble search`.

REST/SDK surface: `POST /v2/agents/*`. Credentials: read `NIMBLE_API_KEY` from the environment
only — never echo, log, or paste a key into a prompt, params, or output.

## Table of Contents

- [Reuse-priority chain](#reuse-priority-chain)
- [1. Discover agent templates](#1-discover-agent-templates)
- [2. Create an agent](#2-create-an-agent)
- [3. Run lifecycle: create → status → result](#3-run-lifecycle-create--status--result)
- [Effort tiers](#effort-tiers)
- [Authoring a from-scratch agent](#authoring-a-from-scratch-agent)
- [Trust & citations](#trust--citations)
- [Failure handling](#failure-handling)

---

## Reuse-priority chain

Before creating a new agent, check in this order:

1. **Existing agent** already covers this — `nimble agents list`, reuse its `id`.
2. **Close-match agent template** worth materializing — `nimble agents:templates list`, then
   `nimble agents create --template <template_name>`.
3. **Only if neither fits**, create one from scratch.

---

## 1. Discover agent templates

```bash
nimble --client-source nimble-agent-skills agents:templates list
nimble --client-source nimble-agent-skills agents:templates get --template-name <template_name>
```

Each template carries `template_name`, `display_name`, `description`, `use_case`
(`research` / `data_enrichment` / `dataset_building`), a default `effort`, a `skill`
(domain-expertise prompt), and an `output_schema`. Read these to judge fit before
materializing.

---

## 2. Create an agent

```bash
# From a pre-built template (copies its fields, goals, sources, output_schema)
nimble --client-source nimble-agent-skills agents create --template <template_name>

# From scratch (see "Authoring" below for how to fill each field)
nimble --client-source nimble-agent-skills agents create \
  --display-name "Company Profiler" \
  --goal "Identify the company" --goal "Summarize funding history" \
  --sources '{...}' \
  --output-schema '{...}' \
  --effort high
```

**Key flags:** `--agent-name` (stable name), `--display-name`, `--description`,
`--goal` (repeatable, ordered), `--sources` (mapping), `--output-schema` (JSON schema),
`--effort`, `--skill` (domain-expertise prompt), `--suggested-question` (repeatable),
`--use-case`, `--template` (materialize from a template), `--is-active`.

`agents create` returns the agent's `id` — use it for runs. (`nimble agents run --input "…"`
is a convenience that creates a minimal persistent agent and starts one run, returning a
`web_search_agent_id`.)

---

## 3. Run lifecycle: create → status → result

Runs are **asynchronous**: create, poll status to a terminal state, then fetch the result.

```bash
# 1. Start a run
nimble --client-source nimble-agent-skills agents:runs create \
  --agent-id <agent_id> --input "<task or question>" --effort high

# 2. Poll status until terminal (completed | failed | cancelled) — wait ~15–30s between polls
nimble --client-source nimble-agent-skills agents:runs get \
  --agent-id <agent_id> --run-id <run_id>

# 3. Fetch the output once completed
nimble --client-source nimble-agent-skills agents:runs result \
  --agent-id <agent_id> --run-id <run_id>
```

**`agents:runs create` flags:**

| Flag                       | Description                                                              |
| -------------------------- | ------------------------------------------------------------------------ |
| `--agent-id`               | Agent to run (required)                                                  |
| `--input`                  | Natural-language task/question for the run (required)                    |
| `--effort`                 | `low` / `medium` / `high` / `x-high` / `max` (see below)                 |
| `--output-schema`          | JSON schema overriding the agent's default structured output            |
| `--input-data`             | Existing rows to ENRICH — a list/object mirroring the output_schema shape |
| `--sources`                | Source guidance overriding the agent default                            |
| `--enable-events`          | Publish live progress; follow with `agents:runs stream-events`          |
| `--previous-interaction-id`| Continue a prior run as a conversation                                  |

**Run states:** `queued` → (running) → terminal: `completed`, `failed`, or `cancelled`. List
an agent's runs newest-first with `nimble agents:runs list --agent-id <id>`.

---

## Effort tiers

Set effort to the shape of the task — don't ask the user to pick a number:

| Tier                 | When                                                                    |
| -------------------- | ----------------------------------------------------------------------- |
| `low` / `medium`     | Fast, simple asks — a handful of easy-to-find fields                    |
| `high`               | **Default** once several fields need real digging                       |
| `x-high` / `max`     | Genuinely complex, multi-faceted profiles (financials, filings, history) |

For a quick first look, offer a **preview** run at `low`, then re-run at the recommended tier —
the user chooses "quick preview" vs "full run" without ever touching the value.

---

## Authoring a from-scratch agent

When creating from scratch, fill each field deliberately (adapted from Nimble's own agent
configuration guidance):

- **Domain Expertise** (`--skill`) — a dense role paragraph, under five sentences: who the
  agent is for this use case; how to handle inputs supplied in more than one format; which
  source to check first for which fact; how to handle data that can't be found (say
  "Unknown," never invent); and whether to return a per-field confidence indicator.
- **Goals** (`--goal`, repeatable) — one verb phrase per logical group of output fields,
  ordered most-important first. If there's a way to skip re-fetching data the user already
  has, make that the first goal.
- **Sources** (`--sources`) — a hard whitelist grouped into priority tiers, most important
  first. Prefer a domain already covered by an Extraction Template (cleaner, structured
  data); where none exists, the agent falls back to general web search there.
- **Output** (`--output-schema`) — use the user's own field names; use plain strings for
  ranges/estimates ("50 to 200 employees", not an invented number); group related fields into
  nested structures and use lists for anything naturally a list; mark required vs optional.
- **Effort** — per the tiers above.

Also draft a recommended starting prompt for the first run based on the conversation.

---

## Trust & citations

`agents:runs result` returns an `output` that is either `type: "text"` (a prose answer) or
`type: "json"` (structured data matching the output schema), **plus `trust` metadata with
per-claim citations**. Surface the citations alongside the answer — every claim should trace
to a source. This is what makes a Web Search Agent's answer verifiable rather than an
unsourced summary.

---

## Failure handling

- Poll `agents:runs get` until a terminal state; don't fetch `result` before `completed`.
- `failed` / `cancelled` are real outcomes — report them plainly, don't present a partial or
  empty result as success. Suggest an obvious next step (broaden sources, raise effort, or a
  different capability) where one exists.
- Never work around a missing/blocked transport with WebFetch, WebSearch, or curl.

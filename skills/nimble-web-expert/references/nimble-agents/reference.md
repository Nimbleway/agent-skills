---
name: nimble-web-search-agents-reference
description: |
  Reference for Nimble Web Search Agents (Agent API V2). Load when a task needs open-ended
  research, enrichment, or dataset building — where the source isn't fixed, data is
  scattered, structure is inconsistent, or a synthesized answer is needed.
  Covers: the three run modes, dynamic discovery, the reuse-priority chain, `use_case`
  locking, run-level `skill` override, run controls, live events vs polling, trust and
  citations, and safe credentials.
---

# nimble agents — Web Search Agents reference

A **Web Search Agent** is Nimble's AI-driven agent for open-ended web work. Given a goal, it
discovers where the information lives, navigates to it, and returns a structured or written
result with per-claim citations — rather than being pointed at a fixed set of URLs. It serves
three use cases: **research**, **enrichment**, and **dataset building**.

Use a Web Search Agent when at least one is true: the source isn't known or varies and must be
discovered; the data is scattered across sources that may not be specified; page structure is
inconsistent enough that fixed parsing won't work and the tool needs to reason about what it
finds; or free-text synthesis is needed (a report or summary, not just raw results). When a
single known page can be parsed directly, prefer an Extraction Template
(`references/nimble-extract-templates/reference.md`); for raw results to work from, use
`nimble search`.

Requires **Nimble CLI 1.2.0+**. REST/SDK surface: `POST /v2/agents/*`. Credentials: read
`NIMBLE_API_KEY` from the environment only — never echo, log, or paste a key into a prompt,
params, or output.

## Table of Contents

- [Run modes — pick one before anything else](#run-modes--pick-one-before-anything-else)
- [`use_case` — set once, then locked](#use_case--set-once-then-locked)
- [`skill` — a one-time run override](#skill--a-one-time-run-override)
- [Run controls](#run-controls)
- [Discovery and the reuse-priority chain](#discovery-and-the-reuse-priority-chain)
- [Run lifecycle: create → status → result](#run-lifecycle-create--status--result)
- [Live progress: events, and polling as the fallback](#live-progress-events-and-polling-as-the-fallback)
- [Effort tiers](#effort-tiers)
- [Authoring a from-scratch agent](#authoring-a-from-scratch-agent)
- [Trust & citations](#trust--citations)
- [MCP fallback — transport differences](#mcp-fallback-and-its-gaps)
- [Failure handling](#failure-handling)

---

## Run modes — pick one before anything else

Which identity you pass on the run decides which route runs, and which route you're on
decides which command to call. Choose the mode first, then build the command.

| Mode                            | Identity passed              | Command                                | Use when                                                                                          |
| ------------------------------- | ---------------------------- | -------------------------------------- | ------------------------------------------------------------------------------------------------- |
| **1 — named create-or-reuse**   | `--agent-name`, no agent ID  | `nimble agents run --agent-name <name>` | **Default for skills.** A stable name you can re-derive each session without storing an ID.        |
| **2 — explicit agent**          | `--agent-id`                 | `nimble agents:runs create --agent-id <id>` | You already manage the agent's lifecycle (materialized from a template or authored from scratch). |
| **3 — caller-anonymous**        | neither                      | `nimble agents run`                     | A genuine one-off where no agent needs to survive the run.                                        |

**Routing rule:** `agents:runs create` **requires** `--agent-id` — it is the Mode 2 command
only, and `--agent-name` is ignored there. Modes 1 and 3 both go through `nimble agents run`.

**Mode 1 reuse is by name, and it is exact.** An unseen name creates a new agent; a name
already in the account resolves to that agent and returns the **same `web_search_agent_id`**
on every subsequent run. Derive names deterministically (e.g. `{skill}-{purpose}`) so a
repeat session lands on the same agent instead of littering the account with near-duplicates.

**Mode 3 still creates an agent.** The response carries a generated `web_search_agent_id` —
keep it, because `agents:runs get` and `agents:runs result` both need it.

Every mode returns the same run envelope: `id` (= `interaction_id`), `status`,
`web_search_agent_id`, `effort`, `prompt`.

```bash
# Mode 1 — named create-or-reuse
nimble --client-source nimble-agent-skills agents run \
  --agent-name "competitor-intel-news" --use-case research \
  --input "<task or question>" --effort high

# Mode 2 — explicit agent
nimble --client-source nimble-agent-skills agents:runs create \
  --agent-id <agent_id> --input "<task or question>" --effort high

# Mode 3 — caller-anonymous
nimble --client-source nimble-agent-skills agents run \
  --input "<task or question>" --effort high
```

---

## `use_case` — set once, then locked

Exactly three values: **`research`**, **`enrichment`**, **`dataset_building`**. Nothing else
is accepted — a wrong value fails validation with the accepted enum echoed back.

`use_case` is agent configuration, **not a per-run override**:

- It is stored when the agent is **created** — including on a Mode 1 first call and on a
  Mode 3 run.
- Against an **existing** agent, passing the **same** value is accepted as a no-op.
- Against an existing agent, passing a **different** value is **rejected** (`422`,
  `use_case cannot be changed for an existing agent`). Omit it, or match it.

Read an agent's stored value with `agents get --agent-id <id>` before running if you're not
sure. To work in a different use case, use a different agent — don't try to flip an
existing one.

**`dataset_building` carries two extra requirements**, both enforced server-side:

- `--output-schema` is required (`output_schema is required when use_case is dataset_building`).
- Effort must be `high` or above (`dataset_building requires effort 'high' or higher`).

---

## `skill` — a one-time run override

`--skill` is the agent's domain-expertise prompt. On a run it behaves differently from
`use_case`:

- **Against an existing agent** (Mode 2, or Mode 1 on a name that already resolves), `--skill`
  applies to **that run only**. The agent's stored `skill` is left untouched — verified by
  re-reading the agent after an override run.
- **First-call exception:** when the run is the call that *creates* the agent (Mode 1 with an
  unseen name, or Mode 3), `--skill` and `--use-case` are not overrides at all — they become
  the new agent's **stored configuration**.

So the same flag means "just this once" or "from now on" depending on whether the agent
already existed. When it matters, check with `agents get` first.

---

## Run controls

Available on both `agents run` and `agents:runs create`:

| Flag                        | Description                                                                        |
| --------------------------- | ---------------------------------------------------------------------------------- |
| `--input`                   | Natural-language task/question for the run (required)                              |
| `--effort`                  | `low` / `medium` / `high` / `x-high` (see below; `max` is not available)            |
| `--output-schema`           | JSON schema (a full mapping) overriding the agent's default structured output      |
| `--input-data`              | Existing rows to ENRICH — a list or single object mirroring the output_schema shape |
| `--sources`                 | Source guidance overriding the agent default                                       |
| `--enable-events`           | Publish live progress; consume with `agents:runs stream-events`                    |
| `--previous-interaction-id` | Continue a prior run as a conversation (pass the earlier run's `interaction_id`)   |
| `--skill` / `--use-case`    | Per the two sections above                                                         |

### `--sources` — four fields, two different shapes

```json
{
  "allow":      [{ "title": "Reference encyclopedias", "domains": ["example.com"], "order": 0 }],
  "block":      [{ "title": "Social pinboards",        "domains": ["example.net"], "order": 0 }],
  "prioritize": "Prefer the organization's official site over aggregators.",
  "avoid":      "Avoid unsourced blog aggregators."
}
```

- **`allow` / `block`** are arrays of source *groups* — objects with `title` (**required**),
  `domains`, and an optional `order` that sets priority. A bare domain string is rejected.
- **`prioritize` / `avoid`** are plain guidance **strings**. An array is rejected.

`allow` is a hard whitelist; `prioritize`/`avoid` are soft steering. Prefer a domain already
covered by an Extraction Template — the agent gets cleaner structured data there.

### `--input-data` vs `--output-schema` — they are not the same thing

- `--output-schema` describes the **shape of the answer**.
- `--input-data` supplies the **rows you already have**, mirroring that shape; the agent fills
  the gaps rather than re-deriving what you gave it.

Two things to get right:

- **Enriching several rows needs an array `output_schema`.** An object schema returns one
  object no matter how many rows go in.
- Fields carried in from `input_data` come back in `trust.claims` with
  `confidence: "pre_existing"` and no citations — they were passed through, not verified.
  Don't present them as sourced findings.

---

## Discovery and the reuse-priority chain

Before creating a new agent, check in this order:

1. **Existing agent** already covers this — `nimble agents list`, reuse its `id` (Mode 2), or
   just re-run its `agent_name` (Mode 1).
2. **Close-match agent template** worth materializing — `nimble agents:templates list`, then
   `nimble agents create --template <template_name>`.
3. **Only if neither fits**, create one from scratch.

```bash
nimble --client-source nimble-agent-skills agents list --limit 100
nimble --client-source nimble-agent-skills agents:templates list
nimble --client-source nimble-agent-skills agents:templates get --template-name <template_name>
```

Neither `agents list` nor `agents:templates list` takes a server-side search term — list and
filter **client-side** on `agent_name` / `template_name` / `description` / `use_case`. Names
are dynamic: discover them at runtime, never hardcode them.

Each template carries `template_name`, `display_name`, `description`, `use_case`, a default
`effort`, a `skill`, `sources`, and an `output_schema`. Read these to judge fit
before materializing. Note the template `sources` shape differs from the run/agent shape —
it is a flat ordered array of `{title, domains, order}` groups.

```bash
# From a pre-built template (copies its fields, sources, output_schema)
nimble --client-source nimble-agent-skills agents create --template <template_name>
```

**Key `agents create` flags:** `--agent-name` (stable name), `--display-name`,
`--description`, `--sources`, `--output-schema`, `--effort`,
`--skill`, `--suggested-question` (repeatable), `--use-case`, `--template`, `--is-active`.

---

## Run lifecycle: create → status → result

Runs are **asynchronous**: create, reach a terminal state, then fetch the result.

```bash
# 2. Poll status until terminal (completed | failed | cancelled) — wait ~15–30s between polls
nimble --client-source nimble-agent-skills agents:runs get \
  --agent-id <agent_id> --run-id <run_id>

# 3. Fetch the output once completed
nimble --client-source nimble-agent-skills agents:runs result \
  --agent-id <agent_id> --run-id <run_id>
```

**Run states:** `queued` → (running) → terminal: `completed`, `failed`, or `cancelled`. List
an agent's runs newest-first with `nimble agents:runs list --agent-id <id>`.

Fetching `result` before the run is terminal returns **`409` — "Run still active; poll the run
status endpoint"**. That is a timing signal, not an error to retry blindly: go back to
`agents:runs get`.

---

## Live progress: events, and polling as the fallback

**On the CLI, events work** (verified on 1.2.0). Create the run with `--enable-events`, then
consume the stream:

```bash
nimble --client-source nimble-agent-skills agents run \
  --agent-name <name> --enable-events --input "..." --effort high

nimble --client-source nimble-agent-skills agents:runs stream-events \
  --agent-id <agent_id> --run-id <run_id> [--max-items <n>]
```

Events arrive as JSON objects with a `type`: `task_run.state` (carries the run's `status`),
`task_run.progress_msg.*` (`exec_status`, `plan`, …), and `task_run.progress_stats` (source
counts and a sample of URLs read).

**Termination behavior:** the stream **closes on its own** once the run reaches a terminal
state — the final `task_run.state` event carries `completed`. `--max-items <n>` closes it
after `n` events instead, leaving the run going. Either way the stream never carries the
output: fetch `agents:runs result` after it closes.

**On MCP, use bounded status polling instead** — the shell-less transport works on
request/response, so poll `nimble_agents_run_status` every ~15–30s, cap the total wait, and
report the run as still active if the cap is hit rather than hanging or declaring failure.
Polling is also the right approach in any host that can't hold a long-lived stream open.

---

## Effort tiers

Effort: 'high' is the default. 'low' (~20 s) for one closed fact; 'medium' (~3 min) for a short answer from a few sources; 'high' (~8 min, up to ~17) when several fields need real digging; 'x-high' (~12 min, up to ~28) only for a deep multi-source profile (financials, filings, history) the user explicitly wants exhaustive - measured quality is about the same as 'high'. Never 'max' (not available). dataset_building needs 'medium' or above. Set it yourself; do not ask the user to pick an effort.

| Tier | Typical duration (production p50 / p90) |
| --- | --- |
| `low` | ~20 s / ~50 s |
| `medium` | ~3 min / ~6 min |
| `high` (default) | ~8 min / ~17 min |
| `x-high` | ~12 min / ~28 min |

---

## Configuring a run well (guidance v2, shared with the Nimble MCP server)

- Effort: 'high' is the default. 'low' (~20 s) for one closed fact; 'medium' (~3 min) for a short answer from a few sources; 'high' (~8 min, up to ~17) when several fields need real digging; 'x-high' (~12 min, up to ~28) only for a deep multi-source profile (financials, filings, history) the user explicitly wants exhaustive - measured quality is about the same as 'high'. Never 'max' (not available). dataset_building needs 'medium' or above. Set it yourself; do not ask the user to pick an effort.
- One run per request: put all entities in a single run (dataset_building and enrichment take lists; enrichment input_data holds up to 40 rows / 200 cells). Split into more runs only above those limits, and never have more than 3 runs in flight. For research that needs several sources, use one Web Search Agent run instead of many nimble_search / nimble_extract calls.
- Write a task-specific skill (3-5 sentences), never a generic one: (1) the role, e.g. 'You are a B2B firmographics researcher'; (2) how to resolve the entity (name, domain, ticker; disambiguate same-name entities and say which one you chose); (3) source priority: the official/primary source first for exact or time-sensitive facts (company site, investor relations, regulator, registry), aggregators only to fill gaps; (4) freshness window if the user gave one; (5) output rules: 'Unknown' instead of guessing, cite a source URL for every fact.
- For any list, table, comparison or 'for each X' ask, pass an output_schema: an array of objects whose property names are the user's own field names verbatim, all strings unless the user asked for numbers.
- Sources shape: {"allow": [{"title": "Official filings", "domains": ["sec.gov"]}, ...], "block": [{"title": "...", "domains": [...]}], "prioritize": "free text", "avoid": "free text"}. allow/block items are groups with a short title and a list of domains (a plain list of domains is also accepted). An allow list is a hard limit on where the agent searches; use it only when the user restricts sources. Otherwise put source preferences in 'prioritize'.
- Source priority by kind of task (put the relevant line into 'prioritize' or the skill): companies / lead gen -> company website, LinkedIn company page, official registry; financial figures -> investor relations, SEC/EDGAR or the local regulator before aggregators; people / recruiting -> LinkedIn profile, company team page, official bios; e-commerce / products -> the brand or retailer product page, then marketplaces; real estate -> the listing portal and official property records; healthcare -> official registries (e.g. NPI, clinicaltrials.gov), regulator, provider site; regulatory / legal -> the official gazette, regulator or court site.
- Ask the user only when the request leaves out something that decides a config field, and map every answer into that field: which entity -> input + skill; which fields/format -> output_schema; time window -> input + skill; sources to trust or avoid -> sources; how long they can wait -> effort; how many items -> use_case/effort. Do not ask anything that would not change the config.
- After starting a run, keep this turn open: tell the user the expected time, then poll nimble_agents_run_status at the suggested interval until it is terminal, call nimble_agents_run_result, and present the answer with its citations. Do not hand the waiting to a background task or end the turn before the result is shown; a run nobody fetches is wasted.

---

## Authoring a from-scratch agent

When creating from scratch, fill each field deliberately (adapted from Nimble's own agent
configuration guidance):

- **Domain Expertise** (`--skill`) — a dense role paragraph, under five sentences: who the
  agent is for this use case; how to handle inputs supplied in more than one format; which
  source to check first for which fact; how to handle data that can't be found (say
  "Unknown," never invent); and whether to return a per-field confidence indicator.
- **Goals** — deprecated; do not set them. Put the agent's objectives in the skill and the run input.
- **Sources** (`--sources`) — priority-ordered groups per the shape above, most important
  first.
- **Output** (`--output-schema`) — use the user's own field names; use plain strings for
  ranges/estimates ("50 to 200 employees", not an invented number); group related fields into
  nested structures and use lists for anything naturally a list; mark required vs optional.
- **Use case** (`--use-case`) — pick deliberately; it locks on creation.
- **Effort** — per the tiers above.

Also draft a recommended starting prompt for the first run based on the conversation.

---

## Trust & citations

`agents:runs result` returns an `output` that is either `type: "text"` (a prose answer) or
`type: "json"` (structured data matching the output schema), **plus `trust` metadata**:

- `trust.sources` — every source used, with `title`, `url`, `type`, and `source_category`.
- `trust.claims` — per-claim citations with `excerpts` and a `confidence`. Structured outputs
  anchor each claim to a JSON path (`$.founded_year`); text outputs anchor to a numbered
  callout in the prose.
- `trust.confidence` + `trust.reasoning` — a run-level judgement and why.

Surface the citations alongside the answer — every claim should trace to a source. This is
what makes a Web Search Agent's answer verifiable rather than an unsourced summary. Treat
`confidence: "pre_existing"` claims as caller-supplied input, not findings.

---

## MCP fallback — transport differences

Shell-less hosts use the production Nimble MCP server. Run parameters carry over — the run
tool takes `agent_id`, `agent_name` (create-or-reuse, same semantics as Mode 1), `use_case`,
`skill`, `sources`, `output_schema`, `input_data`, and `effort`.

**One routing rule to know:** `nimble_agents_run` takes **either** `agent_id` **or**
`agent_name` — always pass one. Sending neither returns *"Provide either `agent_id` (run an
existing agent) or `agent_name` (create-or-reuse by name)."* On MCP, then, reach for a
Mode 1 `agent_name` wherever you'd have used Mode 3 on the CLI. That's the better default
anyway: a named agent is reusable next session, which is exactly what Mode 3 gives up.

| Capability                           | CLI                              | MCP                                        |
| ------------------------------------ | -------------------------------- | ------------------------------------------ |
| Mode 1 — named create-or-reuse       | ✅                                | ✅ (`nimble_agents_run` + `agent_name`)     |
| Mode 2 — explicit agent              | ✅                                | ✅ (`nimble_agents_run` + `agent_id`)       |
| Mode 3 — caller-anonymous            | ✅                                | Pass an `agent_name` — one identity is required |
| Discovery / inspect                  | ✅                                | ✅ (`nimble_agents_list`, `nimble_agents_get`, `nimble_agent_templates_list` / `_get`) |
| Status → result                      | ✅                                | ✅ (`nimble_agents_run_status`, `nimble_agents_run_result`) |
| Live events                          | ✅ `--enable-events` + `stream-events` | Use bounded status polling instead     |
| `previous_interaction_id`            | ✅                                | Start a fresh run with the prior context restated in `input` |
| `--client-source nimble-agent-skills`| ✅ on every call                  | Attributed at the transport level — don't try to override it |

---

## Failure handling

| Signal                                                              | What it means                                            | Do this                                                        |
| ------------------------------------------------------------------- | -------------------------------------------------------- | -------------------------------------------------------------- |
| `409` "Run still active"                                            | Fetched `result` before the run finished                 | Go back to `agents:runs get`; don't hammer `result`            |
| `404` "Run '…' not found for agent"                                 | Wrong `run_id`/`agent_id` pairing                        | Re-read the IDs from the create response                       |
| `422` `use_case cannot be changed for an existing agent`            | Locked `use_case` mismatch                               | Omit `--use-case`, match it, or use a different agent          |
| `422` "Input should be 'research', 'enrichment' or 'dataset_building'" | Invalid enum value                                    | Use one of the three exactly                                   |
| `422` `output_schema is required when use_case is dataset_building` | Missing schema on a dataset run                          | Supply `--output-schema`                                       |
| `422` `dataset_building requires effort 'high' or higher`           | Effort too low for a dataset run                         | Raise to `high` or above                                       |
| `422` on `sources`                                                  | Wrong shape, or a group missing `title`                  | `allow`/`block` = arrays of objects, each with a `title`; `prioritize`/`avoid` = strings |
| `Required flag "agent-id" not set`                                  | Used `agents:runs create` for a Mode 1 / Mode 3 run      | Switch to `nimble agents run`                                  |
| Run reaches `failed` / `cancelled`                                  | A real outcome                                           | Report it plainly; suggest broadening sources or raising effort |

- Poll `agents:runs get` until a terminal state; don't fetch `result` before `completed`.
- `failed` / `cancelled` are real outcomes — report them plainly, don't present a partial or
  empty result as success. Suggest an obvious next step (broaden sources, raise effort, or a
  different capability) where one exists.
- Never work around a missing/blocked transport with WebFetch, WebSearch, or curl.

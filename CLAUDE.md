# CLAUDE.md

## What this repo is

**Nimble Web Search Skills** — agent skills that give any AI agent the ability to search, scrape, and extract structured data from any website using the Nimble CLI. Built following the [Agent Skills specification](https://agentskills.io/specification.md), compatible with Claude Code, Codex, Cursor, and any agent platform that supports the spec.

Two layers of skills:
- **Core data skill** (`skills/nimble-web-expert/`) — the raw capabilities: fetch a URL, run a search, map/crawl a site, run Extraction Templates, and run Web Search Agents
- **Business intelligence skills** (every other skill) — one-command workflows that turn live web data into actionable reports

See `.claude-plugin/marketplace.json` for the full list of published skills.

Business skills are built on top of the core skill — they call `nimble search` / `nimble extract`, run Extraction Templates for structured site data, and run Web Search Agents for open-ended research, under the hood.

## Prerequisites

```bash
npm i -g @nimble-way/nimble-cli
export NIMBLE_API_KEY="your-key"   # or set in ~/.claude/settings.json under env
```

## Repo structure

```
skills/
  {skill-name}/                  # Each skill is a DIRECT child of skills/
    SKILL.md                     #   Skill definition (frontmatter + instructions)
    references/                  #   On-demand docs, loaded when needed (reference.md, never SKILL.md)
agents/                          # Shared sub-agent definitions (.md with frontmatter)
_shared/                         # Canonical shared references (synced into skills)
assets/                          # Plugin listing assets (logo, composer icon)
.claude-plugin/plugin.json       # Claude Code plugin manifest
.cursor-plugin/plugin.json       # Cursor plugin manifest
.codex-plugin/plugin.json        # OpenAI / Codex plugin manifest
.grok-plugin/plugin.json         # xAI / Grok Build plugin manifest
plugin.json                      # Portable Agent Plugins manifest
.mcp.json                        # Hosted MCP config — Claude Code Connector + Codex (Grok inline)
mcp.json                         # Portable Agent Plugins MCP config (different vocabulary)
commands/                        # Slash commands
scripts/                         # Repo tooling
```

### `skills/` must stay flat

**Every skill directory is an immediate child of `skills/`. Never add a grouping
subdirectory.** This is a hard platform requirement, not a style preference:

- **OpenAI / Codex** rejects nesting at submission — `skill_manifest_nested` ("Each skill
  directory must be an immediate child of `skills/`"), and a grouping folder without its own
  `SKILL.md` additionally trips `skill_manifest_missing`. Errors block submission. The array
  form of `skills` is rejected too (`plugin_skills_path_wrong_type`), so there is no
  manifest-side alternative.
- **xAI** indexes only direct children of `skills/`, so a nested skill does not appear in
  the plugin index.

Runtime discovery in Claude Code and Codex *is* recursive, so a nested skill can appear to
work locally while being absent from both catalogs. Don't rely on local behavior here.

Verticals are recorded as `metadata.category` in each `SKILL.md` frontmatter:

```yaml
metadata:
  author: Nimbleway
  version: 1.4.0
  category: business-research
```

Add a new category by setting `metadata.category`, not by creating a folder.

The four plugin manifests (`.claude-plugin/plugin.json`, `.cursor-plugin/plugin.json`,
`.codex-plugin/plugin.json`, `.grok-plugin/plugin.json`) point at `./skills/`, so they need no per-skill path.
`.claude-plugin/marketplace.json` enumerates skills individually — add an entry there when you
add a skill, plus an `agents` update if applicable. That enumeration is deliberate: it gives
consumers that scan recursively an explicit list rather than a filesystem walk.

Reference documents inside a skill's `references/` directory are named `reference.md`, never
`SKILL.md` — see [Naming & structure](#naming--structure). `bash scripts/check-plugin-structure.sh`
enforces the flat tree, the `reference.md` convention, and the marketplace enumeration together.

### The two MCP config files are not duplicates

**Do not merge `mcp.json` into `.mcp.json`, or "harmonise" their `type` values.** They describe
the same endpoint in vocabularies that are mutually exclusive:

| File | Consumer | Transport declared as |
|---|---|---|
| `mcp.json` | Agent Plugins v1.0.0 (portable) | `"type": "streamable-http"` — a schema `const` |
| `.mcp.json` | Claude Code, and the Codex manifest's `mcpServers` path | `"type": "http"` |
| — | Codex | no `type` key at all; HTTP inferred from `url` |

The portable schema sets `additionalProperties: false` at the root *and* on every server, so one
file cannot carry both. `.mcp.json` is what Claude Code auto-registers as a Connector over native
HTTP with OAuth — the primary install path — so it is the one that must not move.

Root `mcp.json` is the spec's canonical path and is validated in CI against the published schema:
`$schema` must be the exact canonical identifier, only `$schema` and `mcpServers` are permitted at
the top level, and each server's `type` must be one of `stdio`, `streamable-http`, or `sse`.
Pasting Claude's `"type": "http"` in there fails with `portable_mcp_transport_invalid`.

Note that Cursor does **not** read this repository's root `mcp.json` — a Cursor user pastes the
snippet into their own `.cursor/mcp.json`. An earlier changelog entry described root `mcp.json` as
"preserved for Cursor compatibility"; that was inaccurate.

## Commands

```bash
# Sync _shared/ references into business skill references/ folders
bash scripts/sync-shared.sh

# Test a skill locally — trigger it by name in a Claude Code session
claude "run competitor-intel for acme.com"

# Routing eval — does nimble-web-expert pick the right capability per prompt?
# Reads the routing text out of SKILL.md, so eval and doc can't drift. No
# Nimble calls, no credits, no API key.
python3 scripts/run-routing-eval.py --runs 3

# Production CLI eval — run nimble-web-expert via Claude/Codex against the
# private Langfuse dataset. See evals/README.md.
# Prompts/traces are never committed to this public repo.
cd evals && uv sync
uv run python -m evals.suites.web_expert \
  --dataset-name=nimble-web-expert-production --runtime claude --max-items 50

# Packaging gates — all three run in CI on every PR
bash scripts/tag-release.sh --check           # all version references agree
bash scripts/check-plugin-structure.sh        # skills tree is packageable everywhere
python3 scripts/check-plugin-manifests.py     # manifest fields, assets, brand contrast
```

Run the routing eval after any change to `nimble-web-expert`'s Core principles
or Analyze & Route sections. Cases live in `evals/nimble-web-expert-routing.json`;
add one whenever a mis-route is found in the wild. A failing case is not
automatically a doc bug — check whether the expectation is right first.

Run the production CLI eval (`evals/`) when changing skill load behavior, CLI
routing to Nimble commands, or before a release that touches `nimble-web-expert`.
Results stay out of git — see `evals/README.md`.

## Skill authoring

Every skill follows the [Agent Skills specification](https://agentskills.io/specification.md). Key rules for this repo:

### Writing style
- Clarity over cleverness. Specific over vague. Active voice over passive.
- Short paragraphs (2-4 sentences). One idea per section. Exception: intro taglines (one sentence after `# Skill Name`) are intentionally short.
- Challenge every token: "Does the agent really need this to do the job?"
- Say nothing notable rather than padding with fluff.

### Naming & structure
- Name: `{domain}-{action}`, lowercase, hyphenated. Folder name must match frontmatter `name`.
- The folder must sit directly under `skills/` — no grouping subdirectory (see [`skills/` must stay flat](#skills-must-stay-flat)). Set `metadata.category` for the vertical.
- Aim to keep SKILL.md under ~500 lines. Use progressive disclosure: frontmatter (always loaded) → body (on trigger) → `references/` directory (on demand). The `references/` directory IS the dedicated deeper layer — SKILL.md does not need a `## References` heading.
- **Never name a reference document `SKILL.md`.** Use `reference.md`. Codex reads a
  `.codex-plugin/plugin.json` as a Legacy-format manifest and scans for `SKILL.md`
  recursively, so a reference document named `SKILL.md` registers as a real skill in the
  model-visible catalog. `bash scripts/check-plugin-structure.sh` fails on any `SKILL.md`
  under a `references/` directory.
- The frontmatter `description` must stay within **1024 characters** — OpenAI rejects a
  longer one with `skill_description_too_long`, and `check-plugin-structure.sh` measures it.

### SKILL.md frontmatter
```yaml
---
name: skill-name
description: |
  [What it does] + [When to use it] + [Key capabilities]. Max 1024 chars.
  Third-person voice. Include trigger phrases and negative triggers (use "Do NOT use for X — use Y instead" format).
allowed-tools:
  - Bash(nimble:*)
  - Bash(date:*)
metadata:
  author: Nimbleway
  version: 1.0.0
---
```

### DRY
- Shared patterns live in `_shared/` — edit there, then `bash scripts/sync-shared.sh`. The sync script copies `_shared/` files into each skill's `references/` directory — these synced copies are expected and not duplication.
- Never manually copy-paste shared logic into a SKILL.md — reference it via `references/`.
- Skill-specific logic (output format, entity research, agent team composition) stays in SKILL.md.
- When referencing shared patterns from SKILL.md, say "do X" and point to the playbook for "how X works" — don't restate the pattern inline.
- The restatement test: if `_shared/nimble-playbook.md` changed, would SKILL.md become
  wrong? If yes, SKILL.md is restating, not referencing. Grep for shared pattern
  signatures (`nimble map`, `nimble extract --`, `--render`, scaling tier tables) — if
  found inline in SKILL.md, it's a DRY violation.
- If a skill has multiple execution paths (e.g., geographic vs SaaS), each path must be first-class with its own discovery, scoring, output template, and error handling.

### Data access
- Use `nimble search` / `nimble extract` via Bash for web data access.
- Two structured-data families (CLI 1.2.0+): **Extraction Templates** (`extract:templates
  list`/`get --extract-template-name`/`run --template`) for site-specific structured
  scrapers, and **Web Search Agents** (`agents:templates`, `agents create`, `agents run`,
  `agents:runs create`/`get`/`result`/`stream-events`) for open-ended research/enrichment
  with trust/citations. The singular `nimble agent …` group is retired.
- WSA runs have three modes — named create-or-reuse (`agents run --agent-name`, the
  default), explicit agent ID (`agents:runs create --agent-id`, which *requires* the ID),
  and caller-anonymous (`agents run` with neither). `use_case` (`research` / `enrichment` /
  `dataset_building`) locks on agent creation; run-level `skill` overrides once. Full
  contract: `skills/nimble-web-expert/references/nimble-agents/reference.md`.
- Template/agent names are dynamic — never hardcode them. `extract:templates list`,
  `agents list`, and `agents:templates list` have no server-side search: list and filter
  client-side (by domain, keyword, entity_type). Web Search Agents follow the
  reuse-priority chain (existing agent → clone a template → from scratch). Validate a
  template's `input_schema` before running.
- WSA reference files must teach discovery strategy, not list known agents. The test:
  if 10 new agents/templates were added tomorrow, would the skill find them automatically?
- `--search-depth` valid values: `lite`, `fast`, `deep` (not `standard`). Use `lite` for discovery, `deep` for full content.
- All Nimble calls carry `--client-source nimble-agent-skills` (the stable integration attribution).
- Always verify CLI commands with real data before writing them into SKILL.md — `--help` alone isn't enough.

### Agent definitions (`agents/`)

Agent files are `.md` files with YAML frontmatter + a Markdown system prompt:

```yaml
---
name: agent-name              # required — lowercase, hyphenated
description: When to use...   # required — helps Claude decide when to delegate
model: haiku                  # haiku | sonnet | opus (default: inherit)
tools:                        # optional — inherits all if omitted
  - Bash
  - Read
  - Grep
---
```

Skills spawn agents with `mode: "bypassPermissions"` (they don't inherit parent permissions). Max 4 concurrent. Always include a fallback if an agent fails.

### Output quality
- Every signal must have a verified event date + clickable source URL.
- TL;DR first, then structured sections, then "What This Means".
- Deduplicate against `~/.nimble/memory/` before reporting — only surface new findings.

## Publishing

Four plugin manifests declare the same shared `skills/` tree, one per platform:

| Manifest | Platform | `skills` field | MCP declared as |
|---|---|---|---|
| `.claude-plugin/plugin.json` | Claude Code | array of paths (`["./skills/"]`) | root `.mcp.json` (auto) |
| `.cursor-plugin/plugin.json` | Cursor | string path (`"./skills/"`) | root `mcp.json` |
| `.codex-plugin/plugin.json` | OpenAI / Codex | string path (`"./skills/"`) | `"./.mcp.json"` |
| `.grok-plugin/plugin.json` | xAI / Grok Build | string path (`"./skills/"`) | **inline object** |

They point at the directory, not at individual skills, so adding a skill needs no manifest
path. `.claude-plugin/marketplace.json` is the exception — it enumerates skills individually,
so **add an entry there when you add a skill**, plus an `agents` update if applicable.

### Why the Grok manifest declares MCP inline

**Do not "simplify" `.grok-plugin/plugin.json`'s `mcpServers` to `"./.mcp.json"`.** It looks
tidier and silently breaks the Grok listing. `scripts/check-plugin-manifests.py` fails on it.

xAI's indexer (`scripts/plugin_catalog.py` in `xai-org/plugin-marketplace`, verified 2026-08-09)
reads a `.mcp.json` file's `mcpServers` key and nothing else. This repo's `.mcp.json` is a bare
server map with no such key, so a path declaration indexes **zero** servers and Grok Build's
catalog would claim the plugin ships no MCP server at all. If xAI later accepts a bare map, this
rationale is what to re-check — the CI guard asserts our two copies agree, not their parser.

The obvious fix — adding an `mcpServers` wrapper to `.mcp.json` — is the wrong one. That file is
what Claude Code auto-registers as a Connector over native HTTP with OAuth, and it is the primary
install path. Declaring inline keeps `.mcp.json` byte-identical, so Claude behaviour cannot
regress, and it leaves OpenAI's path declaration valid too (OpenAI documents the bare map).

The cost is one duplicated server config, and CI asserts the copies never drift.

The Codex manifest carries an `interface` block with the listing metadata OpenAI shows at
install time, and `mcpServers` pointing at the root `.mcp.json` shared with Claude Code. Its
hard limits are enforced at submission, so keep them in mind when editing: `interface.logo`
and `interface.composerIcon` are both required and must be square images; `brandColor` needs
at least 2:1 contrast against white and `brandColorDark` at least 2:1 against `#212121`;
`defaultPrompt` allows at most three entries; and `category` must come from OpenAI's fixed
list.

`python3 scripts/check-plugin-manifests.py` asserts all of that, naming each failure after
the error code OpenAI would raise. Run it after editing any manifest, and
`bash scripts/check-plugin-structure.sh` after any change to the skills tree — CI runs both.

### Version bumps

`.claude-plugin/plugin.json` is the source of truth. A bump must touch every reference: all
four `plugin.json` manifests, `marketplace.json`, the `README.md` badge, and every
`skills/**/SKILL.md` `metadata.version` field (some quote the value, some don't). The checker
below prints the live count, so don't rely on a number written down here.

**Do not search-and-replace the bare version string** — it also matches CHANGELOG history and
Nimble CLI version references like `CLI 1.1.0+`, which must not be rewritten. Anchor each
replacement to its context: `"version": "X"` in the JSON files, `version-X-green` in the README
badge, and an indented `version:` key inside `SKILL.md` frontmatter.

Verify with:

```bash
bash scripts/tag-release.sh --check
```

This is the same assertion CI runs on every PR, so a partial bump fails the build. It ignores
illustrative `version:` values in documentation examples — only real references are enforced.

### Cutting a release

After a version-bump PR merges to `main`:

```bash
git checkout main && git pull
bash scripts/tag-release.sh      # verifies, then creates the annotated tag
git show v1.4.0                  # review the notes
git push origin v1.4.0           # deliberate, manual
```

The tag message is taken from that version's `CHANGELOG.md` section, so the notes must be
written before tagging. The script refuses to run on a dirty worktree, off `main`, or when the
tag already exists — and it never pushes. **A published tag is never moved**; if a release is
wrong, cut a new version.

Note that both Anthropic marketplaces pin this plugin by commit SHA rather than by tag, so a tag
is a named rollback target and release-notes anchor, not the distribution mechanism.

## Memory Wiki Architecture

`~/.nimble/memory/` is a local web knowledge wiki with Obsidian-compatible `[[wikilinks]]`.
Architecture documented in `_shared/memory-and-distribution.md` — read it before modifying
memory patterns. Per-directory indexes are optimizations, not gates — always fall back to
reading files directly if index is missing.
- When removing skill-specific error handling in favor of shared playbook, verify the playbook covers all error types being removed

## Conventions

- Commits: conventional commits (`feat:`, `fix:`, `test:`, `docs:`)
- Branches: `{type}/{short-description}` (e.g., `feat/new-skill`)
- Skills persist data under `~/.nimble/` — never touch user project files
- Reports: `{skill-name}-{YYYY-MM-DD}.md`
- Never commit secrets, API keys, or credentials — even as examples

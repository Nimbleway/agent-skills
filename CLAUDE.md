# CLAUDE.md

## What this repo is

**Nimble Web Search Skills** — agent skills that give any AI agent the ability to search, scrape, and extract structured data from any website using the Nimble CLI. Built following the [Agent Skills specification](https://agentskills.io/specification.md), compatible with Claude Code, Codex, Cursor, and any agent platform that supports the spec.

Two layers of skills:
- **Core data skills** (`skills/web-search-tools/`) — the raw capabilities: fetch a URL, run a search, build a reusable extraction agent
- **Business intelligence skills** (all other verticals) — one-command workflows that turn live web data into actionable reports

See `.claude-plugin/marketplace.json` for the full list of published skills.

Business skills are built on top of core skills — they call `nimble search` / `nimble extract` under the hood. The two core skills also form a feedback loop: web-expert runs agents built by agent-builder, and when a one-off lookup becomes recurring, agent-builder turns it into a reusable pipeline.

## Prerequisites

```bash
npm i -g @nimble-way/nimble-cli
export NIMBLE_API_KEY="your-key"   # or set in ~/.claude/settings.json under env
```

## Repo structure

```
skills/
  {vertical}/                    # Skills grouped by vertical
                                 #   business-research/, healthcare/, marketing/,
                                 #   productivity/, web-search-tools/
    {skill-name}/                #   Each skill = SKILL.md + optional references/
      SKILL.md                   #   Skill definition (frontmatter + instructions)
      references/                #   On-demand docs, loaded when needed
agents/                          # Shared sub-agent definitions (.md with frontmatter)
_shared/                         # Canonical shared references (synced into skills)
.claude-plugin/plugin.json       # Claude Code plugin manifest
.cursor-plugin/plugin.json       # Cursor plugin manifest
commands/                        # Slash commands
scripts/                         # Repo tooling
```

Verticals are just grouping folders — add new ones freely. `.claude-plugin/plugin.json` lists vertical directories explicitly; `.cursor-plugin/plugin.json` points to `./skills/` (all verticals). Update the relevant manifest when adding or removing verticals or agents.

## Commands

```bash
# Sync _shared/ references into business skill references/ folders
bash scripts/sync-shared.sh

# Test a skill locally — trigger it by name in a Claude Code session
claude "run competitor-intel for acme.com"
```

## Skill authoring

Every skill follows the [Agent Skills specification](https://agentskills.io/specification.md). Key rules for this repo:

### Writing style
- Clarity over cleverness. Specific over vague. Active voice over passive.
- Short paragraphs (2-4 sentences). One idea per section. Exception: intro taglines (one sentence after `# Skill Name`) are intentionally short.
- Challenge every token: "Does the agent really need this to do the job?"
- Say nothing notable rather than padding with fluff.

### Naming & structure
- Name: `{domain}-{action}`, lowercase, hyphenated. Folder name must match frontmatter `name`.
- Aim to keep SKILL.md under ~500 lines. Use progressive disclosure: frontmatter (always loaded) → body (on trigger) → `references/` directory (on demand). The `references/` directory IS the dedicated deeper layer — SKILL.md does not need a `## References` heading.

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
- WSA names are dynamic — never hardcode them in skills or reference files, not even
  Nimble-managed agents. Discover at runtime using 3 layers: (1) vertical search
  (`nimble agent list --search "healthcare"`), (2) session-specific search (user's
  specialty, directories they mention), (3) general tools (`google_maps`, `yelp`, `bbb`).
  Validate with `nimble agent get --template-name {name}` before running.
- WSA reference files must teach discovery strategy, not list known agents. The test:
  if 10 new WSAs were added tomorrow, would the skill find them automatically?
- `--search-depth` valid values: `lite`, `fast`, `deep` (not `standard`). Use `lite` for discovery, `deep` for full content.
- `nimble agent list --limit` max is 250.
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

Plugin manifests live in `.claude-plugin/plugin.json` and `.cursor-plugin/plugin.json`. They declare which `skills/` directories and `agents/` files are included. Update these when adding or removing a skill.

When adding a new skill, also add it to `.claude-plugin/marketplace.json` `skills` array. Version bump (minor) must touch ALL files: both plugin.json manifests, marketplace.json, README.md badge, and every `skills/**/SKILL.md` `metadata.version` field. Grep for the version number itself (e.g., `0.12.1`) — some files quote it (`"0.12.1"`), some don't.

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

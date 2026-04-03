# CLAUDE.md

## What this repo is

**Nimble Web Search Skills** — agent skills that give any AI agent the ability to search, scrape, and extract structured data from any website using the Nimble CLI. Built following the [Agent Skills specification](https://agentskills.io/specification.md), compatible with Claude Code, Codex, Cursor, and any agent platform that supports the spec.

Two layers of skills:
- **Core data skills** (`nimble-web-expert`, `nimble-agent-builder`) — the raw capabilities: fetch a URL, run a search, build a reusable extraction agent
- **Business intelligence skills** (`competitor-intel`, `meeting-prep`, `company-deep-dive`, `competitor-positioning`) — one-command workflows that turn live web data into actionable reports

Business skills are built on top of core skills — they call `nimble search` / `nimble extract` under the hood. The two core skills also form a feedback loop: web-expert runs agents built by agent-builder, and when a one-off lookup becomes recurring, agent-builder turns it into a reusable pipeline.

## Prerequisites

```bash
npm i -g @nimble-way/nimble-cli
export NIMBLE_API_KEY="your-key"   # or set in ~/.claude/settings.json under env
```

## Repo structure

```
skills/
  {vertical}/                    # Skills grouped by vertical (e.g., web-search-tools/)
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
- Short paragraphs (2-4 sentences). One idea per section.
- Challenge every token: "Does the agent really need this to do the job?"
- Say nothing notable rather than padding with fluff.

### Naming & structure
- Name: `{domain}-{action}`, lowercase, hyphenated. Folder name must match frontmatter `name`.
- Aim to keep SKILL.md under ~500 lines. Use progressive disclosure: frontmatter (always loaded) → body (on trigger) → `references/` (on demand).

### SKILL.md frontmatter
```yaml
---
name: skill-name
description: |
  [What it does] + [When to use it] + [Key capabilities]. Max 1024 chars.
  Third-person voice. Include trigger phrases and negative triggers.
allowed-tools:
  - Bash(nimble:*)
  - Bash(date:*)
metadata:
  author: Nimbleway
  version: 1.0.0
---
```

### DRY
- Shared patterns live in `_shared/` — edit there, then `bash scripts/sync-shared.sh`.
- Never copy-paste shared logic into a SKILL.md — reference it.
- Skill-specific logic (output format, entity research, agent team composition) stays in SKILL.md.

### Data access
- Use `nimble search` / `nimble extract` via Bash for web data access.

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

## Conventions

- Commits: conventional commits (`feat:`, `fix:`, `test:`, `docs:`)
- Branches: `{type}/{short-description}` (e.g., `feat/new-skill`)
- Skills persist data under `~/.nimble/` — never touch user project files
- Reports: `{skill-name}-{YYYY-MM-DD}.md`
- Never commit secrets, API keys, or credentials — even as examples

# CLAUDE.md

## What this repo is

**Nimble Web Search Skills** — agent skills that give any AI agent the ability to search, scrape, and extract structured data from any website using the Nimble CLI. Built following the [Agent Skills specification](https://agentskills.io/specification.md), compatible with Claude Code, Codex, Cursor, and any agent platform that supports the spec.

Two layers of skills:
- **Core data skill** (`skills/web-search-tools/nimble-web-expert/`) — the raw capabilities: fetch a URL, run a search, map/crawl a site, run Extraction Templates, and run Web Search Agents
- **Business intelligence skills** (all other verticals) — one-command workflows that turn live web data into actionable reports

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

# Routing eval — does nimble-web-expert pick the right capability per prompt?
# Reads the routing text out of SKILL.md, so eval and doc can't drift. No
# Nimble calls, no credits, no API key.
python3 scripts/run-routing-eval.py --runs 3
```

Run the routing eval after any change to `nimble-web-expert`'s Core principles
or Analyze & Route sections. Cases live in `evals/nimble-web-expert-routing.json`;
add one whenever a mis-route is found in the wild. A failing case is not
automatically a doc bug — check whether the expectation is right first.

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
- Two structured-data families (CLI 1.2.0+): **Extraction Templates** (`extract:templates
  list`/`get --extract-template-name`/`run --template`) for site-specific structured
  scrapers, and **Web Search Agents** (`agents:templates`, `agents create`, `agents run`,
  `agents:runs create`/`get`/`result`/`stream-events`) for open-ended research/enrichment
  with trust/citations. The singular `nimble agent …` group is retired.
- WSA runs have three modes — named create-or-reuse (`agents run --agent-name`, the
  default), explicit agent ID (`agents:runs create --agent-id`, which *requires* the ID),
  and caller-anonymous (`agents run` with neither). `use_case` (`research` / `enrichment` /
  `dataset_building`) locks on agent creation; run-level `skill` overrides once. Full
  contract: `skills/web-search-tools/nimble-web-expert/references/nimble-agents/SKILL.md`.
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

Plugin manifests live in `.claude-plugin/plugin.json` and `.cursor-plugin/plugin.json`. They declare which `skills/` directories and `agents/` files are included. Update these when adding or removing a skill.

When adding a new skill, also add it to `.claude-plugin/marketplace.json` `skills` array.

### Version bumps

`.claude-plugin/plugin.json` is the source of truth. A bump must touch every reference: both
`plugin.json` manifests, `marketplace.json`, the `README.md` badge, and every
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
git show v1.2.0                  # review the notes
git push origin v1.2.0           # deliberate, manual
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

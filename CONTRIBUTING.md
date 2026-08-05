# Contributing

Want to add a new web data skill? Great — the more workflows this plugin covers, the more useful it becomes for everyone.

## Quick overview

Each skill is a `SKILL.md` file inside `skills/{vertical}/{skill-name}/`. Skills are grouped into verticals like `business-research/`, `marketing/`, `productivity/`, and `web-search-tools/`. New verticals are welcome.

## How to add a skill

The fastest way is to use an AI agent (Claude Code, Cursor, etc.) pointed at this repo. The repo's `CLAUDE.md` contains all the conventions, naming rules, frontmatter structure, shared reference patterns, and testing guidelines an agent needs to build a skill correctly.

If you prefer to do it manually:

1. Read `CLAUDE.md` at the repo root — it covers repo structure, skill anatomy, and authoring rules
2. Look at an existing skill (e.g., `skills/competitor-intel/SKILL.md`) as a template
3. Create your skill folder directly under `skills/` — never inside a grouping subdirectory — and set `metadata.category` in the frontmatter to record its vertical
4. Register it in `.claude-plugin/marketplace.json` (the plugin manifests already point at `./skills/`, so no per-skill path entry is needed)
5. Test it locally: `claude "run {skill-name} for acme.com"`

## Conventions

- **Commits:** conventional commits (`feat:`, `fix:`, `test:`, `docs:`)
- **Branches:** `{type}/{short-description}` (e.g., `feat/new-skill`)
- **No secrets:** never commit API keys or credentials, even as examples

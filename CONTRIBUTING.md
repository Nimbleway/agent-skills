# Contributing

Want to add a new web data skill? Great — the more workflows this plugin covers, the more useful it becomes for everyone.

## Quick overview

Each skill is a `SKILL.md` file inside `skills/{vertical}/{skill-name}/`. Skills are grouped into verticals like `business-research/`, `marketing/`, `productivity/`, and `web-search-tools/`. New verticals are welcome.

## How to add a skill

The fastest way is to use an AI agent (Claude Code, Cursor, etc.) pointed at this repo. The repo's `CLAUDE.md` contains all the conventions, naming rules, frontmatter structure, shared reference patterns, and testing guidelines an agent needs to build a skill correctly.

If you prefer to do it manually:

1. Read `CLAUDE.md` at the repo root — it covers repo structure, skill anatomy, and authoring rules
2. Look at an existing skill (e.g., `skills/business-research/competitor-intel/SKILL.md`) as a template
3. Create your skill folder under the right vertical in `skills/`
4. Register it in `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`
5. Test it locally: `claude "run {skill-name} for acme.com"`

## Conventions

- **Commits:** conventional commits (`feat:`, `fix:`, `test:`, `docs:`)
- **Branches:** `{type}/{short-description}` (e.g., `feat/new-skill`)
- **No secrets:** never commit API keys or credentials, even as examples

## Versions and releases

The plugin version is duplicated across both plugin manifests, `marketplace.json`, the README
badge, and every skill's `metadata.version`. `.claude-plugin/plugin.json` is the source of truth.

If your change warrants a version bump, bump all of them in one pass and check it:

```bash
bash scripts/tag-release.sh --check
```

CI runs the same check on every pull request, so a partial bump fails the build.

**Don't search-and-replace the bare version number.** It also matches CHANGELOG history and
Nimble CLI version references such as `CLI 1.1.0+`, which must stay as they are.

Add a `CHANGELOG.md` entry under a new `## [X.Y.Z] - YYYY-MM-DD` heading. Describe what changed
technically; the release tag's message is taken verbatim from that section.

Releases are tagged from `main` by a maintainer after merge (`bash scripts/tag-release.sh`).
Tags are pushed manually and never moved — if a release is wrong, a new version is cut.

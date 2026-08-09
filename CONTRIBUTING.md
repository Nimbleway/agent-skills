# Contributing

Want to add a new web data skill? Great — the more workflows this plugin covers, the more useful it becomes for everyone.

## Quick overview

Each skill is a `SKILL.md` file inside `skills/{skill-name}/` — always an immediate child of `skills/`, never inside a grouping subdirectory. The vertical is recorded as `metadata.category` in the frontmatter (`business-research`, `marketing`, `productivity`, `web-search-tools`, and others). New categories are welcome; add one by setting `metadata.category`, not by creating a folder.

Deeper documentation goes in the skill's `references/` directory. Name those files `reference.md` or anything descriptive — never `SKILL.md`, which some platforms would register as a separate skill.

## How to add a skill

The fastest way is to use an AI agent (Claude Code, Cursor, etc.) pointed at this repo. The repo's `CLAUDE.md` contains all the conventions, naming rules, frontmatter structure, shared reference patterns, and testing guidelines an agent needs to build a skill correctly.

If you prefer to do it manually:

1. Read `CLAUDE.md` at the repo root — it covers repo structure, skill anatomy, and authoring rules
2. Look at an existing skill (e.g., `skills/competitor-intel/SKILL.md`) as a template
3. Create your skill folder directly under `skills/` — never inside a grouping subdirectory — and set `metadata.category` in the frontmatter to record its vertical
4. Register it in `.claude-plugin/marketplace.json` (the plugin manifests already point at `./skills/`, so no per-skill path entry is needed)
5. Test it locally: `claude "run {skill-name} for acme.com"`
6. For `nimble-web-expert` changes, also run the production CLI eval (see `evals/README.md`)
   and/or the routing eval: `python3 scripts/run-routing-eval.py`
7. Check the packaging gates: `bash scripts/check-plugin-structure.sh` and, if you touched a
   manifest, `python3 scripts/check-plugin-manifests.py`

## Conventions

- **Commits:** conventional commits (`feat:`, `fix:`, `test:`, `docs:`)
- **Branches:** `{type}/{short-description}` (e.g., `feat/new-skill`)
- **No secrets:** never commit API keys or credentials, even as examples

## Versions and releases

The plugin version is duplicated across all four plugin manifests (Claude Code, Cursor, Codex,
and Grok Build), `marketplace.json`, the README badge, and every skill's `metadata.version`.
`.claude-plugin/plugin.json` is the source of truth.

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

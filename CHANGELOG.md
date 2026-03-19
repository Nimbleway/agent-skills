# Changelog

## [0.8.0] - 2026-03-08

### Changed
- **nimble-agents** skill renamed to **nimble-agent-builder** — clearer name that reflects its purpose (build, discover, and run structured-data agents)
  - Folder: `skills/nimble-agents/` → `skills/nimble-agent-builder/`
  - YAML `name:` field updated from `nimble-agents` to `nimble-agent-builder`
- **nimble-web-expert** skill — major structural overhaul (v2.0.0)
  - Rewritten as thin hub (~430 lines) with 12 load-on-demand reference files under `references/`
  - References reorganised into subfolders: `nimble-agents/`, `nimble-crawl/`, `nimble-extract/`, `nimble-map/`, `nimble-search/`
  - Added YAML `argument-hint`, `allowed-tools` (9 tools), `license`, and `metadata` fields
  - Added `$ARGUMENTS` variable at top of skill body
  - Added **Core principles** section (10 hard rules replacing prose CRITICAL BEHAVIOR block)
  - Added **Response shapes** table (all command/flag combinations with output shape and access pattern)
  - Added **Final response format** (Step 4 summary table + attribution)
  - Added **Guardrails** section (11 NEVER/hard rules consolidated at bottom)
  - Added `run_in_background=False` rule for all Task agents
  - Added Hard 429 rule and hard retry limit (max 2 on error)
  - Added AskUserQuestion format constraints: header ≤12 chars, label 1–5 words, `(Recommended)` first
  - All reference files gained YAML frontmatter (`name`, `description`)
  - Playwright added as free Tier 6 alternative to browser-use
  - Nimble Docs MCP section added (`claude mcp add nimble-docs`)
- Version bumped to 0.8.0 across all plugin configs
- README.md updated with new skill name and directory structure

## [0.7.0] - 2026-02-28

### Added
- **nimble-web-expert** skill — extract-first scraping expert replacing `nimble-web-tools`
  - Lean SKILL.md (~500 lines) covering extract, search, map, crawl, parallelization, and example workflows
  - 5 reference files: parsing-schema, browser-actions, network-capture, search-focus-modes, error-handling
  - 2 rules files: nimble-web-expert.mdc (routing), output.md (security)
  - Render escalation tiers (1-5): static → render → stealth → browser actions → network capture
  - Geo targeting, parser schemas, XHR mode for public APIs

### Removed
- **nimble-web-tools** skill (fully replaced by `nimble-web-expert`)

### Changed
- Version bumped to 0.7.0 across all plugin configs
- README.md updated with new skill name, directory structure, and examples
- `rules/nimble-tools.mdc` updated to reference nimble-web-expert

## [0.6.1] - 2026-02-24

### Changed
- **nimble-agents** skill — comprehensive rewrite for MCP reliability and best practices
  - Fixed `allowed-tools` prefix (`mcp__plugin_nimble_nimble-mcp-server__` format)
  - Task agents now use `run_in_background=False` to preserve MCP access ([#13254](https://github.com/anthropics/claude-code/issues/13254))
  - Added MCP tool registry blocks to all Task prompt templates
  - Enforced `nimble_web_search` (MCP) as only search method — banned WebSearch, WebFetch, curl
  - Description rewritten to third-person with specific trigger phrases
  - Step 3 condensed; detailed content moved to `references/generate-update-and-publish.md`
  - Added anti-hallucination guardrails for subagent prompts
- Version bumped to 0.6.1 across all plugin configs
- Deduplicated `google_search` caveat in `error-recovery.md`

## [0.5.0] - 2026-02-23

### Added
- **nimble-web-tools** skill — replaces `nimble-web-search` with full Nimble CLI wrapper
  - `nimble search` — web search with 8 focus modes
  - `nimble extract` — extract content from any URL (JS rendering, geolocation, parsing)
  - `nimble map` — discover URLs and sitemaps on a website
  - `nimble crawl` — bulk crawl website sections with depth/path control

### Changed
- Skills now use Nimble CLI (`@nimble-way/nimble-cli`) instead of curl-based wrapper scripts
- Version bumped to 0.5.0 across all plugin configs
- `rules/nimble-tools.mdc` updated to reference `nimble-web-tools` skill
- README.md updated with CLI installation and new skill documentation

### Removed
- `nimble-web-search` skill (replaced by `nimble-web-tools`)
- `scripts/search.sh` and `scripts/validate-query.sh` curl wrapper scripts
- `examples/` and `references/` directories from old web-search skill

## [0.4.0] - 2026-02-18

### Added
- **nimble-agents** skill — find, generate, and run agents for structured data from any website
- `.cursor-plugin/plugin.json` — Cursor IDE plugin support
- `.mcp.json` / `mcp.json` — MCP server configuration for Claude Code and Cursor
- `rules/nimble-tools.mdc` — Cursor rule for preferring Nimble tools
- Multi-platform support: Claude Code, Cursor, and Vercel Agent Skills CLI

### Changed
- Plugin renamed from `nimble-web` to `nimble` (unified plugin)
- Version bumped to 0.4.0 across all skills and config files
- `.claude-plugin/plugin.json` updated with new name, description, and keywords
- `.claude-plugin/marketplace.json` updated to reflect unified plugin
- `.gitignore` updated to include `.cursor/`, `.claude/`, `*.bak`
- `README.md` rewritten to cover all installation channels

## [0.1.0] - 2025-01-01

### Added
- Initial release with `nimble-web-search` skill
- 8 focus modes: general, coding, news, academic, shopping, social, geo, location
- AI-powered answer generation
- Agent Skills standard compatibility

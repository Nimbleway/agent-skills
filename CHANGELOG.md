# Changelog

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

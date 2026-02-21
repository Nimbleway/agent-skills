# Changelog

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

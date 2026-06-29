# Changelog

## [0.25.0] - 2026-06-24

### Added
- **`launch-monitor` skill** in `marketing/` — monitors press, social, developer communities, and competitor channels around a product launch, tracking sentiment, flagging mischaracterizations, surfacing competitor responses, and recommending actions in real time. Delivers a Response War Room dashboard with a live signal feed, mischaracterization tracker, competitor response panel, and sentiment velocity chart. Ships with `references/template.html` and `references/sources.md`.

## [0.24.0] - 2026-06-24

### Added
- **`brand-mention-monitor` skill** in `marketing/` — scans Reddit, X, LinkedIn, Instagram, TikTok, YouTube, blogs, news, and review platforms for brand mentions, scores each on reach/velocity/sentiment/risk-topic match, and buckets into Crisis / Watch / Engage / Log with routing and response windows. Ships with `references/template.html` (interactive triage console) and `references/sources.md` (per-platform query templates).

## [0.23.0] - 2026-06-14

### Changed
- **`nimble-databricks-data-products` — SQL-native agent discovery.** Replaced the `nimble agent get` CLI introspection with the new `nimble_agent_describe()` Unity Catalog SQL function, so the full discovery path runs through SQL (`nimble_agent_list()` → `nimble_agent_describe()` → `nimble_agent_run()`) with no `nimble` CLI dependency. `references/nimble-agents.md` §2 now reads inputs via `nimble_agent_describe('<agent>')` and splits input discovery (from `describe`) from output-field discovery (the §2.5 run-probe). `SKILL.md` updates the "discover, don't assume" golden rule and Phase 2, and drops `Bash(nimble:*)` from `allowed-tools` (it existed only for `nimble agent get`). This removes the skill's only hard `nimble`-CLI dependency for discovery — the Phase 0 unblock for packaging it into Databricks Genie Code (SQL/notebook-native, no shell). Requires the `nimble_agent_describe` UDTF from the Nimble cookbook.

## [0.22.0] - 2026-06-12

### Added
- **`nimble-databricks-data-products` skill** in a new **`data-platforms/`** vertical — turns a one-line brief (e.g. "pricing comparison on dog products from Amazon and Walmart in Databricks") into working Databricks data products (Delta tables, an AI/BI dashboard, and/or a deployed app), end to end — equally for production data products or quick demos. It runs Phase 0 preflight (auth, warehouse, integration gate, writable-schema confirm), discovers the right Nimble agents at runtime via the `nimble_integration` Unity Catalog functions (never hardcoded), ingests live web data into Delta tables using a **control-table + correlated `LATERAL nimble_agent_run`** pattern (one set-based, expandable INSERT — not per-keyword files), and produces an **AI/BI dashboard** and/or a **deployed Databricks App**, branded "Powered by Nimble". Bundles reference cookbooks (preflight, agent discovery/ingest, Lakeview dashboard, AppKit app, branding, official-`databricks-*`-skill delegation map, integration-install fallback), helper scripts (`build_dashboard.py` for one-shot dashboard creation, `ingest.sh` for async statement fan-out), and the Nimble logo asset. Encodes hard-won gotchas: defensive numeric casts for currency-string prices, per-agent localization, probe-before-fan-out, reconcile-against-control-table verification, Lakeview JSON pitfalls, and AppKit numeric-string / light-mode fixes. Registered in `.claude-plugin/plugin.json`, `.cursor-plugin/plugin.json`, and `.claude-plugin/marketplace.json`.

## [0.21.3] - 2026-05-27

### Fixed
- **Cowork / claude.ai connector detection & hallucinated auth flows** — in those hosts the plugin is often installed while its MCP connector isn't connected. The previous guidance was reactive ("if the first call errors, then guide"), so agents fired a data call, got back an OAuth authorization URL, and improvised a fabricated recovery flow ("paste the full URL from your address bar back here and I'll complete the connection"). The fix makes connection verification a **proactive preflight** (one read-only `nimble_agents_list` probe before any work), **corrects the connect path** everywhere to `Customize → Connectors → Nimble → Connect → browser login` (superseding the 0.21.1 `Personal plugins → … → Add to your team` wording), adds an **inline sign-up** note for users without a Nimble account, and adds a **hard anti-hallucination rule** (present any "Authorize" link verbatim and stop; never invent a completion step; never claim tools "will activate" then call them in the same turn). Touches `_shared/` canonical sources, all 11 synced business-skill `references/` directories, both core skills' `SKILL.md` + `rules/setup.md`, and `README.md`.
- **Missing probe-tool permission** — added `mcp__plugin_nimble_nimble__nimble_agents_list` to `nimble-agent-builder`'s `allowed-tools` so it can actually run the mandated preflight probe in MCP-only hosts.
- **Dangling reference** — both core `SKILL.md` files pointed connector guidance at a `references/profile-and-onboarding.md` that doesn't exist in those skills; guidance is now self-contained and points to `rules/setup.md`.

## [0.21.1] - 2026-05-13

### Fixed
- **Cowork onboarding** — when the plugin is installed but the connector isn't activated yet (typical Cowork / claude.ai first-run state), the skills were silently falling back to WebFetch instead of guiding the user to activate. The fix adds a dedicated "plugin installed but connector not activated" state to the transport-selection table in `_shared/nimble-playbook.md`, a matching sub-section in `_shared/profile-and-onboarding.md`, and an explicit hard-stop rule in both core SKILL.md files. When this state is detected, the skill now surfaces verbatim instructions: `Customize → Personal plugins → Nimble → Connectors → Add to your team`, then stops. WebFetch / WebSearch / curl substitution is explicitly forbidden. Synced into all 11 business-skill `references/` directories via `scripts/sync-shared.sh`.

## [0.21.0] - 2026-05-13

### Changed
- **MCP server ID renamed to `nimble`** (was `nimble-mcp-server`) across `.mcp.json`, `mcp.json` (Cursor), README, both core-skill SKILL.md `allowed-tools` whitelists, the `claude mcp list` health check, and all CLI→MCP mapping tables in `nimble-agent-builder`. New tool prefix: `mcp__plugin_nimble_nimble__*`. Aligns with the lowercase server-ID convention used by every Anthropic-official plugin (linear, github, asana, etc.).
- **Onboarding rewritten around the plugin install path.** Every install instruction now leads with `/plugin install nimble` for any Claude product (Claude Code, Claude Cowork, claude.ai) — the plugin's `.mcp.json` auto-registers as a Connector in `Customize → Personal plugins → Nimble → Connectors`, and OAuth handles auth on first tool call. Updated `_shared/nimble-playbook.md` (Transport Selection block), `_shared/profile-and-onboarding.md` (prerequisite-check flow), `README.md`, `nimble-agent-builder/README.md`, both `rules/setup.md` files, and both core skills' Prerequisites sections. Synced into all 11 business-skill `references/` folders via `scripts/sync-shared.sh`.
- **Transport selection is now explicit.** Skills pick CLI or MCP at session start (`nimble --version` → CLI; `claude mcp list | grep nimble` → plugin MCP) and stick with it for the session.
- **CLI package name corrected** in onboarding docs: `@nimbleway/cli` → `@nimble-way/nimble-cli` (the actual published package).

## [0.20.0] - 2026-05-13

### Changed
- **Plugin MCP config** — migrated `.mcp.json` from the `mcp-remote` stdio shim with bearer-token header to native HTTP transport with OAuth (`type: "http"`, `url`, no headers). Matches the canonical pattern in `anthropics/claude-plugins-official` (Linear, Asana). Removes the `npx -y mcp-remote@latest` cold-start and the `${NIMBLE_API_KEY}` header — Claude Code now drives the full OAuth 2.1 + PKCE + Dynamic Client Registration flow against `mcp.nimbleway.com` automatically. Root-level `mcp.json` preserved for Cursor compatibility.

## [0.19.0] - 2026-04-20

### Added
- **Human Resources vertical** (`skills/human-resources/`) — new vertical for HR and recruiting workflows; scoped to cover future skills like comp-analysis, interview-prep, and onboarding
- **talent-sourcing** — distribution step (Step 8) added; skill now offers Notion/Slack report delivery via connector detection pattern from `memory-and-distribution.md`

### Changed
- Renamed `skills/talent/` → `skills/human-resources/` — "talent" was ambiguous; human-resources is the standard term and the right scope for the vertical
- Updated `.claude-plugin/plugin.json` and `marketplace.json` to reference `./skills/human-resources/`

## [0.18.0] - 2026-04-13

### Added
- **`seo-intel`** — single-skill SEO intelligence toolkit covering the full lifecycle via 7 router-dispatched workflows: keyword research, rank tracking, technical site audit, content gap analysis, competitor keyword reverse-engineering, AI visibility measurement (ChatGPT, Perplexity, Google AI, Gemini, Grok), and GitHub repository SEO. One install, one entry point — intent detection routes to the right workflow, and workflows chain naturally across a session.

### Changed
- **`_shared/`** — removed `ai-platform-profiles.md` (only SEO-specific) and `output-quality.md` (marginal value, overlaps playbook) from the shared sync set

## [0.17.0] - 2026-04-07

### Added
- **Two-tier wiki index** — global `index.md` (one line per directory) + per-directory `{dir}/index.md` catalogs for scalable entity lookup
- **Chronological activity log** (`log.md`) — append-only timestamped record of skill runs and findings, rotated at 90 days
- **Cross-entity references** — Obsidian-compatible `[[path/entity]]` wiki links between related entities (people → companies, competitors → competitors)
- **Ad-hoc insights** — "save this" / "remember that" files insights into relevant entity pages with `[ad-hoc]` tags
- **Cross-entity synthesis pages** (`synthesis/`) — dynamically created when patterns emerge across 3+ entities, with YAML source tracking for deterministic staleness detection
- **Research backlog** (`backlog.md`) — tracks knowledge gaps and unanswered questions across skill runs

### Changed
- All 9 business skills now run 5 preflight calls (added index load) and reference wiki update patterns in their save steps
- **competitor-intel** — new Step 7.5 generates synthesis pages using `nimble-analyst` agent; save step adds cross-references and appends to backlog
- **meeting-prep** — preflight follows cross-references from person files to load related competitor/company context
- **company-deep-dive** — save step adds cross-references for discovered people and related competitors
- Bootstrapping now creates `synthesis/` directory alongside existing entity directories

## [0.16.0] - 2026-04-06

### Changed
- All 5 business skills now discover WSAs dynamically at runtime via `nimble agent list --search` instead of hardcoding agent names
- **local-places** — replaced 10 hardcoded WSA names across Steps 4-7 with a new WSA Discovery step (Step 4) that discovers, classifies, and caches WSAs for all phases
- **competitor-intel**, **company-deep-dive**, **meeting-prep**, **competitor-positioning** — added slim WSA discovery step before main execution, prioritizing search/extract/crawl/map WSAs
- `wsa-pipeline.md` reference converted from static WSA inventory to discovery strategy document
- Added sibling skill suggestions to follow-up sections across all business skills
- Fixed weakness language in competitor-positioning battlecard template

## [0.15.1] - 2026-04-06

### Changed
- All 5 business skills now reference Scaled Execution pattern from `nimble-playbook.md` with call estimation guidance
- Added explicit 500 retry and timeout handling to error sections of company-deep-dive, meeting-prep, competitor-positioning, local-places, and competitor-intel

## [0.15.0] - 2026-04-05

### Added
- **healthcare-providers-verify** skill — cross-references provider data against authoritative sources (NPI registry, state licensing boards) for accuracy verification

## [0.14.0] - 2026-04-05

### Added
- **healthcare-providers-enrich** skill — enriches extracted provider records with reviews, credentials, and contact info from multiple web sources

## [0.13.0] - 2026-04-05

### Added
- **healthcare-providers-extract** skill — first skill in the `healthcare/` vertical; extracts structured practitioner directories from any web source using dynamic WSA discovery

### Changed
- Fixed `--shared-inputs` YAML syntax in shared playbook
- Strengthened entity dedup normalization rules

## [0.12.1] - 2026-04-05

### Added
- Audit mode for **market-finder** skill — validates a reference list against live web data, scores market presence, and produces gap analysis

## [0.12.0] - 2026-04-05

### Added
- **market-finder** skill in `business-research/` — discovers all businesses of a given type in any geography using Nimble WSAs
- 6 vertical presets (Healthcare, SaaS, Restaurants, Legal, Auto/Home, Custom) with dynamic WSA discovery
- SaaS treated as first-class vertical with two-pass discovery and funding verification
- Shared "Scaled Execution" pattern added to `_shared/nimble-playbook.md` (tiered: individual → batch → multi-batch → confirmation gate)

## [0.11.0] - 2026-04-05

### Added
- **local-places** skill in `productivity/` — discovers, enriches, and scores local businesses using Nimble WSAs (Google Maps, Yelp, Facebook, Instagram, DoorDash, Uber Eats)
- Skill-specific WSA pipeline reference with category detection, location disambiguation, and interactive Leaflet.js map generation

## [0.10.2] - 2026-04-03

### Added
- `CONTRIBUTING.md` with contributor guidelines
- Shared patterns and conventions for new skill development

### Changed
- Rewrote README with category-level skill table
- Fixed sync script for shared reference distribution

## [0.10.1] - 2026-04-02

### Added
- `CLAUDE.md` with repo context, skill authoring rules, and conventions

### Changed
- Added agent CLI commands (`nimble agent list`, `nimble agent get`, `nimble agent run`) to all business skill playbooks
- Added MCP fallback table and fixed `agent get` flag syntax
- Updated plugin descriptions across both manifests

## [0.10.0] - 2026-03-30

### Changed
- Grouped skills into vertical directories: `business-research/`, `healthcare/`, `marketing/`, `productivity/`, `web-search-tools/`
- Updated `plugin.json` and `marketplace.json` for grouped directory structure
- Standardized author metadata across all skills

## [0.9.0] - 2026-03-26

### Added
- **Business skills foundation** — shared references (`_shared/nimble-playbook.md`, `profile-and-onboarding.md`, `memory-and-distribution.md`), custom sub-agents (`nimble-researcher`, `nimble-analyst`)
- **competitor-intel** skill — ongoing competitor monitoring with signal classification and delta detection
- **company-deep-dive** skill — 360-degree company research from web sources
- **meeting-prep** skill — attendee research and meeting briefings with calendar detection
- **competitor-positioning** skill — marketing-focused positioning analysis with before/after change tracking

### Changed
- Added signal date validation to filter stale events from reports
- Added value positioning section to meeting-prep briefings
- Enforced DRY across all business skills: replaced `site:` operator with `--include-domain`, standardized placeholder names, added same-day detection

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

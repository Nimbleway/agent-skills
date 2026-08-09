# Changelog

## [1.4.0] - 2026-08-09

### Added
- **xAI/Grok plugin layer.** New `.grok-plugin/plugin.json` declares the shared `./skills/` tree to Grok Build. Verified against xAI's own `scripts/plugin_catalog.py`: the plugin now indexes 15 skills, 2 agents, 1 command, and 1 HTTP MCP server. No Grok-only skill copies, no second repository — the marketplace is an index, so distribution is one catalog entry in xAI's repo pinning a commit from this one.
- **`mcpServers` drift assertion in `scripts/check-plugin-manifests.py`.** The Grok manifest declares its MCP server as an inline object rather than as a path to `.mcp.json`, which duplicates one server config. The checker now asserts the two copies agree — matching server names and identical config — and fails if the Grok manifest is changed to a path declaration. Verified against fixtures for URL drift, a server present in only one file, and the path-declaration case.

### Changed
- **`scripts/tag-release.sh` also asserts `.grok-plugin/plugin.json`.** All five manifests, the README badge, and every skill's frontmatter must agree on the version, so a partial bump fails CI.
- `README.md`, `CLAUDE.md`, and `CONTRIBUTING.md` document Grok as a fourth packaging target, including why the Grok manifest declares MCP inline. xAI's indexer reads only the `mcpServers` key out of a `.mcp.json` file, and this repo's is a bare server map, so a path declaration would index zero servers and the Grok listing would claim the plugin ships no MCP server. Declaring inline is also what keeps `.mcp.json` byte-identical, preserving Claude Code's Connector registration over native HTTP with OAuth.

## [1.3.0] - 2026-08-06

### Added
- **OpenAI/Codex plugin layer.** New `.codex-plugin/plugin.json` declares `skills` as the single `./skills/` string path (an array is rejected with `plugin_skills_path_wrong_type`), `mcpServers` pointing at the existing root `.mcp.json`, and an `interface` block carrying the listing metadata: display name, short and long descriptions, developer name, category, capabilities, brand colors, three starter prompts, and the required `logo` and `composerIcon` assets. The long description and `capabilities` separate the four data capabilities explicitly — Search, Extract, Extraction Templates, and Web Search Agents — alongside Map and Crawl. The shared skill tree, the hosted MCP configuration, and all Claude, Cursor, and CLI behavior are unchanged; no OpenAI-only skill copies were added.
- **`assets/nimble-logo.png`** at the repository root, referenced by `interface.logo` and `interface.composerIcon`. Square 200×200 PNG, satisfying the square, minimum 48×48, maximum 4096×4096, and 5 MiB asset gates.
- **`scripts/check-plugin-manifests.py`.** Validates the manifest fields the structure check and a JSON parse both pass straight over: `skills` declared as a string rather than an array, the required `logo` and `composerIcon` assets and their dimensions read from the file header, brand-color contrast against both the light and dark surfaces, the `category` enum, and the display-name, description, and starter-prompt length limits. Each check is named after the error code OpenAI would raise, so a CI failure maps onto the published submission-error reference directly. Standard library only — no new dependency.
- **`scripts/check-plugin-structure.sh` and a `Plugin packaging` CI workflow.** Asserts every `SKILL.md` is an immediate child of `skills/`, that no `SKILL.md` exists under any `references/` directory, that each skill's frontmatter `name` matches its directory, that `<plugin>:<skill>` stays within 64 characters, that frontmatter is present and closed, that descriptions stay within 1024 characters, and that `marketplace.json` enumerates exactly the skills that exist. Runtime discovery is recursive on both Claude Code and Codex, so these violations work locally while blocking OpenAI submission and silently emptying the xAI index — a CI gate is the only thing that surfaces them.

### Changed
- **Reference documents under `skills/nimble-web-expert/references/` are now named `reference.md` instead of `SKILL.md`.** The seven affected documents cover Search, Extract, Extraction Templates, Web Search Agents, Map, Crawl, and Tasks. A `.codex-plugin/plugin.json` is read as a Legacy-format manifest whose loader scans for `SKILL.md` recursively, so these progressive-disclosure documents registered as seven extra skills in the model-visible catalog — 22 instead of 15. Every pointer was updated across `CLAUDE.md`, `_shared/nimble-playbook.md` and its synced copies, `nimble-web-expert`'s `SKILL.md`, `README.md`, `rules/nimble-web-expert.mdc`, and `references/batch-patterns.md`. Directory names are unchanged, so no skill identifier moves.
- **`scripts/tag-release.sh` also asserts `.codex-plugin/plugin.json`.** All four manifests, the README badge, and every skill's frontmatter must agree, so a partial bump fails CI instead of shipping manifests that disagree about the version.
- **Trimmed the `brand-mention-monitor` and `launch-monitor` descriptions** to 1006 and 1005 characters, from 1102 and 1072. Both exceeded the 1024-character cap and would have been rejected with `skill_description_too_long`. Only descriptive prose was removed — every trigger phrase and every negative trigger is intact.

## [1.2.0] - 2026-08-05

### Changed
- **Flattened the skills tree.** All 15 skills are now direct children of `skills/` instead of being grouped into vertical subdirectories (`business-research/`, `data-platforms/`, `healthcare/`, `human-resources/`, `marketing/`, `productivity/`, `seo/`, `web-search-tools/`). **Skill directory names are unchanged**, so every skill identifier (`nimble:competitor-intel`, `nimble:meeting-prep`, …) and every `npx skills add --skill <name>` invocation keeps working exactly as before. Both plugin platforms require the flat layout: OpenAI/Codex rejects nested skill directories at submission (`skill_manifest_nested`, `skill_manifest_missing`), and xAI indexes only direct children of `skills/`. Runtime discovery in Claude Code and Codex is recursive, so the previous layout worked locally while being absent from both catalogs.
- **Verticals are now recorded as `metadata.category`** in each skill's `SKILL.md` frontmatter rather than as directory names. The README skills table keeps the same categories and links to each skill directly.
- `.claude-plugin/plugin.json` `skills` is now a single `./skills/` entry instead of eight vertical paths; `.claude-plugin/marketplace.json` lists the 15 flat skill paths. `.cursor-plugin/plugin.json` was already pointing at `./skills/` and is unchanged.
- `scripts/sync-shared.sh` globs `skills/*/references` instead of `skills/*/*/references`.
- `CONTRIBUTING.md` now instructs contributors to create skills directly under `skills/` and set `metadata.category`, and to register them in `marketplace.json` only — the plugin manifests no longer need a per-skill path.
- `CLAUDE.md` documents the flat-tree requirement and both platforms' constraints so the layout can't silently regress.

### Fixed
- Broken relative link in `skills/nimble-web-expert/README.md` — `../../README.md` resolved to a nonexistent `skills/README.md` at the previous nesting depth and now resolves to the root README.

## [1.1.0] - 2026-07-29

### Added
- **Three Web Search Agent run modes, taught and routed.** The canonical WSA reference and the shared playbook now lead with a mode decision table: **named create-or-reuse** (`agents run --agent-name <name>`, no agent ID — the default for skills, since a repeated name resolves to the same `web_search_agent_id`), **explicit agent** (`agents:runs create --agent-id <id>`), and **caller-anonymous** (`agents run` with neither, which still returns a generated `web_search_agent_id`). Documented the routing trap behind it: `agents:runs create` **requires** `--agent-id` and ignores `--agent-name`, so Modes 1 and 3 must go through `nimble agents run`.
- **`use_case` locking semantics.** `research` / `enrichment` / `dataset_building` are documented exactly. `use_case` is stored when the agent is created (including on a Mode 1 first call), accepted as a no-op when it matches an existing agent, and rejected when it differs — it is not a per-run override. Also documented the two server-side rules that come with `dataset_building`: an `output_schema` is required, and effort must be `high` or above.
- **Run-level `skill` override.** Against an existing agent, `--skill` applies to that run only and leaves stored config untouched; on the call that *creates* the agent, `--skill` and `--use-case` become its stored configuration instead.
- **Verified live-progress documentation.** On the CLI, `--enable-events` plus `agents:runs stream-events` emits `task_run.state` / `task_run.progress_msg.*` / `task_run.progress_stats` events and **closes on its own** at a terminal state (`--max-items <n>` closes it after `n` events). The stream never carries the output — `agents:runs result` is still required. On production MCP the documented approach is bounded status polling, verified separately rather than assumed from the CLI behavior.
- **Error table for the run contract** — `409` "Run still active", `404` run/agent mismatch, the four distinct `422` shapes (locked `use_case`, invalid enum, missing `dataset_building` schema, effort too low), the `sources` shape rejection, and the `Required flag "agent-id" not set` routing mistake.

### Added
- **Routing eval for `nimble-web-expert`** (`scripts/run-routing-eval.py` + `evals/nimble-web-expert-routing.json`). Ten cases assert which capability the routing guidance selects for a given prompt, and whether the researched-report/quick-scan fork is offered. The runner reads the routing text out of SKILL.md at run time, so the eval and the doc can't drift; it makes no Nimble calls, so it needs no API key and spends no credits. Currently 10/10, unanimous over three runs per case. It earned its keep immediately: it caught that `dataset_building`'s `high`+ effort floor was documented only in the on-demand reference, leaving the fork rule undecidable at routing time — now stated inline.

### Changed
- **`nimble-web-expert` routing split into two gates.** Gate A asks where the data lives (URL → `extract`, site + item → Extraction Template, sitemap → `map`, section → `crawl`); anything with no location signal — and any named site with no template — falls through to Gate B, which asks what the user wants back. `nimble search` returns raw material to skim; a Web Search Agent returns a finished, cited answer, and the prompt's deliverable noun decides which. Previously the routing table keyed only on input shape, so a request like "create a report on X" carried no distinguishing signal and defaulted to `search` — the flat table has been replaced, the core-principles bullet no longer contradicts it, a lexical trigger table was added, and a guardrail now forbids answering a synthesis deliverable with raw search results.
- **The expensive fork is now offered rather than silently taken.** When Gate B lands on a Web Search Agent at `high` effort or above, the skill offers one `AskUserQuestion` — researched report (minutes, cited) vs quick scan (`nimble search`, seconds) — instead of picking for the user. Below `high` it just runs. Web Search Agent runs must also announce their expected duration and narrate progress, since on MCP progress comes from bounded polling and an un-narrated multi-minute run reads as a hang. Added "Research & report" to the ambiguous-request options, which previously offered no path to a Web Search Agent at all.
- **CLI prerequisite raised to 1.2.0**, the first release exposing the complete run contract. Updated in the playbook transport table, the onboarding install/upgrade flow, and the `nimble-web-expert` description.
- **Corrected the `use_case` enum.** The stale value `data_enrichment` is replaced with the released `enrichment` everywhere.
- **Documented the real `--sources` shape.** `allow` / `block` are arrays of ordered source groups (`{title, domains, order}`); `prioritize` / `avoid` are plain guidance strings. The previous docs implied a single uniform shape, which the API rejects.
- **Separated enrichment input from output shape.** `--input-data` carries the rows you already have; `--output-schema` describes the shape of the answer. Enriching several rows needs an **array** schema — an object schema returns a single object. Fields carried in from `input_data` come back as `confidence: "pre_existing"` with no citations and must not be presented as sourced findings.
- **Discovery is client-side filtering everywhere.** `agents list` and `agents:templates list` take no server-side search term, matching the already-documented `extract:templates list` behavior.
- **Transport differences are now documented per capability** rather than assumed parity. Modes 1 and 2, `use_case`, `skill`, `sources`, `output_schema`, `input_data`, and `effort` work the same on both transports. Three CLI-path capabilities have a documented MCP approach instead: `enable_events`/`stream-events` → bounded status polling; `previous_interaction_id` → restate prior context in `input`; and Mode 3 → pass an `agent_name`, since `nimble_agents_run` requires `agent_id` or `agent_name`. Added `nimble_agents_get` to the `nimble-web-expert` MCP allow-list so an agent's stored `use_case` can be checked before a run.
- **Attribution unchanged** — `--client-source nimble-agent-skills` on every CLI call; production MCP still exposes no integration-specific attribution parameter, so the managed-transport exception is retained.

### Verified
Every command, parameter, and error documented above was exercised against live services — nothing was inferred from SDK types or `--help` output.

**On CLI 1.2.0:** all three run modes; same-name reuse returning the same agent ID; a run-level `skill` override leaving stored config untouched; a locked-`use_case` rejection; a structured `enrichment` run with `input_data` + `output_schema` + `sources`; event streaming to self-termination, plus a capped stream (`--max-items`) confirmed not to cancel its run; terminal result retrieval with trust/citations; and the not-ready (`409`) and validation-error (`422`) paths, including the `sources` group `title` requirement.

**On production MCP:** Modes 1 and 2, status polling, and result retrieval with trust metadata. Mode 3 was probed too: `nimble_agents_run` takes `agent_id` or `agent_name`, so the transport table routes Mode 3 to a named agent on MCP rather than claiming blanket parity.

## [1.0.0] - 2026-07-22

### Changed
- **Migrated the plugin to Nimble's current web-data surface (CLI 1.1.0+ / production MCP).** The taxonomy is now Search · Extract · **Extraction Templates** · **Web Search Agents** · Map · Crawl, using Nimble's own product names. `nimble-web-expert` was reworked around this taxonomy and the Ask-Nimble tool-selection model (including the "no template for a site → use a Web Search Agent" rule and the Web Search Agent reuse-priority chain). Added `references/nimble-extract-templates/` (existing-only discover/inspect/run) and reworked `references/nimble-agents/` into the Web Search Agents / Agent API V2 lifecycle (`agents` / `agents:templates` / `agents:runs`) with the agent-authoring schema and per-claim trust/citation metadata.
- **Repointed every skill off the removed singular `nimble agent` command group.** CLI 1.1.0 replaced it with `extract:templates *` (structured site scrapers — the old `amazon_pdp`/`google_maps`/`yelp`/NPI-style agents) and `agents:runs *` (open-ended research). Business, healthcare, marketing, HR, and SEO skills now discover via `extract:templates list` + client-side filter (the `--search` flag is gone) and run via `extract:templates run`. The response envelope is unchanged (`data.parsing`).
- **Request attribution** is now the stable integration tag `nimble-agent-skills`, carried on the CLI path via `--client-source` / `CLIENT_SOURCE`. MCP requests are attributed at the transport level, so the CLI path is used when per-integration attribution matters.

### Removed
- **`nimble-agent-builder` skill** — removed entirely. Building/publishing new templates or agents is out of scope for the plugin; use existing Extraction Templates and Web Search Agents, or the Nimble app to author new ones. Removed from both plugin manifests and the marketplace.

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

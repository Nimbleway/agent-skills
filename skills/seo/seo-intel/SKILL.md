---
name: seo-intel
description: |
  SEO intelligence toolkit covering the full lifecycle via live web data:
  keyword research, rank tracking, site audits, content gap analysis,
  competitor keyword reverse-engineering, AI visibility across five platforms
  (ChatGPT, Perplexity, Google AI, Gemini, Grok), and GitHub repo SEO.
  Crawls real sites and SERPs via Nimble CLI — no fabricated metrics.

  Triggers: "SEO", "keywords", "rank tracker", "site audit", "content gap",
  "competitor keywords", "AI visibility", "GitHub SEO", "SERP analysis",
  "keyword research", "technical SEO", "keyword difficulty", "topic
  clusters", "ranking delta", "on-page SEO", "AI citation audit".

  Do NOT use for competitor business signals — use `competitor-intel`
  instead. Do NOT use for competitor messaging — use
  `competitor-positioning` instead. Do NOT use for general web scraping
  — use `nimble-web-expert` instead.
allowed-tools:
  - Bash(nimble:*)
  - Bash(date:*)
  - Bash(cat:*)
  - Bash(mkdir:*)
  - Bash(python3:*)
  - Bash(echo:*)
  - Bash(jq:*)
  - Bash(ls:*)
  - Bash(gh:*)
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Agent
  - AskUserQuestion
metadata:
  author: Nimbleway
  version: 0.19.0
---

# SEO Intelligence Toolkit

All-in-one SEO intelligence: keyword discovery, rank tracking, technical audits,
content gaps, competitor analysis, AI visibility, and GitHub SEO.

User request: $ARGUMENTS

**Before running any commands**, read `references/nimble-playbook.md` for Claude Code
constraints (no shell state, no `&`/`wait`, sub-agent permissions, communication style).

---

## Workflow Router

Detect the user's SEO intent from `$ARGUMENTS` and route to the appropriate
workflow. If the intent is ambiguous or generic ("help me with SEO"), ask which
workflow to run.

### Available Workflows

| Workflow | Triggers | Reference |
|----------|----------|-----------|
| **Keyword Research** | keyword opportunities, topic clusters, difficulty, what to rank for | `references/wf-keyword-research.md` |
| **Rank Tracker** | track rankings, keyword positions, ranking delta, position check | `references/wf-rank-tracker.md` |
| **Site Audit** | SEO audit, technical SEO, meta tags, schema, crawl for issues, CWV | `references/wf-site-audit.md` |
| **Content Gap** | content gap, keyword gap, compare coverage, missing topics | `references/wf-content-gap.md` |
| **Competitor Keywords** | competitor keywords, reverse-engineer SEO, competitor title tags | `references/wf-competitor-keywords.md` |
| **AI Visibility** | AI visibility, ChatGPT presence, Perplexity, AI Overview, GEO | `references/wf-ai-visibility.md` |
| **GitHub SEO** | github seo, repo discoverability, optimize readme, repo audit | `references/wf-github-seo.md` |

### Intent Detection

Map the request to one workflow:

- **Keywords / topics / difficulty / clusters / "what to rank for"** → Keyword Research
- **Rankings / positions / tracking / delta / monitoring** → Rank Tracker
- **Audit / crawl / technical / meta / schema / links / CWV** → Site Audit
- **Gap / missing topics / coverage comparison / "what should I write"** → Content Gap
- **Competitor site crawl / reverse-engineer / on-page at scale** → Competitor Keywords
- **AI visibility / ChatGPT / Perplexity / AI Overview / GEO** → AI Visibility
- **GitHub / repo / README / discoverability** → GitHub SEO

If unclear, present the options with AskUserQuestion:

> Which SEO workflow should I run?
> - **Keyword Research** — discover keyword opportunities and topic clusters
> - **Rank Tracker** — check and track keyword positions over time
> - **Site Audit** — full technical SEO crawl with JS rendering
> - **Content Gap** — compare content coverage against competitors
> - **Competitor Keywords** — reverse-engineer competitor on-page SEO at scale
> - **AI Visibility** — measure brand presence across 5 AI platforms
> - **GitHub SEO** — audit repository discoverability and README quality

### Execution

Once a workflow is identified:

1. **Read** the corresponding `references/wf-{name}.md`
2. **Follow** its instructions from Step 0 (Preflight) through to the output format
3. All `references/` paths inside workflow files are relative to this skill's directory

### Workflow Chaining

After completing a workflow, suggest natural next steps using sibling workflows.
Common chains:

- Site Audit → Keyword Research → Content Gap → Rank Tracker
- Keyword Research → Competitor Keywords → Content Gap
- AI Visibility → Content Gap → Keyword Research

When chaining, read the next workflow file and continue. Context from the
previous run (discovered domains, keyword lists, profile data) carries forward
— do not re-run preflight or re-ask onboarding questions.

### Shared Configuration

All workflows use:
- **Business profile + onboarding:** `references/profile-and-onboarding.md`
- **Data persistence:** `references/memory-and-distribution.md`
- **CLI patterns + constraints:** `references/nimble-playbook.md`
- **AI platform agent discovery:** `references/ai-platform-profiles.md`

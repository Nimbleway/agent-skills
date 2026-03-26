# Memory & Distribution

How skills persist knowledge across sessions and distribute reports to external tools.

---

## Memory Architecture

All persistence lives under `~/.nimble/` — never touch user project files.

```
~/.nimble/
├── business-profile.json          # Tier 1: Hot cache (see profile-and-onboarding.md)
└── memory/                        # Tier 2: Deep storage (loaded on demand)
    ├── competitors/               # Accumulated intel per competitor
    ├── people/                    # Contact profiles for meeting prep
    ├── companies/                 # Deep-dive research results
    ├── reports/                   # Timestamped full skill outputs
    └── glossary.md                # Industry terms and jargon
```

**Tier 1** (`business-profile.json`) — loaded every session. See
`references/profile-and-onboarding.md` for the full schema and update patterns.

**Tier 2** (`memory/`) — loaded on demand when a skill needs deeper context.

## Deep Storage Formats

### competitors/

One file per competitor. Append new findings under dated headers — never overwrite.

```markdown
# WidgetCo

## Key Facts
- Domain: widgetco.com
- HQ: San Francisco
- Funding: Series C ($45M, Jan 2026)
- CEO: Jane Smith

## Signals
### 2026-03-20
- Launched new enterprise tier pricing — [source URL]
- Hired VP of Sales from Salesforce — [source URL]

### 2026-03-13
- Announced partnership with AWS — [source URL]
```

### people/

One file per contact. Used by meeting-prep skill.

```markdown
# Sarah Chen

## Current Role
VP of Engineering at WidgetCo (since 2024)

## Background
- Previously: Senior Director at Google Cloud (2019-2024)
- Education: MS CS Stanford

## Notes from Previous Meetings
### 2026-03-15
- Interested in our API performance benchmarks
- Prefers technical depth over high-level summaries
```

### companies/

Detailed company profiles from deep-dive research.

```markdown
# Target Corp

## Overview
- Industry: Enterprise SaaS | Founded: 2015 | HQ: Austin, TX | ~500 employees

## Financials
- Last funding: Series B ($30M, Sep 2025) | Revenue: Est. $40M ARR

## Recent News
(dated entries, same format as competitors/)
```

### reports/

Timestamped **full** skill outputs. Save the complete briefing, not a summary.

**Naming:** `{skill-name}-{YYYY-MM-DD}.md` — if a skill may produce multiple reports
per day (e.g., meeting-prep for different companies), add a qualifier:
`{skill-name}-{qualifier}-{YYYY-MM-DD}.md`. The qualifier is defined in each skill's
SKILL.md (e.g., company slug for meeting-prep).

### glossary.md

Industry terms and jargon. Updated when the user uses unfamiliar terms.

## Bootstrapping (First Run)

```bash
mkdir -p ~/.nimble/memory/{competitors,people,companies,reports}
```

Create stub files for each competitor from the onboarding flow.

## Differential Analysis

The key feature across all skills. When a skill runs:

1. Read `~/.nimble/memory/{category}/{name}.md` for previous findings
2. Run fresh search with date filter
3. Compare new results against stored history
4. Surface only **genuinely new** signals

"WidgetCo raised a Series C" is noise if already in memory.
"WidgetCo just hired a new CTO" is a new signal worth highlighting.

## Learning from Corrections

When the user corrects the skill, update both tiers:

| Correction | Profile update | Deep storage update |
|------------|---------------|-------------------|
| "Skip CompanyX" | `preferences.skip_competitors` | Archive file |
| "Track CompanyY" | `competitors` list | Create stub file |
| "That info is wrong" | — | Update the file |
| "ARR means Annual Recurring Revenue" | — | Add to `glossary.md` |
| "I prefer bullet points" | `preferences.output_format` | — |

Always confirm the update to the user.

## Rules

- **Never touch user project files.** All persistence under `~/.nimble/`.
- **Append, don't overwrite.** Deep storage grows over time with dated sections.
- **Read on demand.** Only load files when the skill actually needs them.
- **Update profile after every run.** At minimum, `last_runs` timestamp.
- **Handle missing gracefully.** If a file doesn't exist, create it.

---

## Report Distribution

After presenting output, offer sharing based on available MCP connectors.

### Connector Detection

Check before presenting options:
- **Notion:** `mcp__plugin_Notion_notion__notion-create-pages`
- **Slack:** Any Slack MCP tool

### Sharing Flow

Use `AskUserQuestion` with only the available options:

> **Share this report?**
> - **Save to Notion** — full report as a page
> - **Send to Slack** — TL;DR to a channel
> - **Both**
> - **Skip**

**Notion:** Create a dated subpage. If `integrations.notion.reports_page_id` exists
in the profile, use it as parent. Otherwise ask and save the ID for next time.

**Slack:** Post **TL;DR only** — Slack is for alerts, not full reports. If
`integrations.slack.channel` exists, use it. Otherwise ask and save.

**Neither available** (first run only):
> **Tip:** If you connect a Notion or Slack MCP server, I can save reports or post
> TL;DRs to your team automatically.

Don't repeat this tip on subsequent runs.

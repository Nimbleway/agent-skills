---
name: competitor-intel
description: |
  Searches the live web via Nimble APIs to monitor competitors and produce a
  structured intelligence briefing. Runs parallel searches for news, product
  launches, hiring signals, and funding — then compares against previous
  findings to highlight only what's new.

  Use this skill when the user asks about competitors, competitive intelligence,
  or what rival companies are doing. Common triggers: "what are my competitors
  doing", "competitor update", "competitor news", "competitive landscape",
  "market intel", "what's new with [company]", "track [company]", "competitor
  briefing", "who's making moves", "competitive analysis", "losing deals to
  [company]", "battlecard". Also use before board meetings or strategy sessions
  when the user wants competitive context.

  Requires the Nimble CLI (nimble search, nimble extract) for live web data.
  Do NOT use for single-company deep dives (use company-deep-dive), meeting
  prep with attendees (use meeting-prep), or non-business queries.
allowed-tools:
  - Bash(nimble:*)
  - Bash(date:*)
  - Bash(cat:*)
  - Bash(mkdir:*)
  - Bash(python3:*)
  - Bash(echo:*)
  - Bash(jq:*)
  - Bash(ls:*)
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Agent
  - AskUserQuestion
metadata:
  author: Nimbleway
  version: 1.0.0
---

# Competitor Intelligence

Real-time competitive intelligence powered by Nimble's web data APIs.

User request: $ARGUMENTS

**Before running any commands**, read `references/nimble-playbook.md` for Claude Code
constraints (no shell state, no `&`/`wait`, sub-agent permissions, communication style).

---

## Instructions

### Step 0: Preflight

Follow the preflight pattern from `references/nimble-playbook.md`. Make these Bash
calls simultaneously:

- 14-days-ago date calculation (see execution-rules.md for cross-platform command)
- `date +%Y-%m-%d` (today)
- `nimble --version && echo "NIMBLE_API_KEY=${NIMBLE_API_KEY:+set}"`
- `cat ~/.nimble/business-profile.json 2>/dev/null`

From the results:
- CLI missing or API key unset → `references/profile-and-onboarding.md`, stop
- Profile exists → read all `~/.nimble/memory/competitors/*.md` for known signals
  (used for dedup in Steps 3 + 5). Determine mode using smart date windowing
  from `references/nimble-playbook.md`:
  - **Full mode:** first run OR last run > 14 days ago
  - **Quick refresh:** last run < 14 days ago
  - Skip to Step 2
- No profile → Step 1

### Step 1: First-Run Onboarding (2 prompts max)

**Prompt 1** — ask in plain text (NOT AskUserQuestion with options):

> "What's your company's website domain? (e.g., acme.com)"

Verify — make two Bash calls simultaneously:

- `nimble search --query "site:[domain]" --max-results 3 --search-depth lite`
- `nimble search --query "[domain] company" --max-results 5 --search-depth lite`

**Prompt 2** — confirm company + choose competitor method (use AskUserQuestion):

> I found that **[Company]** ([domain]) is [brief description].
> Is this right? And how should I find your competitors?
> - **Yes — find competitors for me**
> - **Yes — I'll list them myself**
> - **Wrong company — let me clarify**

If "find competitors", make three Bash calls simultaneously:

- `nimble search --query "[Company] competitors" --max-results 10 --search-depth lite`
- `nimble search --query "[Company] vs" --max-results 10 --search-depth lite`
- `nimble search --query "[Company] alternatives" --max-results 5 --search-depth lite`

Propose the list. Once the user confirms, create the profile and start Steps 2+3.
When creating the profile, also ask for or infer each competitor's domain and the
user's industry keywords. See `references/profile-and-onboarding.md` for the full
profile schema (company, competitors with domains/categories, industry_keywords,
integrations, preferences).

### Step 2: Research the User's Company

Use `site:[domain]` to avoid noise from generic company names. Make two Bash calls:

- `nimble search --query "site:[company-domain] product updates OR changelog OR releases" --start-date "[start-date]" --max-results 5 --search-depth lite`
- `nimble search --query "[UserCompany] news" --focus news --start-date "[start-date]" --max-results 5 --search-depth lite`

**Fallback if 0 results:** `nimble search --query "site:[company-domain] blog" --max-results 5 --search-depth lite`

### Step 3: Parallel Research Per Competitor (sub-agents)

Read `references/competitor-agent-prompt.md` for the full agent prompt template.
Follow the sub-agent spawning rules from `references/nimble-playbook.md`
(bypassPermissions, batch max 4, explicit Bash instruction, fallback on failure).

Spawn `nimble-researcher` agents (`agents/nimble-researcher.md`) with
`mode: "bypassPermissions"`. Customize the prompt template with each competitor's
name, domain, start-date, and known signals from memory (loaded in Step 0).

Also run **industry searches** directly (not in sub-agents), using `industry_keywords`
from the business profile:

- `nimble search --query "[industry_keyword] AI agents OR automation" --focus news --start-date "[start-date]" --max-results 5 --search-depth lite`
- `nimble search --query "[industry_keyword] regulation OR compliance OR pricing" --focus news --start-date "[start-date]" --max-results 5 --search-depth lite`

### Step 4: Deep Extraction

From all sub-agent results, pick the **top 3-5 P1/P2 articles** for full content.
Make one Bash call per URL, all simultaneously:

`nimble extract --url "https://..." --format markdown`

For extraction failures, follow the fallback in `references/nimble-playbook.md`.
Skip this step if search snippets already have enough detail.

### Step 5: Analysis & Output

**Full mode** (first run or > 14 days since last) — structured briefing:

- **TL;DR** — 3-5 P1 signals, most recent first, every one dated with source
- **Per competitor** — "Recent" and "Older Context" subsections, "Where They Win
  vs. Where You Win" table, "What This Means" (1-2 sentences)
- **Industry Trends** — signals from industry searches
- **Your Company Update** — releases/news from Step 2
- **Cross-Competitor Patterns** — converging trends
- **What This Means for [Company]** — strategic implications + suggested actions

**Quick refresh mode** (last run < 14 days) — short format:

- **New Signals** — dated, with competitor name, priority, and source
- **Nothing New** — list competitors with no new signals
- **Action Items** — only if something requires attention

**Core rules:**
- Every signal MUST have a date. A 6-month-old funding round is context, not news.
- Deduplicate against `~/.nimble/memory/competitors/*.md` — only surface NEW findings.
- Say "nothing notable this period" rather than padding with fluff.
- P3 signals: mention briefly or omit if report is long.

### Step 6: Save & Update Memory

Make all Write calls simultaneously:

- Report → `~/.nimble/memory/reports/competitor-intel-[date].md` (save the **full
  briefing**, not a summary — this is the local source of truth)
- Per competitor → append new signals to `~/.nimble/memory/competitors/[name].md`
  (use the format documented in `references/memory-and-distribution.md`)
- Profile → update `last_runs.competitor-intel` in `~/.nimble/business-profile.json`

### Step 7: Share & Distribute

Follow `references/memory-and-distribution.md` to offer Notion/Slack sharing based on
available connectors.

### Step 8: Follow-ups

- **Go deeper** on a competitor → more focused searches
- **Skip a competitor** → update `preferences.skip_competitors`
- **Add a competitor** → update `competitors`, create memory stub
- **"Looks good"** → done

---

## Agent Teams Mode (Dual-Mode)

Check at startup: `echo $CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`

**Team mode** (flag set): Spawn full **teammates** instead of sub-agents:

- **Lead** (you): Assign competitors, synthesize the final briefing
- **One teammate per competitor**: Uses `references/competitor-agent-prompt.md` —
  teammates can message each other when they find overlapping signals
- **Devil's Advocate** (optional): Challenges findings, looks for blind spots
- Lead synthesizes a **cross-validated** briefing with higher confidence

**Solo mode** (flag not set): Standard sub-agent flow from Step 3.

---

## Error Handling

- **Missing API key:** `references/profile-and-onboarding.md`
- **Empty results:** Retry without `--start-date`. Still empty → broaden query.
- **429 rate limit:** Fewer simultaneous Bash calls
- **401 expired:** "Regenerate at app.nimbleway.com > API Keys"
- **Extraction garbage:** See fallback in `references/nimble-playbook.md`

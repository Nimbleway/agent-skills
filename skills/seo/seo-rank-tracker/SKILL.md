---
name: seo-rank-tracker
description: |
  Tracks live SERP positions for target keywords using Nimble search APIs, stores
  JSON snapshots, and computes position deltas across runs. Unlike SaaS rank
  trackers with stale daily caches, every check hits live SERPs — positions
  reflect what Google shows right now, with SERP feature detection included.

  Use when the user asks to check or track keyword rankings over time. Triggers:
  "track rankings", "rank tracker", "keyword positions", "SERP position", "ranking
  report", "did rankings change", "which keywords dropped", "keyword monitoring",
  "position check", "ranking delta".

  Do NOT use for keyword discovery — use `seo-keyword-research` instead. Do NOT
  use for on-page SEO audits — use `seo-site-audit` instead. Do NOT use for
  competitor business signals — use `competitor-intel` instead.
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
  version: 0.18.0
---

# SEO Rank Tracker

Live keyword position tracking with JSON snapshots and delta reporting.

User request: $ARGUMENTS

**Before running any commands**, read `references/nimble-playbook.md` for Claude Code
constraints (no shell state, no `&`/`wait`, sub-agent permissions, communication style).

---

## Instructions

### Step 0: Preflight

Run the preflight pattern from `references/nimble-playbook.md` (5 simultaneous Bash
calls: date calc, today, CLI check, profile load, index.md load).

From the results:
- CLI missing or API key unset → `references/profile-and-onboarding.md`, stop
- Profile exists → check for same-day sibling output from `seo-keyword-research`:

```bash
ls ~/.nimble/memory/reports/seo-keyword-research-*$(date +%Y-%m-%d).md 2>/dev/null
```

If found, read the sibling report and extract target keywords from it. These become
the default keyword list for this run — skip keyword questions in Step 2.

Also load any existing snapshot directory for the target domain (determined from the
user's request or business profile):

```bash
ls ~/.nimble/memory/seo/rank-snapshots/ 2>/dev/null
```

This tells us which domains have tracking history.

### Step 1: First-Run Onboarding

Delegate to `references/profile-and-onboarding.md`. If no business profile exists,
run the company setup flow (2 prompts max). Once the profile exists, proceed.

### Step 2: Shape Scope (2 prompts max)

Gather the tracking parameters. If a sibling handoff provided keywords, skip to
the confirmation prompt.

**Prompt 1** — target domain and keywords:

> "Which domain should I track rankings for? And what keywords do you want to
> monitor?"
>
> Provide a list of keywords (one per line or comma-separated), or say
> "use the keywords from my keyword research" if you just ran that.

If the user provides a domain different from their business profile domain, confirm:
"Tracking rankings for **[domain]** — is this a competitor or your own site?"

**Prompt 2** — locale and depth (use AskUserQuestion):

> **Locale and depth:**
> - **Country/locale:** defaults to US/en — change? (e.g., GB/en, DE/de)
> - **Quick check** — positions only, lite search
> - **Full report** — positions + SERP feature analysis on top keywords

Default to US/en and quick check if the user doesn't specify. If < 5 keywords,
always run full report (the cost difference is negligible).

### Step 3: Smart Date Windowing

Scan for the last snapshot:

```bash
ls ~/.nimble/memory/seo/rank-snapshots/{domain}/ 2>/dev/null | sort -r | head -1
```

Classify the run mode based on the most recent snapshot:

| Condition | Mode | Behavior |
|-----------|------|----------|
| No snapshot OR last snapshot > 14 days ago | **Full mode** | Baseline run, no deltas |
| Last snapshot 1-14 days ago | **Delta mode** | Compare current vs previous |
| Last snapshot is today | **Same-day repeat** | Show existing snapshot, ask before re-running |

For same-day repeats: "Already tracked rankings today. Show existing results, or
re-run for fresh positions?"

Inform the user which mode was selected:
- "First rank check for **[domain]** — establishing baseline positions."
- "Last check was **[N days ago]**. Running delta comparison."

### Step 4: WSA Discovery

Discover SERP-related agents in parallel:

```bash
nimble agent list --search "serp" --limit 20
nimble agent list --search "google search" --limit 20
```

From the results, look for agents that return structured SERP data (organic results,
positions, SERP features). Validate any candidate with:

```bash
nimble agent get --template-name {name}
```

Check that the agent accepts keyword/query input and returns ranked organic results.
If a suitable WSA exists, use it for SERP queries in Step 5 alongside or instead of
`nimble search`. If no suitable WSA is found, use `nimble search` exclusively — do
not fail.

### Step 5: SERP Query Execution

Read `references/serp-query-patterns.md` for query construction rules, SERP feature
extraction, and batching patterns.

**Batch keywords** into groups of ~5 per sub-agent. Spawn up to 4 `nimble-researcher`
agents (`agents/nimble-researcher.md`) with `mode: "bypassPermissions"`.

Each agent receives a prompt like:

```
Check SERP rankings for these keywords against domain "{domain}".
Country: {country_code}, Locale: {locale}

KEYWORDS:
{keyword_list}

RULES:
- Use the **Bash tool** to execute each nimble command.
- Do NOT use run_in_background. All Bash calls must be synchronous.
- Run all searches simultaneously (multiple Bash tool calls in one response).

For each keyword, run:
nimble search --query "{keyword}" --search-depth lite --max-results 20 --country {cc} --locale {locale}

Parse the JSON results. For each keyword:
1. Find the first organic result where the root domain matches "{domain}"
   (strip www., trailing slash, protocol when comparing).
2. Record position (1-indexed), ranking URL, title, and description.
3. If the domain does not appear in top 20, record position as null.

Return results as a JSON array:
[
  {
    "keyword": "...",
    "position": 3,
    "ranking_url": "https://...",
    "title": "...",
    "snippet": "...",
    "serp_features": ["featured_snippet", "people_also_ask"],
    "checked_at": "2026-04-13T..."
  }
]

**Note:** `--search-depth lite` returns organic result metadata only — it does NOT
include SERP feature indicators. Set `serp_features` to `[]` for lite queries.
SERP features are detected in the enrichment pass below (full report mode only).
```

**For full report mode — SERP feature enrichment:** After lite queries complete,
identify the top 5 keywords by business priority. Run the `google_search` agent
for those to get typed SERP entities:

```bash
nimble agent run --agent google_search --params '{"query": "{keyword}", "num_results": 20, "country": "{cc}", "locale": "{locale}"}'
```

The `google_search` agent returns `data.parsing.entities` — a dict keyed by
entity type. Entity types are **dynamic** — iterate all keys to detect which
SERP features are present. Common mappings to `serp_features`:
`AIOverview` → `"ai_overview"`, `RelatedQuestion` → `"people_also_ask"`,
`Ad` → `"ads"`. For any other entity type key that appears (news, images,
shopping, local, knowledge panels, etc.), add it as a lowercase snake_case
entry in `serp_features`. Do not skip unknown types.

Additional params: `time` (hour/day/week/month/year), `location` (city string
or UULE for geo-specific rankings), `start` (pagination offset: 10=page 2).
See `references/ai-platform-profiles.md` for the full schema.

**Fallback on agent failure:** If any sub-agent returns without results, run those
keyword searches directly from the main context. Do not leave gaps.

### Step 6: Snapshot Storage

Create the snapshot directory if it does not exist:

```bash
mkdir -p ~/.nimble/memory/seo/rank-snapshots/{domain}
```

Write two files simultaneously:

**Snapshot file** — `~/.nimble/memory/seo/rank-snapshots/{domain}/snapshot-{YYYY-MM-DD}.json`:

```json
{
  "domain": "example.com",
  "date": "2026-04-13",
  "country": "US",
  "locale": "en",
  "keywords_tracked": 15,
  "keywords_ranked": 12,
  "rankings": [
    {
      "keyword": "project management software",
      "position": 3,
      "ranking_url": "https://example.com/features",
      "title": "Project Management Features | Example",
      "snippet": "...",
      "serp_features": ["people_also_ask", "site_links"],
      "checked_at": "2026-04-13T14:30:00Z"
    }
  ]
}
```

For keywords where the domain does not appear in top 20, record `"position": null`
and `"ranking_url": null`.

**Canonical keyword list** — `~/.nimble/memory/seo/rank-snapshots/{domain}/keywords.json`:

```json
{
  "domain": "example.com",
  "updated": "2026-04-13",
  "keywords": [
    "project management software",
    "team collaboration tool",
    "task tracking app"
  ]
}
```

Merge new keywords into the existing list (union, not replace). This file persists
the tracked keyword set across runs so future runs can auto-load it.

### Step 7: Delta Computation

**Skip in full mode** (no previous snapshot) — all positions are new baselines.

**In delta mode**, load the previous snapshot and compute deltas:

```python
delta = previous_position - current_position
```

Positive delta = position improved (moved up). Negative delta = position dropped.

Classify each keyword:

| Condition | Classification |
|-----------|---------------|
| `abs(delta) >= 5` | **Major move** |
| `abs(delta)` is 2-4 | **Notable shift** |
| `abs(delta) <= 1` | **Stable** |
| Previously null, now ranked | **New entry** (entered top 20) |
| Previously ranked, now null | **Drop-out** (fell out of top 20) |
| Both null | **Not ranked** (unchanged) |

Compute summary stats:
- Keywords in positions 1-3, 4-10, 11-20, not ranked — current vs previous
- Total improved, declined, stable
- Average position change

### Step 8: Report Generation

Build the report using the output format below. In delta mode, the TL;DR focuses
on what changed. In full mode, the TL;DR summarizes the current position landscape.

Always include the full keyword rankings table regardless of mode — the TL;DR and
Biggest Movers sections handle the delta focus; the full table is the reference.

### Step 9: Save & Update Memory

Write the report and update memory simultaneously:

- Report → `~/.nimble/memory/reports/seo-rank-tracker-{YYYY-MM-DD}.md`
- Profile → update `last_runs.seo-rank-tracker` in `~/.nimble/business-profile.json`
- Follow `references/memory-and-distribution.md` for wiki updates:
  - Update `~/.nimble/memory/index.md` (bump seo/ directory entry)
  - Append to `~/.nimble/memory/log.md`:

```markdown
## [YYYY-MM-DD] seo-rank-tracker
- Domain: {domain}, {N} keywords tracked
- Key findings:
  - {biggest mover up}
  - {biggest mover down or notable pattern}
```

  - Add cross-references if the tracked domain matches a known competitor in
    `~/.nimble/memory/competitors/`

### Step 10: Share & Distribute

Follow `references/memory-and-distribution.md` for connector detection and sharing.

- **Slack:** TL;DR with biggest movers only — positions and deltas, no full table.
- **Notion:** Full report as a dated subpage.

### Step 11: Follow-ups

Suggest next actions based on findings:

> **Next steps:**
> - Run `seo-keyword-research` to discover new keywords worth tracking
> - Run `seo-site-audit` to fix on-page issues for keywords that dropped
> - Run `seo-content-gap` to find content opportunities around low-ranking keywords
> - Re-run this tracker in a week to measure progress

If keywords dropped significantly, specifically recommend `seo-site-audit` for
those URLs.

---

## Output Format

```markdown
# SEO Rank Tracker: {domain} — {date}

## TL;DR
[3-5 sentences: total keywords tracked, how many ranked, biggest movers,
overall trend direction. In full mode: position distribution summary.
In delta mode: what changed since last check on {previous_date}.]

## Position Summary

| Range | Count | Change vs Last |
|-------|-------|----------------|
| 1-3 (top positions) | {n} | {+/-n or "—" if first run} |
| 4-10 (page 1) | {n} | {"—" if first run} |
| 11-20 (page 2) | {n} | {"—" if first run} |
| Not ranked (>20) | {n} | {"—" if first run} |

**First-run convention:** Use "—" for all delta columns (Change vs Last, Delta).
In the Full Keyword Rankings table, use "BASELINE" instead of "NEW" for first-run
entries. "NEW" is reserved for delta mode when a keyword newly enters the top 20.

**{n} keywords improved, {n} declined, {n} stable.**

## Biggest Movers

### Gains ▲

| Keyword | Previous | Current | Delta | URL |
|---------|----------|---------|-------|-----|
| {keyword} | {pos} | {pos} | +{n} | [link]({url}) |

### Drops ▼

| Keyword | Previous | Current | Delta | URL |
|---------|----------|---------|-------|-----|
| {keyword} | {pos} | {pos} | {-n} | [link]({url}) |

### New Entries
[Keywords that entered the top 20 for the first time.]

### Drop-outs
[Keywords that fell out of the top 20.]

### Top Competitors per Unranked Keyword

For keywords where the target domain is not in the top 20, show the top 3
ranking competitors to give context on who occupies those positions:

| Keyword | #1 | #2 | #3 |
|---------|----|----|-----|
| {keyword} | {domain} | {domain} | {domain} |

This section helps the user understand the competitive landscape for keywords
they don't yet rank for. Skip in delta mode if the unranked set hasn't changed.

## Full Keyword Rankings

| Keyword | Position | Delta | URL | SERP Features |
|---------|----------|-------|-----|---------------|
| {keyword} | {pos} | {delta or "NEW"} | [link]({url}) | {features} |
| {keyword} | — | DROP | — | — |

## SERP Feature Presence

| Feature | Keywords Appearing | Change vs Last |
|---------|-------------------|----------------|
| Featured Snippet | {n} | {+/-n} |
| People Also Ask | {n} | {+/-n} |
| AI Overview | {n} | {+/-n} |
| Image Pack | {n} | {+/-n} |
| Video Pack | {n} | {+/-n} |
| Local Pack | {n} | {+/-n} |
| Knowledge Panel | {n} | {+/-n} |
| Site Links | {n} | {+/-n} |

## What This Means
[2-3 paragraphs: interpret the ranking data. Are positions trending up or down?
Which keyword clusters are strongest? Are SERP features creating opportunities
or squeezing organic clicks? Specific, actionable — not generic SEO advice.]

## Next Steps
[Bulleted recommendations tied to the data. Link to sibling skills where relevant.]
```

---

## Error Handling

See `references/nimble-playbook.md` for the standard error table (missing API key,
429, 401, empty results, timeout). Skill-specific errors:

- **Empty SERP result** for a keyword: Retry once with a broader query variant
  (e.g., drop quotes, simplify phrasing). If still empty, record position as null
  and note "SERP returned no organic results" in the keyword record.
- **Keyword not in top 20:** Record `position: null`, `ranking_url: null`. This is
  expected behavior, not an error. Show as "Not ranked" in the report.
- **Rate limit (429):** Reduce sub-agent concurrency from 4 to 2. If still hitting
  limits, serialize queries (one at a time). Do not drop keywords.
- **WSA agent error:** Fall back to `nimble search` for that keyword batch. Log which
  WSA failed so the user knows.
- **Snapshot parse error:** If a previous snapshot JSON is malformed, treat as first
  run (full mode). Warn: "Previous snapshot was corrupted — running fresh baseline."

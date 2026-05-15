
# SEO Rank Tracker

Live keyword position tracking with JSON snapshots and delta reporting.


---

## Instructions

### Step 0: Preflight

Follow the transport selection + standard preflight from `references/nimble-playbook.md` — pick CLI or MCP at session start, then run the standard preflight calls (date calc, today, profile, memory index) in parallel.

From the results:
- CLI missing or API key unset → `references/profile-and-onboarding.md`, stop
- Tag all `nimble` CLI calls: `nimble --client-source skill-seo-intel <subcommand>`. MCP path: not yet supported — see `references/nimble-playbook.md` for status.
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

### Step 4: SERP Query Execution

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
nimble --client-source skill-seo-intel serp run \
  --search-engine google_search \
  --query "{keyword}" \
  --parse --num-results 20 \
  --country {cc} --locale {locale}

Parse data.parsing.entities from the JSON response. For each keyword:
1. Look in entities.OrganicResult for entries where the root domain matches "{domain}"
   (strip www., trailing slash, protocol when comparing).
2. Position is already in the entity: OrganicResult[n].position (1-indexed).
3. Record position, url, title, snippet from the matching OrganicResult entry.
4. If the domain does not appear in OrganicResult, record position as null.
5. SERP features: check which entity type keys are present in entities.
   Map them to serp_features: AnswerBox → "featured_snippet",
   RelatedQuestion → "people_also_ask", AIOverview → "ai_overview",
   Ad → "ads", KnowledgeGraph → "knowledge_panel".
   Add any other entity type key as lowercase_snake_case. Do not skip unknown types.

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
```

**Fallback on agent failure:** If any sub-agent returns without results, run those
keyword searches directly from the main context. Do not leave gaps.

### Step 5: Snapshot Storage

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

### Step 6: Delta Computation

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

### Step 7: Report Generation

Build the report using the output format below. In delta mode, the TL;DR focuses
on what changed. In full mode, the TL;DR summarizes the current position landscape.

Always include the full keyword rankings table regardless of mode — the TL;DR and
Biggest Movers sections handle the delta focus; the full table is the reference.

### Step 8: Save & Update Memory

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

### Step 9: Share & Distribute

Follow `references/memory-and-distribution.md` for connector detection and sharing.

- **Slack:** TL;DR with biggest movers only — positions and deltas, no full table.
- **Notion:** Full report as a dated subpage.

### Step 10: Follow-ups

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

Close with bulleted recommendations tied to the data, linking to sibling
skills where relevant. Keep these as a final paragraph under What This Means,
not a new top-level section.
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

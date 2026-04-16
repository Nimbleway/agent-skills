
# Content Gap Analysis

Crawl-based content gap analysis validated against live SERP data.


---

## Instructions

### Step 0: Preflight

Run the preflight pattern from `references/nimble-playbook.md` (5 simultaneous Bash
calls: date calc, today, CLI check, profile load, index.md load).

From the results:
- CLI missing or API key unset → `references/profile-and-onboarding.md`, stop
- Profile exists → check for sibling handoff from `seo-keyword-research` or
  `seo-site-audit` (same-day reports under `~/.nimble/memory/reports/`):
  ```bash
  ls ~/.nimble/memory/reports/seo-keyword-research-*$(date +%Y-%m-%d).md 2>/dev/null
  ls ~/.nimble/memory/reports/seo-site-audit-*$(date +%Y-%m-%d).md 2>/dev/null
  ```
  If found, load the sibling report to reuse competitor lists, site maps, or keyword
  data — avoid re-crawling domains already mapped today.
- Load prior content-gap snapshots from
  `~/.nimble/memory/seo/content-gap/{user-domain-slug}/`. If a previous JSON exists,
  load it for delta mode (Step 9). Determine mode using smart date windowing from
  `references/nimble-playbook.md`:
  - **Full mode:** first run OR last run > 14 days ago
  - **Delta mode:** last run < 14 days ago — surface only new gaps
  - **Same-day repeat:** if `last_runs.seo-content-gap` is today, check for an
    existing report. If found, ask: "Already ran content gap analysis today. Run
    again for fresh data?" Don't silently re-run.
  - Skip to Step 2
- No profile → Step 1

### Step 1: First-Run Onboarding (2 prompts max)

Follow `references/profile-and-onboarding.md` for prerequisite checks (CLI install,
version validation, API key setup) and company setup (Prompt 1: domain verification).

**Prompt 2** — skill-specific setup (use AskUserQuestion):

> I found that **[Company]** ([domain]) is [brief description].
> Tell me about your content gap analysis goals:
> - **Competitor URLs** — which 1-3 competitors should I compare against?
> - **Focus area** — full site, or a specific section? (e.g., `/blog`, `/resources`)
> - **Goal** — content strategy, traffic growth, or competitive coverage?

Capture answers into the profile under `seo_context` and create the profile per
`references/profile-and-onboarding.md`.

### Step 2: Shape Scope (2 prompts max)

If the user's domain, competitors, and scope are already known (from profile, sibling
handoff, or `$ARGUMENTS`), skip to Step 3.

**Prompt 1** — ask in plain text (NOT AskUserQuestion):

> "What's your site domain, and which 1-3 competitor domains should I compare against?"

If only the user domain is provided, discover competitors automatically:

```bash
nimble search --query "[Company] competitors" --max-results 10 --search-depth lite
nimble search --query "[Company] vs" --max-results 10 --search-depth lite
nimble search --query "[Company] alternatives" --max-results 5 --search-depth lite
```

Run all three simultaneously. Propose a competitor shortlist and confirm.

**Prompt 2** — confirm scope (use AskUserQuestion):

> I'll compare **{user domain}** against **{competitor 1}**, **{competitor 2}**
> {, **{competitor 3}**}.
> - **Focus area?** Full site / `/blog` / `/resources` / other path prefix
> - **Crawl depth?**
>   - **Quick (50 pages per domain)** — ~2 min
>   - **Standard (200 pages)** — ~5 min
>   - **Deep (500 pages)** — ~10 min

Parse: user domain, competitor domains (1-3), optional path prefix, crawl depth
(50/200/500).

### Step 3: Parallel Site Mapping

Map all domains simultaneously — one `nimble map` call per domain, all in a single
response:

```bash
nimble map --url "https://{user-domain}" --limit {crawl_depth}
nimble map --url "https://{competitor-1}" --limit {crawl_depth}
nimble map --url "https://{competitor-2}" --limit {crawl_depth}
```

If a focus area was specified (e.g., `/blog`), filter each domain's URL list to keep
only pages matching the path prefix. Always keep the homepage regardless of prefix.

Store the URL lists per domain for extraction in Step 4.

**Fallback:** If `nimble map` returns empty for any domain, fall back to site-search:

```bash
nimble search --query "site:{domain}" --max-results 20 --search-depth lite
```

Parse URLs from the search results and use those as the crawl list.

### Step 4: Content Extraction via Sub-Agents

Read `references/content-gap-agent-prompt.md` for the full agent prompt template.
Follow the sub-agent spawning rules from `references/nimble-playbook.md`
(bypassPermissions, batch max 4, explicit Bash instruction, fallback on failure).

Spawn `nimble-researcher` agents (`agents/nimble-researcher.md`) with
`mode: "bypassPermissions"`. One agent per domain. Replace template placeholders
with actual values: `{domain}`, `{page_urls_json}`, `{focus_prefix}`, `{date}`,
`{batch_cap}`.

Each agent handles one domain and returns a JSON array of page records. Per page:
- `url`, `title`, `meta_description`, `h1`, `h2_outline` (list)
- `primary_topic` (single noun phrase), `secondary_topics` (list)
- `target_keywords` (list — inferred from title + H1 + first paragraph)
- `word_count`, `content_type` (blog_post / product / landing / docs / resource /
  pricing / about / other)
- `pub_date` (if visible)

Agents use `nimble extract-batch` when their page list has 11+ URLs, otherwise
parallel `nimble extract` calls. See the agent prompt for extraction and escalation
rules.

**Call estimation:** Before launching agents, estimate total extractions: pages per
domain x number of domains. For 100+ total pages, tell agents to use `extract-batch`
per the Scaled Execution pattern in `references/nimble-playbook.md`.

**Fallback:** If an agent fails or returns empty, re-run those extractions directly
from the main context. Don't leave gaps.

### Step 5: Topic Modeling & Normalization

Cluster all extracted pages across all domains into normalized topic clusters:

1. **Extract noun phrases** from each page's H1, H2 outline, and `primary_topic`.
2. **Normalize** — lowercase, strip punctuation, stem noun phrases
   (e.g., "Content Marketing Strategies" → "content marketing strategy").
3. **Cluster** — group pages sharing the same normalized primary topic or 2+
   overlapping secondary topics. Label each cluster with the most common noun phrase.
4. **Build coverage matrix** — rows = topic clusters, columns = domains, cells:
   - `page_count`: number of pages covering this topic
   - `avg_word_count`: mean word count across those pages
   - `has_hub_page`: boolean — true if any page in the cluster has `content_type`
     of `landing` or `resource` with 3+ internal links to other pages in the cluster

Use `python3` for clustering if the page count exceeds 50 — write a short inline
script that reads the extracted JSON and outputs the coverage matrix as JSON.

### Step 6: Gap Identification

A topic is a **gap** if:
- Any competitor has >= 1 page AND the user has 0 pages on that topic, OR
- The user's `avg_word_count` for the topic is < 30% of the best competitor's
  `avg_word_count` (thin coverage gap)

For each identified gap, record:
- `topic_cluster`: the normalized topic label
- `gap_type`: "missing" (no user pages) or "thin" (word count deficit)
- `competitors`: list of competitor domains covering the topic
- `competitor_page_count`: total pages competitors have on this topic
- `competitor_avg_word_count`: best competitor's average word count
- `competitor_has_hub`: whether any competitor has a hub page
- `representative_url`: the best competitor page URL for this topic
  (highest word count or hub page)
- `user_page_count`: 0 for missing, actual count for thin
- `user_avg_word_count`: 0 for missing, actual for thin

### Step 7: SERP Validation

For each gap topic, derive 2-3 representative search queries from the topic's top
H1s and target keywords.

**Tiered SERP validation** — validate in two passes to control costs:

**Pass 1 (all gaps):** lite sweep to confirm competitor presence:

```bash
nimble search --query "{query}" --search-depth lite --max-results 10
```

Run in parallel batches of 4. Classify each gap based on whether the competitor's
domain appears in organic results (CONFIRMED / MODERATE / LOW_PRIORITY per the
table below).

**Pass 2 (CONFIRMED gaps only):** deep enrichment for SERP features and PAA:

```bash
nimble search --query "{query}" --search-depth deep --max-results 10
```

Run only for gaps classified as CONFIRMED in Pass 1. This captures AI Overview
presence, Featured Snippets, PAA questions, and richer result data. Skip deep
queries for MODERATE and LOW_PRIORITY gaps — the lite pass already established
their rank.

For each query, check whether the competitor's representative URL appears in the
SERP results. Classify the gap's SERP strength:

| Competitor Rank | Classification |
|-----------------|----------------|
| Top 10 | **CONFIRMED** — high-value gap |
| Top 11-20 | **MODERATE** — competitor ranks but not dominant |
| Not found in top 20 | **LOW PRIORITY** — competitor has content but doesn't rank |

Also capture SERP features for each query:
- AI Overview present (yes/no)
- Featured Snippet present (yes/no)
- People Also Ask present (yes/no, list questions)
- Video carousel, image pack, local pack

**Fallback:** If a SERP query returns < 3 results, retry without date filters or
with a broader query (shorter, fewer modifiers). If still sparse, classify as
**UNVALIDATED** and note it in the report.

### Step 8: Scoring & Prioritization

Score each validated gap using:

```
score = (competitor_rank_strength x topic_relevance) / estimated_effort
```

Where:
- **competitor_rank_strength**: CONFIRMED = 3, MODERATE = 2, LOW_PRIORITY = 1,
  UNVALIDATED = 1 (gaps without SERP data default to lowest rank strength — they
  don't get penalized but they can't score higher than validated gaps)
- **topic_relevance**: how closely the topic aligns with the user's domain and
  stated goals (High = 3, Medium = 2, Low = 1) — inferred from overlap with the
  user's existing content themes
- **estimated_effort**: based on the competitor's avg_word_count for the topic
  (< 1500 words = Low effort = 1, 1500-3000 = Medium = 2, 3000+ = High = 3) plus
  a hub page bonus (+1 if the competitor has a hub page, since the user would need
  to build one too)

**Partial SERP coverage guard:** If SERP validation was run for < 50% of gaps (due
to cost constraints or query limits), note this in the report TL;DR:
"SERP validated {N}/{total} gaps — unvalidated gaps scored conservatively." This
prevents the scoring from creating misleading buckets when most gaps are unvalidated.

Bucket gaps into three tiers:

| Tier | Criteria |
|------|----------|
| **Quick Wins** | Low effort + CONFIRMED or MODERATE rank — fastest path to new traffic |
| **Strategic Bets** | High effort + CONFIRMED rank — worth investing in, significant opportunity |
| **Nice-to-Have** | LOW PRIORITY rank, or high effort + MODERATE rank |

Sort each tier by score descending.

### Step 9: Report & Save

**Report** → `~/.nimble/memory/reports/seo-content-gap-{user-domain-slug}-{YYYY-MM-DD}.md`

**Snapshot** → `~/.nimble/memory/seo/content-gap/{user-domain-slug}/{YYYY-MM-DD}.json`

The JSON snapshot stores all gap records with SERP validation data — used for delta
mode on future runs. Structure:

```json
{
  "date": "YYYY-MM-DD",
  "user_domain": "...",
  "competitors": ["..."],
  "crawl_depth": 200,
  "gaps": [
    {
      "topic_cluster": "...",
      "gap_type": "missing|thin",
      "serp_classification": "CONFIRMED|MODERATE|LOW_PRIORITY|UNVALIDATED",
      "tier": "quick_win|strategic_bet|nice_to_have",
      "score": 4.5,
      "competitor_url": "...",
      "serp_features": ["ai_overview", "featured_snippet", "paa"]
    }
  ],
  "coverage_matrix": { ... }
}
```

**Delta mode:** If a prior snapshot exists (loaded in Step 0), compare the current
gap list against the previous one. Mark each gap as:
- **NEW** — not in the prior snapshot
- **CLOSED** — was in the prior snapshot but no longer qualifies (user added content)
- **UNCHANGED** — still present

In the report, highlight NEW gaps prominently and note CLOSED gaps as wins. Only
surface new and changed gaps in the TL;DR.

**Profile** → update `last_runs.seo-content-gap` in `~/.nimble/business-profile.json`

Follow the wiki update pattern from `references/memory-and-distribution.md`: update
`index.md` rows for affected directories, append a `log.md` entry for this run.
Create `~/.nimble/memory/seo/content-gap/{user-domain-slug}/` if it doesn't exist.

Make all Write calls simultaneously.

### Step 10: Share & Distribute

**Always offer distribution — do not skip this step.** Follow
`references/memory-and-distribution.md` for connector detection, sharing flow, and
source links enforcement.

**Slack-specific:** Post a concise TL;DR with the top 5 gaps:

> Content Gap: {user domain} vs {competitors} — {N} gaps found.
> Top gaps: {gap 1}, {gap 2}, {gap 3}, {gap 4}, {gap 5}.
> Full report saved locally.

### Step 11: Follow-ups

- **Go deeper on a gap** → expand the topic with more keyword research
- **Add a competitor** → re-run with the additional domain
- **Narrow the focus** → re-run scoped to a specific path prefix
- **"Looks good"** → done

**Sibling skill suggestions:**

> **Next steps:**
> - Run `seo-keyword-research` to expand keywords for the top gap topics
> - Run `seo-site-audit` to ensure existing content is technically healthy
> - Run `competitor-positioning` to understand how competitors message these topics
> - Run `seo-competitor-keywords` to see the full keyword landscape competitors own

---

## Output Format

```markdown
# Content Gap Analysis: {user domain} vs [{competitors}]

**Pages analyzed:** {X} yours, {Y} competitor(s) | **Date:** {YYYY-MM-DD}
**Scope:** {full site | path prefix} | **Crawl depth:** {50|200|500} per domain

## TL;DR

- **{N} content gaps** found across {M} topic clusters
- **{N} Quick Wins** — low effort, competitors ranking in top 10
- **Biggest gap:** "{topic}" — {competitor} has {N} pages, you have none
- **{N} SERP-confirmed** gaps with real ranking opportunity
{If delta mode: "**{N} new gaps** since last run on {prior date}. {N} gaps closed."}

---

## Quick Wins (low effort, high opportunity)

| Gap Topic | Gap Type | Competitor Coverage | Their Best Rank | SERP Features | Suggested Content |
|-----------|----------|--------------------:|:---------------:|---------------|-------------------|
| {topic} | Missing | {domain}: {N} pages, {avg words} avg | Top 10 | PAA, Snippet | {content type + angle} |
| ... | ... | ... | ... | ... | ... |

## Strategic Bets (high effort, high opportunity)

| Gap Topic | Gap Type | Competitor Coverage | Their Best Rank | SERP Features | Suggested Content |
|-----------|----------|--------------------:|:---------------:|---------------|-------------------|
| {topic} | Missing | {domain}: {N} pages, hub page | Top 10 | AI Overview | {content type + angle} |
| ... | ... | ... | ... | ... | ... |

## Nice-to-Have

| Gap Topic | Gap Type | Competitor Coverage | Their Best Rank | SERP Features | Suggested Content |
|-----------|----------|--------------------:|:---------------:|---------------|-------------------|
| ... | ... | ... | ... | ... | ... |

## Coverage Matrix

| Topic Cluster | {your domain} | {competitor 1} | {competitor 2} | {competitor 3} |
|---------------|:-------------:|:--------------:|:--------------:|:--------------:|
| {topic} | {N} pages ({avg wc}) | {N} pages ({avg wc}) [hub] | -- | -- |
| {topic} | -- | {N} pages ({avg wc}) | {N} pages ({avg wc}) | -- |
| ... | ... | ... | ... | ... |

**Legend:** -- = no coverage, [hub] = has a hub/pillar page

## SERP Landscape

- **CONFIRMED gaps (top 10):** {N}
- **MODERATE gaps (top 20):** {N}
- **LOW PRIORITY (not ranking):** {N}
- **Common SERP features across gaps:** {list}
- **PAA questions discovered:** {list 5-10 — these are content angle ideas}

## What This Means

{2-4 sentences: strategic interpretation. Where is the biggest opportunity cluster?
What content types dominate the gap topics? What's the fastest path to closing the
top gaps? Any pattern in what competitors cover that the user doesn't?}

**30-day priorities:** {top 3 Quick Wins to create}
**60-day priorities:** {top 2 Strategic Bets to plan}
**90-day priorities:** {remaining Strategic Bets + hub page buildout}

Recommended follow-ups:

- Run `seo-keyword-research` to expand keywords for the top gap topics
- Run `seo-site-audit` to ensure existing content is technically healthy
- Run `competitor-positioning` to understand competitor messaging angles
- Run `seo-competitor-keywords` for the full competitor keyword landscape
```

Every gap in the report MUST tie to a verified competitor URL from the SERP results.

---

## Error Handling

See `references/nimble-playbook.md` for the standard error table (missing API key,
429, 401, empty results, extraction garbage). Skill-specific errors:

- **Empty map** — `nimble map` returns 0 URLs for a domain. Fall back to site-search:
  `nimble search --query "site:{domain}" --max-results 20 --search-depth lite`.
  Parse URLs from results and use those as the page list.
- **Extraction garbage** — agent returns pages with < 100 chars of meaningful content.
  Escalate render tier per `references/nimble-playbook.md`: retry with `--render`,
  then `--render --driver vx10-pro`. If still garbage after Tier 3, record the page
  as "extraction failed" and exclude from topic modeling.
- **SERP returns < 3 results** — retry the query without date filters. If still
  sparse, broaden the query (shorter terms, fewer modifiers). If still < 3,
  classify the gap as **UNVALIDATED** and note it in the report.
- **Search 500** — retry once without `--focus` flag. If persistent, simplify the
  query. Log the failure but continue with remaining gaps.
- **Too few pages mapped** — if a domain returns < 5 pages, note limited coverage
  in the report. The analysis is still valid but less comprehensive.
- **Agent failure** — if a sub-agent fails entirely, re-run its extractions directly
  from the main context. Don't skip a domain.

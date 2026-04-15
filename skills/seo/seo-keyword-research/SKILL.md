---
name: seo-keyword-research
description: |
  Discovers keyword opportunities by analyzing live SERPs, competitor pages,
  and search intent — using Nimble's web data APIs instead of third-party SEO
  tool estimates. Returns evidence-based difficulty scores, intent
  classifications, and prioritized topic clusters grounded in actual SERP data.

  Use when the user asks about keyword research, SEO keywords, or similar.
  Triggers: "keyword research", "keyword opportunities", "keyword strategy",
  "find keywords", "SEO keywords", "keyword gaps", "keyword ideas", "keyword
  difficulty", "content gaps", "what to rank for", "keyword cluster", "search
  intent", "long-tail keywords".

  Do NOT use for technical SEO audits — use `seo-site-audit` instead. Do NOT
  use for tracking rank positions over time — use `seo-rank-tracker` instead.
  Do NOT use for writing or optimizing content.
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

# SEO Keyword Research

Evidence-based keyword discovery and opportunity scoring powered by live SERP data.

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
- Profile exists → read `~/.nimble/memory/seo/keyword-research/` and
  `~/.nimble/memory/reports/seo-keyword-research-*.md` to check for previous runs.
  Load any existing keyword data for dedup. Determine mode using smart date windowing
  from `references/nimble-playbook.md`:
  - **Full mode:** first run OR last run > 14 days ago
  - **Quick refresh:** last run < 14 days ago
  - **Same-day repeat:** if `last_runs.seo-keyword-research` is today, check for an
    existing report. If found, ask: "Already ran keyword research today. Run again
    for fresh data?" Don't silently re-run.
  - Skip to Step 2
- No profile → Step 1

### Step 1: First-Run Onboarding (2 prompts max)

Follow `references/profile-and-onboarding.md` for prerequisite checks (CLI install,
version validation, API key setup) and company setup (Prompt 1: domain verification).

**Prompt 2** — skill-specific setup (use AskUserQuestion):

> I found that **[Company]** ([domain]) is [brief description].
> Tell me about your keyword research goals:
> - **Topic or seed keywords** — what topics do you want to rank for?
>   (e.g., "AI-powered project management tools")
> - **Competitor URLs** — any competitors already ranking for your target terms?
> - **Goal** — traffic growth, lead generation, content strategy, or product launch?
> - **Geography** — US, global, or specific markets?
> - **Site maturity** — new site, established with some rankings, or authority domain?

Capture answers into the profile under `seo_context` and create the profile per
`references/profile-and-onboarding.md`.

### Step 2: WSA Discovery

Discover available WSAs for SEO data. Run three searches simultaneously:

```bash
nimble agent list --search "seo" --limit 20
nimble agent list --search "google" --limit 20
nimble agent list --search "trends" --limit 20
```

From the results, filter for WSAs related to search results, keyword data, or
trend analysis. Validate each candidate with `nimble agent get --template-name {name}`
to confirm input params and output fields. Cache discovered WSA names for this run.

If no useful WSAs found, continue with `nimble search` alone — WSAs are an
enrichment layer, not a requirement.

### Step 3: Seed Expansion

Generate 15-25 seed keyword variations from the user's topic/seed keywords. Use these
strategies:

1. **Core terms** — the user's exact seed keywords
2. **Modifiers** — add "best", "how to", "vs", "alternatives", "tools", "software",
   "guide", "template", "examples", "for [audience]"
3. **Long-tail questions** — "how to [topic]", "what is [topic]", "why [topic]",
   "[topic] for [use case]"
4. **Commercial variants** — "[topic] pricing", "[topic] reviews", "[topic] comparison"
5. **Related concepts** — adjacent topics the target audience also searches for

Group seeds into 3-5 thematic clusters. Each cluster gets a working label
(e.g., "Informational Guides", "Product Comparison", "Use-Case Specific").

### Step 4: Live SERP Analysis

For each seed keyword, run a SERP query. Batch 4 searches at a time:

```bash
nimble search --query "{keyword}" --search-depth lite --max-results 10
```

Run up to 4 simultaneously per the parallel execution rules in
`references/nimble-playbook.md`. For 10+ keywords, batch in groups of 4.

From each SERP, collect:
- **Top URLs** — the ranking pages (title, URL, domain)
- **Dominant content types** — blog posts, product pages, listicles, tools,
  comparison pages, videos
- **Dominant domains** — which domains appear across multiple keywords

**Note:** `--search-depth lite` returns organic result metadata only (title, URL,
description, position). It does NOT return SERP features.

**SERP feature enrichment** — for 3-5 priority keywords, run the `google_search`
agent to get typed SERP entities (PAA, Featured Snippets, Shopping, Sitelinks):

```bash
nimble agent run --agent google_search --params '{"query": "{keyword}", "num_results": 20, "country": "US", "locale": "en"}'
```

The `google_search` agent returns `data.parsing.entities` — a **dict keyed by
entity type name**, where each value is an array of records. Entity types are
dynamic — iterate all keys rather than hardcoding. Commonly observed types:

| Entity type | What it is | Key fields |
|---|---|---|
| `AIOverview` | AI-generated answer at top of SERP | `content`, `links`, `blocks` |
| `OrganicResult` | Standard organic listing | `position`, `url`, `title`, `snippet`, `cleaned_domain` |
| `RelatedQuestion` | People Also Ask questions | `question` |
| `RelatedSearch` | Related searches at bottom | `query`, `url` |
| `Ad` | Paid ads | `position`, `url`, `title`, `description` |

Other types may appear depending on query (news, images, shopping, local, knowledge
panels, featured snippets, etc.). Always iterate `entities.keys()` to detect
which features are present — do not check only the types listed above.

Parse `data.parsing.entities` to collect:
- **SERP features** — check which entity type keys exist (e.g., `AIOverview`
  present = GEO surface; `RelatedQuestion` present = AEO opportunity)
- **PAA questions** — `entities.RelatedQuestion[].question` — free long-tail ideas
- **Related searches** — `entities.RelatedSearch[].query` — free keyword expansion
- **AI Overview content** — `entities.AIOverview[0].content` — check if brand/competitor is mentioned

Additional `google_search` params available: `time` (hour/day/week/month/year),
`location` (city/state string or UULE), `start` (pagination: 0/10/20...).
See `references/ai-platform-profiles.md` for the full agent schema.

If a lite search returns < 3 results, broaden the query (remove modifiers, use shorter
terms) and retry once.

### Step 5: Competitor Page Extraction

Identify the top 3-5 ranking pages per priority keyword cluster. Spawn
`nimble-researcher` sub-agents (`agents/nimble-researcher.md`) with
`mode: "bypassPermissions"` to extract and analyze these pages.

Read `references/keyword-research-agent-prompt.md` for the full sub-agent prompt
template. Replace placeholders with actual values before spawning.

Follow the sub-agent spawning rules from `references/nimble-playbook.md`
(bypassPermissions, batch max 4, explicit Bash instruction, fallback on failure).

Each agent extracts assigned URLs with:

```bash
nimble extract --url "{url}" --format markdown --render
```

Agents return structured findings per URL: word count, H1/H2/H3 heading outline,
topic coverage, content type, and domain authority signals (site age indicators,
backlink mentions, brand recognition).

**Call estimation:** Before launching agents, estimate total extractions. For 5+
keyword clusters with 3-5 pages each (15-25 extractions), tell agents to use
`extract-batch` per the Scaled Execution pattern in `references/nimble-playbook.md`.

If any agent fails or returns empty, run those extractions directly from the main
context. Don't leave gaps.

### Step 6: Site Structure Signal

For each top competitor domain discovered in Step 4, map their content structure:

```bash
nimble map --url "{competitor-domain}" --limit 5
```

Run up to 4 simultaneously. Use the discovered page structure to assess:
- Content depth (number of pages on the topic)
- Site architecture signals (dedicated sections, pillar pages, supporting content)
- Internal linking patterns

If `nimble map` returns empty or < 3 pages, skip this signal for that domain and
continue. Don't block the analysis on a missing site map.

### Step 7: Difficulty Scoring

Score each keyword as **Low / Medium / High / Very High** based on observable evidence.
No fabricated metrics — every score must trace back to SERP data.

**Scoring inputs:**
- **Domain authority signals of top rankers** — are they major brands (Forbes, HubSpot)
  or niche sites? How many unique domains appear in top 10?
- **Content depth from extraction** — average word count and heading depth of top
  ranking pages
- **SERP feature saturation** — featured snippets, PAA boxes, and knowledge panels
  indicate Google has strong existing answers
- **Content type alignment** — does the user's likely content type match what's ranking?
  (e.g., if all top results are tools and user plans a blog post, difficulty goes up)
- **Site structure from Step 6** — competitors with deep topical coverage on a keyword
  are harder to displace

**Scoring rubric:**

| Difficulty | Criteria |
|---|---|
| **Low** | Niche/small domains in top 5, thin content (<1500 words avg), few SERP features, content type match |
| **Medium** | Mix of authority and niche domains, moderate content depth, some SERP features |
| **High** | Authority domains dominate top 5, deep content (3000+ words avg), multiple SERP features |
| **Very High** | Major brands own top 10, rich SERP features, deep topical coverage, content type mismatch |

### Step 8: Intent Classification + AI Surface Type

Classify each keyword's search intent based on SERP evidence (not guessing):

| Intent | SERP Signals |
|---|---|
| **Informational** | How-to guides, blog posts, Wikipedia, educational content dominate |
| **Navigational** | Brand-specific results, official site dominates position 1 |
| **Commercial** | Comparison pages, "best of" lists, review sites, G2/Capterra |
| **Transactional** | Product pages, pricing pages, "buy" CTAs, shopping results |

Use the actual SERP composition from Step 4 as evidence. A keyword can have mixed
intent — note the primary and secondary intent.

**AI Surface Type** — also classify which AI surfaces this keyword triggers:

| Surface | Detection Signal | Content Strategy |
|---------|-----------------|------------------|
| **GEO** (AI Overview, Perplexity, ChatGPT) | AI Overview present in fast-pass results; query is a question or comparison | Self-contained 134-167 word passages with statistics and citations (see `references/ai-platform-profiles.md` for Princeton GEO methods) |
| **AEO** (Featured Snippet, PAA) | Featured Snippet or PAA box present | Direct 40-55 word answer blocks; FAQ schema JSON-LD |
| **Traditional SERP only** | No AI features detected | Standard SEO: title, meta, content depth, backlinks |

This classification changes the content recommendation in Step 9 (Clustering).
A keyword triggering GEO surfaces needs citation-rich, statistic-dense content
blocks. A keyword triggering AEO needs concise direct-answer formatting. Note
the surface type alongside intent in the output.

### Step 9: Clustering

Group all keywords (seeds + PAA discoveries + long-tail variants) into topic clusters:

- **Pillar keyword** — the broadest, highest-volume term in the cluster
- **Supporting long-tails** — more specific variants that link back to the pillar
- **Content strategy** — the recommended content type and approach for each cluster
  (pillar page + supporting blog posts, comparison hub, tool/template, etc.)

Aim for 3-7 clusters depending on the breadth of the user's topic. Each cluster should
have a clear content hierarchy.

### Step 10: Opportunity Scoring

Rank all keywords by opportunity using:

```
Opportunity = (Relevance x Intent Value) / Difficulty
```

Where:
- **Relevance** — how closely the keyword matches the user's stated goals (High=3,
  Medium=2, Low=1)
- **Intent Value** — Transactional=4, Commercial=3, Informational=2, Navigational=1
- **Difficulty** — Low=1, Medium=2, High=3, Very High=4

Surface three tiers:
- **Quick Wins** — Low/Medium difficulty + high relevance + commercial/transactional
  intent. These are the fastest path to traffic and conversions.
- **Growth Targets** — Medium/High difficulty + high intent value. Worth investing in
  with quality content.
- **Moonshots** — Very High difficulty but exceptional intent value. Long-term plays
  requiring sustained effort.

### Step 11: Save & Update Memory

Save results simultaneously:

- **Report** → `~/.nimble/memory/reports/seo-keyword-research-{YYYY-MM-DD}.md`
  (full output — this is the local source of truth)
- **Raw data** → `~/.nimble/memory/seo/keyword-research/{slug}/` where `{slug}` is
  derived from the primary topic. Save:
  - `keywords.json` — all keywords with scores, intent, difficulty, cluster assignment
  - `serp-snapshots.json` — raw SERP data per keyword (top URLs, features, PAA)
  - `competitor-pages.json` — extraction summaries per URL
- **Profile** → update `last_runs.seo-keyword-research` in
  `~/.nimble/business-profile.json`

Follow `references/memory-and-distribution.md` for wiki updates:
- Update `~/.nimble/memory/seo/keyword-research/index.md` (create if missing)
- Update `~/.nimble/memory/index.md` global index
- Append a `log.md` entry for this run
- Add `[[path/entity]]` cross-references where appropriate (e.g., link to
  `[[competitors/name]]` for domains that overlap with tracked competitors)

### Step 12: Share & Distribute

Follow `references/memory-and-distribution.md` for connector detection and sharing flow.
Always offer distribution — do not skip this step.

### Step 13: Follow-ups

Suggest next steps based on findings:

> **Next steps:**
> - Run `seo-site-audit` to check if your site is technically ready to rank for these keywords
> - Run `seo-rank-tracker` to monitor your position on the top opportunities over time
> - Run `seo-content-gap` to find what competitors cover that you don't
> - "Go deeper on [cluster name]" — expand a specific cluster with more long-tail research

---

## Output Format

```markdown
# Keyword Research: [Topic]

**Date:** [YYYY-MM-DD]
**Site:** [domain] | **Geography:** [target market]
**Goal:** [user's stated goal]

## TL;DR

- **[N] keyword opportunities** across **[N] topic clusters**
- **[N] Quick Wins** — low difficulty, high intent
- **Top opportunity:** "[keyword]" — [intent], [difficulty] difficulty
- **Dominant SERP content type:** [e.g., listicles, comparison pages, how-to guides]

---

## Quick Wins

| Keyword | Intent | Difficulty | Content Type | Top Competitor | Opportunity |
|---------|--------|------------|--------------|----------------|-------------|
| [keyword] | [Commercial] | [Low] | [Comparison page] | [competitor.com] | [SERP source URL] |
| ... | ... | ... | ... | ... | ... |

## Growth Targets

| Keyword | Intent | Difficulty | Content Type | Top Competitor | Opportunity |
|---------|--------|------------|--------------|----------------|-------------|
| [keyword] | [Transactional] | [Medium] | [Product page] | [competitor.com] | [source URL] |
| ... | ... | ... | ... | ... | ... |

## Topic Clusters

### Cluster 1: [Pillar Keyword]
- **Pillar:** "[keyword]" — [intent], [difficulty]
- **Supporting:**
  - "[long-tail 1]" — [intent], [difficulty] — [source URL]
  - "[long-tail 2]" — [intent], [difficulty] — [source URL]
- **Content strategy:** [Recommended approach — e.g., "Create a comprehensive pillar
  page covering [topic], link from supporting how-to posts targeting each long-tail."]

### Cluster 2: [Pillar Keyword]
...

## SERP Landscape

- **Features observed:** [Featured snippets on N keywords, PAA on N keywords, ...]
- **Dominant domains:** [domain1.com (appears on N/N keywords), domain2.com (N/N), ...]
- **Format trends:** [Most top results are listicles/guides/tools/videos...]
- **PAA questions discovered:** [List 5-10 PAA questions found — these are free keyword ideas]

## Competitor Strength Analysis

| Domain | Keywords Ranking | Avg Content Depth | Content Type | Site Structure |
|--------|-----------------|-------------------|--------------|----------------|
| [competitor.com] | [N of N keywords] | [~N words] | [Blog/Tool/Hub] | [Deep/Shallow] |
| ... | ... | ... | ... | ... |

## What This Means

[2-4 sentences: strategic interpretation of the findings. What's the fastest path to
traffic? Where are the gaps competitors haven't filled? What content types work best
in this space?]

## Next Steps

- Run `seo-site-audit` to verify your site's technical readiness
- Run `seo-rank-tracker` to monitor positions on Quick Win keywords
- Run `seo-content-gap` to find topics your competitors cover that you don't
```

Every keyword in the report MUST have a source URL from the SERP results.

---

## Error Handling

See `references/nimble-playbook.md` for the standard error table (missing API key, 429,
401, empty results, extraction garbage). Skill-specific notes:

- **Empty SERPs** — broaden the query: remove modifiers, shorten to core terms, remove
  date filters. If still empty after retry, skip the keyword and note it in the report
  as "insufficient SERP data."
- **`nimble map` returns empty** — skip the site structure signal for that domain and
  continue. Site structure is supplementary, not required for difficulty scoring.
- **Extraction returns garbage** — follow the extraction fallback in
  `references/nimble-playbook.md` (retry with `--render`, try alternate URL, skip and
  log). Don't abort a batch for a single extraction failure.
- **Too few seed keywords** — if the user's topic is very narrow and only 5-10 seeds
  can be generated, proceed with fewer but note the limited scope. Suggest broadening
  the topic in follow-ups.
- **Search 500** — retry once without `--focus` flag. If persistent, simplify the query.
  Log the failure but continue with remaining keywords.

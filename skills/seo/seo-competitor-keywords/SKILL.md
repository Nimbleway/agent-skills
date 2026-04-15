---
name: seo-competitor-keywords
description: |
  Reverse-engineers competitor on-page SEO strategy. Maps competitor sites,
  bulk-crawls with JS rendering, then extracts title tags, H1s, meta
  descriptions, blog topics, anchor text patterns, and heading hierarchy at
  scale. Clusters findings into keyword themes and produces a comparison
  matrix across multiple competitors. Unlike prompt-template SEO skills,
  this one actually crawls the full site with `nimble map` + `nimble crawl`
  and extracts structured fields across hundreds of pages.

  Use when the user wants to understand what a competitor is targeting across
  their site, not just one page. Triggers: "competitor keywords",
  "reverse-engineer SEO", "competitor SEO strategy", "what keywords are they
  targeting", "competitor title tags", "competitor H1s", "on-page SEO
  analysis", "site-wide keyword analysis", "competitor blog topics", "anchor
  text analysis", "SEO teardown".

  Do NOT use for technical SEO audits — use `seo-site-audit`. Do NOT use for
  competitor business signals — use `competitor-intel`. Do NOT use for
  competitor messaging/positioning — use `competitor-positioning`. Do NOT
  use for SERP-based content gap analysis — use `seo-content-gap`.
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

# SEO Competitor Keywords

Reverse-engineer competitor on-page SEO strategy at scale — crawl entire sites, extract
structured SEO elements, cluster into keyword themes, and compare across domains.

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
- Profile exists → load prior snapshots from
  `~/.nimble/memory/seo/competitor-keywords/{domain}/` for each known competitor
  domain. If `snapshot-*.json` files exist, load the most recent per domain — these
  provide the baseline for delta detection in Step 10. Also check
  `~/.nimble/memory/reports/seo-competitor-keywords-*-*.md` for same-day runs. If a
  same-day report exists for the same domain set, ask: "Already ran today. Run again
  for fresh data?" Don't silently re-run.
- No profile → Step 1

### Step 1: First-Run Onboarding (2 prompts max)

Follow `references/profile-and-onboarding.md` for the full onboarding flow. If a
business profile already exists, skip this step entirely.

### Step 2: Shape Scope (2 prompts max)

If `$ARGUMENTS` already specifies competitor URLs or domains, use those and skip
to the depth prompt.

**Prompt 1** — ask in plain text (NOT AskUserQuestion with options):

> "Which competitor sites should I analyze? (1-3 URLs or domains, e.g.,
> widgetco.com, gizmotech.io)"

Accept natural language: "my main competitors", "the ones in my profile" → resolve
from `business-profile.json` competitor list.

**Prompt 2** — use AskUserQuestion:

> I'll analyze **{domains}**. A few quick questions:
> - **Scope:** Full site, or a specific section? (e.g., `/blog`, `/product`)
> - **Include your site for comparison?** (yes/no — adds {user-domain})
> - **Depth:**
>   - **Quick (50 pages)** per domain — key sections, ~2 min
>   - **Standard (200 pages)** per domain — broad coverage, ~5 min
>   - **Deep (500 pages)** per domain — maximum coverage, ~10 min

Parse: list of domains, optional section filter, whether to include user's domain,
and page cap per domain (50 / 200 / 500).

### Step 3: WSA Discovery

Search for relevant WSAs in parallel:

```bash
nimble agent list --search "seo" --limit 100
nimble agent list --search "keyword" --limit 100
```

From results, filter for agents relevant to SEO data extraction. Validate any
promising agents with `nimble agent get --template-name {name}` before using them.
Cache discovered agent names and parameters.

**Fall back to `nimble map` + `nimble extract` / `nimble crawl` if no useful WSAs
are found.** The skill works without WSAs — they are an optimization, not a
requirement.

### Step 4: Site Discovery

Run `nimble map` for each domain in parallel (one Bash call per domain):

```bash
nimble map --url "https://{domain}" --limit {page_cap * 2}
```

If a section filter was specified (e.g., `/blog`), also run:

```bash
nimble map --url "https://{domain}/{section}" --limit {page_cap}
```

From the returned URLs, classify each page into a section by path prefix:

| Section | Path patterns |
|---------|---------------|
| Homepage | `/`, `/index` |
| Product | `/product`, `/features`, `/platform`, `/solutions` |
| Pricing | `/pricing`, `/plans` |
| Blog | `/blog`, `/articles`, `/news`, `/resources` |
| Docs | `/docs`, `/documentation`, `/help`, `/support` |
| Customers | `/customers`, `/case-studies`, `/testimonials` |
| About | `/about`, `/team`, `/careers`, `/company` |
| Other | everything else |

Note blog velocity signal: count URLs under `/blog` that contain date-like path
segments (e.g., `/2026/03/`) — this hints at publishing cadence.

If `nimble map` returns fewer than 3 URLs for a domain, fall back to homepage plus
site-search discovery:

```bash
nimble search --query "site:{domain}" --max-results 20 --search-depth lite
```

Parse URLs from results to build the crawl list.

### Step 5: On-Page Extraction at Scale

Read `references/seo-extraction-prompt.md` for the full sub-agent prompt template.
Follow the sub-agent spawning rules from `references/nimble-playbook.md`
(bypassPermissions, batch max 4, explicit Bash instruction, fallback on failure).

**Call estimation:** ~1 map + N extractions per domain. For 2+ domains with 50+
pages each, this is a large job — use batch/crawl strategies per the tier below.

**Extraction strategy per domain (based on discovered page count):**

| Pages | Strategy | Implementation |
|-------|----------|----------------|
| < 50 | Sub-agent parallel extract | Spawn `nimble-researcher` agents (max 4), each extracts its assigned URLs with `nimble extract --url {url} --render --format markdown` |
| 50-500 | Batch or crawl | `nimble crawl run --url "https://{domain}" --limit {N} --include-path "{section}" --name "seo-keywords-{domain}-{YYYY-MM-DD}"` per domain; poll with `nimble crawl status --name "..."` |
| 500+ | Crawl with confirmation | Show estimate, confirm with user, then crawl |

Spawn one `nimble-researcher` agent per domain with `mode: "bypassPermissions"`.
Customize each agent's prompt from `references/seo-extraction-prompt.md` with:
- The domain and its discovered URL list
- Section scope (if filtered)
- Page cap
- Render flag (`--render` by default for SEO pages)
- Snapshot date for naming

Each agent extracts these fields per page:

| Field | Description |
|-------|-------------|
| `url` | Page URL |
| `title` | `<title>` tag content |
| `h1` | H1 element text |
| `meta_description` | Meta description content |
| `h2_outline` | List of H2 headings (max 10) |
| `h3_h6_outline` | List of H3-H6 headings (max 20) |
| `internal_anchors` | Anchor text for same-domain links from the **article body only** (max 50). Extract anchors only between the H1 heading and the first occurrence of "Related Posts", "Subscribe", "Newsletter", "Footer", or a second `---` rule. Skip nav/header/footer links entirely — they are boilerplate that pollutes hub-and-spoke detection. |
| `img_alt` | Image alt text values (max 30) |
| `word_count` | Body text word count |
| `section` | Inferred from URL path |
| `pub_date` | If visible in meta or structured data |

Agents return structured JSON per `references/seo-extraction-prompt.md`. No
analysis — just structured data.

**Fallback:** If an agent fails entirely, run its extractions directly from the
main context using the same strategy. Don't leave gaps.

### Step 6: Theme Analysis

Cluster extracted pages into keyword themes using noun-phrase patterns from
titles, H1s, and H2s:

1. **Extract candidate phrases** — collect all titles, H1s, and H2 values across
   all pages for each domain.
2. **Normalize** — lowercase, strip stop words, collapse whitespace.
3. **Filter boilerplate H2s before clustering.** Drop generic section headers
   that pollute theme labels: `conclusion`, `summary`, `introduction`, `overview`,
   `table of contents`, `faq`, `faqs`, `frequently asked questions`, `related posts`,
   `related articles`, `you might also be interested`, `what's next`, `next steps`,
   `about the author`, `references`, `citations`, `sources`, `further reading`,
   `tl;dr`, `get started`, `try it free`, `contact us`, `share this post`.
   These H2s appear across unrelated content and distort clustering.
4. **Cluster** — group pages sharing 2+ overlapping content words in their
   title + H1 + (filtered) H2 fields. Aim for 5-15 theme labels per domain.
4. **Label each theme** — derive a short keyword label from the most frequent
   noun phrases in the cluster (e.g., "API integration", "enterprise security",
   "pricing comparison").

For each theme, identify:
- **Primary keyword targets** — the 3-5 most repeated phrases across the cluster
- **Supporting pages** — all URLs in the cluster
- **Hub-and-spoke structure** — detect hub pages in three steps:
  1. **Body-only extraction:** Internal anchors must come from the article body
     (between H1 and footer markers), not the full page. See extraction rules in
     `references/seo-extraction-prompt.md`.
  2. **Filter boilerplate anchors:** Compute anchor frequency across ALL pages.
     Any anchor text appearing on > 80% of pages is navigation boilerplate (e.g.,
     "Features", "Pricing", "Blog", "Contact"). Strip these before hub detection.
  3. **Detect hubs with exact URL matching:** A page is a hub if its URL appears
     in the `internal_anchors` list of 3+ OTHER pages in the same theme. Use
     **exact URL equality** (after normalization: strip trailing slash, strip
     `#fragment`, strip tracking params). Do NOT use substring matching —
     substring matching produces false positives (e.g., `/blog` matches every
     `/blog/*` page).
- **Content hub URL** — the hub page URL if detected

### Step 7: Pattern Extraction

Analyze all 7 SEO element categories across extracted pages:

**Title Tags** — keyword frequency (top 20 terms), length distribution (avg/min/max),
truncation rate (% > 60 chars), format patterns: `"X | Brand"`, `"X: Y"`,
`"How to X"`, `"N Best X"`, `"X?"`, `"X - Y"`, Other.

**H1 Headlines** — H1-title alignment rate (% where H1 overlaps title), headline
tone (benefit / feature / question / how-to / listicle), top H1 keywords.

**Meta Descriptions** — CTA patterns ("Learn more", "Get started", "Try free"),
keyword inclusion rate, avg length, missing rate (% without meta description).

**Blog Topics** — theme map (Step 6 themes filtered to blog section), posting
velocity (posts/month from `pub_date` or URL dates), content type distribution
(how-to / listicle / comparison / case study / thought leadership / product update).

**Heading Hierarchy (H2-H6)** — subtopic depth (avg H2s/page, avg H3s/H2), common
H2 patterns per content type, heading keyword density.

**Internal Anchor Text** — keyword-rich anchor ratio (descriptive vs generic like
"click here"), hub-and-spoke detection (pages cited by 5+ others), top 10
most-linked-to pages.

**Image Alt Text** — keyword signals (top terms), coverage rate (% with non-empty
alt), keyword stuffing flags (alt > 125 chars or 5+ comma-separated keywords).

### Step 8: Cross-Competitor Comparison

Skip this step if only one domain was analyzed and the user's site was not
included.

Build a comparison matrix across all analyzed domains:

| Dimension | Domain A | Domain B | User's Site |
|-----------|----------|----------|-------------|
| **Theme coverage** | themes A targets | themes B targets | themes user targets |
| **Theme depth** (avg pages/theme) | N | N | N |
| **Title patterns** | dominant format | dominant format | dominant format |
| **Avg title length** | N chars | N chars | N chars |
| **H1-title alignment** | N% | N% | N% |
| **Heading depth** (avg H2/page) | N | N | N |
| **Anchor text style** | keyword-rich % | keyword-rich % | keyword-rich % |
| **Blog velocity** | N posts/month | N posts/month | N posts/month |
| **Meta description coverage** | N% | N% | N% |
| **Image alt coverage** | N% | N% | N% |

Highlight notable gaps: themes one competitor targets that others don't,
patterns that differ significantly, and areas where the user's site lags.

### Step 9: Save Snapshots & Report

Make all Write calls simultaneously:

- **Per-domain snapshot** → `~/.nimble/memory/seo/competitor-keywords/{domain}/snapshot-{YYYY-MM-DD}.json`

  Snapshot JSON structure:
  ```json
  {
    "domain": "example.com",
    "date": "2026-04-13",
    "page_count": 150,
    "themes": [
      {
        "label": "API integration",
        "keywords": ["api", "integration", "webhook"],
        "page_count": 12,
        "hub_url": "https://example.com/docs/api-guide"
      }
    ],
    "title_stats": {
      "avg_length": 52,
      "truncation_rate": 0.15,
      "top_keywords": ["api", "platform", "enterprise"],
      "dominant_pattern": "X | Brand"
    },
    "h1_stats": { "title_alignment_rate": 0.85, "dominant_tone": "how-to", "top_keywords": [...] },
    "heading_stats": { "avg_h2_per_page": 6.2, "avg_h3_per_h2": 1.8, "top_h2_keywords": [...] },
    "anchor_stats": { "keyword_rich_ratio": 0.72, "top_cited_pages": [...], "boilerplate_anchors_filtered": 12 },
    "meta_stats": { "coverage_rate": 0.85, "avg_length": 148 },
    "blog_stats": { "velocity": 8, "velocity_source": "url_dates", "content_type_distribution": {...} },
    "img_alt_stats": { "coverage_rate": 0.62, "top_keywords": [...] }
  }
  ```

- **Report** → `~/.nimble/memory/reports/seo-competitor-keywords-{domain-slug}-{YYYY-MM-DD}.md`
  (save the full report — this is the local source of truth). If multiple domains
  were analyzed together, use a combined slug (e.g., `widgetco-gizmotech`).

- **Profile** → update `last_runs.seo-competitor-keywords` in
  `~/.nimble/business-profile.json`

- Follow the wiki update pattern from `references/memory-and-distribution.md`:
  update `index.md` rows for affected directories, append a `log.md` entry for
  this run. Create `~/.nimble/memory/seo/competitor-keywords/{domain}/` directories
  if they don't exist.

### Step 10: Delta Mode

On re-run when prior snapshots exist (loaded in Step 0), diff new findings against
the most recent snapshot per domain. Surface only changes:

- **New theme emerging** — 3+ new pages under a theme that didn't exist or had
  fewer pages in the previous snapshot
- **Theme abandoned** — a previously active theme (5+ pages) with no new pages
  and no updates since last snapshot
- **Title pattern shift** — dominant title format changed (e.g., moved from
  `"X | Brand"` to `"How to X"` across 10+ pages)
- **Anchor text shift** — keyword-rich ratio changed by > 10 percentage points,
  or top-cited pages reshuffled significantly
- **Blog velocity change** — posting rate increased or decreased by > 30%
- **New section** — a new URL path section appeared (e.g., `/integrations/`)
  with 5+ pages

Format delta findings clearly with before/after values:

> **Theme shift:** "API integration" grew from 8 to 14 pages (+75%).
> New hub page: https://example.com/integrations/api-guide
>
> **Title pattern shift:** Moved from "X | Brand" (65%) to "How to X" (40%).
> 12 blog titles rewritten since last snapshot.

If no meaningful changes are detected, say so: "No significant on-page SEO
changes since {last_snapshot_date}."

### Step 11: Share & Distribute

**Always offer distribution — do not skip this step.** Follow
`references/memory-and-distribution.md` for connector detection, sharing flow,
and source links enforcement.

**Slack-specific:** Post TL;DR only — theme summary and top opportunities.
Not the full report.

### Step 12: Follow-ups

- **Go deeper** on a theme → extract all pages in that cluster, analyze keyword
  density and internal linking within the cluster
- **Compare with SERP data** → "Run `seo-content-gap` for SERP-level gaps"
- **Analyze competitor messaging** → "Run `competitor-positioning` for messaging"
- **Business context** → "Run `competitor-intel` for business signals"
- **Track changes over time** → "Re-run in 2-4 weeks for delta analysis"
- **"Looks good"** → done

**Sibling skill suggestions:**

> **Next steps:**
> - Run `seo-content-gap` to find SERP-level keyword gaps you can target
> - Run `competitor-positioning` to understand competitor messaging strategy
> - Run `competitor-intel` for business context (funding, hiring, launches)

---

## Output Format

```
# SEO Competitor Keywords: {Domain(s)} — {Date}

## TL;DR
Dominant keyword themes, notable patterns, biggest opportunities.
3-5 bullet points with specific numbers.

## Keyword Theme Map
| Theme | Pages | Primary Keywords | Hub Page | Coverage Depth |
|-------|-------|-----------------|----------|----------------|

(Per domain if multiple. 5-15 themes per domain.)

## Title Tag Analysis
- Dominant format: {pattern} ({N}% of pages)
- Top keywords: {list with counts}
- Avg length: {N} chars | Truncation rate: {N}%
- Notable patterns: {observations}

## H1 Headlines
- H1-title alignment: {N}%
- Dominant tone: {classification}
- Top H1 keywords: {list}

## Content Structure
- Hub pages: {list of detected hub URLs with inbound link counts}
- Blog velocity: ~{N} posts/month
- Topic clusters: {theme labels with page counts}
- Content types: {distribution}

## Anchor Text Patterns
- Keyword-rich ratio: {N}% (vs {N}% generic)
- Most-linked pages: {top 5-10 with link counts}
- Hub-and-spoke: {detected hub/spoke structures}

## Meta Description Patterns
- Coverage: {N}% of pages have meta descriptions
- Avg length: {N} chars
- CTA formulas: {common patterns with frequency}
- Keyword inclusion rate: {N}%

## Heading Hierarchy
- Avg H2s per page: {N} | Avg H3s per H2: {N}
- Common H2 patterns by content type:
  - Blog: {patterns}
  - Product: {patterns}
- Top heading keywords: {list}

## Image Alt Text
- Coverage: {N}% of images have alt text
- Top keywords: {list}
- Keyword stuffing flags: {count if any}

## Competitor Comparison Matrix
(If 2+ domains analyzed. Table from Step 8.)

## Delta Summary
(If prior snapshots exist. Changes only from Step 10.)

## What This Means
- Keyword opportunities: themes worth targeting or differentiating on
- Patterns worth adopting: title formats, anchor strategies, hub structures
- Gaps to exploit: themes competitors miss, thin coverage areas
- Quick wins: specific changes to make based on findings

## Next Steps
- Run `seo-content-gap` for SERP-level gaps between your content and competitors
- Run `competitor-positioning` for messaging and positioning analysis
- Run `competitor-intel` for business context (funding, hiring, launches)
```

---

## Error Handling

See `references/nimble-playbook.md` for the standard error table (missing API key,
429, 401, empty results, extraction garbage). Skill-specific errors:

- **Crawl task fails:** Retry with a smaller `--limit` (halve it). If still
  failing, fall back to sampled `nimble extract` calls for the top URLs from
  the map step. Record partial coverage in the report.
- **`nimble map` returns empty:** Fall back to homepage + site-search:
  `nimble search --query "site:{domain}" --max-results 20 --search-depth lite`.
  Parse URLs from results and use those as the crawl list.
- **Crawl task stuck:** Poll `nimble crawl status` every 30 seconds. After 10
  minutes with no progress, terminate and use partial results. Note incomplete
  coverage in the report.
- **Batch extraction timeout:** Fetch whatever results are available and continue
  analysis with partial data. Note affected pages.
- **Sub-agent returns empty:** Re-run that domain's extractions directly from
  the main context. Don't leave gaps in the analysis.
- **Too few pages for meaningful clustering:** If a domain returns < 10 pages,
  skip theme clustering and report raw element analysis only. Note: "Insufficient
  pages for theme analysis — {N} pages extracted."

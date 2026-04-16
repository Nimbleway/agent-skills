
# SEO Site Audit

Full-crawl technical and on-page SEO audit powered by Nimble's web data APIs.


---

## Instructions

### Step 0: Preflight

Run the preflight pattern from `references/nimble-playbook.md` (5 simultaneous Bash
calls: date calc, today, CLI check, profile load, index.md load).

From the results:
- CLI missing or API key unset → `references/profile-and-onboarding.md`, stop
- Profile exists → check for prior audit data at
  `~/.nimble/memory/seo/audits/{domain-slug}/`. If a `findings-*.json` file exists,
  load the most recent one — it provides the baseline for dedup in Step 9
  (only NEW or WORSENED findings go in the TL;DR). Also check
  `~/.nimble/memory/reports/seo-site-audit-{domain-slug}-*.md` for same-day runs.
  If a same-day report exists, ask: "Already ran today. Run again for fresh data?"
  Don't silently re-run.
- No profile → Step 1

### Step 1: First-Run Onboarding (2 prompts max)

Follow `references/profile-and-onboarding.md` for the full onboarding flow. If a
business profile already exists, skip this step entirely.

### Step 2: Scope Shaping (2 prompts max)

**Prompt 1** — ask in plain text (NOT AskUserQuestion with options):

> "What site should I audit? (URL or domain, e.g., acme.com or acme.com/blog)"

If `$ARGUMENTS` already contains a URL or domain, skip this prompt.

**Prompt 2** — confirm scope (use AskUserQuestion):

> I'll audit **{domain}**{" scoped to {path}" if path provided}.
> How thorough should the scan be?
> - **Quick (50 pages)** — homepage + key sections, ~2 min
> - **Standard (200 pages)** — cross-section of the site, ~5 min
> - **Comprehensive (500 pages)** — deep crawl, ~10 min

Also ask:
- "Any known issues or priorities I should focus on?" (free text, optional)
- "Is this a single-page app (React, Vue, Angular) or heavily JS-rendered?"
  (yes/no — determines starting render tier)

Parse the domain, optional path prefix, scan size (Quick/Standard/Comprehensive →
50/200/500), and SPA flag from the responses.

### Step 3: Site Discovery

Discover URLs on the target site using the map pattern in
`references/nimble-playbook.md` (Mapping section). Pass `--limit` equal to
roughly twice the chosen scan size and include the sitemap so orphan pages
are caught.

If a path prefix was specified (e.g., `/blog`), filter discovered URLs to
keep only those matching the prefix. Always keep the homepage regardless of
prefix. Store the discovered URL list for sampling in Step 4.

### Step 4: Sampling Strategy

If the site returned more URLs than the chosen scan size, select a representative
sample:

- **Always include:** homepage (prepend `https://{domain}/` if the map step did
  not return it), `/sitemap.xml` (check), `/robots.txt` (check)
- **Depth 1** (primary landing pages): all pages one click from homepage
- **Depth 2** (content cross-section): proportional selection across site sections
  (e.g., `/blog/`, `/products/`, `/docs/`)
- **Paginated pages:** at least one paginated URL per section (page-2, page-3)
- **Orphans:** a few URLs that appeared in the sitemap but not in the link graph

If the map step returned fewer URLs than the scan size, use all of them.

### Step 5: Execution Tier Selection

Choose the extraction strategy from `references/nimble-playbook.md` →
Scaled Execution based on the final sampled page count:

- **Small** sets: parallel individual extractions (JS-rendered).
- **Medium** sets: `extract-batch` with shared inputs.
- **Large** sets: async `crawl` with periodic status polling.

Scale thresholds, concurrency caps, batch-input syntax, and crawl-status
polling cadence all live in the shared playbook — do not restate them
inline. When the crawl tier is used, treat partial results as acceptable
and note the incomplete coverage in the report.

### Step 6: Render Tier and Extraction Mode

**Default extraction mode:** Two formats per page — markdown for content analysis,
HTML for head metadata parsing:

```bash
nimble extract --url "{url}" --format markdown   # body, headings, word count
nimble extract --url "{url}" --format html       # <head>: title, description, canonical, og, twitter, schema JSON-LD, hreflang, lang
```

Run both calls in parallel per page. Parse `data.markdown` for body-level fields
(h1, h2_outline, word_count, internal_link_count). Parse `data.html` with regex
or BeautifulSoup-style logic for head-level fields:
- `<title>` → title
- `<meta name="description" content="...">` → meta_description
- `<link rel="canonical" href="...">` → canonical
- `<meta property="og:*" content="...">` → og_title, og_description
- `<meta name="twitter:card" content="...">` → twitter_card
- `<script type="application/ld+json">...</script>` → schema_jsonld (parse JSON body)
- `<link rel="alternate" hreflang="...">` → has_hreflang
- `<html lang="...">` → lang_attr

**Render tier:** Start at the tier determined by the SPA flag from Step 2:

| Tier | Flags | When |
|------|-------|------|
| Tier 1 | `--format html` + `--format markdown` (no `--render`) | Default for static sites |
| Tier 2 | `--render --format html` + `--render --format markdown` | User indicated SPA, or Tier 1 returned empty head |
| Tier 3 | `--render --driver vx10-pro --format html` | Tier 2 still fails |

**Auto-escalation:** After the first batch, check the parsed HTML. If > 30% of
pages returned empty or < 100-char `<head>`, escalate to the next tier and re-extract.
If the user flagged SPA in Step 2, start at Tier 2.

**Alternative: parser mode.** For precise structured extraction, use
`--parse --parser '{schema}'` with the schema from `references/seo-audit-checks.md`
instead of HTML parsing. Use when the LLM parser is more reliable than regex for
the target site (e.g., heavily nested or dynamic markup).

### Step 7: Parallel Extraction via Sub-Agents

Read `references/audit-agent-prompt.md` for the full agent prompt template. Follow
the sub-agent spawning rules from `references/nimble-playbook.md`
(bypassPermissions, batch max 4, explicit Bash instruction, fallback on failure).

Split the sampled URLs into batches and spawn `nimble-researcher` agents
(`agents/nimble-researcher.md`) with `mode: "bypassPermissions"`. Customize each
agent's prompt with:
- Its batch of page URLs
- The current render tier
- The parser schema from `references/seo-audit-checks.md`
- The target domain

Each agent handles extraction for its batch — using `extract-batch` when the batch
contains 11+ URLs, or parallel `nimble extract` calls for smaller batches.

**Fallback:** If an agent fails or returns empty results, re-run its extractions
directly from the main context. Don't leave gaps.

### Step 8: Structured SEO Extraction

Each page extraction should capture these fields (via the parser schema defined in
`references/seo-audit-checks.md`):

- `title` — page `<title>` tag content
- `meta_description` — meta description content
- `canonical` — canonical URL
- `og_title`, `og_description`, `twitter_card` — social meta tags
- `h1` — list of all H1 elements
- `h2_h6_outline` — heading hierarchy outline
- `schema_jsonld` — list of JSON-LD `@type` values found
- `internal_link_count`, `external_link_count` — link counts
- `img_without_alt_count` — images missing alt text
- `word_count` — body text word count
- `content_to_html_ratio` — ratio of text content to total HTML size
- `has_hreflang` — boolean, hreflang tags present
- `lang_attr` — `<html lang="...">` attribute value
- `status_code` — HTTP response status
- `canonical_self_referential` — boolean, canonical points to same URL

For pages where the parser returns nulls for all fields, escalate the render tier
(Step 6) and retry. If still null after Tier 3, record the page as "extraction
failed" and continue.

### Step 9: Audit Analysis

Run checks across all 7 categories defined in `references/seo-audit-checks.md`:

1. **Meta Tags** — title, description, canonical, OG/Twitter
2. **Heading Structure** — H1 presence, duplicates, hierarchy gaps
3. **Schema Markup (JSON-LD)** — presence, required fields, deprecated types
4. **Internal Links** — orphans, broken links, redirect chains, excessive links
5. **Content Quality** — thin content, duplicates, missing alt text, low ratio
6. **Technical Foundations** — robots.txt, sitemap, HTTPS, URL structure
7. **Core Web Vitals (observational)** — large images, render-blocking, DOM depth

Each finding gets:
- **Severity:** Critical / High / Medium / Low
- **Category:** one of the 7 above
- **Page URL:** the affected page
- **Issue:** what was found
- **Recommendation:** specific, actionable fix

See `references/seo-audit-checks.md` for the full rule set, severity logic, and
escalation rules (e.g., widespread duplication affecting > 10% of pages bumps
severity by one level).

**Dedup against prior audit:** If a previous findings JSON exists (loaded in
Step 0), compare each finding's page URL + issue signature against it. Mark matches
as "unchanged" — only NEW or WORSENED findings appear in the TL;DR and Critical
Issues sections. Carryover findings appear in category breakdowns only.

### Step 10: Save & Update Memory

Make all Write calls simultaneously:

- **Report** → `~/.nimble/memory/reports/seo-site-audit-{domain-slug}-{YYYY-MM-DD}.md`
  (save the full audit report — this is the local source of truth)

- **Raw findings** → `~/.nimble/memory/seo/audits/{domain-slug}/findings-{YYYY-MM-DD}.json`
  (structured JSON of all findings — used for dedup in future runs)

- **Profile** → update `last_runs.seo-site-audit` in `~/.nimble/business-profile.json`

- Follow the wiki update pattern from `references/memory-and-distribution.md`: update
  `index.md` rows for affected directories, append a `log.md` entry for this run.
  Create `~/.nimble/memory/seo/` and `~/.nimble/memory/seo/audits/{domain-slug}/`
  directories if they don't exist.

### Step 11: Share & Distribute

**Always offer distribution — do not skip this step.** Follow
`references/memory-and-distribution.md` for connector detection, sharing flow, and
source links enforcement.

**Slack-specific:** Post critical issues only — not the full report. Format:

> SEO Audit: {domain} — {critical_count} critical issues found.
> Top issue: {description}. Full report saved locally.

### Step 12: Follow-ups

- **Fix a specific issue** → provide detailed implementation guidance
- **Re-audit a section** → run a Quick scan scoped to that path
- **Compare with previous audit** → load prior findings JSON and diff
- **"Looks good"** → done

**Sibling skill suggestions:**

> **Next steps:**
> - Run `seo-keyword-research` to find what keywords to optimize for
> - Run `seo-content-gap` to discover content opportunities versus competitors
> - Run `competitor-positioning` to see how competitors present themselves

---

## Audit Categories

Brief overview — full rules, severity logic, and parser schema live in
`references/seo-audit-checks.md`.

1. **Meta Tags** — title presence/length/uniqueness, meta description, canonical,
   OG and Twitter Card tags
2. **Heading Structure** — H1 presence and count, heading hierarchy (no gaps),
   empty headings
3. **Schema Markup (JSON-LD)** — JSON-LD presence on content pages, required fields
   per type, deprecated types
4. **Internal Links** — orphan pages, broken links (4xx/5xx), redirect chains,
   excessive links per page, link depth from homepage
5. **Content Quality** — thin content (< 300 words), duplicate content (shingle
   similarity > 0.9), images missing alt text, low content-to-HTML ratio
6. **Technical Foundations** — robots.txt accessibility, sitemap presence, HTTPS
   enforcement, URL hygiene (underscores, mixed case, session IDs)
7. **Core Web Vitals (observational)** — large unoptimized images (> 500KB without
   lazy loading), render-blocking resources, excessive DOM depth (> 32 levels)

---

## Output Format

```
# SEO Site Audit: {domain}
Date: {YYYY-MM-DD} | Pages audited: {N}/{total discovered} | Render tier: {1|2|3}

## TL;DR
Overall health: {A/B/C/D/F}. Top 3 critical issues. Biggest quick win.

## Critical Issues ({count})
| # | Page | Issue | Category | Recommendation |
|---|------|-------|----------|----------------|

## High Priority ({count})
| # | Page | Issue | Category | Recommendation |
|---|------|-------|----------|----------------|

## Medium Priority ({count})
| # | Page | Issue | Category | Recommendation |
|---|------|-------|----------|----------------|

## Low Priority ({count})
| # | Page | Issue | Category | Recommendation |
|---|------|-------|----------|----------------|

## Category Breakdown

### Meta Tags — {pass}/{total} pages pass
(breakdown per check: missing title, duplicate title, length out of range, etc.)

### Heading Structure — {pass}/{total} pages pass

### Schema Markup — {pass}/{total} pages pass

### Internal Links — {pass}/{total} pages pass

### Content Quality — {pass}/{total} pages pass

### Technical Foundations — {pass}/{total} checks pass

### Core Web Vitals (observational) — {pass}/{total} checks pass

## Site Structure Overview
Total pages discovered: {X}. Sections: {list}. Depth distribution.

## Quick Wins (< 2 hours each)
1. ...
2. ...
3. ...

## What This Means
Where to start, estimated effort, expected impact on search visibility.

Recommended follow-ups:
- Run `seo-keyword-research` to find optimization targets for pages that pass
  the audit
- Run `seo-content-gap` to discover content opportunities versus competitors
```

---

## Health Grade

Calculate the overall health grade from finding severity counts:

| Grade | Criteria |
|-------|----------|
| **A** | 0 Critical, ≤ 2 High, any Medium/Low |
| **B** | 0 Critical, 3–5 High |
| **C** | 1–2 Critical, or 6–10 High |
| **D** | 3–5 Critical, or > 10 High |
| **F** | > 5 Critical |

---

## Error Handling

See `references/nimble-playbook.md` for the standard error table (missing API key,
429, 401, empty results, extraction garbage). Skill-specific errors:

- **`nimble map` returns empty:** Fall back to homepage + site-search:
  `nimble search --query "site:{domain}" --max-results 20 --search-depth lite`.
  Parse URLs from results and use those as the crawl list.
- **Crawl task stuck:** Poll `nimble crawl status` every 30 seconds. After 10
  minutes with no progress, terminate the crawl and use whatever partial results
  are available. Note incomplete coverage in the report.
- **Parser returns nulls for all fields:** Escalate the render tier (Step 6). If
  already at Tier 3, record the page as "extraction failed" and continue with
  remaining pages. Don't abort the audit for individual page failures.
- **Batch extraction timeout:** If `nimble batches progress` shows no movement for
  5 minutes, fetch whatever results are available and continue analysis with
  partial data. Note affected pages in the report.

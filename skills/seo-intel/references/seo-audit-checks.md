# SEO Audit Checks

Detailed rules, severity logic, and parser schema for the seo-site-audit skill.

---

## Parser Schema

Use this JSON schema with `nimble extract --parse --parser '{...}'` to extract
structured SEO fields from each page. Pass this schema to sub-agents via the
`{parser_schema}` placeholder.

```json
{
  "title": "The content of the <title> tag",
  "meta_description": "The content attribute of <meta name='description'>",
  "canonical": "The href attribute of <link rel='canonical'>",
  "og_title": "The content attribute of <meta property='og:title'>",
  "og_description": "The content attribute of <meta property='og:description'>",
  "twitter_card": "The content attribute of <meta name='twitter:card'>",
  "h1": "A JSON array of all H1 element text contents on the page",
  "h2_h6_outline": "A hierarchical outline of H2-H6 headings as nested text",
  "schema_jsonld": "A JSON array of all @type values found in <script type='application/ld+json'> blocks",
  "internal_link_count": "Count of <a> links pointing to the same domain",
  "external_link_count": "Count of <a> links pointing to external domains",
  "img_without_alt_count": "Count of <img> tags missing the alt attribute or with empty alt",
  "word_count": "Total word count of visible body text (excluding nav, footer, scripts)",
  "has_hreflang": "true if any <link rel='alternate' hreflang='...'> tags exist, false otherwise",
  "lang_attr": "The value of the lang attribute on the <html> element",
  "canonical_self_referential": "true if the canonical URL matches the current page URL, false otherwise"
}
```

When the parser returns nulls for all fields on a page, escalate the render tier
and retry before recording the page as "extraction failed."

**Fields NOT available via the parser:**
- `status_code` — HTTP response status comes from the extract response metadata
  (the `status_code` field in the API response JSON), not from parsed page content.
  Read it from the response envelope, not the parser output.
- `content_to_html_ratio` — requires access to the raw HTML byte count, which the
  parser does not provide. Estimate it by comparing `word_count` (from parser) to
  the total response size (from response metadata). If response metadata lacks size,
  skip this check and note it as "not measurable."

---

## Category 1: Meta Tags

| # | Rule | Condition | Severity |
|---|------|-----------|----------|
| 1.1 | Missing title | `title` is null or empty | Critical |
| 1.2 | Duplicate title | Same `title` value on 2+ pages | High |
| 1.3 | Title too short | `title` length < 30 characters | Medium |
| 1.4 | Title too long | `title` length > 60 characters | Medium |
| 1.5 | Missing meta description | `meta_description` is null or empty | Medium |
| 1.6 | Duplicate meta description | Same `meta_description` on 3+ pages | High |
| 1.7 | Meta description too short | `meta_description` length < 70 characters | Low |
| 1.8 | Meta description too long | `meta_description` length > 160 characters | Low |
| 1.9 | Missing canonical | `canonical` is null or empty | Medium |
| 1.10 | Non-self-referential canonical | `canonical_self_referential` is false | Medium |
| 1.11 | Missing OG tags | `og_title` or `og_description` is null | Low |
| 1.12 | Missing Twitter Card | `twitter_card` is null or empty | Low |

**Recommendations:**
- 1.1: Add a unique, descriptive `<title>` tag to every page. Include primary keyword.
- 1.2: Write unique titles for each page reflecting its specific content.
- 1.3/1.4: Aim for 30–60 characters. Include primary keyword near the start.
- 1.5: Add a meta description summarizing page content in 70–160 characters.
- 1.6: Write unique descriptions. Shared descriptions signal thin content to search engines.
- 1.9/1.10: Add a self-referential canonical tag to prevent duplicate content issues.
- 1.11/1.12: Add OG and Twitter Card meta tags for better social sharing previews.

---

## Category 2: Heading Structure

| # | Rule | Condition | Severity |
|---|------|-----------|----------|
| 2.1 | Missing H1 | `h1` array is empty | Critical |
| 2.2 | Multiple H1s | `h1` array has 2+ elements | High |
| 2.3 | Hierarchy gap | H3 appears without a preceding H2, or H4 without H3, etc. (from `h2_h6_outline`) | Medium |
| 2.4 | Empty heading | Any heading in the outline has empty or whitespace-only text | Low |
| 2.5 | Duplicate H1 | Same H1 text on 2+ pages (excluding homepage) | Medium |

**Recommendations:**
- 2.1: Every page needs exactly one H1 describing the page's primary topic.
- 2.2: Use a single H1 per page. Use H2–H6 for subsections.
- 2.3: Maintain proper heading hierarchy. Don't skip from H1 to H3.
- 2.4: Remove empty heading tags or add meaningful text.
- 2.5: Write unique H1s reflecting each page's distinct content.

---

## Category 3: Schema Markup (JSON-LD)

| # | Rule | Condition | Severity |
|---|------|-----------|----------|
| 3.1 | No JSON-LD on content page | `schema_jsonld` is empty on a page with word_count > 300 | High |
| 3.2 | Missing required fields | JSON-LD `@type` present but lacks required properties for that type (Article needs headline + datePublished; Product needs name + offers; Organization needs name + url) | Medium |
| 3.3 | Deprecated @type | `schema_jsonld` contains deprecated types (e.g., `DataCatalog` for datasets) | Low |
| 3.4 | No Organization schema on homepage | Homepage `schema_jsonld` doesn't include `Organization` or `WebSite` | Medium |

**Recommendations:**
- 3.1: Add JSON-LD structured data matching the page content type (Article, Product,
  FAQ, etc.). This enables rich snippets in search results.
- 3.2: Fill in all required properties per schema.org type definitions.
- 3.3: Update to current schema.org types.
- 3.4: Add Organization and WebSite schema to the homepage for brand knowledge panel.

---

## Category 4: Internal Links

| # | Rule | Condition | Severity |
|---|------|-----------|----------|
| 4.1 | Orphan page | Page has 0 internal inlinks (discovered via sitemap but not linked from any crawled page) | Critical |
| 4.2 | Broken internal link | A linked internal URL returns `status_code` >= 400 | High |
| 4.3 | Redirect chain > 2 hops | Internal link resolves through 3+ redirects | High |
| 4.4 | Excessive internal links | A single page has `internal_link_count` > 100 | Medium |
| 4.5 | Deep link depth | Page is > 4 clicks from the homepage (measured via link graph) | Medium |
| 4.6 | No internal links | `internal_link_count` is 0 on a content page | High |

**Recommendations:**
- 4.1: Add internal links to orphan pages from relevant parent or hub pages.
- 4.2: Fix or remove broken internal links. Update href to the correct URL.
- 4.3: Update links to point directly to the final destination URL.
- 4.4: Reduce internal links on mega-navigation pages. Prioritize contextual links.
- 4.5: Flatten site architecture. Important pages should be reachable in 3 clicks.
- 4.6: Add contextual internal links to related content pages.

---

## Category 5: Content Quality

| # | Rule | Condition | Severity |
|---|------|-----------|----------|
| 5.1 | Thin content | `word_count` < 300 on an indexable page (not a redirect, not noindex) | High |
| 5.2 | Duplicate content | Jaccard or 4-gram shingle similarity > 0.9 between two pages | High |
| 5.3 | Images missing alt text | `img_without_alt_count` > 0 on a content page | Medium |
| 5.4 | Low content-to-HTML ratio | `content_to_html_ratio` < 0.10 | Low |
| 5.5 | Very thin content | `word_count` < 100 on an indexable page | Critical |

**Recommendations:**
- 5.1/5.5: Expand thin pages with substantive content or consolidate with related pages.
- 5.2: Merge duplicate pages, implement canonical tags, or differentiate content.
- 5.3: Add descriptive alt text to all content images for accessibility and image SEO.
- 5.4: Reduce template bloat. Simplify HTML structure and remove unnecessary markup.

**Duplicate detection approach:** For each pair of pages in the same site section,
compute 4-gram shingle sets from the body text and calculate Jaccard similarity.
Pairs exceeding 0.9 are flagged. For large page sets (> 100 pages), compare within
sections only to keep computation tractable.

---

## Category 6: Technical Foundations

| # | Rule | Condition | Severity |
|---|------|-----------|----------|
| 6.1 | robots.txt missing | Fetching `{domain}/robots.txt` returns 404 or empty | Critical |
| 6.2 | robots.txt blocks important paths | robots.txt disallows paths with high-value content (check for blanket `Disallow: /`) | Critical |
| 6.3 | Sitemap missing | No sitemap found at `/sitemap.xml` or referenced in robots.txt | Critical |
| 6.4 | Sitemap stale | Sitemap `<lastmod>` dates are > 90 days old | Medium |
| 6.5 | HTTPS not enforced | HTTP URLs don't redirect to HTTPS, or mixed content detected | Critical |
| 6.6 | Mixed content | Page loaded over HTTPS contains HTTP resources | High |
| 6.7 | URL uses underscores | URL path contains underscores instead of hyphens | Medium |
| 6.8 | URL mixed case | URL path contains uppercase characters | Medium |
| 6.9 | Session IDs in URLs | URL contains session-like parameters (`?sid=`, `?session=`, `?jsessionid=`) | Medium |
| 6.10 | Missing lang attribute | `lang_attr` is null or empty on the `<html>` element | Low |
| 6.11 | AI bots blocked | `robots.txt` disallows GPTBot, ClaudeBot, PerplexityBot, or ChatGPT-User — reduces AI visibility | Medium |
| 6.12 | No llms.txt | No `/llms.txt` file at site root — the emerging standard for AI agent discoverability | Low |

**Recommendations:**
- 6.1: Create a robots.txt file at the domain root.
- 6.2: Review Disallow rules. Ensure important content paths are crawlable.
- 6.3: Generate and submit an XML sitemap. Reference it in robots.txt.
- 6.4: Update sitemap `<lastmod>` dates to reflect actual content changes.
- 6.5: Enforce HTTPS site-wide via server redirects (301).
- 6.6: Update all resource references to use HTTPS or protocol-relative URLs.
- 6.7/6.8: Use lowercase hyphens in URLs. Set up 301 redirects from old URLs.
- 6.9: Remove session IDs from URLs. Use cookies for session tracking instead.
- 6.10: Add `lang="en"` (or appropriate language code) to the `<html>` element.
- 6.11: Allow AI bots in robots.txt unless there's a specific reason to block.
  Blocking GPTBot/ClaudeBot/PerplexityBot reduces visibility in AI-generated answers.
  See `references/ai-platform-profiles.md` for the full AI bot user-agent list.
- 6.12: Add an `/llms.txt` file describing your site structure and capabilities for
  AI agents. See llmstxt.org for the spec. Low priority but forward-looking.

---

## Category 7: Core Web Vitals (Observational)

These checks are inferred from page content — not measured with Lighthouse. They
flag likely CWV problems based on observable HTML patterns.

| # | Rule | Condition | Severity |
|---|------|-----------|----------|
| 7.1 | Large images without lazy loading | `<img>` with `src` pointing to an image likely > 500KB (based on URL patterns like high-res filenames) and no `loading="lazy"` attribute | Medium |
| 7.2 | Render-blocking resources | `<link rel="stylesheet">` or `<script>` in `<head>` without `async`/`defer` attributes | Medium |
| 7.3 | Excessive DOM depth | DOM nesting exceeds 32 levels (inferred from heading/div nesting in extracted HTML) | Low |
| 7.4 | No viewport meta tag | Missing `<meta name="viewport">` tag | Medium |

**Recommendations:**
- 7.1: Add `loading="lazy"` to below-the-fold images. Serve images in modern formats
  (WebP/AVIF) and use responsive `srcset`.
- 7.2: Add `async` or `defer` to non-critical scripts. Inline critical CSS.
- 7.3: Simplify DOM structure. Reduce unnecessary wrapper elements.
- 7.4: Add `<meta name="viewport" content="width=device-width, initial-scale=1">`.

---

## Finding Confidence Tiers

Every finding must be tagged with a confidence level based on how it was detected:

| Tier | Label | Meaning | When to assign |
|------|-------|---------|----------------|
| **Confirmed** | `[C]` | Measured by parser or script — deterministic | Parser returned the field; value was checked against a rule |
| **Likely** | `[L]` | Strong signal from markdown/content analysis | Inferred from markdown extraction (e.g., heading count, word count); no parser verification |
| **Hypothesis** | `[H]` | Possible issue, needs manual verification | Could not verify from available data (e.g., schema detected in markdown text but not validated, redirect chain inferred from URL patterns) |

Display in the report: `[C] Missing title tag on /about` vs `[H] Possible missing
JSON-LD — could not parse from markdown-only extraction`.

Rules by category (assuming extraction uses `--format html` + `--format markdown`
or `--parse --parser`):
- **Meta Tags (1.x):** **Confirmed** — all tags (title, meta description, canonical,
  og, twitter) parseable from `data.html` `<head>`. Hypothesis only if HTML
  extraction failed entirely (empty `<head>`).
- **Heading Structure (2.x):** Confirmed — parseable from both HTML and markdown.
- **Schema Markup (3.x):** **Confirmed** — `<script type="application/ld+json">`
  blocks parseable from `data.html`. Hypothesis only if HTML extraction failed.
- **Internal Links (4.x):** Likely — link counts from markdown are approximate
  (nav boilerplate inflates counts); Confirmed when using HTML body section.
- **Content Quality (5.x):** Confirmed for word count from markdown; Likely for
  duplicate detection (shingle analysis depends on clean text extraction).
- **Technical Foundations (6.x):** Confirmed for robots.txt/sitemap/llms.txt
  (directly fetched); **Confirmed** for lang_attr (from `<html lang>`) and
  hreflang; Hypothesis for HTTPS/mixed content enforcement (inferred from URLs).
- **Core Web Vitals (7.x):** Hypothesis — all CWV checks are observational estimates.

---

## Severity Escalation Rules

- **Widespread duplication:** If the same issue (same rule number) affects > 10% of
  audited pages, bump severity by one level (Low → Medium, Medium → High,
  High → Critical). Critical stays Critical.
- **Homepage penalty:** Issues found on the homepage are NOT auto-escalated — they
  carry the same base severity as any other page. The homepage is important, but the
  rule severity already reflects the issue's impact.
- **Combined impact:** If a page has 3+ distinct Critical/High issues, flag it as a
  "high-priority fix page" in the Quick Wins section.

---

## Dedup Against Prior Audit

When a prior `findings-{date}.json` exists for this domain:

1. **Build a signature** for each finding: `{page_url}|{rule_number}` (e.g.,
   `https://acme.com/blog|1.1`)
2. **Compare** each new finding's signature against the prior findings
3. **Classify:**
   - Signature exists in prior AND severity is the same → **Unchanged**
   - Signature exists in prior AND severity is worse → **Worsened**
   - Signature does NOT exist in prior → **New**
   - Prior signature does NOT exist in current → **Resolved**

**Report placement:**
- **New** and **Worsened** findings → TL;DR, Critical/High/Medium/Low issue tables
- **Unchanged** findings → Category Breakdown sections only (with "unchanged" tag)
- **Resolved** findings → noted as improvements in the TL;DR ("3 issues resolved
  since last audit")

This keeps the executive summary focused on what changed while preserving the full
picture in category breakdowns.

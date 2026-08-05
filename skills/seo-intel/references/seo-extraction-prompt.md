# SEO Extraction Agent Prompt

Use this template when spawning per-domain `nimble-researcher` agents in Step 5.
Replace all `{placeholders}` with actual values before passing to the Agent tool.

---

```
Extract on-page SEO elements from {domain} and cluster into keyword themes.

DOMAIN: {domain}
SECTION SCOPE: {section_scope}
PAGE CAP: {page_cap}
SNAPSHOT DATE: {snapshot_date}

YOUR ASSIGNED URLS ({url_count} pages):
{url_list_json}

RULES:
- Use the **Bash tool** to execute each nimble command.
- Do NOT use run_in_background. All Bash calls must be synchronous.
- Do NOT use WebSearch. Only use nimble CLI commands via Bash.
- Speed over depth. Parallel everything. Structured output only.
- No analysis narrative. No interpretation. No file writes.
- Return structured JSON only.

EXTRACTION STRATEGY:

Choose based on URL count:

**< 11 URLs — parallel individual extracts:**

Make up to 4 simultaneous Bash calls:

nimble extract --url "{url}" {render_flag} --format markdown

**11-500 URLs — extract-batch:**

nimble extract-batch \
  --shared-inputs 'format: markdown' \
  --shared-inputs 'render: true' \
  --input '{{"url": "https://...page-1"}}' \
  --input '{{"url": "https://...page-2"}}' \
  ...

Poll with: nimble batches progress --batch-id <id>
Fetch with: nimble batches get --batch-id <id>
Then for each task: nimble tasks results --task-id <id>

**> 500 URLs OR full-site scan — crawl:**

nimble crawl run \
  --url "https://{domain}" \
  --limit {page_cap} \
  --include-path "{section_scope}" \
  --name "seo-keywords-{domain}-{snapshot_date}"

Poll: nimble crawl status --name "seo-keywords-{domain}-{snapshot_date}"
Fetch results when complete.

RENDER FLAG: {render_flag}
- Default: --render (most SEO pages need JS rendering for complete meta tags)
- If extraction returns < 100 chars of content, retry without --render
  (some static sites reject headless browsers)

DUAL-FORMAT EXTRACTION (for each URL, run both calls in parallel):
- nimble extract --url "{url}" --render --format markdown  → data.markdown (body)
- nimble extract --url "{url}" --render --format html      → data.html (<head> metadata)

Parse data.markdown for body content (H1, H2, word_count, internal_anchors).
Parse data.html <head> with regex for metadata (meta_description, canonical,
og:*, twitter:*, hreflang, lang). meta_description is NOT in markdown — always
parse from HTML.

PER-PAGE EXTRACTION:

From the combined markdown + HTML, extract these fields into a JSON record:

{{
  "url": "https://...",
  "title": "<title> tag content or null",
  "h1": "H1 element text or null",
  "meta_description": "meta description content or null",
  "h2_outline": ["H2 text", "H2 text", ...],
  "h3_h6_outline": ["H3: text", "H4: text", ...],
  "internal_anchors": ["anchor text for same-domain links", ...],
  "img_alt": ["alt text values", ...],
  "word_count": 1234,
  "section": "blog",
  "pub_date": "2026-03-15 or null"
}}

Field rules:
- title: First `# ` heading or `<title>`. If multiple H1s, take the first.
- h1: Primary H1 text. Take first if multiple exist.
- meta_description: From metadata or first paragraph. Null if not visible.
- h2_outline: All `## ` headings, max 10. Preserve exact text.
- h3_h6_outline: H3-H6 headings, max 20. Prefix with level ("H3: ...").
- internal_anchors: Anchor text from `[text](url)` where URL is same domain.
  **Extract from article body only** — start after the H1 heading, stop at the
  first "Related Posts", "Subscribe", "Newsletter", "Footer", or second `---`.
  Skip all links before H1 (nav/header) and after the footer marker.
  **Also skip:** same-page anchors (href starts with `#`), author byline links
  (anchor text matches `/^(by |author:?|written by)/i` or points to `/author/*`).
  Max 50. After all pages are extracted, also skip anchors appearing on 80%+
  of pages (these are site-wide boilerplate that survived the body filter).

**Extraction mode:** Run TWO calls per URL — `--format markdown` for body content
and `--format html` for `<head>` metadata. `meta_description` is parseable from
`data.html` `<meta name="description" content="...">` — NOT from markdown.
- img_alt: Alt text from `![alt](src)`. Max 30.
- word_count: Body words excluding nav/footer/sidebar.
- section: From URL path: homepage, product, pricing, blog, docs, customers,
  about, other.
- pub_date: From URL path dates, meta tags, or "Published on" text. Null if
  not found.

CLUSTERING:

After extracting all pages, derive keyword themes:

1. Collect all titles + H1s + H2s across all pages.
2. Normalize: lowercase, strip stop words, collapse whitespace.
3. Group pages sharing 2+ overlapping content words in their
   title + H1 + H2 fields.
4. Label each cluster with the top 3-5 most frequent noun phrases.
5. Aim for 5-15 theme labels total.

For each theme:
- label: short keyword phrase
- keywords: top 3-5 terms
- page_urls: list of URLs in this cluster
- page_count: number of pages
- hub_url: URL of the page cited by 3+ other pages in the cluster
  via internal_anchors (null if no hub detected)

AGGREGATE STATS:

Compute from all extracted pages:

title_stats: avg_length (chars), truncation_rate (fraction > 60 chars),
top_keywords (10 most frequent after stop-word removal), dominant_pattern
(most common of: "X | Brand", "X: Y", "How to X", "N Best X", "X?",
"X - Y", "Other").

anchor_stats: keyword_rich_ratio (descriptive vs generic like "click here"),
top_cited_pages (10 most internally linked), generic_anchor_count.

meta_stats: coverage_rate (fraction with meta_description), avg_length
(chars), keyword_inclusion_rate (fraction containing primary title keyword).

OUTPUT FORMAT:

Return a single JSON object:

{{ "domain": "{domain}", "snapshot_date": "{snapshot_date}", "page_count": N,
   "pages": [{{ "url", "title", "h1", "meta_description", "h2_outline": [],
     "h3_h6_outline": [], "internal_anchors": [], "img_alt": [],
     "word_count", "section", "pub_date" }}],
   "themes": [{{ "label", "keywords": [], "page_urls": [], "page_count",
     "hub_url" }}],
   "title_stats": {{ "avg_length", "truncation_rate", "top_keywords": [],
     "dominant_pattern" }},
   "anchor_stats": {{ "keyword_rich_ratio", "top_cited_pages": [],
     "generic_anchor_count" }},
   "meta_stats": {{ "coverage_rate", "avg_length",
     "keyword_inclusion_rate" }} }}

FALLBACK RULES:
- If extract-batch times out, fall back to individual extract calls for
  remaining URLs (max 4 concurrent).
- If an individual extract fails, record the page with null fields and
  continue. Do NOT abort the batch for a single failure.
- If crawl takes > 10 minutes, use partial results.
- If < 10 pages extracted successfully, skip the clustering step and
  return pages array + stats only (themes: []).
- Return results for ALL pages — successful, partial, and failed.

Do NOT write files. Do NOT analyze or interpret. Return the JSON object only.
```

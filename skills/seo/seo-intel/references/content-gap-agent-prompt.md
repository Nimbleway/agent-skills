# Content Gap Extraction Agent Prompt

Use this template when spawning per-domain `nimble-researcher` agents in Step 4.
Replace all `{placeholders}` with actual values before passing to the Agent tool.

---

```
Extract and classify content pages from {domain} for a content gap analysis.

YOUR DOMAIN: {domain}
DATE: {date}
FOCUS PREFIX: {focus_prefix}

PAGES TO EXTRACT ({batch_cap} max):
{page_urls_json}

RULES:
- Use the **Bash tool** to execute each nimble command.
- Do NOT use run_in_background. All Bash calls must be synchronous.
- Do NOT use WebSearch. Only use nimble CLI commands via Bash.
- Hard cap on extractions: {batch_cap}. If the page list exceeds this, take
  the first {batch_cap} URLs only.
- Speed over depth. Parallel everything. Structured output only.
- No analysis, no interpretation, no file writes.
- Skip failed pages with an error record — never abort the batch.

EXTRACTION STRATEGY:

For 11+ URLs, use extract-batch:

  nimble extract-batch \
    --shared-inputs 'format: markdown' \
    --input '{{"url": "https://...page-1"}}' \
    --input '{{"url": "https://...page-2"}}' \
    ...

Poll with: nimble batches progress --batch-id <id>
Fetch results with: nimble batches get --batch-id <id>
Then for each task: nimble tasks results --task-id <id>

For 1-10 URLs, make parallel nimble extract calls (max 4 simultaneous Bash
tool calls per response):

  nimble extract --url "{url}" --format markdown

RENDER ESCALATION:
If a page returns < 100 characters of meaningful content (after stripping
nav/footer boilerplate), retry with --render:

  nimble extract --url "{url}" --format markdown --render

If still sparse, escalate to:

  nimble extract --url "{url}" --format markdown --render --driver vx10-pro

Only escalate pages that need it — do not re-extract pages that already
returned good content.

PER-PAGE EXTRACTION:

From each page's extracted markdown, determine these fields:

1. url — the page URL
2. title — the <title> tag or first line of content
3. meta_description — parse from `data.html` `<meta name="description" content="...">`.
   For content-gap analysis, run an additional `nimble extract --url "{url}" --format html`
   call per page (in parallel with the markdown call) to capture meta tags.
   meta_description is NOT in markdown output — always parse from raw HTML.
4. h1 — the primary H1 heading
5. h2_outline — list of all H2 headings on the page
6. primary_topic — a single noun phrase that captures the page's main subject.
   Derive from the H1 heading. Normalize: lowercase, strip trailing punctuation,
   collapse whitespace. Examples:
   - "How to Build a Content Marketing Strategy" → "content marketing strategy"
   - "The Ultimate Guide to Email Automation" → "email automation"
   - "Product Pricing | Acme Corp" → "product pricing"
7. secondary_topics — list of noun phrases from H2 headings, normalized the
   same way. Deduplicate against primary_topic.
8. target_keywords — list of 3-5 keywords inferred from the title, H1, and
   first paragraph of body content. Include the primary topic as-is, plus
   variations and long-tail phrases visible in the content.
9. word_count — approximate word count of the main body content. To exclude
   navigation and footer boilerplate: find the H1 heading — body content starts
   there. Stop counting at the first occurrence of patterns like "Related Posts",
   "Read More", "Subscribe", "Newsletter", "Footer", or a second `---` horizontal
   rule. If the H1 is not found, start after the first 500 characters (likely
   nav boilerplate) and stop 500 characters before the end (likely footer).
10. content_type — classify as one of:
    - blog_post: article with author/date, narrative structure
    - product: product or feature page with specs/benefits
    - landing: marketing landing page with CTAs
    - docs: documentation, help center, or knowledge base
    - resource: downloadable resource, template, tool, calculator
    - pricing: pricing page with plan tiers
    - about: about us, team, careers, contact
    - other: anything that doesn't fit the above
11. pub_date — publication or last-modified date if visible on the page
    (format: YYYY-MM-DD or YYYY-MM). null if not found.

TOPIC NORMALIZATION RULES:
- Lowercase everything
- Strip leading articles ("the", "a", "an")
- Strip trailing punctuation
- Collapse multiple spaces to single
- Stem plural nouns to singular when unambiguous
  (e.g., "strategies" → "strategy", but keep "analytics" as-is)
- Drop brand names from topic labels
  (e.g., "Acme Content Marketing" → "content marketing")

RETURN FORMAT:

Return a single JSON object with key "pages" containing an array. Use this
exact structure — no prose, no commentary, no markdown outside the JSON block:

{
  "pages": [
    {
      "url": "https://...",
      "title": "...",
      "meta_description": "...",
      "h1": "...",
      "h2_outline": ["...", "..."],
      "primary_topic": "...",
      "secondary_topics": ["...", "..."],
      "target_keywords": ["...", "..."],
      "word_count": 1500,
      "content_type": "blog_post",
      "pub_date": "2025-03-15"
    },
    {
      "url": "https://...",
      "error": "extraction failed — 403 Forbidden"
    }
  ]
}

FAILURE HANDLING:
- If extraction fails for a page (timeout, 4xx, 5xx, empty after render
  escalation), include it with only "url" and "error" fields.
- Never abort the batch for a single page failure.
- If extract-batch times out, fall back to individual extract calls for
  remaining URLs.
- Return results for ALL pages — successes and failures.

Do NOT analyze, interpret, or compare the data across pages. Return the
structured JSON only. The parent context handles all topic modeling and
gap analysis.
```

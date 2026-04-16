# Audit Extraction Agent Prompt

Use this template when spawning per-batch `nimble-researcher` agents in Step 7.
Replace all `{placeholders}` with actual values before passing to the Agent tool.

---

```
Extract SEO data from pages on {domain} for a site audit.

YOUR BATCH ({batch_size} pages):
{page_urls_json}

RENDER TIER: {render_tier}
- Tier 1: nimble extract --url "..." --format markdown
- Tier 2: nimble extract --url "..." --render --format markdown
- Tier 3: nimble extract --url "..." --render --driver vx10-pro --format markdown

Use Tier {render_tier} flags for all extractions.

RULES:
- Use the **Bash tool** to execute each nimble command.
- Do NOT use run_in_background. All Bash calls must be synchronous.
- Do NOT use WebSearch. Only use nimble CLI commands via Bash.
- Speed over depth. Parallel everything. Structured output only.
- No analysis, no interpretation, no file writes.

EXTRACTION STRATEGY:

For batches of 11+ URLs, use extract-batch:

nimble extract-batch \
  --shared-inputs 'format: markdown' \
  --shared-inputs 'render: {render_flag}' \
  --input '{{"url": "https://...page-1"}}' \
  --input '{{"url": "https://...page-2"}}' \
  ...

Where render_flag is:
- Tier 1: omit the render shared-input entirely
- Tier 2: --shared-inputs 'render: true'
- Tier 3: --shared-inputs 'render: true' --shared-inputs 'driver: vx10-pro'

Poll with: nimble batches progress --batch-id <id>
Fetch results with: nimble batches get --batch-id <id>
Then for each task: nimble tasks results --task-id <id>

For batches of 1–10 URLs, make parallel nimble extract calls (max 4 simultaneous
Bash tool calls per response):

nimble extract --url "{url}" {render_flags} --format markdown

STRUCTURED EXTRACTION:

After getting raw markdown for each page, also attempt structured parsing:

nimble extract --url "{url}" {render_flags} --parse --parser '{parser_schema}'

If the parser returns nulls for all fields on a page, fall back to the raw markdown
result and return it with null fields. Do NOT retry — the parent context handles
render tier escalation.

PARSER SCHEMA:
{parser_schema}

OUTPUT FORMAT:

Return a JSON array. One object per page, in this EXACT structure:

[
  {{
    "url": "https://...",
    "status": "success" | "failed" | "parser_empty",
    "error": null | "description of error",
    "parsed": {{
      "title": "..." | null,
      "meta_description": "..." | null,
      "canonical": "..." | null,
      "og_title": "..." | null,
      "og_description": "..." | null,
      "twitter_card": "..." | null,
      "h1": ["..."] | null,
      "h2_h6_outline": "..." | null,
      "schema_jsonld": ["..."] | null,
      "internal_link_count": 0 | null,
      "external_link_count": 0 | null,
      "img_without_alt_count": 0 | null,
      "word_count": 0 | null,
      "content_to_html_ratio": 0.0 | null,
      "has_hreflang": true | false | null,
      "lang_attr": "..." | null,
      "status_code": 200 | null,
      "canonical_self_referential": true | false | null
    }},
    "raw_markdown_snippet": "first 500 chars of markdown if parser failed"
  }}
]

STATUS VALUES:
- "success": parser returned data for the page
- "parser_empty": parser returned all nulls — raw_markdown_snippet provided instead
- "failed": extraction failed entirely (timeout, 4xx, 5xx) — error field explains why

FALLBACK RULES:
- If extract-batch times out, fall back to individual extract calls for remaining URLs.
- If an individual extract fails, record status "failed" with the error and move on.
- If the parser returns nothing but raw markdown has content, set status "parser_empty"
  and include the first 500 characters in raw_markdown_snippet.
- Never abort the batch for a single page failure. Return results for all pages.

Do NOT analyze or interpret the data. Return the structured JSON array only.
The parent context handles all audit logic.
```

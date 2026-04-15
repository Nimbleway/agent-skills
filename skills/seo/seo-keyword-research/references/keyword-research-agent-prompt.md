# Keyword Research Agent Prompt

Use this template when spawning per-keyword-cluster `nimble-researcher` agents in Step 5.
Replace all `{placeholders}` with actual values before passing to the Agent tool.

---

```
Extract and analyze the top ranking pages for the keyword cluster "{cluster_name}".

ASSIGNED KEYWORDS:
{keywords}

TOP URLS TO EXTRACT:
{top_urls}

RULES:
- Use the **Bash tool** to execute each nimble command.
- Do NOT use run_in_background. All Bash calls must be synchronous.
- Max 10 Bash tool calls total. Prioritize extraction over search.
- For 5+ URLs, use extract-batch instead of individual extract calls.

EXTRACTION:
For each URL above, extract the full rendered page:

  nimble extract --url "{url}" --format markdown --render

If extraction fails (empty, garbage, or error), retry once without --render.
If still failing, skip and log the URL. Do not abort the batch.

For 5+ URLs, batch them:

  nimble extract-batch \
    --shared-inputs 'format: markdown' --shared-inputs 'render: true' \
    --input '{"url": "{url1}"}' \
    --input '{"url": "{url2}"}' \
    ...

Poll with nimble batches progress --batch-id {id}, then fetch individual results
with nimble tasks results --task-id {id}.

ANALYSIS PER URL:
From the extracted markdown, determine:
1. Word count (of main content, excluding nav/footer)
2. Heading structure — list all H1, H2, H3 headings
3. Topic coverage — what subtopics does the page cover?
4. Content type — blog post, listicle, comparison, tool page, product page,
   landing page, guide, video transcript, other
5. Domain authority signals — brand recognition (Fortune 500? niche startup?),
   site age indicators, breadth of content on the topic
6. SERP features — did this URL hold a featured snippet, PAA, or other special
   placement? (from the SERP data if available)

RETURN FORMAT:
Return structured findings for each URL. Use this exact format — no prose, no
commentary, no interpretation:

URL: {url}
KEYWORD: {keyword}
DOMAIN: {domain}
CONTENT_TYPE: [blog|listicle|comparison|tool|product|landing|guide|video|other]
WORD_COUNT: [number]
HEADINGS:
  - H1: [heading text]
  - H2: [heading text]
  - H2: [heading text]
    - H3: [heading text]
  ...
TOPICS_COVERED:
  - [subtopic 1]
  - [subtopic 2]
  - [subtopic 3]
  ...
AUTHORITY_SIGNALS:
  - [signal 1 — e.g., "Major brand (HubSpot)", "Niche blog, no brand recognition"]
  - [signal 2 — e.g., "Deep topical coverage (50+ pages on topic)"]
  ...
SERP_FEATURES: [featured_snippet|paa|knowledge_panel|video|none]
EXTRACTION_STATUS: [success|partial|failed]
---

After all URLs are processed, add a cluster summary:

CLUSTER_SUMMARY: {cluster_name}
URLS_EXTRACTED: [N of N]
AVG_WORD_COUNT: [number]
DOMINANT_CONTENT_TYPE: [type]
COMMON_TOPICS: [topics that appear across 2+ pages]
MISSING_TOPICS: [topics covered by only 1 page or none — these are content gaps]
DIFFICULTY_SIGNAL: [Low|Medium|High|Very High — based on authority and depth observed]
---
```

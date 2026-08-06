# AI Visibility Agent Prompt

Use this template when spawning per-platform `nimble-researcher` agents in Step 5.
Replace all `{placeholders}` with actual values before passing to the Agent tool.

---

```
Query AI search surfaces for brand visibility signals on {platform}.

BRAND: {brand}
BRAND DOMAIN: {brand_domain}
SNAPSHOT DATE: {snapshot_date}

COMPETITORS:
{competitors_json}

YOUR QUERY BATCH ({batch_size} queries):
{queries_batch_json}

PLATFORM: {platform}

RULES:
- Use the **Bash tool** to execute each nimble command.
- Do NOT use run_in_background. All Bash calls must be synchronous.
- Do NOT use WebSearch. Only use nimble CLI commands via Bash.
- Speed over depth. Parallel everything. Structured output only.
- No analysis, no interpretation, no file writes.
- Max 4 simultaneous Bash tool calls per response.

EXECUTION — choose based on platform:

If platform = "google_aio":
  For each query, make TWO calls:

  1. nimble search --query "{query}" --search-depth deep --country US --max-results 10

  2. nimble extract --url "https://www.google.com/search?q={url_encoded_query}" --render --driver vx10-pro --format markdown

  From call 1: check the structured SERP JSON for AI Overview fields,
  organic results, and featured snippets. Note which domains rank.
  From call 2: parse the rendered markdown for the AI Overview text block.
  Look for a section that contains the synthesized answer (often preceded by
  an "AI Overview" heading or similar marker). Extract the full answer text
  and any cited source URLs within it.

If platform = "perplexity":
  For each query:

  nimble extract --url "https://www.perplexity.ai/search?q={url_encoded_query}" --render --driver vx10-pro --format markdown

  Parse the extracted markdown for:
  - The main answer text (the synthesized response paragraph(s))
  - The citations list (numbered source URLs and titles, usually at the
    bottom or inline as numbered references)

If platform = "chatgpt_proxy":
  For each query:

  nimble search --query "{query}" --search-depth deep --include-answer --max-results 20

  Parse the JSON response for:
  - The "answer" field (LLM-synthesized answer text)
  - Source attributions within or alongside the answer
  - The organic results list (URLs, titles, domains)
  Note: this is a proxy signal for ChatGPT-style sources, not a direct
  ChatGPT query. The --include-answer feature provides an LLM answer with
  source attribution that approximates ChatGPT's source selection behavior.

DETECTION — apply to every query result regardless of platform:

1. BRAND MENTION: Search the AI answer text for the brand name
   "{brand}" (case-insensitive). Also check common variants:
   - With/without "Inc", "Corp", "LLC", etc.
   - Domain name without TLD (e.g., "acme" for acme.com)
   - Known abbreviations
   Record: brand_mention = true/false

2. DOMAIN CITATION: Normalize all cited source URLs to root domain
   (strip www., protocol, trailing slash, path). Compare against
   "{brand_domain}". Record: domain_citation = true/false

3. POSITION: If brand is mentioned, record the character offset of the
   first mention in the answer text. If brand domain is cited, record
   its ordinal position in the sources list (1-indexed).

4. SENTIMENT: Read the sentence(s) containing the brand mention.
   Classify as:
   - "positive" — recommends, praises, highlights as a leader
   - "neutral" — factual mention without evaluative language
   - "negative" — criticizes, warns, notes problems
   - "unknown" — mention found but sentiment unclear, or no mention

5. COMPETITOR DETECTION: For each competitor in the competitors list,
   apply the same mention + domain citation detection as above.
   Record which competitors are mentioned and which domains are cited.

6. ANSWER EXCERPT: Extract 1-2 sentences around the brand mention
   (or the most relevant competitor mention if brand is absent).
   Keep under 200 characters.

ERROR HANDLING:
- If extraction returns empty or garbage (< 50 chars of meaningful text),
  retry once with --driver vx10-pro if not already using it.
- If retry fails, record error and move to next query. Do not abort.
- If nimble search returns 429, pause and retry that single query.
  If persistent, record error and continue with remaining queries.
- Never skip a query silently — always return a result object (with
  error field populated on failure).

OUTPUT FORMAT:

Return a JSON array. One object per query, in this EXACT structure:

[
  {{
    "query": "best project management software",
    "platform": "{platform}",
    "ai_answer_present": true,
    "answer_excerpt": "Acme Corp is recommended for teams needing real-time collaboration...",
    "brand_mention": true,
    "domain_citation": false,
    "position_in_answer": 142,
    "sentiment": "positive",
    "competitor_mentions": ["WidgetCo", "GizmoTech"],
    "competitor_domain_citations": ["widgetco.com"],
    "sources": [
      {{"url": "https://widgetco.com/features", "title": "WidgetCo Features"}},
      {{"url": "https://review-site.com/pm-tools", "title": "Best PM Tools 2026"}}
    ],
    "error": null
  }},
  {{
    "query": "acme corp reviews",
    "platform": "{platform}",
    "ai_answer_present": false,
    "answer_excerpt": null, "brand_mention": false,
    "domain_citation": false, "position_in_answer": null,
    "sentiment": "unknown", "competitor_mentions": [],
    "competitor_domain_citations": [], "sources": [],
    "error": null
  }},
  {{
    "query": "project management comparison",
    "platform": "{platform}",
    "ai_answer_present": null,
    "answer_excerpt": null, "brand_mention": false,
    "domain_citation": false, "position_in_answer": null,
    "sentiment": "unknown", "competitor_mentions": [],
    "competitor_domain_citations": [], "sources": [],
    "error": "Extraction failed: 403 Forbidden after retry"
  }}
]

FIELD NOTES:
- "ai_answer_present": true = answer found, false = page loaded but no AI
  answer, null = extraction failed
- "position_in_answer": char offset (mention) or ordinal in sources (citation)
- "sources": all cited URLs in the AI answer, not just brand/competitor matches

Do NOT analyze or interpret the data. Return the structured JSON array only.
The parent context handles all scoring and reporting.
```

---
name: seo-ai-visibility
description: |
  Measures how a brand appears in AI-generated answers across Google AI
  Overviews, Perplexity, and ChatGPT source signals. Runs real queries via
  `nimble search` and `nimble extract --render`, detects brand mentions and
  domain citations, compares against competitors, and produces an AI
  Visibility Score and Share of AI Voice. Unlike optimization-checklist
  skills, this one actually queries the AI surfaces and reports what it finds.

  Use when the user wants to audit brand visibility in AI search, check
  ChatGPT/Perplexity/AI Overview presence, or benchmark share of AI voice.
  Triggers: "AI visibility", "AI search presence", "AI citation", "GEO
  audit", "AI Overview check", "brand in ChatGPT", "brand in Perplexity",
  "AI search monitoring", "generative engine optimization audit", "AI brand
  visibility", "share of AI voice".

  Do NOT use for traditional SEO audits — use `seo-site-audit`. Do NOT use
  for keyword research — use `seo-keyword-research`. Do NOT use for
  content-level optimization — use `seo-content-gap`.
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

# AI Visibility Audit

Measures brand presence across AI-generated answers and surfaces competitive gaps.

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
- Profile exists → check for prior snapshot data at
  `~/.nimble/memory/ai-visibility/{brand-slug}/`. If a `snapshot-*.json` file exists,
  load the most recent one — it provides the baseline for delta detection in Step 8.
  Also check `~/.nimble/memory/reports/seo-ai-visibility-{brand-slug}-*.md` for
  same-day runs. If a same-day report exists, ask: "Already ran today. Run again for
  fresh data?" Don't silently re-run.
- No profile → Step 1

### Step 1: First-Run Onboarding (2 prompts max)

Follow `references/profile-and-onboarding.md` for the full onboarding flow. If a
business profile already exists, skip this step entirely.

### Step 2: Shape Scope (2 prompts max)

**Prompt 1** — ask in plain text (NOT AskUserQuestion with options):

> "Which brand should I audit for AI visibility? (Brand name + domain, e.g.,
> Acme Corp / acme.com)"

If `$ARGUMENTS` already contains a brand name or domain, skip this prompt. If only
one is provided, infer the other from the business profile or ask.

**Prompt 2** — confirm scope and gather inputs (use AskUserQuestion):

> I'll audit **{brand}** ({domain}) across AI search surfaces.
>
> **Query set:** How should I choose which queries to test?
> - **From profile** — pull from your `industry_keywords` + recent
>   `seo-keyword-research` results
> - **I'll provide a list** — paste queries directly
> - **Auto-discover** — I'll search for queries where your brand appears
>   and category queries where it should appear
>
> **Competitors:** {list from profile, or "Who are your main competitors?"}
>
> **Platforms:**
> - **All five** — ChatGPT + Perplexity + Google AI + Gemini + Grok
> - **Top three** — ChatGPT + Perplexity + Google AI (fastest, most reliable)
> - **Specific platforms** — pick which to test

Parse the brand name, domain, query source preference, competitor list, and platform
selection from the responses.

### Step 3: Query Discovery (if auto or profile)

**User-provided list:** Parse and deduplicate. Cap at 40 queries.

**From profile:** Combine `industry_keywords` + top keywords from the most recent
`seo-keyword-research` report. Target 20-40 queries.

**Auto-discover:** Run 4 parallel searches (`"{brand} {category}"`, `"best {category}"`,
`"{category} comparison"`, `"{category} reviews"`) using `industry_keywords` as
category terms. Filter for queries where the brand or competitors surface. Present
the list for user confirmation. Target 20-40 queries.

### Step 4: WSA Discovery

Search for relevant agents in parallel:

```bash
nimble agent list --search "google serp" --limit 100
nimble agent list --search "search engine" --limit 100
```

For any promising agents, validate with `nimble agent get --template-name {name}`.
Use WSA agents if they provide structured SERP data (AI Overview fields, featured
snippets). Fall back to `nimble search` + `nimble extract --render` if no suitable
agent exists or if the agent output lacks AI Overview content.

Never hardcode agent names — discover dynamically every run.

### Step 5: AI Platform Querying via Dedicated Agents

Read `references/ai-platform-profiles.md` for the full agent schemas, per-platform
ranking factors, and Princeton GEO optimization methods.

Use Nimble's dedicated AI platform agents to query **5 platforms** directly. Each
agent sends a real prompt to the platform and returns structured `answer` text +
`sources` with URLs. This replaces the previous approach of `--include-answer`
proxying and flaky Perplexity extraction.

**The 5 platforms:**

| Platform | Agent | Input | Key outputs |
|----------|-------|-------|-------------|
| ChatGPT | `chatgpt` | `prompt` | `answer`, `markdown`, `sources` [{url, title, source, snippet}], `links` |
| Perplexity | `perplexity` | `prompt` | `answer`, `markdown`, `sources` [{url, icon, title, snippet, description, startPosition, endPosition}], `links` |
| Google AI Mode | `google_ai` | `keyword` | `answer`, `sources` [{url, title}] |
| Gemini | `gemini` | `prompt` | `answer`, `markdown`, `answer_html`, `sources` [{icon, title, snippet, description, startPosition, endPosition, source_domain}], `links` |
| Grok | `grok` | `prompt` | `answer`, `answer_html`, `sources` [{url, title}], `links`, `images` |

**Query construction:** Phrase queries as natural questions an end-user would ask
an AI assistant. Example: for keyword "web scraping api", the prompt becomes
"What is the best web scraping API?" or "Compare the top web scraping APIs."
For `google_ai`, use the `keyword` param directly (it's a search query, not a
conversational prompt).

**Execution:** Spawn `nimble-researcher` sub-agents (max 4, `bypassPermissions`).
Reference `references/ai-visibility-agent-prompt.md` for the prompt template.
Assign each agent a batch of 5-8 queries for one platform:

```bash
# Per-query, per-platform
nimble agent run --agent chatgpt --params '{"prompt": "{query}", "skip_sources": false}'
nimble agent run --agent perplexity --params '{"prompt": "{query}"}'
nimble agent run --agent google_ai --params '{"keyword": "{query}"}'
nimble agent run --agent gemini --params '{"prompt": "{query}", "skip_sources": false}'
nimble agent run --agent grok --params '{"prompt": "{query}"}'
```

For 6+ queries per platform, use `nimble agent run-batch`:

```bash
nimble agent run-batch \
  --shared-inputs 'agent: chatgpt' \
  --input '{"params": {"prompt": "query 1", "skip_sources": false}}' \
  --input '{"params": {"prompt": "query 2", "skip_sources": false}}'
```

**Also run traditional SERP** for Google AI Overview detection:

```bash
nimble search --query "{query}" --search-depth deep --country US --max-results 10
```

This captures whether the query triggers an AI Overview in standard Google Search
(distinct from Google AI Mode). Check the response for AI Overview indicators.

**Agent coordination:**
- 5 platform agents + 1 SERP track = 6 data sources per query
- Max 4 sub-agents concurrently — cycle through platforms
- Each agent returns `data.parsing.answer` + `data.parsing.sources`
- If an agent fails, retry once. If still failing, exclude that platform for
  that query and note it. Don't fabricate data for unreachable platforms.

**Fallback for agent unavailability:** If any agent is not found during WSA
discovery (Step 4), fall back to `nimble search --include-answer` for that
platform's queries and note reduced data quality in the report.

### Step 6: Citation & Mention Analysis

For each query + platform combination, analyze the returned content and extract:

| Field | Description |
|-------|-------------|
| `brand_mention` | Brand name appears in the AI answer text (case-insensitive, including common variants) |
| `domain_citation` | Brand's domain appears in the cited sources list |
| `position_in_answer` | Character offset of first brand mention, or ordinal position among cited sources |
| `sentiment` | Sentiment of the sentence containing the brand mention: positive / neutral / negative / unknown |
| `competitor_mentions` | List of competitor names found in the answer text |
| `competitor_domain_citations` | List of competitor domains found in the cited sources |
| `answer_excerpt` | 1-2 sentence snippet around the brand or competitor mention for evidence |

Detection rules:
- **Brand mention:** case-insensitive match of brand name and common abbreviations
  (e.g., "Acme Corp", "Acme", "ACME"). Check the full AI answer text.
  **False-positive guard for common-word brands:** If the brand name is a common
  English word (e.g., "Nimble", "Stripe", "Notion", "Craft"), require EITHER:
  (a) the brand name appears within 5 words of a domain-relevant term (e.g.,
  "Nimble" near "API", "scraping", "web data"), OR
  (b) the brand's domain is also cited in the sources list.
  A standalone mention of the common word without contextual proximity or domain
  citation is likely generic usage, not a brand mention. Record as `brand_mention:
  false` with a note: "generic usage — not brand mention."
- **Domain citation:** normalize URLs to root domain (strip `www.`, protocol, path)
  and compare against brand domain and competitor domains.
- **Sentiment:** analyze only the sentence(s) containing the brand mention. Use
  positive/negative signal words. Default to "unknown" if ambiguous.

### Step 7: Scoring

Compute the following metrics from the per-query analysis:

**AI Visibility Score** = percentage of queries where the brand has at least one
mention OR domain citation in any AI answer across tested platforms.

```
visibility_score = queries_with_brand_presence / total_queries * 100
```

**Share of AI Voice** = brand's share of total mentions and citations across all
queries, compared against competitors.

```
brand_signals = brand_mentions + brand_citations
all_signals = brand_signals + sum(competitor_mentions + competitor_citations)
share_of_voice = brand_signals / max(all_signals, 1) * 100
```

**Zero-signal guard:** If `all_signals == 0` (no brand or competitor appears in any
AI answer), set `share_of_voice = 0` and note in the report: "No brands detected in
AI answers for the tested queries — the space may not yet trigger AI-generated
responses." Do not divide by zero.

**Platform Breakdown** — per-platform metrics:
- Queries where an AI answer was present
- Brand mentioned count
- Brand domain cited count
- Coverage rate (brand present / AI answers present)

**Citation Rate** — how often brand mentions translate into domain citations:

```
citation_rate = domain_citations / max(brand_mentions, 1)
```

A high mention count with low citation rate means the brand is discussed but not
linked — an optimization opportunity.

**Competitor Gap** — queries where at least one competitor appears in an AI answer
but the brand does not. These are the highest-priority optimization targets.

If a platform was unreachable for some or all queries, compute scores only from
platforms that returned data. Never fabricate metrics for missing platforms — report
the gap explicitly.

### Step 8: Delta Tracking

If a prior snapshot exists (loaded in Step 0), compare the current run against it:

- **New citations gained:** queries where brand was absent before but appears now
- **Citations lost:** queries where brand was present before but absent now
- **Competitor movements:** competitors that gained or lost visibility since last run
- **AI Overview coverage changes:** queries that newly trigger (or stop triggering)
  AI Overviews
- **Score changes:** visibility score and share of voice delta (current - previous)

Surface only changes in the TL;DR. If this is the first run (no prior snapshot),
skip delta tracking and present the full baseline.

### Step 9: Save & Update Memory

Make all Write calls simultaneously:

- **Report** → `~/.nimble/memory/reports/seo-ai-visibility-{brand-slug}-{YYYY-MM-DD}.md`
  (save the full audit report)

- **Snapshot** → `~/.nimble/memory/ai-visibility/{brand-slug}/snapshot-{YYYY-MM-DD}.json`
  (structured JSON of all per-query results — used for delta tracking in future runs)

  Snapshot schema:
  ```json
  {
    "brand": "...",
    "domain": "...",
    "date": "YYYY-MM-DD",
    "competitors": [...],
    "queries": [
      {
        "query": "...",
        "platforms": {
          "chatgpt": { "ai_answer_present": true, "brand_mention": false, "domain_citation": false, "sources": [...], "error": null },
          "perplexity": { ... },
          "google_ai": { ... },
          "gemini": { ... },
          "grok": { ... }
        }
      }
    ],
    "scores": {
      "visibility_score": 65.0,
      "share_of_voice": 28.5,
      "citation_rate": 0.42,
      "platform_breakdown": { ... }
    }
  }
  ```

- **Profile** → update `last_runs.seo-ai-visibility` in
  `~/.nimble/business-profile.json`

- Follow the wiki update pattern from `references/memory-and-distribution.md`: update
  `index.md` rows for affected directories, append a `log.md` entry for this run.
  Create `~/.nimble/memory/ai-visibility/` and
  `~/.nimble/memory/ai-visibility/{brand-slug}/` directories if they don't exist.

### Step 10: Share & Distribute

**Always offer distribution — do not skip this step.** Follow
`references/memory-and-distribution.md` for connector detection, sharing flow, and
source links enforcement.

**Slack-specific:** Post TL;DR only — not the full report. Format:

> AI Visibility: {brand} — {visibility_score}% visible across {N} queries.
> Share of Voice: {share_of_voice}% (vs {top_competitor} at {competitor_share}%).
> {Top finding}. Full report saved locally.

### Step 11: Follow-ups

- **Drill into a query** → show full answer text, all citations, competitor detail
- **Expand query set** → add more queries and re-run for those
- **Compare with previous run** → load prior snapshot and diff
- **"Looks good"** → done

**Sibling skill suggestions:**

> **Next steps:**
> - Run `seo-content-gap` to find content opportunities for queries where
>   competitors are cited but you're not
> - Run `seo-keyword-research` to expand the query set with high-intent terms
> - Schedule weekly re-runs to track visibility trends over time

If the user's agent platform supports a `loop` pattern, mention it as an option
for automated weekly monitoring.

---

## Output Format

```
# AI Visibility Report — {Brand} — {Date}

## TL;DR
{Brand} appears in AI answers for {X}% of {N} queries tested.
Share of AI Voice: {Y}% vs {top competitor} at {Z}%.
{Delta summary if re-run: "+3 new citations gained, -1 lost since {last_date}."}
{Top 2-3 findings with specifics.}

## Platform Breakdown

### Google AI Overviews
- Queries triggering AI Overview: {N}/{total}
- Brand mentioned in AIO: {N}
- Brand domain cited in AIO: {N}
- Coverage rate: {N}%
- Top queries where brand appears:
  - "{query}" — mentioned + cited, position {N} — [source]({url})
  - "{query}" — mentioned only — [source]({url})

### Perplexity
- Queries with answers: {N}/{total}
- Brand mentioned: {N}
- Brand domain cited: {N}

### ChatGPT
- Queries with answers: {N}/{total}
- Brand mentioned: {N}
- Brand domain cited: {N}

### Gemini
- Queries with answers: {N}/{total}
- Brand mentioned: {N}
- Brand domain cited: {N}

### Grok
- Queries with answers: {N}/{total}
- Brand mentioned: {N}
- Brand domain cited: {N}

## Query-Level Results

| Query | Google AIO | ChatGPT | Perplexity | Gemini | Grok | Competitor(s) |
|-------|-----------|---------|------------|--------|------|---------------|
| {query} | Cited | Mentioned | Cited | — | — | WidgetCo |

## Competitor Comparison

| Brand | Visibility Score | Share of Voice | Citation Rate | Queries Present |
|-------|-----------------|----------------|---------------|-----------------|
| {Brand} | {X}% | {Y}% | {Z} | {N}/{total} |
| {Competitor1} | {X}% | {Y}% | {Z} | {N}/{total} |
| {Competitor2} | {X}% | {Y}% | {Z} | {N}/{total} |

## Optimization Opportunities

### High-Priority (competitor visible, you're not)
- "{query}" — {Competitor} cited on {platform}, you're absent
  Suggested action: {specific recommendation}

### Quick Wins (mentioned but not cited)
- "{query}" — brand mentioned in {platform} answer but domain not in sources
  Suggested action: {specific recommendation to earn citation}

### Coverage Gaps (no AI answer yet, but emerging)
- "{query}" — no AI Overview triggered yet; early content positioning opportunity

## GEO Optimization Playbook

For each high-priority gap (competitor visible, you're not), recommend specific
Princeton GEO methods from `references/ai-platform-profiles.md`:

| Gap Query | Platform(s) | Recommended GEO Methods | Expected Boost |
|-----------|-------------|------------------------|----------------|
| {query} | ChatGPT, Perplexity | Cite Sources (+40%), Add Statistics (+37%) | High |
| {query} | Google AIO | Authoritative Tone (+25%), Technical Terms (+18%) | Medium |

Per-platform actions and content block sizing guidance are in
`references/ai-platform-profiles.md` — reference it directly rather than
restating here. Key rules: GEO blocks = 134-167 words; AEO blocks = 40-55
words; keyword stuffing hurts AI visibility by -10%.

## What This Means
Strategic interpretation: what the visibility scores mean for the brand's
discoverability in AI-first search. Where the brand is strong, where it's
vulnerable, and what the competitor landscape looks like across AI surfaces.

## Next Steps
- Run `seo-content-gap` for content opportunities on high-priority gap queries
- Run `seo-keyword-research` to expand the query set
- Schedule weekly re-runs to track visibility trends
```

---

## Error Handling

See `references/nimble-playbook.md` for the standard error table (missing API key,
429, 401, empty results, extraction garbage). Skill-specific errors:

- **Agent returns error or empty:** Retry once. If still failing, log the platform
  as "unavailable" for that query and continue with others. Do not abort for a
  single platform failure. Common agent errors: timeout (the AI platform took too
  long), rate limit (too many concurrent requests — reduce batch size).

- **Gemini 500 errors:** Intermittent platform issue. Retry once; if still failing,
  exclude Gemini and note "Gemini unavailable" in the report. Score from remaining
  platforms only.

- **429 on Google searches:** Reduce sub-agent concurrency from 4 to 2. If 429
  persists, switch to sequential queries with a brief pause between calls. Note
  reduced throughput in the report but complete the run.

- **Google AI Overview not present for a query:** This is expected — not all queries
  trigger AI Overviews. Record `ai_answer_present: false` and move on. Do not treat
  this as an error.

- **Sub-agent returns partial results:** Merge what the agent returned. Re-run only
  the missing queries directly from the main context. Don't re-run queries that
  already have data.

- **All platforms fail for a query:** Record the query as "all platforms unreachable"
  in the results. Exclude it from score calculations but list it in the report so
  the user knows the query was tested.

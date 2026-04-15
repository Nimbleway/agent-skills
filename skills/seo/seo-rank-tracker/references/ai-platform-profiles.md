# AI Platform Profiles

Reference for querying AI platforms and optimizing content for AI visibility.

---

## Nimble AI Platform Agents

Agents enable direct querying of AI platforms and Google Search. Discover them at
runtime with `nimble agent list --search "ai"` — the table below documents current
behavior but new agents may appear.

### AI Platform Agents

| Agent | Input Param | Input Type | Key Output Fields | Managed By |
|---|---|---|---|---|
| `chatgpt` | `prompt` | string | `answer`, `markdown`, `sources` [{url, title, source, snippet}], `links` | community |
| `perplexity` | `prompt` | string | `answer`, `markdown`, `answer_html`, `sources` [{url, icon, title, snippet, description, startPosition, endPosition}], `links` | community |
| `google_ai` | `keyword` | string | `answer`, `sources` [{title, url}] | nimble |
| `gemini` | `prompt` | string | `answer`, `markdown`, `answer_html`, `sources` [{icon, title, snippet, description, startPosition, endPosition, source_domain}], `links` | nimble |
| `grok` | `prompt` | string | `answer`, `answer_html`, `sources` [{title, url}], `links`, `images` | nimble |
| `google_sge_new` | `query` | string | `content` (raw HTML), `entity_type` | nimble |

### Google Search Agent (SERP Enrichment)

The `google_search` agent returns **typed SERP entities** — each result includes
an `entity_type` field (e.g., `OrganicResult`, `PeopleAlsoAsk`, `FeaturedSnippet`,
`ShoppingResult`, `SiteLinks`). Use as an enrichment layer on top of
`nimble search --search-depth lite` when SERP feature detection is needed.

| Param | Required | Type | Description |
|---|---|---|---|
| `query` | yes | string | Search term |
| `country` | no | string | ISO Alpha-2 (default: `US`) |
| `locale` | no | string | LCID language (e.g., `en`, `de`) |
| `location` | no | string | City/state string (Nimble resolves to UULE) or raw UULE value |
| `num_results` | no | number | Results to return (max 100) |
| `start` | no | number | Pagination offset: 0=page 1, 10=page 2, 20=page 3 |
| `time` | no | string | Time range: `hour`, `day`, `week`, `month`, `year` |

Response structure: `data.parsing.entities` is a **dict keyed by entity type
name** (e.g., `AIOverview`, `OrganicResult`, `RelatedQuestion`, `Ad`). Each
value is an array of records. Entity types are **dynamic** — new types may
appear for different queries (news, images, shopping, local, knowledge panels,
featured snippets, etc.). Always iterate all keys to discover present features.

Common fields per `OrganicResult`: `position`, `title`, `url`, `cleaned_domain`,
`description`, `snippet`. `RelatedQuestion` records have `question`.
Also check `data.parsing.entities_count` for a quick type→count summary.

```bash
nimble agent run --agent google_search --params '{"query": "best web scraping api", "num_results": 20, "country": "US", "locale": "en"}'
```

**When to use:** SERP feature enrichment on priority keywords (3-5 per run).
**When NOT to use:** Bulk position checks — use `nimble search --search-depth lite`
for all-keyword sweeps (cheaper, faster). The `google_search` agent is the
enrichment layer, not the replacement.

### Usage Pattern

```bash
nimble agent run --agent chatgpt --params '{"prompt": "What is the best web scraping API?"}'
nimble agent run --agent perplexity --params '{"prompt": "What is the best web scraping API?"}'
nimble agent run --agent google_ai --params '{"keyword": "best web scraping api"}'
nimble agent run --agent gemini --params '{"prompt": "What is the best web scraping API?"}'
nimble agent run --agent grok --params '{"prompt": "What is the best web scraping API?"}'
```

### Agent-Specific Notes

- **chatgpt:** Set `skip_sources: false` to get source citations. Increases load time
  but required for visibility analysis.
- **perplexity:** Sources include `startPosition`/`endPosition` — use these for
  position-in-answer detection (earlier position = stronger citation).
- **gemini:** Sources include `source_domain` — simplifies domain matching without
  URL parsing.
- **google_sge_new:** Returns raw HTML, not a structured answer. Use `google_ai` for
  structured responses with clean `answer` and `sources` fields.
- **All agents:** Response fields live under `data.parsing.{field}` in the JSON.
- **Batch queries:** Use `nimble agent run-batch` when running 6+ queries per platform.

---

## Per-Platform Ranking Factor Profiles

Based on Princeton/KDD 2024 GEO study (arXiv:2311.09735), SE Ranking (400K page
study), and ZipTie research.

### ChatGPT

- Content-answer fit accounts for ~55% of citation likelihood (ZipTie study)
- Domain authority contributes only ~12% — far less than traditional SEO
- Content published within 30 days gets 3.2x more citations than older content
- Preferred formats: direct answers, structured comparisons, statistics-rich content
- Key signal: match ChatGPT's own response style — mirror the concise, list-oriented
  format it uses when answering
- Lists and tables are cited more often than prose paragraphs
- Definitions that start with "X is..." pattern get high citation rates

### Perplexity

- FAQ schema (JSON-LD) disproportionately rewarded over other structured data types
- Publicly accessible PDFs get priority treatment
- Publishing velocity matters more than keyword targeting — frequent updates win
- Content with explicit source citations is favored (Perplexity prefers citing
  content that itself cites sources)
- Position in answer correlates with source quality + freshness
- `startPosition`/`endPosition` in agent output map to citation placement within
  the generated answer — lower startPosition means the source was cited earlier
- Sources appearing in the first paragraph of Perplexity's answer carry the
  highest visibility value

### Google AI Overviews / Google AI Mode

- E-E-A-T signals dominate: Experience, Expertise, Authoritativeness, Trust
- Structured data (JSON-LD) helps significantly — especially FAQ, HowTo, Product
- Passage-level optimization outperforms page-level (AI extracts passages, not pages)
- Content within Google's knowledge graph entities ranks higher
- Featured snippet winners are 2x more likely to appear in AI Overviews
- Pages ranking in positions 1-5 organically supply ~80% of AI Overview citations
- Long-tail informational queries trigger AI Overviews most frequently

### Gemini

- Uses Google's knowledge graph for entity recognition
- Favors authoritative, well-structured content with clear headings
- Source citations often mirror Google AI Overview patterns
- `source_domain` field in agent output enables direct domain matching
- Structured data signals overlap heavily with Google AI — optimize once, benefit twice

### Grok

- Integrated with X (Twitter) data — real-time content weighted heavily
- Social signals and trending topics influence responses
- Recency bias is the strongest of any platform
- Less studied than other platforms — treat findings as directional, not definitive

### Claude (Reference Only — Not Directly Queryable)

- Uses Brave Search backend (not Google/Bing) for web-grounded responses
- Extremely selective about citations — quality over quantity
- Factual density with specific numbers is the strongest signal
- Crawl-to-refer ratio: 38,065:1 — most crawled pages never get cited
- No Nimble agent available; monitor via robots.txt and Brave Search visibility
- To estimate Claude visibility, check Brave Search rankings for your target queries
  and look for `ClaudeBot` / `anthropic-ai` access in robots.txt

---

## Princeton GEO Optimization Methods

Nine methods ranked by measured visibility boost from the KDD 2024 study
(arXiv:2311.09735). Apply these to content blocks targeting AI citation.

| # | Method | Visibility Boost | When to Apply |
|---|--------|-----------------|---------------|
| 1 | Cite Sources | +40% | Add authoritative external citations to claims |
| 2 | Statistics Addition | +37% | Include specific numbers, percentages, data points |
| 3 | Quotation Addition | +30% | Add expert quotes with attribution |
| 4 | Authoritative Tone | +25% | Confident, expert language (not hedging) |
| 5 | Easy-to-Understand | +20% | Simplify complex concepts for broad audience |
| 6 | Technical Terms | +18% | Use domain-specific vocabulary appropriately |
| 7 | Unique Words | +15% | Vocabulary diversity distinguishes from competitors |
| 8 | Fluency Optimization | +15-30% | Readability and natural flow |
| 9 | Keyword Stuffing | **-10%** | AVOID — actively hurts AI visibility |

### Best Combinations

- **Fluency + Statistics** = highest overall boost across platforms
- **Citations + Authoritative Tone** = best for professional/B2B content
- **Easy Language + Statistics** = best for consumer-facing content

### Content Block Sizing

Different AI surfaces extract content at different granularities:

- **GEO (AI Overview citations):** 134-167 word self-contained passage blocks
- **AEO (Featured Snippets):** 40-55 word direct answer blocks
- **Voice search:** Under 30 words — one clear sentence

Each block should be self-contained: a reader (or AI) should understand it without
needing surrounding paragraphs for context.

### Applying GEO Methods to Existing Content

When auditing a page for AI visibility optimization:

1. Identify the target query (what question should this page answer?)
2. Check which AI platforms currently cite the page (run agents above)
3. Score the page against the 9 methods — which are present, which are missing?
4. Prioritize adding the top 3 methods (Citations, Statistics, Quotations) first
5. Restructure content into appropriately-sized blocks for the target surface
6. Re-query platforms after changes to measure improvement

Do not apply all 9 methods to every page. Pick the 3-4 most relevant based on
content type and target audience.

---

## AI Bot Access

### Robots.txt User Agents

Check `robots.txt` for these crawlers. Blocking them reduces AI visibility.

| User Agent | Platform |
|---|---|
| `GPTBot` | OpenAI training crawler |
| `ChatGPT-User` | ChatGPT browse mode |
| `ClaudeBot` / `anthropic-ai` | Anthropic's crawler |
| `PerplexityBot` | Perplexity's crawler |
| `GoogleOther` | Google's AI training crawler |
| `Googlebot` | Google's main crawler (also used for AI Overviews) |

**Recommendation:** Allow all AI bots unless there is a specific, documented reason
to block. Each blocked bot is a visibility channel closed.

### LLMs.txt

Check for `/llms.txt` at the site root — the emerging standard for telling AI agents
about site structure and capabilities. Presence of this file signals AI-awareness and
can improve how AI platforms index the site.

```bash
nimble extract --url "https://example.com/llms.txt" --format markdown
nimble extract --url "https://example.com/robots.txt" --format markdown
```

### Access Audit Pattern

For a target domain, run both checks in parallel:

1. Fetch `robots.txt` and grep for AI bot user agents listed above
2. Fetch `/llms.txt` and check for structured site description

Report which bots are allowed, which are blocked, and whether `llms.txt` exists.
This is a prerequisite for any AI visibility optimization — if bots cannot crawl,
no amount of content optimization will help.

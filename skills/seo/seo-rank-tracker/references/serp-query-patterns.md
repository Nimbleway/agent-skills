# SERP Query Patterns

Query construction, SERP parsing, and batching rules for rank tracking.

---

## Query Normalization

Before sending a keyword to `nimble search`, normalize it:

1. **Lowercase** the entire query string.
2. **Trim** leading and trailing whitespace.
3. **Collapse** multiple spaces into a single space.
4. **Preserve intentional quotes.** If the user wraps a keyword in quotes
   (e.g., `"project management"`), keep them — this signals an exact phrase match.
   Do not add quotes to unquoted keywords.
5. **Strip special characters** that break search queries: `[`, `]`, `{`, `}`.
   Leave hyphens, ampersands, and periods intact (they are meaningful in brand
   names and domains).

Examples:
- `"  Project Management Software "` → `"project management software"`
- `"\"best CRM tools\""` → `"\"best crm tools\""` (quotes preserved)
- `"SaaS [enterprise]"` → `"saas enterprise"`

## Locale Flags

Two flags control geographic and language targeting:

| Flag | Values | Default | Purpose |
|------|--------|---------|---------|
| `--country` | ISO 3166-1 alpha-2 (e.g., `US`, `GB`, `DE`, `FR`, `AU`) | `US` | SERP geo-targeting |
| `--locale` | ISO 639-1 (e.g., `en`, `de`, `fr`, `es`, `ja`) | `en` | Result language |

Always set both flags explicitly. If the user says "UK rankings", use
`--country GB --locale en`. If "German rankings", use `--country DE --locale de`.

Common combinations: `US`/`en`, `GB`/`en`, `DE`/`de`, `FR`/`fr`, `AU`/`en`,
`JP`/`ja`, `BR`/`pt`.

## SERP Feature Taxonomy

When parsing SERP results, scan for these features and record which are present
for each keyword query:

| Feature | Detection Signal |
|---------|-----------------|
| **AI Overview** | AI-generated summary at the top of results |
| **Featured Snippet** | Answer box above organic result #1 |
| **People Also Ask** | Expandable question list in results |
| **Knowledge Panel** | Entity info panel on the right side |
| **Image Pack** | Row of image thumbnails in results |
| **Video Pack** | Video carousel (usually YouTube) |
| **News Pack** | News article cluster in results |
| **Shopping Pack** | Product listing ads with prices |
| **Local Pack** | Map with local business listings |
| **Site Links** | Expanded sub-links under an organic result |

Record features as a JSON array of lowercase snake_case identifiers:
`["featured_snippet", "people_also_ask", "site_links"]`.

Not every feature will be detectable from `--search-depth lite` JSON. The lite
response focuses on organic results. Use `--search-depth fast` on priority
keywords for richer SERP feature data.

## Parsing `nimble search` Results

### Lite depth (`--search-depth lite`)

Returns a JSON response. Navigate to the organic results array. For each result:

- `position`: 1-indexed rank in the organic results list (first result = 1).
- `url`: The ranking page URL.
- `title`: The page title as shown in the SERP.
- `description`: The meta description or snippet shown in the SERP.

### Domain Matching

To determine whether the target domain ranks for a keyword:

1. Extract the `url` from each organic result.
2. Normalize the URL:
   - Strip protocol (`https://`, `http://`).
   - Strip `www.` prefix.
   - Strip trailing slash.
   - Extract the root domain (e.g., `blog.example.com` → `example.com`).
3. Compare the normalized root domain against the target domain.

A domain "ranks" if any organic result's root domain matches the target domain.
Record the **first** (highest) matching position.

Example: tracking `example.com`
- `https://www.example.com/features` → matches at position 3
- `https://blog.example.com/post` → matches at position 7
- Use position 3 (the higher rank).

If no organic result matches the target domain within the top 20 results, record
`position: null` and `ranking_url: null`.

### SERP Feature Enrichment via `google_search` Agent

The `google_search` Nimble agent returns **typed SERP entities** — each result has
an `entity_type` field (e.g., `OrganicResult`, `PeopleAlsoAsk`, `FeaturedSnippet`,
`ShoppingResult`, `SiteLinks`). Use this for SERP feature detection on priority
keywords after the lite pass:

```bash
nimble agent run --agent google_search --params '{"query": "{keyword}", "num_results": 20, "country": "US", "locale": "en"}'
```

Additional params: `time` (hour/day/week/month/year), `location` (city string or
UULE), `start` (pagination offset: 0=page1, 10=page2, 20=page3).

## When to Use What

| Source | Cost | Use Case |
|--------|------|----------|
| `nimble search --search-depth lite` | 1 credit | Per-keyword position check. Default for all keywords. |
| `google_search` agent | 1 agent call | SERP feature enrichment on top 5 priority keywords. Full report mode. |

Never use `--search-depth deep` for rank tracking — it fetches full page content,
which is unnecessary for position detection and wastes credits.

Never use `--search-depth standard` — it is not a valid value.

## Batching Pattern

Group keywords into batches for parallel sub-agent execution:

1. **Batch size:** ~5 keywords per sub-agent. This balances parallelism against
   rate limits and keeps each agent's scope manageable.
2. **Max agents:** 4 concurrent `nimble-researcher` agents.
3. **Max keywords per run:** 4 agents x 5 keywords = 20 keywords in one wave.
   For > 20 keywords, run in multiple waves (complete wave 1, then wave 2).

Each agent handles its batch independently and returns a JSON array of per-keyword
ranking records. The parent context merges results from all agents into the final
snapshot.

### Agent return format

Each sub-agent returns a JSON array with one object per keyword. Fields:
`keyword`, `position` (int or null), `ranking_url`, `title`, `snippet`,
`serp_features` (array of snake_case feature IDs), `checked_at` (ISO 8601).
Use null for all fields except `keyword`, `serp_features`, and `checked_at`
when the domain is not in the top 20.

## Handling Unranked Keywords

When the target domain does not appear in the top 20 results for a keyword:

- Set `position: null`, `ranking_url: null`, `title: null`, `snippet: null`.
- Still record `serp_features` for the keyword — knowing what features appear
  on that SERP is useful even when the domain is absent.
- Still record `checked_at` — confirms the query ran.
- In the report, show as "Not ranked" or "—" in the position column.
- In delta computation: transitioning from a numeric position to null is a
  **Drop-out**; transitioning from null to a numeric position is a **New entry**.

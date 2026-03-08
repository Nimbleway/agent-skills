---
name: nimble-search-reference
description: |
  Reference for nimble search command. Load when searching the live web.
  Contains: all flags, 8 focus modes (general/coding/news/academic/shopping/social/geo/location),
  v0.5.0 vs v0.4.x flag differences (--focus vs --topic, --max-results vs --num-results),
  response structure, credit costs.
---

# nimble search — reference

Real-time web search with 8 focus modes. Returns results with titles, URLs, and optionally full content and AI answers.

## Basic usage

```bash
# Fast search — metadata only, no page fetch (v0.5.0+)
nimble search --query "React server components" --deep-search=false

# Fast search (v0.4.x — omit --deep-search entirely)
nimble search --query "React server components"

# Deep search — fetches full content from each result page (v0.5.0+)
nimble search --query "React server components"

# With AI-synthesized answer
nimble search --query "how to implement JWT auth in Node.js" \
  --focus coding --deep-search=false --include-answer
```

## Focus modes

| Mode       | Best for                            | Example query                            |
| ---------- | ----------------------------------- | ---------------------------------------- |
| `general`  | Broad web (default)                 | "best practices for X"                   |
| `coding`   | Docs, code, Stack Overflow, GitHub  | "how to implement X in Python"           |
| `news`     | Current events, breaking news       | "EU AI Act enforcement 2026"             |
| `academic` | Research papers, scholarly articles | "transformer attention mechanisms paper" |
| `shopping` | Products, price comparisons         | "best wireless headphones under $200"    |
| `social`   | People, LinkedIn, X, YouTube        | "Jane Doe Head of Engineering"           |
| `geo`      | Geographic and regional data        | "tech companies in Berlin"               |
| `location` | Local businesses, restaurants       | "italian restaurants San Francisco"      |

```bash
# News with time filter
nimble search --query "OpenAI announcements" --focus news --time-range week --deep-search=false

# Shopping comparison
nimble search --query "standing desk under $500" --focus shopping --deep-search=false --include-answer

# People research — run both social and general in parallel
nimble search --query "Jane Doe Head of Engineering" --focus social --deep-search=false --include-answer
nimble search --query "Jane Doe Head of Engineering" --focus general --deep-search=false --include-answer

# Domain-filtered (coding)
nimble search --query "Python asyncio best practices" \
  --focus coding --deep-search=false \
  --include-domain docs.python.org --include-domain realpython.com

# Extract only URLs from results
nimble --transform "results.#.url" search --query "React tutorials" --deep-search=false

# Date range
nimble search --query "EU AI Act" --focus news --start-date 2025-01-01 --end-date 2025-12-31
```

## All flags

| Flag                          | Description                                                         |
| ----------------------------- | ------------------------------------------------------------------- |
| `--query`                     | Search query (required)                                             |
| `--deep-search=false`         | Fast metadata-only (5–10× faster)                                   |
| `--focus`                     | Focus mode (see table above)                                        |
| `--max-results`               | Result count (default 10)                                           |
| `--include-answer`            | AI-synthesized answer (premium — retry without if 402/403)          |
| `--include-domain`            | Restrict to domain (repeatable, max 50)                             |
| `--exclude-domain`            | Exclude domain (repeatable, max 50)                                 |
| `--time-range`                | Recency: `hour`, `day`, `week`, `month`, `year`                     |
| `--start-date` / `--end-date` | Date range (YYYY-MM-DD)                                             |
| `--content-type`              | File type filter: `pdf`, `docx`, `xlsx` (only with `general` focus) |
| `--output-format`             | Content format: `markdown`, `plain_text`, `simplified_html`         |
| `--country` / `--locale`      | Localized results                                                   |
| `--max-subagents`             | Parallel agents for shopping/social/geo/location (1–10)             |

## Response structure

```
total_results   integer
answer          string  — AI summary (if --include-answer)
results[]
  title         string
  description   string
  url           string
  content       string  — full page content (if deep search)
  metadata
    position    integer
    entity_type string
    country     string
    locale      string
request_id      UUID
```

## Credit costs

| Mode                         | Cost                            |
| ---------------------------- | ------------------------------- |
| Fast (`--deep-search=false`) | 1 credit per search             |
| Deep search                  | 1 credit + 1 per page extracted |

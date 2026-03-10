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

## Table of Contents

- [Parameters](#parameters)
- [Focus modes](#focus-modes)
- [CLI](#cli)
- [Python SDK](#python-sdk)
- [Response structure](#response-structure)

---

## Parameters

| Parameter                 | Type            | Default   | Description                                                                                                       |
| ------------------------- | --------------- | --------- | ----------------------------------------------------------------------------------------------------------------- |
| `query`                   | string          | required  | Search query                                                                                                      |
| `focus`                   | string or array | `general` | Focus mode (see table below) or array of specific agent names e.g. `["amazon_serp", "target_serp"]`               |
| `deep_search`             | bool            | `true`    | `true` = fetch full page content; `false` = metadata only (5–10× faster)                                          |
| `include_answer`          | bool            | `false`   | AI-synthesized answer (premium — retry without if 402/403)                                                        |
| `max_results`             | int             | `10`      | Result count (1–100)                                                                                              |
| `output_format`           | string          | —         | `plain_text` \| `markdown` \| `simplified_html`                                                                   |
| `include_domains`         | array           | —         | Restrict to these domains (max 50)                                                                                |
| `exclude_domains`         | array           | —         | Exclude these domains (max 50)                                                                                    |
| `time_range`              | string          | —         | `hour` \| `day` \| `week` \| `month` \| `year` — cannot combine with dates                                        |
| `start_date` / `end_date` | string          | —         | Date range `YYYY-MM-DD` — cannot combine with `time_range`                                                        |
| `content_type`            | string          | —         | File type filter: `pdf`, `docx`, `xlsx`, `documents`, `spreadsheets`, `presentations` — only with `general` focus |
| `max_subagents`           | int             | —         | Parallel agents for shopping/social/geo/location (1–5)                                                            |
| `country`                 | string          | —         | ISO Alpha-2 geo-targeted results (e.g. `US`)                                                                      |
| `locale`                  | string          | —         | Language code (e.g. `en`, `fr`, `de`)                                                                             |

CLI uses hyphens (`--deep-search`, `--include-answer`). SDK uses underscores (`deep_search`, `include_answer`).

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

## CLI

```bash
# Deep search (default — fetches full content)
nimble search --query "React server components"

# Fast metadata-only
nimble search --query "OpenAI announcements" --focus news --deep-search=false

# With AI answer + domain filter
nimble search --query "Python asyncio best practices" \
  --focus coding --deep-search=false --include-answer \
  --include-domain docs.python.org --include-domain realpython.com

# Date range
nimble search --query "EU AI Act" --focus news --start-date 2025-01-01 --end-date 2025-12-31

# Extract just URLs
nimble --transform "results.#.url" search --query "React tutorials" --deep-search=false
```

## Python SDK

```python
from nimble_python import Nimble
nimble = Nimble(api_key=os.environ["NIMBLE_API_KEY"])

# Deep search (default)
resp = nimble.search(query="React server components")

# Fast + AI answer
resp = nimble.search(
    query="OpenAI announcements",
    focus="news",
    deep_search=False,
    include_answer=True,
    time_range="week",
)

# Custom focus — explicit agent array
resp = nimble.search(
    query="best wireless headphones",
    focus=["amazon_serp", "walmart_serp"],
    max_results=10,
)

results = resp.results       # list of result objects
answer = resp.answer         # AI summary (if include_answer=True)
```

## Response structure

| Field                            | Type   | Description                           |
| -------------------------------- | ------ | ------------------------------------- |
| `total_results`                  | int    | Total results returned                |
| `results`                        | array  | Search results                        |
| `results[].title`                | string | Page title                            |
| `results[].description`          | string | Snippet                               |
| `results[].url`                  | string | Page URL                              |
| `results[].content`              | string | Full page content (deep search only)  |
| `results[].metadata.position`    | int    | Result rank                           |
| `results[].metadata.entity_type` | string | e.g. `OrganicResult`                  |
| `answer`                         | string | AI summary (if `include_answer=True`) |
| `request_id`                     | UUID   | Request identifier                    |

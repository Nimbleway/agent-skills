---
name: nimble-serp-reference
description: |
  Reference for nimble serp command. Load when querying Google search engines
  directly for structured SERP data — organic rankings, SERP features, Maps,
  Images, News, AI Overview. Contains: all 7 search engines, flags, entity type
  guide, rank lookup pattern, batch, pagination, relationship to nimble search.
---

# nimble serp — reference

Returns live Google search results as typed, structured entity arrays. The direct
SERP API — no agent discovery needed, position included in every OrganicResult.

Use `nimble serp` when you need structured SERP data (rank positions, SERP features,
Maps listings, etc.). Use `nimble search` for general research and topic discovery.

## Commands

| Command                 | When to use                                           |
| ----------------------- | ----------------------------------------------------- |
| `nimble serp run`       | Single query — sync, returns structured entities      |
| `nimble serp run-async` | Single query async — delivers to cloud storage        |
| `nimble serp run-batch` | Up to 1,000 queries in one call                       |

---

## Search Engines

| `--search-engine` value | What it returns                                              | Key extra params         |
| ----------------------- | ------------------------------------------------------------ | ------------------------ |
| `google_search`         | Organic results, ads, answer boxes, related questions        | `num_results`, `time`, `location`, `device` |
| `google_aio`            | Google AI Overview (rendered) — best for AI Overview detection | `num_results`, `domain` |
| `google_news`           | Google News results                                          | `time`                   |
| `google_images`         | Google Images results                                        | `time`, `device`         |
| `google_maps_search`    | Google Maps business/location results                        | `coordinates`            |
| `google_maps_place`     | Detailed info for a specific place                           | `place_id` or `data_id`  |
| `google_maps_reviews`   | Reviews for a specific place                                 | `place_id` or `data_id`, `sort` |

---

## Parameters

| Flag               | Type    | Required | Description                                                           |
| ------------------ | ------- | -------- | --------------------------------------------------------------------- |
| `--search-engine`  | string  | Yes      | One of the 7 values above                                             |
| `--query`          | string  | Yes*     | Search query. Required for all engines except `google_maps_place` and `google_maps_reviews`. |
| `--parse`          | bool    | No       | Return structured `data.parsing.entities` JSON. Always use for rank data. |
| `--num-results`    | int     | No       | Number of results (1–100, default 10). Supported on `google_search`, `google_aio`, `google_maps_reviews`. |
| `--country`        | string  | No       | ISO Alpha-2 geo targeting (e.g. `US`, `GB`, `DE`)                    |
| `--locale`         | string  | No       | LCID locale (e.g. `en`, `en-US`, `fr-FR`)                            |
| `--location`       | string  | No       | Physical location context — string (e.g. `"New York, NY"`) or raw UULE value |
| `--time`           | string  | No       | Recency filter: `hour`, `day`, `week`, `month`, `year`                |
| `--device`         | string  | No       | `mobile` to emulate mobile. Defaults to desktop.                      |
| `--domain`         | string  | No       | Google TLD to target (e.g. `com`, `co.uk`, `de`). For `google_aio`.  |
| `--page`           | int     | No       | Result page number for pagination                                     |
| `--render`         | bool    | No       | JS rendering. Required for `ads_optimization`.                        |

---

## CLI examples

```bash
# Google web search — structured entities, 20 results, US/English
nimble serp run \
  --search-engine google_search \
  --query "project management software" \
  --parse --num-results 20 \
  --country US --locale en

# Google AI Overview — for AI Overview detection
nimble serp run \
  --search-engine google_aio \
  --query "best web scraping api" \
  --parse --country US

# Google News — recent news
nimble serp run \
  --search-engine google_news \
  --query "nimbleway" \
  --parse --time week

# Google Maps — local business search
nimble serp run \
  --search-engine google_maps_search \
  --query "Italian restaurants" \
  --country US --parse

# Google Maps reviews for a place
nimble serp run \
  --search-engine google_maps_reviews \
  --place-id "ChIJN1t_tDeuEmsRUsoyG83frY4" \
  --num-results 20 --parse
```

---

## Output shape — `data.parsing.entities`

When `--parse` is used, the response contains `data.parsing.entities` — a dict keyed by entity type. Entity types vary by search engine.

**google_search entity types:**

| Entity type       | Key fields                                                      |
| ----------------- | --------------------------------------------------------------- |
| `OrganicResult`   | `position`, `title`, `url`, `snippet`, `cleaned_domain`, `displayed_url` |
| `AnswerBox`       | `snippet`, `snippet_highlighted`                                |
| `KnowledgeGraph`  | `title`, `description`, `url`                                   |
| `RelatedQuestion` | `question`                                                      |
| `RelatedSearch`   | `query`, `url`                                                  |
| `Ad`              | `position`, `title`, `url`, `snippet`                           |
| `Pagination`      | `current_page`, `next_page_url`, `other_page_urls`              |
| `AIOverview`      | `snippet` (when AI Overview present)                            |

**Accessing rank position:**

```python
entities = response["data"]["parsing"]["entities"]
organic = entities.get("OrganicResult", [])

# Find position of target domain
for result in organic:
    if "yourdomain.com" in result.get("url", ""):
        print(result["position"], result["url"])
        break
# If not found → domain not in top N results
```

**Detecting SERP features from entities:**

```python
features = []
if "AnswerBox" in entities:   features.append("featured_snippet")
if "RelatedQuestion" in entities: features.append("people_also_ask")
if "AIOverview" in entities:  features.append("ai_overview")
if "Ad" in entities:          features.append("ads")
if "KnowledgeGraph" in entities: features.append("knowledge_panel")
# Add any other entity type key as lowercase_snake_case
```

---

## Rank lookup pattern (for rank tracking)

```bash
# Check rank for a keyword — domain presence + SERP features in one call
nimble --client-source skill-{name} serp run \
  --search-engine google_search \
  --query "{keyword}" \
  --parse --num-results 20 \
  --country {cc} --locale {locale}
```

This replaces the `nimble search` + separate WSA SERP agent pattern. Position is
in `OrganicResult[n].position` directly — no manual parsing of result order needed.

---

## Batch pattern

```bash
# Up to 1,000 queries in one call
nimble serp run-batch \
  --shared-inputs 'search_engine: google_search' \
  --shared-inputs 'parse: true' \
  --shared-inputs 'num_results: 20' \
  --shared-inputs 'country: US' \
  --input '{"query": "keyword one"}' \
  --input '{"query": "keyword two"}' \
  --input '{"query": "keyword three"}'
```

For async batch delivery to cloud storage, add `storage_url`, `storage_type`, and
`storage_object_name` to `--shared-inputs`. Poll with `nimble tasks` reference.

---

## Pagination

```bash
# Page 1 (default, results 1–10)
nimble serp run --search-engine google_search --query "..." --parse --num-results 10

# Page 2 (results 11–20) — use --page or pass start offset
nimble serp run --search-engine google_search --query "..." --parse --num-results 10 --page 2
```

Or fetch all in one call: `--num-results 100` returns up to 100 organic results.

---

## Relationship to nimble search

| Use case                              | Tool            |
| ------------------------------------- | --------------- |
| Rank position for a domain/keyword    | `nimble serp`   |
| SERP feature detection                | `nimble serp`   |
| Google Maps listings / reviews        | `nimble serp`   |
| Google AI Overview content            | `nimble serp --search-engine google_aio` |
| General research, topic discovery     | `nimble search` |
| Non-Google search engines (Bing, etc.)| `nimble search` |
| News feed, multi-source discovery     | `nimble search` |

---
name: nimble-crawl-reference
description: |
  Reference for nimble crawl command. Load when bulk-crawling many pages asynchronously.
  Contains: async workflow (run → status → tasks results), all flags, polling guidelines,
  CRITICAL: use task_id (not crawl_id) for results, crawl vs map comparison.
---

# nimble crawl — reference

Async bulk crawling — starts a crawl job, returns a `crawl_id`, then you poll for results.
For LLM use, prefer `map` + `extract --format markdown` (faster, cleaner output).
Use crawl when you need raw HTML archives of many pages at once.

## Async workflow

```bash
# Step 1: Start crawl → get crawl_id
nimble crawl run --url "https://docs.example.com" --limit 50 --name "docs-crawl"
# → { "crawl_id": "abc-123", "status": "queued" }

# Step 2: Poll status → get task_ids per page
nimble crawl status --id "abc-123"
# → { "status": "running", "total": 50, "completed": 12, "tasks": [{"task_id": "task-456", "url": "..."}, ...] }

# Step 3: Retrieve content for each page using task_id (NOT crawl_id)
nimble tasks results --task-id "task-456"
```

> **CRITICAL:** `nimble tasks results` requires the per-page `task_id` from `crawl status` — NOT the `crawl_id`. Using the crawl_id returns 404.

## All flags

| Flag | Default | Description |
|------|---------|-------------|
| `--url` | — | Starting URL (required) |
| `--limit` | 5000 | **Always set this.** Max pages to crawl (1–10,000) |
| `--name` | — | Label for tracking and management |
| `--sitemap` | `include` | Sitemap usage: `include`, `only`, `skip` |
| `--include-path` | — | Regex for URLs to include (repeatable) |
| `--exclude-path` | — | Regex for URLs to exclude (repeatable) |
| `--max-discovery-depth` | 5 | Max link depth from start (1–20) |
| `--crawl-entire-domain` | false | Follow sibling/parent paths (not just the given path) |
| `--allow-subdomains` | false | Follow links to subdomains |
| `--allow-external-links` | false | Follow external (cross-domain) links |
| `--ignore-query-parameters` | false | Deduplicate query param variants |
| `--country` | `ALL` | ISO Alpha-2 proxy location |
| `--locale` | — | LCID format (e.g. `en-US`) |

## Status & management

```bash
# List all crawls
nimble crawl list

# Filter by status
nimble crawl list --status running    # or: queued, completed, failed, canceled

# Cancel a crawl
nimble crawl terminate --id "abc-123"
```

## Crawl status values

`queued` → `running` → `succeeded` / `failed` / `canceled`

## Polling guidelines

| Crawl size | Poll interval |
|------------|---------------|
| < 50 pages | every 15–30s |
| 50–500 pages | every 30–60s |
| 500+ pages | every 60–120s |

## Examples

```bash
# Crawl only the /api section
nimble crawl run --url "https://docs.example.com" --include-path "/api" --limit 100 --name "api-docs"

# Exclude the blog section
nimble crawl run --url "https://example.com" --exclude-path "/blog" --limit 200

# Deep crawl with subdomain support
nimble crawl run \
  --url "https://example.com" \
  --limit 500 \
  --max-discovery-depth 10 \
  --allow-subdomains \
  --name "full-site"
```

## Task results structure

```json
{
  "url": "https://example.com/page",
  "html": "<html>...</html>",
  "markdown": "# Page Title\n\nContent...",
  "headers": { "content-type": "text/html" },
  "status_code": 200,
  "metadata": { "title": "...", "description": "..." }
}
```

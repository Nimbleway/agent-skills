---
name: nimble-map-reference
description: |
  Reference for nimble map command. Load when discovering URLs on a site before bulk extraction.
  Contains: all flags (limit 1-100000, sitemap include/only/skip, domain_filter),
  response structure {links[].url/title/description}, map→filter→extract pattern, map vs crawl comparison.
---

# nimble map — reference

Discovers all URLs on a site in seconds. Returns URL metadata (url, title, description) — run `extract` on results to get page content.

## Basic usage

```bash
# Discover URLs on a site
nimble map --url "https://docs.example.com" --limit 100 > .nimble/docs-map.json

# Extract just the URLs (JMESPath transform)
nimble --transform "links.#.url" map --url "https://docs.example.com" --limit 100

# Map a specific path section
nimble map --url "https://shop.example.com/products/" --limit 200

# Fastest — sitemap only (no crawling)
nimble map --url "https://example.com" --sitemap only --limit 500
```

## All flags

| Flag | Default | Description |
|------|---------|-------------|
| `--url` | — | Starting URL (required) |
| `--limit` | 100 | Max URLs returned (1–100,000) |
| `--sitemap` | `include` | Sitemap usage: `include` (sitemap + crawl), `only` (sitemap only), `skip` (crawl only) |
| `--domain-filter` | `all` | Domain scope: `domain` (exact), `subdomain` (include subdomains), `all` (all linked) |
| `--country` | `ALL` | ISO Alpha-2 proxy location (e.g. `US`) or `ALL` |
| `--locale` | — | LCID format (e.g. `en-US`) — pair with `--country` |

## Response structure

```json
{
  "task_id": "UUID",
  "success": true,
  "links": [
    {
      "url": "https://docs.example.com/api/auth",
      "title": "Authentication",
      "description": "How to authenticate with the API"
    }
  ]
}
```

## Common patterns

```bash
# Map → filter → extract specific pages
nimble --transform "links.#.url" map --url "https://docs.stripe.com" --limit 200 > .nimble/stripe-urls.txt
grep "charges\|refund" .nimble/stripe-urls.txt
nimble --transform "data.markdown" extract --url "https://docs.stripe.com/api/charges/object" --format markdown

# Map → parallel extract all pages
nimble --transform "links.#.url" map --url "https://docs.example.com/api" --limit 50 \
  | python3 -c "
import sys, subprocess
urls = sys.stdin.read().strip().split('\n')
procs = []
for url in urls[:10]:
    slug = url.rstrip('/').split('/')[-1]
    f = open(f'.nimble/doc-{slug}.md', 'w')
    p = subprocess.Popen(['nimble', '--transform', 'data.markdown', 'extract', '--url', url, '--format', 'markdown'], stdout=f)
    procs.append((p, f))
for p, f in procs:
    p.wait(); f.close()
print(f'Done: {len(procs)} pages saved to .nimble/')
"

# Map news/blog section for bulk scraping
nimble --transform "links.#.url" map \
  --url "https://techcrunch.com/category/artificial-intelligence/" \
  --limit 50 > .nimble/tc-ai-urls.txt
wc -l .nimble/tc-ai-urls.txt
```

## When to use map vs crawl

| | `map` | `crawl` |
|--|-------|---------|
| Speed | Fast (seconds) | Slow (async, minutes) |
| Output | URL list with metadata | Raw HTML per page |
| Best for | Find the right URL, then selectively extract | Archive all pages at once |
| LLM use | ✅ Combine with `extract --format markdown` | ⚠️ Returns raw HTML — needs post-processing |

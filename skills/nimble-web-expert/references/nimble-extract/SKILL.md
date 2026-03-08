---
name: nimble-extract-reference
description: |
  Reference for nimble extract command. Load when fetching URLs or scraping pages.
  Contains: render tiers 1-5, all flags, browser actions (Tier 4), network capture (Tier 5),
  parser schemas, geo targeting, parallelization.
---

# nimble extract — reference

Fetches a URL and returns its content. The workhorse command — use for any URL where no agent exists.

## Basic usage

```bash
# Markdown (default for 90% of tasks)
nimble --transform "data.markdown" extract \
  --url "https://example.com/page" --format markdown

# Save to file
nimble --transform "data.markdown" extract \
  --url "https://example.com/page" --format markdown > .nimble/page.md
head -100 .nimble/page.md
```

## Render tiers — escalate on failure

**Failure signals:** status 500 · empty `data.html` / `data.markdown` · "captcha" / "verify you are human" in content · login wall instead of target page

| Tier | Command | When |
|------|---------|------|
| 1 | `extract --url "..."` | Static pages, docs, news articles, GitHub, Wikipedia, HN |
| 2 | `extract --url "..." --render` | SPAs, dynamic content, JS-rendered pages |
| 2b | `--render --render-options '{"render_type":"idle2","timeout":60000}'` | Slow SPAs, wait for network idle |
| 3 | `--render --driver vx10-pro` | E-commerce, social, job boards — max stealth |

```bash
# Tier 1 — no render
nimble --transform "data.markdown" extract --url "https://example.com" --format markdown

# Tier 2 — render
nimble --transform "data.markdown" extract --url "https://example.com" --render --format markdown

# Tier 3 — stealth
nimble --transform "data.markdown" extract --url "https://example.com" --render --driver vx10-pro --format markdown
```

## Browser actions (Tier 4)

For data behind clicks, scrolls, or form fills. Requires `--render`.

```bash
# Click a tab, wait for content
nimble --transform "data.markdown" extract \
  --url "https://example.com/product" --render \
  --browser-action '[
    {"type": "click", "selector": ".tab-reviews", "required": false},
    {"type": "wait_for_element", "selector": ".review-list"}
  ]' --format markdown

# Infinite scroll
nimble --transform "data.markdown" extract \
  --url "https://example.com/feed" --render \
  --browser-action '[{"type": "auto_scroll", "max_duration": 15, "idle_timeout": 3}]' \
  --format markdown

# Fill and submit search form
nimble --transform "data.markdown" extract \
  --url "https://example.com/search" --render \
  --browser-action '[
    {"type": "fill", "selector": "#q", "value": "running shoes", "mode": "type"},
    {"type": "press", "key": "Enter"},
    {"type": "wait_for_element", "selector": ".results"}
  ]' --format markdown
```

## Network capture (Tier 5)

When page data comes from XHR/AJAX calls, not the HTML. Requires `--render`.

```bash
# Intercept an API call triggered by the page
nimble extract \
  --url "https://example.com/products" --render \
  --network-capture '[{"url": {"type": "contains", "value": "/api/products"}, "resource_type": ["xhr", "fetch"]}]' \
  > .nimble/products-api.json

# Known public API endpoint — use --is-xhr (no browser, fastest)
nimble --transform "data.markdown" extract \
  --url "https://api.example.com/v1/markets?q=elections&limit=50" \
  --is-xhr --format markdown
```

> **Note:** `--is-xhr` and `--render` are mutually exclusive. `--is-xhr` = direct API call, no browser. `--render` + `--network-capture` = trigger and intercept via browser.

## Parser schemas — structured extraction

When markdown doesn't contain fields cleanly. Results land in `data.parsing`.

```bash
# Schema (single item)
nimble extract --url "https://example.com/product" --render --parse \
  --parser '{
    "type": "schema",
    "fields": {
      "title":  {"type": "terminal", "selector": {"type": "css", "css_selector": "h1"}, "extractor": {"type": "text"}},
      "price":  {"type": "terminal", "selector": {"type": "css", "css_selector": "[data-price]"}, "extractor": {"type": "text"}},
      "rating": {"type": "terminal", "selector": {"type": "css", "css_selector": ".rating"}, "extractor": {"type": "text"}}
    }
  }' | python3 -c "import json,sys; d=json.load(sys.stdin); print(json.dumps(d.get('data',{}).get('parsing',{}), indent=2))"

# Schema list (multiple items on a page)
nimble extract --url "https://example.com/listings" --render --parse \
  --parser '{
    "type": "schema_list",
    "selector": {"type": "css", "css_selector": ".listing-item"},
    "fields": {
      "title": {"type": "terminal", "selector": {"type": "css", "css_selector": "h2"}, "extractor": {"type": "text"}},
      "price": {"type": "terminal", "selector": {"type": "css", "css_selector": ".price"}, "extractor": {"type": "text"}}
    }
  }' | python3 -c "import json,sys; items=json.load(sys.stdin)['data']['parsing']; [print(i) for i in items[:10]]"
```

## Geo targeting

```bash
# US residential proxy
nimble --transform "data.markdown" extract --url "https://amazon.com/dp/B09XYZ" --country US --format markdown

# City-level
nimble --transform "data.markdown" extract --url "https://example.com" --country US --state CA --city los_angeles --format markdown

# Localized (always pair --locale with --country)
nimble --transform "data.markdown" extract --url "https://example.com/fr" --country FR --locale fr-FR --format markdown
```

## Key flags

| Flag | Description |
|------|-------------|
| `--url` | Target URL (required) |
| `--render` | Enable headless browser rendering |
| `--driver` | Render driver: `vx10-pro` (stealth), `vx8-pro` |
| `--render-options` | JSON: `render_type`, `timeout`, `userbrowser` |
| `--browser-action` | JSON array of browser actions |
| `--network-capture` | JSON array of XHR intercept rules |
| `--is-xhr` | Direct API call — no browser, no render |
| `--parse` | Enable parser (use with `--parser`) |
| `--parser` | JSON schema for structured extraction |
| `--format` | Output format: `markdown`, `html`, `raw` |
| `--country` | ISO Alpha-2 proxy location (e.g. `US`, `GB`) |
| `--state` / `--city` | City-level geo targeting |
| `--locale` | LCID (e.g. `en-US`, `fr-FR`) — pair with `--country` |
| `--transform` | JMESPath transform on response (e.g. `data.markdown`) |

## Parallelization

```bash
mkdir -p .nimble
nimble --transform "data.markdown" extract --url "https://example.com/1" --format markdown > .nimble/1.md &
nimble --transform "data.markdown" extract --url "https://example.com/2" --format markdown > .nimble/2.md &
nimble --transform "data.markdown" extract --url "https://example.com/3" --format markdown > .nimble/3.md &
wait
```

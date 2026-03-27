# Find All Locations

End-to-end location intelligence pipeline powered by Nimble web data APIs.

## What It Does

Discovers every place of a given type in a neighborhood, then enriches each with:

- **Website URL** (filtered for aggregators like Yelp/DoorDash)
- **Social profiles** (Instagram, Facebook, TikTok) with confidence scoring
- **Contact data** (phone, email, hours, menu, reservations) via website crawl

Outputs three formats:
1. **Google Sheet** -- live-updated system of record with all data
2. **JSON export** -- type-coerced, machine-readable
3. **Interactive map webapp** -- single-file HTML with search, filters, and detail modals

## Requirements

- Nimble CLI (`npm i -g @nimble-way/nimble-cli`) + `NIMBLE_API_KEY`
- Google Sheets credentials (`~/.token_enrich.json` or `GOOGLE_SERVICE_ACCOUNT_JSON`)
- Python 3.11+ with `uv` for script execution

## Quick Start

```
find all coffee shops in Williamsburg
map every bar in East Village
build a guide to restaurants in Park Slope
```

## How It Works

1. **Parse** -- extract place type, neighborhood, city from user request
2. **Strategy** -- generate 10+ search queries and 4-8 overlapping map zones
3. **Discovery** -- Google Maps multi-query zone search, deduplicate by place_id
4. **Enrichment** -- parallel web search for website + social URLs
5. **Verification** -- confidence-scored social profile matching
6. **Crawl** -- extract contact data from business websites
7. **Export** -- Google Sheet + JSON + interactive map webapp

## Reference Files

| File | Purpose |
|------|---------|
| `references/pipeline-template.md` | Discovery phase code |
| `references/query-strategies.md` | Search queries per category |
| `references/scoring-patterns.md` | Category-specific scoring |
| `references/enrichment-template.md` | Enrichment + crawl code |
| `references/social-verification.md` | Social confidence scoring |
| `references/webapp-template.md` | Interactive map template |

## Resume Support

The pipeline is fully resume-safe. Google Sheet is the canonical data store --
rerunning skips completed phases per place_id. Low-confidence social matches
are automatically retried.

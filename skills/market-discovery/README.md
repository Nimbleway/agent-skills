# Market Discovery

Discover healthcare practices across U.S. metros using Nimble Maps and web search.

## What It Does

Builds or audits an account universe for a given healthcare vertical by tiling
search across ~390 U.S. metro areas:

1. **Discovers** practices via geo-focused search across metros
2. **Deduplicates** using place_id, domain, and name+city fuzzy match
3. **Enriches** missing website URLs via targeted web search
4. **Audits** against an existing list (e.g., Definitive Healthcare) to find gaps
5. **Exports** to Google Sheet + JSON + CSV

## Output Schema

Per practice:
- Practice name, full address, city, state, ZIP
- Phone, website/domain
- Google Maps rating and review count
- Primary and all categories
- Metro area, query hit count (discovery signal strength)
- Audit status (matched / discovered_only / reference_only)

## Requirements

- Nimble CLI (`npm i -g @nimble-way/nimble-cli`) + `NIMBLE_API_KEY`
- Google Sheets credentials (for Sheet output)
- Python 3.11+ with `uv`

## Quick Start

```
find all ophthalmology practices in the US
discover dental practices in Texas
audit our practice list against the market
```

## Supported Verticals

Ophthalmology, dental, dermatology, orthopedics, cardiology, urology,
primary care — plus a generic template for any specialty.

## Reference Files

| File | Purpose |
|------|---------|
| `references/metro-coverage.md` | U.S. metro tiling strategy |
| `references/vertical-queries.md` | Search queries by specialty |
| `references/discovery-pipeline-template.md` | Python pipeline code template |

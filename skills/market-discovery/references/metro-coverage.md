# Metro Coverage

Strategy for tiling U.S. metro areas for nationwide healthcare practice discovery.

## Metro Tiers

### Tier 1: Top 50 CBSAs (population > 500K)

These metros contain the majority of practices. Search each with full query set.

```
New York, Los Angeles, Chicago, Houston, Phoenix, Philadelphia,
San Antonio, San Diego, Dallas, San Jose, Austin, Jacksonville,
Fort Worth, Columbus, Charlotte, Indianapolis, San Francisco,
Seattle, Denver, Nashville, Oklahoma City, El Paso, Washington DC,
Boston, Portland, Las Vegas, Memphis, Louisville, Baltimore,
Milwaukee, Albuquerque, Tucson, Fresno, Sacramento, Mesa,
Kansas City, Atlanta, Omaha, Colorado Springs, Raleigh,
Long Beach, Virginia Beach, Miami, Oakland, Minneapolis,
Tampa, Tulsa, Arlington, New Orleans, Cleveland
```

### Tier 2: CBSAs 51-150 (population 200K-500K)

Important secondary markets. Search with top 5 queries per metro.

### Tier 3: CBSAs 151-390 (population 50K-200K)

Smaller markets. Search with top 3 queries per metro. These often have
1-3 practices each but contribute to total market count.

### Tier 4: Rural / micropolitan (optional)

Below 50K population. Only search if user specifically requests rural coverage.
Use county-level search with 1-2 broad queries.

## State-Based Batching

For nationwide runs, execute state-by-state to enable checkpointing:

```python
STATE_METRO_COUNTS = {
    "CA": 40, "TX": 35, "FL": 30, "NY": 20, "PA": 18,
    "IL": 15, "OH": 15, "GA": 12, "NC": 12, "MI": 12,
    "NJ": 10, "VA": 10, "WA": 10, "AZ": 8, "MA": 8,
    "TN": 8, "IN": 8, "MO": 8, "MD": 7, "WI": 7,
    "CO": 7, "MN": 7, "SC": 6, "AL": 6, "LA": 6,
    "KY": 6, "OR": 5, "OK": 5, "CT": 5, "IA": 5,
    "MS": 5, "AR": 5, "KS": 4, "UT": 4, "NV": 4,
    "NE": 3, "NM": 3, "WV": 3, "ID": 3, "HI": 2,
    "NH": 2, "ME": 2, "MT": 2, "RI": 2, "DE": 2,
    "SD": 2, "ND": 2, "AK": 1, "DC": 1, "VT": 1, "WY": 1,
}
# Total: ~390 metros
```

## Rate Limit Management

- Nimble API: 10 req/sec per key
- With concurrency 10 and 3-5 queries per metro: ~2-3 metros/sec
- Full US sweep (390 metros x 8 queries): ~3,120 jobs -> ~5 minutes wall time
- With retries and rate limiting: estimate 10-15 minutes for discovery phase

## Coordinate Strategy

For Tier 1 metros, also tile with coordinates to catch places that text
search misses:

1. Look up metro center coordinates via:
   ```bash
   nimble search --query "{metro_name}" --focus geo --max-results 1 --search-depth lite
   ```
2. Generate 4 offset zones (~5km apart) around the center
3. Run coordinate-based searches with `--focus location`

This typically adds 10-20% more results vs text-only search.

## Deduplication Across Metros

Multi-location practices will appear in multiple metros. Dedup strategy:

1. **place_id** match — instant, exact
2. **Domain** match — same website = same practice organization
   - Keep the most complete record (most fields populated)
   - Track all metros where the practice was found
3. **Name + phone** match — catches practices without websites
   - Normalize both: strip "LLC", "Inc", "PA", "PC"; strip non-digits from phone

## Checkpoint Format

The script writes checkpoint per state:

```json
// ~/.nimble/memory/market-discovery/{vertical}-checkpoint.json
{
  "vertical": "ophthalmology",
  "started": "2026-03-26T10:00:00",
  "states_completed": ["CA", "TX", "FL"],
  "states_in_progress": ["NY"],
  "total_practices": 1847,
  "total_raw_results": 5230,
  "sheet_url": "https://docs.google.com/spreadsheets/d/..."
}
```

Resume reads this file and skips completed states.

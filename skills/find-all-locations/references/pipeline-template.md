# Pipeline Template

Discovery phase code for Phase 1 of the find-all-locations pipeline. Generates Google Maps
multi-query zone-based search, deduplication, normalization, and scoring.

## Dependencies

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx", "gspread", "google-auth", "google-auth-oauthlib", "nimble_python"]
# ///
```

## Imports

```python
import asyncio
import json
import os
import re
import sys
import time
import unicodedata
from datetime import datetime
from urllib.parse import urlparse

import httpx
```

## Constants

```python
NIMBLE_API_KEY = os.environ.get("NIMBLE_API_KEY", "")
AGENT_API_URL = "https://sdk.nimbleway.com/v1/agent"

MAX_RETRIES = 3
RETRY_BACKOFF = [2, 5, 15]
BATCH_WRITE_SIZE = 25
DISCOVERY_CONCURRENCY = 10
```

## Phase 1: Discovery

### Job Generation

```python
def generate_discovery_jobs(queries: list[str], zones: list[dict], neighborhood: str, city: str) -> list[dict]:
    """Generate all discovery jobs: (query x zone) + text-geo fallbacks.

    zones: [{"lat": float, "lng": float, "label": str}, ...]
    Returns: [{"query": str, "lat": float, "lng": float, "zoom": 15, "label": str}, ...]
    """
    jobs = []

    # Coordinate-based jobs
    for q in queries:
        for z in zones:
            jobs.append({
                "query": q,
                "lat": z["lat"],
                "lng": z["lng"],
                "zoom": 15,
                "label": f"{q[:30]}@{z['label']}",
            })

    # Text-geo fallback jobs (no coordinates)
    for q in queries:
        jobs.append({
            "query": f"{q} in {neighborhood}, {city}",
            "lat": None,
            "lng": None,
            "zoom": None,
            "label": f"{q[:30]}@text",
        })

    return jobs
```

### Agent Execution

```python
async def run_discovery_job(client: httpx.AsyncClient, job: dict, sem: asyncio.Semaphore) -> list[dict]:
    """Execute a single discovery job via Nimble Maps agent API."""
    async with sem:
        headers = {
            "Authorization": f"Bearer {NIMBLE_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "query": job["query"],
            "num_results": 20,
        }
        if job["lat"] is not None:
            payload["coordinates"] = {"latitude": job["lat"], "longitude": job["lng"]}
            payload["zoom"] = job["zoom"]

        for attempt in range(MAX_RETRIES + 1):
            try:
                resp = await client.post(AGENT_API_URL, json=payload, headers=headers, timeout=60)
                resp.raise_for_status()
                data = resp.json()
                results = data.get("results", data.get("data", []))
                if isinstance(results, dict):
                    results = results.get("results", [])
                return results if isinstance(results, list) else []
            except (httpx.HTTPStatusError, httpx.TimeoutException) as e:
                if attempt == MAX_RETRIES:
                    print(f"  FAIL {job['label']}: {e}", flush=True)
                    return []
                delay = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
                print(f"  Retry {attempt+1}/{MAX_RETRIES} for {job['label']} after {delay}s", flush=True)
                await asyncio.sleep(delay)
    return []
```

### Deduplication

```python
def deduplicate_places(all_results: list[tuple[dict, dict]]) -> dict[str, dict]:
    """Deduplicate by place_id, tracking query_hit_count.

    all_results: [(job_dict, result_dict), ...]
    Returns: {place_id: merged_place_dict}
    """
    places = {}
    for job, result in all_results:
        pid = result.get("place_id", "")
        if not pid:
            continue
        if pid in places:
            places[pid]["query_hit_count"] += 1
            # Merge any missing fields
            for k, v in result.items():
                if k not in places[pid] or not places[pid][k]:
                    places[pid][k] = v
        else:
            place = {**result, "query_hit_count": 1}
            places[pid] = place
    return places
```

### Normalization

```python
def normalize_place(raw: dict) -> dict:
    """Normalize a raw Google Maps result into the master schema."""
    return {
        "place_id": raw.get("place_id", ""),
        "place_name": (raw.get("title") or raw.get("name") or "").strip(),
        "full_address": (raw.get("address") or "").strip(),
        "street_address": (raw.get("street_address") or "").strip(),
        "lat": raw.get("latitude") or raw.get("lat") or 0,
        "lng": raw.get("longitude") or raw.get("lng") or 0,
        "primary_category": (raw.get("category") or raw.get("type") or "").strip(),
        "all_categories": ", ".join(raw.get("categories", [])) if isinstance(raw.get("categories"), list) else str(raw.get("categories", "")),
        "rating": float(raw.get("rating") or 0),
        "review_count": int(raw.get("review_count") or raw.get("reviews") or 0),
        "price_level": (raw.get("price_level") or raw.get("price") or "").strip(),
        "atmosphere": (raw.get("atmosphere") or "").strip(),
        "highlights": ", ".join(raw.get("highlights", [])) if isinstance(raw.get("highlights"), list) else str(raw.get("highlights", "")),
        "offerings": ", ".join(raw.get("offerings", [])) if isinstance(raw.get("offerings"), list) else str(raw.get("offerings", "")),
        "status": (raw.get("status") or raw.get("business_status") or "open").lower(),
        "query_hit_count": raw.get("query_hit_count", 1),
        "sponsored": raw.get("sponsored", False),
    }
```

### Scoring (placeholder -- replaced by category-specific logic)

```python
def score_place(place: dict) -> dict:
    """Apply quality scoring and borderline detection.

    IMPORTANT: Replace this function body with category-specific scoring
    from references/scoring-patterns.md.
    """
    quality_signal = 0
    if place["rating"] >= 4.5:
        quality_signal += 2
    if place["review_count"] >= 100:
        quality_signal += 1
    if place["query_hit_count"] >= 3:
        quality_signal += 1

    place["quality_signal"] = quality_signal
    place["borderline"] = (
        place["status"] != "open" or
        place["rating"] < 3.0 or
        (place["rating"] == 0 and place["review_count"] == 0) or
        place["query_hit_count"] == 1
    )
    return place
```

### Phase 1 Orchestrator

```python
async def run_discovery(jobs: list[dict]) -> list[dict]:
    """Run all discovery jobs, deduplicate, normalize, and score."""
    sem = asyncio.Semaphore(DISCOVERY_CONCURRENCY)
    all_results = []

    print(f"\n{'='*60}")
    print(f"Phase 1: Discovery ({len(jobs)} jobs)")
    print(f"{'='*60}", flush=True)

    async with httpx.AsyncClient() as client:
        tasks = [run_discovery_job(client, job, sem) for job in jobs]
        results_per_job = await asyncio.gather(*tasks)

        for job, results in zip(jobs, results_per_job):
            for r in results:
                all_results.append((job, r))
            if results:
                print(f"  {job['label']}: {len(results)} results", flush=True)

    print(f"\nRaw results: {len(all_results)}", flush=True)

    # Deduplicate
    unique = deduplicate_places(all_results)
    print(f"Unique places: {len(unique)}", flush=True)

    # Normalize and score
    places = []
    for pid, raw in unique.items():
        place = normalize_place(raw)
        place = score_place(place)
        places.append(place)

    places.sort(key=lambda p: (-p["quality_signal"], -p["rating"], -p["review_count"]))
    print(f"Discovery complete: {len(places)} places", flush=True)
    return places
```

## Google Sheets Setup

```python
def create_or_open_sheet(gc, title: str) -> tuple:
    """Create a new sheet or open existing one by title.

    Returns: (spreadsheet, master_ws, coverage_ws, sheet_url)
    """
    try:
        # Try to open existing
        sh = gc.open(title)
        print(f"  Opened existing sheet: {title}")
    except Exception:
        # Create new
        sh = gc.create(title)
        print(f"  Created new sheet: {title}")

    # Ensure master tab
    try:
        master_ws = sh.worksheet("master")
    except Exception:
        master_ws = sh.sheet1
        master_ws.update_title("master")

    # Ensure coverage tab
    try:
        coverage_ws = sh.worksheet("coverage")
    except Exception:
        coverage_ws = sh.add_worksheet("coverage", rows=100, cols=10)

    sheet_url = f"https://docs.google.com/spreadsheets/d/{sh.id}"
    return sh, master_ws, coverage_ws, sheet_url
```

## Coverage Tracking

```python
def write_coverage(coverage_ws, jobs: list[dict], results_per_job: list[int]):
    """Write per-job coverage stats to the coverage tab."""
    headers = ["job_label", "query", "lat", "lng", "results_count", "status", "timestamp"]
    rows = [headers]
    for job, count in zip(jobs, results_per_job):
        rows.append([
            job["label"],
            job["query"],
            str(job.get("lat", "")),
            str(job.get("lng", "")),
            str(count),
            "done" if count > 0 else "empty",
            datetime.now().isoformat(),
        ])
    coverage_ws.clear()
    coverage_ws.update(range_name="A1", values=rows)
```

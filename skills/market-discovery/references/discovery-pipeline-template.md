# Discovery Pipeline Template

Python code template for the market discovery pipeline.

## Dependencies

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx", "gspread", "google-auth", "google-auth-oauthlib"]
# ///
```

## Imports

```python
import argparse
import asyncio
import csv
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
SEARCH_API_URL = "https://sdk.nimbleway.com/v1/search"

MAX_RETRIES = 3
RETRY_BACKOFF = [2, 5, 15]
BATCH_WRITE_SIZE = 50
DISCOVERY_CONCURRENCY = 10
ENRICH_CONCURRENCY = 15

AGGREGATOR_DOMAINS = {
    "yelp.com", "tripadvisor.com", "google.com", "facebook.com",
    "instagram.com", "twitter.com", "tiktok.com", "healthgrades.com",
    "vitals.com", "zocdoc.com", "webmd.com", "ratemds.com",
    "doximity.com", "npidb.org", "npino.com", "yellowpages.com",
    "bbb.org", "mapquest.com", "superpages.com",
}
```

## Phase 1: Discovery

```python
async def search_metro_query(client: httpx.AsyncClient, query: str,
                              sem: asyncio.Semaphore) -> list[dict]:
    """Execute a single geo-focused search for a metro + query pair."""
    async with sem:
        headers = {
            "Authorization": f"Bearer {NIMBLE_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "query": query,
            "focus": "geo",
            "num_results": 20,
            "deep_search": False,
        }

        for attempt in range(MAX_RETRIES + 1):
            try:
                resp = await client.post(SEARCH_API_URL, json=payload,
                                         headers=headers, timeout=30)
                resp.raise_for_status()
                data = resp.json()

                # Extract local business results
                results = []
                for item in data.get("results", data.get("data", {}).get("results", [])):
                    if isinstance(item, dict):
                        results.append(item)
                return results

            except (httpx.HTTPStatusError, httpx.TimeoutException) as e:
                if attempt == MAX_RETRIES:
                    print(f"  FAIL: {query[:50]}: {e}", flush=True)
                    return []
                delay = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
                await asyncio.sleep(delay)
    return []


async def discover_state(client: httpx.AsyncClient, state: str,
                          metros: list[str], queries: list[str],
                          sem: asyncio.Semaphore) -> list[dict]:
    """Run discovery for all metros in a state."""
    all_results = []
    jobs = []

    for metro in metros:
        metro_queries = [q.format(metro=f"{metro}, {state}") for q in queries]
        for q in metro_queries:
            jobs.append(q)

    print(f"\n  {state}: {len(metros)} metros, {len(jobs)} jobs", flush=True)

    tasks = [search_metro_query(client, q, sem) for q in jobs]
    results_per_job = await asyncio.gather(*tasks)

    for job_query, results in zip(jobs, results_per_job):
        for r in results:
            r["_discovery_query"] = job_query
            all_results.append(r)

    print(f"  {state}: {len(all_results)} raw results", flush=True)
    return all_results
```

## Phase 2: Deduplication

```python
def normalize_name(name: str) -> str:
    """Normalize practice name for fuzzy matching."""
    name = unicodedata.normalize("NFD", name)
    name = "".join(c for c in name if unicodedata.category(c) != "Mn")
    name = name.lower()
    # Remove common suffixes
    for suffix in [" llc", " inc", " pc", " pa", " pllc", " md", " do",
                   " associates", " & associates", " group", " practice"]:
        name = name.replace(suffix, "")
    return re.sub(r"[^a-z0-9 ]", "", name).strip()


def normalize_phone(phone: str) -> str:
    """Normalize phone to 10 digits."""
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    return digits if len(digits) == 10 else ""


def domain_of(url: str) -> str:
    """Extract root domain."""
    try:
        host = urlparse(url).hostname or ""
        parts = host.split(".")
        if len(parts) >= 2:
            if parts[-2] in ("co", "com", "org", "net"):
                return ".".join(parts[-3:]) if len(parts) >= 3 else host
            return ".".join(parts[-2:])
        return host
    except Exception:
        return ""


def deduplicate_practices(all_results: list[dict]) -> list[dict]:
    """Three-layer deduplication: place_id -> domain -> name+city."""
    # Layer 1: place_id
    by_pid = {}
    no_pid = []
    for r in all_results:
        pid = r.get("place_id", "")
        if pid:
            if pid in by_pid:
                by_pid[pid]["_hit_count"] = by_pid[pid].get("_hit_count", 1) + 1
                # Merge missing fields
                for k, v in r.items():
                    if k not in by_pid[pid] or not by_pid[pid][k]:
                        by_pid[pid][k] = v
            else:
                r["_hit_count"] = 1
                by_pid[pid] = r
        else:
            no_pid.append(r)

    practices = list(by_pid.values())

    # Layer 2: domain match (merge no_pid and cross-check)
    by_domain = {}
    for p in practices:
        url = p.get("website", p.get("url", ""))
        d = domain_of(url)
        if d and d not in AGGREGATOR_DOMAINS:
            if d in by_domain:
                by_domain[d]["_hit_count"] = by_domain[d].get("_hit_count", 1) + 1
            else:
                by_domain[d] = p
                practices  # already in list

    # Layer 3: name + city fuzzy match
    # (simplified: just check normalized name equality within same city)
    seen = set()
    unique = []
    for p in practices:
        name = normalize_name(p.get("title", p.get("name", "")))
        city = (p.get("city", "") or "").lower().strip()
        key = f"{name}|{city}"
        if key and key not in seen:
            seen.add(key)
            unique.append(p)

    return unique
```

## Phase 3: Enrichment (missing domains)

```python
async def enrich_missing_domains(client: httpx.AsyncClient,
                                  practices: list[dict],
                                  vertical: str,
                                  sem: asyncio.Semaphore) -> list[dict]:
    """Search for website URLs for practices that don't have one."""
    to_enrich = [p for p in practices if not domain_of(p.get("website", p.get("url", "")))]
    print(f"\n  Enriching {len(to_enrich)} practices missing domains...", flush=True)

    async def search_domain(practice):
        name = practice.get("title", practice.get("name", ""))
        city = practice.get("city", "")
        state = practice.get("state", "")
        query = f'"{name}" {city} {state} {vertical} website'

        results = await search_metro_query(client, query, sem)
        for r in results:
            url = r.get("url", "")
            if url and not domain_of(url) in AGGREGATOR_DOMAINS:
                practice["website"] = url
                practice["_enriched_domain"] = True
                break
        return practice

    tasks = [search_domain(p) for p in to_enrich]
    await asyncio.gather(*tasks)

    enriched = sum(1 for p in to_enrich if p.get("_enriched_domain"))
    print(f"  Found domains for {enriched}/{len(to_enrich)} practices", flush=True)
    return practices
```

## Phase 4: Audit

```python
def load_reference_list(path: str) -> list[dict]:
    """Load reference list from CSV or JSON."""
    if path.endswith(".csv"):
        with open(path) as f:
            return list(csv.DictReader(f))
    elif path.endswith(".json"):
        with open(path) as f:
            return json.load(f)
    else:
        print(f"  Unsupported reference format: {path}", flush=True)
        return []


def audit_against_reference(discovered: list[dict], reference: list[dict]) -> dict:
    """Compare discovered practices against a reference list.

    Returns: {
        "matched": [(discovered, reference)],
        "discovered_only": [discovered],
        "reference_only": [reference],
    }
    """
    # Build reference indexes
    ref_by_domain = {}
    ref_by_name_city = {}
    ref_by_phone = {}

    for ref in reference:
        url = ref.get("url", ref.get("website", ref.get("domain", "")))
        d = domain_of(url)
        if d:
            ref_by_domain[d] = ref

        name = normalize_name(ref.get("practice_name", ref.get("name", "")))
        city = (ref.get("city", "") or "").lower().strip()
        if name and city:
            ref_by_name_city[f"{name}|{city}"] = ref

        phone = normalize_phone(ref.get("phone", ""))
        if phone:
            ref_by_phone[phone] = ref

    matched = []
    discovered_only = []
    matched_ref_ids = set()

    for disc in discovered:
        disc_url = disc.get("website", disc.get("url", ""))
        disc_domain = domain_of(disc_url)
        disc_name = normalize_name(disc.get("title", disc.get("name", "")))
        disc_city = (disc.get("city", "") or "").lower().strip()
        disc_phone = normalize_phone(disc.get("phone", ""))

        match = None

        # Try domain match
        if disc_domain and disc_domain in ref_by_domain:
            match = ref_by_domain[disc_domain]
        # Try name + city
        elif f"{disc_name}|{disc_city}" in ref_by_name_city:
            match = ref_by_name_city[f"{disc_name}|{disc_city}"]
        # Try phone
        elif disc_phone and disc_phone in ref_by_phone:
            match = ref_by_phone[disc_phone]

        if match:
            matched.append((disc, match))
            matched_ref_ids.add(id(match))
        else:
            discovered_only.append(disc)

    reference_only = [r for r in reference if id(r) not in matched_ref_ids]

    return {
        "matched": matched,
        "discovered_only": discovered_only,
        "reference_only": reference_only,
    }
```

## Phase 5: Export

```python
def normalize_practice(raw: dict) -> dict:
    """Normalize a raw result into the output schema."""
    address = raw.get("address", raw.get("full_address", ""))
    city = raw.get("city", "")
    state = raw.get("state", "")
    zip_code = raw.get("zip", raw.get("postal_code", ""))

    # Try to parse city/state/zip from address if not available
    if not city and address:
        parts = address.split(",")
        if len(parts) >= 2:
            city = parts[-2].strip().split()[0] if parts[-2].strip() else ""

    url = raw.get("website", raw.get("url", ""))

    return {
        "place_id": raw.get("place_id", ""),
        "practice_name": (raw.get("title") or raw.get("name") or "").strip(),
        "street_address": (raw.get("street_address", "") or "").strip(),
        "city": city,
        "state": state,
        "zip": zip_code,
        "full_address": address,
        "lat": raw.get("latitude", raw.get("lat", 0)),
        "lng": raw.get("longitude", raw.get("lng", 0)),
        "phone": (raw.get("phone", "") or "").strip(),
        "domain": domain_of(url),
        "website_url": url,
        "rating": float(raw.get("rating", 0) or 0),
        "review_count": int(raw.get("review_count", raw.get("reviews", 0)) or 0),
        "primary_category": (raw.get("category", raw.get("type", "")) or "").strip(),
        "all_categories": raw.get("categories", ""),
        "query_hit_count": raw.get("_hit_count", 1),
        "metro": raw.get("_metro", ""),
        "audit_status": "",
    }
```

## Google Sheets Setup

Use the same `load_google_credentials()` and sheet helpers from the
find-all-locations `enrichment-template.md`, adapted for the market
discovery schema.

## CLI Arguments (for batched execution)

```python
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vertical", required=True)
    parser.add_argument("--states", help="Comma-separated state codes (e.g., CA,NY,TX)")
    parser.add_argument("--reference", help="Path to reference list CSV/JSON for audit")
    parser.add_argument("--sheet-url", help="Existing sheet URL for resume")
    return parser.parse_args()
```

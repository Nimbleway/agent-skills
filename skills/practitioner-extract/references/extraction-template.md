# Extraction Template

Python code template for the practitioner extraction pipeline.

## Dependencies

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx", "gspread", "google-auth", "google-auth-oauthlib"]
# ///
```

## Imports

```python
import asyncio
import csv
import json
import os
import re
import sys
import time
import unicodedata
from datetime import datetime
from urllib.parse import urljoin, urlparse

import httpx
```

## Constants

```python
NIMBLE_API_KEY = os.environ.get("NIMBLE_API_KEY", "")
MAP_API_URL = "https://sdk.nimbleway.com/v1/map"
EXTRACT_API_URL = "https://sdk.nimbleway.com/v1/url/extract"

MAX_RETRIES = 3
RETRY_BACKOFF = [2, 5, 15]
BATCH_WRITE_SIZE = 25

MAP_CONCURRENCY = 10
EXTRACT_CONCURRENCY = 8
```

## Credential & Specialty Patterns

```python
CREDENTIAL_PATTERN = re.compile(
    r'\b(M\.?D\.?|D\.?O\.?|O\.?D\.?|Ph\.?D\.?|F\.?A\.?C\.?S\.?|'
    r'F\.?A\.?A\.?O\.?|M\.?B\.?A\.?|M\.?P\.?H\.?|M\.?S\.?|'
    r'D\.?P\.?M\.?|P\.?A\.?[\-\s]?C?\.?|N\.?P\.?|R\.?N\.?|'
    r'C\.?N\.?P\.?|D\.?N\.?P\.?|F\.?A\.?C\.?P\.?)\b',
    re.IGNORECASE
)

# Ophthalmology specialties (extend for other verticals)
SPECIALTY_KEYWORDS = {
    "retina": ["retina", "vitreoretinal", "macular degeneration", "diabetic eye"],
    "glaucoma": ["glaucoma"],
    "cataract": ["cataract", "lens implant", "iol", "intraocular"],
    "cornea": ["cornea", "corneal", "external disease", "keratoconus"],
    "oculoplastics": ["oculoplastic", "orbital", "eyelid", "lacrimal", "cosmetic eye"],
    "pediatric": ["pediatric", "strabismus", "amblyopia", "children"],
    "neuro-ophthalmology": ["neuro-ophthalmology", "neuro-ophthalmic"],
    "refractive": ["lasik", "refractive", "prk", "smile", "vision correction"],
    "comprehensive": ["comprehensive", "general ophthalmology"],
    "optometry": ["optometry", "optometrist", "optometric"],
}

TITLE_KEYWORDS = [
    "medical director", "chief", "founder", "partner", "associate",
    "attending", "surgeon", "director", "president", "chair",
]
```

## Provider Page Scoring

```python
PROVIDER_URL_PATTERNS = {
    # pattern: score
    r"/(our-?)?(providers?|doctors?|physicians?|team)": 10,
    r"/meet-(our|the)-(doctors?|team|providers?)": 10,
    r"/find-a-(doctor|provider)": 10,
    r"/provider-directory": 10,
    r"/(our-?)?(staff|people|specialists?|clinicians?)": 7,
    r"/about/(team|providers?|staff)": 7,
    r"/dr[.-]": 8,
    r"/doctor[.-]": 8,
    r"/providers?/[a-z]": 8,
    r"/doctors?/[a-z]": 8,
    r"/team/[a-z]": 8,
    r"/(retina|glaucoma|cataract|cornea|lasik|oculoplastic)": 5,
    r"/services?/": 3,
    r"/locations?/": 3,
}

def score_provider_url(url: str) -> int:
    """Score a URL for likelihood of containing practitioner data."""
    path = urlparse(url).path.lower()
    best_score = 0
    for pattern, score in PROVIDER_URL_PATTERNS.items():
        if re.search(pattern, path):
            best_score = max(best_score, score)
    # Always include homepage as fallback (score 1)
    if path in ("/", "/index.html", "/index.php", ""):
        best_score = max(best_score, 1)
    return best_score
```

## Practitioner Parsing

```python
def extract_practitioners_from_markdown(markdown: str, practice_name: str,
                                         practice_url: str, source_page: str) -> list[dict]:
    """Parse practitioner records from extracted markdown content.

    Uses multiple strategies to find provider data in the page content.
    """
    practitioners = []

    # Strategy 1: "Name, Credentials" pattern (most common)
    # Matches: "John Smith, MD", "Dr. Jane Doe, MD, FACS", "Sarah Lee, OD"
    name_cred_pattern = re.compile(
        r'(?:#{1,4}\s+)?(?:Dr\.?\s+)?([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
        r',?\s*(' + CREDENTIAL_PATTERN.pattern + r'(?:[,\s/]+' + CREDENTIAL_PATTERN.pattern + r')*)',
        re.MULTILINE
    )

    seen_names = set()
    for match in name_cred_pattern.finditer(markdown):
        name = match.group(1).strip()
        creds = match.group(2).strip().rstrip(",. ")

        # Deduplicate
        name_key = re.sub(r'[^a-z]', '', name.lower())
        if name_key in seen_names or len(name_key) < 4:
            continue
        seen_names.add(name_key)

        # Extract surrounding context (200 chars after the match)
        context_start = match.end()
        context = markdown[context_start:context_start + 500]

        practitioner = {
            "practice_name": practice_name,
            "practice_url": practice_url,
            "practitioner_name": name,
            "credentials": creds,
            "specialty": detect_specialty(context),
            "subspecialty": "",
            "title": detect_title(context),
            "office_location": "",
            "phone": extract_phone(context),
            "email": extract_email(context),
            "bio_url": extract_bio_link(context, source_page),
            "photo_url": "",
            "appointment_url": "",
            "patient_portal_url": "",
            "source_page": source_page,
            "extraction_confidence": "medium",
        }

        # Confidence scoring
        filled = sum(1 for v in [creds, practitioner["specialty"],
                                  practitioner["phone"], practitioner["bio_url"]]
                     if v)
        if filled >= 3:
            practitioner["extraction_confidence"] = "high"
        elif filled <= 1:
            practitioner["extraction_confidence"] = "low"

        practitioners.append(practitioner)

    return practitioners


def detect_specialty(context: str) -> str:
    """Detect specialty from surrounding text context."""
    context_lower = context.lower()
    for specialty, keywords in SPECIALTY_KEYWORDS.items():
        for kw in keywords:
            if kw in context_lower:
                return specialty
    return ""


def detect_title(context: str) -> str:
    """Detect professional title from surrounding text."""
    context_lower = context.lower()
    for title in TITLE_KEYWORDS:
        if title in context_lower:
            return title.title()
    return ""


def extract_phone(text: str) -> str:
    """Extract first phone number from text."""
    match = re.search(r'(\+?1?\s*[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})', text)
    if match:
        digits = re.sub(r'\D', '', match.group(1))
        if 10 <= len(digits) <= 11:
            return match.group(1).strip()
    return ""


def extract_email(text: str) -> str:
    """Extract first non-generic email from text."""
    match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    if match:
        email = match.group(0).lower()
        generic = ("noreply", "postmaster", "admin", "info@", "support@",
                   "contact@", "webmaster", "hello@", "office@")
        if not any(email.startswith(g) for g in generic):
            return email
    return ""


def extract_bio_link(text: str, base_url: str) -> str:
    """Extract a link to individual bio page from context."""
    link_pattern = re.compile(r'\[([^\]]*)\]\(([^)]+)\)')
    for match in link_pattern.finditer(text[:300]):
        href = match.group(2)
        if any(kw in href.lower() for kw in ("/dr", "/doctor", "/provider", "/team/")):
            return urljoin(base_url, href)
    return ""
```

## Retry Helper

```python
async def with_retry(fn, label: str, max_retries=MAX_RETRIES):
    for attempt in range(max_retries + 1):
        try:
            return await fn()
        except (httpx.HTTPStatusError, httpx.TimeoutException, httpx.ConnectError) as e:
            if attempt == max_retries:
                raise
            delay = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
            print(f"  Retry {attempt+1}/{max_retries} for {label} after {delay}s: {e}", flush=True)
            await asyncio.sleep(delay)
```

## Phase 1: Site Mapping

```python
async def map_site(client: httpx.AsyncClient, url: str, sem: asyncio.Semaphore) -> list[dict]:
    """Map a practice site to discover all pages."""
    async with sem:
        headers = {
            "Authorization": f"Bearer {NIMBLE_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {"url": url, "limit": 50}

        async def _do():
            resp = await client.post(MAP_API_URL, json=payload, headers=headers, timeout=60)
            resp.raise_for_status()
            return resp.json()

        try:
            data = await with_retry(_do, f"map:{urlparse(url).hostname}")
            urls = data.get("urls", data.get("data", {}).get("urls", []))
            if isinstance(urls, list):
                return [{"url": u, "score": score_provider_url(u)} for u in urls if isinstance(u, str)]
        except Exception as e:
            print(f"  MAP FAIL {url}: {e}", flush=True)
        return []
```

## Phase 2: Page Extraction

```python
async def extract_page(client: httpx.AsyncClient, url: str, sem: asyncio.Semaphore) -> str:
    """Extract page content as markdown."""
    async with sem:
        headers = {
            "Authorization": f"Bearer {NIMBLE_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {"url": url, "format": "markdown"}

        async def _do():
            resp = await client.post(EXTRACT_API_URL, json=payload, headers=headers, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", {}).get("markdown", data.get("markdown", ""))

        try:
            md = await with_retry(_do, f"extract:{url[:60]}")
            if md and len(md) > 100:
                return md
            # Retry with render
            payload["render"] = True
            md = await with_retry(_do, f"extract-render:{url[:60]}")
            return md or ""
        except Exception as e:
            print(f"  EXTRACT FAIL {url}: {e}", flush=True)
            return ""
```

## Google Sheets I/O

Use the same `load_google_credentials()`, `ensure_columns()`, `write_batch()`,
and `upsert_rows()` functions from the find-all-locations `enrichment-template.md`.

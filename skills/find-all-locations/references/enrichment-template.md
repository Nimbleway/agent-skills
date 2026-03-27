# Enrichment Template

Parameterized Python code for Phases 2-4 of the find-all-locations pipeline. Adapted from `~/enrich_restaurants.py` and `~/find_instagram.py`.

When generating the master pipeline script, inline these code blocks into the appropriate phases. All functions use the same Google Sheets I/O, retry helpers, and name-matching utilities.

## Dependencies

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx", "gspread", "google-auth", "google-auth-oauthlib", "nimble_python"]
# ///
```

## System-of-Record Schema

```python
# Primary key: place_id (Google's stable unique identifier)
# On rerun: merge by place_id, update only empty/stale fields
# Sheet is canonical — script reads Sheet to determine what's already done

ENRICHMENT_COLUMNS = [
    # Phase 2: Search enrichment
    "website_url", "instagram_url", "facebook_url",
    "enrichment_status", "enrichment_notes",
    # Phase 3: Social discovery + verification
    "social_status",
    "instagram_verified", "instagram_confidence",
    "instagram_match_reason", "instagram_evidence",
    "facebook_verified", "facebook_confidence",
    "facebook_match_reason", "facebook_evidence",
    "tiktok_url", "tiktok_verified", "tiktok_confidence",
    "tiktok_match_reason", "tiktok_evidence",
    "social_error",
    # Phase 4: Website crawl
    "crawl_status", "crawl_timestamp",
    "crawl_phone", "crawl_email", "crawl_hours",
    "crawl_menu_url", "crawl_reservation_url",
    "crawl_pages_visited", "crawl_raw_text_length",
    "crawl_error",
]
```

## Resume System (Sheet-Canonical)

```python
def get_pending_place_ids(rows, phase_status_col):
    """Return place_ids that need processing for a given phase."""
    return [
        row["place_id"] for row in rows
        if row.get(phase_status_col, "").strip().lower() not in ("done", "skipped")
    ]

# Discovery resume: read coverage tab -> re-run jobs where status != "done"
# Enrichment resume: read master tab -> process where enrichment_status not in (done, skipped)
# Social resume: read master tab -> process where social_status not in (done, skipped)
#   BUT also retry where *_confidence == "low" (may improve with new data)
# Crawl resume: read master tab -> process where crawl_status not in (done, skipped)
```

## Upsert Helper

```python
def upsert_rows(ws, rows_data, col_map, key_col="place_id"):
    """Update existing rows by place_id or append new ones.

    Reads current place_ids from Sheet to build a row-number index.
    Updates in-place for existing rows; appends new rows at the end.
    """
    all_values = ws.get_all_values()
    headers = all_values[0] if all_values else []
    key_col_idx = headers.index(key_col) if key_col in headers else -1
    if key_col_idx < 0:
        return

    existing = {}
    for row_num, row_vals in enumerate(all_values[1:], start=2):
        if key_col_idx < len(row_vals):
            pid = row_vals[key_col_idx].strip()
            if pid:
                existing[pid] = row_num

    updates = []
    appends = []
    for data in rows_data:
        pid = data.get(key_col, "")
        if pid in existing:
            updates.append((existing[pid], data))
        else:
            appends.append(data)

    if updates:
        write_batch(ws, updates, col_map)
    if appends:
        import gspread
        for data in appends:
            row_values = [""] * len(headers)
            for col_name, value in data.items():
                if col_name in col_map:
                    idx = col_map[col_name] - 1
                    if idx < len(row_values):
                        row_values[idx] = str(value)
            ws.append_row(row_values, value_input_option="RAW")
```

## Shared Utilities

```python
SEARCH_API_URL = "https://sdk.nimbleway.com/v1/search"

AGGREGATOR_DOMAINS = {
    "yelp.com", "tripadvisor.com", "grubhub.com", "doordash.com",
    "ubereats.com", "seamless.com", "opentable.com", "google.com",
    "facebook.com", "instagram.com", "twitter.com", "tiktok.com",
    "foursquare.com", "zomato.com", "menupages.com", "allmenus.com",
    "postmates.com", "caviar.com", "eater.com", "timeout.com",
    "thrillist.com", "infatuation.com", "yelp.ca",
}

MAX_RETRIES = 3
RETRY_BACKOFF = [2, 5, 15]

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


def normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", strip_accents(name).lower())


def fuzzy_name_match(place_name: str, candidate: str) -> bool:
    """Check if candidate text plausibly refers to the same place."""
    norm_place = normalize_name(place_name)
    norm_cand = normalize_name(candidate)
    if not norm_place or not norm_cand:
        return False
    if norm_place in norm_cand or norm_cand in norm_place:
        return True
    words = re.findall(r"[a-z0-9]+", strip_accents(place_name).lower())
    if not words:
        return False
    matches = sum(1 for w in words if w in norm_cand)
    return matches / len(words) >= 0.6


def domain_of(url: str) -> str:
    """Extract the root domain from a URL."""
    try:
        host = urlparse(url).hostname or ""
        parts = host.split(".")
        if len(parts) >= 2:
            return ".".join(parts[-2:])
        return host
    except Exception:
        return ""


def is_aggregator(url: str) -> bool:
    return domain_of(url) in AGGREGATOR_DOMAINS


def extract_city(address: str) -> str:
    """Extract city name from an address string."""
    parts = address.split(",")
    if len(parts) >= 2:
        return parts[-2].strip().split()[-1] if parts[-2].strip() else ""
    return ""
```

## Google Sheets I/O

```python
def load_google_credentials():
    """Load Google credentials using service account or OAuth."""
    import gspread
    from google.oauth2.credentials import Credentials as OAuthCredentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request

    token_paths = [
        os.path.expanduser("~/.token_enrich.json"),
        os.path.expanduser("~/.agents/skills/nimble-to-sheets/scripts/.token.json"),
    ]

    creds = None
    cred_path = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")

    for tp in token_paths:
        if os.path.isfile(tp):
            try:
                creds = OAuthCredentials.from_authorized_user_file(tp, SCOPES)
                if creds and creds.valid:
                    print(f"Using cached token from {tp}")
                    break
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    print(f"Refreshed cached token from {tp}")
                    break
            except Exception:
                creds = None

    if not creds or not creds.valid:
        if cred_path and os.path.isfile(cred_path):
            with open(cred_path) as f:
                cred_data = json.load(f)
            if cred_data.get("type") == "service_account":
                from google.oauth2.service_account import Credentials as SACredentials
                creds = SACredentials.from_service_account_file(cred_path, scopes=SCOPES)
                print("Using service account credentials")
            elif "installed" in cred_data or "web" in cred_data:
                flow = InstalledAppFlow.from_client_secrets_file(cred_path, SCOPES)
                creds = flow.run_local_server(port=0)
                with open(token_paths[0], "w") as f:
                    f.write(creds.to_json())
                print("OAuth flow completed, token cached")

    if not creds:
        print("FATAL: No valid Google credentials found.")
        print("  Set GOOGLE_SERVICE_ACCOUNT_JSON to a service account key file path.")
        sys.exit(1)

    return gspread.authorize(creds)


def open_sheet(gc, sheet_url: str, worksheet_name: str):
    """Open a Google Sheet by URL and return (spreadsheet, worksheet, headers, rows)."""
    sh = gc.open_by_url(sheet_url)
    try:
        ws = sh.worksheet(worksheet_name)
    except Exception:
        ws = sh.sheet1
        print(f"  Worksheet '{worksheet_name}' not found, using first sheet: '{ws.title}'")

    all_values = ws.get_all_values()
    if not all_values:
        print("FATAL: Sheet is empty.")
        sys.exit(1)

    headers = [h.strip() for h in all_values[0]]
    rows = []
    for row_values in all_values[1:]:
        row = {}
        for i, h in enumerate(headers):
            row[h] = row_values[i] if i < len(row_values) else ""
        rows.append(row)

    print(f"  Loaded {len(rows)} rows, {len(headers)} columns from '{ws.title}'")
    return sh, ws, headers, rows


def ensure_columns(ws, headers: list[str], new_columns: list[str]) -> dict[str, int]:
    """Add missing columns to the sheet. Returns col_name -> 1-based col index."""
    missing = [c for c in new_columns if c not in headers]
    if missing:
        current_cols = ws.col_count
        needed_cols = len(headers) + len(missing)
        if needed_cols > current_cols:
            ws.resize(cols=needed_cols)

        start_col = len(headers) + 1
        import gspread
        cells = []
        for i, col_name in enumerate(missing):
            cells.append(gspread.Cell(1, start_col + i, col_name))
        ws.update_cells(cells, value_input_option="RAW")
        headers.extend(missing)
        print(f"  Added {len(missing)} new columns: {', '.join(missing)}")

    return {h: idx + 1 for idx, h in enumerate(headers)}


def write_batch(ws, updates: list[tuple[int, dict]], col_map: dict[str, int]):
    """Write enrichment results for a batch of rows.
    updates = [(row_number_1based, {col_name: value}), ...]
    """
    import gspread
    if not updates:
        return
    cells = []
    for row_num, data in updates:
        for col_name, value in data.items():
            if col_name in col_map:
                cells.append(gspread.Cell(row_num, col_map[col_name], str(value)))
    if cells:
        ws.update_cells(cells, value_input_option="RAW")
```

## Retry Helper

```python
async def with_retry(fn, label: str, max_retries=MAX_RETRIES):
    """Execute async fn with exponential backoff."""
    for attempt in range(max_retries + 1):
        try:
            return await fn()
        except (httpx.HTTPStatusError, httpx.TimeoutException, httpx.ConnectError) as e:
            if attempt == max_retries:
                raise
            delay = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
            print(f"  Retry {attempt + 1}/{max_retries} for {label} after {delay}s: {e}", flush=True)
            await asyncio.sleep(delay)
```

## Phase 2: Search Enrichment

Search for website, Instagram, and Facebook URLs for each place.

### Core Functions

```python
def get_place_name(row: dict) -> str:
    """Extract place name from row, trying common column names."""
    for key in ("restaurant_name", "place_name", "title", "name"):
        val = row.get(key, "").strip()
        if val:
            return val
    return ""


def get_location(row: dict) -> str:
    """Build location string from row."""
    city = row.get("city", "").strip()
    state = row.get("state", "").strip()
    loc = f"{city} {state}".strip()
    if loc:
        return loc
    address = row.get("address", row.get("full_address", "")).strip()
    if address:
        parts = address.split(",")
        if len(parts) >= 2:
            return parts[-2].strip()
    return ""


def build_search_queries(row: dict) -> list[dict]:
    """Build 3 search queries per place: website, Instagram, Facebook."""
    name = get_place_name(row)
    location = get_location(row)
    return [
        {
            "query": f'"{name}" {location} official website',
            "focus": "general",
            "num_results": 5,
            "deep_search": False,
        },
        {
            "query": f'"{name}" {location} site:instagram.com',
            "focus": "general",
            "num_results": 5,
            "deep_search": False,
        },
        {
            "query": f'"{name}" {location} site:facebook.com',
            "focus": "general",
            "num_results": 5,
            "deep_search": False,
        },
    ]


async def run_search(client: httpx.AsyncClient, query_dict: dict, api_key: str) -> dict:
    """Execute a single Nimble Search API call."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    async def _do():
        resp = await client.post(SEARCH_API_URL, json=query_dict, headers=headers)
        resp.raise_for_status()
        return resp.json()
    return await with_retry(_do, label=f"search: {query_dict['query'][:50]}")


def pick_website_url(results: list[dict], place_name: str) -> tuple[str, str]:
    """Select the best website URL from search results. Returns (url, notes)."""
    if not results:
        return "", "no results"

    candidates = [r for r in results if not is_aggregator(r.get("url", ""))]
    if not candidates:
        return "", "all results are aggregators"

    scored = []
    for r in candidates:
        url = r.get("url", "")
        title = r.get("title", "")
        score = 0
        if fuzzy_name_match(place_name, title):
            score += 10
        if fuzzy_name_match(place_name, url):
            score += 5
        path = urlparse(url).path.strip("/")
        if not path:
            score += 3
        elif path.count("/") <= 1:
            score += 1
        scored.append((score, url, title))

    scored.sort(key=lambda x: -x[0])
    best_url = scored[0][1]
    notes = "website: rank 1"
    if len(scored) >= 2 and scored[0][0] == scored[1][0]:
        tied = sum(1 for s in scored if s[0] == scored[0][0])
        notes = f"ambiguous: {tied} candidates"
    return best_url, notes


def pick_social_url(results: list[dict], platform: str, place_name: str) -> str:
    """Select the best social media URL for a platform."""
    if not results:
        return ""

    for r in results:
        url = r.get("url", "")
        title = r.get("title", "")

        if platform == "instagram":
            if "instagram.com/" not in url:
                continue
            path = urlparse(url).path.strip("/")
            parts = path.split("/")
            if len(parts) >= 1 and parts[0] not in ("p", "reel", "stories", "explore"):
                if fuzzy_name_match(place_name, title) or fuzzy_name_match(place_name, parts[0]):
                    return url

        elif platform == "facebook":
            if "facebook.com/" not in url:
                continue
            path = urlparse(url).path.strip("/")
            parts = path.split("/")
            if parts and parts[0] not in ("events", "posts", "photos", "videos", "groups"):
                if fuzzy_name_match(place_name, title) or fuzzy_name_match(place_name, parts[0]):
                    return url

    # Fallback: first result matching platform domain
    for r in results:
        url = r.get("url", "")
        if platform in url:
            return url
    return ""


async def enrich_one_row(client, api_key, row, semaphore):
    """Search-enrich a single place. Returns enrichment dict."""
    async with semaphore:
        name = get_place_name(row)
        if not name:
            return {"enrichment_status": "error", "enrichment_notes": "no place name found"}

        queries = build_search_queries(row)
        notes_parts = []

        try:
            results = await asyncio.gather(
                run_search(client, queries[0], api_key),
                run_search(client, queries[1], api_key),
                run_search(client, queries[2], api_key),
                return_exceptions=True,
            )
        except Exception as e:
            return {"enrichment_status": "error", "enrichment_notes": str(e)[:200]}

        # Website
        web_results = results[0].get("results", []) if isinstance(results[0], dict) else []
        if isinstance(results[0], Exception):
            notes_parts.append(f"web error: {results[0]}")
        website_url, web_notes = pick_website_url(web_results, name)
        notes_parts.append(web_notes)

        # Fallback website search
        if not website_url and not isinstance(results[0], Exception):
            location = get_location(row)
            fallback_q = {"query": f"{name} {location} {PLACE_TYPE}", "focus": "general",
                          "num_results": 5, "deep_search": False}
            try:
                fallback = await run_search(client, fallback_q, api_key)
                website_url, web_notes = pick_website_url(fallback.get("results", []), name)
                if website_url:
                    notes_parts.append(f"website via fallback: {web_notes}")
            except Exception as e:
                notes_parts.append(f"fallback error: {e}")

        # Instagram
        ig_results = results[1].get("results", []) if isinstance(results[1], dict) else []
        if isinstance(results[1], Exception):
            notes_parts.append(f"ig error: {results[1]}")
        ig_url = pick_social_url(ig_results, "instagram", name)

        # Facebook
        fb_results = results[2].get("results", []) if isinstance(results[2], dict) else []
        if isinstance(results[2], Exception):
            notes_parts.append(f"fb error: {results[2]}")
        fb_url = pick_social_url(fb_results, "facebook", name)

        status = "found" if (website_url and (ig_url or fb_url)) else "partial" if (website_url or ig_url or fb_url) else "not_found"

        return {
            "website_url": website_url,
            "instagram_url": ig_url,
            "facebook_url": fb_url,
            "enrichment_status": status,
            "enrichment_notes": "; ".join(notes_parts),
        }
```

### Phase 2 Pipeline Runner

```python
async def phase2_search_enrichment(client, api_key, ws, rows, col_map, concurrency=20, batch_size=25):
    """Run Phase 2: Search enrichment for all rows needing it."""
    semaphore = asyncio.Semaphore(concurrency)
    pending_writes = []
    write_lock = asyncio.Lock()
    total = 0; skipped = 0; found = 0; errors = 0; done = 0
    start = time.time()

    tasks = []
    for idx, row in enumerate(rows):
        row_num = idx + 2
        status = row.get("enrichment_status", "").strip().lower()
        if status in ("found", "partial", "not_found", "skipped"):
            skipped += 1
            continue
        total += 1
        tasks.append((row_num, idx, row))

    if not tasks:
        print(f"  Phase 2: All {skipped} rows already enriched. Skipping.")
        return
    print(f"  Phase 2: {total} rows to enrich, {skipped} already done")

    async def process_one(row_num, idx, row):
        nonlocal done, found, errors
        try:
            result = await enrich_one_row(client, api_key, row, semaphore)
        except Exception as e:
            result = {"enrichment_status": "error", "enrichment_notes": str(e)[:200]}

        for k, v in result.items():
            rows[idx][k] = v
        if result.get("enrichment_status") in ("found", "partial"):
            found += 1
        elif result.get("enrichment_status") == "error":
            errors += 1
        done += 1

        batch_to_write = None
        async with write_lock:
            pending_writes.append((row_num, result))
            if len(pending_writes) >= batch_size:
                batch_to_write = pending_writes[:]
                pending_writes.clear()
        if batch_to_write:
            write_batch(ws, batch_to_write, col_map)

        if done % 10 == 0 or done == total:
            elapsed = time.time() - start
            print(f"  [{elapsed:>5.0f}s] Phase 2: {done}/{total} | {found} found | {errors} errors", flush=True)

    await asyncio.gather(*(process_one(rn, idx, row) for rn, idx, row in tasks))
    if pending_writes:
        write_batch(ws, pending_writes, col_map)

    elapsed = time.time() - start
    print(f"  Phase 2 complete: {done} rows in {elapsed:.0f}s | {found} found | {errors} errors")
```

## Phase 3: Social Discovery + Verification

Enhanced social search with confidence scoring.

### Social Search Functions

```python
async def search_social_platform(client, api_key, name, location, platform):
    """Search for a social profile using 3-strategy fallback.
    platform: 'instagram' or 'facebook'
    """
    site_domain = "instagram.com" if platform == "instagram" else "facebook.com"
    strategies = [
        f'"{name}" {location} site:{site_domain}',
        f'{name} {location} site:{site_domain}',
        f'{name} {location} {site_domain}',
    ]

    for i, query in enumerate(strategies):
        try:
            result = await run_search(client, {
                "query": query, "num_results": 5, "deep_search": False,
            }, api_key)
            results = result.get("results", [])
            if any(site_domain in r.get("url", "") for r in results):
                return results
        except Exception:
            continue
    return []


async def search_tiktok(client, api_key, name, neighborhood):
    """Search for TikTok profile using discover_users then search_posts fallback."""
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    # Primary: discover users
    try:
        async def _discover():
            resp = await client.post("https://sdk.nimbleway.com/v1/social/tiktok/discover_users",
                json={"query": name, "num_results": 5}, headers=headers)
            resp.raise_for_status()
            return resp.json()
        result = await with_retry(_discover, label=f"tiktok_discover: {name[:40]}")
        users = result.get("users", result.get("results", []))
        if users:
            return [{"url": u.get("profile_url", u.get("url", "")),
                      "title": u.get("nickname", u.get("title", "")),
                      "bio": u.get("bio", u.get("description", ""))} for u in users]
    except Exception:
        pass

    # Fallback: search posts, extract author
    try:
        async def _search_posts():
            resp = await client.post("https://sdk.nimbleway.com/v1/social/tiktok/search_posts",
                json={"query": f"{name} {neighborhood}", "num_results": 5}, headers=headers)
            resp.raise_for_status()
            return resp.json()
        result = await with_retry(_search_posts, label=f"tiktok_posts: {name[:40]}")
        posts = result.get("posts", result.get("results", []))
        seen = set()
        authors = []
        for p in posts:
            author_url = p.get("author_url", p.get("author", {}).get("url", ""))
            author_name = p.get("author_name", p.get("author", {}).get("nickname", ""))
            if author_url and author_url not in seen:
                seen.add(author_url)
                authors.append({"url": author_url, "title": author_name, "bio": ""})
        return authors
    except Exception:
        return []


def is_profile_page(url):
    """Check if URL is a profile page (not a post/reel/event)."""
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    parts = path.split("/")
    host = parsed.hostname or ""

    if "instagram.com" in host:
        return len(parts) == 1 and parts[0] not in ("p", "reel", "stories", "explore", "accounts", "directory")
    if "facebook.com" in host:
        return not (len(parts) >= 2 and parts[-1] in ("events", "posts", "photos", "videos", "groups", "reviews"))
    if "tiktok.com" in host:
        return len(parts) == 1 and parts[0].startswith("@")
    return False


def compute_social_confidence(place_name, place_address, website_url,
                               social_url, social_title, social_bio=""):
    """Score confidence that a social profile belongs to this place."""
    score = 0
    reasons = []
    evidence = []

    if website_url:
        website_domain = domain_of(website_url)
        if website_domain and website_domain in (social_bio or ""):
            score += 60
            reasons.append("domain_match")
            evidence.append(f"bio_links_to:{website_domain}")

    if fuzzy_name_match(place_name, social_title):
        score += 40
        reasons.append("name_match_title")
        evidence.append(f"title:{social_title[:40]}")

    path = urlparse(social_url).path.strip("/").split("/")[0]
    if fuzzy_name_match(place_name, path):
        score += 30
        reasons.append("name_match_url")
        evidence.append(f"path:/{path}")

    city = extract_city(place_address)
    if city and city.lower() in (social_bio or "").lower():
        score += 20
        reasons.append("location_match")
        evidence.append(f"bio_contains:{city}")

    if is_profile_page(social_url):
        score += 10
        reasons.append("profile_page")

    if score >= 70:
        confidence = "high"
    elif score >= 40:
        confidence = "medium"
    else:
        confidence = "low"

    return confidence, "; ".join(reasons), " | ".join(evidence)


def pick_best_social(results, platform, place_name, place_address, website_url):
    """Pick the best social URL from results and compute confidence."""
    site_domain = {"instagram": "instagram.com", "facebook": "facebook.com", "tiktok": "tiktok.com"}.get(platform, "")

    best_url = ""
    best_confidence = "low"
    best_reasons = ""
    best_evidence = ""
    best_score = -1

    for r in results:
        url = r.get("url", "")
        title = r.get("title", "")
        bio = r.get("bio", r.get("description", r.get("snippet", "")))

        if site_domain and site_domain not in url:
            continue

        conf, reasons, ev = compute_social_confidence(
            place_name, place_address, website_url, url, title, bio)

        conf_score = {"high": 3, "medium": 2, "low": 1}.get(conf, 0)
        profile_bonus = 1 if is_profile_page(url) else 0

        total = conf_score * 10 + profile_bonus
        if total > best_score:
            best_score = total
            best_url = url
            best_confidence = conf
            best_reasons = reasons
            best_evidence = ev

    verified = best_confidence in ("high", "medium") if best_url else False
    return best_url, verified, best_confidence, best_reasons, best_evidence
```

### Phase 3 Pipeline Runner

```python
async def phase3_social_verification(client, api_key, ws, rows, col_map,
                                      neighborhood, concurrency=15, batch_size=25):
    """Run Phase 3: Social discovery + verification with confidence scoring."""
    semaphore = asyncio.Semaphore(concurrency)
    pending_writes = []
    write_lock = asyncio.Lock()
    total = 0; skipped = 0; done = 0; errors = 0
    start = time.time()

    tasks = []
    for idx, row in enumerate(rows):
        row_num = idx + 2
        status = row.get("social_status", "").strip().lower()
        if status == "done":
            # But retry low-confidence matches
            retry = False
            for platform in ("instagram", "facebook", "tiktok"):
                if row.get(f"{platform}_confidence", "").strip().lower() == "low":
                    retry = True
                    break
            if not retry:
                skipped += 1
                continue
        if status == "skipped":
            skipped += 1
            continue
        total += 1
        tasks.append((row_num, idx, row))

    if not tasks:
        print(f"  Phase 3: All {skipped} rows already processed. Skipping.")
        return
    print(f"  Phase 3: {total} rows to process, {skipped} already done")

    async def process_one(row_num, idx, row):
        nonlocal done, errors
        name = get_place_name(row)
        location = get_location(row)
        address = row.get("full_address", row.get("address", ""))
        website_url = row.get("website_url", "").strip()
        result = {"social_status": "done"}

        try:
            async with semaphore:
                # Instagram
                if not row.get("instagram_verified", "").strip().lower() == "true" or \
                   row.get("instagram_confidence", "").strip().lower() == "low":
                    ig_results = await search_social_platform(client, api_key, name, location, "instagram")
                    ig_url, ig_verified, ig_conf, ig_reasons, ig_evidence = \
                        pick_best_social(ig_results, "instagram", name, address, website_url)
                    result.update({
                        "instagram_url": ig_url or row.get("instagram_url", ""),
                        "instagram_verified": str(ig_verified),
                        "instagram_confidence": ig_conf,
                        "instagram_match_reason": ig_reasons,
                        "instagram_evidence": ig_evidence,
                    })

                # Facebook
                if not row.get("facebook_verified", "").strip().lower() == "true" or \
                   row.get("facebook_confidence", "").strip().lower() == "low":
                    fb_results = await search_social_platform(client, api_key, name, location, "facebook")
                    fb_url, fb_verified, fb_conf, fb_reasons, fb_evidence = \
                        pick_best_social(fb_results, "facebook", name, address, website_url)
                    result.update({
                        "facebook_url": fb_url or row.get("facebook_url", ""),
                        "facebook_verified": str(fb_verified),
                        "facebook_confidence": fb_conf,
                        "facebook_match_reason": fb_reasons,
                        "facebook_evidence": fb_evidence,
                    })

                # TikTok
                if not row.get("tiktok_verified", "").strip().lower() == "true" or \
                   row.get("tiktok_confidence", "").strip().lower() == "low":
                    tk_results = await search_tiktok(client, api_key, name, neighborhood)
                    tk_url, tk_verified, tk_conf, tk_reasons, tk_evidence = \
                        pick_best_social(tk_results, "tiktok", name, address, website_url)
                    result.update({
                        "tiktok_url": tk_url or row.get("tiktok_url", ""),
                        "tiktok_verified": str(tk_verified),
                        "tiktok_confidence": tk_conf,
                        "tiktok_match_reason": tk_reasons,
                        "tiktok_evidence": tk_evidence,
                    })

        except Exception as e:
            result["social_status"] = "error"
            result["social_error"] = str(e)[:200]
            errors += 1

        for k, v in result.items():
            rows[idx][k] = v
        done += 1

        batch_to_write = None
        async with write_lock:
            pending_writes.append((row_num, result))
            if len(pending_writes) >= batch_size:
                batch_to_write = pending_writes[:]
                pending_writes.clear()
        if batch_to_write:
            write_batch(ws, batch_to_write, col_map)

        if done % 10 == 0 or done == total:
            elapsed = time.time() - start
            print(f"  [{elapsed:>5.0f}s] Phase 3: {done}/{total} | {errors} errors", flush=True)

    await asyncio.gather(*(process_one(rn, idx, row) for rn, idx, row in tasks))
    if pending_writes:
        write_batch(ws, pending_writes, col_map)

    elapsed = time.time() - start
    print(f"  Phase 3 complete: {done} rows in {elapsed:.0f}s | {errors} errors")
```

## Phase 4: Website Crawl

Extract contact data from each place's website using Nimble URL Extract.

### Core Functions

```python
NIMBLE_EXTRACT_URL = "https://sdk.nimbleway.com/v1/url/extract"

PHONE_RE = re.compile(r"(\+?1?\s*[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})")
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
GENERIC_EMAIL_PREFIXES = {"noreply", "no-reply", "mailer-daemon", "postmaster", "admin"}
HOURS_KEYWORDS = ["hours", "open", "schedule", "monday", "tuesday", "wednesday",
                  "thursday", "friday", "saturday", "sunday", "mon-", "tue-", "wed-"]
MENU_KEYWORDS = ["menu", "/menu", "food-menu", "our-menu", "dinner-menu", "lunch-menu"]
RESERVATION_KEYWORDS = ["reserv", "book a table", "opentable.com", "resy.com",
                        "yelp.com/reservations", "booking", "book-a-table"]


async def nimble_url_extract(client, api_key, url, format="markdown"):
    """Extract content from a URL using Nimble URL Extract API."""
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {"url": url, "format": format}
    async def _do():
        resp = await client.post(NIMBLE_EXTRACT_URL, json=body, headers=headers, timeout=60.0)
        resp.raise_for_status()
        data = resp.json()
        return data.get("content", data.get("text", data.get("markdown", "")))
    try:
        return await with_retry(_do, label=f"extract: {url[:60]}")
    except Exception:
        return ""


def extract_nav_links(homepage_content, base_url):
    """Find menu/contact/about/hours links from homepage content."""
    keywords = ["menu", "contact", "about", "hours", "reserv", "book",
                "location", "order", "catering"]
    link_re = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    found = []
    for text, url in link_re.findall(homepage_content):
        if any(kw in text.lower() or kw in url.lower() for kw in keywords):
            resolved = resolve_url(url, base_url)
            if resolved:
                found.append(resolved)
    return list(dict.fromkeys(found))  # dedupe, preserve order


def resolve_url(url, base_url):
    """Resolve a potentially relative URL against a base URL."""
    if url.startswith("http"):
        return url
    if url.startswith("/"):
        parsed = urlparse(base_url)
        return f"{parsed.scheme}://{parsed.netloc}{url}"
    if url.startswith("#") or url.startswith("mailto:") or url.startswith("tel:"):
        return ""
    parsed = urlparse(base_url)
    base_path = parsed.path.rsplit("/", 1)[0]
    return f"{parsed.scheme}://{parsed.netloc}{base_path}/{url}"


def parse_phone(content: str) -> str:
    matches = PHONE_RE.findall(content)
    for m in matches:
        digits = re.sub(r"\D", "", m)
        if 10 <= len(digits) <= 11:
            return m.strip()
    return ""


def parse_email(content: str) -> str:
    matches = EMAIL_RE.findall(content)
    if not matches:
        return ""
    valid = []
    for email in matches:
        local = email.split("@")[0].lower()
        ext = email.rsplit(".", 1)[-1].lower()
        if ext in ("png", "jpg", "jpeg", "gif", "svg", "webp"):
            continue
        if local in GENERIC_EMAIL_PREFIXES:
            continue
        valid.append(email)
    if not valid:
        return matches[0] if matches else ""
    preferred_prefixes = ["contact", "hello", "reservations", "info", "dine", "eat"]
    for prefix in preferred_prefixes:
        for email in valid:
            if email.split("@")[0].lower().startswith(prefix):
                return email
    return valid[0]


def parse_hours(content: str) -> str:
    lines = content.split("\n")
    hours_lines = []
    capturing = False
    for line in lines:
        line_lower = line.lower().strip()
        if not line_lower:
            if capturing and hours_lines:
                break
            continue
        if any(kw in line_lower for kw in HOURS_KEYWORDS):
            capturing = True
            hours_lines.append(line.strip())
        elif capturing:
            if re.search(r"\d{1,2}[:\.]?\d{0,2}\s*(am|pm|AM|PM)", line) or \
               any(day in line_lower for day in ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]):
                hours_lines.append(line.strip())
            else:
                break
    result = " | ".join(hours_lines)
    return result[:500] if result else ""


def find_menu_url(content: str, base_url: str) -> str:
    base_domain = domain_of(base_url)
    link_re = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)
    links = link_re.findall(content)
    for link in links:
        if any(kw in link.lower() for kw in MENU_KEYWORDS):
            link_domain = domain_of(link)
            if not link_domain or link_domain == base_domain:
                if link.startswith("/"):
                    parsed = urlparse(base_url)
                    return f"{parsed.scheme}://{parsed.netloc}{link}"
                return link
            return link
    # Also search plain text
    url_re = re.compile(r'https?://[^\s<>"\']+menu[^\s<>"\']*', re.IGNORECASE)
    urls = url_re.findall(content)
    return urls[0] if urls else ""


def find_reservation_url(content: str, base_url: str) -> str:
    platform_re = re.compile(
        r'https?://(?:www\.)?(?:opentable\.com|resy\.com|yelp\.com/reservations)[^\s<>"\']*',
        re.IGNORECASE,
    )
    platforms = platform_re.findall(content)
    if platforms:
        return platforms[0]
    link_re = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)
    links = link_re.findall(content)
    for link in links:
        if any(kw in link.lower() for kw in RESERVATION_KEYWORDS):
            if link.startswith("/"):
                parsed = urlparse(base_url)
                return f"{parsed.scheme}://{parsed.netloc}{link}"
            if link.startswith("http"):
                return link
    return ""


async def crawl_one_place(client, api_key, row, semaphore):
    """Crawl a place's website: homepage + discovered sub-pages."""
    async with semaphore:
        website_url = row.get("website_url", "").strip()
        if not website_url:
            return {"crawl_status": "skipped"}

        base_url = website_url.rstrip("/")
        all_content = []
        pages_visited = []

        try:
            # Step 1: Always extract homepage
            homepage_content = await nimble_url_extract(client, api_key, base_url)
            if homepage_content:
                all_content.append(homepage_content)
                pages_visited.append(base_url)

            # Step 2: Discover sub-page URLs from homepage links
            discovered_links = extract_nav_links(homepage_content, base_url) if homepage_content else []

            # Step 3: Fallback paths for anything not discovered
            FALLBACK_PATHS = ["/about", "/contact", "/menu"]
            for path in FALLBACK_PATHS:
                url = base_url + path
                if url not in discovered_links:
                    discovered_links.append(url)

            # Step 4: Extract each sub-page (up to 5 total, skip 404s)
            for url in discovered_links[:5]:
                if url in pages_visited:
                    continue
                content = await nimble_url_extract(client, api_key, url)
                if content:
                    pages_visited.append(url)
                    all_content.append(content)

        except Exception as e:
            return {
                "crawl_status": "error",
                "crawl_error": str(e)[:200],
                "crawl_timestamp": datetime.now(timezone.utc).isoformat(),
            }

        combined_content = "\n\n".join(all_content)
        return {
            "crawl_status": "done",
            "crawl_timestamp": datetime.now(timezone.utc).isoformat(),
            "crawl_phone": parse_phone(combined_content),
            "crawl_email": parse_email(combined_content),
            "crawl_hours": parse_hours(combined_content),
            "crawl_menu_url": find_menu_url(combined_content, base_url),
            "crawl_reservation_url": find_reservation_url(combined_content, base_url),
            "crawl_pages_visited": ", ".join(pages_visited),
            "crawl_raw_text_length": str(len(combined_content)),
        }
```

### Phase 4 Pipeline Runner

```python
async def phase4_website_crawl(client, api_key, ws, rows, col_map, concurrency=5, batch_size=25):
    """Run Phase 4: Website crawl for all rows with website_url."""
    semaphore = asyncio.Semaphore(concurrency)
    pending_writes = []
    write_lock = asyncio.Lock()
    total = 0; skipped = 0; done = 0; errors = 0
    start = time.time()

    tasks = []
    for idx, row in enumerate(rows):
        row_num = idx + 2
        if not row.get("website_url", "").strip():
            if not row.get("crawl_status"):
                rows[idx]["crawl_status"] = "skipped"
                pending_writes.append((row_num, {"crawl_status": "skipped"}))
            skipped += 1
            continue
        status = row.get("crawl_status", "").strip().lower()
        if status in ("done", "skipped"):
            skipped += 1
            continue
        total += 1
        tasks.append((row_num, idx, row))

    # Flush skipped markers
    if pending_writes:
        write_batch(ws, pending_writes, col_map)
        pending_writes.clear()

    if not tasks:
        print(f"  Phase 4: All {skipped} rows already crawled or skipped. Skipping.")
        return
    print(f"  Phase 4: {total} rows to crawl, {skipped} already done/skipped")

    async def process_one(row_num, idx, row):
        nonlocal done, errors
        try:
            result = await crawl_one_place(client, api_key, row, semaphore)
        except Exception as e:
            result = {"crawl_status": "error", "crawl_error": str(e)[:200],
                      "crawl_timestamp": datetime.now(timezone.utc).isoformat()}

        for k, v in result.items():
            rows[idx][k] = v
        if result.get("crawl_status") == "error":
            errors += 1
        done += 1

        batch_to_write = None
        async with write_lock:
            pending_writes.append((row_num, result))
            if len(pending_writes) >= batch_size:
                batch_to_write = pending_writes[:]
                pending_writes.clear()
        if batch_to_write:
            write_batch(ws, batch_to_write, col_map)

        if done % 10 == 0 or done == total:
            elapsed = time.time() - start
            print(f"  [{elapsed:>5.0f}s] Phase 4: {done}/{total} | {errors} errors", flush=True)

    await asyncio.gather(*(process_one(rn, idx, row) for rn, idx, row in tasks))
    if pending_writes:
        write_batch(ws, pending_writes, col_map)

    elapsed = time.time() - start
    print(f"  Phase 4 complete: {done} rows in {elapsed:.0f}s | {errors} errors")
```

## Export Helpers

```python
NUMERIC_FIELDS = {
    "rating", "review_count", "query_hit_count",
    "coffee_quality_signal", "ambience_signal", "work_friendly_signal",
    "crowdedness_signal", "value_signal", "service_signal", "third_wave_score",
    "quality_signal", "craft_signal", "cuisine_signal", "fine_dining_signal",
    "family_friendly_signal", "specialty_fitness_signal", "community_signal",
    "artisan_signal",
}

BOOLEAN_FIELDS = {"borderline", "sponsored"}


def coerce_value(key: str, value: str):
    """Convert string values from the sheet to appropriate Python types."""
    if not value or value.strip() == "":
        if key in NUMERIC_FIELDS:
            return 0
        if key in BOOLEAN_FIELDS:
            return False
        return ""
    v = value.strip()
    if key in BOOLEAN_FIELDS:
        return v.lower() in ("true", "yes", "1")
    if key in NUMERIC_FIELDS:
        try:
            return float(v) if "." in v else int(v)
        except ValueError:
            return 0
    return v


def export_json_from_sheet(ws, output_path):
    """Export all Sheet data to a JSON file with proper type coercion."""
    all_values = ws.get_all_values()
    if not all_values:
        return []

    headers = [h.strip() for h in all_values[0]]
    rows = []
    for row_values in all_values[1:]:
        row = {}
        for i, h in enumerate(headers):
            if not h:
                continue
            raw = row_values[i] if i < len(row_values) else ""
            row[h] = coerce_value(h, raw)
        rows.append(row)

    with open(output_path, "w") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)

    return rows
```

---
name: find-all-locations
description: |
  End-to-end location intelligence. Discovers every place of a given type in a
  neighborhood via Google Maps multi-zone coverage, enriches each with website,
  Instagram, Facebook, and TikTok via Nimble, crawls websites for contact data
  (phone, email, hours, menus, reservations), exports to Google Sheets + JSON,
  and generates an interactive map webapp.

  Triggers: "find all coffee shops in Williamsburg", "map every bar in East Village",
  "build a guide to restaurants in Park Slope", "discover all gyms near me",
  "list every bakery in [neighborhood]", "location guide for [place type] in [area]".

  Do NOT use for single-company research (use company-deep-dive),
  competitor monitoring (use competitor-intel), or general web search
  (use nimble-web-expert).
allowed-tools:
  - Bash(nimble:*)
  - Bash(date:*)
  - Bash(cat:*)
  - Bash(mkdir:*)
  - Bash(python3:*)
  - Bash(echo:*)
  - Bash(jq:*)
  - Bash(ls:*)
  - Bash(uv:*)
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Agent
  - AskUserQuestion
metadata:
  author: Nimbleway
  version: 2.0.0
---

# Find All Locations

End-to-end location intelligence pipeline. Discovers every place of a given type
in a neighborhood, enriches with website + social media + contact data, exports to
Google Sheets + JSON, and generates an interactive map.

User request: $ARGUMENTS

**Before running any commands**, read `references/nimble-playbook.md` for Claude Code
constraints (no shell state, no `&`/`wait`, sub-agent permissions, communication style).

---

## Instructions

### Step 0: Preflight

Follow the preflight pattern from `references/nimble-playbook.md`. Make these Bash
calls simultaneously:

- 14-days-ago date calculation (see nimble-playbook.md for cross-platform command)
- `date +%Y-%m-%d` (today)
- `nimble --version && echo "NIMBLE_API_KEY=${NIMBLE_API_KEY:+set}"`
- `cat ~/.nimble/business-profile.json 2>/dev/null`
- `ls ~/.nimble/memory/locations/ 2>/dev/null` (check for prior location datasets)

From the results:
- CLI missing or API key unset -> `references/profile-and-onboarding.md`, stop
- Profile exists -> note user's company for context
- Prior location data exists for same neighborhood + place type -> offer **resume mode**
  ("I found a prior dataset for [neighborhood] [place_type] from [date]. Resume and
  fill gaps, or start fresh?")
- No profile -> fine, this skill doesn't require onboarding. Proceed to Step 1.

### Step 1: Parse Intent

Extract from `$ARGUMENTS`:

| Signal | Description | Examples |
|--------|-------------|----------|
| `place_type` | What to find | coffee, bar, restaurant, gym, bakery |
| `neighborhood` | Target area | Williamsburg, Park Slope, East Village |
| `city` | City context (infer if possible) | Brooklyn NY, Austin TX, SF CA |
| `quality_focus` | Optional quality filter | "specialty", "craft", "best" |

**If clear** (e.g., "find all coffee shops in Williamsburg"):
- Extract all signals
- Confirm briefly: "Finding every **[place_type]** in **[neighborhood]**..."

**If ambiguous** (e.g., "map everything in Soho" -- place_type unclear):
- Ask one clarifying question: "What type of places? (restaurants, bars, coffee, gyms, etc.)"

**If missing** -- ask: "What type of places and which neighborhood?"

### Step 2: Generate Search Strategy

Read these reference files:

- **`references/query-strategies.md`** -- pick or generate 10+ search queries for the category
- **`references/scoring-patterns.md`** -- pick category-specific scoring logic

Then generate:

1. **10+ search queries** matching the place type and neighborhood
2. **4-8 overlapping zones at zoom level 15** (~30% overlap between zones). Use
   `nimble search --query "[neighborhood] [city]" --focus geo --max-results 3 --search-depth lite`
   to look up coordinates if needed.
3. **Text-geo fallback queries** -- each query + neighborhood name (no coordinates)

```
Total jobs = (queries x zones) + queries
```

Print the strategy summary (queries, zones, total jobs, estimated API calls) and
proceed without confirmation.

### Step 3: Generate Master Pipeline Script

Compose ONE Python script combining code from these templates (read each before
generating):

1. **`references/pipeline-template.md`** -- Discovery phase: Google Maps multi-query
   zone-based search, deduplicate by place_id, normalize, score
2. **`references/enrichment-template.md`** -- Phases 2-4: website/social search,
   social verification with confidence scoring, website crawl for contact data
3. **`references/social-verification.md`** -- Confidence scoring model, profile
   URL validation, evidence storage

#### Script Structure (6 checkpointed phases)

| Phase | What | Concurrency | Writes to Sheet |
|-------|------|-------------|-----------------|
| 1. Discovery | Google Maps search -> dedupe -> normalize -> score | 10 (asyncio.Semaphore) | `master` + `coverage` tabs |
| 2. Search Enrichment | 3 parallel searches per place (website, IG, FB) | 20 (httpx) | `website_url`, `instagram_url`, `facebook_url` |
| 3. Social Verification | IG/FB via `site:` operator, TikTok via social API | 15 (httpx) | `*_verified`, `*_confidence`, `*_match_reason`, `*_evidence` |
| 4. Website Crawl | Extract homepage + up to 5 pages per site | 5 (httpx) | `crawl_phone`, `crawl_email`, `crawl_hours`, `crawl_menu_url`, `crawl_reservation_url` |
| 5. Export | Read Sheet -> type coerce -> write JSON | -- | -- |
| 6. Summary | Print stats and file paths | -- | -- |

#### Key Implementation Details

**Google Sheets setup:**
- Create spreadsheet: `"{Neighborhood} {Place Type} Dataset"`
- Tabs: `master`, `coverage`, `run_metadata`
- Primary key: `place_id` (Google's stable unique identifier)
- Upsert by `place_id` -- never append duplicates
- Batch writes: every 25 rows

**Dependencies block:**
```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx", "gspread", "google-auth", "google-auth-oauthlib", "nimble_python"]
# ///
```

**Resume behavior (Sheet is canonical):**
- Discovery: read `coverage` tab, re-run jobs where status != "done"
- Enrichment: process where `enrichment_status` not in (done, skipped, found, partial, not_found)
- Social: process where `social_status` != "done" OR any `*_confidence` == "low"
- Crawl: process where `crawl_status` not in (done, skipped)

**Error handling:**
- Smoke-test each API endpoint before full batch
- Estimate and print total API calls before starting
- Max retries: 3 with exponential backoff [2s, 5s, 15s]
- Per-place errors stored in status/error columns, don't abort batch
- Never filter out places during collection -- flag borderline, store ALL

Write the script to `~/{neighborhood}_{place_type}_pipeline.py`.

### Step 4: Execute

```bash
NIMBLE_API_KEY=$NIMBLE_API_KEY PYTHONUNBUFFERED=1 uv run ~/{neighborhood}_{place_type}_pipeline.py
```

Monitor output. The script prints progress every 10 rows per phase. Estimated runtimes:
- ~50 places: 3-5 minutes
- ~200 places: 10-20 minutes
- ~500 places: 30-60 minutes

### Step 5: Generate Webapp

After the pipeline completes, read `references/webapp-template.md` and generate an
interactive map webapp:

1. Select color scheme preset based on category:

   | Category | Scheme | Gold accent |
   |----------|--------|-------------|
   | Coffee | Warm espresso | #D4A574 |
   | Restaurant | Warm burgundy | #C45B4A |
   | Bar | Deep navy | #7B9FCC |
   | Fitness | Energetic green | #5CAA6E |
   | Generic | Teal/slate | #6BAAAA |

2. Fill all placeholders with category-appropriate values:
   - Hero stats, filter pills, sort options
   - Card badges, signal tags, modal signals
   - Quality check expression and CSS class
   - Map center coordinates and zoom level

3. Write to `~/{neighborhood}_{place_type}_app.html`

### Step 6: Save to Memory

Make all Write calls simultaneously:

- Report -> `~/.nimble/memory/reports/find-all-locations-{neighborhood-slug}-{date}.md`
  (summary stats, sheet URL, file paths -- NOT the full dataset)
- Location dataset metadata -> `~/.nimble/memory/locations/{neighborhood-slug}-{place-type-slug}.md`
  (place count, date, sheet URL, top-level stats for future reference)
- Update `last_runs.find-all-locations` in `~/.nimble/business-profile.json`
  (only if profile exists)

### Step 7: Present Results

Print a summary:

```
=== {Neighborhood} {Place Type} Dataset Complete ===

Discovery: {N} unique places from {M} raw results ({X} queries x {Y} zones)
Enrichment: {A}% with website, {B}% with Instagram, {C}% with Facebook
Social verification: {D} high confidence, {E} medium, {F} low
Website crawl: {G} crawled, {H} with phone, {I} with email

Output files:
  Sheet: {sheet_url}
  JSON:  ~/{neighborhood}_{place_type}_data.json
  Map:   ~/{neighborhood}_{place_type}_app.html
```

### Step 8: Share & Distribute

**Always offer distribution -- do not skip this step.** Follow
`references/memory-and-distribution.md` to offer Notion/Slack sharing based on
available connectors. Even if the user hasn't set up integrations, offer it once
per run so they know the option exists.

### Step 9: Follow-ups

Suggest:
- "Run again to pick up any gaps?" (resume-safe)
- "Want to add reviews data?"
- "Adjust scoring thresholds?"
- "Export to a different format?"

---

## Agent Teams Mode (Dual-Mode)

Check at startup: `echo $CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`

**Team mode** (flag set): Spawn 3 **teammates** for the pipeline phases:

| Teammate | Responsibility | Cross-checks with |
|----------|---------------|-------------------|
| **Discovery Lead** | Generate script Phase 1, execute, monitor | Enrichment (passes sheet URL) |
| **Enrichment Lead** | Generate Phases 2-4, execute after discovery | Discovery (reads sheet), Webapp (passes JSON) |
| **Webapp Lead** | Generate interactive map after export | Enrichment (reads JSON file) |

**Solo mode** (flag not set): Standard sequential flow from Step 3.

---

## What This Skill Is NOT

- **Not a company deep dive.** For researching a single company, use `company-deep-dive`.
  This skill discovers MANY places in an area.
- **Not competitor monitoring.** For tracking competitors over time, use `competitor-intel`.
  This skill produces a point-in-time dataset.
- **Not general web search.** For one-off web data access, use `nimble-web-expert`.
  This skill runs a multi-phase pipeline with Google Sheets as system of record.
- **Not a CRM or directory.** This gathers live data from public sources. It doesn't
  manage relationships or verify business status.

---

## Error Handling

- **Missing API key:** `references/profile-and-onboarding.md`
- **Neighborhood not found:** Retry with city context, ask user for clarification
- **Empty discovery:** Broaden queries, increase zones, remove quality filters
- **Google Sheets auth fail:** Check `~/.token_enrich.json` or `GOOGLE_SERVICE_ACCOUNT_JSON`
- **429 rate limit:** Reduce concurrency in script
- **401 expired:** "Regenerate at app.nimbleway.com > API Keys"
- **Social search noise:** Confidence scoring filters these; retry low-confidence on rerun
- **Extraction garbage:** Script retries with `--render`; skips after 3 failures

---
name: market-discovery
description: |
  Discovers healthcare practices across U.S. metros using Nimble Maps and web
  search. Builds or audits an account universe for a given healthcare vertical
  (ophthalmology, dental, dermatology, etc.) by tiling search across metro areas.

  Triggers: "find all ophthalmology practices in the US", "build an account list
  of dental practices", "discover eye clinics nationwide", "audit our practice
  list against the market", "how many [specialty] practices exist in [region]",
  "expand our account universe", "market sizing for [vertical]".

  Outputs a deduplicated practice list with name, address, phone, domain, rating,
  and a coverage delta against any existing list (e.g., Definitive Healthcare).

  Do NOT use for extracting practitioners from known websites (use
  practitioner-extract). Do NOT use for single-company research (use
  company-deep-dive). Do NOT use for neighborhood-level place discovery with
  social enrichment (use find-all-locations).
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
  - Bash(wc:*)
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

# Market Discovery

Healthcare practice discovery across U.S. metros powered by Nimble Maps and
web search APIs.

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
- `ls ~/.nimble/memory/market-discovery/ 2>/dev/null`

From the results:
- CLI missing or API key unset -> `references/profile-and-onboarding.md`, stop
- Prior discovery exists for same vertical -> offer **delta mode**: "Found a prior
  discovery for [vertical] from [date] with [N] practices. Run delta to find new
  additions, or start fresh?"
- No profile -> fine, proceed to Step 1.

### Step 1: Parse Intent

Extract from `$ARGUMENTS`:

| Signal | Description | Examples |
|--------|-------------|----------|
| `vertical` | Healthcare specialty | ophthalmology, dental, dermatology, orthopedics |
| `geography` | Target region | "US nationwide", "Texas", "Northeast", specific metro |
| `existing_list` | Reference list to audit against | Sheet URL, CSV path, or "Definitive Healthcare" |
| `target_count` | Expected market size (if stated) | "5,000+", "north of 3,000" |

**If clear** (e.g., "find all ophthalmology practices in the US"):
- Extract signals, confirm: "Discovering **[vertical]** practices across **[geography]**..."

**If ambiguous** — ask one question:
- "Which healthcare specialty? (ophthalmology, dental, dermatology, etc.)"

**If existing list provided:**
- Load it, count rows, note available fields
- Enable **audit mode**: discovery results will be compared against this list
- Match key: domain (primary) or practice name + city (fallback)

### Step 2: Generate Search Strategy

Read `references/metro-coverage.md` for the U.S. metro tiling strategy.
Read `references/vertical-queries.md` for specialty-specific search queries.

**Geography scoping:**

| Scope | Metros | Estimated API calls |
|-------|--------|-------------------|
| US nationwide | ~390 metros (all CBSAs with pop > 50K) | 4,000-8,000 |
| Single state | 10-50 metros (varies) | 200-1,000 |
| Single metro | 1 metro, 4-8 zones | 40-100 |
| Region (e.g., Northeast) | 80-120 metros | 1,000-2,500 |

**Query generation per vertical:**

Generate 8-12 search queries per metro. For ophthalmology:
```
ophthalmology practice {metro}
ophthalmologist {metro}
eye doctor {metro}
retina specialist {metro}
cataract surgeon {metro}
LASIK center {metro}
eye clinic {metro}
vision center {metro}
```

**Total jobs = metros x queries**

Print strategy summary (metros, queries per metro, total jobs, estimated API
calls, estimated runtime) and ask for confirmation before proceeding on
nationwide runs (>1,000 jobs). Proceed without confirmation for single-metro
or single-state runs.

### Step 3: Generate Discovery Pipeline

Read `references/discovery-pipeline-template.md` for the full code template.

Compose ONE Python script with 5 checkpointed phases:

| Phase | What | Concurrency | Output |
|-------|------|-------------|--------|
| 1. Discovery | Maps search per metro x query | 10 | Raw place results |
| 2. Deduplicate | Merge by place_id, then by domain + name fuzzy match | -- | Unique practices |
| 3. Enrich | Web search for missing domains/phones | 15 | Practice profiles |
| 4. Audit | Compare against existing list (if provided) | -- | Delta analysis |
| 5. Export | Write Sheet + JSON + CSV | -- | Final dataset |

#### Phase 1: Discovery

For each (metro, query) pair, search via Nimble Maps:

```bash
nimble search --query "{query}" --focus geo --max-results 20 --search-depth lite
```

**Why `--focus geo`:** Returns local business results with structured place data
(name, address, phone, rating, categories, coordinates) rather than web pages.

For larger metros, also tile with coordinates:
```bash
nimble search --query "{query}" --focus location --max-results 20 --search-depth lite
```

#### Phase 2: Deduplication

Three-layer dedup:
1. **place_id** exact match (Google's unique identifier)
2. **Domain match** — same root domain = same practice (catches multi-location)
3. **Name + city fuzzy match** — normalized name + city match within 2 Levenshtein
   distance (catches "Smith Eye Center" vs "Smith Eye Associates")

Track `query_hit_count` per practice (number of distinct queries that found it).

#### Phase 3: Enrichment

For practices missing website/phone, run targeted web searches:

```bash
nimble search --query "\"{practice_name}\" {city} {state} ophthalmology website" --max-results 5 --search-depth lite
```

Extract domain from top non-aggregator result. Apply the same aggregator filter
as find-all-locations (`references/enrichment-template.md`).

#### Phase 4: Audit (if existing list provided)

Compare discovered practices against the reference list:

**Matching strategy:**
1. Domain match (strip www, compare root domain)
2. Practice name + city (fuzzy match, 80% word overlap threshold)
3. Phone match (normalize to 10 digits)

**Output categories:**
- `matched` — found in both discovery and reference list
- `discovered_only` — found by Nimble but NOT in reference list (expansion candidates)
- `reference_only` — in reference list but NOT found by Nimble (coverage gaps)

#### Phase 5: Export

**Output schema per practice:**

```
place_id               — Google's unique identifier
practice_name          — full practice name
street_address         — street address
city                   — city
state                  — state abbreviation
zip                    — ZIP code
full_address           — complete formatted address
lat                    — latitude
lng                    — longitude
phone                  — phone number
domain                 — root domain (e.g., smitheye.com)
website_url            — full URL
rating                 — Google Maps rating
review_count           — number of Google reviews
primary_category       — primary Google Maps category
all_categories         — all listed categories
query_hit_count        — discovery signal strength
metro                  — metro area where discovered
audit_status           — matched / discovered_only / reference_only (if audit mode)
```

**Google Sheet:** `"{Vertical} Market Discovery {date}"` with tabs:
- `practices` — full deduplicated practice list
- `discovered_only` — practices NOT in reference list (if audit mode)
- `reference_only` — reference practices NOT found (if audit mode)
- `coverage` — per-metro discovery stats
- `summary` — aggregate statistics

**JSON:** `~/{vertical}_market_discovery_{date}.json`
**CSV:** `~/{vertical}_market_discovery_{date}.csv`

### Step 4: Execute

```bash
NIMBLE_API_KEY=$NIMBLE_API_KEY PYTHONUNBUFFERED=1 uv run ~/{vertical}_market_discovery.py
```

Estimated runtimes:
- Single metro: 2-5 minutes
- Single state: 15-30 minutes
- US nationwide: 2-4 hours (batch in segments by state)

For nationwide runs, the script should support `--states` argument for batched
execution (e.g., `--states CA,NY,TX`).

### Step 5: Save to Memory

Make all Write calls simultaneously:

- Report -> `~/.nimble/memory/reports/market-discovery-{vertical}-{date}.md`
- Discovery metadata -> `~/.nimble/memory/market-discovery/{vertical}-{date}.md`
  (practice count by metro, coverage stats, delta summary)
- Update `last_runs.market-discovery` in `~/.nimble/business-profile.json`

### Step 6: Present Results

```
=== {Vertical} Market Discovery Complete ===

Geography: {scope} ({N} metros searched)
Queries: {Q} per metro, {total_jobs} total jobs

Practices found: {P} unique (from {R} raw results)
  - With website: {A}% | With phone: {B}%
  - Average rating: {C} | Median reviews: {D}

Top metros: {metro1} ({n1}), {metro2} ({n2}), {metro3} ({n3})

{If audit mode:}
Audit vs. {reference_name} ({ref_count} practices):
  - Matched: {M} ({M/ref_count}%)
  - Discovered only (new): {X} practices NOT in reference
  - Reference only (gaps): {Y} practices NOT found by Nimble

Output files:
  Sheet: {sheet_url}
  JSON:  ~/{vertical}_market_discovery_{date}.json
  CSV:   ~/{vertical}_market_discovery_{date}.csv
```

### Step 7: Share & Distribute

**Always offer distribution -- do not skip this step.** Follow
`references/memory-and-distribution.md` to offer Notion/Slack sharing based on
available connectors. Even if the user hasn't set up integrations, offer it once
per run so they know the option exists.

### Step 8: Follow-ups

Suggest:
- "Run practitioner-extract on the discovered URLs?" (natural next step)
- "Drill deeper into a specific state or metro?"
- "Run audit mode against your existing list?"
- "Export the discovered-only subset for outreach?"

---

## Agent Teams Mode (Dual-Mode)

Check at startup: `echo $CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`

**Team mode** (flag set): Partition metros across teammates by region:

| Teammate | Region | Metros |
|----------|--------|--------|
| **Northeast** | ME to VA | ~80 metros |
| **Southeast + Midwest** | NC to MN | ~130 metros |
| **West + Southwest** | TX to WA | ~180 metros |

Lead (you): Merge all results, run dedup + audit + export.

**Solo mode** (flag not set): Standard sequential pipeline.

---

## What This Skill Is NOT

- **Not practitioner extraction.** For pulling doctor-level data from known
  practice websites, use `practitioner-extract`. This skill discovers PRACTICES.
- **Not a definitive database.** Google Maps coverage varies by region and category.
  Use this for discovery and auditing, not as sole source-of-truth.
- **Not social enrichment.** For adding social profiles and contact data, use
  `find-all-locations` or `practitioner-extract` after discovery.
- **Not real-time monitoring.** For tracking changes over time, re-run periodically
  and use delta mode to surface new additions.

---

## Error Handling

- **Missing API key:** `references/profile-and-onboarding.md`
- **Invalid geography:** Ask for clarification; suggest metro or state names
- **Empty results for a metro:** Log and continue; don't abort the batch
- **Low coverage in a metro:** May indicate wrong query terms; retry with broader queries
- **429 rate limit:** Reduce concurrency in script; batch by state
- **401 expired:** "Regenerate at app.nimbleway.com > API Keys"
- **Audit list format issues:** Attempt to auto-detect columns; ask if ambiguous
- **Fuzzy match false positives:** Use conservative thresholds; flag uncertain matches

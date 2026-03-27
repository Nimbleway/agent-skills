---
name: practitioner-extract
description: |
  Extracts practitioner-level data from healthcare practice websites. Given a list
  of practice URLs (CSV, Google Sheet, or inline), crawls each site to discover
  provider/team/doctors pages, then extracts structured data: practitioner name,
  credentials, specialty, office location, phone, bio URL, appointment URL.

  Triggers: "extract doctors from these practice websites", "pull practitioners
  from this URL list", "crawl these clinic sites for provider data", "get doctor
  info from these ophthalmology practices", "extract staff from healthcare sites",
  "build a practitioner database from these URLs".

  Works for any healthcare vertical: ophthalmology, dental, dermatology, orthopedics,
  primary care, etc. The extraction patterns adapt to each site's structure.

  Do NOT use for discovering practices (use market-discovery). Do NOT use for
  general web extraction (use nimble-web-expert). Do NOT use for social media
  enrichment (use find-all-locations).
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

# Practitioner Extract

Extract practitioner-level data from healthcare practice websites using Nimble's
web crawl and extraction APIs.

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
- `ls ~/.nimble/memory/practitioner-extracts/ 2>/dev/null`

From the results:
- CLI missing or API key unset -> `references/profile-and-onboarding.md`, stop
- Prior extract exists for same input -> offer **resume mode**: "Found a prior
  extract from [date] with [N] practitioners. Resume and fill gaps, or start fresh?"
- No profile -> fine, proceed to Step 1.

### Step 1: Parse Input

Determine the input source from `$ARGUMENTS`:

**Input formats supported:**

| Format | Detection | Action |
|--------|-----------|--------|
| Google Sheet URL | Contains `docs.google.com/spreadsheets` | Read sheet directly |
| CSV file path | Ends in `.csv`, file exists | Read CSV |
| Inline URLs | One or more URLs in the message | Parse directly |
| Definitive Healthcare export | User mentions "Definitive" | Ask for file path or Sheet URL |

**Required columns/data:**
- `url` or `website` or `domain` — the practice website (required)
- `practice_name` — practice name (optional, extracted from site if missing)
- `city`, `state` — location context (optional, helps disambiguation)

**If clear** (e.g., "extract practitioners from this sheet: [URL]"):
- Load the input, count rows
- Confirm: "Loaded **[N] practice URLs**. Extracting practitioner data..."

**If ambiguous** — ask one clarifying question:
- "Where's the URL list? (Google Sheet URL, CSV file path, or paste URLs directly)"

**Vertical detection** — infer the healthcare vertical from context:
- User mentions "ophthalmology", "eye", "retina" -> ophthalmology
- User mentions "dental", "dentist" -> dental
- User mentions "dermatology", "skin" -> dermatology
- No signal -> generic healthcare (works for all)

The vertical tunes page-discovery patterns and extraction fields (see Step 2).

### Step 2: Site Mapping (discover provider pages)

Read `references/page-discovery-patterns.md` for the full pattern library.

For each practice URL, use `nimble map` to discover the site structure, then
identify pages likely to contain practitioner data.

**Phase A — Map all practice domains** (parallel, max 10 concurrent):

```bash
nimble map --url "https://example-practice.com" --limit 50
```

**Phase B — Filter for provider pages:**

Score each discovered URL against provider-page patterns:

| Pattern | Weight | Examples |
|---------|--------|---------|
| Path contains `/providers`, `/doctors`, `/physicians`, `/our-team`, `/staff` | 10 | `/our-providers`, `/meet-the-doctors` |
| Path contains `/team`, `/about`, `/people`, `/specialists` | 7 | `/about-us/team`, `/our-specialists` |
| Path contains `/locations` + practitioner signals | 5 | `/locations/dr-smith` |
| Path contains individual name patterns (`/dr-`, `/doctor-`) | 8 | `/dr-john-smith`, `/doctor-jane-doe` |
| Path contains specialty keywords | 3 | `/retina-specialist`, `/cataract-surgeon` |
| Homepage (always include as fallback) | 1 | `/`, `/index` |

**Keep:** All URLs scoring >= 5, plus homepage. Cap at 15 pages per site to
control costs.

**Fallback if `nimble map` returns < 3 URLs:**
```bash
nimble search --query "site:{domain} doctors OR providers OR team OR physicians" --max-results 10 --search-depth lite
```

### Step 3: Generate Extraction Pipeline

Read `references/extraction-template.md` for the full code template.

Compose ONE Python script with 4 checkpointed phases:

| Phase | What | Concurrency | Output |
|-------|------|-------------|--------|
| 1. Map | `nimble map` all domains -> filter provider pages | 10 | Page URLs per practice |
| 2. Extract | `nimble extract --format markdown` on provider pages | 8 | Raw markdown per page |
| 3. Parse | LLM-assisted structured extraction from markdown | -- | Practitioner records |
| 4. Export | Deduplicate, merge, write Sheet + JSON + CSV | -- | Final dataset |

#### Phase 2: Page Extraction

For each provider page, extract content:

```bash
nimble extract --url "https://example.com/our-providers" --format markdown
```

If extraction returns JavaScript/boilerplate:
1. Retry with `--render --format markdown`
2. If still garbage, skip and log error

#### Phase 3: Structured Parsing

For each extracted page, parse practitioner records. The script should use
regex + heuristic patterns to extract:

**Output schema per practitioner:**

```
practice_name          — from input list or extracted from site
practice_url           — the input URL
practitioner_name      — full name (Dr. John Smith)
credentials            — MD, DO, OD, PhD, FACS, etc.
specialty              — ophthalmology, retina, glaucoma, cataract, etc.
subspecialty            — if listed (e.g., pediatric ophthalmology)
title                  — Medical Director, Partner, Associate, etc.
office_location         — specific office/branch if multi-location
phone                  — direct or office phone
email                  — if listed
bio_url                — link to individual bio/profile page
photo_url              — headshot URL if found
appointment_url         — online scheduling link if found
patient_portal_url      — patient portal link if found
source_page            — the URL this data was extracted from
extraction_confidence   — high/medium/low based on data completeness
```

**Parsing strategy:**
1. **Structured HTML patterns** — many practice sites use repeating card/grid layouts
   with consistent CSS classes. Look for repeating `<div>` blocks containing name +
   credentials + photo + link patterns.
2. **Markdown heading patterns** — extracted markdown often has `## Dr. Name, MD`
   followed by specialty and bio text.
3. **Table patterns** — some sites list providers in tables.
4. **Individual page patterns** — `/dr-smith` pages typically have the name in `<h1>`,
   credentials nearby, and bio text in the main content area.

**Credential detection regex:**
```python
CREDENTIAL_PATTERN = r'\b(M\.?D\.?|D\.?O\.?|O\.?D\.?|Ph\.?D\.?|F\.?A\.?C\.?S\.?|F\.?A\.?A\.?O\.?|M\.?B\.?A\.?|M\.?P\.?H\.?|M\.?S\.?|B\.?S\.?|R\.?N\.?|N\.?P\.?|P\.?A\.?[-\s]?C?\.?)\b'
```

**Specialty keyword matching (ophthalmology vertical):**
```python
OPHTHO_SPECIALTIES = {
    "retina": ["retina", "vitreoretinal", "macular"],
    "glaucoma": ["glaucoma"],
    "cataract": ["cataract", "lens", "iol"],
    "cornea": ["cornea", "corneal", "external disease"],
    "oculoplastics": ["oculoplastic", "orbital", "eyelid", "lacrimal"],
    "pediatric": ["pediatric", "strabismus", "amblyopia"],
    "neuro": ["neuro-ophthalmology", "neuro-ophthalmic"],
    "refractive": ["lasik", "refractive", "prk"],
    "comprehensive": ["comprehensive", "general ophthalmology"],
    "optometry": ["optometry", "optometrist"],
}
```

**Contact extraction patterns:**
- Phone: same regex as find-all-locations enrichment template
- Email: filter generic addresses (info@, noreply@, admin@)
- Appointment URL: look for links with text/href matching `schedule`, `appointment`,
  `book`, `request`, or known platforms (Zocdoc, Solutionreach, NexHealth, ModMed)
- Patient portal: links matching `portal`, `patient login`, `myhealth`

#### Phase 4: Export

**Google Sheet:** Create `"{Vertical} Practitioner Extract {date}"` with tabs:
- `practitioners` — one row per practitioner (main output)
- `practices` — one row per practice with extraction stats
- `errors` — sites that failed extraction with error details

**JSON:** `~/{vertical}_practitioners_{date}.json`
**CSV:** `~/{vertical}_practitioners_{date}.csv`

### Step 4: Execute

```bash
NIMBLE_API_KEY=$NIMBLE_API_KEY PYTHONUNBUFFERED=1 uv run ~/{vertical}_practitioner_pipeline.py
```

Estimated runtimes:
- 50 practices: 5-10 minutes
- 500 practices: 30-60 minutes
- 3,500 practices: 3-5 hours (batch in segments of 500)

For large inputs (500+), the script should support `--start` and `--end` row
arguments for batched execution.

### Step 5: Save to Memory

Make all Write calls simultaneously:

- Report -> `~/.nimble/memory/reports/practitioner-extract-{vertical}-{date}.md`
- Extract metadata -> `~/.nimble/memory/practitioner-extracts/{vertical}-{date}.md`
  (practice count, practitioner count, extraction rates, sheet URL)
- Update `last_runs.practitioner-extract` in `~/.nimble/business-profile.json`

### Step 6: Present Results

```
=== {Vertical} Practitioner Extract Complete ===

Practices processed: {N} of {M} ({N/M}%)
  - Successful: {A} | Failed: {B} | Skipped: {C}

Practitioners found: {P} total
  - With credentials: {D}% | With specialty: {E}%
  - With phone: {F}% | With email: {G}%
  - With bio URL: {H}% | With appointment URL: {I}%

Confidence: {J} high, {K} medium, {L} low

Output files:
  Sheet: {sheet_url}
  JSON:  ~/{vertical}_practitioners_{date}.json
  CSV:   ~/{vertical}_practitioners_{date}.csv
```

### Step 7: Share & Distribute

**Always offer distribution -- do not skip this step.** Follow
`references/memory-and-distribution.md` to offer Notion/Slack sharing based on
available connectors. Even if the user hasn't set up integrations, offer it once
per run so they know the option exists.

### Step 8: Follow-ups

Suggest:
- "Run again to pick up extraction gaps?" (resume-safe)
- "Want to enrich with social profiles?" (-> find-all-locations enrichment)
- "Export a specific subset?" (by specialty, location, etc.)
- "Run market-discovery to find practices not in your list?"

---

## Agent Teams Mode (Dual-Mode)

Check at startup: `echo $CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`

**Team mode** (flag set): Partition the input list across teammates:

| Teammate | Responsibility | Cross-checks with |
|----------|---------------|-------------------|
| **Mapper** | Map all domains, discover provider pages | Extractor (passes page URLs) |
| **Extractor** | Extract + parse all provider pages | Mapper (reads page list), Exporter (passes records) |
| **Exporter** | Deduplicate, merge, write all outputs | Extractor (reads parsed records) |

**Solo mode** (flag not set): Standard sequential flow.

---

## What This Skill Is NOT

- **Not practice discovery.** For finding practices you don't already have, use
  `market-discovery`. This skill extracts from KNOWN practice URLs.
- **Not social enrichment.** For adding Instagram/Facebook/TikTok, use
  `find-all-locations`. This skill focuses on the practice website itself.
- **Not general web extraction.** For one-off URL extraction, use `nimble-web-expert`.
  This skill runs a multi-phase pipeline optimized for healthcare provider pages.
- **Not a medical database.** This extracts publicly listed information. It doesn't
  verify credentials, NPI numbers, or board certifications.

---

## Error Handling

- **Missing API key:** `references/profile-and-onboarding.md`
- **Invalid URLs in input:** Skip and log; don't abort the batch
- **Site blocks extraction:** Retry with `--render`; if still blocked, log and skip
- **No provider pages found:** Log as "no provider pages detected"; include in errors tab
- **Empty extraction:** Site may use PDF or image-based provider listings; log and skip
- **429 rate limit:** Reduce concurrency in script
- **401 expired:** "Regenerate at app.nimbleway.com > API Keys"
- **Google Sheets auth fail:** Check credentials per enrichment-template.md

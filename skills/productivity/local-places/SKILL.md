---
name: local-places
description: |
  Discovers, enriches, and scores local businesses in any neighborhood using
  Nimble Web Search Agents (WSAs) and web data. Returns a structured, ranked
  list with confidence scores, reviews, social presence, and an interactive map.

  Use this skill when the user asks about local businesses, places, or
  neighborhood discovery. Common triggers: "find all coffee shops in",
  "map every bar in", "local businesses in", "discover gyms near",
  "what restaurants are in", "neighborhood guide for", "local places in",
  "find places near", "list all [business type] in [area]", "best [type]
  near [location]", "build a neighborhood guide", "local place search".

  Requires the Nimble CLI (nimble agent run, nimble search, nimble extract)
  for live web data via WSAs and fallback search.
  Do NOT use for competitor analysis or monitoring (use competitor-intel),
  company research or deep dives (use company-deep-dive), general web search
  or extraction (use nimble-web-expert).
allowed-tools:
  - Bash(nimble:*)
  - Bash(date:*)
  - Bash(cat:*)
  - Bash(mkdir:*)
  - Bash(python3:*)
  - Bash(echo:*)
  - Bash(jq:*)
  - Bash(ls:*)
  - Bash(open:*)
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Agent
  - AskUserQuestion
metadata:
  author: Nimbleway
  version: 0.15.0
---

# Local Places

Location intelligence powered by Nimble Web Search Agents and web data APIs.

User request: $ARGUMENTS

**Before running any commands**, read `references/nimble-playbook.md` for Claude Code
constraints (no shell state, no `&`/`wait`, sub-agent permissions, communication style).

---

## Instructions

### Step 0: Preflight

Run the preflight pattern from `references/nimble-playbook.md` (4 simultaneous Bash
calls: date calc, today, CLI check, profile load).

Also simultaneously:
- `mkdir -p ~/.nimble/memory/{reports,local-places/checkpoints}`
- Check for existing checkpoints: `ls ~/.nimble/memory/local-places/checkpoints/ 2>/dev/null`

From the results:
- CLI missing or API key unset -> `references/profile-and-onboarding.md`, stop
- Profile exists -> note the user's location preferences if any. Determine mode
  using smart date windowing from `references/nimble-playbook.md`:
  - **Full mode:** first run OR last run > 14 days ago
  - **Quick refresh:** last run < 14 days ago (skip social enrichment, reviews only
    for new places)
  - **Same-day repeat:** if `last_runs.local-places` is today, check if a report
    already exists at `~/.nimble/memory/reports/local-places-*[today].md`. If so,
    ask: "Already ran today for this area. Run again for fresh data?" Don't silently
    re-run.
  - Skip to Step 1
- No profile -> that's fine. Local places doesn't require onboarding. Proceed to Step 1.

### Step 1: Parse Request & Starting Questions

Parse `$ARGUMENTS` for place type and location. Extract:

| Field | Required | Source |
|-------|----------|--------|
| Place type | Yes | User input ("coffee shops", "gyms", "restaurants") |
| Location | Yes | User input ("Williamsburg", "downtown Austin", "Park Slope") |
| Filters | Optional | User input ("with good reviews", "open late", "cheap") |
| Output preference | Optional | User input ("map", "list", "guide") |

**If both place type and location are clear** from `$ARGUMENTS`, confirm briefly and
proceed: "Searching for **coffee shops** in **Williamsburg, Brooklyn**..."

**If partial or ambiguous**, ask one combined question in plain text:

> "What type of places are you looking for, and where? (e.g., 'coffee shops in
> Williamsburg' or 'gyms near downtown Austin')"

**If the user provided both but you want to scope further**, use AskUserQuestion
(counts as 1 of max 2 prompts):

> **How thorough should this search be?**
> - **Quick scan** -- top results from Google Maps + Yelp (~20 places)
> - **Comprehensive** -- full discovery + social enrichment + reviews (~50+ places)
> - **Deep dive with map** -- everything above + interactive neighborhood map

### Step 2: Location Disambiguation

Before any API calls, resolve the location to avoid wasted searches.

**Disambiguation triggers:**
- Location name exists in multiple cities/states (e.g., "Williamsburg" = Brooklyn NY
  vs. Williamsburg VA)
- Location is a broad area (e.g., "downtown Austin" = multiple neighborhoods)
- Location is informal (e.g., "Soho" = NYC vs. London)

**If ambiguous**, ask the user (counts toward 2-prompt max):

> "There are a few places called **Williamsburg**. Which one?"
> - **Williamsburg, Brooklyn, NY**
> - **Williamsburg, VA**
> - **Other -- I'll specify**

**If unambiguous**, infer the full location (city + state/country) and confirm inline:
"Searching **Williamsburg, Brooklyn, NY**..."

After disambiguation, derive the `slug` for checkpointing and file paths:
lowercase, hyphenated, includes city + state/country (e.g., `williamsburg-brooklyn-ny`).

### Step 3: Check for Existing Checkpoint

Follow the Checkpointing & Resume pattern from `references/memory-and-distribution.md`.

Check: `cat ~/.nimble/memory/local-places/checkpoints/{slug}/discovery.json 2>/dev/null`

- **Checkpoint found** -> offer: "Found previous run ({N} places from {date}).
  Resume and fill gaps, or start fresh?"
- **No checkpoint** -> proceed to Step 4

### Step 4: Discovery (WSA Phase 1)

Read `references/wsa-pipeline.md` for the full WSA-to-phase mapping and category
detection logic.

**Validate WSA schemas first** -- run simultaneously to confirm param names:

```bash
nimble agent get --template-name google_maps_search
```

```bash
nimble agent get --template-name yelp_serp
```

Use the returned parameter names in the calls below. The examples show expected
params, but always confirm with `nimble agent get` since WSA schemas may change.

**Primary discovery** -- run simultaneously:

```bash
nimble agent run --agent google_maps_search --params '{"query": "[place-type] in [location]"}'
```

```bash
nimble agent run --agent yelp_serp --params '{"search_query": "[place-type]", "location": "[location]"}'
```

**Tertiary (conditional):** Run `bbb_org_business_search` only if primary + secondary
return < 10 combined unique results, or if the user explicitly asked for
credibility/trust data:

```bash
nimble agent run --agent bbb_org_business_search --params '{"query": "[place-type] [location]"}'
```

If any WSA fails or returns empty, fall back to:
`nimble search --query "[place-type] in [location]" --max-results 20 --search-depth lite`

**After discovery:**
1. Parse all results into a unified entity list
2. Deduplicate following the Entity Deduplication pattern from
   `references/nimble-playbook.md`: place_id exact match -> domain normalization ->
   fuzzy name + city
3. Save checkpoint:
   `~/.nimble/memory/local-places/checkpoints/{slug}/discovery.json`

### Step 5: Social Enrichment (WSA Phase 2)

For each discovered place that has a Facebook page or Instagram handle, run
enrichment WSAs. See `references/wsa-pipeline.md` for the full mapping.

Batch max **4 concurrent Bash calls** to respect rate limits. For places with
social handles found in discovery:

```bash
nimble agent run --agent facebook_page --params '{"url": "https://facebook.com/[page]"}'
```

```bash
nimble agent run --agent instagram_profile_by_account --params '{"account": "[handle]"}'
```

Skip `tiktok_account` unless the user specifically asked for social depth or chose
"Comprehensive" / "Deep dive" in Step 1.

Save checkpoint: `~/.nimble/memory/local-places/checkpoints/{slug}/social.json`

### Step 6: Reviews (WSA Phase 3)

For the top places (by source count and data completeness), pull reviews:

```bash
nimble agent run --agent google_maps_reviews --params '{"place_id": "[place_id]"}'
```

Batch max 4 concurrent calls. Focus on places that have a `place_id` from
Google Maps discovery. Save checkpoint:
`~/.nimble/memory/local-places/checkpoints/{slug}/reviews.json`

### Step 7: Food/Drink Bonus (WSA Phase 4)

**Auto-trigger** when the place type category matches food/drink keywords.
See `references/wsa-pipeline.md` for the category detection logic.

If triggered, search for delivery listings first, then fetch details:

**Discovery** -- run simultaneously:

```bash
nimble agent run --agent doordash_serp --params '{"query": "[place-name] [location]"}'
```

```bash
nimble search --query "[place-name] [location] site:ubereats.com" --max-results 1 --search-depth lite
```

**Detail** -- for places found on delivery platforms, fetch full details:

```bash
nimble agent run --agent doordash_pdp --params '{"url": "[doordash-url-from-serp]"}'
```

```bash
nimble agent run --agent uber_eats_pdp --params '{"url": "[uber-eats-url-from-search]"}'
```

Only run detail calls for places that returned a valid delivery URL. Skip if
category is not food/drink (gyms, yoga studios, etc.).

### Step 8: Deduplication & Confidence Scoring

**Deduplication:** Run a final dedup pass across all phases following the Entity
Deduplication pattern from `references/nimble-playbook.md`. Merge fields from
multiple sources into a single enriched record per place.

**Confidence scoring:** Follow the Entity Confidence Scoring pattern from
`references/nimble-playbook.md`. Skill-specific target fields (N=8):

| Field | Description |
|-------|-------------|
| name | Business name |
| address | Full street address |
| phone | Phone number |
| website | Website URL |
| rating | Average rating |
| review_count | Number of reviews |
| social | At least one social profile |
| hours | Operating hours |

Scoring criteria:
- **High** (8/8 fields + 2+ sources + 10+ reviews) -> display as `*** High`
- **Medium** (5-7/8 fields OR 2+ sources with partial data) -> `** Medium`
- **Low** (<=4/8 fields, single source, few/no reviews) -> `* Low`

### Step 9: Output

Present results as a numbered table sorted by confidence (High first), then by
rating within each tier.

```
# Local Places: [Place Type] in [Location]
*Found [N] places | [Date] | Confidence: [H] High, [M] Medium, [L] Low*

## Results

| # | Name | Rating | Reviews | Confidence | Address | Sources |
|---|------|--------|---------|------------|---------|---------|
| 1 | Place A | 4.8 (312) | *** High | 123 Main St | [Maps][Yelp] |
| 2 | Place B | 4.6 (89)  | ** Medium | 456 Oak Ave | [Maps] |
...

## Top Picks (High Confidence)

### 1. Place A
- **Address:** 123 Main St, Williamsburg, Brooklyn, NY
- **Phone:** (555) 123-4567 | **Website:** [placea.com](https://placea.com)
- **Rating:** 4.8/5 (312 reviews on Google Maps, 289 on Yelp)
- **Social:** Instagram @placea (2.1K followers) | Facebook (1.8K likes)
- **Hours:** Mon-Fri 7am-7pm, Sat-Sun 8am-6pm
- **Delivery:** Available on DoorDash, Uber Eats
- **Why it stands out:** [1-2 sentences from review highlights]
- **Sources:** [Google Maps](link) | [Yelp](link) | [Facebook](link)

[Repeat for each High confidence place]

## Other Results (Medium + Low Confidence)
[Briefer format -- name, rating, address, missing data noted]

## What's Missing
[Note any data gaps: "3 places had no website or social presence",
 "Reviews unavailable for BBB-only listings"]
```

**Source links are mandatory.** Every place must have at least one clickable source
URL (Google Maps link, Yelp listing, website, or social profile). Places without
any source link should be noted in "What's Missing" but still included if they have
sufficient data from WSA results.

**Drill-down:** After presenting, tell the user:
> "Want details on any place? Say 'tell me more about #3' or ask for the
> interactive map."

### Step 10: Interactive Map (on request or "Deep dive" mode)

Generate an HTML file with Leaflet.js + OpenStreetMap tiles. See
`references/wsa-pipeline.md` for the full map generation pattern and color scheme.

Save to: `~/.nimble/memory/local-places/{slug}-map-{date}.html`

Open in browser: `open ~/.nimble/memory/local-places/{slug}-map-{date}.html`

Only generate automatically if the user chose "Deep dive with map" in Step 1.
Otherwise, offer it as a follow-up action.

### Step 11: Save to Memory

Make all Write calls simultaneously:

- Report -> `~/.nimble/memory/reports/local-places-{slug}-{date}.md`
- Per-place data -> `~/.nimble/memory/local-places/{slug}/places.json`
  (structured JSON with all enriched records)
- Profile -> update `last_runs.local-places` in `~/.nimble/business-profile.json`
  (only if profile exists)
- Clean up checkpoint (complete run) or keep (partial run)

### Step 12: Share & Distribute

**Always offer distribution -- do not skip this step.** Follow
`references/memory-and-distribution.md` for connector detection, sharing flow, and
source links enforcement.

Notion: full results table as a dated subpage.
Slack: TL;DR with top 5 places only.

### Step 13: Follow-ups

- **"Tell me more about #N"** -> show full detail for that place
- **"Show the map"** -> generate interactive map (Step 10)
- **"Add filters"** -> re-search with additional constraints
- **"Search nearby area"** -> expand to adjacent neighborhoods
- **"Export as CSV"** -> generate CSV from places.json
- **"Looks good"** -> done

**Sibling skill suggestions:**

> **Next steps:**
> - Run `company-deep-dive` for a full 360 profile on any business from this list
> - Run `meeting-prep` if you're meeting with someone at one of these businesses
> - Run `competitor-positioning` to compare businesses in this area

---

## Sub-Agent Strategy

For comprehensive searches (50+ places), use `nimble-researcher` agents
(`agents/nimble-researcher.md`) to parallelize enrichment.

Follow the sub-agent spawning rules from `references/nimble-playbook.md`
(bypassPermissions, batch max 4, explicit Bash instruction, fallback on failure).

**Spawn pattern:** One agent per batch of 10 places for social enrichment.
Each agent runs the Phase 2 WSAs for its batch and returns structured results.

**Single-batch optimization:** If <= 10 places, run enrichment directly from the
main context instead of spawning agents -- saves overhead.

**Fallback:** If any agent fails, run those WSA calls directly from the main context.

---

## Agent Teams Mode (Dual-Mode)

Check at startup: `echo $CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`

**Team mode** (flag set): Spawn **teammates** for parallel phases:

- **Discovery teammate**: Runs all Phase 1 WSAs, deduplicates, returns unified list
- **Enrichment teammate**: Runs Phases 2-4 for each place batch
- **Lead** (you): Coordinates, scores, generates output and map

**Solo mode** (flag not set): Standard sequential flow from Steps 4-7.

---

## Error Handling

See `references/nimble-playbook.md` for the standard error table (missing API key, 429,
401, empty results, extraction garbage). Skill-specific errors:

- **WSA not found:** If a WSA from the pipeline doesn't exist (e.g., `bbb_org_business_search`),
  skip it silently and rely on other discovery sources. Log which WSAs were unavailable.
- **Location not found:** "Couldn't find results for [location]. Could you be more specific?
  Try including city and state (e.g., 'Williamsburg, Brooklyn, NY')."
- **No results for place type:** "No [place type] found in [location]. Want to try a
  broader category or nearby area?"
- **Ambiguous place type:** "Did you mean [option A] or [option B]?" (e.g., "bar" could be
  cocktail bar, sports bar, wine bar)

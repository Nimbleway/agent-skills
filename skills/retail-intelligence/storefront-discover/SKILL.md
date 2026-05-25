---
name: storefront-discover
description: |
  Investigates any ecommerce storefront's category structure and produces a
  reusable extraction rulebook — a step-by-step MD file that storefront-extract
  can follow to extract all category and subcategory URLs. Works for any
  grocery, retail, or marketplace site.

  Triggers: "investigate storefront", "reverse-engineer categories for",
  "how does X organize categories", "create extraction rulebook for",
  "discover category structure", "map categories on", "analyze storefront".

  Do NOT use for executing an existing rulebook — use storefront-extract.
  Do NOT use for product scraping — this skill only maps the category tree.
allowed-tools:
  - Bash(nimble:*)
  - Bash(date:*)
  - Bash(cat:*)
  - Bash(mkdir:*)
  - Bash(python3:*)
  - Bash(echo:*)
  - Bash(jq:*)
  - Bash(ls:*)
  - Bash(curl:*)
  - Bash(head:*)
  - Bash(wc:*)
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Agent
  - AskUserQuestion
  - mcp__browser-use__browser_task
  - mcp__browser-use__monitor_task
  - mcp__browser-use__list_skills
  - mcp__browser-use__execute_skill
metadata:
  author: Nimbleway
  version: 0.21.2
---

# Storefront Discover

Reverse-engineer any storefront's category structure into a reusable extraction rulebook.

User request: $ARGUMENTS

Do NOT read `references/nimble-playbook.md` until Step 3d (validation). This skill uses `nimble map` as the primary discovery method — browser-use is a fallback only.

---

## Execution Order

1. **Step 0** — Preflight: lightweight checks only (date, profile, mkdir, ls)
2. **Step 1** — Parse the storefront URL from user input
3. **Step 2** — Check existing rulebooks (ls/read only)
4. **Step 3a** — **Run `nimble map`** + cluster URLs by path structure (THIS IS THE FIRST REAL ACTION)
5. **Step 3b/3c** — Fallback to browser-use navigation, then static API probes, only if map yields < 5 category URLs
6. **Step 3d** — Validate the best source
7. **Steps 4–10** — Classify, write rulebook, test, save, distribute

---

## File-Based Pipeline (used from Step 3b onward)

All API validation calls use curl → temp file → Python script. Raw responses are NEVER loaded into the LLM context.

### Nimble Web Extract (via curl)
```bash
curl -s -X POST "https://api.webit.live/api/v1/realtime/web" \
  -H "Authorization: Bearer $NIMBLE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url": "<url>", "country": "<country>", "render": true}' \
  > /tmp/{slug}_raw_{step}.json
```

### Response Format
Nimble API wraps responses in a JSON envelope:
```json
{"url": "...", "status": "success", "html_content": "<pre>{ ... actual JSON ... }</pre>"}
```

Python scripts must:
1. Read the file and parse the outer JSON
2. Extract `html_content`
3. Strip `<pre>` tags: `re.sub(r'</?pre[^>]*>', '', text)`
4. Unescape HTML entities: `html.unescape(text)`
5. Parse the inner JSON

The `NIMBLE_API_KEY` is available as the environment variable `$NIMBLE_API_KEY`.

---

## Instructions

### Step 0: Preflight

Run these lightweight checks in parallel — **no API calls, no nimble commands, no curl**:

- `date +%Y-%m-%d` (today)
- `cat ~/.nimble/business-profile.json 2>/dev/null` (profile)
- `cat ~/.nimble/memory/index.md 2>/dev/null` (wiki index)
- `mkdir -p ~/.nimble/memory/{reports,retail-intelligence/rulebooks,retail-intelligence/extractions}`
- `ls ~/.nimble/memory/retail-intelligence/rulebooks/ 2>/dev/null` (existing rulebooks)
- Verify `$NIMBLE_API_KEY` is set: `echo ${NIMBLE_API_KEY:+OK}` — if empty, see `references/profile-and-onboarding.md`, stop

From the results:
- Profile exists -> note industry context if any
- No profile -> fine, proceed to Step 1
- Existing rulebooks -> used in Step 2

**After preflight, proceed directly to Step 1 → Step 2 → Step 3a (nimble map). Do NOT skip ahead to browser-use.**

### Step 1: Parse Request

Extract from `$ARGUMENTS`:

| Field | Required | Source |
|-------|----------|--------|
| Storefront URL | Yes | User input (e.g., "costco.com", "https://www.metro.ca") |
| Country | Recommended | User input or infer from domain TLD |
| Storefront name | Auto | Derive slug from domain (e.g., `metro-ca`, `costco`, `bws`) |

**If URL is missing**, ask: "Which storefront should I investigate? Provide the URL (e.g., https://www.metro.ca)."

**If URL is clear**, confirm and proceed: "Investigating **metro.ca** category structure..."

Normalize the URL: ensure `https://` prefix, strip trailing slashes.

### Step 2: Cross-Reference Existing Rulebooks

**Before probing the site**, check if a sibling domain already has a rulebook:

```bash
ls ~/.nimble/memory/retail-intelligence/rulebooks/*.md 2>/dev/null
```

Sibling domains share the same brand but differ by country TLD (e.g., `costco.ca` ↔ `costco.com`, `metro.ca` ↔ `metro.fr`). If a sibling rulebook exists:

1. Read it — note the API endpoint pattern, response structure, and extraction method
2. **Adapt the URL to the target domain** (e.g., `search.costco.ca/api/...` → `search.costco.com/api/...`)
3. Test the adapted endpoint immediately — this is the fastest path to a working rulebook
4. If it works, skip to Step 5 (classify) with the adapted data

Even if no exact sibling exists, scan all rulebooks for the same **platform** (VTEX, Shopify, Salesforce Commerce Cloud, etc.) — storefronts on the same platform share API patterns.

### Step 3: Discover Category URLs

Discovery runs in two stages. **Start with nimble map** (fast, no browser). Fall back to browser-use only if map yields no usable category patterns.

#### 3a. Nimble map — primary discovery

```bash
nimble map --url "{storefront_url}" --limit 5000 --sitemap include --country "{country}" > /tmp/{slug}_map.json
```

Then write a Python script to `/tmp/{slug}_map_cluster.py` that:
1. Reads `/tmp/{slug}_map.json` and parses the `links` array (`[{url, title, description}]`)
2. Filters noise URLs — skip any path starting with: `/cdn-cgi/`, `/wp-content/`, `/wp-admin/`, `/static/`, `/assets/`, `/images/`, `/img/`, `/css/`, `/js/`, `/api/`, `/graphql`, `/_next/`
3. Skips static pages: `about`, `careers`, `contact`, `faq`, `help`, `login`, `privacy`, `search`, `signin`, `signup`, `support`, `sitemap`
4. Skips asset extensions: `.css`, `.gif`, `.ico`, `.jpg`, `.js`, `.json`, `.pdf`, `.png`, `.svg`, `.woff`, `.xml`
5. Groups remaining URLs by path depth (number of `/`-separated segments)
6. For each depth group, builds a structural mask: a segment position is **fixed** if it has ≤3 unique values or <30% variation across all URLs at that depth; otherwise **variable**
7. Sub-clusters URLs by their fixed segments (variable positions become `*`)
8. Prints a summary table — one row per pattern group, sorted by size descending (top 20):
   ```
   Pattern                        | Size | Example URLs (first 2)
   /shop/{slug}                   |  12  | /shop/dairy, /shop/bakery
   /shop/{slug}/{slug}            |  87  | /shop/dairy/milk, /shop/dairy/cheese
   /products/{slug}               | 5000 | /products/abc-123
   ```
9. Also prints: total URLs collected, total after filtering, recommendation (which pattern(s) look like categories vs products)

Run the script:
```bash
python3 /tmp/{slug}_map_cluster.py
```

**Interpret the output:**
- Pattern groups with depth 1–3 and 5–500 members are likely category pages
- Groups with 1000+ members at depth ≥2 are likely product pages — skip
- If multiple depths exist (e.g., `/shop/{slug}` + `/shop/{slug}/{slug}`), the storefront has a nested hierarchy — note both levels

**If map yields ≥5 clear category URLs → proceed to Step 3d (validate). Skip 3b and 3c.**

#### 3b. Fallback: browser-use navigation (only if map yields < 5 category URLs)

Use `mcp__browser-use__browser_task` with model `claude-sonnet-4-6` and `max_steps: 20`:

> "Go to {storefront_url}. Navigate to the main Shop/Categories/Departments section of the site.
>
> 1. Find and interact with the top-level navigation menu (hover or click on 'Shop', 'Categories', 'Departments', or equivalent)
> 2. Visit at least 2 distinct category pages (e.g., 'Dairy', 'Bakery', or 'Electronics', 'Clothing')
> 3. For each category page, also navigate into one subcategory if available
>
> Return:
> - Every category and subcategory URL you visited
> - Whether the URLs follow a consistent pattern (e.g., `/shop/dairy`, `/shop/dairy/milk`)
> - Any API endpoints that appeared in the network traffic while navigating (JSON responses containing category/navigation data)
> - Whether the navigation required JavaScript rendering (hover menus, dynamic loading)"

After `browser_task` returns a `task_id`, call `monitor_task` to get the results.

Extract from the response:
- Visited category URLs → used for pattern clustering in Step 3d
- Any API endpoints reported from network traffic → validate in Step 3d

#### 3c. Fallback: static API probes (only if both map and browser-use fail)

If neither method found usable category URLs, probe common API patterns via the file-based pipeline:

```bash
# Try common category API endpoints
curl -s -X POST "https://api.webit.live/api/v1/realtime/web" \
  -H "Authorization: Bearer $NIMBLE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url": "{storefront_url}/api/v1/categories", "render": false}' \
  > /tmp/{slug}_probe_api.json
```

Common patterns to try (one at a time until one works):
```
{domain}/api/v1/categories
{domain}/api/navigation
{domain}/api/megamenu
{domain}/api/catalog/categories
{domain}/_next/data/.../categories.json
search.{domain}/api/apps/www_{slug}/query/www_{slug}_megamenu
```

For each probe, write a Python script to read the file, extract `html_content` (strip `<pre>` tags, unescape HTML entities), parse the inner JSON, and print: field names, nesting depth, children key name, sample category names (first 5), total count.

#### 3d. Validate the best source

Once you have candidate category URLs or an API endpoint from any method above:

**For URL patterns from map/browser:** fetch 2–3 example URLs using the file-based pipeline to confirm they are real category pages (contain product listings, subcategory links, or breadcrumbs — not 404s or login walls).

**For API endpoints:** fetch the endpoint via curl → file → Python to confirm it returns structured category data outside the browser context. Document whether `"render": false` or `"render": true` is required.

### Step 4: Determine Extraction Method

Based on what Step 3 found, choose the highest-priority source:

| Priority | Source type | Why |
|----------|-----------|-----|
| **1st** | JSON API returning nested tree | One call, structured, Pattern B |
| **2nd** | Embedded JSON (`__NEXT_DATA__` etc.) | No extra calls, Pattern A/B |
| **3rd** | URL patterns from `nimble map` | Machine-readable, Pattern A — one map call extracts all |
| **4th** | XML sitemap with category URLs | Machine-readable, Pattern A |
| **5th** | Rendered mega-menu HTML | Requires JS rendering, Pattern D |

Read `references/extraction-patterns.md` for the pattern taxonomy.

**Never load raw API responses into context.** If a script fails, read the error, fix the script, and re-run.

### Step 5: Classify the Pattern

Read `references/extraction-patterns.md` and classify this storefront:

| Pattern | Description | Example |
|---------|-------------|---------|
| **A** | Flat list — single response, no nesting | Simple department list |
| **B** | Nested tree — single response, recursive children | VTEX `submenu[]` trees |
| **C1** | Fixed-depth multi-request — known number of levels | Aisle IDs -> per-aisle subcategories |
| **C2** | Self-expanding — drill down until leaf nodes | `/cp/` pages that may contain sub-`/cp/` pages |
| **D** | No programmatic categories | Must use browser navigation |

### Step 6: Write the Rulebook

Read `references/rulebook-template.md` for the exact format.

Write the rulebook to: `~/.nimble/memory/retail-intelligence/rulebooks/{slug}.md`

The rulebook must contain:
- **Overview** — 1-2 sentence summary
- **Input** — required parameters with defaults
- **Extraction Method** — which tools and how many calls
- **Step-by-Step Instructions** — exact curl commands (to `api.webit.live`), response parsing, URL construction
- **Response Schema** — example JSON for each level
- **URL Construction** — base URL, pattern, field mapping table
- **Known Issues** — storefront-specific quirks only
- **Category Pattern** — the classified type

Every step must specify:
- The exact curl command with all parameters (URL, headers, body)
- How to parse the response (field paths in the JSON envelope, inner data structure)
- What to collect and pass to the next step

### Step 7: Test the Rulebook

Follow the rulebook steps end-to-end using the file-based pipeline:

1. **Fetch** — run each curl command from the rulebook, redirect to `/tmp/{slug}_test_{step}.json`
2. **Parse** — generate a Python script based on the rulebook's parsing instructions that:
   - Reads each response file
   - Extracts `html_content`, strips `<pre>` tags, unescapes HTML entities
   - Walks the data structure as described in the rulebook
   - Applies skip/filter rules
   - Builds final URLs using the base URL and pattern
   - Deduplicates and sorts
   - Writes results to `/tmp/{slug}_categories_urls.txt`
   - Prints summary: `Store: {slug}\nTotal category URLs: {count}`
3. **Run** the script and check output

**PASS** = `/tmp/{slug}_categories_urls.txt` exists with real category URLs from the storefront.
**FAIL** = fix the rulebook and/or script, re-test. Repeat until PASS.

### Default Behaviors for Python Scripts

- Build retry logic **into the script** (3 retries with 2s/4s/6s backoff)
- Do NOT retry by making multiple tool calls — let the script handle it
- Deduplicate all URLs
- Sort alphabetically
- Write to `/tmp/{slug}_categories_urls.txt` (one URL per line)
- Print summary to stdout

### Step 8: Save to Memory

Make all Write calls simultaneously:

- Rulebook -> already written in Step 6
- Report -> `~/.nimble/memory/reports/storefront-discover-{slug}-{date}.md`
- Follow the wiki update pattern from `references/memory-and-distribution.md`
- Append to `~/.nimble/memory/retail-intelligence/rulebooks/index.md`:
  ```
  | {slug} | {domain} | {country} | {pattern} | {category_count} | {date} |
  ```

### Step 9: Share & Distribute

**Always offer distribution — do not skip this step.** Follow
`references/memory-and-distribution.md` for connector detection and sharing flow.

Notion: full rulebook as a dated subpage.
Slack: TL;DR with storefront name, pattern type, category count.

### Step 10: Follow-ups

- **"Extract categories now"** -> run `storefront-extract` with this rulebook
- **"Investigate another storefront"** -> restart from Step 1
- **"Show the rulebook"** -> display the MD file
- **"Update the rulebook"** -> re-investigate specific steps

**Sibling skill suggestions:**

> **Next steps:**
> - Run `storefront-extract` to extract all category URLs using this rulebook
> - Run `competitor-intel` to monitor this retailer's competitive moves
> - Run `company-deep-dive` for a full 360 profile on this retailer

---

## Sub-Agent Strategy

For multi-step storefronts (pattern C1/C2), use sub-agents to parallelize endpoint testing:

Use `nimble-researcher` agents (`agents/nimble-researcher.md`) when:
- Testing multiple candidate API endpoints simultaneously
- Fetching multiple category pages to verify the pattern

Sub-agent rules: always `mode: "bypassPermissions"`, batch max 4, fallback on failure.

---

## Error Handling

For rate limits and general API errors, see `references/nimble-playbook.md`. Skill-specific errors:

- **Cloudflare/bot protection:** Retry with `--render` flag. If still blocked, note in the rulebook's Known Issues that rendering is required.
- **Empty navigation:** Try alternate URLs (`/sitemap.xml`, `/categories`, `/departments`). Some storefronts hide nav behind JS — use `--render`.
- **No discoverable API:** Fall back to rendered HTML parsing. Document the CSS selectors / DOM structure in the rulebook.
- **Geo-locked content:** If the site returns different content by region, ask the user for a postal code or address and document it as a required input.
- **Rate limiting (429):** Back off and reduce concurrency. Note rate limits in the rulebook's Known Issues.

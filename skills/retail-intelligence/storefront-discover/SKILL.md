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
metadata:
  author: Nimbleway
  version: 0.21.2
---

# Storefront Discover

Reverse-engineer any storefront's category structure into a reusable extraction rulebook.

User request: $ARGUMENTS

**Before running any commands**, read `references/nimble-playbook.md` for constraints.

---

## Instructions

### Step 0: Preflight

Follow the transport selection + standard preflight from `references/nimble-playbook.md` — pick CLI or MCP at session start, then run the standard preflight calls (date calc, today, profile, memory index) in parallel.

Also simultaneously:
- `mkdir -p ~/.nimble/memory/{reports,retail-intelligence/rulebooks,retail-intelligence/extractions}`
- Check for existing rulebooks: `ls ~/.nimble/memory/retail-intelligence/rulebooks/ 2>/dev/null`

From the results:
- CLI missing or API key unset -> `references/profile-and-onboarding.md`, stop
- Tag all `nimble` CLI calls: `nimble --client-source skill-storefront-discover <subcommand>`.
- Profile exists -> note industry context if any
- No profile -> fine, proceed to Step 1

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

### Step 2: Map the Site

Discover the site's structure to find navigation and category endpoints.

```bash
nimble --client-source skill-storefront-discover map --url "{storefront_url}" --limit 30
```

From the sitemap/URL list, identify:
- Navigation pages (`/categories`, `/departments`, `/aisles`, `/browse`, `/shop`)
- API endpoints (`/api/`, `/graphql`, `/__NEXT_DATA__`)
- Patterns in URL structure (path depth, slug conventions)

Save results to `/tmp/storefront_discover_{slug}_map.json`.

### Step 3: Extract Navigation Structure

Fetch the homepage/main navigation with rendering enabled to capture JS-rendered content:

```bash
nimble --client-source skill-storefront-discover extract --url "{storefront_url}" --render --format json > /tmp/storefront_discover_{slug}_nav.json
```

Write a Python script (`/tmp/storefront_discover_{slug}_analyze_nav.py`) that reads the response file and searches for:

1. **Embedded JSON** — look for `__NEXT_DATA__`, `window.__data__`, `window.mobifyData`, or similar global JS objects containing category trees
2. **Navigation HTML** — `<nav>`, `<ul class="menu">`, `data-aisle`, `data-category` attributes
3. **API references** — URLs in the HTML pointing to category/taxonomy/menu endpoints
4. **Mega-menu data** — nested `<li>` structures with category links

Run the script and capture the findings. The goal is to identify which **approach** will work for this storefront.

### Step 4: Test Category Endpoints

Based on Step 3 findings, test the most promising approach. Read `references/extraction-patterns.md` for the pattern taxonomy — identify which pattern this storefront matches.

**Approach A — Embedded JSON (preferred, fastest):**
If `__NEXT_DATA__` or similar embedded JSON was found, extract it and walk the category tree directly. No additional HTTP calls needed.

**Approach B — API endpoint:**
If an API endpoint was discovered (e.g., `/api/categories`, `/mega-menu.json`), fetch it:
```bash
nimble --client-source skill-storefront-discover extract --url "{api_endpoint}" --format json > /tmp/storefront_discover_{slug}_api.json
```

**Approach C — Rendered HTML parsing:**
If categories are only in rendered HTML, extract with rendering:
```bash
nimble --client-source skill-storefront-discover extract --url "{category_page_url}" --render --format markdown > /tmp/storefront_discover_{slug}_rendered.json
```

**Approach D — Multi-step discovery:**
If L1 categories are visible but L2/L3 require drilling down, test a single drill-down to understand the pattern, then document the iteration strategy.

For each approach tested, write the raw response to a file and generate a Python analysis script — **never load raw API responses into context**.

Document what was found:
- Response structure (field names, nesting depth)
- Whether it returns names, URLs, IDs, or all three
- Whether subcategories are inline or require additional calls
- Any authentication, cookies, or headers required

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
- **Step-by-Step Instructions** — exact `nimble extract` commands, response parsing, URL construction
- **Response Schema** — example JSON for each level
- **URL Construction** — base URL, pattern, field mapping table
- **Known Issues** — storefront-specific quirks only
- **Category Pattern** — the classified type

Every step must specify:
- The exact `nimble extract` command with all parameters
- How to parse the response (field paths, regex if needed)
- What to collect and pass to the next step

### Step 7: Test the Rulebook

Run `storefront-extract` (or manually follow the rulebook steps) to verify:
1. Each API call returns expected data
2. The parsing instructions produce valid URLs
3. The URL construction pattern produces working links
4. The total URL count is reasonable for the storefront

**PASS** = output file exists with real category URLs from the storefront.
**FAIL** = fix the rulebook, re-test. Repeat until PASS.

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

Follow the sub-agent spawning rules from `references/nimble-playbook.md`
(bypassPermissions, batch max 4, fallback on failure).

---

## Error Handling

See `references/nimble-playbook.md` for the standard error table. Skill-specific errors:

- **Cloudflare/bot protection:** Retry with `--render` flag. If still blocked, note in the rulebook's Known Issues that rendering is required.
- **Empty navigation:** Try alternate URLs (`/sitemap.xml`, `/categories`, `/departments`). Some storefronts hide nav behind JS — use `--render`.
- **No discoverable API:** Fall back to rendered HTML parsing. Document the CSS selectors / DOM structure in the rulebook.
- **Geo-locked content:** If the site returns different content by region, ask the user for a postal code or address and document it as a required input.
- **Rate limiting (429):** Back off and reduce concurrency. Note rate limits in the rulebook's Known Issues.

# Rulebook Template

This is the exact structure that `category-discover` must produce. Every rulebook follows this format so that `category-extract` can parse and execute it mechanically.

---

## Template

````markdown
# {Storefront Name} — Category Extraction Rules

**Domain:** {domain}
**Country:** {country_code}
**Last verified:** {YYYY-MM-DD}

## Overview

{1-2 sentence summary: how categories are structured, how many levels, how many API calls needed, approximate category count if known.}

## Input

{Declare ALL required inputs. Use a table:}

| Parameter | Required | Description | Default |
|-----------|----------|-------------|---------|
| `{param}` | Yes/No | {what it is} | {default value or "None — caller must provide"} |

{If no input is needed (national catalog, hardcoded URL), state:}
No input required. {Explain why — e.g., "The megamenu API returns a national catalog."}

## Extraction Method

**Primary method:** {e.g., "Nimble Extract — single call, returns full tree" or "Nimble Extract — 2-step: aisle IDs + per-aisle tree fetch"}

## Step-by-Step Instructions

### Step 1: {description}

**Tool:** `nimble extract`
**Command:**
```bash
nimble extract --url "{url}" --render --format json
```

**Response format:** {description of what comes back — e.g., "JSON with `departments[]` array"}

**Parse:** {Exact instructions:}
1. {Extract field X from the response}
2. {Filter/skip rules}
3. {What to collect for the next step}

### Step 2: {description}

**Tool:** `nimble extract`
**For each:** {what to iterate over from Step 1}
**Command:**
```bash
nimble extract --url "{url_pattern_with_variables}" --format json
```

**Concurrency:** {e.g., "Max 3 concurrent requests" or "Sequential with 2s delay"}

**Response format:** {description}
**Parse:** {how to extract subcategories}

### Step N: Build URLs

**Base URL:** `{base}`
**Pattern:** `{base}/{path_pattern}`
**Variables:** {where each part comes from}

## Response Schema

### Level 1 ({name — e.g., Departments})
```json
{
  "name": "Grocery",
  "url": "/grocery",
  "children": [...]
}
```

### Level 2 ({name — e.g., Categories})
```json
{
  "name": "Fresh Produce",
  "url": "/grocery/fresh-produce",
  "children": [...]
}
```

### Level 3 ({name — e.g., Subcategories, if applicable})
```json
{
  "name": "Fruits",
  "url": "/grocery/fresh-produce/fruits",
  "children": []
}
```

## URL Construction

**Base URL:** `{base}`
**Pattern:** `{base}{url_field}`

| Level | Source field | Example |
|-------|-------------|---------|
| L1 | `{field_name}` | `/grocery` |
| L2 | `{field_name}` | `/grocery/fresh-produce` |
| L3 | `{field_name}` | `/grocery/fresh-produce/fruits` |

## Known Issues

{ONLY include store-specific issues. Examples:}
- {Cloudflare blocks direct calls — `--render` is required}
- {Response intermittently returns empty data — retry resolves this}
- {Category names contain HTML entities — unescape before use}
- {Locale prefix in URLs must be normalized}

{If there are no known issues, omit this section.}

## Category Pattern

**Type:** {A/B/C1/C2/D} — {one-line description, e.g., "Single response, nested tree with 3 levels"}
````

---

## Writing Guidelines

- **Be specific, not vague.** Every `nimble extract` command must include the exact URL or URL pattern with placeholders. "Fetch the categories" is not enough.
- **Document the response, not just the request.** Show the JSON structure with actual field names from the tested response.
- **One step per API call.** If the extraction requires 3 API calls, document 3 steps (plus a final URL-building step).
- **Field names are sacred.** Use the exact field names from the API response (`categoryName`, not `category_name`). Case matters.
- **Include skip/filter rules.** If certain categories should be excluded (e.g., "Specials", "The Drop", promotional pages), document them explicitly.
- **Document the children key.** If the tree uses `submenu`, say `submenu`. If it uses `children`, say `children`. Never say "subcategories array" generically.
- **URL construction must be unambiguous.** Given a leaf node, the reader must be able to construct the full URL without guessing.

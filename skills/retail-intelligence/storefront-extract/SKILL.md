---
name: storefront-extract
description: |
  Extracts all category and subcategory URLs from an ecommerce storefront
  by following a rulebook produced by storefront-discover. Uses a file-based
  pipeline — API responses are saved to temp files, parsed by generated Python
  scripts, and only the extracted URLs enter the conversation. Keeps context
  small regardless of response size.

  Triggers: "extract categories for X", "get category URLs from X",
  "run category extraction", "scrape X categories", "list all categories on",
  "get the category tree for".

  Do NOT use for investigating a new storefront — use storefront-discover first.
  Do NOT use for product scraping — this skill only extracts category URLs.
allowed-tools:
  - Bash(nimble:*)
  - Bash(date:*)
  - Bash(cat:*)
  - Bash(mkdir:*)
  - Bash(python3:*)
  - Bash(echo:*)
  - Bash(jq:*)
  - Bash(ls:*)
  - Bash(wc:*)
  - Bash(head:*)
  - Bash(tail:*)
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

# Storefront Extract

Extract all category URLs from a storefront using its rulebook.

User request: $ARGUMENTS

**Before running any commands**, read `references/nimble-playbook.md` for constraints.

---

## Instructions

### Step 0: Preflight

Follow the transport selection + standard preflight from `references/nimble-playbook.md` — pick CLI or MCP at session start, then run the standard preflight calls (date calc, today, profile, memory index) in parallel.

Also simultaneously:
- `mkdir -p ~/.nimble/memory/{reports,retail-intelligence/rulebooks,retail-intelligence/extractions}`
- List available rulebooks: `ls ~/.nimble/memory/retail-intelligence/rulebooks/*.md 2>/dev/null`

From the results:
- CLI missing or API key unset -> `references/profile-and-onboarding.md`, stop
- Tag all `nimble` CLI calls: `nimble --client-source skill-storefront-extract <subcommand>`.
- Profile exists -> note context if any
- No profile -> fine, proceed to Step 1

### Step 1: Load the Rulebook

Parse `$ARGUMENTS` for the storefront name or slug.

| Field | Required | Source |
|-------|----------|--------|
| Storefront name/slug | Yes | User input (e.g., "costco", "metro-ca") |
| Extraction params | Optional | User input (e.g., "zip_code=M5V 3L9") |

Look for the rulebook at:
```
~/.nimble/memory/retail-intelligence/rulebooks/{slug}.md
```

**If not found**, list available rulebooks and suggest:
- "No rulebook found for **{slug}**. Available: {list}. Run `storefront-discover` first to create one."

**If found**, read the entire rulebook into context — it is the instruction set for everything that follows.

### Step 2: Check Inputs

Read the rulebook's `## Input` section.

- If inputs are required and provided in `$ARGUMENTS`, use them
- If inputs are required with defaults and user didn't specify, use the defaults
- If inputs are required with no defaults and user didn't provide them, ask once:
  "The **{storefront}** rulebook requires: {param_list}. Please provide values."
- If no inputs are required, proceed immediately

### Step 3: Plan the Pipeline

From the rulebook, identify:

| Element | Where in rulebook |
|---------|-------------------|
| Number of API calls | Count the `### Step N` sections |
| URL/params per call | `**Command:**` block in each step |
| Response parsing logic | `**Parse:**` section in each step |
| URL construction pattern | `## URL Construction` section |
| Skip/filter rules | Mentioned in `**Parse:**` or `## Known Issues` |
| Children key for tree-walking | `## Response Schema` section |
| Concurrency guidance | `**Concurrency:**` in multi-request steps |

### Step 4: Execute the Pipeline

**Read `references/file-pipeline-pattern.md` for the detailed execution pattern.**

For each step in the rulebook, follow the three-phase file-based pipeline:

#### Phase 1: Fetch and save to file

Execute the `nimble extract` command from the rulebook step, redirecting output to a temp file:

```bash
nimble --client-source skill-storefront-extract extract --url "{url}" --format json > /tmp/{slug}_raw_{step_num}.json
```

The raw response **NEVER** enters the conversation context. It goes straight to a file.

#### Phase 2: Generate a parsing script

Based on the rulebook's parsing instructions for this step, write a Python script to `/tmp/{slug}_parse_{step_num}.py` that:

1. Reads the raw response file
2. Extracts the content from the API response wrapper (`html_content` field, strip `<pre>` tags, unescape HTML entities)
3. Parses JSON
4. Walks the data structure exactly as described in the rulebook
5. Applies skip/filter rules from the rulebook
6. Outputs structured data (URLs, IDs for next step, or both)

**Script requirements:**
- All HTTP calls use `subprocess.run(["nimble", ...])` — never raw `requests` or `urllib`
- Build retry logic into the script (3 retries with 2s/4s/6s backoff)
- Handle missing fields gracefully (skip, don't crash)
- Print progress to stderr: `Step {n}: processing {count} items...`

#### Phase 3: Run the script

```bash
python3 /tmp/{slug}_parse_{step_num}.py
```

If the script fails, read the error, fix the script, and re-run. Do not retry more than 3 times per script — if it keeps failing, the rulebook instructions may need updating.

### Step 5: Build Final URLs

After all pipeline steps complete, run the final URL construction.

Write `/tmp/{slug}_build_urls.py` that:
1. Reads the intermediate results from previous steps
2. Applies the URL construction pattern from the rulebook's `## URL Construction` section
3. Deduplicates all URLs
4. Sorts alphabetically
5. Writes to `/tmp/{slug}_categories_urls.txt` (one URL per line)
6. Prints summary to stdout:
   ```
   Storefront: {name}
   Total category URLs: {count}
   Pattern: {type}
   ```

Run it:
```bash
python3 /tmp/{slug}_build_urls.py
```

### Step 6: Verify

Check the output:
- `/tmp/{slug}_categories_urls.txt` exists and has content
- URL count is reasonable for the storefront (10-1000+ depending on size)
- URLs follow the expected pattern from the rulebook
- Spot-check 3-5 URLs by fetching them to confirm they resolve

If the count is 0 or suspiciously low, re-check the pipeline. Common issues:
- Response wrapper not stripped (still has `html_content` envelope)
- Wrong children key for tree-walking
- Filter rules too aggressive

### Step 7: Output

Display the results:

```
# Category Extraction: {Storefront Name}
*{count} category URLs extracted | {date} | Pattern: {type}*

## Summary
- **Storefront:** {name} ({domain})
- **Categories extracted:** {count} unique URLs
- **Extraction method:** {from rulebook}
- **Inputs used:** {param=value, or "None"}

## Sample URLs (first 20)
| # | URL |
|---|-----|
| 1 | https://example.com/category/fruits |
| 2 | https://example.com/category/vegetables |
...

## Full Results
Saved to: `/tmp/{slug}_categories_urls.txt`
```

### Step 8: Save to Memory

Make all Write calls simultaneously:

- Results -> `~/.nimble/memory/retail-intelligence/extractions/{slug}-{date}.json`
  ```json
  {
    "storefront": "{slug}",
    "domain": "{domain}",
    "extracted_at": "{ISO timestamp}",
    "inputs": {"param": "value"},
    "pattern": "{type}",
    "total_urls": {count},
    "urls": ["..."]
  }
  ```
- Report -> `~/.nimble/memory/reports/storefront-extract-{slug}-{date}.md`
- Follow the wiki update pattern from `references/memory-and-distribution.md`

### Step 9: Share & Distribute

**Always offer distribution — do not skip this step.** Follow
`references/memory-and-distribution.md` for connector detection and sharing flow.

Notion: summary table + full URL list as a dated subpage.
Slack: TL;DR with storefront name, category count, and extraction date.

### Step 10: Follow-ups

- **"Show all URLs"** -> cat `/tmp/{slug}_categories_urls.txt`
- **"Export as CSV"** -> generate CSV with url, storefront, extracted_at columns
- **"Compare with last run"** -> diff against previous extraction in memory
- **"Extract again"** -> re-run from Step 4 (same rulebook, fresh data)
- **"Update the rulebook"** -> run `storefront-discover` to re-investigate

**Sibling skill suggestions:**

> **Next steps:**
> - Run `storefront-discover` to investigate a new storefront
> - Run `competitor-intel` to monitor this retailer's competitive landscape
> - Compare extractions over time to detect category changes

---

## Sub-Agent Strategy

For multi-request storefronts (pattern C1/C2), use sub-agents to parallelize fetching:

Use `nimble-researcher` agents (`agents/nimble-researcher.md`) when:
- Fetching L2 subcategories for 10+ L1 categories simultaneously
- Processing large result sets in parallel

Follow the sub-agent spawning rules from `references/nimble-playbook.md`
(bypassPermissions, batch max 4, fallback on failure).

---

## Error Handling

See `references/nimble-playbook.md` for the standard error table. Skill-specific errors:

- **Rulebook not found:** Guide user to run `storefront-discover` first. List available rulebooks.
- **API response structure changed:** If parsing fails because field names don't match the rulebook, warn the user and suggest re-running `storefront-discover` to update.
- **Empty results after parsing:** Check the response wrapper — most common cause is not stripping `html_content` or `<pre>` tags. See `references/file-pipeline-pattern.md`.
- **Rate limiting on multi-request extraction:** Reduce concurrency, increase delay. Note in output that extraction was throttled.
- **Partial extraction failure:** If some L1 categories succeed but others fail, report partial results with a warning listing which categories failed.

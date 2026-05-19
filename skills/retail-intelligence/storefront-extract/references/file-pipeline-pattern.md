# File-Based Pipeline Pattern

The core execution pattern for `storefront-extract`. Every API response is written to a temp file, processed by a generated Python script, and only the script output (extracted URLs or IDs) enters the conversation.

This keeps the LLM context small regardless of API response size — some storefront responses are 1MB+.

---

## Three-Phase Pattern

For every API call in the rulebook, follow these three phases in order.

### Phase 1: Fetch and save to file

Execute the `nimble extract` command from the rulebook and redirect output to a temp file:

```bash
nimble --client-source skill-storefront-extract extract \
  --url "{url_from_rulebook}" \
  --format json \
  > /tmp/{slug}_raw_{step_num}.json
```

With rendering (when rulebook specifies `--render`):
```bash
nimble --client-source skill-storefront-extract extract \
  --url "{url_from_rulebook}" \
  --render \
  --format json \
  > /tmp/{slug}_raw_{step_num}.json
```

**Rules:**
- Always redirect to file with `>` — the response must NOT enter the conversation
- Use descriptive filenames: `{slug}_raw_{step}_{item}.json` for per-item fetches
- Verify the file was created and is non-empty: `wc -c /tmp/{slug}_raw_{step_num}.json`
- If the file is empty or the command failed, retry once before reporting an error

### Phase 2: Generate a parsing script

Write a Python script to `/tmp/{slug}_parse_{step_num}.py` based on the rulebook's parsing instructions.

**Script template:**

```python
import json
import html
import re
import sys
import os
import time
import subprocess

SLUG = "{slug}"
STEP = "{step_num}"
INPUT_FILE = f"/tmp/{SLUG}_raw_{STEP}.json"
OUTPUT_FILE = f"/tmp/{SLUG}_parsed_{STEP}.json"

def unwrap_response(filepath):
    """Extract inner data from the Nimble API response envelope."""
    with open(filepath, "r") as f:
        raw = json.load(f)

    content = raw.get("html_content", "")
    if not content:
        content = raw.get("content", "")
    if not content:
        return raw

    # Strip <pre> tags if present
    content = re.sub(r"</?pre[^>]*>", "", content)
    # Unescape HTML entities
    content = html.unescape(content)
    # Parse inner JSON
    return json.loads(content)

def fetch_with_retry(url, output_path, max_retries=3):
    """Fetch a URL via nimble extract with retry logic."""
    for attempt in range(max_retries):
        result = subprocess.run(
            ["nimble", "--client-source", "skill-storefront-extract",
             "extract", "--url", url, "--format", "json"],
            capture_output=True, text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            with open(output_path, "w") as f:
                f.write(result.stdout)
            return True
        delay = (attempt + 1) * 2
        print(f"Retry {attempt + 1}/{max_retries} after {delay}s...", file=sys.stderr)
        time.sleep(delay)
    return False

def main():
    data = unwrap_response(INPUT_FILE)

    # --- RULEBOOK-SPECIFIC PARSING GOES HERE ---
    # Walk the data structure as described in the rulebook
    # Apply skip/filter rules
    # Collect results
    results = []

    # ... parsing logic based on rulebook instructions ...

    # Write results
    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Step {STEP}: extracted {len(results)} items", file=sys.stderr)

if __name__ == "__main__":
    main()
```

**Customization points** (the parts that change per rulebook step):
- `unwrap_response` — adjust if the response format differs from standard
- The main parsing logic — field names, tree-walking, filter rules, all from the rulebook
- `fetch_with_retry` — only include if this step makes additional HTTP calls (multi-request patterns)

### Phase 3: Run the script

```bash
python3 /tmp/{slug}_parse_{step_num}.py
```

**On success:** The script writes results to `/tmp/{slug}_parsed_{step_num}.json` and prints a summary to stderr.

**On failure:**
1. Read the error message
2. Fix the script (most common issues below)
3. Re-run
4. Max 3 fix attempts per script — if still failing, the rulebook may need updating

---

## Common Response Formats

### Standard JSON with `html_content` envelope

Most Nimble responses wrap the actual data:
```json
{
  "url": "...",
  "status": "success",
  "html_content": "{ ... actual JSON string ... }"
}
```

The `unwrap_response` function in the template handles this. Extract `html_content` and parse it as JSON.

### HTML-wrapped JSON (inside `<pre>` tags)

Some endpoints return JSON inside HTML `<pre>` tags:
```json
{
  "html_content": "<pre>{ \"categories\": [...] }</pre>"
}
```

The template's `re.sub(r"</?pre[^>]*>", "", content)` handles this. Always also run `html.unescape()` to fix `&amp;`, `&lt;`, etc.

### Rendered HTML (no JSON)

When `--render` is used and the response is HTML:
```json
{
  "html_content": "<html><head>...</head><body>...</body></html>"
}
```

Parse with regex or a simple HTML parser. Look for:
- `<script id="__NEXT_DATA__">` — embedded JSON in Next.js apps
- `data-*` attributes on navigation elements
- `<a href="...">` links in category navigation

### Direct JSON (no envelope)

Some endpoints return clean JSON without a wrapper. The `unwrap_response` function falls through to `return raw` in this case.

---

## Multi-Request Pipeline

For Pattern C1/C2 storefronts, the script from an earlier step produces a list of IDs/URLs that feed into the next step.

**Chaining pattern:**

```python
# Step 1 output: /tmp/{slug}_parsed_1.json -> list of aisle IDs
# Step 2 script reads Step 1 output and fetches each aisle

def main():
    with open(f"/tmp/{SLUG}_parsed_1.json") as f:
        aisle_ids = json.load(f)

    all_categories = []
    for i, aisle_id in enumerate(aisle_ids):
        url = f"https://example.com/api/aisle/{aisle_id}"
        output_path = f"/tmp/{SLUG}_raw_2_{aisle_id}.json"

        print(f"Fetching aisle {i+1}/{len(aisle_ids)}: {aisle_id}", file=sys.stderr)

        if not fetch_with_retry(url, output_path):
            print(f"WARN: Failed to fetch aisle {aisle_id}", file=sys.stderr)
            continue

        data = unwrap_response(output_path)
        categories = walk_tree(data)  # tree-walking from rulebook
        all_categories.extend(categories)

        time.sleep(1)  # rate limiting

    with open(OUTPUT_FILE, "w") as f:
        json.dump(all_categories, f, indent=2, ensure_ascii=False)

    print(f"Step 2: extracted {len(all_categories)} categories from {len(aisle_ids)} aisles", file=sys.stderr)
```

---

## Final URL Builder

The last script in the pipeline collects all parsed results and builds the final URL list:

```python
import json

SLUG = "{slug}"
BASE_URL = "{base_url_from_rulebook}"

def main():
    # Read all parsed results
    with open(f"/tmp/{SLUG}_parsed_final.json") as f:
        categories = json.load(f)

    urls = set()
    for cat in categories:
        url_field = cat.get("url", "")
        if url_field.startswith("http"):
            urls.add(url_field)
        elif url_field.startswith("/"):
            urls.add(f"{BASE_URL}{url_field}")
        else:
            urls.add(f"{BASE_URL}/{url_field}")

    sorted_urls = sorted(urls)

    with open(f"/tmp/{SLUG}_categories_urls.txt", "w") as f:
        for url in sorted_urls:
            f.write(url + "\n")

    print(f"Storefront: {SLUG}")
    print(f"Total category URLs: {len(sorted_urls)}")

if __name__ == "__main__":
    main()
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Empty output file | Response envelope not unwrapped | Check `unwrap_response` — add `html_content` extraction |
| `JSONDecodeError` | `<pre>` tags not stripped | Add `re.sub(r"</?pre[^>]*>", "", content)` |
| `KeyError` on field name | Response structure differs from rulebook | Print the actual keys and update the script |
| 0 URLs after tree-walk | Wrong children key | Check `Response Schema` in rulebook for the exact key name |
| Duplicate URLs | No deduplication | Use `set()` before writing output |
| HTML entities in names | `&amp;` etc. not unescaped | Add `html.unescape(content)` before JSON parsing |
| Script hangs | Rate limiting / no timeout on fetch | Add timeout to `subprocess.run` and reduce concurrency |

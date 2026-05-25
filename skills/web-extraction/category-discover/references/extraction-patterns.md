# Category Extraction Patterns

Reference for classifying site category structures. Use during Step 5 of `category-discover` to identify the pattern type, and when writing the rulebook's extraction steps.

---

## Pattern Taxonomy

### Pattern A — Flat List

**Single response, no nesting.** One API call returns all categories as a flat array. No tree-walking needed.

**Characteristics:**
- Response is an array of objects, each with `name` and `url`
- No `children`, `subcategories`, or nested arrays
- Typically < 50 categories

**Extraction:** One `nimble extract` call, iterate the array, build URLs.

**Example response:**
```json
{
  "categories": [
    {"name": "Fruits", "url": "/fruits"},
    {"name": "Vegetables", "url": "/vegetables"},
    {"name": "Dairy", "url": "/dairy"}
  ]
}
```

---

### Pattern B — Nested Tree

**Single response, recursive children.** One API call returns the full category hierarchy as a tree with a known children key.

**Characteristics:**
- Response has a root array of top-level categories
- Each category may have a `children`, `subcategories`, `submenu`, `internalMenu`, or `subagrupaciones` key
- Tree depth is typically 2-4 levels
- Leaf nodes have an empty children array or no children key

**Extraction:** One `nimble extract` call, then recursively walk the tree to collect leaf URLs.

**Tree-walking algorithm:**
```
function collect_leaves(node, results):
    children_key = identify_children_key(node)  # submenu, children, etc.
    if node[children_key] is empty or absent:
        results.append(node)  # leaf node
    else:
        for child in node[children_key]:
            collect_leaves(child, results)
```

**Leaf detection rules:**
- `children` is `[]` (empty array)
- `children` key is absent
- `final` field is `true` (some platforms use an explicit flag)
- Node has a `product_count` > 0 but no subcategories

**Example response:**
```json
{
  "departments": [
    {
      "name": "Grocery",
      "url": "/grocery",
      "submenu": [
        {
          "name": "Fresh Produce",
          "url": "/grocery/fresh-produce",
          "internalMenu": [
            {"name": "Fruits", "url": "/grocery/fresh-produce/fruits"},
            {"name": "Vegetables", "url": "/grocery/fresh-produce/vegetables"}
          ]
        }
      ]
    }
  ]
}
```

---

### Pattern C1 — Fixed-Depth Multi-Request

**Known number of levels, multiple API calls.** The first call returns L1 identifiers (aisle IDs, department slugs), and a second call per L1 item returns its subtree.

**Characteristics:**
- Step 1: fetch a list of top-level IDs/slugs
- Step 2: for each ID, fetch its subcategory tree
- The depth is known in advance (usually 2-3 levels)
- Subcategory responses may be trees (combine with Pattern B walking)

**Extraction:** Multiple `nimble extract` calls. First call for L1, then one call per L1 item for L2+.

**Concurrency guidance:**
- Max 3-5 concurrent requests to avoid rate limiting
- Add 1-2 second delay between sequential calls
- Build retry logic into the parsing script (3 retries, 2s/4s/6s backoff)

**Example flow:**
```
Step 1: GET /api/aisles -> ["000006", "000008", "000010"]
Step 2: GET /api/aisle/000006 -> {id: "000006", name: "Fruits & Veg", children: [...]}
Step 2: GET /api/aisle/000008 -> {id: "000008", name: "Dairy", children: [...]}
```

---

### Pattern C2 — Self-Expanding

**Unknown depth, recursive drill-down.** Some URLs are leaf pages, others are intermediate pages that contain further subcategory links. Must recursively follow non-leaf URLs.

**Characteristics:**
- Initial call returns a mix of leaf and non-leaf URLs
- Leaf vs non-leaf is determined by URL pattern (e.g., `/browse/` = leaf, `/cp/` = non-leaf)
- Non-leaf pages must be fetched to discover deeper URLs
- Depth is variable — some branches are 2 levels, others 4+

**Extraction:** Recursive `nimble extract` calls with a depth limit (typically max 4). Track visited URLs to avoid cycles.

**Leaf detection heuristics:**
- URL contains `/browse/`, `/shop/`, `/product-list/` -> leaf
- URL contains `/cp/`, `/category/`, `/department/` -> non-leaf, drill deeper
- Page has no subcategory links -> leaf (fallback)

**Example flow:**
```
Step 1: GET /departments -> ["/cp/grocery", "/browse/electronics", "/cp/household"]
Step 2: GET /cp/grocery -> ["/browse/fruits", "/cp/dairy", "/browse/bakery"]
Step 3: GET /cp/dairy -> ["/browse/milk", "/browse/cheese", "/browse/yogurt"]
(Stop: all results are /browse/ leaves)
```

---

### Pattern D — No Programmatic Categories

**No API, no embedded data.** Categories are only accessible through browser interaction (clicking menus, hovering over navigation). This is the last resort.

**Characteristics:**
- No discoverable API endpoints
- No embedded JSON (`__NEXT_DATA__`, etc.)
- Navigation requires JS interaction (hover menus, click-to-expand)
- Cloudflare or heavy bot protection

**Extraction:** Use `nimble extract` with `--render` and parse the rendered HTML. May need to extract category links from the DOM structure using CSS selectors or regex patterns.

---

## URL Construction Patterns

Every rulebook must document how to build the final category URLs from the extracted data.

### Common patterns

| Pattern | Example | When to use |
|---------|---------|-------------|
| **Relative path append** | `{base}{node.url}` | URL field starts with `/` |
| **Slug assembly** | `{base}/aisles/{l1_slug}/{l2_slug}` | Each level has a slug field |
| **API URL with params** | `{base}/api/products?category={id}&store={store_id}` | Product listing via API |
| **Full URL in response** | Use `node.url` as-is | URL field contains `https://` |

### URL cleaning checklist

- Strip tracking parameters (`?icid=`, `?utm_`, `?ref=`)
- Fix double slashes (`//` in path)
- Ensure `https://` prefix for relative URLs
- URL-decode if encoded (`%20` -> space)
- Handle locale prefixes (`/en/`, `/fr/`) consistently

---

## Response Wrapper Formats

Nimble API responses typically have an envelope. The parsing script must unwrap it first.

### Standard JSON envelope
```json
{
  "url": "...",
  "status": "success",
  "html_content": "{ ... actual JSON ... }"
}
```
Extract `html_content`, then parse as JSON.

### HTML-wrapped JSON
```json
{
  "html_content": "<pre>{ ... JSON ... }</pre>"
}
```
Strip `<pre>` tags, unescape HTML entities (`&amp;` -> `&`), then parse as JSON.

### Rendered HTML
```json
{
  "html_content": "<html>...</html>"
}
```
Parse as HTML — extract data from DOM elements, `<script>` tags, or `data-*` attributes.

### Markdown format
When using `--format markdown`, the response is clean text. Parse for links, headings, or structured content.

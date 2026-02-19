# Building `params` from `input_schema`

This guide explains how to read an agent's `input_schema` and construct the
`params` dict for `nimble_agents_run`.

## What input_schema looks like

Every agent's `input_schema` follows standard JSON Schema format:

```json
{
  "type": "object",
  "properties": {
    "url": {
      "type": "string",
      "description": "Target page URL"
    },
    "query": {
      "type": "string",
      "description": "Search keywords to filter results"
    }
  },
  "required": ["url"]
}
```

Key fields:
- `properties` -- each key is a parameter name, each value describes its type and purpose.
- `required` -- array of parameter names that must be provided. If missing, treat all properties as optional.

## Mapping schema properties to params

The `params` dict passed to `nimble_agents_run` should contain one key per
property in the schema. Required properties must always be included; optional
properties can be omitted.

**Schema:**

```json
{
  "properties": {
    "url": { "type": "string", "description": "Product page URL" },
    "locale": { "type": "string", "description": "Locale code (e.g. en_US)" }
  },
  "required": ["url"]
}
```

**Resulting params:**

```json
{
  "url": "https://www.example.com/product/123",
  "locale": "en_US"
}
```

Or, omitting the optional `locale`:

```json
{
  "url": "https://www.example.com/product/123"
}
```

## Required vs optional properties

| Aspect | Required | Optional |
|--------|----------|----------|
| Listed in `required` array | Yes | No |
| Must be in `params` | Yes | No |
| Missing value behavior | Agent run will fail | Agent uses default or ignores |
| When to prompt the user | Always, if not inferrable | Only if relevant to the task |

Rule of thumb: only ask the user for missing **required** parameters. Fill
optional parameters when you can infer them from context; otherwise omit them.

## Common patterns

### Pattern 1: URL-only agents

The most common pattern. The agent takes a single required URL.

**Schema:**

```json
{
  "properties": {
    "url": { "type": "string", "description": "Target page URL" }
  },
  "required": ["url"]
}
```

**Params:**

```json
{ "url": "https://www.amazon.com/dp/B0DGHRT7PS" }
```

### Pattern 2: URL with search query

Agents for search or listing pages often need a query alongside the URL.

**Schema:**

```json
{
  "properties": {
    "url": { "type": "string", "description": "Website base URL" },
    "query": { "type": "string", "description": "Search terms" }
  },
  "required": ["url", "query"]
}
```

**Params:**

```json
{ "url": "https://www.amazon.com", "query": "wireless earbuds" }
```

### Pattern 3: Multi-parameter agents

Some agents accept several parameters for filtering or configuration.

**Schema:**

```json
{
  "properties": {
    "url": { "type": "string", "description": "Listings page URL" },
    "min_price": { "type": "number", "description": "Minimum price filter" },
    "max_price": { "type": "number", "description": "Maximum price filter" },
    "sort_by": { "type": "string", "description": "Sort order: price_asc, price_desc, rating" }
  },
  "required": ["url"]
}
```

**Params (all fields):**

```json
{
  "url": "https://www.example.com/listings",
  "min_price": 20,
  "max_price": 100,
  "sort_by": "rating"
}
```

**Params (required only):**

```json
{
  "url": "https://www.example.com/listings"
}
```

### Pattern 4: Identifier-based agents

Many ecommerce and catalog agents take a product identifier instead of (or in
addition to) a URL. The identifier name varies by site.

**Schema (Amazon — ASIN):**

```json
{
  "properties": {
    "asin": { "type": "string", "description": "Amazon Standard Identification Number" }
  },
  "required": ["asin"]
}
```

**Params:**

```json
{ "asin": "B0CCZ1L489" }
```

**Schema (Walmart / Target — product_id):**

```json
{
  "properties": {
    "product_id": { "type": "string", "description": "Product identifier" }
  },
  "required": ["product_id"]
}
```

**Params:**

```json
{ "product_id": "436473700" }
```

### Pattern 5: Keyword/search agents

Search/SERP agents typically accept a `keyword` parameter and return a list of
matching records rather than a single product detail.

**Schema:**

```json
{
  "properties": {
    "keyword": { "type": "string", "description": "Search query" }
  },
  "required": ["keyword"]
}
```

**Params:**

```json
{ "keyword": "wireless headphones" }
```

### Pattern 6: No URL parameter

Rare, but some agents operate on a fixed domain and only need non-URL inputs.

**Schema:**

```json
{
  "properties": {
    "username": { "type": "string", "description": "Profile username to look up" }
  },
  "required": ["username"]
}
```

**Params:**

```json
{ "username": "johndoe" }
```

## Type mapping reference

| Schema type | JSON/Python type | Example value |
|-------------|-----------------|---------------|
| `string` | string / str | `"https://example.com"` |
| `number` | number / float | `29.99` |
| `integer` | integer / int | `10` |
| `boolean` | boolean / bool | `true` |
| `array` | array / list | `["tag1", "tag2"]` |
| `object` | object / dict | `{"key": "value"}` |

## Checklist for building params

1. Retrieve the agent's details with `nimble_agents_get`.
2. Read `input_schema.properties` to see all available parameters.
3. Read `input_schema.required` to identify which are mandatory.
4. Map values from the user's request to matching parameter names.
5. Prompt the user for any required values you cannot infer.
6. Construct the `params` dict with the correct types.
7. Pass `params` to `nimble_agents_run`.

# Building `params` from `input_properties`

This guide explains how to read an agent's `input_properties` and construct the
`params` dict for `nimble_agents_run`.

## What `input_properties` looks like

Every agent returned by `nimble_agents_get` includes an `input_properties` array.
Each element describes one input parameter:

```json
[
  {
    "name": "query",
    "required": true,
    "type": "string",
    "description": "Search term",
    "rules": ["minLength: 1"],
    "examples": ["donald trump"],
    "default": null
  },
  {
    "name": "country",
    "required": false,
    "type": "string",
    "description": "exit country",
    "rules": ["minLength: 2"],
    "examples": ["US", "DE"],
    "default": "US"
  }
]
```

Key fields per property:
- `name` — parameter name to use in the `params` dict.
- `required` — boolean. If `true`, must be provided.
- `type` — data type (`"string"`, `"integer"`, etc.).
- `description` — what the parameter controls.
- `examples` — sample values. Use these to guide inference.
- `default` — default value if omitted (`null` = no default, must provide if required).
- `rules` — validation constraints (e.g. `"minLength: 1"`).

## Mapping input_properties to params

The `params` dict for `nimble_agents_run` maps 1:1 to `input_properties` names. Include all properties where `required: true`; optional ones can be omitted.

**Rule:** Only ask the user for missing **required** parameters that cannot be inferred from context. Fill optional parameters when inferable; otherwise omit them.

> **See also:** `references/sdk-patterns.md` > "Agent Parameters" for a quick-reference table of common parameter patterns.

## Presenting schema to the user

When presenting agent schema before running, show a markdown table of input parameters:

| Parameter | Required | Type | Description | Example |
|-----------|----------|------|-------------|---------|
| `query` | Yes | string | Search term | `"donald trump"` |
| `country` | No | string | Country code (default: US) | `"US"` |

Also note key output fields from the `skills` dict so the user knows what data to expect.

## Common patterns

### URL-based agents

Most agents take a required `url` and optionally additional parameters.

**Example — input_properties with optional filters:**

```json
[
  { "name": "url", "required": true, "type": "string", "description": "Target page URL", ... },
  { "name": "query", "required": false, "type": "string", "description": "Search filter", ... }
]
```

**Params (required only):** `{ "url": "https://www.amazon.com/dp/B0DGHRT7PS" }`

**Params (with optional):** `{ "url": "https://www.amazon.com", "query": "wireless earbuds" }`

### Identifier-based agents

Ecommerce agents often take a product identifier instead of a URL:

| Site | Parameter | Example |
|------|-----------|---------|
| Amazon | `asin` | `{ "asin": "B0CCZ1L489" }` |
| Walmart / Target | `product_id` | `{ "product_id": "436473700" }` |
| LinkedIn | `identifier` | `{ "identifier": "dustinlucien" }` |

### Keyword/search agents

SERP agents accept a keyword parameter. The name varies by agent — check `input_properties`:

| Agent | Parameter | Example |
|-------|-----------|---------|
| `google_search` | `query` | `{ "query": "fintech NYC" }` |
| `linkedin_search_peoples` | `keywords` | `{ "keywords": "CTO fintech" }` |
| Amazon/Walmart SERP | `keyword` | `{ "keyword": "wireless headphones" }` |

### Non-URL agents

Some agents operate on a fixed domain and only need non-URL inputs (e.g. `{ "username": "johndoe" }`).

## Building params — step by step

1. Call `nimble_agents_get` to read `input_properties`.
2. Identify all properties where `required: true`.
3. Map values from the user's request to matching parameter names. Use `examples` for guidance.
4. Ask via `AskUserQuestion` only for required values that cannot be inferred. Omit optional params unless inferable.
5. Pass constructed `params` dict to `nimble_agents_run`.

## Also check output fields

Before running or generating code, inspect the `skills` dict from `nimble_agents_get` to understand what data the agent returns. This is critical for:
- **Interactive path:** knowing which fields to show in the results table.
- **Codegen path:** determining the correct response parsing — see `agent-api-reference.md` > "Response shape inference".

# Find and Run an Existing Agent

This walkthrough demonstrates the preferred path: searching for an existing agent,
inspecting its details, and running it to extract structured data.

## Step 1 -- Search for an agent

Use `nimble_agents_list` with a short keyword query to find agents matching your
extraction goal.

```json
{
  "tool": "nimble_agents_list",
  "params": {
    "query": "amazon products",
    "limit": 5,
    "skip": 0
  }
}
```

**Expected response:**

```json
{
  "agents": [
    { "name": "amazon-product-details", "description": "Extracts product details from Amazon product pages" },
    { "name": "amazon-product-search", "description": "Extracts search result listings from Amazon" },
    { "name": "amazon-reviews", "description": "Extracts customer reviews from Amazon product pages" }
  ],
  "skip": 0,
  "limit": 5,
  "curr_count": 3,
  "count": 3
}
```

**Present as a table:**

| # | Agent name | Description |
|---|-----------|-------------|
| 1 | `amazon-product-details` | Extracts product details from Amazon product pages |
| 2 | `amazon-product-search` | Extracts search result listings from Amazon |
| 3 | `amazon-reviews` | Extracts customer reviews from Amazon product pages |

Since multiple agents plausibly match, use `AskUserQuestion`:

```
question: "Which agent matches your needs?"
header: "Select agent"
options:
  - label: "amazon-product-details (Recommended)"
    description: "Extracts product details from Amazon product pages"
  - label: "amazon-product-search"
    description: "Extracts search result listings from Amazon"
  - label: "Generate new agent"
    description: "Create a custom agent instead"
```

## Step 2 -- Get agent details

After the user selects agent #1, call `nimble_agents_get` to retrieve its full
schema before running.

```json
{
  "tool": "nimble_agents_get",
  "params": {
    "agent_id": "amazon-product-details"
  }
}
```

**Expected response (abbreviated):**

```json
{
  "agent": {
    "name": "amazon-product-details",
    "description": "Extracts product details from Amazon product pages",
    "input_properties": [
      { "name": "url", "required": true, "type": "string", "description": "Amazon product page URL", "rules": ["minLength: 1"], "examples": ["https://www.amazon.com/dp/B0DGHRT7PS"], "default": null }
    ],
    "skills": {
      "title": { "type": "string" },
      "price": { "type": "number" },
      "rating": { "type": "number" },
      "availability": { "type": "string" }
    },
    "entity_type": "Product Detail Page (PDP)"
  }
}
```

**Present details:**

### Agent: `amazon-product-details`

Extracts product details from Amazon product pages.

#### Input parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | string | Yes | Amazon product page URL |

#### Output fields

| Field | Type |
|-------|------|
| `title` | string |
| `price` | number |
| `rating` | number |
| `availability` | string |

Use `AskUserQuestion` to confirm:

```
question: "Run this agent?"
header: "Confirm"
options:
  - label: "Run agent (Recommended)"
    description: "Execute amazon-product-details with inferred parameters"
  - label: "Generate new agent"
    description: "Create a custom agent instead"
```

## Step 3 -- Run the agent

The user picks "Run this agent." Build `params` from the input schema and call
`nimble_agents_run`.

```json
{
  "tool": "nimble_agents_run",
  "params": {
    "agent_name": "amazon-product-details",
    "params": {
      "url": "https://www.amazon.com/dp/B0DGHRT7PS"
    }
  }
}
```

**Expected response:**

```json
{
  "data": {
    "results": [
      {
        "title": "Wireless Noise Cancelling Headphones",
        "price": 79.99,
        "rating": 4.6,
        "availability": "In Stock"
      }
    ]
  },
  "url": "https://www.amazon.com/dp/B0DGHRT7PS",
  "agent_name": "amazon-product-details"
}
```

**Present results:**

### Results -- `amazon-product-details`

**Source:** https://www.amazon.com/dp/B0DGHRT7PS
**Records:** 1

| # | Title | Price | Rating | Availability |
|---|-------|-------|--------|--------------|
| 1 | Wireless Noise Cancelling Headphones | $79.99 | 4.6 | In Stock |

Use `AskUserQuestion` for next steps:

```
question: "What next?"
header: "Next step"
options:
  - label: "Done (Recommended)"
    description: "Finish with these results"
  - label: "Run again"
    description: "Re-run with different parameters"
  - label: "Get code"
    description: "Generate a script to reproduce this"
```

## Key takeaways

- Always start with `nimble_agents_list` using short keyword queries.
- Use `nimble_agents_get` to inspect `input_properties` and `skills` (output fields) before running.
- Build the `params` dict from the agent's `input_properties` entries.
- Present every result as a markdown table. Use `AskUserQuestion` for follow-up choices.

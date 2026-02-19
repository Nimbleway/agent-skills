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

**Pick a number:**
4. Search with different keywords
5. Generate a new custom agent

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
    "input_schema": {
      "type": "object",
      "properties": {
        "url": { "type": "string", "description": "Amazon product page URL" }
      },
      "required": ["url"]
    },
    "output_schema": {
      "type": "object",
      "properties": {
        "title": { "type": "string" },
        "price": { "type": "number" },
        "rating": { "type": "number" },
        "availability": { "type": "string" }
      }
    }
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

**Pick a number:**
1. Run this agent
2. Go back to search results
3. Generate a new agent instead

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

**Pick a number:**
2. Run again with different inputs
3. Get Python code for this extraction
4. Search for a different agent
5. Done

## Key takeaways

- Always start with `nimble_agents_list` using short keyword queries.
- Use `nimble_agents_get` to inspect the input/output schema before running.
- Build the `params` dict from the agent's `input_schema` properties.
- Present every result as a markdown table with numbered follow-up options.

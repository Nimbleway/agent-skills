# Bulk Extraction Across Multiple URLs

This walkthrough demonstrates running an agent against several URLs and
aggregating results into a combined summary table.

## Scenario

Extract product details from five Amazon product pages using the
`amazon-product-details` agent.

## Step 1 -- Confirm the agent exists

Call `nimble_agents_get` to verify the agent and inspect its input schema.

```json
{
  "tool": "nimble_agents_get",
  "params": {
    "agent_id": "amazon-product-details"
  }
}
```

Confirmed input schema requires a single `url` parameter.

## Step 2 -- Prepare the URL list

Define the set of URLs to process:

```
URLs:
1. https://www.amazon.com/dp/B0DGHRT7PS
2. https://www.amazon.com/dp/B0CX23V2ZK
3. https://www.amazon.com/dp/B0BT9CXXXX
4. https://www.amazon.com/dp/B0D77HXXXX
5. https://www.amazon.com/dp/B0CR6FXXXX
```

## Step 3 -- Run the agent for each URL

Call `nimble_agents_run` once per URL, iterating through the list.

**Call 1:**

```json
{
  "tool": "nimble_agents_run",
  "params": {
    "agent_name": "amazon-product-details",
    "params": { "url": "https://www.amazon.com/dp/B0DGHRT7PS" }
  }
}
```

**Response 1:**

```json
{
  "data": {
    "results": [
      { "title": "Wireless Headphones Pro", "price": 79.99, "rating": 4.6, "availability": "In Stock" }
    ]
  },
  "url": "https://www.amazon.com/dp/B0DGHRT7PS",
  "agent_name": "amazon-product-details"
}
```

**Call 2:**

```json
{
  "tool": "nimble_agents_run",
  "params": {
    "agent_name": "amazon-product-details",
    "params": { "url": "https://www.amazon.com/dp/B0CX23V2ZK" }
  }
}
```

**Response 2:**

```json
{
  "data": {
    "results": [
      { "title": "USB-C Charging Hub", "price": 34.99, "rating": 4.3, "availability": "In Stock" }
    ]
  },
  "url": "https://www.amazon.com/dp/B0CX23V2ZK",
  "agent_name": "amazon-product-details"
}
```

Repeat for URLs 3 through 5.

## Step 4 -- Handle errors gracefully

If a run returns an error for one URL, log it and continue with the remaining
URLs. Do not abort the entire batch.

```json
{
  "error": "Page not found or access denied",
  "url": "https://www.amazon.com/dp/B0BT9CXXXX",
  "agent_name": "amazon-product-details"
}
```

Record the failure and move on to the next URL.

## Step 5 -- Aggregate into a summary table

After all runs complete, combine the results into a single table.

### Bulk Extraction Results -- `amazon-product-details`

**Agent:** `amazon-product-details`
**URLs processed:** 5
**Successful:** 4
**Failed:** 1

| # | Title | Price | Rating | Availability | Source URL |
|---|-------|-------|--------|--------------|-----------|
| 1 | Wireless Headphones Pro | $79.99 | 4.6 | In Stock | amazon.com/dp/B0DGHRT7PS |
| 2 | USB-C Charging Hub | $34.99 | 4.3 | In Stock | amazon.com/dp/B0CX23V2ZK |
| 3 | Ergonomic Keyboard | $59.99 | 4.7 | In Stock | amazon.com/dp/B0D77HXXXX |
| 4 | Portable Monitor 15.6" | $149.99 | 4.4 | In Stock | amazon.com/dp/B0CR6FXXXX |

**Failed URLs:**

| # | URL | Error |
|---|-----|-------|
| 1 | amazon.com/dp/B0BT9CXXXX | Page not found or access denied |

## Variation -- Multi-parameter agents

Some agents accept more than just a URL. For example, a search-based agent might
require both `url` and `query`. Iterate over different parameter combinations:

```json
{
  "tool": "nimble_agents_run",
  "params": {
    "agent_name": "amazon-product-search",
    "params": { "url": "https://www.amazon.com", "query": "wireless earbuds" }
  }
}
```

```json
{
  "tool": "nimble_agents_run",
  "params": {
    "agent_name": "amazon-product-search",
    "params": { "url": "https://www.amazon.com", "query": "bluetooth speaker" }
  }
}
```

Aggregate these results the same way, adding a column for the varying parameter.

| # | Query | Title | Price | Rating |
|---|-------|-------|-------|--------|
| 1 | wireless earbuds | EarPods Ultra | $49.99 | 4.5 |
| 2 | wireless earbuds | BudsFit Pro | $39.99 | 4.2 |
| 3 | bluetooth speaker | SoundBlast Mini | $29.99 | 4.6 |
| 4 | bluetooth speaker | BassBoom 360 | $44.99 | 4.3 |

## When to switch to codegen

The interactive approach above works well for small batches (roughly 2–5 URLs) where calling the MCP tool per URL is practical. For more than ~5 URLs, the interactive approach becomes tedious — SKILL.md Step 1 routes to the codegen path based on scale, output format, and other signals. See `references/codegen-walkthrough.md` for a full walkthrough.

### Example routing decision

User request: *"Extract product details for these 200 Amazon URLs from my urls.txt file and save to CSV"*

**Signals detected:**

| Signal | Value | Evidence |
|--------|-------|----------|
| Scale | large | 200 URLs |
| Output format | CSV file | "save to CSV" |
| Batch input | file | "from my urls.txt" |

**Route: codegen path.** Generate a script using the async batch pipeline
pattern from `references/sdk-patterns.md` (section: Async Agent Endpoint).

For a full codegen walkthrough, see `references/codegen-walkthrough.md`.

## Key takeaways

- Run the agent once per URL or parameter combination.
- Collect results from each call and merge them into one summary table.
- Handle individual failures without aborting the batch.
- Include source URL or varying parameters as columns for traceability.
- Present a final summary with success/failure counts.
- For larger batches (more than ~5 URLs), file-based output, or multi-store comparisons, route to the codegen path instead.

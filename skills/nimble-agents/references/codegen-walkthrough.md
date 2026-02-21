# Codegen Path Walkthrough

This walkthrough demonstrates the codegen path: when the skill generates a
ready-to-run script instead of making interactive MCP tool calls.

## Scenario

User request: *"Compare prices for wireless headphones on Amazon and Walmart,
save results to comparison.csv"*

## Step 1 -- Parse intent and route

Extract signals from the request:

| Signal | Value | Evidence |
|--------|-------|----------|
| Execution mode | `codegen` | Multi-store comparison + CSV output |
| Scale | `small` | No explicit count, but file output triggers codegen |
| Output format | `csv` | "save results to comparison.csv" |
| Stores | Amazon, Walmart | "on Amazon and Walmart" |
| Target type | `search` | "wireless headphones" is a keyword |
| Language | Python | Default — no project files detected |

**Route to codegen** because: multi-store comparison with file-based output.

## Step 2 -- Agent discovery (parallel)

Search for agents for both stores simultaneously:

**Call 1:**

```json
{ "tool": "nimble_agents_list", "params": { "query": "amazon search" } }
```

**Call 2 (parallel):**

```json
{ "tool": "nimble_agents_list", "params": { "query": "walmart search" } }
```

Results: found `amazon_serp` and `walmart_serp`. Both match — narrate silently:

> Found `amazon_serp` and `walmart_serp` — using both for the comparison script.

On the codegen path with clear matches, narrate the agent choice without
presenting options. The user will review the generated code.

## Step 3 -- Get schemas (parallel)

**Call 1:**

```json
{ "tool": "nimble_agents_get", "params": { "agent_id": "amazon_serp" } }
```

**Call 2 (parallel):**

```json
{ "tool": "nimble_agents_get", "params": { "agent_id": "walmart_serp" } }
```

Use the returned `input_properties` and `skills` (output fields) to inform code generation.
Do NOT present schemas interactively on the codegen path.

**Key schema details extracted:**

| Agent | Required input | Key output fields |
|-------|---------------|-------------------|
| `amazon_serp` | `keyword` (string) | `product_name`, `price`, `rating`, `review_count` |
| `walmart_serp` | `keyword` (string) | `product_name`, `product_price`, `product_rating`, `product_reviews_count` |

Note the field name differences — the generated script must normalize these.

## Step 4 -- Infer language

Check the project for language signals:

| Project file | Found? |
|-------------|--------|
| `pyproject.toml`, `requirements.txt`, `*.py` | No |
| `package.json`, `tsconfig.json` | No |
| `go.mod`, `Cargo.toml` | No |

No project files detected → default to **Python**.

## Step 5 -- Generate script

This request involves 2 agents (Amazon + Walmart). Per the routing table in
`references/sdk-patterns.md` > "When to use async vs sync":

- 2–3 agents → batch sync template (`asyncio.gather` + `/v1/agent`)

Consult `references/sdk-patterns.md` > "Batch Example with CSV Output" for
the template. Substitute agent names, params, and field names from the schemas.

**Generated script:**

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["nimble_python"]
# ///
"""Compare wireless headphone prices: Amazon vs Walmart."""
import asyncio, csv, os
from nimble_python import AsyncNimble

nimble = AsyncNimble(api_key=os.environ["NIMBLE_API_KEY"], max_retries=4, timeout=120.0)
SEM = asyncio.Semaphore(10)


async def run_agent(agent: str, params: dict) -> dict:
    async with SEM:
        return await nimble.post(
            "/v1/agent",
            body={"agent": agent, "params": params},
            cast_to=object,
        )


def normalize(store: str, record: dict) -> dict:
    """Map store-specific fields to a common schema."""
    if store == "Amazon":
        return {
            "store": "Amazon",
            "product_name": record.get("product_name", ""),
            "price": record.get("price"),
            "rating": record.get("rating"),
            "review_count": record.get("review_count"),
        }
    return {
        "store": "Walmart",
        "product_name": record.get("product_name", ""),
        "price": record.get("product_price"),
        "rating": record.get("product_rating"),
        "review_count": record.get("product_reviews_count"),
    }


async def main():
    results = await asyncio.gather(
        run_agent("amazon_serp", {"keyword": "wireless headphones"}),
        run_agent("walmart_serp", {"keyword": "wireless headphones"}),
        return_exceptions=True,
    )

    rows = []
    for (store, resp) in zip(["Amazon", "Walmart"], results):
        if isinstance(resp, Exception):
            print(f"  {store} failed: {resp}")
            continue
        parsing = resp.get("data", {}).get("parsing", [])
        if isinstance(parsing, list):
            rows.extend(normalize(store, r) for r in parsing)

    # Deduplicate by (store, product_name)
    seen, unique = set(), []
    for row in rows:
        key = (row["store"], row["product_name"])
        if key not in seen:
            seen.add(key)
            unique.append(row)

    if unique:
        with open("comparison.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=unique[0].keys())
            w.writeheader()
            w.writerows(unique)
        print(f"Wrote {len(unique)} products to comparison.csv")

    await nimble.close()

asyncio.run(main())
```

## Step 6 -- Present and confirm

Use `AskUserQuestion` before executing:

```
question: "Run this script now?"
header: "Execute"
options:
  - label: "Run now (Recommended)"
    description: "Execute the script and show results"
  - label: "Save only"
    description: "Save the file without running"
```

## Step 7 -- Execute and summarize

```
NIMBLE_API_KEY=your-key uv run comparison.py
```

Present a final summary table:

| Field | Value |
|-------|-------|
| Agent(s) used | `amazon_serp`, `walmart_serp` |
| Source | Existing |
| Records extracted | 42 |
| Output | `comparison.csv` |

Include the top results in a markdown table.

## Variation -- TypeScript project

If the project had a `package.json` or `tsconfig.json`, the skill would:

1. Infer **TypeScript/Node** as the language
2. Consult `references/rest-api-patterns.md` for the fetch-based pattern
3. Generate a TypeScript script using the REST API directly (`POST /v1/agent`)
4. Use `Promise.all` instead of `asyncio.gather`

No `AskUserQuestion` for language — it is inferred from project context.
Only ask if both Python and Node project files exist simultaneously.

## Variation -- Large scale (50+ items per store)

For 50+ results per store (e.g., "top 1000 keyboards"), the skill would:

1. Use the **async batch pipeline** template instead of `asyncio.gather`
2. Submit jobs via `POST /v1/agent/async` and poll `GET /v1/tasks/{id}`
3. Set tuning parameters based on batch size (see `references/sdk-patterns.md`
   > "Tuning parameters" table)
4. Handle pagination by generating jobs for pages 1–N

## Key takeaways

- Codegen triggers when: scale >50, file output, multi-store, batch input, or explicit request.
- Language is inferred from project files, not asked.
- Agent discovery and schema retrieval happen the same way as the interactive path.
- The generated script uses templates from `references/sdk-patterns.md` (Python) or `references/rest-api-patterns.md` (other languages).
- `AskUserQuestion` confirms execution, not the code itself.
- Field normalization is needed when comparing across stores with different schemas.

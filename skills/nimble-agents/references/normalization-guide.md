# Multi-Agent Output Normalization

Guide for normalizing output fields when comparing data across multiple agents or stores. Used during the codegen path (SKILL.md Step 3B). See `references/codegen-walkthrough.md` for a worked example.

## Table of Contents

- [What normalization does](#what-normalization-does)
- [Strategy](#strategy)
- [Normalization function template](#normalization-function-template)
- [Deduplication](#deduplication)
- [Dynamic normalization](#dynamic-normalization)

---

## What normalization does

Different agents return the same data under different field names. One agent may call a field `price`, another `product_price`, another `web_price` — all meaning the same thing. Normalization maps every agent's output to a single unified schema so results from multiple agents can be merged into one table, CSV, or dataset.

**The goal:** after normalization, every record has the same field names regardless of which agent produced it, plus a `store` (or `source`) column identifying the origin.

**When to apply:**
- Multi-source comparison (2+ agents whose `skills` output fields differ)
- Aggregation from different agents into a single CSV/table
- Any request combining results that need a consistent structure

If all agents share identical field names, skip normalization.

## Strategy

1. Call `nimble_agents_get` for each agent to read `skills` (output fields). See `agent-api-reference.md` > "Output fields format" for the `skills` dict structure.
2. Compare field names across schemas — identify semantically equivalent fields (same concept, different names).
3. Choose unified field names for the merged output.
4. Build a mapping function per agent: `{unified_name: agent_specific_name}`.
5. Apply the mapping after each agent run, before merging results. Each record gets a `store`/`source` label.

## Normalization function template

### Python

```python
def make_normalizer(store: str, field_map: dict[str, str]):
    """Create a normalizer from a field mapping.

    Args:
        store: Store label (e.g., "Amazon", "Walmart")
        field_map: Maps unified field name -> agent-specific field name
    """
    def normalize(record: dict) -> dict:
        return {"store": store, **{
            unified: record.get(agent_field, "")
            for unified, agent_field in field_map.items()
        }}
    return normalize

# Example usage:
amazon_norm = make_normalizer("Amazon", {
    "product_name": "product_name",
    "price": "price",
    "rating": "rating",
    "review_count": "review_count",
})

walmart_norm = make_normalizer("Walmart", {
    "product_name": "product_name",
    "price": "product_price",
    "rating": "product_rating",
    "review_count": "product_reviews_count",
})
```

### TypeScript

```typescript
function makeNormalizer(store: string, fieldMap: Record<string, string>) {
  return (record: Record<string, unknown>) => ({
    store,
    ...Object.fromEntries(
      Object.entries(fieldMap).map(([unified, agentField]) => [
        unified,
        record[agentField] ?? "",
      ])
    ),
  });
}
```

## Deduplication

After normalization, deduplicate by a composite key — typically `(store, product_name)`:

```python
seen, unique = set(), []
for row in rows:
    key = (row["store"], row["product_name"])
    if key not in seen:
        seen.add(key)
        unique.append(row)
```

Choose the composite key based on what uniquely identifies a record. For search results, `(store, product_name)` works. For detail pages, `(store, url)` may be better.

## Dynamic normalization

When agents are discovered at runtime (not hardcoded), build the field mapping dynamically:

1. Read the `skills` dict from each agent via `nimble_agents_get`.
2. For each unified field, search the agent's properties for a matching or similar name.
3. Use exact matches first, then fall back to substring/suffix matching:
   - `price` matches `price`, `product_price`, `web_price`
   - `rating` matches `rating`, `product_rating`, `average_of_reviews`
4. If no match is found, omit the field for that agent (use empty string).

This approach handles new agents without requiring manual mapping updates.

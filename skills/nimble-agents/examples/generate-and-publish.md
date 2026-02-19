# Generate, Run, and Publish an Agent

This walkthrough demonstrates the fallback path: generating a new agent when no
existing one meets the user's needs, running it, and then publishing it for reuse.

## Step 1 -- Create a session ID

Every generate/publish flow requires a stable `session_id` (UUID v4). Generate one
before the first call and reuse it throughout the entire flow.

```
session_id = "a3b1c2d4-5678-9abc-def0-1234567890ab"
```

## Step 2 -- Call generate with a prompt

Describe exactly what data to extract and from which site.

```json
{
  "tool": "nimble_agents_generate",
  "params": {
    "prompt": "Extract restaurant name, cuisine type, rating, price range, and address from Yelp restaurant pages",
    "session_id": "a3b1c2d4-5678-9abc-def0-1234567890ab",
    "url": "https://www.yelp.com/biz/example-restaurant"
  }
}
```

## Step 3 -- Handle the conversational flow

The generate endpoint returns a `status` field. You must handle each status.

### Status: `waiting` (follow-up questions)

```json
{
  "status": "waiting",
  "session_id": "a3b1c2d4-5678-9abc-def0-1234567890ab",
  "message": "I have a few questions:\n1. Should I extract the full street address or just city/state?\n2. Do you want the number of reviews as well?"
}
```

Present questions and collect answers, then call generate again with the **same
session_id** and the user's answers as the new `prompt`:

```json
{
  "tool": "nimble_agents_generate",
  "params": {
    "prompt": "1. Full street address. 2. Yes, include review count.",
    "session_id": "a3b1c2d4-5678-9abc-def0-1234567890ab"
  }
}
```

### Status: `processing`

```json
{
  "status": "processing",
  "session_id": "a3b1c2d4-5678-9abc-def0-1234567890ab",
  "message": "Agent generation in progress..."
}
```

Wait a few seconds and call generate again with the same session_id to poll:

```json
{
  "tool": "nimble_agents_generate",
  "params": {
    "prompt": "",
    "session_id": "a3b1c2d4-5678-9abc-def0-1234567890ab"
  }
}
```

### Status: `complete`

```json
{
  "status": "complete",
  "session_id": "a3b1c2d4-5678-9abc-def0-1234567890ab",
  "agent_name": "yelp-restaurant-details",
  "domain": "yelp.com",
  "input_schema": {
    "type": "object",
    "properties": {
      "url": { "type": "string", "description": "Yelp restaurant page URL" }
    },
    "required": ["url"]
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "name": { "type": "string" },
      "cuisine": { "type": "string" },
      "rating": { "type": "number" },
      "price_range": { "type": "string" },
      "address": { "type": "string" },
      "review_count": { "type": "integer" }
    }
  }
}
```

### Status: `error`

```json
{
  "status": "error",
  "session_id": "a3b1c2d4-5678-9abc-def0-1234567890ab",
  "error": "Could not access the provided URL"
}
```

On error, present the message and offer to retry or search for existing agents.

## Step 4 -- Run the generated agent

Once status is `complete`, build params from the returned `input_schema` and run.

```json
{
  "tool": "nimble_agents_run",
  "params": {
    "agent_name": "yelp-restaurant-details",
    "params": {
      "url": "https://www.yelp.com/biz/the-french-laundry-yountville"
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
        "name": "The French Laundry",
        "cuisine": "French, American (New)",
        "rating": 4.5,
        "price_range": "$$$$",
        "address": "6640 Washington St, Yountville, CA 94599",
        "review_count": 2847
      }
    ]
  },
  "url": "https://www.yelp.com/biz/the-french-laundry-yountville",
  "agent_name": "yelp-restaurant-details"
}
```

**Present results:**

| # | Name | Cuisine | Rating | Price | Address | Reviews |
|---|------|---------|--------|-------|---------|---------|
| 1 | The French Laundry | French, American (New) | 4.5 | $$$$ | 6640 Washington St, Yountville, CA | 2847 |

## Step 5 -- Publish the agent

After a successful run, ask the user whether to save the agent. If confirmed,
call `nimble_agents_publish` with the **same session_id**.

```json
{
  "tool": "nimble_agents_publish",
  "params": {
    "session_id": "a3b1c2d4-5678-9abc-def0-1234567890ab"
  }
}
```

**Expected response:**

```json
{
  "agent": {
    "name": "yelp-restaurant-details",
    "description": "Extracts restaurant details from Yelp pages",
    "input_schema": { "..." : "..." },
    "output_schema": { "..." : "..." }
  }
}
```

The agent is now searchable via `nimble_agents_list` for future use.

## Key takeaways

- Generate a UUID session_id once and reuse it for all generate and publish calls.
- Handle all four statuses: `waiting`, `processing`, `complete`, `error`.
- Poll with the same session_id when status is `processing`.
- Answer follow-up questions by passing answers as the `prompt` with the same session_id.
- Only publish after a successful run and explicit user confirmation.

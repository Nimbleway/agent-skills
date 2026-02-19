# Agent API Reference

Concise reference for the five Nimble agent tools.

---

## nimble_agents_list

Search and paginate through available agents.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | No | — | Search keyword(s). Use short terms, not full sentences. |
| `skip` | integer | No | 0 | Number of results to skip (for pagination). |
| `limit` | integer | No | 50 | Max results to return. Maximum allowed value is 100. |

### Returns: `PaginatedAgentList`

| Field | Type | Description |
|-------|------|-------------|
| `agents` | array | List of agent summary objects (name, description). |
| `skip` | integer | Current skip offset. |
| `limit` | integer | Current limit value. |
| `curr_count` | integer | Number of agents returned in this page. |
| `count` | integer | Total number of matching agents. |

### Example

```json
// Request
{ "query": "linkedin", "limit": 5, "skip": 0 }

// Response
{
  "agents": [
    { "name": "linkedin-profile", "description": "Extracts LinkedIn profile data" }
  ],
  "skip": 0, "limit": 5, "curr_count": 1, "count": 1
}
```

---

## nimble_agents_get

Retrieve full details and schemas for a single agent.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `agent_id` | string | Yes | The agent name/identifier to look up. |

### Returns: `AgentDetailsResult`

| Field | Type | Description |
|-------|------|-------------|
| `agent` | object | Agent details dict. |
| `agent.name` | string | Agent identifier. |
| `agent.description` | string | What the agent extracts. |
| `agent.input_schema` | object | JSON Schema defining required input parameters. |
| `agent.output_schema` | object | JSON Schema defining the structure of extracted data. |

### Example

```json
// Request
{ "agent_id": "amazon-product-details" }

// Response
{
  "agent": {
    "name": "amazon-product-details",
    "description": "Extracts product details from Amazon product pages",
    "input_schema": {
      "type": "object",
      "properties": { "url": { "type": "string" } },
      "required": ["url"]
    },
    "output_schema": {
      "type": "object",
      "properties": { "title": { "type": "string" }, "price": { "type": "number" } }
    }
  }
}
```

---

## nimble_agents_generate

Start or continue an agent generation conversation.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | Yes | Description of what to extract, or answers to follow-up questions. |
| `session_id` | string | Yes | UUID v4. Must remain the same across all calls in one flow. |
| `url` | string | No | Example target URL for the agent. |
| `output_schema` | object | No | Desired output schema (JSON Schema format). |
| `input_schema` | object | No | Desired input schema (JSON Schema format). |

### Returns: `AgentGenerateResult`

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | One of: `waiting`, `processing`, `complete`, `error`. |
| `session_id` | string | Echo of the session ID. |
| `message` | string | Follow-up questions (when `waiting`) or status info. |
| `agent_name` | string | Agent name (when `complete`). |
| `domain` | string | Target domain (when `complete`). |
| `input_schema` | object | Generated input schema (when `complete`). |
| `output_schema` | object | Generated output schema (when `complete`). |
| `error` | string | Error message (when `error`). |

### Status lifecycle

```
waiting  -->  processing  -->  complete
   ^             |
   |             v
   +-- waiting (more questions)
                 |
                 v
              error
```

- `waiting` -- The generator needs more information. Respond and call again.
- `processing` -- Generation is in progress. Poll with the same session_id.
- `complete` -- Agent is ready to run.
- `error` -- Generation failed. Inspect the `error` field.

---

## nimble_agents_run

Execute an agent against a target with the given parameters.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `agent_name` | string | Yes | Name of the agent to run. |
| `params` | object | Yes | Input values matching the agent's `input_schema`. |

### Returns: `RunAgentResult`

| Field | Type | Description |
|-------|------|-------------|
| `data.results` | array | List of extracted record objects. |
| `url` | string | The URL that was processed. |
| `agent_name` | string | Echo of the agent name. |
| `error` | string | Error message if the run failed. |

### Example

```json
// Request
{ "agent_name": "amazon-product-details", "params": { "url": "https://www.amazon.com/dp/B0DGHRT7PS" } }

// Response
{
  "data": {
    "results": [
      { "title": "Wireless Headphones", "price": 79.99, "rating": 4.6 }
    ]
  },
  "url": "https://www.amazon.com/dp/B0DGHRT7PS",
  "agent_name": "amazon-product-details"
}
```

---

## nimble_agents_publish

Save a generated agent so it becomes searchable and reusable.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `session_id` | string | Yes | The same UUID used during `nimble_agents_generate`. |

### Returns: `AgentDetailsResult`

Same structure as `nimble_agents_get`. The agent is now discoverable via
`nimble_agents_list`.

### Example

```json
// Request
{ "session_id": "a3b1c2d4-5678-9abc-def0-1234567890ab" }

// Response
{
  "agent": {
    "name": "yelp-restaurant-details",
    "description": "Extracts restaurant details from Yelp pages",
    "input_schema": { "..." : "..." },
    "output_schema": { "..." : "..." }
  }
}
```

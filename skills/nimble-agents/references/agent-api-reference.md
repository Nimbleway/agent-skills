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

**Request:**

```json
{ "query": "linkedin", "limit": 5, "skip": 0 }
```

**Response:**

```json
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
| `agent.input_properties` | array | List of input parameter objects (see below). |
| `agent.skills` | object | Output field definitions — keys are field names, values describe their type (see below). |
| `agent.entity_type` | string | `"Search Engine Results Page (SERP)"` or `"Product Detail Page (PDP)"`. Determines response nesting — see "Response shape inference" below. |
| `agent.feature_flags` | object | Capabilities: `is_pagination_supported`, `is_localization_supported`. |

### Input properties format

Each element of `input_properties` is an object:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Parameter name (e.g. `"query"`, `"url"`, `"identifier"`). |
| `required` | boolean | Whether this parameter must be provided. |
| `type` | string | Data type (e.g. `"string"`, `"integer"`). |
| `description` | string | What the parameter controls. |
| `rules` | array | Validation rules (e.g. `["minLength: 1"]`). |
| `examples` | array | Example values (e.g. `["elon musk"]`). |
| `default` | any | Default value if omitted (`null` = no default). |

### Output fields format (`skills`)

The `skills` dict maps field names to type descriptors: `{ "field_name": { "type": "string" } }`.

### Response shape inference

Use `entity_type` and `skills` from `nimble_agents_get` to predict the REST API response shape:

| `entity_type` | `skills` structure | REST `data.parsing` shape |
|---------------|-------------------|--------------------------|
| PDP | Flat fields | `dict` — single record |
| SERP (ecommerce) | Flat fields | `list` — array of records |
| SERP (non-ecommerce) | Nested fields (contains `entities`, `total_entities_count`) | `dict` — with `entities.{EntityType}` arrays |

**Important:** Inspect `skills` before generating code to determine which shape applies. See `sdk-patterns.md` > "Response structure verification".

---

## nimble_agents_generate

Start or continue an agent generation conversation.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | **No** | Description of what to extract, or answers to follow-up questions. **Omit when polling a `processing` session** — sending any prompt (even `""`) re-invokes the generation backend instead of checking status. |
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
- `processing` -- Generation is in progress. Poll immediately with only `session_id` (omit `prompt`). The server waits ~50 s internally before responding — no sleep needed. Stop after 12 consecutive polls (~10 minutes).
- `complete` -- Agent is ready to run.
- `error` -- Generation failed. Inspect the `error` field.

---

## nimble_agents_run

Execute an agent against a target with the given parameters.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `agent_name` | string | Yes | Name of the agent to run. |
| `params` | object | Yes | Input values matching the agent's `input_properties`. |

### Returns: `RunAgentResult`

| Field | Type | Description |
|-------|------|-------------|
| `data.results` | array | List of extracted record objects. |
| `url` | string | The URL that was processed. |
| `agent_name` | string | Echo of the agent name. |
| `error` | string | Error message if the run failed. |

### Example

**Request:**

```json
{ "agent_name": "amazon-product-details", "params": { "url": "https://www.amazon.com/dp/B0DGHRT7PS" } }
```

**Response:**

```json
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

**Request:**

```json
{ "session_id": "a3b1c2d4-5678-9abc-def0-1234567890ab" }
```

**Response:**

```json
{
  "agent": {
    "name": "yelp-restaurant-details",
    "description": "Extracts restaurant details from Yelp pages",
    "input_properties": [ "..." ],
    "skills": { "..." : "..." }
  }
}
```

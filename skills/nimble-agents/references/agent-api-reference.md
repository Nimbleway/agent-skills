# Agent API Reference

Concise reference for the six Nimble agent tools.

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

## nimble_agents_generate (initial creation only)

Start agent creation. Use ONLY for the initial call. All follow-ups go through `nimble_agents_update`.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | No | Description of what to extract. Required on the first call. This tool is for initial creation only — for follow-ups, use `nimble_agents_update` with the same `session_id`. |
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

- `waiting` -- The generator needs more information. Respond via `nimble_agents_update` with the same `session_id` and the user's answer as `prompt`.
- `processing` -- Generation in progress. Use `nimble_agents_status` to poll for completion. Do NOT call this tool for status checks.
- `complete` -- Agent is ready to run.
- `error` -- Generation failed. Inspect the `error` field.

---

## nimble_agents_status

Check the current status of a generate or update session (read-only).

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `session_id` | string | Yes | The `session_id` from a previous `nimble_agents_generate` or `nimble_agents_update` call. |

### Returns: `AgentGenerateResult`

Same shape as `nimble_agents_generate`. Use this to poll for completion after `nimble_agents_generate` or `nimble_agents_update` returns `processing`.

### When to use

- After `nimble_agents_generate` or `nimble_agents_update` returns `processing` status.
- From a background Task agent polling every ~30 seconds.
- Do NOT use this tool to send clarifications — use `nimble_agents_update` with `prompt` and the same `session_id` instead.

### Example

**Request:**

```json
{ "session_id": "a3b1c2d4-5678-9abc-def0-1234567890ab" }
```

**Response (still processing):**

```json
{
  "status": "processing",
  "session_id": "a3b1c2d4-5678-9abc-def0-1234567890ab",
  "message": "Template generation in progress..."
}
```

**Response (complete):**

```json
{
  "status": "complete",
  "session_id": "a3b1c2d4-5678-9abc-def0-1234567890ab",
  "agent_name": "yelp-restaurant-details",
  "domain": "yelp.com",
  "input_schema": { "..." : "..." },
  "output_schema": { "..." : "..." }
}
```

---

## nimble_agents_update (primary tool for all follow-ups)

Refine an existing agent or continue any generate/update session. Primary tool for all post-creation interactions.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `session_id` | string | No | Existing session to continue refining. |
| `agent_name` | string | No | Agent to update. Published agents are forked; user's unpublished agents are updated in-place. |
| `prompt` | string | No | Refinement instruction. At least one of prompt/input_schema/output_schema required. |
| `input_schema` | object | No | JSON Schema override for input parameters. |
| `output_schema` | object | No | JSON Schema override for output fields. |

### Returns: `AgentGenerateResult`

Same shape as `nimble_agents_generate`. Status flow is identical — use `nimble_agents_status` to poll.

### Status lifecycle

Same as generate:
- `waiting` — Backend needs more info. Call `nimble_agents_update` with user's answer as `prompt`.
- `processing` — Update in progress. Poll with `nimble_agents_status`.
- `complete` — Agent updated. `agent_name` is set.
- `error` — Apply retry-with-fix protocol: compose a prompt from the error diagnostics and call `nimble_agents_update` again.

### Example

**Request:**

```json
{
  "agent_name": "amazon-product-details",
  "prompt": "Add a ratings field and review count to the output schema"
}
```

**Response:**

```json
{
  "status": "processing",
  "session_id": "auto-generated-thread-id",
  "message": "Update in progress...\n\n[Use nimble_agents_status to poll for completion.]"
}
```

---

## nimble_agents_run

Execute an agent against a target with the given parameters.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `agent_name` | string | No | Name of the agent to run. At least one of `agent_name` or `session_id` is required. |
| `session_id` | string | No | Session/thread ID for running an unpublished workflow. Use instead of `agent_name` for testing before publishing. |
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

> **Default behavior:** Publish first, then run by `agent_name`. Running by `session_id` is for testing unpublished workflows before publishing — only use when the user explicitly asks to test first.

---

## nimble_agents_publish

Save a generated agent so it becomes searchable and reusable.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `session_id` | string | Yes | The same UUID used during `nimble_agents_generate` (and subsequent `nimble_agents_update` calls). |

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

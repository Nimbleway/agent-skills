# Agent API Reference

Concise reference for the nine Nimble agent MCP tools plus input parameter mapping.

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

Start agent creation for a new agent. Use only once per new generation flow.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | No | Description of what to extract. Required on first call. |
| `session_id` | string | Yes | UUID v4. Must remain the same for all follow-ups in this flow. |
| `url` | string | No | Example target URL for the agent. |
| `output_schema` | object | No | Desired output schema (JSON Schema format). |
| `input_schema` | object | No | Desired input schema (JSON Schema format). |

### Returns: `AgentGenerateResult`

Same status shape used by update tools (`waiting`, `processing`, `complete`, `error`).

### Status lifecycle

- `waiting` — Generator needs more information. Continue with `nimble_agents_update_session` using the same `session_id`.
- `processing` — Generation in progress. Poll with `nimble_agents_status`.
- `complete` — Agent is ready to run/publish.
- `error` — Generation failed. Use retry-with-fix via `nimble_agents_update_session` with same `session_id`.

If this call returns HTTP 429/quota errors, stop and report quota exhaustion. Do not start a new session.

---

## nimble_agents_status

Check the current status of a generate or update session (read-only).

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `session_id` | string | Yes | The `session_id` from `nimble_agents_generate`, `nimble_agents_update_from_agent`, or `nimble_agents_update_session`. |

### Returns: `AgentGenerateResult`

Same shape as generation/update responses.

### When to use

- After `nimble_agents_generate`, `nimble_agents_update_from_agent`, or `nimble_agents_update_session` returns `processing`.
- From a background Task agent polling every ~30 seconds.
- Do not use this tool to send clarifications — use `nimble_agents_update_session` instead.

---

## nimble_agents_update_from_agent

Start refinement from an existing `agent_name`.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `agent_name` | string | Yes | Agent to refine. Published agents are forked; owned unpublished agents are updated in-place. |
| `prompt` | string | No | Refinement instruction. |
| `input_schema` | object | No | JSON Schema override for input parameters. |
| `output_schema` | object | No | JSON Schema override for output fields. |

At least one of `prompt`, `input_schema`, or `output_schema` is required.

### Returns: `AgentGenerateResult`

Includes update metadata fields:
- `source_agent_name`: current agent being edited
- `forked_from_agent_name`: original name when forked

### Flow rules

- Call this tool once to enter update mode from an existing agent.
- After it returns a `session_id`, never call it again in the same run.
- Continue with `nimble_agents_update_session` for all follow-ups.
- On HTTP 429/quota errors, stop and report quota exhaustion. Do not start another session.

---

## nimble_agents_update_session

Continue an existing update/generate session by `session_id`.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `session_id` | string | Yes | Existing session to continue refining (must already exist). |
| `prompt` | string | No | Refinement instruction or answer to waiting question. |
| `input_schema` | object | No | JSON Schema override for input parameters. |
| `output_schema` | object | No | JSON Schema override for output fields. |

At least one of `prompt`, `input_schema`, or `output_schema` is required.

### Returns: `AgentGenerateResult`

Same shape as generate/update-from-agent responses.

### Status lifecycle

- `waiting` — backend needs more info; call `nimble_agents_update_session` again with same `session_id`.
- `processing` — poll with `nimble_agents_status`.
- `complete` — refinement finished.
- `error` — apply retry-with-fix using the same `session_id`.

### Example

```json
{
  "session_id": "thread_123",
  "prompt": "Add a ratings field and review count to the output schema"
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
| `session_id` | string | Yes | Session used during `nimble_agents_generate` / `nimble_agents_update_from_agent` / `nimble_agents_update_session`. |

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

---

## nimble_web_search

Real-time web search returning structured results.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Search query. |

### Returns

Structured search results with titles, URLs, and snippets.

### When to use

- Exploring unfamiliar domains before committing to an agent approach.
- Finding real-world examples for agent generation discovery phase.
- General information-finding tasks (preferred over `google_search` for this purpose).
- Fallback when a data source agent is down — see `error-recovery.md`.

---

## Input Parameter Mapping

How to read an agent's `input_properties` and construct the `params` dict for `nimble_agents_run` or REST API calls.

### Mapping input_properties to params

The `params` dict maps 1:1 to `input_properties` names. Include all properties where `required: true`; optional ones can be omitted.

**Rule:** Only ask the user for missing **required** parameters that cannot be inferred from context. Fill optional parameters when inferable; otherwise omit them.

### Presenting schema to the user

When presenting agent schema before running, show a markdown table:

| Parameter | Required | Type | Description | Example |
|-----------|----------|------|-------------|---------|
| `query` | Yes | string | Search term | `"donald trump"` |
| `country` | No | string | Country code (default: US) | `"US"` |

Also note key output fields from the `skills` dict so the user knows what data to expect.

### Common patterns

#### URL-based agents

Most agents take a required `url` and optionally additional parameters.

**Params (required only):** `{ "url": "https://www.amazon.com/dp/B0DGHRT7PS" }`

**Params (with optional):** `{ "url": "https://www.amazon.com", "query": "wireless earbuds" }`

#### Identifier-based agents

Ecommerce agents often take a product identifier instead of a URL:

| Site | Parameter | Example |
|------|-----------|---------|
| Amazon | `asin` | `{ "asin": "B0CCZ1L489" }` |
| Walmart / Target | `product_id` | `{ "product_id": "436473700" }` |
| LinkedIn | `identifier` | `{ "identifier": "dustinlucien" }` |

#### Keyword/search agents

SERP agents accept a keyword parameter. The name varies — check `input_properties`:

| Agent | Parameter | Example |
|-------|-----------|---------|
| `google_search` | `query` | `{ "query": "fintech NYC" }` |
| `linkedin_search_peoples` | `keywords` | `{ "keywords": "CTO fintech" }` |
| Amazon/Walmart SERP | `keyword` | `{ "keyword": "wireless headphones" }` |

#### Non-URL agents

Some agents operate on a fixed domain and only need non-URL inputs (e.g., `{ "username": "johndoe" }`).

### Building params — step by step

1. Call `nimble_agents_get` to read `input_properties`.
2. Identify all properties where `required: true`.
3. Map values from the user's request to matching parameter names. Use `examples` for guidance.
4. Ask via `AskUserQuestion` only for required values that cannot be inferred. Omit optional params unless inferable.
5. Pass constructed `params` dict to `nimble_agents_run`.

### Also check output fields

Before running or generating code, inspect the `skills` dict from `nimble_agents_get` to understand what data the agent returns. This is critical for:
- **Interactive path:** knowing which fields to show in the results table.
- **Codegen path:** determining the correct response parsing — see "Response shape inference" above.

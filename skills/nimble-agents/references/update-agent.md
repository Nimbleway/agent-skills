# Update Agent Reference

## Tool: `nimble_agents_update`

Refine an existing agent with new instructions or schema overrides.

### Role in the workflow

`nimble_agents_update` is the primary tool for all post-creation interactions:
- Refining existing agents (change output fields, adjust behavior)
- Answering follow-up questions from `nimble_agents_generate` (`waiting` status)
- Retrying errors from generate or update (compose fix prompt from diagnostics)
- Continuing any session started by generate or update

`nimble_agents_generate` is only used once for initial creation.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `session_id` | string | No | Existing session to continue refining |
| `agent_name` | string | No | Agent to update (at least one of session_id or agent_name required) |
| `prompt` | string | No | Refinement instruction (at least one of prompt/input_schema/output_schema required) |
| `input_schema` | object | No | JSON Schema override for input parameters |
| `output_schema` | object | No | JSON Schema override for output fields |

### Behavior

**Published agents** (is_public=True or owned by another user):
- Automatically forked to a private copy under the caller's account
- All sub-resources are cloned
- Original agent is untouched
- Returns a new `session_id` for the forked version

**User's unpublished agents** (is_public=False, owned by caller):
- Updated in-place on the existing thread
- No fork — modifications apply directly


### Status flow

Same as `nimble_agents_generate`. Both use `nimble_agents_status` for polling:
- `"waiting"` → Backend needs more info; relay message, call update again with answer
- `"processing"` → Poll with `nimble_agents_status` every ~30s
- `"complete"` → Agent refined; `agent_name` is set
- `"error"` → Apply retry-with-fix protocol (see below)

### Retry-with-fix protocol

When update (or status polling) returns `status="error"`:

1. Read the `error` and `message` fields — they contain supervisor diagnostics
2. Compose a fix prompt:
   ```
   "The previous update attempt failed: {error}. The assistant reported: {message}. Please fix the configuration accordingly."
   ```
3. Call `nimble_agents_update` again with same `session_id` and the fix prompt
4. If it returns `"processing"`, resume polling with `nimble_agents_status`
5. Max 2 retries — then present error to user

### Typical workflow (default: publish first)

```
1. nimble_agents_get(agent_id="amazon_search")        → inspect current schemas
2. nimble_agents_update(agent_name="amazon_search", prompt="add a ratings field")
3. nimble_agents_status(session_id)                    → poll until complete
4. nimble_agents_publish(session_id=...)               → publish the refined agent
5. nimble_agents_run(agent_name=..., params={...})     → run the published agent
```

The default behavior is to **publish first, then run by agent_name**. This ensures the agent is persisted and reusable.

### Optional: test before publishing

If the user explicitly wants to test before publishing, use `session_id` in `nimble_agents_run`:

```
1-3. (same as above — update, poll until complete)
4. nimble_agents_run(session_id="thread_abc123", params={"url": "https://..."})  → test unpublished
5. nimble_agents_publish(session_id=...)                                          → publish if satisfied
6. nimble_agents_run(agent_name=..., params={...})                               → run published
```

This runs the workflow directly from the session's thread without needing a published template. Only use this path when the user explicitly asks to test first.

---
name: nimble-tasks-reference
description: |
  Reference for nimble tasks commands. Load when polling async task status or fetching results.
  Works for ALL async types: agent run-async, crawl (per-page tasks), extract async, search async, map async.
  CRITICAL: agent tasks use "success"/"error" states; crawl page tasks use "completed"/"failed".
---

# nimble tasks — reference

Unified task layer for ALL async Nimble operations. Every async job (agent, crawl page, extract, search, map) produces a `task_id` — use these commands to check status and retrieve results.

## Table of Contents

- [1. Get task status](#1-get-task-status)
- [2. Get task results](#2-get-task-results)
- [3. List tasks](#3-list-tasks)
- [Common patterns](#common-patterns)

---

## 1. Get task status

**Parameters:**

| Parameter | CLI flag | Type | Description |
|-----------|----------|------|-------------|
| `task_id` | `--task-id` | string | Task ID (required) |

**CLI:**
```bash
nimble tasks get --task-id "8e8cfde8-345b-42b8-b3e2-0c61eb11e00f"
```

**Python SDK:**
```python
from nimble_python import Nimble
nimble = Nimble(api_key=os.environ["NIMBLE_API_KEY"])

task = nimble.tasks.get(task_id)
state = task.task.state
```

**Task state values by source:**

| Source | Terminal states | Intermediate |
|--------|----------------|--------------|
| `agent run-async` | `success` / `error` | `pending` |
| Crawl page task | `completed` / `failed` | `pending` / `processing` |

---

## 2. Get task results

**Parameters:**

| Parameter | CLI flag | Type | Description |
|-----------|----------|------|-------------|
| `task_id` | `--task-id` | string | Task ID (required) |

**CLI:**
```bash
nimble tasks results --task-id "8e8cfde8-345b-42b8-b3e2-0c61eb11e00f"
```

**Python SDK:**
```python
results = await nimble.tasks.results(task_id)  # returns plain dict
```

**Response shape by source:**

| Source | Shape |
|--------|-------|
| `agent run-async` | `{"data": {"parsing": ...}, "status": "success", ...}` |
| Crawl page | `{"url": "...", "data": {"html": "...", "markdown": "..."}, "status_code": 200, ...}` |
| Extract async | `{"data": {"html": "...", "markdown": "...", "parsing": {}}, "status": "success", ...}` |

> `tasks.results()` returns **plain dicts** — no `.model_dump()` needed.

---

## 3. List tasks

**Parameters:**

| Parameter | CLI flag | Type | Description |
|-----------|----------|------|-------------|
| `limit` | `--limit` | int | Results per page |
| `cursor` | `--cursor` | string | Pagination cursor |

**CLI:**
```bash
nimble tasks list --limit 20
```

**Python SDK:**
```python
result = nimble.tasks.list()
```

---

## Common patterns

### Agent async — full poll loop

```bash
# Submit
TASK_ID=$(nimble agent run-async --agent amazon_pdp --params '{"asin": "B0CHWRXH8B"}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['task']['id'])")

# Poll
while true; do
  STATE=$(nimble tasks get --task-id "$TASK_ID" \
    | python3 -c "import json,sys; print(json.load(sys.stdin)['task']['state'])")
  [ "$STATE" = "success" ] || [ "$STATE" = "error" ] && break
  sleep 3
done

nimble tasks results --task-id "$TASK_ID"
```

**Python SDK (async):**
```python
import asyncio, os
from nimble_python import AsyncNimble

async def run():
    nimble = AsyncNimble(api_key=os.environ["NIMBLE_API_KEY"])
    resp = await nimble.agent.run_async(agent="amazon_pdp", params={"asin": "B0CHWRXH8B"})
    task_id = resp.task["id"]

    while True:
        task = await nimble.tasks.get(task_id)
        if task.task.state in ("success", "error"):
            break
        await asyncio.sleep(2)

    results = await nimble.tasks.results(task_id)
    parsing = results["data"]["parsing"]
    await nimble.close()
```

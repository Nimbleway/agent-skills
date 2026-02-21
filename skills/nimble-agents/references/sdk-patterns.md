# Nimble Python SDK Patterns

Reference for generating correct Python code that runs Nimble agents programmatically.

For TypeScript, Node.js, curl, and other non-Python languages, see `references/rest-api-patterns.md`.

## Table of Contents

- [Installation](#installation)
- [Running an Agent](#running-an-agent)
- [Agent Parameters](#agent-parameters)
- [Single-Agent Example](#single-agent-example)
- [Batch Example with CSV Output](#batch-example-with-csv-output)
- [Async Agent Endpoint (High-Throughput)](#async-agent-endpoint-high-throughput)
- [Retry Behavior](#retry-behavior)
- [Common Mistakes](#common-mistakes)

---

## Installation

```
pip install nimble_python
```

Or use `uv run` with inline script metadata for zero-setup execution (no install step needed):

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["nimble_python"]
# ///
```

Run with: `uv run script.py`

---

## Running an Agent

The correct way to run a Nimble agent via the Python SDK is through the raw `POST /v1/agent` endpoint.

**IMPORTANT:** Do **not** use `client.extract(url=..., skill=...)` for running agents. That endpoint does not support agent execution and will return errors.

### Correct pattern

```python
import os
from nimble_python import Nimble

nimble = Nimble(api_key=os.environ["NIMBLE_API_KEY"])

resp = nimble.post(
    "/v1/agent",
    body={"agent": "<agent-name>", "params": {"param_key": "param_value"}},
    cast_to=object,
)

parsing = resp.get("data", {}).get("parsing", {})
```

### Response structure

The response from `POST /v1/agent` is a dict. Extracted data lives at `resp["data"]["parsing"]`.

### Response structure verification

**Before generating code**, always check the output fields from `nimble_agents_get` (the `skills` dict) to determine which response shape to expect:

- If `skills` has flat fields (`product_title`, `price`, `rating`) → flat list or dict.
- If `skills` has fields like `entity_type`, `position`, `cleaned_domain` grouped under distinct entity types → nested `parsing.entities.{EntityType}` structure.

This prevents generating broken parsing code. See `agent-api-reference.md` > "Response shape inference" for the full mapping table.

## Agent Parameters

Agent parameters vary by agent. Common patterns:

| Pattern | Parameter | Example |
|---------|-----------|---------|
| Product ID (Amazon) | `asin` | `{"asin": "B0CCZ1L489"}` |
| Product ID (Walmart) | `product_id` | `{"product_id": "436473700"}` |
| Product ID (Target) | `product_id` | `{"product_id": "91250634"}` |
| Search query | `keyword` | `{"keyword": "wireless headphones"}` |
| URL-based | `url` | `{"url": "https://example.com/page"}` |

Always check the agent's `input_properties` via `nimble_agents_get` to determine the correct parameter names.

---

## Single-Agent Example

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["nimble_python"]
# ///
"""Extract product details from Amazon."""
import os
from nimble_python import Nimble

nimble = Nimble(api_key=os.environ["NIMBLE_API_KEY"])

resp = nimble.post(
    "/v1/agent",
    body={"agent": "amazon_pdp", "params": {"asin": "B0CCZ1L489"}},
    cast_to=object,
)

parsing = resp.get("data", {}).get("parsing", {})
if isinstance(parsing, dict):
    print(
        f"title: {parsing.get('product_title')}, "
        f"price: {parsing.get('web_price')}, "
        f"rating: {parsing.get('average_of_reviews')}"
    )
```

Run: `NIMBLE_API_KEY=your-key uv run script.py`

---

## Batch Example with CSV Output

For batch processing, use `AsyncNimble` with `asyncio.Semaphore(10)` + `asyncio.gather`. Share a single client instance across all tasks.

**Note:** `AsyncNimble` holds an async HTTP connection pool (httpx) that should be closed when done via `await nimble.close()`. The sync `Nimble` class cleans up automatically.

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["nimble_python"]
# ///
"""Batch extraction with CSV output."""
import asyncio
import csv
import os
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


async def main():
    # Define extraction tasks
    jobs = [
        ("amazon_pdp", {"asin": "B0CCZ1L489"}),
        ("amazon_pdp", {"asin": "B09XS7JWHH"}),
        ("walmart_pdp", {"product_id": "436473700"}),
    ]

    results = await asyncio.gather(
        *(run_agent(a, p) for a, p in jobs),
        return_exceptions=True,
    )

    # Write to CSV
    rows = []
    for (agent, params), resp in zip(jobs, results):
        if isinstance(resp, Exception):
            continue
        parsing = resp.get("data", {}).get("parsing", {})
        if isinstance(parsing, list):
            for rec in parsing:
                rows.append({"agent": agent, **params, **rec})
        elif isinstance(parsing, dict):
            entities = parsing.get("entities")
            if entities:
                for entity_list in entities.values():
                    if isinstance(entity_list, list):
                        for rec in entity_list:
                            rows.append({"agent": agent, **params, **rec})
            else:
                rows.append({"agent": agent, **params, **parsing})

    if rows:
        with open("output.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        print(f"Wrote {len(rows)} rows to output.csv")

    await nimble.close()


asyncio.run(main())
```

---

## Async Agent Endpoint (High-Throughput)

`POST /v1/agent/async` decouples submission from processing. Submit jobs instantly, then poll for results concurrently.

### Async flow

1. **Submit** — `POST /v1/agent/async` with same body as `/v1/agent`. Returns immediately with `task_id`.
2. **Poll** — `GET /v1/tasks/{task_id}` until `task.state` reaches a terminal value.
3. **Retrieve** — `GET /v1/tasks/{task_id}/results` to fetch the parsed data.

### Task states

| State | Meaning |
|-------|---------|
| `pending` | Queued, not yet processing |
| `success` | Completed — fetch results |
| `failed` | Processing failed |

### Submit response structure

```python
resp = await nimble.post("/v1/agent/async", body={...}, cast_to=object)
# resp["task"]["id"]    — UUID for polling
# resp["task"]["state"] — always "pending" initially
task_id = resp["task"]["id"]
```

### Poll + retrieve

```python
# Poll
poll = await nimble.get(f"/v1/tasks/{task_id}", cast_to=object)
state = poll["task"]["state"]  # "pending", "success", or "failed"

# Retrieve (only after state == "success")
results = await nimble.get(f"/v1/tasks/{task_id}/results", cast_to=object)
parsing = results.get("data", {}).get("parsing", {})
```

### Smoke test — always validate one query first

**CRITICAL:** Before launching any batch, run a single query through the full submit → poll → fetch cycle. This catches auth issues, bad parameters, API outages, and parsing bugs before committing to hundreds of jobs.

```python
async def smoke_test(nimble, agent: str, params: dict, timeout: float = 90.0):
    """Run a single async job end-to-end. Returns parsed data or raises."""
    print(f"Smoke test: {agent} with {params}")

    # Submit
    r = await nimble.post("/v1/agent/async",
        body={"agent": agent, "params": params}, cast_to=object)
    task_id = r["task"]["id"]
    print(f"  Submitted task {task_id}")

    # Poll
    t0 = time.time()
    poll_count = 0
    while time.time() - t0 < timeout:
        await asyncio.sleep(3.0)
        poll_count += 1
        r = await nimble.get(f"/v1/tasks/{task_id}", cast_to=object)
        state = r.get("task", {}).get("state", "unknown")
        elapsed = time.time() - t0
        print(f"  Poll #{poll_count}: state={state} ({elapsed:.0f}s)")
        if state == "success":
            results = await nimble.get(
                f"/v1/tasks/{task_id}/results", cast_to=object)
            parsing = results.get("data", {}).get("parsing", {})
            print(f"  Smoke test passed — got data")
            return parsing
        if state == "failed":
            raise RuntimeError(f"Smoke test failed: task {task_id} state=failed")

    raise TimeoutError(
        f"Smoke test timed out after {timeout}s — task stuck at '{state}'. "
        f"The API may be overloaded or the query may be invalid.")
```

**Usage in scripts:** Call `smoke_test()` before `run_pipeline()`:

```python
# Validate one query before committing to the full batch
first_agent, first_params = jobs[0]
sample = await smoke_test(nimble, first_agent, first_params)
if not sample:
    print("Smoke test returned empty results — aborting batch")
    return
print(f"Smoke test OK. Launching {len(jobs)} jobs...\n")
```

### Progress reporting

Scripts running in background (via `Bash(run_in_background=True)`) need clear, compact progress output that is useful when tailing the output file.

**Rules:**
- Print a single-line status after each poll cycle — overwrite-friendly format
- Include: elapsed time, completed/total, results so far, in-flight count
- Use `PYTHONUNBUFFERED=1` or `print(..., flush=True)` to ensure output is visible immediately

```python
# Inside the main poll loop, after processing completions:
done_count = stats["completed"] + stats["failed"] + stats["timeout"]
elapsed = time.time() - t0
print(
    f"[{elapsed:>5.0f}s] {done_count}/{len(jobs)} done | "
    f"{len(rows)} results | {len(in_flight)} in-flight | "
    f"{stats['failed']} failed",
    flush=True,
)
```

### High-throughput batch pipeline

For large batches, maintain a pool of in-flight tasks. As tasks complete, immediately submit new ones to keep the pool full.

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["nimble_python"]
# ///
"""High-throughput async batch pipeline.

Keeps max_in_flight tasks on the server at all times. As tasks
complete, new ones are submitted immediately to fill the pool.

Always runs a smoke test on the first job before launching the batch.
"""
import asyncio, csv, os, time
from nimble_python import AsyncNimble

TERMINAL = {"success", "failed"}


# smoke_test() — identical to standalone version above (see "Smoke test" section).
# Included inline so this script is fully self-contained and copy-pasteable.
async def smoke_test(nimble, agent: str, params: dict, timeout: float = 90.0):
    """Run a single async job end-to-end. Returns parsed data or raises."""
    print(f"Smoke test: {agent} with {params}")
    r = await nimble.post("/v1/agent/async",
        body={"agent": agent, "params": params}, cast_to=object)
    task_id = r["task"]["id"]
    print(f"  Submitted task {task_id}")
    t0 = time.time()
    poll_count = 0
    state = "pending"
    while time.time() - t0 < timeout:
        await asyncio.sleep(3.0)
        poll_count += 1
        r = await nimble.get(f"/v1/tasks/{task_id}", cast_to=object)
        state = r.get("task", {}).get("state", "unknown")
        elapsed = time.time() - t0
        print(f"  Poll #{poll_count}: state={state} ({elapsed:.0f}s)", flush=True)
        if state == "success":
            results = await nimble.get(
                f"/v1/tasks/{task_id}/results", cast_to=object)
            parsing = results.get("data", {}).get("parsing", {})
            print(f"  Smoke test passed — got data")
            return parsing
        if state == "failed":
            raise RuntimeError(f"Smoke test failed: task {task_id} state=failed")
    raise TimeoutError(
        f"Smoke test timed out after {timeout}s — task stuck at '{state}'")


async def run_pipeline(
    nimble,
    jobs: list[tuple[str, dict]],
    max_in_flight: int = 100,
    poll_interval: float = 3.0,
    task_timeout: float = 120.0,
):
    """Async batch pipeline. Returns (rows, stats)."""
    t0 = time.time()
    queue = list(reversed(jobs))  # pop() = FIFO
    in_flight = {}   # task_id -> {agent, params, submitted_at}
    rows = []
    stats = {"submitted": 0, "completed": 0, "failed": 0, "timeout": 0}

    async def submit_one():
        if not queue:
            return
        agent, params = queue.pop()
        r = await nimble.post("/v1/agent/async",
            body={"agent": agent, "params": params}, cast_to=object)
        in_flight[r["task"]["id"]] = {
            "agent": agent, "params": params, "t": time.time(),
        }
        stats["submitted"] += 1

    # Fill initial window
    await asyncio.gather(*(submit_one() for _ in range(min(max_in_flight, len(queue)))))
    print(f"Submitted initial batch of {min(max_in_flight, stats['submitted'])} jobs",
          flush=True)

    # Main loop: poll → expire → fetch → refill
    while in_flight or queue:
        await asyncio.sleep(poll_interval)
        now = time.time()

        # Expire stuck tasks (>task_timeout seconds)
        for tid in [t for t, i in in_flight.items() if now - i["t"] > task_timeout]:
            del in_flight[tid]
            stats["timeout"] += 1

        if not in_flight and not queue:
            break

        # Poll all in-flight
        async def check(tid):
            r = await nimble.get(f"/v1/tasks/{tid}", cast_to=object)
            return tid, r.get("task", {}).get("state")

        poll_results = await asyncio.gather(
            *(check(t) for t in in_flight), return_exceptions=True)

        # Collect completed + fetch results
        done = [(tid, st) for tid, st in
                (item for item in poll_results if not isinstance(item, Exception))
                if st in TERMINAL]

        if done:
            async def fetch(tid, state):
                info = in_flight.pop(tid)
                if state != "success":
                    stats["failed"] += 1
                    return
                r = await nimble.get(f"/v1/tasks/{tid}/results", cast_to=object)
                parsing = r.get("data", {}).get("parsing", {})
                if isinstance(parsing, list):
                    for rec in parsing:
                        rows.append({"agent": info["agent"], **info["params"], **rec})
                elif isinstance(parsing, dict) and parsing:
                    entities = parsing.get("entities")
                    if entities:
                        for entity_list in entities.values():
                            if isinstance(entity_list, list):
                                for rec in entity_list:
                                    rows.append({"agent": info["agent"], **info["params"], **rec})
                    else:
                        rows.append({"agent": info["agent"], **info["params"], **parsing})
                stats["completed"] += 1

            await asyncio.gather(*(fetch(tid, st) for tid, st in done))

        # Refill window
        to_submit = min(max_in_flight - len(in_flight), len(queue))
        if to_submit:
            await asyncio.gather(*(submit_one() for _ in range(to_submit)))

        # Progress
        done_count = stats["completed"] + stats["failed"] + stats["timeout"]
        elapsed = time.time() - t0
        print(
            f"[{elapsed:>5.0f}s] {done_count}/{len(jobs)} done | "
            f"{len(rows)} results | {len(in_flight)} in-flight | "
            f"{stats['failed']} failed",
            flush=True,
        )

    stats["wall_time"] = time.time() - t0
    return rows, stats


async def main():
    nimble = AsyncNimble(api_key=os.environ["NIMBLE_API_KEY"], max_retries=2, timeout=120.0)

    jobs = [
        ("amazon_pdp", {"asin": "B0CCZ1L489"}),
        ("amazon_pdp", {"asin": "B09XS7JWHH"}),
        ("walmart_pdp", {"product_id": "436473700"}),
    ]

    # Validate first job before launching batch
    first_agent, first_params = jobs[0]
    sample = await smoke_test(nimble, first_agent, first_params)
    if not sample:
        print("ERROR: Smoke test returned empty results — aborting.")
        await nimble.close()
        return
    print(f"Smoke test OK. Launching {len(jobs)} jobs...\n", flush=True)

    rows, stats = await run_pipeline(nimble, jobs)

    if rows:
        with open("output.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=rows[0].keys())
            w.writeheader()
            w.writerows(rows)
        print(f"\nWrote {len(rows)} rows  |  {stats}")

    await nimble.close()


asyncio.run(main())
```

### Tuning parameters

| Parameter | Small (≤5) | Medium (6-50) | Large (50+) |
|-----------|-----------|---------------|-------------|
| `max_in_flight` | 5 | 50 | 100 |
| `poll_interval` | 1.5s | 3.0s | 5.0s |
| `task_timeout` | 45s | 90s | 120s |

### When to use async vs sync

| Scenario | Endpoint | Why |
|----------|----------|-----|
| Single agent run (interactive) | `/v1/agent` (sync) | Simpler, immediate result |
| 2-3 agents, user waiting | `/v1/agent` + `asyncio.gather` | Low overhead, fast enough |
| 4+ agents, batch processing | **`/v1/agent/async`** + batch pipeline | Much higher throughput than sync |
| Background / scheduled jobs | **`/v1/agent/async`** + `callback_url` | No polling needed |

### AsyncOptions (optional submit parameters)

| Parameter | Type | Description |
|-----------|------|-------------|
| `storage_url` | string | S3/GCS bucket URL for result delivery (e.g., `"s3://my-bucket/"`) |
| `storage_type` | string | Storage provider: `"s3"` or `"gcs"` |
| `callback_url` | string | Webhook URL — receives POST when task completes |

```python
# Submit with callback (no polling needed)
await nimble.post("/v1/agent/async", body={
    "agent": "amazon_serp",
    "params": {"keyword": "wireless headphones"},
    "callback_url": "https://my-server.com/webhook",
}, cast_to=object)
```

---

## Incremental File Writes (Crash-Resilient)

For large pipelines (50+ jobs), write records to disk as each batch completes. This bounds memory and preserves partial results on crashes.

### Why this is safe in asyncio

`asyncio` is single-threaded cooperative multitasking. Synchronous file I/O (`writer.writerow()`, `f.write()`, `pq.write_table()`) never yields to the event loop, so **no two coroutines can interleave mid-write** — even inside `asyncio.gather`. No locks required.

### Format comparison

| Format | Append-friendly | Crash-resilient | Schema evolution | Compressible | Extra dependency |
|--------|:-:|:-:|:-:|:-:|---|
| **CSV** | Yes | Yes (flush) | Drops extra cols | No | None |
| **JSONL** | Yes | Yes (flush) | Natural (self-describing) | No | None |
| **Parquet (partitioned dir)** | Yes (new part file per batch) | Yes (each part self-contained) | `pa.unify_schemas()` at read | Snappy/zstd | `pyarrow` |
| **JSON array** | **No** | **No** | N/A | No | None |

**JSON arrays are NOT append-friendly.** A JSON array (`[{...}, {...}]`) requires the entire structure in memory to write. If the user requests JSON output, either:
1. **Use JSONL instead** and note that it can be converted to JSON after completion.
2. **Buffer in memory** and write the JSON array at the end (no crash resilience for large batches).
3. For crash resilience with JSON-like output, write JSONL incrementally, then convert at the end:
   ```python
   # After pipeline completes — convert JSONL to JSON array
   with open("output.jsonl") as f:
       rows = [json.loads(line) for line in f]
   with open("output.json", "w") as f:
       json.dump(rows, f, indent=2, ensure_ascii=False)
   ```

Only use incremental file writers (CSV, JSONL, Parquet) when the target format supports it. For formats that do not (JSON array, Excel), buffer in memory and write at the end.

### CSV incremental writer

```python
import csv

class CSVIncrementalWriter:
    def __init__(self, path: str):
        self.path = path
        self._file = None
        self._writer = None
        self._fieldnames = None
        self.rows_written = 0

    def write_batch(self, rows: list[dict]):
        if not rows:
            return
        if self._file is None:
            self._fieldnames = list(rows[0].keys())
            self._file = open(self.path, "w", newline="")
            self._writer = csv.DictWriter(
                self._file, fieldnames=self._fieldnames,
                extrasaction="ignore")
            self._writer.writeheader()
        self._writer.writerows(rows)
        self._file.flush()
        self.rows_written += len(rows)

    def close(self):
        if self._file:
            self._file.close()
```

**Late columns:** `extrasaction="ignore"` silently drops columns not in the header. Missing keys produce empty strings.

### JSONL incremental writer

```python
import json

class JSONLIncrementalWriter:
    def __init__(self, path: str):
        self._file = open(path, "w")
        self.rows_written = 0

    def write_batch(self, rows: list[dict]):
        for row in rows:
            self._file.write(json.dumps(row, ensure_ascii=False) + "\n")
        self._file.flush()
        self.rows_written += len(rows)

    def close(self):
        self._file.close()
```

### Parquet partitioned directory writer

Each `write_batch` creates a self-contained `.parquet` part file. Crash-safe: completed files survive.

```python
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path

class ParquetPartitionedWriter:
    def __init__(self, directory: str, schema: pa.Schema | None = None):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self._schema = schema
        self._part_num = 0
        self.rows_written = 0

    def write_batch(self, rows: list[dict]):
        if not rows:
            return
        table = pa.Table.from_pylist(rows, schema=self._schema)
        if self._schema is None:
            self._schema = table.schema
        pq.write_table(table, self.directory / f"part-{self._part_num:06d}.parquet",
                        compression="snappy")
        self._part_num += 1
        self.rows_written += len(rows)

    def read_all(self) -> pa.Table:
        import pyarrow.dataset as ds
        parts = sorted(self.directory.glob("*.parquet"))
        if not parts:
            return pa.table({})
        unified = pa.unify_schemas([pq.read_schema(str(p)) for p in parts])
        return ds.dataset(str(self.directory), format="parquet",
                          schema=unified).to_table()
```

**Schema evolution:** Different part files can have different schemas. `pa.unify_schemas()` merges them — missing columns become null at read time.

**Compaction:** After the pipeline finishes, optionally merge parts into a single optimized file:

```python
table = writer.read_all()
pq.write_table(table, "output.parquet", compression="snappy")
```

### Integration with the async pipeline

Call `write_batch()` inside the `fetch()` coroutine, right after parsing results:

```python
if done:
    batch_rows = []

    async def fetch(tid, state):
        info = in_flight.pop(tid)
        if state != "success":
            stats["failed"] += 1
            return
        r = await nimble.get(f"/v1/tasks/{tid}/results", cast_to=object)
        parsing = r.get("data", {}).get("parsing", {})
        # ... parse rows as before ...
        batch_rows.extend(parsed_rows)
        stats["completed"] += 1

    await asyncio.gather(*(fetch(tid, st) for tid, st in done))
    writer.write_batch(batch_rows)  # sync — safe, no interleaving
```

### Key rules

- **Format guard:** Only use incremental writers for CSV, JSONL, or Parquet. For JSON array or Excel output, buffer in memory and write at the end.
- **File handle:** Open once at pipeline start, close in `finally`
- **Flush:** After each poll cycle's batch — balances durability vs I/O
- **No threading:** Stay within asyncio. `threading`/`multiprocessing` breaks the safety guarantee
- **Parquet add `pyarrow` to script deps:** `# dependencies = ["nimble_python", "pyarrow"]`

---

## Retry Behavior

The SDK retries transient errors (429, 5xx, timeouts) automatically with exponential backoff. Default: 2 retries. For batch scripts, increase to 4: `AsyncNimble(max_retries=4, timeout=120.0)`. Do NOT implement custom retry logic — the SDK handles it correctly.

---

## Common Mistakes

| Mistake | Correct approach |
|---------|-----------------|
| `client.extract(url=..., skill=...)` | `nimble.post("/v1/agent", body={...}, cast_to=object)` |
| `response.data.parsing.entities` | `resp.get("data", {}).get("parsing", {})` |
| `nimble.agent(...)` | Method does not exist. Use `nimble.post(...)` |
| `nimble.agents.run(...)` | `agents` is for management only. Use `nimble.post(...)` |
| Assuming all responses are lists | Check `isinstance(parsing, list)` vs `isinstance(parsing, dict)` |
| Using `pip install` for one-off scripts | Use `uv run` with inline `# /// script` metadata |
| Checking `state == "completed"` for async | Terminal state is `"success"`, not `"completed"` |
| Using semaphore on async submit | Submit freely — no observed submission rate limit |
| Fixed poll interval for large batches | Scale poll interval with batch size (see tuning table) |
| Polling `/v1/tasks` via raw curl | Use SDK `nimble.get(...)` — curl may 401 due to auth handling |
| Using sync `/v1/agent` for 4+ parallel jobs | Use `/v1/agent/async` for batch workloads |
| Assuming `parsing` is always a flat list for SERP agents | `google_search` and similar non-ecommerce SERP agents return `parsing.entities.OrganicResult` — always check `nimble_agents_get` output fields first |
| Using `agent.input_schema` or `agent.output_schema` | Actual fields are `agent.input_properties` (array) and `agent.skills` (dict) — see `agent-api-reference.md` |
| Appending to a JSON array file incrementally | JSON arrays require the full structure in memory — use JSONL or CSV for incremental writes. Convert JSONL to JSON array at end if needed. |
| Using `ParquetWriter` for crash-resilient writes | `ParquetWriter` data is lost if process dies before `close()`. Use partitioned directory instead. |
| Using `threading` with shared file writer in asyncio | Stay in asyncio — single-thread model guarantees safe writes. Threading breaks this. |
| Launching 50+ async jobs without testing one first | Always run `smoke_test()` on the first job. Catches auth, bad params, API outages before wasting time. |
| No progress output in background scripts | Print compact status each poll cycle with `flush=True`. Essential for `tail -f` monitoring. |

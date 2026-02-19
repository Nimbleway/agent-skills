# Nimble Python SDK Patterns

Reference for generating correct Python code that runs Nimble agents programmatically.

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
    body={"agent": "agent-name", "params": {"param_key": "param_value"}},
    cast_to=object,
)

parsing = resp.get("data", {}).get("parsing", {})
```

### Response structure

The response from `POST /v1/agent` is a dict. Extracted data lives at `resp["data"]["parsing"]`.

Two response shapes exist depending on the agent type:

| Agent type | `parsing` shape | Example agents |
|-----------|----------------|----------------|
| Detail/PDP agents | `dict` (flat object with fields) | `amazon_pdp`, `walmart_pdp`, `target_pdp` |
| Search/SERP agents | `list` (array of record dicts) | `amazon_serp`, `walmart_serp`, `target_serp` |

### Handling both response types

```python
parsing = resp.get("data", {}).get("parsing", {})

if isinstance(parsing, list):
    # Search/SERP agent — list of records
    for record in parsing:
        print(record.get("field_name"))
elif isinstance(parsing, dict):
    # Detail/PDP agent — single record as flat dict
    print(parsing.get("field_name"))
```

---

## Agent Parameters

Agent parameters vary by agent. Common patterns:

| Pattern | Parameter | Example |
|---------|-----------|---------|
| Product ID (Amazon) | `asin` | `{"asin": "B0CCZ1L489"}` |
| Product ID (Walmart) | `product_id` | `{"product_id": "436473700"}` |
| Product ID (Target) | `product_id` | `{"product_id": "91250634"}` |
| Search query | `keyword` | `{"keyword": "wireless headphones"}` |
| URL-based | `url` | `{"url": "https://example.com/page"}` |

Always check the agent's `input_schema` via `nimble_agents_get` to determine the correct parameter names.

---

## Async Parallel Execution

For batch processing many items, use `AsyncNimble` with `asyncio.gather` for concurrent requests.

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["nimble_python"]
# ///
import asyncio
import os
from nimble_python import AsyncNimble

nimble = AsyncNimble(api_key=os.environ["NIMBLE_API_KEY"])


async def run_agent(agent: str, params: dict) -> dict:
    return await nimble.post(
        "/v1/agent",
        body={"agent": agent, "params": params},
        cast_to=object,
    )


async def main():
    tasks = [
        run_agent("amazon_pdp", {"asin": "B0CCZ1L489"}),
        run_agent("amazon_pdp", {"asin": "B09XS7JWHH"}),
        run_agent("walmart_pdp", {"product_id": "436473700"}),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for resp in results:
        if isinstance(resp, Exception):
            print(f"Error: {resp}")
            continue
        parsing = resp.get("data", {}).get("parsing", {})
        # process parsing...


asyncio.run(main())
```

### Concurrency tuning

Use `asyncio.Semaphore` to limit concurrent requests. Benchmarked optimal concurrency for Nimble agent calls:

| Concurrency | Throughput | Errors | Verdict |
|:-----------:|:----------:|:------:|---------|
| 5 | 0.17 req/s | rare | Too slow — requests queue up |
| **10** | **0.36 req/s** | **0%** | **Sweet spot — zero errors** |
| 15 | 0.38 req/s | ~7% | Marginal gain, some errors |
| 20 | 0.36 req/s | ~20% | No speed gain, more errors |
| 30 | 0.49 req/s | ~20% | Fastest wall-clock but 20% failure |

**Use `Semaphore(10)` as the default.** Going higher causes 429s without meaningful speed gains because the bottleneck is server-side processing time (7–55s per request), not client dispatch.

```python
SEM = asyncio.Semaphore(10)  # benchmarked sweet spot

async def run_agent_throttled(agent: str, params: dict) -> dict:
    async with SEM:
        return await nimble.post(
            "/v1/agent",
            body={"agent": agent, "params": params},
            cast_to=object,
        )
```

Additional tips:
- Wrap individual calls in try/except to handle failures without aborting the batch.
- For very large batches (1000+), process in chunks to manage memory.
- A single `AsyncNimble` instance reuses connections — always share one client across all tasks.

---

## Complete Single-Agent Example

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

## Complete Batch Example with CSV Output

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

nimble = AsyncNimble(api_key=os.environ["NIMBLE_API_KEY"])
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
        if isinstance(parsing, dict):
            rows.append({"agent": agent, **params, **parsing})
        elif isinstance(parsing, list):
            for rec in parsing:
                rows.append({"agent": agent, **params, **rec})

    if rows:
        with open("output.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        print(f"Wrote {len(rows)} rows to output.csv")


asyncio.run(main())
```

---

## Retry Behavior

### SDK built-in retry (use this — no custom code needed)

The `nimble_python` SDK retries automatically on transient errors. No custom retry wrapper needed.

| Setting | Default | Configurable via |
|---------|---------|-----------------|
| Max retries | 2 | `Nimble(max_retries=N)` or `AsyncNimble(max_retries=N)` |
| Initial delay | 0.5s | — |
| Max delay | 8.0s | — |
| Backoff | `min(0.5 * 2^attempt, 8.0) * jitter` | — |
| Jitter | `1 - 0.25 * random()` (0.75x–1.0x) | — |

**Automatically retried:** 429 (rate limit), 408, 409, 5xx, connection errors, timeouts, `x-should-retry: true` header.

**Not retried:** 400, 401, 403, 404 (client errors — the request itself is wrong).

**Retry-After header respected:** If the API returns `Retry-After` between 0–60s, the SDK uses that instead of the calculated backoff.

**Recommendation for batch scripts:** Increase retries to 4:

```python
nimble = AsyncNimble(
    api_key=os.environ["NIMBLE_API_KEY"],
    max_retries=4,       # up from default 2
    timeout=120.0,       # 2 min per request (agents can be slow)
)
```

### When to add custom retry on top of SDK retry

Only needed when graceful degradation is required after all SDK retries exhaust:

```python
from nimble_python import AsyncNimble, RateLimitError

async def run_agent_safe(nimble, agent: str, params: dict) -> dict | None:
    try:
        return await nimble.post(
            "/v1/agent",
            body={"agent": agent, "params": params},
            cast_to=object,
        )
    except RateLimitError as e:
        retry_after = e.response.headers.get("Retry-After", "?")
        print(f"Rate limited after all retries (retry-after: {retry_after})")
        return None  # graceful degradation
    except Exception as e:
        print(f"Failed: {type(e).__name__}: {e}")
        return None
```

Do NOT re-implement exponential backoff — the SDK already does it correctly.

---

## Dynamic Batching (Semaphore-Only Pattern)

For batch processing, use the **semaphore-only** pattern instead of fixed-batch + gather.

**Why:** Fixed batching (process N, wait for ALL N to finish, then start next N) suffers from
the "wait for slowest in batch" problem. With API calls ranging 7–55s, this wastes significant
time. The semaphore-only pattern launches all tasks upfront and starts new ones the instant
any slot frees up — achieving ~7x speedup over sequential execution.

```python
async def main():
    nimble = AsyncNimble(
        api_key=os.environ["NIMBLE_API_KEY"],
        max_retries=4,   # SDK handles backoff automatically
        timeout=120.0,
    )
    sem = asyncio.Semaphore(10)  # benchmarked sweet spot

    jobs = [("amazon_serp", {"keyword": "headphones"}), ...]
    completed = 0

    async def run_one(agent, params):
        nonlocal completed
        async with sem:
            try:
                resp = await nimble.post(
                    "/v1/agent",
                    body={"agent": agent, "params": params},
                    cast_to=object,
                )
                return resp
            except Exception as e:
                return e
            finally:
                completed += 1
                print(f"\r  {completed}/{len(jobs)} done", end="", flush=True)

    # Launch ALL tasks — semaphore limits concurrency dynamically
    tasks = [run_one(a, p) for a, p in jobs]
    results = await asyncio.gather(*tasks)
    print()

    for resp in results:
        if isinstance(resp, Exception):
            continue
        parsing = resp.get("data", {}).get("parsing", {})
        # process...
```

**Key difference:** `asyncio.gather` with a semaphore maintains exactly `min(remaining, limit)`
in-flight requests at all times. Total runtime approaches `ceil(N / K) * avg_time` rather than
`ceil(N / K) * max_time`.

**No external dependencies needed.** The SDK's built-in retry handles 429/5xx with exponential
backoff. The semaphore holds the slot during retries, preventing retry storms.

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

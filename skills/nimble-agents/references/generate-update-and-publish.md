# Generate, Update, and Publish an Agent

Background agent workflow for creating, updating, and publishing agents with automated validation.

**HARD RULE: `nimble_agents_generate`, `nimble_agents_update`, `nimble_agents_status`, and `nimble_agents_publish` are BANNED from the foreground conversation.** This entire workflow MUST run inside a background `Task(subagent_type="general-purpose", run_in_background=True)` agent. Calling these tools in the foreground floods context with large polling responses. No exceptions — not even for a single update or status check.

## Overview — Closed-loop lifecycle

```
User chooses refine-validate (yes/no) — ONCE, in the foreground
        ↓
┌─→ Discovery (nimble_web_search deep → refined prompt, fields, URLs)
│   ↓
│   Create/Update (nimble_agents_generate or nimble_agents_update)
│   ↓
│   Poll (nimble_agents_status every 30s, max 10 checks)
│   ↓                              ↓
│   5 consecutive errors ──→┐   On complete
│                           │      ↓
│                           │   Validate (SDK script, 50 inputs, ≥80% pass)
│                           │      ↓              ↓
│                           │   ≥80% pass     <80% pass
│                           │      ↓              │
│                           │   Publish           │
│                           │      ↓              │
│                           │   Report            │
│                           │                     │
│   ┌───────────────────────┘                     │
│   ↓  UPDATE LOOP (auto-triggered)  ←────────────┘
│   Discovery with failure context
│   ↓
└── nimble_agents_update (same session_id) → re-poll → re-validate
    (max 2 cycles → escalate to user)
    NEVER regenerate — always update
```

**Key rule:** The update loop is **auto-triggered on failure** — 5 consecutive poll errors/issue-messages, poll timeout, or <80% validation — regardless of the user's initial preference. The user's choice only controls whether discovery and validation run on the *happy path*. **Never regenerate — always use `nimble_agents_update` with the same session_id for all recovery.**

**Overall timeout: 15 minutes wall-clock.** The entire background agent lifecycle — all cycles, all phases combined — must complete within 15 minutes. If the timeout is reached, immediately stop, skip remaining phases, and jump to Phase 6 (Report) with `STATUS: timed_out`. Use `max_turns=50` on the Task launch to enforce a turn budget.

## Phase 0: User preference (ONCE, in the foreground)

**CRITICAL: AskUserQuestion happens ONCE in the foreground conversation, BEFORE launching the background agent. The background agent receives `refine_validate=true|false` and NEVER asks the user anything.**

```
question: "Run refinement-validation before publishing?"
header: "Validate"
options:
  - label: "Yes, validate (Recommended)"
    description: "Discovery → generate → validate 50 inputs (80% pass) → publish. Auto-retries on failure."
  - label: "No, generate only"
    description: "Generate → publish immediately without validation testing"
```

This determines `refine_validate=true|false` for the background agent. Even with `false`, failures still auto-trigger the loop.

## Phase 1: Discovery

Run when `refine_validate=true` OR when entering the refine-validate loop after a failure.

**Discovery tools:**

1. **`nimble_web_search`** (MCP) with `deep_search=true`, `max_results=5` — searches the target domain and extracts full page content from each result. This provides product listings, detail pages, and field structures in a single call.

**Discovery outputs** (feed into the generate/update prompt):
- Refined extraction prompt with specific field names
- Target URLs or URL patterns
- Expected input fields (with examples)
- Expected output fields (with types)
- Links to example pages

Skip discovery when the user provides a fully specified prompt with URL, fields, and clear intent. **Always run discovery when entering the refine-validate loop after a failure.** When re-entering from failure, also include:
- All accumulated error messages
- Failing input examples
- Failure pattern analysis (empty results, exceptions, partial data)

## Phase 2: Create or Update

### Initial creation

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

### Update (refining existing agent)

`nimble_agents_update` is the primary tool for all post-creation interactions:
- Refining existing agents (change output fields, adjust behavior)
- Answering follow-up questions from `nimble_agents_generate` (`waiting` status)
- Retrying errors (compose fix prompt from diagnostics)
- Continuing any session started by generate or update
- Refine-validate loop — updating after validation failures

`nimble_agents_generate` is only used once for initial creation.

```json
{
  "tool": "nimble_agents_update",
  "params": {
    "agent_name": "yelp-restaurant-details",
    "prompt": "Add review_count and photos_count to the output schema",
    "session_id": "a3b1c2d4-5678-9abc-def0-1234567890ab"
  }
}
```

**Published agents** (`is_public=True` or owned by another user):
- Automatically forked to a private copy under the caller's account
- All sub-resources are cloned; original agent is untouched
- Returns a new `session_id` for the forked version

**User's unpublished agents** (`is_public=False`, owned by caller):
- Updated in-place on the existing thread
- No fork — modifications apply directly

### Status handling

| Status | Action |
|--------|--------|
| `waiting` | Relay follow-up questions to user via `AskUserQuestion`. Call `nimble_agents_update` with same `session_id` and user's answer as `prompt`. |
| `processing` | Enter Phase 3 (polling). |
| `complete` | Enter Phase 4 (validation) if `refine_validate=true`, otherwise Phase 5 (publish). |
| `error` | Apply retry-with-fix (max 2 retries, then auto-trigger refine-validate loop). |

### Retry-with-fix protocol

When update (or status polling) returns `status="error"`:

1. Read the `error` and `message` fields — they contain supervisor diagnostics.
2. Compose a fix prompt:
   ```
   "The previous attempt failed: {error}. The assistant reported: {message}. Please fix the configuration accordingly."
   ```
3. Call `nimble_agents_update` with same `session_id` and the fix prompt.
4. If it returns `processing`, resume polling with `nimble_agents_status`.
5. Max 2 retries — then trigger the update loop (discovery with error context, then `nimble_agents_update` with same session_id).

## Phase 3: Polling with consecutive error tracking

Poll with `nimble_agents_status` every **strictly 30 seconds** (max 10 checks per polling phase). Use `Bash(sleep 30)` — never sleep longer.

Use `nimble_agents_status` (read-only GET) for polling — never `nimble_agents_generate` (POST).

### 5 consecutive errors/issue-messages → auto-trigger update loop

**This is a hard rule.** Track every polled status that returns `error` or contains an issue/problem message. When 5 consecutive such statuses occur:

1. **Collect** all error messages and issue descriptions from the 5 failures.
2. **Run discovery** (Phase 1) with accumulated error context to understand the failure pattern.
3. **Update** — call `nimble_agents_update` with the **same session_id** and a refined prompt incorporating error analysis.
4. **Resume** from Phase 3 (polling).

**Never regenerate. Never create a new session_id.** Always use `nimble_agents_update` to fix the existing agent. This happens automatically regardless of the user's initial `refine_validate` preference.

### Polling template

```
Track consecutive_errors = 0, check_count = 0.
Loop: call nimble_agents_status, check_count += 1, check status.
- "processing" → consecutive_errors = 0, print progress, Bash(sleep 30), repeat.
- "complete" → consecutive_errors = 0, print agent_name and schemas. Stop.
- "waiting" → consecutive_errors = 0, print "WAITING: " + message. Stop.
- "error" → consecutive_errors += 1, print "ERROR ({consecutive_errors}/5): " + error.
  If consecutive_errors >= 5: print "UPDATE_LOOP_TRIGGERED: " + all error messages. Stop.
  Otherwise: Bash(sleep 30), repeat.
Max 10 checks per polling phase (5 minutes).
If max checks reached: print "POLL_TIMEOUT: generation did not complete after 10 checks."
  → Treat as generation failure → auto-trigger refine-validate (same as 5 consecutive errors).
```

## Phase 4: Validation (SDK script, 50-input test set)

Run when `refine_validate=true` OR when auto-triggered by the refine-validate loop.

**CRITICAL: Validation uses a generated SDK script executed via `uv run`, NOT 50 individual MCP tool calls.** The script uses the REST API `POST /v1/agent` (response at `data.parsing`), not MCP `nimble_agents_run` (response at `data.results`).

### Step 4a: Generate test inputs

Generate or search for **50 diverse test inputs** matching the agent's `input_properties`. Variability is critical:

- **Different entities** — varied products, pages, queries (not the same item 50 times)
- **Edge cases** — missing fields, unusual formats, non-English content where applicable
- **Scale variation** — short queries, long queries, single-word, multi-word
- **URL patterns** — different URL structures for the same domain (if URL-based)

**How to generate inputs:**

1. Read `input_properties` from `nimble_agents_get` to understand required fields and types.
2. Use `nimble_web_search` (MCP) with `deep_search=true` to find real examples of the target domain/content.
3. Combine searched real-world inputs with synthetically varied inputs.
4. Store the 50 inputs as a JSON array.

### Step 4b: Generate and run validation script

The background agent generates a Python validation script, writes it to `/tmp/validate_agent_{agent_name}.py`, and executes via `Bash(uv run /tmp/validate_agent_{agent_name}.py)`.

**Validation script template:**

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["nimble_python"]
# ///
"""Validate {agent_name} with 50 diverse test inputs."""
import asyncio, json, os
from nimble_python import AsyncNimble

AGENT = "{agent_name}"
INPUTS = {json_array_of_50_inputs}

async def main():
    nimble = AsyncNimble(api_key=os.environ["NIMBLE_API_KEY"], max_retries=2, timeout=60.0)
    sem = asyncio.Semaphore(10)
    results = {"passed": 0, "failed": 0, "errors": [], "empty": []}

    async def run_one(i, params):
        async with sem:
            try:
                resp = await nimble.post(
                    "/v1/agent",
                    body={"agent": AGENT, "params": params},
                    cast_to=object,
                )
                parsing = resp.get("data", {}).get("parsing", {})
                if parsing and (
                    isinstance(parsing, list) and len(parsing) > 0
                    or isinstance(parsing, dict) and any(v for v in parsing.values() if v)
                ):
                    results["passed"] += 1
                else:
                    results["failed"] += 1
                    results["empty"].append({"index": i, "input": params})
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({"index": i, "input": params, "error": str(e)})

    await asyncio.gather(*(run_one(i, p) for i, p in enumerate(INPUTS)))
    await nimble.close()

    results["pass_rate"] = round(results["passed"] / len(INPUTS) * 100, 1)
    print(json.dumps(results, indent=2, ensure_ascii=False), flush=True)

asyncio.run(main())
```

**Key points:**
- Uses REST API `POST /v1/agent` (response at `data.parsing`), NOT MCP `nimble_agents_run` (response at `data.results`)
- `asyncio.Semaphore(10)` for concurrency control
- `asyncio.gather` for parallel execution
- Outputs JSON to stdout for the background agent to parse

### Step 4c: Assert 80% success

| Pass rate | Action |
|-----------|--------|
| >= 80% | Validation passed → Phase 5 (publish). |
| < 80% | **Auto-trigger update loop**: analyze failures → Phase 1 (discovery with failure context) → Phase 2 (`nimble_agents_update` with same session_id) → Phase 3 (poll) → Phase 4 (re-validate with same 50 inputs). Max 2 cycles. |

**Failure analysis for the refine-validate prompt:**
- Group errors by type (empty results, exceptions, partial data)
- Identify which input patterns fail most
- Compose a refinement prompt:
  ```
  "The agent failed on {X}% of test inputs. Common failures: {patterns}.
   Example failing inputs: {samples}. Refine the extraction to handle these cases."
  ```

## Phase 5: Publish

After validation passes (>= 80%) or immediately after `complete` (if `refine_validate=false` and no failures):

```json
{
  "tool": "nimble_agents_publish",
  "params": {
    "session_id": "a3b1c2d4-5678-9abc-def0-1234567890ab"
  }
}
```

If 409 (already published), proceed to report.

## Phase 6: Report

Return a structured generation/update report **regardless of outcome** (pass or fail):

```markdown
## Agent Generation Report

| Field | Value |
|-------|-------|
| Agent name | `{agent_name}` |
| Operation | Generated / Updated |
| Domain | {domain} |
| Session ID | `{session_id}` |
| Status | Published / Failed |

### Validation Results

| Metric | Value |
|--------|-------|
| Test inputs | 50 |
| Passed | {n} |
| Failed | {m} |
| Pass rate | {rate}% |
| Refine cycles | {count} |

### Input Schema
{input fields table}

### Output Schema
{output fields table}

### Sample Results
{top 3 successful extractions as table}

### Errors (if any)
{error summary}
```

## Update loop (auto-triggered on failure)

**Two triggers — both auto-fire the same closed loop using `nimble_agents_update` (never regenerate):**

| Trigger | When | What happens |
|---------|------|-------------|
| 5 consecutive poll errors | 5 `error`/issue-message statuses in a row, or poll timeout (10 checks) | Discovery with accumulated errors → `nimble_agents_update` (same session_id) → poll → validate |
| Validation failure | < 80% pass rate | Analyze failures → discovery with failure context → `nimble_agents_update` (same session_id) → poll → re-validate with same 50 inputs |

**Never regenerate. Never create a new session_id.** Always use `nimble_agents_update` to fix the existing agent.

**Max 2 update cycles.** After 2 cycles without reaching 80%, the background agent stops and reports the best result. The foreground conversation presents recovery options to the user.

## Background agent Task prompt template

```
Task(subagent_type="general-purpose", run_in_background=True, max_turns=50, prompt="""
Generate/update agent workflow.

**Session ID:** {session_id}
**Agent intent:** {user_prompt}
**Target URL:** {url}
**Operation:** generate | update
**Refine-validate:** {true|false}

**IMPORTANT: Do NOT use AskUserQuestion. All decisions are pre-made.**
**IMPORTANT: Do NOT use nimble_find_search_agent, nimble_run_search_agent, or any WSA template tools.**

Execute the closed-loop lifecycle:

1. DISCOVERY (if refine_validate=true, or re-entering from failure):
   - Use `nimble_web_search` (MCP) with deep_search=true, max_results=5 to explore the target domain and extract page content.
   - Build a refined prompt with specific fields, URLs, and examples.
   - If re-entering from failure, include all accumulated error messages and failing inputs.

2. CREATE/UPDATE:
   - First time: call nimble_agents_generate with the prompt.
   - All subsequent (recovery, refinement): call nimble_agents_update with the SAME session_id. NEVER regenerate.
   - Handle waiting/processing/complete/error statuses.
   - On error: retry with fix prompt (max 2). After 2 failures → go to step 1 (update loop).

3. POLL (if processing):
   - Call nimble_agents_status every STRICTLY 30s (use Bash(sleep 30), never longer), max 10 checks.
   - Track consecutive_errors counter.
   - If 10 checks reached without completion: treat as failure, trigger update loop.
   - After 5 consecutive error/issue-message statuses:
     → Collect all error messages.
     → Go to step 1 (update loop) with error context. Keep same session_id.

4. VALIDATE (if refine_validate=true, or re-entering from failure):
   - Call nimble_agents_get to read input_properties.
   - Generate 50 diverse test inputs (use `nimble_web_search` MCP with deep_search=true for real examples).
   - High variability: different entities, edge cases, URL patterns.
   - Write a Python validation script to /tmp/validate_agent_{agent_name}.py using the template from generate-update-and-publish.md Phase 4b.
   - Execute via Bash: uv run /tmp/validate_agent_{agent_name}.py
   - Parse JSON output. If >= 80% pass: go to step 5.
   - If < 80%: analyze failures, go to step 1 (update loop via nimble_agents_update, same session_id).
   - Max 2 update cycles total. After 2: stop, report best result.
   - OVERALL TIMEOUT: 15 minutes wall-clock for the entire workflow. If exceeded, stop and report.

5. PUBLISH (on validation pass, or immediately if refine_validate=false and no failures):
   - Call nimble_agents_publish with session_id.

6. REPORT:
   Print structured report:
   AGENT_NAME: {name}
   OPERATION: generate|update
   STATUS: published|failed
   PASS_RATE: {n}%
   REFINE_CYCLES: {count}
   INPUT_SCHEMA: {json}
   OUTPUT_SCHEMA: {json}
   SAMPLE_RESULTS: {json}
   ERRORS: {summary}
""")
```

## Parallel generation

When generating multiple agents (e.g., multi-store comparison), launch background tasks **in parallel** — one per session_id. Each task runs the full closed-loop lifecycle independently. Gather reports when all complete.

## Key rules

- **Generate/update ALWAYS runs as a background agent.** No exceptions.
- **AskUserQuestion happens ONCE in the foreground before launching.** The background agent NEVER asks the user anything.
- **Validation uses a generated SDK script** (`uv run`), NOT individual MCP tool calls.
- **5 consecutive poll errors/issue-messages → auto-trigger update loop.** Hard rule, no exceptions.
- `nimble_agents_generate` is for initial creation only. **All recovery and follow-ups use `nimble_agents_update` — never regenerate.**
- Generate a UUID session_id once; **never create a new one.** Use the same session_id for all updates and recovery.
- **Discovery uses `nimble_web_search`** (MCP, with `deep_search=true`) only. `nimble_agents_list` is already called in the foreground routing step.
- 80% pass rate is the minimum threshold for publishing with validation.
- Max 2 update cycles before escalating to the user.
- **Overall timeout: 15 minutes wall-clock.** Stop and report if exceeded. Use `max_turns=50` on Task launch.
- **Polling: strictly 30s intervals** (`Bash(sleep 30)`), max 10 checks per phase. Never sleep longer.
- Report results regardless of outcome (pass or fail).

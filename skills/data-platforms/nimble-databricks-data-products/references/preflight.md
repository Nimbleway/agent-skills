# Phase 0 — Preflight (exact commands)

Goal: confirm everything works **before** writing anything, then recommend a target and let the
user confirm. Generic Databricks bits defer to the **`databricks-core`** skill.

## 1. Auth + identity
```bash
databricks current-user me -o json | jq '{user: .userName, active}'
```
Capture the username — the default write target is `users.<username>` (dots/`@` become part of the
schema name as-is, e.g. `users.jane_doe`).

## 2. A running SQL warehouse
```bash
databricks warehouses list -o json | jq -r '.[] | "\(.id)\t\(.state)\t\(.name)"'
```
Prefer a warehouse already `RUNNING` (no cold-start wait). If none is running, offer to start one:
`databricks warehouses start <id>` (then poll until RUNNING). Hold the id as `$WH`.

## 3. Integration gate
```bash
databricks functions list nimble_integration tools -o json \
  | jq -r '.[].name' | grep -E '^(nimble_search|nimble_extract|nimble_agent_run|nimble_agent_list|nimble_agent_describe)$'
```
You want all five public wrappers present. If the catalog/schema or functions are missing → **STOP**
and go to `install-nimble-integration.md`. Don't try to install it yourself.

Sanity-ping the live path (optional, ~few s):
```bash
databricks api post /api/2.0/sql/statements --json '{
  "warehouse_id":"'"$WH"'","catalog":"nimble_integration","schema":"tools",
  "statement":"SELECT count(*) n FROM nimble_search(\"hello\", 3)","wait_timeout":"30s"}' \
  | jq '.status.state'
```

## 4. Recommend + confirm the target
Pick a default and **verify writability** rather than assuming — in the POC, `CREATE TABLE` was
denied on a shared schema while `users.<username>` worked.

```bash
# Probe write permission with a throwaway table. ONE statement per call — the Statements API rejects
# multiple ';'-separated statements with a parse error, so CREATE and DROP are two separate calls.
databricks api post /api/2.0/sql/statements --json '{
  "warehouse_id":"'"$WH"'",
  "statement":"CREATE TABLE IF NOT EXISTS users.<username>._nimble_probe (x INT)",
  "wait_timeout":"30s"}' | jq '{state:.status.state, err:.status.error.message}'
databricks api post /api/2.0/sql/statements --json '{
  "warehouse_id":"'"$WH"'",
  "statement":"DROP TABLE IF EXISTS users.<username>._nimble_probe",
  "wait_timeout":"30s"}' | jq -r '.status.state'
```
If the CREATE fails, fall back to another schema the user owns. Then present the recommendation:

> "I'll use **warehouse `<name>` (`$WH`)** and write to **`users.<username>`**. OK, or override?"

Only proceed to ingestion after the user confirms.

## Running SQL throughout this skill
Use the Statements API and read `.result.data_array`:
```bash
databricks api post /api/2.0/sql/statements --json '{
  "warehouse_id":"'"$WH"'","statement":"<SQL>","wait_timeout":"50s"}'
```
`wait_timeout` max is 50s. For longer work (agent calls), submit async (`"wait_timeout":"0s"`) and
poll `GET /api/2.0/sql/statements/<id>` — that's what `scripts/ingest.sh` does.

Two environment rules that bite:
- **One statement per Statements API call.** `"statement"` must contain a single SQL statement;
  `CREATE …; DROP …` in one call is a parse error. Loop in bash to run several.
- **Each Bash tool call is a fresh shell** — env vars (`$WH`, `$DIR`, …) and `cd` do **not** persist
  between calls. Re-set what you need inline in every block, or write paths/ids to a temp file and
  read them back.

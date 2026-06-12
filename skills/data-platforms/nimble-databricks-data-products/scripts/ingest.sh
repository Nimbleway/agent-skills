#!/usr/bin/env bash
# ingest.sh — submit ONE long-running SQL statement asynchronously and poll to completion.
#
# Used for the set-based ingest: a single INSERT that calls nimble_agent_run() over every row of the
# control (queries) table via a correlated LATERAL join (see references/nimble-agents.md). That one
# statement fires all the agent calls (~30-60s each, parallelised by a REPARTITION hint), so it runs
# well past the 50s synchronous wait_timeout — hence async submit + poll.
#
# Usage:
#   bash ingest.sh <warehouse_id> <sql-file>
#
# The SQL file must contain exactly ONE statement. Prints final state + error (if any); exits
# non-zero on failure.
set -euo pipefail

WH="${1:?usage: ingest.sh <warehouse_id> <sql-file>}"
FILE="${2:?usage: ingest.sh <warehouse_id> <sql-file>}"
[ -f "$FILE" ] || { echo "No such file: $FILE"; exit 1; }

sql="$(cat "$FILE")"
id=$(databricks api post /api/2.0/sql/statements \
      --json "$(jq -n --arg w "$WH" --arg s "$sql" '{warehouse_id:$w, statement:$s, wait_timeout:"0s"}')" \
      | jq -r '.statement_id')
echo "Submitted $id — polling (agent calls take ~30-60s each)…"

state=""; resp=""
for _ in $(seq 1 120); do          # up to ~20 min
  resp=$(databricks api get "/api/2.0/sql/statements/$id")
  state=$(echo "$resp" | jq -r '.status.state')
  case "$state" in
    PENDING|RUNNING) sleep 10 ;;
    *) break ;;
  esac
done

err=$(echo "$resp" | jq -r '.status.error.message // ""')
echo "state=$state ${err:+— $err}"
[ "$state" = "SUCCEEDED" ] || { echo "Ingest failed."; exit 1; }
echo "Ingest complete. Now reconcile results against the control table (see nimble-agents.md §6)."

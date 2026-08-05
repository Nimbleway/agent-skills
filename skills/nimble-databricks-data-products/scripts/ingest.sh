#!/usr/bin/env bash
# ingest.sh — submit ONE long-running SQL statement asynchronously and poll to completion.
#
# Used for the set-based ingest: a single INSERT that calls nimble_agent_run() over every row of the
# control (queries) table via a correlated LATERAL join (see references/nimble-agents.md). That one
# statement fires all the agent calls (~30-60s each, parallelised by a REPARTITION hint), so it runs
# well past the 50s synchronous wait_timeout — hence async submit + poll.
#
# Usage:
#   bash ingest.sh <warehouse_id> <sql-file> [max_poll_minutes]
#
# The SQL file must contain exactly ONE statement. Prints final state + error (if any); exits
# non-zero on failure. max_poll_minutes defaults to 60 — raise it for very large ingests.
set -euo pipefail

WH="${1:?usage: ingest.sh <warehouse_id> <sql-file> [max_poll_minutes]}"
FILE="${2:?usage: ingest.sh <warehouse_id> <sql-file> [max_poll_minutes]}"
MAX_MIN="${3:-60}"
[ -f "$FILE" ] || { echo "No such file: $FILE"; exit 1; }

# Build the request body in a temp file and pass it with `--json @file`, not as an argv string —
# a large INSERT can exceed the OS argv size limit.
body=$(mktemp); trap 'rm -f "$body"' EXIT
jq -n --arg w "$WH" --rawfile s "$FILE" '{warehouse_id:$w, statement:$s, wait_timeout:"0s"}' > "$body"

submit=$(databricks api post /api/2.0/sql/statements --json "@$body")
id=$(printf '%s' "$submit" | jq -r '.statement_id // empty')
if [ -z "$id" ]; then
  echo "Submit failed — no statement_id returned:"; printf '%s\n' "$submit"; exit 1
fi
echo "Submitted $id — polling (agent calls take ~30-60s each; cap ${MAX_MIN}m)…"

state=""; resp=""; iters=$(( MAX_MIN * 6 ))   # one poll per 10s
for _ in $(seq 1 "$iters"); do
  resp=$(databricks api get "/api/2.0/sql/statements/$id")
  state=$(echo "$resp" | jq -r '.status.state')
  case "$state" in
    PENDING|RUNNING) sleep 10 ;;
    *) break ;;
  esac
done
if [ "$state" = "PENDING" ] || [ "$state" = "RUNNING" ]; then
  echo "Still $state after ${MAX_MIN}m. Statement $id keeps running server-side — re-poll with: databricks api get /api/2.0/sql/statements/$id"
  exit 1
fi

err=$(echo "$resp" | jq -r '.status.error.message // ""')
echo "state=$state ${err:+— $err}"
[ "$state" = "SUCCEEDED" ] || { echo "Ingest failed."; exit 1; }
echo "Ingest complete. Now reconcile results against the control table (see nimble-agents.md §6)."

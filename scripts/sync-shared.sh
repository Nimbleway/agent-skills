#!/usr/bin/env bash
# Copies _shared/ reference files into each skill's references/ directory.
# Run from the repo root after any change to _shared/.
#
# Usage: ./scripts/sync-shared.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SHARED_DIR="$REPO_ROOT/_shared"

if [ ! -d "$SHARED_DIR" ]; then
  echo "Error: _shared/ directory not found at $SHARED_DIR"
  exit 1
fi

synced=0

for refs_dir in "$REPO_ROOT"/skills/*/references; do
  [ -d "$refs_dir" ] || continue

  skill_dir="$(dirname "$refs_dir")"
  skill_name="$(basename "$skill_dir")"

  # Skip skills that manage their own references (core data skill + SQL-native
  # Databricks skill, which is intentionally CLI-free and doesn't use these).
  case "$skill_name" in
    nimble-web-expert|nimble-databricks-data-products) continue ;;
  esac

  # Only sync skills that have a SKILL.md (i.e., actually implemented)
  if [ ! -f "$skill_dir/SKILL.md" ]; then
    echo "Skipping skills/$skill_name/ (no SKILL.md yet)"
    continue
  fi

  cp "$SHARED_DIR"/*.md "$refs_dir/"
  synced=$((synced + 1))
  echo "Synced _shared/ -> skills/$skill_name/references/"
done

if [ "$synced" -eq 0 ]; then
  echo "No skill references/ directories found to sync."
else
  echo "Done. Synced $synced skill(s)."
fi

#!/usr/bin/env bash
# Guards the Extraction Template vs Web Search Agent naming in skill docs.
#
# - A doc that says "WSA" but only runs `extract:templates` is describing Extraction
#   Templates under the wrong name.
# - The singular `nimble agent` CLI group is retired, and "pre-built agent" is its old
#   name for an Extraction Template.
#
# Usage: bash scripts/check-terminology.sh

set -euo pipefail
cd "$(dirname "$0")/.."

fail=0

while IFS= read -r f; do
  if grep -qE '\bWSAs?\b' "$f" && grep -q 'extract:templates' "$f" &&
    ! grep -qE 'nimble agents|agents:runs|nimble_agents_' "$f"; then
    echo "::error file=$f::Says WSA but only runs extract:templates. Call these Extraction Templates."
    fail=1
  fi
done < <(find skills _shared -name '*.md')

if grep -rniE 'nimble agent |pre-built agent' skills _shared; then
  echo "::error::Retired wording above. Use extract:templates for Extraction Templates or nimble agents for Web Search Agents."
  fail=1
fi

[ "$fail" -eq 0 ] && echo "Terminology OK"
exit "$fail"

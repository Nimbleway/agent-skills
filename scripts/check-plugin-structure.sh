#!/usr/bin/env bash
# Assert the skills/ tree satisfies every platform's packaging rules.
#
# Three marketplaces disagree about how they find skills, and the strictest wins:
#
#   - OpenAI/Codex ingestion rejects a nested skill outright (skill_manifest_nested:
#     "Each skill directory must be an immediate child of skills/") and caps each
#     skill's description at 1024 characters (skill_description_too_long). Errors
#     block submission.
#   - xAI indexes only direct children of skills/, so a nested skill is silently
#     absent from the plugin index with no error at all.
#   - Runtime discovery in Claude Code and Codex is recursive, so a violation of
#     either rule still works locally. That is exactly why it needs a CI gate:
#     local behavior proves nothing about whether the catalog will accept the tree.
#
# A stray SKILL.md under references/ is the specific regression this guards. Codex
# treats a .codex-plugin/plugin.json as a Legacy-format manifest and scans for
# SKILL.md recursively, so a reference document named SKILL.md registers as a real
# skill in the model-visible catalog. Reference documents are named reference.md.
#
# Usage:
#   bash scripts/check-plugin-structure.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

SOURCE_OF_TRUTH=".claude-plugin/plugin.json"
DESCRIPTION_MAX=1024   # OpenAI skill_description_too_long
IDENTITY_MAX=64        # OpenAI skill_identity_too_long, on "<plugin>:<skill>"

fail() { echo "ERROR: $*" >&2; exit 1; }

[ -d skills ] || fail "missing skills/ directory"
[ -f "$SOURCE_OF_TRUTH" ] || fail "missing $SOURCE_OF_TRUTH"

# Read the plugin name with a real JSON parser, not grep | head -1.
#
# The manifest holds two "name" keys — the top-level plugin name and author.name — and
# JSON member order carries no meaning. "First match wins" is therefore correct only by
# accident of the current formatting: emit author first, which is a semantically identical
# manifest, and the identity prefix becomes the author's name. With a long author name
# that overshoots IDENTITY_MAX and fails CI on a perfectly valid skills tree.
#
# python3 is already required by scripts/check-plugin-manifests.py and
# scripts/run-routing-eval.py, so this adds no dependency. jq is deliberately avoided —
# nothing in this repo declares it.
PLUGIN_NAME="$(python3 -c '
import json, sys
try:
    manifest = json.load(open(sys.argv[1], encoding="utf-8"))
except (OSError, ValueError) as exc:
    sys.exit(f"{sys.argv[1]}: {exc}")
if not isinstance(manifest, dict):
    sys.exit(f"{sys.argv[1]}: top level must be a JSON object")
name = manifest.get("name")
if not isinstance(name, str) or not name.strip():
    sys.exit(f"{sys.argv[1]}: top-level \"name\" must be a non-empty string")
print(name)
' "$SOURCE_OF_TRUTH")" || fail "could not read a plugin name from $SOURCE_OF_TRUTH"

echo "Plugin: $PLUGIN_NAME"
echo

problems=0
note() { echo "  $*"; problems=$((problems + 1)); }

# ---------------------------------------------------------------------------
# 1. Every SKILL.md sits at exactly skills/<skill>/SKILL.md.
#
# Checking the whole tree rather than the glob is the point: a glob would only
# confirm the skills it already matched, and say nothing about the extra files
# that break the recursive consumers.
# ---------------------------------------------------------------------------
echo "Skill placement:"
while IFS= read -r f; do
  [ -n "$f" ] || continue
  rel="${f#skills/}"
  case "$rel" in
    */*/*) note "NESTED   $f — must be skills/<skill>/SKILL.md (skill_manifest_nested)" ;;
    */SKILL.md) ;;  # correct depth
    *) note "STRAY    $f — a file directly under skills/ is not imported as a skill" ;;
  esac
done <<EOF
$(find skills -name SKILL.md | sort)
EOF
[ "$problems" -eq 0 ] && echo "  ok       every SKILL.md is an immediate child of skills/"

# ---------------------------------------------------------------------------
# 2. Reference documents must not be named SKILL.md.
# ---------------------------------------------------------------------------
echo
echo "Reference documents:"
strays="$(find skills -path '*/references/*' -name SKILL.md | sort)"
if [ -n "$strays" ]; then
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    note "PHANTOM  $f — rename to reference.md; a SKILL.md here registers as a skill"
  done <<EOF
$strays
EOF
else
  echo "  ok       no SKILL.md under any references/ directory"
fi

# ---------------------------------------------------------------------------
# 3. Per-skill frontmatter: name matches directory, description within limits.
# ---------------------------------------------------------------------------
echo
echo "Skill frontmatter:"
count=0
for dir in skills/*/; do
  skill="$(basename "$dir")"
  manifest="${dir}SKILL.md"   # $dir already carries the trailing slash

  case "$skill" in
    .*) note "HIDDEN   $skill — skill directory names cannot begin with '.'" ;;
  esac

  [ -f "$manifest" ] || { note "MISSING  $manifest — every skill directory needs a SKILL.md"; continue; }
  count=$((count + 1))

  # Frontmatter must open on line 1 and close, or the skill is unreadable to the
  # ingestion validator regardless of what the body says.
  if [ "$(head -1 "$manifest")" != "---" ]; then
    note "NOFM     $manifest — must start with YAML frontmatter"
    continue
  fi
  if ! awk 'NR>1 && /^---$/ {found=1; exit} END {exit !found}' "$manifest"; then
    note "OPENFM   $manifest — YAML frontmatter is never closed"
    continue
  fi

  name="$(awk '
    NR == 1 && $0 == "---" { inside = 1; next }
    inside && $0 == "---"   { exit }
    inside && /^name:[[:space:]]*/ {
      line = $0; sub(/^name:[[:space:]]*/, "", line); gsub(/"/, "", line)
      print line; exit
    }
  ' "$manifest")"

  [ -n "$name" ] || note "NONAME   $manifest — frontmatter has no name key"
  [ -n "$name" ] && [ "$name" != "$skill" ] && \
    note "NAME     $manifest — frontmatter name '$name' != directory '$skill'"

  identity="$PLUGIN_NAME:${name:-$skill}"
  [ "${#identity}" -gt "$IDENTITY_MAX" ] && \
    note "IDENT    $manifest — '$identity' is ${#identity} chars, limit $IDENTITY_MAX"

  # Description length, measured on the frontmatter value with block-scalar
  # indentation stripped — that is the text the platforms count.
  desc_len="$(awk '
    NR == 1 && $0 == "---" { inside = 1; next }
    inside && $0 == "---"   { exit }
    inside && /^description:/ {
      collecting = 1
      line = $0; sub(/^description:[[:space:]]*\|?[[:space:]]*/, "", line)
      if (line != "") text = line
      next
    }
    collecting && /^[^[:space:]]/ { collecting = 0 }
    collecting {
      line = $0; sub(/^[[:space:]]+/, "", line)
      text = (text == "" ? line : text "\n" line)
    }
    END { print length(text) }
  ' "$manifest")"

  [ "$desc_len" -eq 0 ] && note "NODESC   $manifest — frontmatter has no description"
  [ "$desc_len" -gt "$DESCRIPTION_MAX" ] && \
    note "DESCLEN  $manifest — description is $desc_len chars, limit $DESCRIPTION_MAX"
done
echo "  checked $count skill(s)"

# ---------------------------------------------------------------------------
# 4. Every skill enumerated in marketplace.json must exist, and vice versa.
#
# marketplace.json lists individual skill paths precisely so recursive consumers
# cannot pick up reference documents. That only holds while the list is complete.
# ---------------------------------------------------------------------------
MARKETPLACE=".claude-plugin/marketplace.json"
echo
echo "Marketplace enumeration:"
if [ -f "$MARKETPLACE" ]; then
  listed="$(grep -o '"\./skills/[^"]*"' "$MARKETPLACE" | tr -d '"' | sed 's|^\./skills/||' | sort -u)"
  actual="$(find skills -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | sort)"

  missing="$(comm -13 <(printf '%s\n' "$listed") <(printf '%s\n' "$actual"))"
  extra="$(comm -23 <(printf '%s\n' "$listed") <(printf '%s\n' "$actual"))"

  while IFS= read -r s; do
    [ -n "$s" ] && note "UNLISTED $s — exists in skills/ but absent from $MARKETPLACE"
  done <<EOF
$missing
EOF
  while IFS= read -r s; do
    [ -n "$s" ] && note "GHOST    $s — listed in $MARKETPLACE but not in skills/"
  done <<EOF
$extra
EOF
  [ -z "$missing" ] && [ -z "$extra" ] && \
    echo "  ok       all $(printf '%s\n' "$actual" | wc -l | tr -d ' ') skill(s) enumerated"
else
  note "MISSING  $MARKETPLACE"
fi

echo
if [ "$problems" -gt 0 ]; then
  fail "$problems structural problem(s) found.
       Every skill directory must be an immediate child of skills/ with a SKILL.md whose
       frontmatter name matches the directory. Reference documents are named reference.md."
fi

echo "Plugin structure is valid for Claude, Cursor, Codex, and xAI packaging."

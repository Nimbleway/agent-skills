#!/usr/bin/env bash
# Verify version consistency and create an annotated release tag.
#
# The plugin version is duplicated across every manifest, the README badge, and
# each skill's frontmatter. This script treats .claude-plugin/plugin.json as the
# source of truth and asserts every other reference agrees, then tags the release
# using that version's CHANGELOG section as the tag message.
#
# Usage:
#   bash scripts/tag-release.sh --check     # verify consistency only (used by CI)
#   bash scripts/tag-release.sh             # verify, then create the annotated tag
#   bash scripts/tag-release.sh --help
#
# The tag is never pushed automatically — the push command is printed instead.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

SOURCE_OF_TRUTH=".claude-plugin/plugin.json"
CHANGELOG="CHANGELOG.md"
RELEASE_BRANCH="main"

CHECK_ONLY=0
case "${1:-}" in
  --check) CHECK_ONLY=1 ;;
  --help|-h)
    sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'
    exit 0
    ;;
  "") ;;
  *) echo "Unknown argument: $1 (try --help)" >&2; exit 2 ;;
esac

fail() { echo "ERROR: $*" >&2; exit 1; }

# ---------------------------------------------------------------------------
# Resolve the expected version from the source of truth.
# ---------------------------------------------------------------------------
[ -f "$SOURCE_OF_TRUTH" ] || fail "missing $SOURCE_OF_TRUTH"

VERSION="$(grep -o '"version": *"[^"]*"' "$SOURCE_OF_TRUTH" | head -1 | sed 's/.*"\([0-9][^"]*\)"/\1/')"
[ -n "$VERSION" ] || fail "could not read a version from $SOURCE_OF_TRUTH"

# A regex, not a `case` glob: in shell patterns `*` matches any characters, so
# [0-9]*.[0-9]*.[0-9]* would accept 1.2.3-beta, 1x.2y.3z, 10.20.30extra and 1.2.3.4 —
# a malformed version could reach a tag name while the error claimed strict semver.
if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  fail "version '$VERSION' in $SOURCE_OF_TRUTH is not strict semver (X.Y.Z)"
fi

echo "Expected version: $VERSION  (source: $SOURCE_OF_TRUTH)"
echo

# ---------------------------------------------------------------------------
# Collect every version reference. Each check is context-anchored: a bare search
# for the version string also matches CHANGELOG history and Nimble CLI version
# references such as "CLI 1.1.0+", which must never be rewritten.
# ---------------------------------------------------------------------------
mismatches=0
checked=0

# Reports one reference. $1=path, $2=human label, $3=found value ("" when absent)
report() {
  local path="$1" label="$2" found="$3"
  checked=$((checked + 1))
  if [ -z "$found" ]; then
    echo "  MISSING  $path — no $label found"
    mismatches=$((mismatches + 1))
  elif [ "$found" != "$VERSION" ]; then
    echo "  MISMATCH $path — $label is '$found', expected '$VERSION'"
    mismatches=$((mismatches + 1))
  else
    echo "  ok       $path"
  fi
}

echo "JSON manifests:"
for f in .claude-plugin/plugin.json .cursor-plugin/plugin.json .claude-plugin/marketplace.json \
         .codex-plugin/plugin.json; do
  if [ ! -f "$f" ]; then
    echo "  MISSING  $f — file not found"
    mismatches=$((mismatches + 1)); checked=$((checked + 1))
    continue
  fi
  found="$(grep -o '"version": *"[^"]*"' "$f" | head -1 | sed 's/.*"\([0-9][^"]*\)"/\1/')"
  report "$f" '"version"' "$found"
done

echo
echo "README badge:"
badge="$(grep -o 'version-[0-9][0-9.]*-green' README.md 2>/dev/null | head -1 | sed 's/version-\(.*\)-green/\1/')"
report "README.md" "version badge" "$badge"

echo
echo "Skill frontmatter:"
# Layout-agnostic: matches skills/<skill>/SKILL.md and skills/<vertical>/<skill>/SKILL.md.
# Reference SKILL.md files under references/ are documentation, not skills, and are excluded.
skill_files="$(find skills -name SKILL.md -not -path '*/references/*' 2>/dev/null | sort)"
[ -n "$skill_files" ] || fail "found no skill SKILL.md files under skills/"

while IFS= read -r f; do
  [ -n "$f" ] || continue
  # Only look inside the frontmatter block, and only at an indented `version:` key.
  found="$(awk '
    NR == 1 && $0 == "---" { inside = 1; next }
    inside && $0 == "---"   { exit }
    inside && /^[[:space:]]+version:[[:space:]]*"?[0-9]/ {
      line = $0
      sub(/^[[:space:]]+version:[[:space:]]*/, "", line)
      gsub(/"/, "", line)
      print line
      exit
    }
  ' "$f")"
  report "$f" "metadata.version" "$found"
done <<EOF
$skill_files
EOF

echo
echo "Checked $checked reference(s)."

if [ "$mismatches" -gt 0 ]; then
  echo
  fail "$mismatches version reference(s) disagree with $SOURCE_OF_TRUTH ($VERSION).
       Bump every reference in one pass. Do not use a bare search-and-replace on the
       version string — that also rewrites CHANGELOG history and CLI version references."
fi

echo "All version references agree on $VERSION."

# ---------------------------------------------------------------------------
# CHANGELOG section — becomes the annotated tag message.
# ---------------------------------------------------------------------------
[ -f "$CHANGELOG" ] || fail "missing $CHANGELOG"

notes="$(awk -v v="$VERSION" '
  $0 ~ "^## \\[" v "\\]" { found = 1; print; next }
  found && /^## \[/       { exit }
  found                   { print }
' "$CHANGELOG")"

if [ -z "$notes" ]; then
  fail "no '## [$VERSION]' section in $CHANGELOG.
       Add the release notes before tagging — the tag message is taken from there."
fi
echo "Found CHANGELOG section for $VERSION ($(printf '%s\n' "$notes" | wc -l | tr -d ' ') lines)."

if [ "$CHECK_ONLY" -eq 1 ]; then
  echo
  echo "--check passed."
  exit 0
fi

# ---------------------------------------------------------------------------
# Tagging guards. Everything below only runs without --check.
# ---------------------------------------------------------------------------
TAG="v$VERSION"
echo

branch="$(git rev-parse --abbrev-ref HEAD)"
[ "$branch" = "$RELEASE_BRANCH" ] || fail "on branch '$branch' — release tags are cut from '$RELEASE_BRANCH' only."

[ -z "$(git status --porcelain)" ] || fail "worktree is not clean — commit or stash first, so the tag points at a reproducible tree."

if git rev-parse -q --verify "refs/tags/$TAG" >/dev/null; then
  fail "tag $TAG already exists locally (at $(git rev-parse --short "$TAG")). Delete it deliberately if you must re-cut it."
fi

if git ls-remote --exit-code --tags origin "refs/tags/$TAG" >/dev/null 2>&1; then
  fail "tag $TAG already exists on origin. Never move a published tag — cut a new version instead."
fi

if ! git merge-base --is-ancestor HEAD "origin/$RELEASE_BRANCH" 2>/dev/null; then
  echo "WARNING: HEAD is not an ancestor of origin/$RELEASE_BRANCH — the tag may point at an unpushed commit."
fi

# --cleanup=verbatim is required: git's default tag-message cleanup strips every line
# starting with '#', which would silently delete the '## [X.Y.Z]' heading and the
# '### Added' / '### Changed' / '### Removed' subheadings, flattening the notes into an
# undifferentiated bullet list.
git tag -a --cleanup=verbatim "$TAG" -m "$notes"

echo "Created annotated tag $TAG at $(git rev-parse --short HEAD)."
echo
echo "Review it, then push deliberately:"
echo
echo "    git show $TAG"
echo "    git push origin $TAG"
echo
echo "Tags are not pushed automatically — a published tag should never be moved."

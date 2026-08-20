---
name: codebase-web-research
description: |
  Pairs repository inspection with live web research: is this dependency
  version current, does an API call match the vendor's latest contract, is
  there a security advisory against a pinned package, what changed in a
  release we're adopting, what does a migration actually require.

  USE FOR: dependency/package currency checks against pinned versions; API
  calls vs current docs (deprecated params, renamed endpoints); CVE/advisory
  lookups for pinned packages; release-note review; upgrade/migration
  planning from vendor docs against actual repo usage.

  Do NOT use for general web search unrelated to this repo's code (use
  nimble-web-expert directly) or business/competitor research (use the
  business-research skills). Output always anchors to a specific file,
  dependency, or call site in the current repository.

  Requires the Nimble CLI (nimble search, nimble extract) for live web data.
allowed-tools:
  - Bash(nimble:*)
  - Bash(cat:*)
  - Bash(head:*)
  - Bash(grep:*)
  - Bash(git:*)
  - Bash(mkdir:*)
  - Bash(python3:*)
  - Read
  - Write
  - Glob
  - Grep
metadata:
  author: Nimbleway
  version: 1.7.0
  category: developer-tools
---

# Codebase Web Research

## Core principle

Every claim this skill makes must trace to two things at once: a location in
this repository (file, dependency manifest, or call site) and a live web
source (vendor doc, changelog, advisory) with a date. Neither alone is
sufficient — "the code does X" without checking whether X is still current is
stale, and "the vendor says Y" without checking whether this repo actually
does Y is unanchored.

Read `references/nimble-playbook.md` before running any Nimble command — it
covers the transport preflight, parallel-call pattern, and failure handling
this skill assumes rather than restates.

## Phase 1 — Anchor in the repository

Identify the specific target before searching the web:

- **Dependency check**: read the manifest (`package.json`, `requirements.txt`,
  `Cargo.toml`, `go.mod`, etc.) for the pinned name and version.
- **API-call check**: `grep` the call site(s) for the endpoint, SDK method, or
  CLI flags in use, plus any version string in a nearby import or client
  constructor.
- **Migration/upgrade planning**: read the current usage pattern across the
  repo (`Grep` for the API surface being touched) so the web research in
  Phase 2 is scoped to what this repo actually calls, not the vendor's full
  surface area.

Skip Phase 2 entirely if the target can't be pinned to a specific file or
manifest entry — ask the user which dependency or call site they mean rather
than researching broadly and guessing at relevance.

## Phase 2 — Live web research

Run Nimble in parallel across every distinct question from Phase 1 (multiple
`Bash` calls in one response, per the playbook's parallel-call pattern — never
one-by-one). Prefer, in order:

1. **Release notes / changelog** for the exact pinned version → latest:
   `nimble search --query "<package> changelog <pinned-version>..<latest>" --focus coding`
   or `nimble extract --url "<known changelog URL>" --format markdown` when the
   URL is already known from the manifest or a prior search.
2. **Current API docs** for the specific method/endpoint the repo calls, not
   the whole product — search or extract the docs page for that one call.
3. **Security advisories** — search for `"<package>" CVE OR advisory
   <pinned-version>`, and check whether the pinned version falls in an
   affected range if a CVE is found.
4. **Migration guides** — when planning an upgrade, search for the vendor's
   own migration/upgrade guide before drafting a plan from general knowledge.

Save extracted pages under `.nimble/` per the playbook rather than returning
large pages into context; work from the saved file.

## Phase 3 — Report

Structure the answer as: **repo location** → **current state per the web
source (with date and URL)** → **gap or match** → **what this means for the
repo** (upgrade needed, call site needs a param rename, no action, etc.).
Every "changed" or "current" claim carries its source URL and, when the source
provides one, a publish or updated date. Preserve trust metadata and stable
attribution from the Nimble response instead of flattening all sources into an
undifferentiated summary.

If Nimble returns a structured failure (rate limit, not-found, auth), report
it as a failure to the user — do not silently fall back to training knowledge
and present it as current.

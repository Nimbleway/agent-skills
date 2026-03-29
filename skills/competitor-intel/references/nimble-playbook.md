# Nimble Playbook

How to run Nimble CLI commands in Claude Code. Read this before executing any commands.

---

## Claude Code Execution Rules

- **No shell state persistence.** Variables set in one Bash call are gone in the next.
  Inline all values (dates, paths, names) directly into every command.
- **No `&` + `wait` parallelism.** It breaks in Claude Code. Instead, make **multiple
  Bash tool calls in a single response** — they run in parallel natively.
- **Search returns JSON** — `--output-format` doesn't change this. With `--search-depth
  lite`, the JSON is small (title, description, URL per result). Parse it directly.
- **Extract returns JSON with `data.markdown`** — use `--format markdown` to get clean
  content in the `data.markdown` field.

## Preflight Pattern

Every skill starts with these simultaneous Bash calls:

- `python3 -c "from datetime import datetime, timedelta; print((datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d'))"` (14 days ago)
- `date +%Y-%m-%d` (today)
- `nimble --version && echo "NIMBLE_API_KEY=${NIMBLE_API_KEY:+set}"`
- `cat ~/.nimble/business-profile.json 2>/dev/null`

From the `nimble --version` output, check:
- **CLI missing** (command not found) → install it interactively
- **CLI outdated** (version < 0.8.0) → upgrade it
- **API key unset** → guide setup

See `references/profile-and-onboarding.md` for the full prerequisite checks with
install/upgrade flows. Don't skip version validation — outdated CLI versions may be
missing flags or features that skills depend on.

## Smart Date Windowing

For any skill using `--start-date` based on previous runs:
- **First run:** 14 days ago → **full mode**
- **Last run < 3 days ago:** use 7 days ago (too narrow = empty results) → **quick refresh**
- **Last run 3-14 days ago:** use the last run date → **quick refresh**
- **Last run > 14 days ago:** 14 days ago → **full mode**
- **Same-day repeat:** if `last_runs.{skill-name}` is today, check if a report already
  exists at `~/.nimble/memory/reports/{skill-name}-[today].md`. If it does, **ask the
  user before re-running**: "Already ran today. Run again for fresh data?" Don't silently
  re-run — it wastes API credits and produces near-identical output.

---

## Search

```bash
# Standard search (always use --search-depth lite for discovery)
nimble search --query "company name news" --max-results 10 --search-depth lite

# News-focused search
nimble search --query "company name" --focus news --max-results 10 --search-depth lite

# Date-filtered search (inline the date — don't use variables)
nimble search --query "company funding" --focus news --start-date "2026-03-11" --max-results 10 --search-depth lite

# Social signals from X/LinkedIn
nimble search --query "Company" --include-domain '["x.com", "linkedin.com"]' --max-results 10 --search-depth lite --time-range week

# Deep search (full page content — only for comprehensive analysis, costs more)
nimble search --query "company name" --search-depth deep --max-results 5

# Fast search (enterprise only — do not use by default)
# nimble search --query "company name" --search-depth fast --max-results 10
```

**Key flags:**
- `--query` — search query string (required)
- `--focus` — `general`, `news`, `shopping`, `social`, `coding`, `academic`.
  **`social`** searches social platform people indices directly (LinkedIn, X) — best
  for finding specific people. Not available on all plans; if it errors, fall back to
  `--include-domain '["linkedin.com"]'`.
- `--max-results` — max results to return
- `--start-date` / `--end-date` — date filters (YYYY-MM-DD)
- `--search-depth` — `lite` (cheapest, 1 credit), `deep` (1 + 1/page), `fast` (enterprise only)
- `--include-domain` — JSON array of domains, e.g., `'["x.com", "linkedin.com"]'`
- `--time-range` — e.g., `week`
- `--country` — geo-targeted results (e.g., "US", "IL")
- `--include-answer` — LLM-powered answer summary

**Date range strategy:**
- First run: 14 days ago
- Subsequent runs: `last_runs` timestamp from business profile
- If < 3 results: retry without `--start-date`

## Extract

```bash
# Extract article content as markdown (recommended)
nimble extract --url "https://example.com/article" --format markdown

# Extract with JavaScript rendering (for dynamic/SPA pages)
nimble extract --url "https://example.com/spa" --render --format markdown
```

Response is JSON with `data.markdown` containing clean content.

**Key flags:**
- `--url` — target URL (required)
- `--format` — `markdown` (recommended), `simplified_html`, `plain_text`
- `--render` — render JavaScript using a browser

**Extraction fallback** (if `data.markdown` is mostly JavaScript/boilerplate):
1. Retry with `--render --format markdown`
2. Search for the same article title on a different domain
3. Skip — don't waste time on broken pages

## Map

```bash
nimble map --url "https://example.com/blog" --limit 20
```

## Parallel Execution

Make **multiple Bash tool calls in a single response**. Claude Code runs them in
parallel automatically:

- Call 1: `nimble search --query "CompanyA news" --max-results 5 --search-depth lite`
- Call 2: `nimble search --query "CompanyB news" --max-results 5 --search-depth lite`
- Call 3: `nimble search --query "CompanyC news" --max-results 5 --search-depth lite`

## Sub-Agent Spawning

When using the Agent tool for parallel research:

- **Always `mode: "bypassPermissions"`** — sub-agents don't inherit Bash permissions.
- **Batch max 4 agents.** More risk hitting rate limits. For 5+, batch in groups.
- **Tell agents to use Bash** — explicitly say "Use the Bash tool to execute nimble
  commands." Some agents try WebSearch instead.
- **Fallback on failure** — if any agent returns without results, run those searches
  directly from the main context. Don't leave gaps.

## Communication Style

Inform the user at **phase transitions only** with concrete numbers:
- "Researching **Acme Corp** + **5 competitors** since Mar 12..."
- "Found **12 new signals**. Pulling top 4 articles..."
- "All data collected. Building your briefing..."

Don't narrate individual tool calls.

## Rate Limits & Common Errors

- **Rate limit:** 10 req/sec per API key
- **Retry on 429:** Reduce simultaneous calls
- **Timeout:** 30 seconds per request

| Error | Cause | Fix |
|-------|-------|-----|
| `NIMBLE_API_KEY not set` | Missing API key | See `profile-and-onboarding.md` |
| `401 Unauthorized` | Expired key | Regenerate at app.nimbleway.com |
| `429 Too Many Requests` | Rate limit | Fewer simultaneous calls |
| `timeout` | Slow response | Retry once, then skip |
| `empty results` | No matches | Remove `--start-date`, broaden query |

## Signal Date Validation

High-quality intelligence requires distinguishing between when a **page was published**
and when the **underlying event occurred**. This matters because:

- Syndicated or republished content may carry a different publication date than the
  original source
- Secondary coverage (regulatory filings, recap articles, industry roundups) can
  report on events that happened weeks or months earlier

### Article Date vs Event Date

Every signal has two dates:

| | What it is |
|---|---|
| **Article date** | When the page was published |
| **Event date** | When the underlying event actually happened |

A signal is "new" only if its **event date** falls within the freshness window.

### Event Date Extraction Rules

Sub-agents must determine the event date from content:

1. **Explicit past reference** — "launched in Q3", "appointed last October" → event
   date is in the past, regardless of the article date
2. **Temporal language** — "last quarter", "months ago", "earlier this year" → resolve
   relative to the article date
3. **Present tense announcement** — "today announces", "is launching" → event date ≈
   article date
4. **Dateline** — "NEW YORK, March 15 —" → event date = that dateline date
5. **If ambiguous** — extract the source URL and check the on-page date

### Source Type Hierarchy

When the same event appears from multiple sources, prefer those closest to the event:

1. **Primary** — the company's own domain, official press release, regulatory filing
2. **Wire service** — AP, Reuters, Bloomberg
3. **Major outlet** — original reporting with bylines
4. **Derivative** — syndicated copies, aggregator sites, recap articles, or content
   that attributes its information to another source

If the only source for a signal is derivative, corroborate against a primary or major
source before reporting.

### Freshness Classification

After determining the event date, classify each signal:

| Classification | Meaning | Action |
|---|---|---|
| **NEW** | Event date within freshness window, not in memory | Include in report |
| **UPDATED** | Known event with genuinely new information | Include as update |
| **STALE** | Old event covered by a recent article | **DROP — do not include** |
| **UNCERTAIN** | Can't determine event date from snippet alone | Extract URL to verify; if still uncertain after extraction, **DROP** |

**Hard rule:** Only signals classified as **NEW** or **UPDATED** may appear in reports.
STALE and UNCERTAIN signals must be dropped entirely — not downgraded, not footnoted,
not included as "background context." If a signal can't be verified as genuinely recent,
it doesn't exist as far as the report is concerned.

### `--start-date` Best Practices

`--start-date` is a useful filter for reducing noise, but always validate event dates
from the content itself:
- For news queries (`--focus news`), consider running a parallel undated query to
  surface original sources alongside recent coverage
- The existing fallback ("If < 3 results, retry without `--start-date`") remains useful

### Verification Budget

Not every signal needs full verification — budget extract calls by priority:

| Priority | Examples | Verification |
|---|---|---|
| **P1** (high impact) | Funding, M&A, leadership changes | Always extract + corroborate (see below) |
| **P2** (medium impact) | Product launches, partnerships, major hires | Extract if date is UNCERTAIN or source is derivative |
| **P3** (low impact) | Blog posts, minor hires, event appearances | Trust if date looks plausible; drop if obviously stale |

Skills define their own P1/P2/P3 signal types in their SKILL.md. The verification
budget above applies universally regardless of which signals a skill classifies at
each level.

### P1 Corroboration (Mandatory)

Any P1 signal sourced from derivative or aggregator sites **must** be corroborated
before it can appear in a report. This is a hard gate, not a suggestion.

For each P1 signal that needs corroboration:

```bash
nimble search --query "[Company] [event summary]" --max-results 5 --search-depth lite
```

Look for the **primary source** (company blog, press release, official filing, regulatory
document). Check the primary source's date:

- **Primary source dates the event within the freshness window** → signal is NEW, include it
- **Primary source dates the event outside the freshness window** → reclassify as STALE, drop
- **No primary source found** → reclassify as UNCERTAIN, drop

Do not report P1 signals that fail corroboration. It's better to miss a real signal than
to report a stale one as new — trust is the product.

---

## Query Construction Tips

- **Be specific:** "Acme Corp product launch 2026" > "Acme Corp"
- **Use `--include-domain '["domain"]'`** for companies with generic names
- **Fallback on empty:** If < 3 results, retry without `--start-date`
- **Combine focus modes:** news + general in parallel for broader coverage
- **Try variations:** "CompanyName" → "Company Name" → domain

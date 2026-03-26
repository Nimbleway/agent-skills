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

If CLI missing or API key unset → see "Onboarding" section in `references/profile-and-onboarding.md`.

## Smart Date Windowing

For any skill using `--start-date` based on previous runs:
- **First run:** 14 days ago
- **Last run < 3 days ago:** use 7 days ago (too narrow = empty results)
- **Last run 3-14 days ago:** use the last run date
- **Last run > 14 days ago:** 14 days ago

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

## Query Construction Tips

- **Be specific:** "Acme Corp product launch 2026" > "Acme Corp"
- **Use `site:domain`** for companies with generic names
- **Fallback on empty:** If < 3 results, retry without `--start-date`
- **Combine focus modes:** news + general in parallel for broader coverage
- **Try variations:** "CompanyName" → "Company Name" → domain

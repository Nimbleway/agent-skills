
# GitHub SEO Audit

Audits GitHub repository discoverability across GitHub search, Google, and AI coding assistants.


---

## Instructions

### Step 0: Preflight

Run the preflight pattern from `references/nimble-playbook.md` (5 simultaneous Bash
calls: date calc, today, CLI check, profile load, index.md load).

Additionally, verify `gh` CLI is installed and authenticated:

```bash
gh auth status
```

From the results:
- CLI missing or API key unset -> `references/profile-and-onboarding.md`, stop
- `gh` not installed -> warn: "GitHub CLI (`gh`) not found. Install with
  `brew install gh` and run `gh auth login`. Without it, metadata and community
  health checks fall back to web scraping (slower, less data)." Continue with
  Nimble-only mode.
- Profile exists -> check for prior audit data at
  `~/.nimble/memory/seo/github-audits/{repo-slug}/`. If a `findings-*.json` file
  exists, load the most recent one for dedup in Step 8. Also check
  `~/.nimble/memory/reports/seo-github-{repo-slug}-*.md` for same-day runs.
  If a same-day report exists, ask: "Already ran today. Run again for fresh data?"
- No profile -> Step 1

### Step 1: First-Run Onboarding (2 prompts max)

Follow `references/profile-and-onboarding.md` for the full onboarding flow. If a
business profile already exists, skip this step entirely.

### Step 2: Scope Shaping (2 prompts max)

**Prompt 1** — ask in plain text (NOT AskUserQuestion with options):

> "Which GitHub repo should I audit? (URL or owner/name, e.g.,
> facebook/react or https://github.com/facebook/react)"

If `$ARGUMENTS` already contains a repo URL or owner/name, skip this prompt.
Parse `{owner}` and `{repo}` from the input. Accept both `github.com/owner/repo`
URLs and bare `owner/repo` format.

**Prompt 2** — confirm scope and gather inputs (use AskUserQuestion):

> I'll audit **{owner}/{repo}** for GitHub SEO.
>
> **Competitor repos** (optional — for benchmarking):
> - Provide up to 3 competitor repos (owner/name format)
> - Or skip for a standalone audit
>
> **Focus area:**
> - **Full audit** — all checks (metadata, README, community, search, AI)
> - **README only** — focus on README optimization
> - **Quick check** — metadata + README, skip search/AI visibility

Parse the competitor list and focus area from the response. Default to full audit
if unclear.

### Step 3: Repository Metadata Audit

Gather repository metadata. If `gh` is available, run these in parallel:

```bash
gh api repos/{owner}/{repo} --jq '{
  description, homepage, license: .license.spdx_id,
  topics, language, stargazers_count, forks_count,
  open_issues_count, has_wiki, has_pages, has_discussions,
  created_at, updated_at, pushed_at, default_branch,
  archived, disabled, visibility,
  subscribers_count, network_count, size
}'
```

```bash
gh api repos/{owner}/{repo}/languages
```

Also extract the rendered GitHub page for visual signals:

```bash
nimble extract --url "https://github.com/{owner}/{repo}" --format markdown --render
```

From the API response and rendered page, assess:

| Field | Check | Details |
|-------|-------|---------|
| Description | Present, 1-3 sentences, includes keywords | See `references/github-seo-checks.md` |
| Topics | 5-15 topics, mix of language + domain + use-case | Topics drive GitHub search |
| Homepage | URL set if docs/website exists | Links to external docs |
| License | Present, OSS-friendly (MIT/Apache/BSD) | Affects adoption willingness |
| Social preview | Custom image set (not auto-generated) | Check via rendered page |
| Languages | Primary language matches topics | Consistency signal |
| Activity | Last push < 90 days | Freshness signal |

If `gh` is not available, extract metadata from the rendered GitHub page using
`nimble extract`. This yields less structured data but covers description, topics,
stars, forks, license, and last update.

### Step 4: README Analysis

Fetch the README content. If `gh` is available:

```bash
gh api repos/{owner}/{repo}/readme --jq '.content' | base64 --decode
```

If `gh` is unavailable, fall back to:

```bash
nimble extract --url "https://github.com/{owner}/{repo}#readme" --format markdown --render
```

Analyze the README against all checks in `references/github-seo-checks.md` under
the README section. Key checks:

**Structure checks:**
- H1 present and matches or includes repo name
- Heading hierarchy (H1 -> H2 -> H3, no skipped levels)
- Table of contents present if README > 500 words
- Word count in 300-3000 range

**Content checks:**
- Code example within first 500 words (critical for developer repos)
- Installation/setup section
- Usage/quickstart section
- API reference or link to docs
- Contributing section or link to CONTRIBUTING.md
- License section or mention

**Polish checks:**
- Badges present (CI status, version/release, license, downloads/stars)
- Screenshots or demo GIF for visual projects
- Links to documentation site if one exists
- No broken links (sample-check 3-5 links via `nimble extract`)
- No stale version numbers or dates in README body

Score each check per the severity weights in `references/github-seo-checks.md`.

### Step 5: Community Health

If `gh` is available:

```bash
gh api repos/{owner}/{repo}/community/profile
```

This returns the community health percentage and status of each file. Check:

| Signal | How to Check | Weight |
|--------|-------------|--------|
| Code of conduct | community profile `code_of_conduct` field | Medium |
| Contributing guide | community profile `contributing` field | Medium |
| Issue templates | `gh api repos/{owner}/{repo}/contents/.github/ISSUE_TEMPLATE` | Medium |
| PR template | `gh api repos/{owner}/{repo}/contents/.github/PULL_REQUEST_TEMPLATE.md` | Low |
| Security policy | community profile `security` field | Medium |
| License | community profile `license` field | High |
| README | community profile `readme` field | Critical |
| Last commit | `pushed_at` from Step 3 — flag if > 90 days | High |
| Open issue response | sample 5 recent issues, check time to first response | Medium |
| Releases | `gh api repos/{owner}/{repo}/releases?per_page=5` | Medium |
| CHANGELOG | check for CHANGELOG.md in root | Low |

If `gh` is unavailable, scrape what's visible from the repository page and the
Insights > Community tab:

```bash
nimble extract --url "https://github.com/{owner}/{repo}/community" --format markdown --render
```

### Step 6: Search Visibility

Run search checks to measure how discoverable the repo is. Execute in parallel
(max 4 simultaneous):

**GitHub-specific search (via Google):**
```bash
nimble search --query "site:github.com {repo-name}" --search-depth lite --max-results 10
```

**Branded search:**
```bash
nimble search --query "{repo-name} github" --search-depth lite --max-results 10
```

**Category search:**
```bash
nimble search --query "{primary-keyword} {language} library" --search-depth lite --max-results 10
```

**Alternative phrasing:**
```bash
nimble search --query "best {category} tool {language}" --search-depth lite --max-results 10
```

Derive `{primary-keyword}` and `{category}` from the repo description and topics.
If topics are empty (common gap), extract category keywords from the repo
description by pulling noun phrases: "web scraping" from "Real-time web scraping
and data extraction", "AI agents" from "for AI agents". Use the repo name words
as fallback keywords. `{language}` comes from the primary language in Step 3.

For each search, record:
- Whether the repo appears in top 10 results
- Position if found
- Which competitor repos appear above it
- Whether the GitHub page or a docs site ranks

### Step 7: AI Discoverability (full audit only)

Check if AI coding assistants know about the repo using dedicated AI platform
agents (see `references/ai-platform-profiles.md`). Never hardcode template
names — discover and validate at runtime per `references/nimble-playbook.md`:

```bash
nimble agent list --search "chatgpt" --limit 50
nimble agent list --search "perplexity" --limit 50
```

Validate the top candidates with `nimble agent get --template-name {name}`
and cache the chosen template names as `{chatgpt_agent}` and
`{perplexity_agent}`. If a platform is not discovered, skip it for this run
and note reduced coverage.

Run 2-3 queries across the discovered platforms:

```bash
# {*_agent} come from the discovery step above
nimble agent run --agent "{chatgpt_agent}" --params '{"prompt": "What are the best {category} tools for {language}?", "skip_sources": false}'
nimble agent run --agent "{perplexity_agent}" --params '{"prompt": "What is {repo-name} and is it any good?"}'
nimble agent run --agent "{chatgpt_agent}" --params '{"prompt": "{use-case} tool recommendation for {language}", "skip_sources": false}'
```

Parse `data.parsing.answer` for brand/repo mentions and `data.parsing.sources`
for GitHub URL citations. Check for:
- Direct mention of the repo by name
- Citation of the repo's GitHub URL or docs URL in sources
- Mention of competitor repos instead
- Context (recommended, compared, or just mentioned)

Also check if Nimble has relevant agents that could surface the repo:

```bash
nimble agent list --search "{category}" --limit 50
```

If a relevant agent exists, run a test query to see if the repo appears in
structured extraction results.

### Step 8: Scoring

Read the scoring weights and grade thresholds from `references/github-seo-checks.md`.

Compute category scores (each 0-100):

| Category | Weight | Scoring Basis |
|----------|--------|---------------|
| README Quality | 30% | Check pass rate, weighted by severity |
| Metadata | 20% | Fields populated + quality |
| Community Health | 20% | Community profile completeness + activity |
| Search Visibility | 15% | Presence in search results for target queries |
| AI Discoverability | 15% | Mention/citation in AI answers |

**Overall Score** = weighted average of category scores.

**Grade mapping:**

| Grade | Score Range |
|-------|-------------|
| A | 90-100 |
| B | 75-89 |
| C | 60-74 |
| D | 40-59 |
| F | 0-39 |

**Dedup against prior audit:** If a previous findings JSON exists (loaded in
Step 0), compare each finding against it. Mark unchanged findings as "carryover."
Only NEW or WORSENED findings appear in the TL;DR and Quick Wins sections.

### Step 9: Competitor Benchmark (if requested)

If competitor repos were provided in Step 2, run Steps 3-7 for each competitor.
Use sub-agents (`agents/nimble-researcher.md`) with `mode: "bypassPermissions"`
to audit competitors in parallel (max 4 concurrent). Each agent receives the
competitor's owner/name and the same search queries used for the primary repo.

Build a comparison matrix covering: stars, forks, topics, README score, community
health, search position, AI mentions, and overall grade. Highlight where the
primary repo lags behind competitors and where it leads.

### Step 10: Report Generation & Save

Generate the report following the Output Format below.

Make all Write calls simultaneously:

- **Report** -> `~/.nimble/memory/reports/seo-github-{repo-slug}-{YYYY-MM-DD}.md`

- **Findings** -> `~/.nimble/memory/seo/github-audits/{repo-slug}/findings-{YYYY-MM-DD}.json`
  (structured JSON of all findings for future dedup)

- **Profile** -> update `last_runs.seo-github` in `~/.nimble/business-profile.json`

- Follow the wiki update pattern from `references/memory-and-distribution.md`: update
  `index.md` rows for affected directories, append a `log.md` entry for this run.
  Create `~/.nimble/memory/seo/github-audits/{repo-slug}/` if it does not exist.

### Step 11: Share & Distribute

**Always offer distribution — do not skip this step.** Follow
`references/memory-and-distribution.md` for connector detection, sharing flow, and
source links enforcement.

**Slack-specific:** Post TL;DR only — not the full report. Format:

> GitHub SEO: {owner}/{repo} — Grade {A-F} ({score}/100).
> Top issue: {description}. Full report saved locally.

### Step 12: Follow-ups

- **Fix a specific issue** -> provide exact text/config to add or change
- **Optimize README** -> generate an improved README draft
- **Add topics** -> suggest specific topics based on category research
- **Re-audit** -> run again after changes
- **"Looks good"** -> done

**Sibling skill suggestions:**

> **Next steps:**
> - Run `seo-site-audit` to audit the project's documentation website
> - Run `seo-ai-visibility` to track brand presence across AI search surfaces
> - Run `seo-keyword-research` to find keywords for the project's docs site

---

## Output Format

```
# GitHub SEO Audit: {owner}/{repo}

Date: {YYYY-MM-DD} | Grade: {A-F} ({score}/100)

## TL;DR
Grade: {A-F}. Top 3 issues. Biggest quick win.
{Delta summary if re-run: "N new issues, M resolved since {last_date}."}

## Metadata ({score}/100)
| Field | Current Value | Status | Recommendation |
(description, topics, homepage, license, social preview, languages, last push)

## README Quality ({score}/100)
| Check | Severity | Status | Details |
(all checks from references/github-seo-checks.md Category 2)

## Community Health ({score}/100)
| Signal | Status | Details |
(all checks from references/github-seo-checks.md Category 3)

## Search Visibility ({score}/100)
| Query | Position | Found? | Competitors Above |
(branded search, site-scoped, category, best-of queries)

## AI Discoverability ({score}/100)
| Query | Mentioned? | Cited? | Context | Competitors Mentioned |
(category recommendation, name recognition, use-case queries)

## Competitor Comparison (if benchmarked)
| Metric | {owner}/{repo} | {competitor-1} | {competitor-2} |
(stars, forks, topics, README score, community, search, AI, grade)

## Quick Wins
1. {Specific, actionable fix — expected effort < 30 min}
2. ...

## What This Means
Where the repo stands. Which gaps hurt most. Impact of fixing top issues.

Recommended follow-ups:
- Run `seo-site-audit` to audit the documentation website
- Run `seo-ai-visibility` to track brand presence in AI assistants
- Run `seo-keyword-research` to optimize docs site content
```

---

## Error Handling

See `references/nimble-playbook.md` for the standard error table (missing API key,
429, 401, empty results, extraction garbage). Skill-specific errors:

- **`gh` not installed or not authenticated:** Fall back to `nimble extract` for
  all GitHub data. Metadata comes from the rendered page. README comes from the
  raw URL (`https://raw.githubusercontent.com/{owner}/{repo}/{branch}/README.md`).
  Community health is limited to what's visible on the repo page. Note reduced
  data quality in the report.

- **`gh api` returns 404:** Repo may be private or nonexistent. Ask the user to
  verify the repo name. If the repo is private, `gh` must be authenticated with
  access. If `gh` returns 404 but `nimble extract` can render the page, the repo
  is public — continue with Nimble-only mode.

- **README not found:** Some repos lack a README. Record README score as 0 and
  make "Add a README" the top recommendation. Continue with other checks.

- **Rate limiting on search queries:** If `nimble search` returns 429, reduce
  parallel queries from 4 to 2. If 429 persists, run queries sequentially.
  Complete the run with available data.

- **AI answer not present for a query:** Expected — not all queries trigger AI
  answers. Record `ai_answer_present: false` and continue. Do not treat as error.

- **Competitor repo inaccessible:** Skip that competitor and note it in the
  report. Do not abort the entire benchmark for one failed competitor.

- **Base64 decode failure on README:** Fall back to fetching README via
  `nimble extract --url "https://github.com/{owner}/{repo}#readme" --format markdown`.

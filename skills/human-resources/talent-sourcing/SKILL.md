---
name: talent-sourcing
description: |
  Finds qualified candidates for a role by searching LinkedIn, Indeed, GitHub,
  and other professional platforms using Nimble Web Search Agents. Accepts a
  job description, role title, or freeform request and returns a ranked
  candidate list with profiles, skills, and contact signals.

  Use this skill when the user wants to find, source, or recruit candidates for
  a role. Common triggers: "find candidates for", "source engineers in",
  "who can I hire for", "find me a [role]", "recruiting for", "talent search",
  "find a [role] in [city]", "build a candidate list", "sourcing for [role]",
  "who's available for", "find potential hires". Also triggers on a pasted job
  description followed by a sourcing request.

  Do NOT use for job market research or salary benchmarking — use
  market-finder instead. Do NOT use for researching a single known person
  — use company-deep-dive or meeting-prep instead.
allowed-tools:
  - Bash(nimble:*)
  - Bash(date:*)
  - Bash(cat:*)
  - Bash(mkdir:*)
  - Bash(python3:*)
  - Bash(echo:*)
  - Bash(jq:*)
  - Bash(ls:*)
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Agent
  - AskUserQuestion
metadata:
  author: Nimbleway
  version: 0.19.0
---

# Talent Sourcing

Candidate discovery powered by Nimble Web Search Agents.

User request: $ARGUMENTS

**Before running any commands**, read `references/nimble-playbook.md` for Claude Code
constraints (no shell state, no `&`/`wait`, sub-agent permissions, communication style).

---

## Instructions

### Step 0: Preflight

Run the preflight pattern from `references/nimble-playbook.md` (5 simultaneous Bash
calls: date calc, today, CLI check, profile load, index.md load).

Also simultaneously:
- `mkdir -p ~/.nimble/memory/{reports,talent-sourcing}`

From the results:
- CLI missing or API key unset → read `references/profile-and-onboarding.md`, stop
- Profile exists → note industry keywords if any; proceed to Step 1
- No profile → fine, talent-sourcing doesn't require onboarding; proceed to Step 1

### Step 1: Parse Request & Confirm Search Parameters

Parse `$ARGUMENTS` for:
- **Role** — job title or function (e.g. "Senior React Engineer", "Head of Sales")
- **Location** — city, metro, region, or remote (e.g. "New York City", "remote US")
- **Skills / requirements** — specific technologies, years of experience, domain expertise
- **Seniority** — junior, mid, senior, staff, director, VP, C-level
- **Source preference** — specific platforms (LinkedIn, GitHub, Indeed, etc.) or "all"

If a full job description was pasted, extract the above fields from it.

If **role** is missing or ambiguous, ask with `AskUserQuestion`:

> "What role are you hiring for, and where? (e.g. 'Senior ML Engineer, remote US'
> or paste a job description)"

Once parameters are clear, confirm with the user using `AskUserQuestion`:

> "Searching for: **[Role]** | Location: **[Location]** | Key skills: **[Skills]**
> | Seniority: **[Seniority]**
>
> Platforms to search: LinkedIn, Indeed, GitHub (for technical roles), AngelList /
> Wellfound, and professional communities.
>
> - **Start search**
> - **Adjust parameters first**"

### Step 2: WSA Discovery

Discover available Web Search Agents for candidate-sourcing platforms. Run
simultaneously:

```bash
nimble agent list --search "linkedin people" --limit 20
nimble agent list --search "indeed resume" --limit 20
nimble agent list --search "github profile" --limit 20
nimble agent list --search "wellfound talent" --limit 20
```

Filter results for `entity_type: SERP` or `entity_type: PDP`. Prefer
`managed_by: "nimble"`. Validate promising agents with:

```bash
nimble agent get --template-name {name}
```

Cache discovered WSA names and required params. If no WSAs found for a platform,
fall back to `nimble search` for that platform.

### Step 3: Parallel Candidate Search (Sub-Agents)

Spawn `nimble-researcher` agents (`agents/nimble-researcher.md`) with
`mode: "bypassPermissions"`, max 4 concurrent. Assign one agent per platform:

**Agent 1 — LinkedIn**

Search for people matching the role criteria. Use Boolean-style query construction:

```bash
nimble search --query "site:linkedin.com/in [Role] [Location] [Key Skills]" \
  --max-results 15 --search-depth fast
nimble search --query "[Role] [Location] linkedin profile [Skill1] [Skill2]" \
  --max-results 10 --search-depth fast
```

If a LinkedIn WSA was discovered in Step 2, use it instead with the role title,
location, and skill keywords as inputs.

**Agent 2 — Indeed / Resumes**

```bash
nimble search --query "site:indeed.com resume [Role] [Location] [Key Skills]" \
  --max-results 10 --search-depth fast
nimble search --query "[Role] resume [Location] [Key Skills]" \
  --max-results 10 --search-depth fast
```

**Agent 3 — GitHub (technical roles only)**

Skip this agent for non-technical roles (e.g. Sales, Marketing, Operations).

```bash
nimble search --query "site:github.com [Role] [Location] [Key Skills]" \
  --max-results 10 --search-depth fast
nimble search --query "github [Key Skills] developer [Location] open to work" \
  --max-results 10 --search-depth fast
```

**Agent 4 — AngelList / Wellfound + Communities**

```bash
nimble search --query "site:wellfound.com [Role] [Location] [Key Skills]" \
  --max-results 10 --search-depth fast
nimble search --query "[Role] [Location] open to work OR seeking opportunities \
  [Key Skills]" --max-results 10 --search-depth fast
```

Each agent returns: candidate name (if available), profile URL, current title,
location snippet, inferred skills, availability signals ("open to work", "seeking",
"available") with event date (if available) and source URL.

### Step 4: Deep Profile Extraction

For the top candidates identified in Step 3 (aim for 10–20 unique profiles across
all platforms), extract full profile details. Run all extractions simultaneously:

```bash
nimble extract --url "[profile-url]" --format markdown
```

From each extracted profile, pull:
- **Full name**
- **Current role & company**
- **Location**
- **Skills / tech stack**
- **Experience summary** (years, notable employers)
- **Education**
- **Availability signals** (open to work, recent job change, posting activity)
- **Contact signals** (email, personal site, GitHub handle)

For extraction failures, follow the fallback pattern in
`references/nimble-playbook.md`. If a profile is behind a login wall and extraction
fails, keep the search-snippet summary instead — do not skip the candidate.

**Extraction budget:** extract up to 15 profiles. If more than 15 candidates were
found in Step 3, prioritize by relevance score (seniority match + skill overlap +
location match) before extracting.

### Step 5: Score & Rank Candidates

Score each candidate (1–10) using these weighted signals:

| Signal | Weight |
|--------|--------|
| Role / title match | 30% |
| Skill overlap with requirements | 30% |
| Location match | 20% |
| Seniority match | 10% |
| Availability signals | 10% |

Group candidates into tiers:
- **Tier 1 (Strong match, 7–10):** All required signals present
- **Tier 2 (Partial match, 4–6):** Most signals present, 1–2 gaps
- **Tier 3 (Stretch, 1–3):** Worth reviewing if Tier 1/2 list is thin

### Step 6: Output

Before presenting results, check `~/.nimble/memory/talent-sourcing/[role-slug].md` —
if a candidate was surfaced in a prior run, mark them `(previously surfaced)` rather
than re-presenting them as new.

Present a structured candidate report:

```
## Candidate Report: [Role] in [Location]
Searched: LinkedIn, Indeed, GitHub, Wellfound
Found: [N] candidates | Tier 1: [N] | Tier 2: [N] | Tier 3: [N]

**TL;DR:** [2-3 sentence summary of the strongest candidates and any notable patterns]

---

### Tier 1 — Strong Match

#### 1. [Name] — [Score]/10
- **Current role:** [Title] at [Company]
- **Location:** [Location]
- **Skills:** [Skill1], [Skill2], [Skill3]
- **Experience:** [X years, notable employers]
- **Availability:** [signal] — [event date or "date unknown"] — [source URL]
- **Profile:** [URL]
- **Contact signals:** [email / personal site / GitHub]

...

---

### What This Means
[1-2 sentences on hiring outlook: supply/demand signal, speed recommendation, any
standout sourcing channel]
```

Omit fields where data is unavailable. Do not fabricate details — use "unknown"
for missing fields. Add a one-sentence **"Why this candidate"** note for each
Tier 1 result.

### Step 7: Save to Memory

Make all Write calls simultaneously:

- Report → `~/.nimble/memory/reports/talent-sourcing-{YYYY-MM-DD}.md` (full candidate report with all tiers)
- Per-role → `~/.nimble/memory/talent-sourcing/[role-slug].md` (candidate list; write or update)
- Profile → update `last_runs.talent-sourcing` in `~/.nimble/business-profile.json` using the python3 snippet in `references/profile-and-onboarding.md`. Skip if the file does not exist.

Update `~/.nimble/memory/talent-sourcing/index.md` with a row for this search.
Follow the wiki update pattern from `references/memory-and-distribution.md`.

### Step 8: Share & Distribute

**Always offer distribution — do not skip this step.** Follow
`references/memory-and-distribution.md` for connector detection, sharing flow, and
source links enforcement.

### Step 9: Follow-ups

Offer next steps using `AskUserQuestion`:

> **What's next?**
> - **Go deeper on a candidate** — extract full profile + find contact info
> - **Expand search** — broaden location, relax seniority, try more platforms
> - **Narrow search** — add a required skill or tighten location
> - **Export list** — save as CSV or formatted doc
> - **Done**

**Sibling skill suggestions:**

> - Run `company-deep-dive` on a candidate's current employer for deal context
> - Run `meeting-prep` before reaching out to a Tier 1 candidate

---

## Error Handling

See `references/nimble-playbook.md` for the standard error table. Skill-specific
handling:

- **Profile behind login wall:** Keep search-snippet summary; note "full profile
  unavailable — LinkedIn/Indeed login required" in the candidate entry.
- **< 5 total candidates found:** Notify the user, suggest broadening location to
  remote or relaxing seniority, then ask whether to re-run with adjusted params.
- **Search 500 on a platform:** Retry once with a simplified query; if still failing,
  skip that platform and note it in the report header.
- **GitHub agent skipped for non-technical role:** Note "GitHub not searched for
  this role type" in the report header.

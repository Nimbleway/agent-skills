---
name: meeting-prep
description: |
  Researches meeting attendees and their companies before any meeting using
  real-time web data. Surfaces roles, recent activity, company context, and
  talking points — then maps cross-attendee relationships.

  Use this skill when the user asks to prepare for a meeting, research someone
  they're meeting, or wants context on attendees. Common triggers: "prepare me
  for my meeting", "who am I meeting with", "research this person", "meeting
  prep", "brief me on [person]", "I have a meeting with [person/company]",
  "get me ready for my call", "what should I know about [person]",
  "background on [person] before our meeting", "attendee research".

  Requires the Nimble CLI (nimble search, nimble extract) for live web data.
  Do NOT use for multi-company competitor monitoring (use competitor-intel)
  or single-company deep dives without attendees (use company-deep-dive).
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
  version: 1.0.0
---

# Meeting Prep

Research-powered meeting preparation with attendee intelligence and company context.

User request: $ARGUMENTS

**Before running any commands**, read `references/nimble-playbook.md` for Claude Code
constraints (no shell state, no `&`/`wait`, sub-agent permissions, communication style).

---

## Instructions

### Step 0: Preflight

Follow the preflight pattern from `references/nimble-playbook.md`. Make these Bash
calls simultaneously:

- 14-days-ago date calculation (see nimble-playbook.md for cross-platform command)
- `date +%Y-%m-%d` (today)
- `nimble --version && echo "NIMBLE_API_KEY=${NIMBLE_API_KEY:+set}"`
- `cat ~/.nimble/business-profile.json 2>/dev/null`

From the results:
- CLI missing or API key unset → `references/profile-and-onboarding.md`, stop
- Profile exists → note the user's company (helps frame "them vs us" context).
  Load any existing person profiles from `~/.nimble/memory/people/` for attendees
  you've researched before — skip redundant searches, surface prior meeting notes.
- No profile → that's fine. Meeting prep doesn't require onboarding. Proceed to Step 1.

### Step 1: Gather Meeting Context

Parse the meeting details from `$ARGUMENTS` or ask the user.

**Calendar shortcut:** If the user didn't specify attendees and a calendar connector
is available — either a calendar MCP tool (look for `list_events` in the tool list)
or the `gws` CLI (`gws calendar +agenda --today`) — offer to pull today's meetings
so they can pick one. If neither is available, skip this silently.

**If clear** (e.g., "prep me for my meeting with Sarah Chen at Stripe tomorrow"):
- Extract: attendee name(s), company, meeting date/time (if given)
- Confirm briefly: "Preparing briefing for your meeting with **Sarah Chen** at **Stripe**..."

**If partial** (e.g., "prep me for my meeting tomorrow"):
- Ask one clarifying question in plain text:
  > "Who are you meeting with? (names, titles, and company if you have them)"

**If just a person** (e.g., "research John Smith"):
- Proceed with the person. Try to infer their company from search results.

**Extract these fields:**

| Field | Required | Source |
|-------|----------|--------|
| Attendee name(s) | Yes | User input or calendar event |
| Company | Preferred | User input or inferred from search |
| Attendee title(s) | Optional | User input or discovered in Step 2 |
| Meeting type | Optional | User input (discovery, demo, check-in, interview, partnership, internal) |
| Meeting date/time | Optional | User input |
| Additional context | Optional | User notes ("they're evaluating our product", "board member intro") |

**Meeting type detection** — if the user doesn't specify, infer from context clues:

| Signal | Inferred type |
|--------|---------------|
| "prospect", "demo", "sales call" | Sales / discovery |
| "interview", "candidate" | Interview |
| "board", "investor" | Board / investor |
| "partner", "integration" | Partnership |
| "check-in", "sync", "1:1" with colleague | Internal |
| No signal | General external |

The meeting type shapes the briefing focus (see Step 5).

### Step 2: Per-Attendee Research (sub-agents)

Read `references/attendee-agent-prompt.md` for the full agent prompt template.
Follow the sub-agent spawning rules from `references/nimble-playbook.md`
(bypassPermissions, batch max 4, explicit Bash instruction, fallback on failure).

**Check memory first.** For each attendee, check `~/.nimble/memory/people/[name-slug].md`.
If a profile exists and is < 30 days old, load it as known context and pass it to the
agent so it focuses on what's new. If > 30 days old, run a full refresh.

Spawn `nimble-researcher` agents (`agents/nimble-researcher.md`) with
`mode: "bypassPermissions"`. One agent per attendee.

**Important:** The Nimble API has a 10 req/sec rate limit per API key. With each agent
running 4-5 searches, limit concurrent agents to 2 per batch. For 3+ attendees, batch
in groups of 2.

**Batch 1** (2 agents simultaneously):
- Attendee 1 research
- Attendee 2 research

**Batch 2** (if needed):
- Attendee 3 research
- Attendee 4 research

**Single attendee optimization:** If only one person, run the searches directly from
the main context instead of spawning an agent — saves overhead.

**Fallback:** If any agent fails or returns empty, run those searches directly from
the main context. Don't leave gaps in the briefing.

### Step 2.5: Gap Check

Before proceeding, verify every attendee has at least a title and company confirmed.

**For any attendee with < 3 meaningful results or "Role Unknown":**
1. Run a `--focus social` fallback search directly (this searches social platform
   people indices and is the most reliable way to find someone):
   `nimble search --query "[Name] [Company]" --focus social --max-results 5 --search-depth lite`
2. If `--focus social` errors (plan limitation), fall back to:
   `nimble search --query "[Name]" --include-domain '["linkedin.com"]' --max-results 5 --search-depth lite`
3. Try name variations: "[First] [Last]", "[Full Name] [Company] [Title if known]"

Do NOT present a briefing with "Role Unknown" — exhaust social search first. If still
nothing after fallbacks, note it honestly: "Limited public presence — could not confirm
role. Consider asking for their LinkedIn URL."

Also collect **LinkedIn profile URLs** for each attendee during this step if not already
found. These are high-value for the final briefing output and Notion distribution.

### Step 3: Company Research

Research the attendees' company for meeting-relevant context. This is a lighter version
of company-deep-dive — focused on what's useful for the conversation, not a full 360°.

**Company name quoting:** If the company name contains common words that cause noisy
results (e.g., "HD Supply", "Blue Origin", "General Electric"), wrap it in escaped
quotes: `"\"HD Supply\" news"`. Use `site:[domain]` as an alternative anchor.

Make these Bash calls simultaneously:

- `nimble search --query "\"[Company]\" news" --focus news --start-date "[14-days-ago]" --max-results 8 --search-depth lite`
- `nimble search --query "\"[Company]\" product launch OR announcement" --focus news --start-date "[14-days-ago]" --max-results 5 --search-depth lite`
- `nimble search --query "site:[domain] about" --max-results 3 --search-depth lite`
- `nimble search --query "\"[Company]\" funding OR raised OR investors" --max-results 5 --search-depth lite`

If your user's company profile exists, also run:
- `nimble search --query "[Company] [UserCompany] OR [user-domain]" --max-results 5 --search-depth lite`

This catches any existing relationship between the two companies — prior partnerships,
mentions, shared investors, or competitive overlap.

**If < 3 results** from the news searches, retry without `--start-date`.

**If the company was already researched** (exists in `~/.nimble/memory/companies/`),
load the existing profile and only run the news search for fresh updates.

### Step 4: Deep Extraction

From Steps 2-3, identify the **top 3-5 most informative URLs** across all results.
Prioritize:
- Attendee's own LinkedIn posts, articles, or talks
- Recent company announcements directly relevant to the meeting
- Interviews or profiles of the attendee
- The company's about/team page (if attendee title wasn't found)

Make one Bash call per URL, all simultaneously:

`nimble extract --url "https://..." --format markdown`

For extraction failures, follow the fallback in `references/nimble-playbook.md`.

**Single attendee + known company:** Skip company extraction, focus on person URLs.
**Multiple attendees:** Prioritize person-specific URLs over company-level ones.

### Step 5: Synthesize Briefing

Structure the output as a meeting prep briefing. Adapt focus based on meeting type.

```
# Meeting Prep: [Company Name]
*[Meeting date/time if known] | Prepared [today's date]*

## Quick Take
[2-3 sentences: who you're meeting, why it matters, and the one thing to know
going in. This is the "read nothing else" paragraph.]

## Attendees

### [Name] — [Title]
**Background:** [Current role, time in position, career trajectory highlights]
**Recent Activity:** [What they've been posting, speaking about, or working on.
  Direct quotes from posts/talks when available.]
**Conversation hooks:** [2-3 specific things to reference — shared connections,
  their recent project, a post they wrote, a talk they gave]
**Notes from prior meetings:** [If exists in memory — what was discussed, their
  preferences, open items. "No prior meetings on file" if none.]

[Repeat for each attendee]

## Relationship Map
[Cross-attendee connections — shared employers, mutual connections, overlapping
  interests, organizational dynamics between attendees. Skip if single attendee.]

## Company Context
- **What they do:** [One line]
- **Size / Stage:** [Employees, funding stage, HQ]
- **Recent news:** [Top 2-3 items, dated with source]
- **Relevant to your meeting:** [How their company context connects to your
  discussion — e.g., recent product launch you might discuss, funding that
  signals growth, leadership change affecting priorities]

## Talking Points
[3-5 specific, actionable conversation starters grounded in the research.
  Not generic "ask about their priorities" — specific: "Ask about their
  migration from [old tool] to [new tool] that they announced last month."]

## Watch Out For
[1-3 things to be aware of — sensitive topics (recent layoffs, bad press),
  potential awkward overlaps, information gaps you couldn't fill.]

## Sources
[Numbered list of key URLs cited in the briefing]
```

**Meeting type adaptations:**

| Type | Emphasis | Add to briefing |
|------|----------|-----------------|
| Sales / discovery | Buyer authority, pain signals, competitive stack | "Qualification signals" section |
| Interview | Candidate's work history depth, cultural signals | "Assessment angles" section |
| Board / investor | Financial context, market position, portfolio overlap | "Key metrics to reference" section |
| Partnership | Mutual benefit signals, integration opportunities | "Alignment opportunities" section |
| Internal | Skip company research, focus on person's recent work | Lighter format, no company section |
| General external | Balanced across all dimensions | Standard format above |

**Core rules:**
- Every factual claim must have a source URL.
- Lead with the Quick Take — most readers stop there.
- Talking points must be specific to THIS meeting, grounded in research findings.
  Never generate generic conversation starters.
- Say "no public information found" for a person rather than speculating about their
  role or background.
- If memory has prior meeting notes, surface open items and continuity points
  prominently — this is the highest-value content.

### Step 6: Save to Memory

Make all Write calls simultaneously:

- Report → `~/.nimble/memory/reports/meeting-prep-[company-slug]-[date].md`
- Per attendee → `~/.nimble/memory/people/[name-slug].md`
  (use the format in `references/memory-and-distribution.md`)
- Company profile → update `~/.nimble/memory/companies/[company-slug].md` if new
  company data was found
- Profile → update `last_runs.meeting-prep` in `~/.nimble/business-profile.json`
  (only if profile exists)

The person profile in `people/` should contain structured key facts (role, background,
interests, communication style) that can be loaded by future meeting prep runs.

### Step 7: Share & Distribute

**Always offer distribution — do not skip this step.** Follow
`references/memory-and-distribution.md` to offer Notion/Slack sharing based on
available connectors. Even if the user hasn't set up integrations, offer it once
per run so they know the option exists.

### Step 8: Follow-ups

- **Go deeper** on an attendee → more focused person research
- **Add attendees** → research additional people joining the meeting
- **"What about [topic]?"** → targeted search on specific dimension
- **"Looks good"** → done

---

## Agent Teams Mode (Dual-Mode)

Check at startup: `echo $CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`

**Team mode** (flag set): Spawn **teammates** instead of sub-agents. Each teammate
researches one attendee and can message the others when finding cross-connections.

| Teammate | Focus | Cross-checks with |
|----------|-------|-------------------|
| **Attendee 1 researcher** | Full person + company research for attendee 1 | All other teammates (shared employers, connections) |
| **Attendee 2 researcher** | Full person + company research for attendee 2 | All other teammates |
| **[Additional per attendee]** | ... | ... |

How cross-attendee discovery works:
1. Each teammate researches their assigned attendee independently
2. When a teammate discovers a workplace, school, or connection that overlaps with
   another attendee, they send a message to that teammate: "My attendee [Name] worked
   at [Company] from 2019-2022 — did yours overlap?"
3. The receiving teammate checks and responds
4. Lead (you) collects all cross-references and builds the Relationship Map section

This produces higher-quality relationship maps than solo mode because teammates
actively search for connections rather than just comparing results post-hoc.

**Solo mode** (flag not set): Standard sub-agent flow from Step 2.

---

## What This Skill Is NOT

- **Not competitor monitoring.** For tracking multiple competitors over time, use
  `competitor-intel`. This skill researches people and their companies for meetings.
- **Not a company deep dive.** For comprehensive single-company research without
  specific attendees, use `company-deep-dive`.
- **Not a CRM.** This skill gathers live web intelligence. It doesn't manage
  contacts, deals, or pipelines.
- **Not a calendar app.** If a calendar MCP connector is available, this skill
  can read events to auto-detect attendees. But it doesn't create, modify, or
  manage calendar events — it only reads them for meeting context.

---

## Error Handling

- **Missing API key:** `references/profile-and-onboarding.md`
- **Person not found:** Try variations — full name, first + last, with company name.
  If still nothing: "Couldn't find public information on [Name]. They may have a
  limited online presence. Can you share their title or LinkedIn URL?"
- **Ambiguous name:** "I found multiple people named [Name]. Which one?"
  Present top candidates with company/title context.
- **Empty company results:** Retry without `--start-date`. Still empty → note it and
  focus on attendee-level findings.
- **429 rate limit:** Fewer simultaneous Bash calls
- **401 expired:** "Regenerate at app.nimbleway.com > API Keys"
- **Extraction garbage:** See fallback in `references/nimble-playbook.md`

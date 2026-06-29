---
name: launch-monitor
description: |
  Monitors press, social, developer communities, and competitor channels from any point around
  a product launch — tracking sentiment, flagging mischaracterizations, surfacing competitor
  responses, and recommending actions in real time. Nimble reaches sources that block standard
  agents — including paywalled press, Reddit, LinkedIn, JavaScript-heavy pages, and live
  community forums — while Claude triages every signal by urgency. Delivers a Response War Room
  dashboard with a live signal feed, mischaracterization tracker, competitor response panel,
  and sentiment velocity chart.

  Use when asked to "monitor this launch", "track the launch", "what's being said about the
  launch", "flag any mischaracterizations", "competitor response to the launch", "post-launch
  coverage", "check press coverage for the launch", or "what's the reaction to the
  announcement".

  Do NOT use for ongoing brand monitoring unrelated to a launch — use brand-mention-monitor
  instead. Do NOT use for ongoing competitor intelligence unrelated to a specific launch
  window — use competitor-intel instead.
allowed-tools:
  - Bash(nimble:*)
  - Bash(claude:*)
  - Bash(grep:*)
  - Bash(date:*)
  - Bash(cat:*)
  - Bash(mkdir:*)
  - Bash(python3:*)
  - Bash(echo:*)
  - Bash(jq:*)
  - Bash(ls:*)
  - Read
  - Write
  - Agent
  - AskUserQuestion
metadata:
  author: Nimbleway
  version: 0.25.0
---

# Launch Monitor

Monitors press, social, and community forums from launch day — tracking sentiment, flagging mischaracterizations, surfacing competitor responses, and recommending actions so you can respond fast.

---

## Onboarding message

When this skill is triggered for the first time in a session, send this message. Send it exactly once per session, before asking any setup questions. Do not skip it even when the user's opening message already names a product — the onboarding sets expectations for what the skill collects and how it works.

> 👋 **Launch Monitor is ready.**
>
> This skill monitors press, social media, developer communities, and competitor channels around a product launch — tracking sentiment, flagging mischaracterizations, surfacing competitor responses, and telling you exactly what to respond to and how.
>
> To start, just say:
> _"Monitor the launch of [product name]"_
>
> Or try:
> - "Track coverage since we announced [product] yesterday"
> - "What's the reaction to our [product] launch?"
> - "Flag any mischaracterizations in our [product] press coverage"
> - "How are competitors responding to our [product] launch?"
>
> Would you like me to save your preferences so I skip the questions next time?

---

## Preflight

Follow the transport selection and standard preflight from `references/nimble-playbook.md`: pick CLI vs MCP at session start, then run the parallel preflight calls (date, profile, memory index) simultaneously. Tag every Nimble CLI call: `nimble --client-source skill-launch-monitor <subcommand>`.

From the profile (`~/.nimble/business-profile.json`): load product/brand context and `last_runs.launch-monitor` for date windowing. Pre-populate setup questions so the user confirms rather than re-enters. If no profile exists, follow the first-run onboarding flow in `references/profile-and-onboarding.md` and create a stub after the first run.

---

## How to start

**Before asking anything, do two quick research steps:**

**Step A — Resolve alternate names automatically:**
Search for the product the user named to discover all alternate names, codenames, version names, and related search terms. Do not ask the user for this. Use what you find to build a comprehensive search term list for Step 1.
- Search: `"[product name]" official name OR "also known as" OR codename OR version`
- For Apple products, always check for internal codename, model number, and marketing name variants
- For software: check GitHub repo names, API names, and SDK names
- Add all confirmed variants to your search queries silently — the user never needs to see this step

**Step B — Confirm launch date automatically:**
Search for when the product launched before asking the user. Surface what you find and ask the user to confirm or correct it.
- Search: `"[product name]" launch date OR announced OR "available now" OR "shipping today"`
- If you find a clear date, present it to the user for confirmation
- If you find multiple conflicting dates (announcement vs GA), surface both and ask which window to use

**Then ask in a single message:**

> "Before I run — just confirming a couple of things:
> 1. **Launch date:** I found that [product] launched on [DATE YOU FOUND] — is that the right date to monitor from, or a different one?
> 2. **Window:** How far back should I look beyond that? (default: from launch date to now)
> 3. **Depth:** Quick scan (faster) or deep sweep (more thorough, more sources)? (default: deep)
> 4. **Competitors:** I'll monitor competitor responses by default — any specific competitors to prioritize or exclude?"

**Output is always the Response War Room rendered directly in Claude.** Do not ask about format or output options.

**Exceptions — skip asking entirely if:**
- The user provided all the above in their initial message
- The user has run this skill before in the session (use prior config)

**Defaults if user says "just run it":**
- Window: launch date to now
- Depth: deep
- Competitors: on (identify automatically from context profiling)

**Disambiguation:** If the product name is ambiguous after research, confirm before proceeding:
> "Just to confirm — by [product], do you mean [Option A] or [Option B]?"

---

## Step 0 — Context profiling (run before any searches)

Before searching, profile the product to adapt all queries:

1. What category is this? (developer tool, consumer app, enterprise SaaS, hardware, API, etc.)
2. What ecosystem does it live in? (e.g. Claude/Anthropic, AWS, Salesforce, open source)
3. Who is the target audience? (developers, PMs, enterprise buyers, consumers)
4. What are the key claims made at launch? (extract from the user's description or a quick search of the announcement)
5. What would a mischaracterization look like? (wrong category, wrong pricing, wrong capability, wrong comparison)

Use this profile to:
- Target the right communities and press outlets
- Build precise search queries that find real coverage vs noise
- Know what "correct" positioning looks like so mischaracterizations can be flagged accurately
- Understand what competitor responses would look like

---

## Step 1 — Signal sweep

Run all of the following in parallel. Use `--search-depth lite` for the discovery pass. Switch to `--search-depth deep` only when extracting full article or thread content. Tag every call: `nimble --client-source skill-launch-monitor search ...`

### Press & editorial
- `"[product name]" site:techcrunch.com`
- `"[product name]" site:theverge.com`
- `"[product name]" site:wired.com`
- `"[product name]" site:arstechnica.com`
- `"[product name]" site:venturebeat.com`
- `"[product name]" site:siliconangle.com`
- `"[product name]" site:theregister.com`
- `"[product name]" site:zdnet.com`
- `"[product name]" "[company name]" announcement OR launch OR release`
- Category-specific press (e.g. for dev tools: InfoQ, SDTimes; for AI: The Information, Import AI)

### Social & community
Run ALL of the following — social moves faster than press. Use `focus:"social"` on Nimble for broader platform reach. See `references/sources.md` Tier 2b for full query patterns per platform.

**Reddit** (run multiple subreddit-specific queries, not just the broad one):
- `"[product name]" site:reddit.com` — broad
- `"[product name]" site:reddit.com/r/[category]` — category subreddit
- `"[product name]" site:reddit.com/r/[company]` — brand subreddit
- `"[product name]" site:reddit.com/r/technology` and other relevant subs
- Nimble social focus: `focus:"social"` query `"[product name]" reddit`

**X / Twitter:**
- `"[product name]" site:x.com`
- `"[product name]" wrong OR broken OR disappointed site:x.com` — complaint hunt
- `"[product name]" "actually" OR correcting site:x.com` — correction chains
- Check quote-tweets of the official launch tweet

**LinkedIn:**
- `"[product name]" site:linkedin.com`
- `"[product name]" launched OR "my take" site:linkedin.com`

**Instagram:**
- Nimble social focus: `focus:"social"` query `"[product name]" instagram`
- Signal: influencer posts, brand account engagement, consumer reactions

**TikTok:**
- Nimble social focus: `focus:"social"` query `"[product name]" tiktok review OR reaction`
- Signal: viral reaction videos within 48h; comment sentiment

**YouTube:**
- `"[product name]" review OR reaction OR "first impressions" site:youtube.com`
- `"[product name]" problems OR issues site:youtube.com`

**Facebook / Threads:**
- Nimble social focus: `focus:"social"` query `"[product name]" facebook OR threads`

**Hacker News:**
- `"[product name]" site:news.ycombinator.com`
- Also search: `hn.algolia.com/?q=[product+name]&dateRange=last24h`

**Dev communities:**
- `"[product name]" site:dev.to`
- `"[product name]" site:medium.com`

### Developer communities (if applicable)
- `"[product name]" site:stackoverflow.com`
- `"[product name]" site:github.com` — issues, discussions, reactions
- `"[product name]" site:discord.com OR discord community`
- `"[product name]" site:hashnode.com`

### Competitor monitoring (if enabled)
- `[competitor A] "[product name]" OR "[category]"` — how are they reacting?
- `[competitor A] announcement OR response OR "compared to"` — any counter-announcements?
- Check competitor social accounts and blogs for positioning moves
- Search for "[competitor] vs [product name]" content published since launch date

### Mischaracterization hunting
Run targeted queries designed to surface wrong information:
- `"[product name]" "[wrong claim to watch for]"`
- `"[product name]" pricing OR price` — check if pricing is being reported accurately
- `"[product name]" vs "[wrong comparison]"` — is it being compared to the wrong thing?
- `"[product name]" "[capability it doesn't have]"` — check for capability inflation or deflation

---

## Step 2 — Signal triage

For every signal found, assign:

**Urgency level:**
- 🔴 **Act now** — mischaracterization going viral, high-reach negative coverage, competitor counter-announcement, crisis signal
- 🟡 **Monitor** — emerging negative theme, mid-reach inaccurate coverage, competitor positioning content
- 🟢 **Good signal** — accurate positive coverage, organic enthusiasm, developer adoption signals
- ⬜ **Noise** — irrelevant mentions, unrelated products with similar names, spam

**Action badge:**
- `RESPOND` — requires a direct public response (tweet, comment, press outreach)
- `CORRECT` — requires a correction or clarification (DM, comment, press note)
- `AMPLIFY` — worth sharing, retweeting, or building on
- `ESCALATE` — needs to go to comms, legal, or leadership
- `WATCH` — no action yet but track for escalation
- `IGNORE` — filtered noise

**Signal type:**
- Press coverage · Community discussion · Social mention · Competitor move · Mischaracterization · Churn signal · Influencer take · Developer reaction · Analyst comment

**Source URL — required for every signal:**
Every signal must include the **exact URL** returned by Nimble for that article, thread, or post. This URL powers the clickable **↗ source** link on each card. A homepage URL is useless to the user.

**CORRECT — exact article/thread/post URLs:**
- `https://techcrunch.com/2026/06/11/nimble-mcp-connector-launch`
- `https://news.ycombinator.com/item?id=12345678`
- `https://reddit.com/r/MachineLearning/comments/abc123/is_nimble_just_another_scraper`
- `https://x.com/[username]/status/[POST_ID]`

**WRONG — never use these:**
- `https://techcrunch.com`
- `https://news.ycombinator.com`
- `https://reddit.com`
- `https://x.com`

Use the URL exactly as Nimble returns it in the search result. Do not fabricate a URL.

---

## Step 3 — Mischaracterization analysis

For every piece of coverage that gets something wrong, extract:
1. **The claim** — exactly what was said
2. **The source** — outlet, author, reach estimate, date
3. **What's wrong** — specific inaccuracy
4. **The correct version** — what the accurate statement is
5. **Spread risk** — is this being picked up by others? (search for secondary coverage citing the wrong claim)
6. **Suggested response** — one-sentence correction Claude recommends

---

## Step 4 — Sentiment velocity

Track how sentiment is trending over time since launch:

- Break the window into intervals (e.g. hourly for first 24h, daily after that)
- For each interval: count positive, negative, neutral signals
- Identify the inflection point — when did sentiment peak? When did it shift?
- Flag any velocity spike — sudden surge in mentions (positive or negative)

---

## Memory dedup (filter already-known signals)

Before generating output, run the dedup lifecycle from `references/memory-and-distribution.md` against prior launch-monitor reports in `~/.nimble/memory/reports/`.

Skill-specific rules:
- **Fingerprint:** `{url, signal_type, published_date}` — normalize URLs (strip query params, trailing slashes).
- **Returning signal, urgency changed:** keep in feed, mark with `↩ returning · urgency changed` badge.
- **Already known, no change:** suppress from Act Now / Monitor sections; include in appendix only if user requested full history.
- **Summary line:** show at top of war room: `X net-new · Y returning (urgency changed) · Z suppressed`.
- **Persist:** after the run, save signal fingerprints to `~/.nimble/memory/reports/launch-monitor-{YYYY-MM-DD}.md` and append a `log.md` entry per `references/memory-and-distribution.md`.

---

## Output template (REQUIRED)

Claude MUST follow `references/template.html` exactly when generating the HTML output. Load the template, substitute real researched data into placeholders, keep all CSS, JS, and interaction patterns identical.

### Required response structure

Every launch-monitor response must follow this structure, in order:

1. **`## TL;DR`** — first section, always. Two to three sentences: overall sentiment read (positive / mixed / negative / trending), count of act-now items, and the single most urgent signal or mischaracterization. Example: "Sentiment is mixed-to-negative in the first 48 hours, with 5 act-now items. The dominant risk is the 'Gemini reskin' framing spreading across HN and press. Three mischaracterizations are active, two spreading."
2. **The inline Response War Room widget** — rendered immediately after TL;DR per the sequence below.
3. **`## What This Means`** — final section, always. Two to three sentences synthesizing what the signal pattern implies for launch trajectory and the single most important action for the team to take right now.

### Rendering — INLINE FIRST, ALWAYS (read this before producing output)

The Response War Room is an **interactive widget that must be rendered inline in the chat**. A downloadable file is a *secondary* artifact, never the primary deliverable. Follow this sequence exactly, every run:

1. **Render the war room inline FIRST.** Write the fully-populated `launch-monitor-{YYYY-MM-DD}.html` to `~/.nimble/` using the Write tool, then emit the HTML content inline in the conversation so the user sees the interactive widget immediately. This inline output is the main deliverable and must happen before anything else is offered.
2. **Then, and only then, offer downloads.** After the inline widget is on screen, confirm that `~/.nimble/launch-monitor-{YYYY-MM-DD}.html` and `~/.nimble/launch-monitor-{YYYY-MM-DD}.md` have been saved and offer them to the user for download or sharing.

**Hard rules:**
- **Never** respond with only a download link or only a file. If the user sees a file but no inline war room, the run has failed its primary job.
- **Do not ask** the user whether they want it inline or as a file, and do not ask about format — inline is always the default and the file always accompanies it.
- The inline widget and the downloadable HTML are the **same artifact** — render the identical template, do not produce a stripped-down inline version.

**If the inline output genuinely cannot be produced:**
1. Say so explicitly in one short line — e.g. "I couldn't render the war room inline this time, so here's the file instead."
2. Confirm the file has been saved to `~/.nimble/launch-monitor-{YYYY-MM-DD}.html` as the fallback.

Never silently fall back to a download — if inline fails, name the failure so the user knows it was the environment, not the intended behavior.

### Output template spec (`launch-monitor-{YYYY-MM-DD}.html`)

The Response War Room has a distinct visual identity from all other skills:
- **Light background** using CSS variables — inherits host theme, works in both light and dark mode
- **Monospace accents** for signal metadata — feels operational, not reporty
- **Color system:** Red `#A32D2D` / Amber `#854F0B` / Green `#3B6D11` for urgency — matches the CSS variable palette
- **Tight, dense layout** — war room feel, not a dashboard feel
- **Source links:** `<a href="[EXACT_NIMBLE_URL]" class="src-link">↗ source</a>` — color `#185FA5`, no border/background, click listener on `sc-top` (not `sc`) so links pass through

**Required sections in order:**

**0. Launch header bar**
Full-width bar showing: product name · launch date · time since launch · total signals found · last updated timestamp

**1. Sentiment velocity chart**
A small line chart (not bars) showing signal volume over time since launch, split into positive (green line) and negative (red line). X-axis = time intervals. Y-axis = signal count. Hoverable data points showing count + top signal at that moment. Click a point to filter the signal feed to that time window.

**2. Signal feed — the war room**
The main panel. Signal cards displayed in a **responsive grid that packs 2–3 cards across** by available width (it auto-fills columns rather than forcing a fixed count, so the feed stays compact and never collapses to a single long column). Cards are sorted by urgency (🔴 first, then 🟡, then 🟢). Each card shows:
- Top row: urgency dot + action badge + type tag + chevron (all on one line in `.sc-header`)
- Headline (font-size 12px, font-weight 500)
- One-line context (font-size 11px, muted)
- Bottom row: metadata + ↗ source link — pinned to card bottom with `margin-top:auto` and a top border so all cards in a row align visually
- Suggested action shown on expand — click card to expand (click listener on `.sc-top`, not `.sc`, so source link clicks pass through)

**Grid layout CSS:** `.feed { display:grid; grid-template-columns:repeat(auto-fill,minmax(215px,1fr)); gap:8px }` — auto-fill packs as many ~215px columns as fit (2–3 across at typical render widths), keeping the feed short. Do not change this back to a fixed `repeat(2,...)`, which can collapse to one column at narrow widths.
**`.no-sigs` spans both columns:** `grid-column:1/-1`

**Filter bar above the feed:**
- Primary: View tabs — All / 🔴 Act now / 🟡 Monitor / 🟢 Good / Mischar. — synced with clickable stat cards
- Secondary: Collapsed "Refine" button → expands panel with action type + signal type pills
- Active filters shown as dismissable chips with "Clear all"

All filters stack. Signal count updates live. "No signals match" empty state spans full width.

**3. Mischaracterization tracker**
A dedicated panel — only shown if mischaracterizations were found. Two-column layout:

Left column: **The claim** (what was said, source, reach)
Right column: **The correction** (accurate version + suggested response text)

Each row has a `COPIED` button that copies the suggested correction to clipboard. Status badge: `SPREADING` (if being picked up) / `CONTAINED` (single source) / `CORRECTED` (if already addressed).

**4. Competitor response panel**
Only shown if competitor monitoring is enabled. One card per competitor showing:
- Competitor name
- What they did (published content, tweet, counter-announcement, silence)
- Urgency assessment
- Suggested counter-move

**5. Coverage summary**
Compact stats row: Total signals · Press mentions · Community threads · Social mentions · Mischaracterizations · Competitor moves · Avg sentiment score

**Interaction requirements (JS click handlers — never CSS hover):**
- Signal cards: click to expand/collapse suggested action text
- Velocity chart: click data point to filter feed to that time window
- Filter buttons: all three filter rows stack independently
- Mischaracterization copy button: copies correction text to clipboard
- All filters show live count of matching signals

**Styling:**
- Background: `var(--color-background-primary)` — transparent outer, inherits host
- Card background: `var(--color-background-primary)` with `0.5px solid var(--color-border-tertiary)` border
- Section backgrounds: `var(--color-background-secondary)`
- Text: `var(--color-text-primary)` / `var(--color-text-secondary)` — never hardcoded
- Monospace: `'SF Mono', 'Fira Code', monospace` for metadata fields
- Urgency red: `#A32D2D` · amber: `#854F0B` · green: `#3B6D11`
- Action badge colors: RESPOND/ESCALATE use red tint · CORRECT amber tint · AMPLIFY green tint · WATCH gray tint
- Source links: `color: #185FA5` — inline `<a href>` tag, no border or background
- Do NOT use hardcoded dark backgrounds anywhere

---

### Markdown output spec (`launch-monitor-{YYYY-MM-DD}.md`)

```markdown
# Launch Monitor — [Product Name]
**Launch date:** [DATE]
**Monitored window:** [DATE RANGE]
**Generated:** [TIMESTAMP]
**Total signals:** [N]

## TL;DR
[2-3 sentences: overall sentiment read, count of act-now items, single most urgent signal or mischaracterization]

## Summary
- Act now: [N] | Monitor: [N] | Good signals: [N] | Noise: [N]
- Mischaracterizations found: [N]
- Competitor moves: [N]
- Overall sentiment: [Positive / Mixed / Negative / Trending negative]

## Signal Feed

### 🔴 Act Now
- **[RESPOND/CORRECT/ESCALATE]** | [Signal type] | [Headline]
  Context: [One sentence]
  Source: [outlet] · Reach: [estimate] · [Time since launch]
  Action: [Suggested action]

### 🟡 Monitor
...

### 🟢 Good Signals
...

## Mischaracterizations
| Claim | Source | Reach | Correct version | Status |
|---|---|---|---|---|
| [What was said] | [Source] | [Reach] | [Accurate version] | SPREADING/CONTAINED |

## Competitor Moves
- **[Competitor]:** [What they did] — [Suggested counter-move]

## Source Index
- [URL] | [Source] | [Date] | [Urgency] | [Action]

## What This Means
[2-3 sentences: what the signal pattern implies for launch trajectory; the single most important action for the team to take right now]
```

---

## Saved preferences

After onboarding, ask once:
> "Would you like me to save your preferences so I skip the questions next time? You can always say **'change settings'** to update anything."

Store: product name(s), key competitors, launch window preference, depth setting.

---

## Distribution

After output is rendered inline and files are saved, offer sharing following `references/memory-and-distribution.md` (connector detection, `AskUserQuestion` flow, Notion/Slack options).

Skill-specific routing: push `launch-monitor-{YYYY-MM-DD}.md` to Notion (full report); post Act Now signals only to Slack. Use destination from `integrations` in `~/.nimble/business-profile.json` if set; otherwise ask and save for next time.

---

## Re-run behavior

For date window calculation, follow the Smart Date Windowing pattern in `references/nimble-playbook.md` — use `last_runs.launch-monitor` from the profile.

If the user asks to re-run or refresh monitoring:
> "I'll sweep for new signals since [last run timestamp] and update the war room. Anything new to add to the watch list?"

Only surface net-new signals since last run. Carry forward unresolved mischaracterizations and open action items.

---

## Related skills — next steps

After delivering the war room, suggest relevant next steps in the `## What This Means` section:

- **Ongoing brand monitoring:** Once the active launch window closes (typically 2–4 weeks post-launch), suggest handing off to `brand-mention-monitor` for continuous brand health tracking — it is optimized for steady-state monitoring rather than launch spikes.
- **Competitor follow-up:** If competitors made significant moves during the launch window, suggest `competitor-intel` for deeper, ongoing competitive intelligence — it tracks messaging, positioning shifts, and counter-narrative development over time.
- **Consumer sentiment:** If the product is consumer-facing and early usage data is accumulating, suggest `consumer-sentiment-monitor` to track how real users are experiencing the product beyond the launch press cycle.

---

## Materiality threshold

Skip signals that are:
- Clearly about a different product with the same name (filter via context profiling)
- Automated bots or spam accounts
- Duplicate coverage with no new information (syndicated wire copy)
- Single-digit reach with no amplification potential

Flag but don't prioritize:
- Neutral coverage that accurately describes the product
- Positive signals that need no action

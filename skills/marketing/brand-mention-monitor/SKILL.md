---
name: brand-mention-monitor
description: |
  Scans Reddit, X, LinkedIn, Instagram, TikTok, YouTube, blogs, news, and review platforms
  for brand mentions — scoring each one across four dimensions (reach, velocity, sentiment,
  and risk-topic match) so marketing teams can respond before a mention spirals. Source
  selection is market- and company-specific: B2B SaaS brands get weighted coverage of
  LinkedIn, G2, HN, and trade press; consumer brands get TikTok, Instagram, X, and YouTube.
  Every mention is bucketed into Crisis / Watch / Engage / Log with a suggested owner and
  response window. Powered by Nimble.

  Use when asked to "monitor brand mentions", "scan for brand mentions", "what are people
  saying about [brand]", "brand monitoring", "social listening", "run a brand sweep",
  "find high-risk mentions", or any variation of brand monitoring across web and social.

  Do NOT use for one-time company research or due diligence — use company-deep-dive instead.
  Do NOT use for competitor messaging/positioning analysis — use competitor-positioning instead.
  Do NOT use for funding/hiring/business signals on a competitor — use competitor-intel instead.
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
  - Agent
  - AskUserQuestion
metadata:
  author: Nimbleway
  version: 0.25.0
---

# Brand Mention Monitor

Scans the web and social media for brand mentions, scores each one on reach, velocity, sentiment, and risk-topic match, and surfaces the ones that need attention — bucketed into Crisis / Watch / Engage / Log with a suggested owner.

---

## Onboarding message

When this skill is triggered for the first time in a session, send this message:

> 👋 **Brand Mention Monitor is ready.**
>
> This skill scans Reddit, X, LinkedIn, Instagram, TikTok, YouTube, blogs, news, and review platforms for mentions of your brand — scoring each one across reach, velocity, sentiment, and risk so you see what matters before it spirals, and telling you exactly who should respond and how fast.
>
> To start, just say:
> _"Monitor mentions of [brand name]"_
>
> Or try:
> - "What are people saying about [brand] this week?"
> - "Run a brand sweep for [brand] — last 30 days"
> - "Find high-risk mentions of [brand]"
> - "How does [brand] compare to [competitor] in the conversation?"
>
> Would you like me to save your preferences so I skip the questions next time?

---

## Preflight

Follow the transport selection and standard preflight from `references/nimble-playbook.md`: pick CLI vs MCP at session start, then run the parallel preflight calls (date, profile, memory index) simultaneously. Tag every Nimble CLI call: `nimble --client-source skill-brand-mention-monitor <subcommand>`.

From the profile (`~/.nimble/business-profile.json`): load brand name, competitors, routing preferences, and `last_runs.brand-mention-monitor` for date windowing. Pre-populate setup questions so the user confirms rather than re-enters. If no profile exists, follow the first-run onboarding flow in `references/profile-and-onboarding.md` and create a stub after the first run. Check `~/.nimble/memory/index.md` to understand what mention data already exists before sweeping.

---

## How to start

**Before asking anything, do two quick research steps:**

**Step A — Resolve brand variants automatically:**
Search for the brand the user named to discover all alternate spellings, hashtags, product names, handles, and common misspellings. Do not ask the user for this. Use what you find to build a comprehensive search term list for the sweep.
- Search: `"[brand name]" official name OR handle OR "also known as" OR hashtag`
- Check the brand's main product names and any sub-brands that get mentioned independently
- For brands with common-word names, find the disambiguating terms (industry, founder, domain) so the sweep doesn't pull unrelated noise
- Add all confirmed variants to your search queries silently — the user never needs to see this step

**Step B — Profile the brand automatically:**
Search to establish the brand's industry, business model (B2B/B2C), geography, language, and audience before asking the user. This selects the market-specific source profile (see Step 0) and calibrates scoring — what counts as "high reach" differs for a niche B2B tool vs a consumer app with millions of users. Surface what you find and fold it into the confirmation question rather than asking blind.
- Search: `"[brand name]" company OR product industry OR category`
- Determine: B2B vs B2C, industry vertical, primary geography/language, rough audience size
- Use this to pick the source profile and the default risk-topic dictionary for the industry

**Then ask in a single message:**

> "Before I run — just confirming a few things:
> 1. **Brand:** I found [brand] — a [category] [B2B/B2C] company targeting [audience]. Is that right, and any competitors to track alongside it?
> 2. **Date range:** How far back should I look? (default: last 7 days — or give me a window like 'June 1–15' or 'since the launch')
> 3. **Depth:** Quick scan (faster) or deep sweep (more thorough, more sources)? (default: deep)
> 4. **Routing:** When I find a Crisis-tier mention, who should I flag it for? (default: marketing team — or name a PR lead, legal, founder, etc.)"

**Output is always the triage console rendered directly in Claude.** Do not ask about format or output options.

**Exceptions — skip asking entirely if:**
- The user provided all the above in their initial message
- The user has run this skill before in the session (use prior config)

**Defaults if user says "just run it":**
- Date range: last 7 days
- Depth: deep
- Risk topics: auto-detected for the industry
- Routing: flag to marketing team

**Disambiguation:** If the brand name is ambiguous after research, confirm before proceeding:
> "Just to confirm — by [brand], do you mean [Option A] or [Option B]?"

---

## Step 0 — Source profile (market-specific, not fixed list)

**This is the most important configuration step.** Source selection must match where the brand's audience actually talks. Do not scan all platforms equally — weight the channels that matter for this company type.

### B2B enterprise software / SaaS
**Primary (run every pass):** LinkedIn, G2, Capterra, Hacker News, r/sysadmin, r/devops, r/[category], trade press (InfoQ, TechCrunch, ZDNet, The Register), Glassdoor (employee signal)
**Secondary:** Reddit broad, X/Twitter (exec accounts, analysts), Medium/Substack
**Deprioritize:** TikTok, Instagram, Facebook (low-signal for B2B buyers)

### Consumer brand / e-commerce
**Primary (run every pass):** TikTok, Instagram, X/Twitter, Reddit, YouTube, Facebook, Trustpilot, Google Play / App Store
**Secondary:** News press, blogs, Pinterest
**Deprioritize:** HN, LinkedIn (low signal for consumer sentiment), trade press

### Regulated industry (finance, healthcare, pharma, insurance)
**Primary:** News press (Reuters, AP, Bloomberg, sector-specific), regulatory watchdog sites, journalist Twitter accounts, LinkedIn exec commentary, formal review platforms (BBB, Consumer Financial Protection Bureau)
**Secondary:** Reddit, X, forums
**Deprioritize:** TikTok, Instagram (reputational risk from user-gen content is lower priority than press/regulatory)

### Regional / non-English brand
**Primary:** Local-language news, regional forums and social platforms (e.g. Weibo for China, VK for Russia, Naver for Korea), local-language Twitter/Instagram
**Secondary:** English-language global platforms only if relevant
**Note:** Use Nimble `locale` and `country` parameters to surface local-language results

### Startup / developer tool
**Primary:** HN, Reddit (r/programming, r/webdev, r/[category]), GitHub discussions, Dev.to, X/Twitter (developer influencers), ProductHunt
**Secondary:** LinkedIn, Medium, TechCrunch

---

## Step 1 — Mention sweep

For deep sweeps, fan out across source tiers using parallel sub-agents (max 4 concurrent) via the `Agent` tool — one agent per source group (e.g., social, review platforms, news, community). Follow the parallel-gathering pattern in `references/nimble-playbook.md`. Always include a fallback: if a sub-agent fails, continue with remaining agents and note the gap in the output.

Run sources matching the brand's profile (Step 0). Use `--search-depth lite` for discovery; use `--search-depth deep` for full content on high-score candidates. Apply `--start-date` / `--end-date` from the user's date range on every search call. Tag every call: `nimble --client-source skill-brand-mention-monitor search ...`

### Core queries (run for every brand type)
- `"[brand name]" site:reddit.com`
- `"[brand name]" site:x.com`
- `"[brand name]" news`
- `"[brand name]" review OR complaint OR "doesn't work"` — risk sweep
- `"[brand name]" love OR recommend OR "game changer"` — opportunity sweep
- Nimble `focus:"social"` query `"[brand name]"` — broad social

### Risk-specific queries (run every pass)
Build from the risk topic dictionary for this brand type plus any user-specified topics:
- `"[brand name]" [risk topic 1]`
- `"[brand name]" [risk topic 2]`
- `"[brand name]" lawsuit OR legal OR "class action"`
- `"[brand name]" outage OR "not working" OR down` (for SaaS/tech)
- `"[brand name]" recall OR safety OR "side effects"` (for consumer/pharma)
- `"[brand name]" scam OR fraud OR fake`

### Velocity check (run on high-score candidates — re-runs only)
For any mention that scored above 50 on a previous run, re-fetch the post to compare engagement counts. If this is a first-pass sweep with no prior baseline, skip hourly-rate velocity scoring — proxy signals only (see Step 2 velocity gating rules).

---

## Step 2 — Scoring each mention (four dimensions)

Score every mention 0–100 on each dimension, then compute composite.

### Reach / Visibility (0–100)
How many people can see this?
| Signal | Points |
|---|---|
| 500K+ followers / major publication | +35 |
| 100K–500K followers | +25 |
| 10K–100K followers | +15 |
| 1K–10K followers | +8 |
| Under 1K | +3 |
| Thread with 100+ replies/comments | +20 |
| Post going viral (100+ reposts in <1h) | +25 |
| High-authority domain (TechCrunch, Reuters, etc.) | +25 |
| Reddit front page / 1K+ upvotes | +25 |

### Velocity (0–100) — the differentiator
How fast is this gaining ground? This is what separates "viral forming" from "stale."

**Baseline requirement:** Hourly-rate rows (+40/+25/+10) require two data points — a prior engagement count and the current count — to compute a real rate. On a first-pass single sweep you do not have a baseline. Apply the following rules:
- **Re-run with prior data (baseline available):** use the full table below.
- **First-pass single sweep (no baseline):** skip hourly-rate rows; score only observable proxy signals (cross-platform pickup, press pickup, absolute engagement thresholds). Set velocity label to `~estimated` on the card so the user knows it is inferred, not measured.

| Signal | Points | Requires baseline? |
|---|---|---|
| Engagement climbing 50%+/hour vs. baseline | +40 | Yes |
| Engagement climbing 20–50%/hour | +25 | Yes |
| Engagement climbing 5–20%/hour | +10 | Yes |
| Flat engagement | +0 | Yes |
| Cross-platform pickup (mention appearing on 2+ platforms) | +20 | No |
| Press picking up a social post | +25 | No |
| 2.3K+ reposts in 40 minutes (crisis velocity) | +40 | No — observable in single sweep |

**Tier upgrade on rapid re-check:** if re-running within 2 hours of a previous run, re-fetch every mention that scored Watch or higher and compare engagement counts. If engagement has grown 20%+ since last check, upgrade the tier and flag it `↑ accelerating`. If flat or declining, note `→ stable` or `↓ declining`.

### Sentiment (0–100 risk score; 0–100 opportunity score)
| Negative signals (risk) | Points |
|---|---|
| Explicit negative sentiment | +20 |
| Complaint + product/service failure language | +20 |
| Sarcasm detected ("great job [brand]…") | +15 |
| All-caps, exclamation marks, profanity | +10 |
| Replies amplifying the negative tone | +15 |
| Positive signals (opportunity) | Points |
| Organic praise, unprompted | +20 |
| Purchase intent or recommendation | +20 |
| User-generated content shareable by brand | +15 |
| Journalist / analyst positive mention | +20 |

### Risk topic match (0–100)
Does this hit a flagged risk category?
| Topic category | Points |
|---|---|
| Legal / regulatory / lawsuit / class action | +40 |
| Safety / health / injury / recall | +40 |
| Executive misconduct or controversy | +35 |
| Product outage or critical failure | +30 |
| Pricing / billing complaint (if viral) | +20 |
| Competitor comparison framing brand negatively | +15 |
| False claim / misinformation about brand | +25 |

### Composite score
`composite = (reach × 0.30) + (velocity × 0.30) + (max(risk_sentiment, risk_topic) × 0.25) + (opportunity × 0.15)`

---

## Step 2.5 — Memory dedup (filter already-known mentions)

Before assigning tiers, run the dedup lifecycle from `references/memory-and-distribution.md` against prior brand-mention-monitor reports in `~/.nimble/memory/reports/`.

Skill-specific rules:
- **Fingerprint:** `{url, platform, published_date}` — normalize URLs (strip query params, trailing slashes).
- **Returning with score shift ≥10:** keep in feed, mark with `↩ returning · score changed` badge.
- **Already known, score unchanged:** move to Log tier; suppress from Crisis/Watch/Engage unless user requested full history.
- **Summary line:** show at top of triage console: `X net-new · Y returning (score changed) · Z suppressed (already logged)`.
- **Persist:** after the run, save mention fingerprints to `~/.nimble/memory/reports/brand-mention-monitor-{BRAND}-{YYYY-MM-DD}.md` and append a `log.md` entry per `references/memory-and-distribution.md`.

---

## Step 3 — Tier assignment and routing

Assign every mention to exactly one tier. Teams act on tiers, not numbers.

| Tier | Score | Color | Action | Suggested owner | Window |
|---|---|---|---|---|---|
| Crisis | 80–100 | 🔴 | Route immediately | PR + Legal + Leadership | Respond <2h |
| Watch | 50–79 | 🟠 | Assign owner, monitor velocity | Marketing / Comms | Respond <24h |
| Engage | Any score, positive high-reach | 🟢 | Amplify / thank / share | Marketing / Social team | Act within 48h |
| Log | <50, no risk signals | ⚪ | No action, searchable record | — | — |

**Crisis-tier mentions must surface immediately** — they should appear at the very top of the output with a full decision card showing: excerpt, reach, velocity, reason for flagging, suggested owner, response window, and suggested draft action.

---

## Output template (REQUIRED)

Claude MUST follow `references/template.html` exactly. Load the template, substitute real data, keep all CSS, JS, and interaction patterns identical.

### Response structure (wrap the widget)

The chat response must follow the standard contract: open with a **TL;DR** and close with a **What This Means** section, with the triage console in between.

1. **TL;DR** (first, 2–4 lines): total mentions, the tier breakdown (`X Crisis · Y Watch · Z Engage`), and the single most urgent item with its response window.
2. **The triage console** — the interactive widget, rendered inline per the rules below.
3. **What This Means** (final top-level section): what the sweep signals for the brand right now and the top 1–3 recommended actions, each tied to a tier and owner.

### Rendering — INLINE FIRST, ALWAYS (read this before producing output)

The triage console is an **interactive widget that must be rendered inline in the chat**. A downloadable file is a *secondary* artifact, never the primary deliverable. Follow this sequence exactly, every run:

1. **Render the triage console inline FIRST.** Write the fully-populated `brand-mention-monitor-{YYYY-MM-DD}.html` to `~/.nimble/` using the Write tool, then emit the HTML content inline in the conversation so the user sees the interactive widget immediately. This inline output is the main deliverable and must happen before anything else is offered.
2. **Then, and only then, offer downloads.** After the inline output is on screen, confirm that `~/.nimble/brand-mention-monitor-{YYYY-MM-DD}.html` and `~/.nimble/brand-mention-monitor-{YYYY-MM-DD}.md` have been saved and offer them to the user for download or sharing.

**Hard rules:**
- **Never** respond with only a file path. If the user sees a path but no inline triage console, the run has failed its primary job.
- **Do not ask** the user whether they want it inline or as a file, and do not ask about format — inline is always the default and the file always accompanies it.
- The inline output and the saved HTML are the **same artifact** — render the identical template, do not produce a stripped-down inline version.

**If the inline output genuinely cannot be produced:**
1. Say so explicitly in one short line — e.g. "I couldn't render the triage console inline this time, so here's the file instead."
2. Confirm the file has been saved to `~/.nimble/brand-mention-monitor-{YYYY-MM-DD}.html` as the fallback.

Never silently fall back to a file — if inline fails, name the failure so the user knows it was the environment, not the intended behavior.

### Output template spec (`brand-mention-monitor-{YYYY-MM-DD}.html`)

**Visual identity — distinct from all other skills:**
- Triage console aesthetic — dense, action-oriented, not a report
- Crisis-tier mentions get a full-width alert card at the top before the feed
- Four score pips per card: Reach / Velocity / Sentiment / Risk — not just one urgency signal
- Tier badge replaces composite number as the primary visual label
- Sources searched panel (collapsible) showing exactly what was queried this run
- Date range picker (custom From/To date inputs) that re-filters the feed client-side
- Platform filter + Tier filter stacked
- Velocity indicator on each card: `↑ accelerating` / `→ stable` / `↓ declining`

**Score pip colors:**
- Reach: `#185FA5` (blue)
- Velocity: `#854F0B` (amber — urgency signal)
- Sentiment: `#A32D2D` (red for risk) / `#3B6D11` (green for opportunity)
- Risk topic: `#A32D2D` (red)

**Tier colors:**
- Crisis 🔴: red left border + red tier badge
- Watch 🟠: amber left border + amber tier badge
- Engage 🟢: green left border + green tier badge
- Log ⚪: gray border

**Required sections (in this render order):**
1. Brand header bar — brand name · date range (from onboarding, read-only label e.g. "Window: Jun 11–18, 2026") · total mentions
2. Sources searched — collapsible panel showing every source queried this run with ✓ marks + mention-count badges; click a source to filter the feed by platform
3. Score summary row — four aggregate meters: avg Reach / top Velocity / top Sentiment risk / top Opportunity
4. Market visibility (share of voice) — donut chart (white center) + legend showing the brand's share of conversations vs competitors in this window. Hovering a segment or legend row highlights it and shows that brand's share in the donut center. CLICKING a segment or row opens a detail panel with critical intelligence for that brand: mention count, trend vs last window (color-coded red rising / green falling), estimated reach, a positive/neutral/negative sentiment split bar, and a one-line Signal takeaway explaining what's driving that brand's share. Use `mvBrands[]`: first entry is the user's brand; each entry is `{name, pct, fill, stroke, mentions, trend, reach, pos, neu, neg, signal}`. Percentages sum to ~100 (include an "Other" bucket); pos+neu+neg sum to 100.
5. Crisis alert cards — full-width, only shown if tier = Crisis; includes excerpt, all 4 scores, published date, reason, owner, window, suggested action
6. Mentions by platform — horizontal bars, clickable to filter feed (synced with sources panel)
7. Geographic breakdown — interactive world map with mention hotspots. Use `geoPoints[]`: each point `{name, lat, lng, tier, sources}` where tier is 'high'/'med'/'low' (drives dot color red/amber/blue, size, pulse ring on high-tier). Mention count is derived from the length of `sources`. Each entry in `sources` is `{head, plat, meta, url, tier}` — head = headline, plat = platform key, meta = followers/upvotes and date, tier = that mention's own tier, and url MUST be the EXACT Nimble result URL (article/post/thread), never a homepage. Hovering a point shows a summary tooltip; CLICKING pins a detail panel below the map listing every source from that location with an open link to the exact URL. Map geometry loads from world-atlas via D3 (jsDelivr/unpkg/cdnjs fallbacks; shows "Map unavailable" if all blocked). lat/lng = country centroid.
8. Mention feed (2-column grid) — sorted by composite score, each card with 4 score pips + tier badge + velocity arrow + platform tag + publish date + source link
9. Filter bar — Tier (All / Crisis / Watch / Engage / Log) + Score range, stacked with dismissable chips

**Interaction:**
- Click any card to expand: full quote, score breakdown explaining each score, routing suggestion, suggested action text
- Click "Sources searched" header to expand/collapse the sources panel; click a source row to filter the feed by platform
- Market visibility donut: hover a segment or legend row to highlight and preview share; click to open the detail panel with that brand's mentions, trend, reach, sentiment split, and signal
- Platform bars clickable to filter feed (synced with sources panel)
- Geographic map: hover a hotspot for the summary; click it to pin a panel listing the exact sources (with open links) from that location
- All filters stack with dismissable chips

**Visualization libraries:**
The template loads D3 (`d3.min.js`) and topojson (`topojson.min.js`) from cdnjs for the geographic map, plus world-atlas country geometry from jsDelivr/unpkg/cdnjs (with fallbacks). The market visibility donut uses a plain `<canvas>` with no dependency. Keep these script tags.

**Source URL rule:**
Every mention must include `<a href="[EXACT_NIMBLE_URL]" class="src-link">↗ source</a>` with the exact article/post URL from Nimble. Never use a homepage.
- CORRECT: `https://reddit.com/r/SaaS/comments/abc123/title`
- CORRECT: `https://x.com/username/status/1234567890`
- WRONG: `https://reddit.com`  WRONG: `https://x.com`

---

### Markdown output spec (`brand-mention-monitor-{YYYY-MM-DD}.md`)

```markdown
# Brand Mention Monitor — [Brand Name]
**Date range:** [DATE RANGE]
**Generated:** [TIMESTAMP]
**Total mentions:** [N]
**Sources searched:** [list]

## TL;DR
[2–4 lines: total mentions · tier breakdown (X Crisis · Y Watch · Z Engage) · the single most urgent item + its response window]

## Crisis tier (80–100) — respond <2h
- **[Tier] Score:[N]** | [Platform] | [Author] | R:[N] V:[N] S:[N] RT:[N]
  "[Excerpt]"
  Owner: [PR/Legal/Marketing] · Window: <2h
  Action: [Suggested action]
  Source: [EXACT_NIMBLE_URL]

## Watch tier (50–79) — respond <24h
...

## Engage tier — amplify within 48h
...

## Log (no action required)
...

## What This Means
[What the sweep signals for the brand right now + the top 1–3 recommended actions, each tied to a tier and owner]
```

---

## Source URL rule

Every mention must include the exact Nimble result URL.
**CORRECT:** `https://reddit.com/r/SaaS/comments/abc123/title`
**WRONG:** `https://reddit.com`

---

## Distribution

After output is rendered inline and files are saved, offer sharing following `references/memory-and-distribution.md` (connector detection, `AskUserQuestion` flow, Notion/Slack options).

Skill-specific routing: push `brand-mention-monitor-{YYYY-MM-DD}.md` to Notion (full report); post Crisis + Watch tiers only to Slack (not the full feed). Use destination from `integrations` in `~/.nimble/business-profile.json` if set; otherwise ask and save for next time.

---

## Saved preferences

After first run, ask:
> "Save preferences? I'll remember [brand], source profile, risk topics, and routing so future runs skip setup."

Say **"change settings"** to update anytime.

---

## Re-run behavior

For date window calculation, follow the Smart Date Windowing pattern in `references/nimble-playbook.md` — use `last_runs.brand-mention-monitor` from the profile.

> "Sweeping for new mentions since [last run]. Anything to add to the watch list?"

Net-new mentions only. Crisis and Watch items carry forward until marked handled.

---

## End-of-run next steps

After delivering the triage console and confirming distribution, suggest the most relevant follow-on action based on what the sweep surfaced:

- **If any Watch or Crisis mentions came from competitors framing your brand negatively:** → "Want to go deeper on what competitors are saying about you? Try the `competitor-positioning` skill — it maps competitor messaging, positioning gaps, and attack vectors in detail."
- **If the brand appeared in funding, hiring, or M&A context:** → "There are signals here that go beyond brand sentiment — the `competitor-intel` skill tracks business moves, hiring signals, and strategic shifts that could affect your market position."
- **If the sweep found mostly positive mentions worth amplifying:** → "Some of these are worth turning into content or outreach — the `competitor-positioning` skill can help you identify the messaging angles your audience is already responding to."
- **If this is the first run (no prior memory):** → "Run this again in 7 days to get velocity data and start seeing trends. I'll have a baseline for comparison on the next pass."

Present only the suggestions relevant to this run — do not list all four if only one applies.

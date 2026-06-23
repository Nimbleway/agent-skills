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

  Do NOT use for one-time company research or due diligence on a specific company.
allowed-tools:
  - Bash(nimble:*)
  - Bash(date:*)
  - Read
  - Write
metadata:
  author: Nimbleway
  version: 0.23.0
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

## Nimble setup

This skill uses Nimble for all web research — review platform searches, social sweeps, news extraction, and competitor monitoring. Nimble is a built-in connector in Claude — no account or API key needed.

**Check for Nimble before starting:**
When the skill is first triggered, verify Nimble is available by attempting a simple `nimble_search` call. If it fails or is unavailable, pause and guide the user to enable it before doing anything else:

> "This skill uses Nimble to search and extract brand mentions from Reddit, X, LinkedIn, Instagram, TikTok, YouTube, review sites, blogs, and news. It looks like Nimble isn't enabled yet — here's how to turn it on: Nimble is a built-in Claude connector that gives this skill accurate, real-time search and extraction across sites that standard AI agents cannot access — including paywalled news, review platforms, social media, and JavaScript-heavy pages."

**How to enable Nimble:**
1. In Claude, open **Settings → Connectors** (or the connected apps/tools panel)
2. Find **Nimble** in the list and toggle it on
3. That's it — no account or API key required
4. Once enabled, confirm by saying "Nimble is on" and Claude will proceed

Do not attempt the mention sweep until Nimble responds normally. If Nimble is already enabled (the MCP tool responds normally), skip this section entirely — do not mention it.

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

Run sources matching the brand's profile (Step 0). Use `search_depth: "lite"` with `include_answer: true` for discovery. Use `search_depth: "deep"` for full content on high-score candidates.

Apply `start_date` and `end_date` parameters from the user's specified date range to every Nimble search query.

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

### Velocity check (critical — run on high-score candidates)
For any mention that scores above 50 on initial pass, check engagement velocity:
- Fetch the current engagement count
- Compare to a re-fetch 30–60 minutes later if re-running, or estimate from post age vs. current engagement
- Flag as "accelerating" if engagement rate exceeds category baseline

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
| Signal | Points |
|---|---|
| Engagement climbing 50%+/hour vs. baseline | +40 |
| Engagement climbing 20–50%/hour | +25 |
| Engagement climbing 5–20%/hour | +10 |
| Flat engagement | +0 |
| Cross-platform pickup (mention appearing on 2+ platforms) | +20 |
| Press picking up a social post | +25 |
| 2.3K+ reposts in 40 minutes (crisis velocity) | +40 |

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

### Rendering — INLINE FIRST, ALWAYS (read this before producing output)

The triage console is an **interactive widget that must be rendered inline in the chat**. A downloadable file is a *secondary* artifact, never the primary deliverable. Follow this sequence exactly, every run:

1. **Render the triage console inline FIRST.** Take the fully-populated `brand-mention-monitor-{YYYY-MM-DD}.html` and render it directly into the conversation as an interactive widget using the visualizer / canvas rendering tool. This inline render is the main deliverable and must happen before anything else is offered.
2. **Then, and only then, offer downloads.** After the inline widget is on screen, additionally save `~/.nimble/brand-mention-monitor-{YYYY-MM-DD}.html` and `~/.nimble/brand-mention-monitor-{YYYY-MM-DD}.md` and offer them as downloadable files for the user to keep or share.

**Hard rules:**
- **Never** respond with only a download link or only a file. If the user sees a file but no inline triage console, the run has failed its primary job.
- **Do not ask** the user whether they want it inline or as a file, and do not ask about format — inline is always the default and the file always accompanies it.
- The inline widget and the downloadable HTML are the **same artifact** — render the identical template, do not produce a stripped-down inline version.

**If the inline render genuinely cannot be produced** (e.g. the rendering/visualizer tool is unavailable or returns an error in this environment):
1. Say so explicitly in one short line — e.g. "I couldn't render the interactive triage console inline this time (the rendering tool didn't respond), so here's the file instead."
2. Then provide the downloadable `~/.nimble/brand-mention-monitor-{YYYY-MM-DD}.html` as the fallback.
3. Briefly note that re-running once the rendering tool is available will show it inline.

Never silently fall back to a download — if inline fails, name the failure so the user knows it was the environment, not the intended behavior.

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
```

---

## Source URL rule

Every mention must include the exact Nimble result URL.
**CORRECT:** `https://reddit.com/r/SaaS/comments/abc123/title`
**WRONG:** `https://reddit.com`

---

## Saved preferences

After first run, ask:
> "Save preferences? I'll remember [brand], source profile, risk topics, and routing so future runs skip setup."

Say **"change settings"** to update anytime.

---

## Re-run behavior

> "Sweeping for new mentions since [last run]. Anything to add to the watch list?"

Net-new mentions only. Crisis and Watch items carry forward until marked handled.

---

## Velocity re-check

If re-running within 2 hours of a previous run:
- For every mention that scored Watch or higher on the previous run, re-fetch the post to check current engagement
- If engagement has grown 20%+ since last check, upgrade tier and flag as "accelerating ↑"
- If engagement is flat or declining, note "stable →" or "declining ↓"

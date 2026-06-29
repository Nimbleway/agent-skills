# Source query templates — Launch Monitor

Launch monitoring requires speed and precision. Run sources in this order: highest-reach first, then community, then niche. For search depth, time windowing, and transport selection (CLI vs MCP), follow `references/nimble-playbook.md` — those mechanics are not restated here. Tag every CLI call: `nimble --client-source skill-launch-monitor search …`

---

## Tier 1 — High-reach press (run first)

These outlets have the widest reach and the highest chance of mischaracterizations spreading to secondary coverage. Check these within the first hour of any run.

- `"[product name]" site:techcrunch.com`
- `"[product name]" site:theverge.com`
- `"[product name]" site:wired.com`
- `"[product name]" site:arstechnica.com`
- `"[product name]" site:venturebeat.com`
- `"[product name]" site:siliconangle.com`
- `"[product name]" site:theregister.com`
- `"[product name]" site:zdnet.com`
- `"[product name]" site:bloomberg.com` (via Nimble)
- `"[product name]" site:reuters.com`
- `"[product name]" "[company name]" announcement OR launch OR release`

**Category-specific press** — add based on context profile:
- Developer tools / APIs: `site:infoq.com`, `site:sdtimes.com`, `site:thenewstack.io`
- AI/ML: `site:theinformation.com`, Import AI newsletter, The Batch
- Enterprise SaaS: `site:cio.com`, `site:computerworld.com`
- Consumer: `site:mashable.com`, `site:engadget.com`

---

## Tier 2 — Community & developer forums (run in parallel with Tier 1)

Community threads move fast and often contain the most honest reactions — including mischaracterizations that spread to press.

### Hacker News
- `"[product name]" site:news.ycombinator.com`
- Also search directly: `hn.algolia.com/?q=[product+name]&dateRange=last24h`
- Signal: threads with 50+ comments are high-priority. Check for top comments with wrong claims.

### Reddit
- `"[product name]" site:reddit.com`
- Target: `r/[product name]`, `r/[category]`, `r/programming`, `r/MachineLearning`, `r/SaaS`, `r/entrepreneur`, `r/webdev`, `r/devops`
- Signal: "I'm disappointed" or "this is actually X not Y" comment threads

### Dev communities
- `"[product name]" site:dev.to`
- `"[product name]" site:hashnode.com`
- `"[product name]" site:stackoverflow.com`
- `"[product name]" site:github.com discussions`

### Discord / Slack
- Search for official Discord server or community Slack
- `"[product name]" discord`
- Signal: early community feedback before it surfaces publicly

---

## Tier 3 — Social (real-time volume and influencer signals)

### X / Twitter
- `"[product name]" site:x.com`
- `"[product name]" launch OR announced OR "just released" site:x.com`
- `"[product name]" wrong OR incorrect OR "actually it's" site:x.com` — targeted mischaracterization hunt
- Check: quote-tweets of the official announcement for corrections and reactions
- Signal: viral threads, influencer reactions, correction chains

### LinkedIn
- `"[product name]" site:linkedin.com`
- Signal: practitioner takes, exec reactions, competitive commentary

---

## Tier 4 — Competitor monitoring

Run these only if competitor monitoring is enabled.

### Competitor content
- `[competitor A] "[product name]" OR "[category keyword]"` — are they writing about your launch?
- `[competitor A] "compared to" OR "vs" OR "alternative"` — positioning content
- `[competitor A] site:twitter.com OR site:x.com` — real-time competitor reactions
- Check competitor blog/changelog for counter-announcements made within 48h of your launch

### Secondary coverage
- `"[product name]" "[wrong claim]"` — is a mischaracterization spreading to secondary sources?
- `"[product name]" site:reddit.com "[wrong claim]"` — community pickup of press errors

---

## Tier 5 — Mischaracterization-specific queries

These are designed specifically to surface wrong information. Run them every pass.

Build queries around the most likely inaccuracies based on context profiling:

- **Pricing mischaracterizations:** `"[product name]" pricing OR price OR "costs $"` — compare against actual pricing
- **Category confusion:** `"[product name]" "[wrong category]"` — e.g. if you're an API being called a "no-code tool"
- **Capability inflation:** `"[product name]" "[feature you don't have]"` — claims about capabilities you haven't launched
- **Capability deflation:** `"[product name]" "only" OR "just" OR "limited to"` — underselling what it does
- **Wrong comparisons:** `"[product name]" vs "[wrong competitor]"` — being compared to unrelated products
- **Attribution errors:** `"[product name]" "[wrong company name]"` — if press misattributes ownership

---

## Re-run cadence

- First 6h post-launch: run every 1-2h
- 6h–24h: run every 3-4h
- After 24h: run once or twice daily until momentum dies
- Always note timestamp of last run so re-runs only surface net-new signals

---

## Tier 6 — Consumer & app-specific sources

Run these for consumer product launches (apps, hardware, consumer software). Less relevant for B2B/developer tools.

### YouTube
- `"[product name]" review OR "hands on" OR reaction site:youtube.com`
- `"[product name]" "[company name]" launch OR announcement site:youtube.com`
- Signal: high-view reaction videos within 48h are a major sentiment signal; comment sections surface consumer concerns fast

### App Store (Apple)
- `"[product name]" site:apps.apple.com`
- Search directly for the app and check recent reviews tab
- Signal: 1-star reviews after an update often signal a feature regression; version-specific complaints surface before they hit press

### Google Play
- `"[product name]" site:play.google.com`
- Signal: same as App Store — Android-specific issues often surface here first

### TikTok / Instagram Reels
- `"[product name]" site:tiktok.com`
- Signal: viral consumer reaction videos; for consumer hardware/software launches these can reach audiences larger than any press outlet

### Podcasts
- `"[product name]" podcast OR episode site:open.spotify.com OR site:podcasts.apple.com`
- Signal: major tech podcasts (Hard Fork, Acquired, All-In, Lenny's Podcast) can significantly shape narrative for consumer products

### Product Hunt
- `"[product name]" site:producthunt.com`
- Signal: launch day upvotes and comments; "alternatives to" pages; maker response patterns

### Forums (consumer-specific)
- For Apple products: `"[product name]" site:forums.macrumors.com OR site:9to5mac.com OR site:appleinsider.com`
- For Android: `site:androidpolice.com`, `site:9to5google.com`
- For gaming: `site:resetera.com`, `site:reddit.com/r/gaming`
- For AI/consumer tech: `site:reddit.com/r/artificial`, `r/ChatGPT`, `r/singularity`

---

## Alternate name resolution — query patterns

Run these on Step A before asking the user anything:

- `"[product name]" codename OR "internal name" OR "project name"`
- `"[product name]" "formerly known as" OR "previously called" OR "rebranded"`
- `"[company name]" "[product category]" names OR versions 2025 OR 2026`
- For Apple: always search for both marketing name AND internal model identifier
- For AI products: check for API name, model name, and consumer-facing name separately — they're often different

---

## Tier 2b — Social media (explicit platform queries)

Run these in parallel with Tier 2. Social moves fast — these should be swept every pass, not just on the first run.

### Reddit — broad + subreddit-specific
Run all of these, not just one:
- `"[product name]" site:reddit.com` — broad sweep
- `"[product name]" site:reddit.com/r/technology`
- `"[product name]" site:reddit.com/r/apple` (for Apple products)
- `"[product name]" site:reddit.com/r/android` (for Android/Google products)
- `"[product name]" site:reddit.com/r/artificial`
- `"[product name]" site:reddit.com/r/ChatGPT`
- `"[product name]" site:reddit.com/r/MachineLearning`
- `"[product name]" site:reddit.com/r/programming`
- `"[product name]" site:reddit.com/r/[category]` — category subreddit based on product type
- `"[product name]" site:reddit.com/r/[company name]` — brand subreddit if it exists
- Also use Nimble `focus:"social"` with query `"[product name]" reddit` for broader social signal sweep
- Signal: sort by "new" to catch real-time reaction; "top" to catch highest-reach threads; check comment counts for engagement depth

### X / Twitter
- `"[product name]" site:x.com`
- `"[product name]" launch OR announced OR released site:x.com`
- `"[product name]" wrong OR broken OR disappointed site:x.com` — complaint hunt
- `"[product name]" actually OR "turns out" OR correcting site:x.com` — correction chains
- Check quote-tweets of the official launch tweet — these are where mischaracterizations and reactions concentrate
- Signal: threads with 100+ likes within 24h; viral complaints; influencer takes; journalist corrections

### LinkedIn
- `"[product name]" site:linkedin.com`
- `"[product name]" launched OR announced OR "my take" site:linkedin.com`
- `"[company name]" "[product name]" site:linkedin.com`
- Signal: founder/exec posts, practitioner commentary, VC reactions, enterprise buyer takes — LinkedIn often has higher-quality signal than X for B2B products

### Instagram
- `"[product name]" site:instagram.com`
- Use Nimble `focus:"social"` with query `"[product name]" instagram` — Instagram blocks most direct search
- Signal: brand account engagement, influencer posts, consumer reaction reels, comment sentiment on official posts
- Especially valuable for consumer hardware, apps, and lifestyle products

### TikTok
- `"[product name]" site:tiktok.com`
- Use Nimble `focus:"social"` with query `"[product name]" tiktok review OR reaction OR hands-on`
- Signal: viral reaction videos within first 48h; comment sections surface raw consumer sentiment fast; high-view negative reactions can reach millions before press picks them up

### YouTube
- `"[product name]" review OR "hands on" OR reaction site:youtube.com`
- `"[product name]" "first look" OR "unboxing" OR "first impressions" site:youtube.com`
- `"[product name]" problems OR issues OR "doesn't work" site:youtube.com`
- Signal: view count within 48h; like/dislike ratio; comment themes; large tech channels (MKBHD, Linus, iJustine, etc.) shape mainstream consumer perception faster than most press

### Facebook
- `"[product name]" site:facebook.com`
- Use Nimble `focus:"social"` with query `"[product name]" facebook group`
- Signal: consumer product groups, brand pages, community reactions — strongest for mainstream consumer products and older demographics

### Threads (Meta)
- `"[product name]" site:threads.net`
- Signal: growing tech and creator community; often surfaces takes from journalists and creators before they publish formal coverage

### Pinterest / Reddit image communities
- For visual/hardware products: `"[product name]" site:pinterest.com`
- Signal: consumer enthusiasm for physical products; design reactions

---

## Nimble social search configuration

**Transport-agnostic.** Examples below are shown in CLI form. In MCP-only environments call `nimble_search` instead — drop the `--` and snake_case each flag (`--focus` → `focus`, `--search-depth` → `search_depth`, `--start-date`/`--end-date` → `time_range`). Pick the transport once at preflight per `references/nimble-playbook.md`.

For social media sweeps, use `--focus social` (CLI) or `focus="social"` (MCP) — Nimble's social mode surfaces posts and threads more effectively than plain web search. Apply the date window on every call. Use `--search-depth lite` for the discovery pass.

CLI example — social reaction sweep:
```bash
nimble --client-source skill-launch-monitor search \
  --query '"[product name]" reaction launch' \
  --focus social --search-depth lite \
  --start-date [YYYY-MM-DD] --end-date [YYYY-MM-DD]
```

CLI example — mischaracterization hunt on social:
```bash
nimble --client-source skill-launch-monitor search \
  --query '"[product name]" wrong OR incorrect OR "actually" OR "misleading"' \
  --focus social --search-depth lite \
  --start-date [YYYY-MM-DD] --end-date [YYYY-MM-DD]
```

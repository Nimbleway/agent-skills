# Source query templates — Brand Mention Monitor

Brand monitoring requires broad coverage across all platforms where your audience talks. Run sources in this order: social first (fastest to surface new mentions), then news, then review platforms.

Use `search_depth: "lite"` with `include_answer: true` for the discovery pass. Use `search_depth: "deep"` to extract full content for scoring high-impact mentions.

---

## Tier 1 — Social media (run first, every pass)

### Reddit
- `"[brand name]" site:reddit.com` — broad sweep
- `"[brand name]" site:reddit.com/r/[category]` — category subreddit
- `"[brand name]" site:reddit.com/r/[brand]` — brand subreddit if exists
- `"[brand name]" complaint OR issue OR problem site:reddit.com` — risk signals
- `"[brand name]" recommend OR love OR "switched to" OR "best" site:reddit.com` — opportunity
- `"[brand name]" vs OR alternative OR "compared to" site:reddit.com` — competitive
- Nimble `focus:"social"` query `"[brand name]" reddit`
- Signal: sort by "new" for recency, "top" for reach; threads with 100+ comments = high priority

### X / Twitter
- `"[brand name]" site:x.com` — broad
- `"#[brand]" site:x.com` — hashtag sweep
- `"[brand name]" angry OR disappointed OR broken OR "doesn't work" OR "worst" site:x.com` — risk
- `"[brand name]" love OR amazing OR "highly recommend" OR "can't believe" site:x.com` — opportunity
- `"[brand name]" OR "#[brand]" complaint OR refund OR scam site:x.com` — escalation risk
- Nimble `focus:"social"` query `"[brand name]" twitter recent`
- Signal: verified accounts, accounts with 10K+ followers, threads with 50+ replies

### LinkedIn
- `"[brand name]" site:linkedin.com`
- `"[brand name]" review OR feedback OR experience OR "working with" site:linkedin.com`
- `"[brand name]" CEO OR founder OR team site:linkedin.com` — exec commentary
- Signal: practitioner posts carry weight with B2B buyers; exec commentary shapes enterprise perception

### Instagram
- Nimble `focus:"social"` query `"[brand name]" instagram`
- Nimble `focus:"social"` query `#[brand] instagram`
- Nimble `focus:"social"` query `"[brand name]" instagram review OR unboxing OR haul`
- Signal: influencer posts, brand account engagement, comment sentiment, UGC reposting opportunities

### TikTok
- Nimble `focus:"social"` query `"[brand name]" tiktok`
- Nimble `focus:"social"` query `#[brand] tiktok review OR reaction OR honest`
- Nimble `focus:"social"` query `"[brand name]" tiktok made me buy`
- Signal: viral reaction content moves faster than press; high-view negative TikToks = urgent; "TikTok made me buy it" = high opportunity

### Facebook
- Nimble `focus:"social"` query `"[brand name]" facebook group`
- Nimble `focus:"social"` query `"[brand name]" facebook review`
- Signal: consumer and SMB brand communities; older demographic feedback

### Threads
- `"[brand name]" site:threads.net`
- Nimble `focus:"social"` query `"[brand name]" threads`

### YouTube
- `"[brand name]" review OR "honest review" OR "is it worth it" site:youtube.com`
- `"[brand name]" "don't buy" OR problems OR issues OR "I returned" site:youtube.com`
- `"[brand name]" unboxing OR "first impressions" site:youtube.com`
- Signal: view count + like ratio; major tech/lifestyle channels shape consumer decisions; negative reviews with 100K+ views = high risk

---

## Tier 2 — News & press

### General news
- `"[brand name]" news` — broad news sweep
- `"[brand name]" site:techcrunch.com OR site:theverge.com OR site:wired.com`
- `"[brand name]" site:businessinsider.com OR site:forbes.com OR site:bloomberg.com`
- `"[brand name]" site:reuters.com OR site:apnews.com`
- Category-specific press based on brand profiling (see Step 0)

### Hacker News
- `"[brand name]" site:news.ycombinator.com`
- `hn.algolia.com/?q=[brand+name]&dateRange=last24h`
- Signal: HN threads with 50+ comments reach a highly influential technical audience

### Blogs & newsletters
- `"[brand name]" site:medium.com`
- `"[brand name]" site:substack.com`
- `"[brand name]" blog review OR opinion OR "my experience"`
- Signal: long-form opinion pieces shape search results and reader perception over time

---

## Tier 3 — Review platforms

### G2
- `"[brand name]" site:g2.com reviews`
- Signal: new 1–3 star reviews = risk; score drop = risk; trending themes in cons section

### Trustpilot
- `"[brand name]" site:trustpilot.com`
- Signal: cluster of negative reviews in short window; response rate patterns

### Capterra / GetApp
- `"[brand name]" site:capterra.com`
- `"[brand name]" site:getapp.com`

### App Store / Google Play
- `"[brand name]" site:apps.apple.com` — for app products
- `"[brand name]" site:play.google.com` — for app products
- Signal: version-specific complaints; rating drops after update

### Product Hunt
- `"[brand name]" site:producthunt.com`
- Signal: launch day reactions; "alternatives to" pages; maker response tone

---

## Tier 4 — Opportunity-specific searches

Run these specifically to find high-opportunity mentions:

### Purchase intent
- `"[brand name]" "thinking of buying" OR "should I get" OR "is [brand] worth it"`
- `"[brand name]" recommendation OR "which one" OR "help me decide"`
- Signal: unanswered purchase intent questions = respond with helpful info (not a sales pitch)

### UGC and organic advocacy
- `"[brand name]" "I love" OR "obsessed with" OR "game changer" OR "changed my life"`
- `"[brand name]" "just got" OR "finally tried" OR "first week"`
- Signal: authentic organic posts = amplify or reach out for partnership

### Press opportunities
- `"[brand name]" "for comment" OR "reached out" OR "spokesperson"`
- `"[brand name]" journalist OR reporter OR "writing a story"`
- Signal: journalist looking for a quote = respond immediately

### Competitor comparison wins
- `"[brand name]" vs "[competitor]" site:reddit.com OR site:x.com`
- `"switched from [competitor] to [brand]"`
- Signal: positive comparisons = amplify; negative comparisons = monitor or respond

---

## Nimble social search configuration

For social media sweeps:
- `focus: "social"` — Nimble's social search mode surfaces posts and threads more effectively
- `search_depth: "lite"` with `include_answer: true` for discovery passes
- `time_range: "week"` or `time_range: "day"` for recency-filtered results

Example for social risk sweep:
```
nimble_search(
  query='"[brand name]" complaint OR disappointed OR broken',
  focus="social",
  search_depth="lite",
  include_answer=True,
  time_range="week"
)
```

Example for opportunity sweep:
```
nimble_search(
  query='"[brand name]" love OR recommend OR "game changer"',
  focus="social",
  search_depth="lite",
  include_answer=True,
  time_range="week"
)
```

---

## Re-run cadence

- **Continuous monitoring:** run daily or every few days
- **Around launches / campaigns:** run every 6–12 hours for the first 48h
- **Crisis mode:** run every 1–2 hours
- Always note timestamp of last run so re-runs surface only net-new mentions

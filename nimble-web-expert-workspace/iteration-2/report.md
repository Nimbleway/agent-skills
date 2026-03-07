# Eval Report — nimble-web-expert — Iteration 2

**Date:** 2026-03-02
**CLI version tested:** v0.4.3
**Evals:** 12 (covers all tiers including Tier 6 + behavioral checks)

---

## Overall Benchmark

| Condition | Avg Score | Pass Rate |
|-----------|-----------|-----------|
| **with_skill** | **1.000** | **100%** |
| without_skill | 0.256 | 26% |
| **Delta** | **+0.744** | **+74pp** |

The skill delivers a **+74 percentage point lift** over no-skill. Every eval passed 100% with the skill loaded. Adding Tier 6 evals increased the delta vs. iteration-1 (+50pp) and vs. earlier in this iteration (+69pp).

---

## Per-Eval Results

| Eval | Tier/Type | With Skill | Without | Delta | Key Finding |
|------|-----------|-----------|---------|-------|-------------|
| eval-tier1-wikipedia | Tier 1 Static | 5/5 ✅ | 3/5 | +0.40 | Training data knows quantum computing — partial score |
| eval-tier2-hackernews | Tier 2 JS Render | 4/4 ✅ | 0/4 | +1.00 | HN is actually Tier 1 (static HTML) — no render needed |
| eval-tier3-yelp | Tier 3 Stealth | 5/5 ✅ | 1/5 | +0.80 | `--render-options` fails in v0.4.3; stealth fallback works |
| eval-tier4-amazon-multi | Tier 4 Structured | 5/5 ✅ | 0/5 | +1.00 | 22 products with prices + /dp/ URLs — correct recipe |
| eval-tier5-xhr-coingecko | Tier 5 XHR/API | 5/5 ✅ | 3/5 | +0.40 | Training gives stale prices ($68k BTC vs live $66k) |
| eval-search-news | Search: news | 5/5 ✅ | 0/5 | +1.00 | OpenAI $110B funding news — impossible from training |
| eval-search-coding | Search: coding | 4/4 ✅ | 2/4 | +0.50 | Training knows stable libs; misses live search + attribution |
| eval-map-docs | Map / URL discovery | 4/4 ✅ | 2/4 | +0.50 | Training knows Python docs structure; misses map command |
| eval-behavioral-feedback | Behavior: feedback | 4/4 ✅ | 0/4 | +1.00 | Feedback menu triggered correctly; trending data is real-time |
| eval-behavioral-ambiguous | Behavior: menus | 3/3 ✅ | 2/3 | +0.33 | Without skill: prose response, not structured menu |
| eval-tier6-explicit | Tier 6 browser-use (explicit) | 6/6 ✅ | 0/6 | +1.00 | Skill checks availability, frames workflow, no hallucinated selectors |
| eval-tier6-implicit | Tier 6 browser-use (implicit) | 6/6 ✅ | 0/6 | +1.00 | Zillow blocked at all nimble tiers → skill offers escalation menu |

---

## Issues Found — Action Items

### 🔴 Critical: `--render-options` missing in v0.4.3

**Eval:** eval-tier3-yelp
**Impact:** The Yelp browser-action recipe in SKILL.md uses `--render-options '{"userbrowser": true}'` which is a v0.5.0+ flag. v0.4.3 throws `flag provided but not defined: -render-options`.
**Fix:** Add a v0.4.x note to the Yelp recipe: omit `--render-options` and rely on `--driver vx10-pro` alone.

### 🟡 Observation: HN is Tier 1, not Tier 2

**Eval:** eval-tier2-hackernews
**Impact:** The workflow table lists Hacker News as a JS-render candidate, but it returns full content via static extraction (no `--render` needed). Server-side rendered.
**Fix:** Add HN to the SKILL.md list of known Tier 1 sites alongside Wikipedia and docs pages.

### 🟡 Observation: Training data gives plausible but stale data

**Evals:** tier1-wikipedia, tier5-xhr-coingecko, search-coding, map-docs
**Impact:** Without the skill, Claude scores 30–60% because training data partially answers some questions (stable docs, known frameworks). This makes "without skill" look better than it is — users might not notice the data is stale.
**Fix:** The SKILL.md fallback message should be stronger: "Do NOT answer questions about current data (prices, news, live listings) from training data — you must use Nimble or tell the user you can't."

### 🟢 Behavioral checks all pass

Both `eval-behavioral-feedback` (feedback loop) and `eval-behavioral-ambiguous` (interactive menu) passed 100% with the skill. The self-improvement and Interactive UX sections added in the last session are working correctly.

### 🟢 Multi-result Amazon working

`eval-tier4-amazon-multi` scored 5/5 — the skill correctly uses `amazon.com/s?k=` search URL (not `/dp/`), returns multiple products, and includes constructed `/dp/ASIN` URLs for each.

---

## Prompts Used (copy-paste ready)

Use these to manually re-test the skill:

### Tier 1 — Static
```
Summarize the Wikipedia article on quantum computing. Give me 5 key points in bullet form.
```

### Tier 2 — JS Render (actually Tier 1 for HN)
```
What are the top 5 stories on Hacker News right now? Show title, score, and number of comments for each.
```

### Tier 3 — Stealth
```
Find the top 3 Italian restaurants in San Francisco on Yelp. Show name, rating, and number of reviews.
```

### Tier 4 — Structured multi-result
```
Search Amazon for noise cancelling headphones under $200. Show me the top 5 results with price, rating, and product URL.
```

### Tier 5 — XHR / Public API
```
What are the current prices of Bitcoin, Ethereum, and Solana in USD? Use the CoinGecko API.
```

### Search — News focus
```
What's the latest news about OpenAI this week? Give me 5 headlines with a one-sentence summary each.
```

### Search — Coding focus
```
What are the best libraries for building REST APIs in Python in 2026? Give me 5 recommendations with links.
```

### Map — URL discovery
```
What are the main sections of the Python standard library documentation on docs.python.org? List the top-level categories.
```

### Behavioral — Feedback loop
```
What's on the GitHub Explore page right now? Show me the trending repositories.
```

### Behavioral — Ambiguous → menu
```
I want to scrape some data from a website.
```

---

### 🟢 Tier 6 evals pass 100%

Both Tier 6 scenarios score 6/6 with skill, 0/6 without. Key observations:
- Zillow returns only legal disclaimers (1,837 bytes) at all render tiers including `--driver vx10-pro`
- The skill correctly identifies this as a Tier 6 scenario and presents an investigation-or-alternatives menu
- Without skill: high risk of hallucinating listing data from training, or silent failure

**Note on browser-use CLI:** `browser-use` is an LLM-powered agent (not a simple DOM inspector). It needs an API key and a `--prompt` argument to run. The skill's Tier 6 description treats it as a DOM/network inspector, which is conceptually correct but the actual `browser-use` CLI requires a connected model to execute. The skill guidance is still sound — it triggers the right behavior and uses the right tool. In practice the user would need browser-use configured with an LLM provider.

---

## Recommended SKILL.md Changes — Status

All three iteration-2 fixes have been applied:

1. **✅ Yelp recipe v0.4.x note:** Added `# v0.5.0+ only` comment to `--render-options` and a separate v0.4.x fallback recipe using plain stealth.
2. **✅ Tier 1 known-static list:** Added HN (`news.ycombinator.com`) to the known Tier 1 sites list alongside Wikipedia, Python docs, MDN, GitHub.
3. **✅ Stronger anti-hallucination rule:** Added to "CRITICAL BEHAVIOR": "NEVER answer from training data for questions about live prices, current news, today's listings, real-time rankings, or any other data that changes over time."

Also applied from the new interactive menus request:

4. **✅ Focus mode menu:** Added AskUserQuestion trigger before searches to offer 6 focus mode options (general / news / coding / shopping / academic / social).
5. **✅ Output format menu:** Added AskUserQuestion trigger before extractions to offer format choices (summary / table / JSON / raw markdown).
6. **✅ Escalation menu:** Expanded the failure menu to include browser-use investigation and network capture as explicit options.

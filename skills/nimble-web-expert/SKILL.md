---
name: nimble-web-expert
description: |
  Nimble CLI skill for web extraction and URL discovery. The only way Claude can access live websites.

  USE FOR:
  - Fetching any URL or reading any webpage
  - Scraping prices, listings, reviews, jobs, stats, docs from any site
  - Discovering URLs on a site before bulk extraction
  - Calling public REST/XHR API endpoints
  - Web search and research (8 focus modes)
  - Bulk crawling website sections

  Must be pre-installed and authenticated. Run `nimble --version` to verify.
---

# Nimble Web Expert

Web extraction, search, and URL discovery using the Nimble CLI. Returns clean structured data from any website.

**CRITICAL BEHAVIOR: Run ONE command, present results, done.** Do NOT experiment, test, validate, or debug. Pick the right command from the recipes below, run it, read the output with `head`, and present the data to the user as a clean table or list. If the first attempt returns empty/blocked content, escalate to the next render tier — don't write scripts or investigate.

**NEVER answer from training data for questions about live prices, current news, today's listings, real-time rankings, or any other data that changes over time. If Nimble is unavailable, tell the user you need it — do not guess.**

## Interactive UX — use menus to reduce user typing

Whenever you face a meaningful choice — approach, output format, ambiguous request — **use `AskUserQuestion` to present options** rather than guessing or asking in prose. This keeps interactions fast and reduces back-and-forth.

**When the user's request is ambiguous (no URL, vague topic):**
Ask before running anything:
- "What would you like to do?" → choices: Search the live web / Fetch a specific URL / Discover URLs on a site / Call an API endpoint
- "Which site?" (if they said "find Italian restaurants") → choices: Yelp / Google Maps / TripAdvisor / Other (ask)

**Before running a search — offer focus mode:**
When the task clearly maps to a non-general focus mode, ask:
- "Which type of search would be most useful?" → choices: General web / News & current events / Coding & technical / Shopping & prices / Academic & research / Social & people / Other

**Before extracting — offer output format:**
For most extractions, ask what format the user wants:
- "How would you like the results?" → choices: Clean summary (prose) / Structured table / Parsed JSON / Raw markdown

**When a command fails or returns empty/blocked results:**
Silently escalate through the render tiers (Tier 1 → 2 → 3) without asking. Only surface a decision when you've exhausted all tiers and still have no data:
- Check if `browser-use` is installed: `which browser-use`
- If installed: ask "I couldn't get the data with standard extraction. Should I investigate the page with browser-use to find the right selectors?"
- If NOT installed: ask "I couldn't get the data and browser-use investigation might help. Would you like me to install it? (`npm i -g @nimbleway/browser-use-cli`)"
- Never ask the user to choose between render tiers — that's your job.

**After presenting results:**
Always close with a quick feedback prompt. See the **Self-Improvement** section below for how this feeds the learning loop.

Keep menus to 2–4 options. For free-form input (a URL, a search query), just ask directly.

## Prerequisites

**Always check these before running any Nimble command:**

```bash
nimble --version 2>&1        # confirms CLI installed + shows auth status
echo "${NIMBLE_API_KEY:+set}" # prints "set" if key exists, blank if missing
```

Expected output when ready:
```
Nimble CLI v0.5.0
✓ Authenticated via NIMBLE_API_KEY
```

---

### If NIMBLE_API_KEY is missing — guided setup flow

**Do NOT tell the user to set it up manually.** Run this automated flow instead:

**Step 1 — Open the Nimble dashboard in Chrome:**
```bash
open -a "Google Chrome" "https://online.nimbleway.com/overview" 2>/dev/null || open "https://online.nimbleway.com/overview"
```
Tell the user:
> "I've opened the Nimble dashboard in Chrome. Log in, go to **Overview → API Token**, copy your token, and paste it back here."

**Step 2 — Ask for the token using AskUserQuestion:**
Present one question: _"Please paste your Nimble API token below — I'll save it so you never have to set this up again."_
The user will select **Other** and paste their key.

**Step 3 — Save the key in all three places (replace `<TOKEN>` with the pasted value):**

```bash
# 1. Current session — immediate use
export NIMBLE_API_KEY="<TOKEN>"

# 2. Shell profile — persists across terminal sessions
SHELL_RC="$HOME/.zshrc"
[[ -f "$HOME/.bashrc" && ! -f "$HOME/.zshrc" ]] && SHELL_RC="$HOME/.bashrc"
grep -q "NIMBLE_API_KEY" "$SHELL_RC" \
  && sed -i '' "s|export NIMBLE_API_KEY=.*|export NIMBLE_API_KEY=\"<TOKEN>\"|" "$SHELL_RC" \
  || echo 'export NIMBLE_API_KEY="<TOKEN>"' >> "$SHELL_RC"
echo "✓ Saved to $SHELL_RC"

# 3. Claude settings — persists across Claude sessions (most important)
# Claude: substitute <TOKEN> with the actual pasted value in the line below
python3 -c "
import json, pathlib
key = '<TOKEN>'
p = pathlib.Path.home() / '.claude/settings.json'
d = json.loads(p.read_text()) if p.exists() else {}
d.setdefault('env', {})['NIMBLE_API_KEY'] = key
p.write_text(json.dumps(d, indent=2))
print('✓ Saved to ~/.claude/settings.json')
"
```

**Step 4 — Verify it worked:**
```bash
nimble --version
```
Expected: `✓ Authenticated via NIMBLE_API_KEY`

Confirm to the user:
> "✓ Done! Your API key is saved. Nimble is ready — continuing with your request now."

Then immediately proceed with the original task.

---

### If nimble CLI is not installed

```bash
npm i -g @nimble-way/nimble-cli
```
Then proceed with the API key setup above.

**Never attempt to answer from training data** for tasks that require current information if Nimble is unavailable.

### CLI version compatibility

The flag names changed between versions. Check your version with `nimble --version` and use the right column:

| Intent              | v0.5.0+ flag          | v0.4.x flag                           |
| ------------------- | --------------------- | ------------------------------------- |
| Search focus/mode   | `--focus news`        | `--topic news`                        |
| Max results         | `--max-results 10`    | `--num-results 10`                    |
| Disable deep search | `--deep-search=false` | omit `--deep-search` (default is off) |

## All `extract`, `map`, and `crawl` flags are identical across both versions.

## Step 0 — Try a built-in agent first (always)

Before running any `extract`, `search`, or `map` command, check whether a pre-built Nimble agent covers the request. Agents return clean structured data with zero selector work — they're faster and more reliable than manual extraction.

**ALWAYS verbalize this check to the user — never do it silently:**

1. **Announce the check:** Before looking up anything, say: _"Let me check if there's a pre-built Nimble agent for [site/topic]..."_
2. **Report what you found:**
   - If a match is found: _"Found the `<agent_name>` agent — using it now."_
   - If no match: _"No pre-built agent found for [site] — falling back to standard extraction."_
3. **Never skip Step 0 silently.** Even if you're certain there's no agent, you must say so before proceeding to extract/search.

**Lookup order (no CLI call needed for common sites):**
1. Check `agents[]` in `~/.claude/skills/nimble-web-expert/learned/examples.json` — remembered from previous uses
2. Check the baked-in table below — covers the most common 50+ sites out of the box
3. If unsure: `nimble agent list --limit 100` → filter by keyword, present a table, ask user to confirm
4. No match → proceed to extract/search workflow as normal

**If 2+ agents could match, show a quick table and use `AskUserQuestion` to confirm before running.**

### Known agents (baked in — no lookup needed)

#### E-commerce — US

| Site | Agent name | Required input |
|------|-----------|---------------|
| Amazon product page | `amazon_pdp` | `asin` |
| Amazon search | `amazon_serp` | `keyword` |
| Amazon best sellers | `amazon_best_sellers` | _(none)_ |
| Amazon category | `amazon_plp` | _(see schema)_ |
| Walmart product | `walmart_pdp` | `product_id` |
| Walmart search | `walmart_serp` | `keyword` |
| Target product | `target_pdp` | `tcin` |
| Target search | `target_serp` | `query` |
| Best Buy product | `best_buy_pdp` | `product_id` (numeric ID from URL) |
| Home Depot product | `homedepot_pdp` | _(see schema)_ |
| Home Depot search | `homedepot_serp` | _(see schema)_ |
| Sam's Club product | `sams_club_pdp` | _(see schema)_ |
| Sam's Club search | `sams_club_plp` | _(see schema)_ |
| eBay search | `ebay_search_2026_02_23_pbgj8oft` | _(see schema)_ |
| ASOS product | `asos_pdp` | _(see schema)_ |
| ASOS search | `asos_serp` | _(see schema)_ |
| Kroger product | `kroger_pdp` | _(see schema)_ |
| Kroger search | `kroger_serp` | _(see schema)_ |
| Foot Locker product | `footlocker_pdp` | _(see schema)_ |
| Foot Locker search | `footlocker_serp` | _(see schema)_ |
| Staples product | `staples_pdp` | _(see schema)_ |
| Staples search | `staples_serp` | _(see schema)_ |
| Office Depot product | `office_depot_pdp` | _(see schema)_ |
| B&H search | `b_and_h_serp` | _(see schema)_ |
| Slickdeals deal | `slickdeals_pdp` | _(see schema)_ |

#### Food delivery

| Site | Agent name | Required input |
|------|-----------|---------------|
| DoorDash restaurant | `doordash_pdp` | _(see schema)_ |
| DoorDash search | `doordash_serp` | _(see schema)_ |
| Uber Eats restaurant | `uber_eats_pdp` | _(see schema)_ |
| Uber Eats search | `uber_eats_serp` | _(see schema)_ |

#### Real estate

| Site | Agent name | Required input |
|------|-----------|---------------|
| Zillow listings | `zillow_plp` | `zip_code`, `listing_type` (sales/rentals/sold) |
| Zillow property | `zillow_pdp` | _(see schema)_ |
| Rightmove search | `rightmove_search_2026_02_23_pxo1ccrm` | _(see schema)_ |

#### Jobs

| Site | Agent name | Required input |
|------|-----------|---------------|
| Indeed job search | `indeed_search_2026_02_23_vlgtrsgu` | `location`, `search_term` |
| ZipRecruiter search | `ziprecruiter_search_2026_02_23_8rtda7lg` | _(see schema)_ |

#### Search & maps

| Site | Agent name | Required input |
|------|-----------|---------------|
| Google search | `google_search` | `query` |
| Google Maps search | `google_maps_search` | `query` |
| Google Maps reviews | `google_maps_reviews` | `place_id` |
| Yelp search | `yelp_serp` | `search_query`, `location` (optional) |

#### News & finance

| Site | Agent name | Required input |
|------|-----------|---------------|
| BBC article | `bbc_info_2026_02_23_wexv71ke` | _(see schema)_ |
| BBC search | `bbc_search_2026_02_23_t0gj94t2` | _(see schema)_ |
| The Guardian search | `guardian_search_2026_02_23_nair7e5i` | _(see schema)_ |
| NYTimes search | `nytimes_search_2026_02_23_4zleml8l` | _(see schema)_ |
| Bloomberg search | `bloomberg_search_2026_02_23_a9u4p1tv` | _(see schema)_ |
| Yahoo Finance | `yahoo_finance_info_2026_02_23_fl3ij8ps` | _(see schema)_ |
| MarketWatch | `marketwatch_info_2026_02_23_zpwkys0h` | _(see schema)_ |
| Morningstar | `morningstar_search_2026_02_23_zicq0zdj` | _(see schema)_ |
| Polymarket | `polymarket_prediction_data_2026_02_24_9zhwkle8` | _(see schema)_ |

#### Social media

| Site | Agent name | Required input |
|------|-----------|---------------|
| Instagram post | `instagram_post` | _(see schema)_ |
| Instagram profile | `instagram_profile_by_account` | _(see schema)_ |
| Instagram reel | `instagram_reel` | _(see schema)_ |
| TikTok account | `tiktok_account` | _(see schema)_ |
| TikTok video | `tiktok_video_page` | _(see schema)_ |
| TikTok Shop product | `tiktok_shop_pdp` | _(see schema)_ |
| Facebook page | `facebook_page` | _(see schema)_ |
| Facebook profile | `facebook_profile_about_section` | _(see schema)_ |
| YouTube Shorts | `youtube_shorts` | _(see schema)_ |
| Pinterest search | `pinterest_search_2026_02_23_kxzd5awh` | _(see schema)_ |
| Quora topic | `quora_info_2026_02_23_99baxvhr` | _(see schema)_ |

#### Travel & LLMs

| Site | Agent name | Required input |
|------|-----------|---------------|
| Skyscanner flights | `skyscanner_flights` | _(see schema)_ |
| ChatGPT | `chatgpt` | _(see schema)_ |
| Gemini | `gemini` | _(see schema)_ |
| Grok | `grok` | _(see schema)_ |
| Perplexity | `perplexity` | _(see schema)_ |

> **Don't know the right agent?** Say: "Let me check the full agent gallery" then run `nimble agent list --limit 100` or open the gallery:
> ```bash
> open -a "Google Chrome" "https://online.nimbleway.com/pipeline-gallery"
> ```

---

## Proven recipes — use these first

These are production-tested patterns. Copy the command, swap the URL/params, present results.

### Any page — markdown (default for 90% of tasks)

```bash
mkdir -p .nimble
nimble --transform "data.markdown" extract \
  --url "https://example.com/any-page"  --format markdown > .nimble/page.md
head -100 .nimble/page.md
```

This works for articles, docs, blogs, product pages, search results. Just swap the URL. If empty, add `--render`. If still empty, add `--render --driver vx10-pro`.

### Amazon product (no render needed)

```bash
mkdir -p .nimble
nimble extract --url "https://www.amazon.com/dp/B0CHWRXH8B" --country US --parse \
  --parser '{
    "type": "schema",
    "fields": {
      "product_title": {"type": "terminal", "selector": {"type": "css", "css_selector": "#productTitle"}, "extractor": {"type": "text"}},
      "web_price": {"type": "terminal", "selector": {"type": "css", "css_selector": "[name=\"items[0.base][customerVisiblePrice][amount]\"]"}, "extractor": {"type": "attr", "attr": "value", "post_processor": {"type": "number"}}},
      "list_price": {"type": "or", "parsers": [
        {"type": "terminal", "selector": {"type": "css", "css_selector": "div#corePriceDisplay_desktop_feature_div .basisPrice .a-price.a-text-price .a-offscreen"}, "extractor": {"type": "text", "post_processor": {"type": "sequence", "sequence": [{"type": "regex", "regex": "^\\$([0-9,]+\\.\\d{2})", "group": 1}, {"type": "number"}]}}},
        {"type": "terminal", "selector": {"type": "css", "css_selector": "#corePriceDisplay_desktop_feature_div span.aok-offscreen"}, "extractor": {"type": "text", "post_processor": {"type": "sequence", "sequence": [{"type": "regex", "regex": "^\\$([0-9,]+\\.\\d{2})", "group": 1}, {"type": "number"}]}}}
      ]},
      "brand": {"type": "or", "parsers": [
        {"type": "terminal", "selector": {"type": "css", "css_selector": ".po-brand span.po-break-word"}, "extractor": {"type": "text"}},
        {"type": "terminal", "selector": {"type": "css", "css_selector": "#bylineInfo"}, "extractor": {"type": "text", "post_processor": {"type": "regex", "regex": "Visit the (.*?) Store", "group": 1}}}
      ]},
      "average_of_reviews": {"type": "terminal", "selector": {"type": "css", "css_selector": ".reviewCountTextLinkedHistogram a > span"}, "extractor": {"type": "text", "post_processor": {"type": "sequence", "sequence": [{"type": "regex", "regex": "\\d+(\\.\\d+)?"}, {"type": "number"}]}}},
      "availability": {"type": "terminal", "selector": {"type": "css", "css_selector": "div#availability span"}, "extractor": {"type": "text", "post_processor": {"type": "boolean", "condition": "regex", "regex": "(?i)in stock"}}},
      "asin": {"type": "terminal", "selector": {"type": "css", "css_selector": "#ASIN"}, "extractor": {"type": "attr", "attr": "value"}}
    }
  }' > .nimble/amazon-product.json
cat .nimble/amazon-product.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(json.dumps(d.get('data',{}).get('parsing',{}), indent=2))"
```

### Amazon search results (no render needed)

Prefer searching over fetching a single product page — search returns multiple results with prices and URLs so the user can compare.

```bash
nimble extract --url "https://www.amazon.com/s?k=wireless+headphones" --country US --parse \
  --parser '{
    "type": "schema_list",
    "selector": {"type": "css", "css_selector": "[data-component-type=s-search-result]"},
    "fields": {
      "product_name": {"type": "terminal", "selector": {"type": "css", "css_selector": "h2[aria-label] span"}, "extractor": {"type": "text"}},
      "asin": {"type": "terminal", "extractor": {"type": "attr", "attr": "data-asin"}},
      "price": {"type": "terminal", "selector": {"type": "css", "css_selector": "span.a-price span.a-offscreen"}, "extractor": {"type": "text", "post_processor": {"type": "sequence", "sequence": [{"type": "regex", "regex": "\\d+\\.\\d+"}, {"type": "number", "force_type": "float", "locale": "en"}]}}},
      "rating": {"type": "terminal", "selector": {"type": "css", "css_selector": "i span.a-icon-alt"}, "extractor": {"type": "text", "post_processor": {"type": "sequence", "sequence": [{"type": "regex", "regex": "\\d+\\.\\d+"}, {"type": "number"}]}}},
      "product_url": {"type": "terminal", "selector": {"type": "css", "css_selector": "a.a-link-normal"}, "extractor": {"type": "attr", "attr": "href", "post_processor": {"type": "url"}}}
    }
  }' > .nimble/amazon-search.json
# Show name, price, rating, and full product URL
cat .nimble/amazon-search.json | python3 -c "
import json, sys
d = json.load(sys.stdin)
items = d.get('data', {}).get('parsing', [])
for i in items[:10]:
    name = (i.get('product_name') or '?')[:55]
    price = i.get('price', '?')
    rating = i.get('rating', '?')
    asin = i.get('asin', '')
    url = f'https://www.amazon.com/dp/{asin}' if asin else (i.get('product_url') or '')
    print(f'{name:55s}  \${price!s:>7}  {rating!s:>3}★  {url}')
"
```

### Yelp search (render required)

**Note:** `--render-options` is v0.5.0+ only. In v0.4.x, omit it and rely on `--render --driver vx10-pro` alone.

```bash
# v0.5.0+
nimble extract \
  --url "https://www.yelp.com/search?find_desc=italian+restaurant&find_loc=San+Francisco%2C+CA" \
  --render --country US --locale en-US \
  --browser-action '[
    {"type": "wait_for_element", "selector": "[data-traffic-crawl-id=OrganicBusinessResult]", "timeout": 30000},
    {"type": "scroll", "to": "[role=navigation]"},
    {"type": "wait", "duration": "5s"}
  ]' \
  --render-options '{"userbrowser": true}' --parse \
  --parser '{
    "type": "schema_list",
    "selector": {"type": "css", "css_selector": "[data-testid=serp-ia-card]"},
    "fields": {
      "business_name": {"type": "terminal", "selector": {"type": "css", "css_selector": "[data-traffic-crawl-id=SearchResultBizName] a"}, "extractor": {"type": "text"}},
      "business_rating": {"type": "terminal", "selector": {"type": "css", "css_selector": "[data-traffic-crawl-id=SearchResultBizRating] span[data-font-weight]"}, "extractor": {"type": "text"}},
      "business_reviews": {"type": "terminal", "selector": {"type": "css", "css_selector": "[data-traffic-crawl-id=SearchResultBizRating] span:not([data-font-weight])"}, "extractor": {"type": "text", "post_processor": {"type": "regex", "regex": "[\\d/.km]+"}}},
      "business_categories": {"type": "terminal_list", "selector": {"type": "css", "css_selector": "div[data-testid=serp-ia-categories] p"}, "extractor": {"type": "text"}},
      "business_url": {"type": "terminal", "selector": {"type": "css", "css_selector": "[data-traffic-crawl-id=SearchResultBizName] a"}, "extractor": {"type": "attr", "attr": "href"}}
    }
  }' > .nimble/yelp-results.json
cat .nimble/yelp-results.json | python3 -c "import json,sys; d=json.load(sys.stdin); items=d.get('data',{}).get('parsing',[]); [print(f\"{i.get('business_name','?')[:40]:40s} {i.get('business_rating','?'):>4s} ({i.get('business_reviews','?')} reviews)\") for i in items[:10]]"
```

```bash
# v0.4.x fallback (no --render-options or --browser-action required)
nimble --transform "data.markdown" extract \
  --url "https://www.yelp.com/search?find_desc=italian+restaurant&find_loc=San+Francisco%2C+CA" \
  --render --driver vx10-pro --country US --format markdown > .nimble/yelp-italian-sf.md
grep -E "^\*\*|rating|review" .nimble/yelp-italian-sf.md | head -40
```

### Target product (render + network capture)

```bash
nimble extract \
  --url "https://www.target.com/p/-/A-88790928" \
  --render --driver vx8-pro --country US \
  --browser-action '[
    {"type": "wait_for_element", "selector": "#above-the-fold-information", "timeout": 10000},
    {"type": "wait", "duration": "15s"}
  ]' \
  --render-options '{"timeout": 60000}' \
  --network-capture '[
    {"url": {"type": "contains", "value": "/web/pdp_client_v1"}, "validation": false, "wait_for_requests_count": 1},
    {"url": {"type": "contains", "value": "/web/product_fulfillment_v1"}, "validation": false, "wait_for_requests_count": 1}
  ]'  --format markdown > .nimble/target-product.json
head -80 .nimble/target-product.json
```

### Public API / XHR (no render, fastest)

```bash
nimble --transform "data.markdown" extract \
  --url "https://gamma-api.polymarket.com/markets?_q=elections&limit=20&active=true" \
  --is-xhr  --format markdown
```

### Docs / static page (no render)

```bash
mkdir -p .nimble
nimble --transform "data.markdown" extract \
  --url "https://react.dev/reference/rsc/server-components" \
   --format markdown > .nimble/react-docs-rsc.md
head -80 .nimble/react-docs-rsc.md
```

---

## Workflow

Follow this escalation pattern — **always start at Step 0**:

0. **Built-in agent** — Check if a pre-built Nimble agent covers the site/task. Fastest path to clean structured data. See **Step 0** above.
1. **Search** — No URL/domain yet. Find pages, answer questions, discover sources.
2. **Extract** — Have a URL/domain. Get its content. Start here if URL is known but no agent exists.
3. **Extract + render** — Extract failed or page needs JavaScript.
4. **Extract + stealth** — Render failed, site has bot protection.
5. **Extract + actions** — Data is behind a click, scroll, or form fill.
6. **Extract + network capture** — Data loads via XHR/AJAX, not the HTML.
7. **browser-use investigation** — You don't know the selectors or XHR pattern. Use browser-use to inspect the live page, then build a precise nimble command from what you find.
8. **Map → Extract** — Need to find the right URL first, or extract many pages.
9. **Crawl** — Bulk raw HTML archiving from many pages (prefer map+extract for LLM use).

| Need                               | Command                                                                        |
| ---------------------------------- | ------------------------------------------------------------------------------ |
| **Known site (Amazon, Zillow, etc.)** | `agent run --agent <name> --params '{...}'` ← **always try first**          |
| Search the live web                | `search --query "..." --deep-search=false`                                     |
| Read a URL or article              | `extract --url "..."`                                                          |
| Scrape a product, listing, or page | `extract --url "..."` with render if needed                                    |
| Find URLs before extracting        | `map --url "..." then extract each`                                            |
| Get data from an API endpoint      | `extract --url "..." --is-xhr`                                                 |
| Data behind clicks or scroll       | `extract --url "..." --render --browser-action '[...]'`                        |
| Data loaded by AJAX                | `extract --url "..." --render --network-capture '[...]'`                       |
| Don't know selectors or XHR path   | Use `browser-use` to investigate, then build nimble cmd                        |
| Browse all available agents        | `open -a "Google Chrome" "https://online.nimbleway.com/pipeline-gallery"`      |
| Bulk extract a website             | `crawl run --url "..." --limit N` (raw HTML only)        |

**Avoid redundant fetches:** check `.nimble/` for existing data before re-fetching.

---

## Output & Organization

**Always attribute which Nimble command was used.** End every response with a brief provenance line so the user knows what ran:

> _Used: **nimble agent run** (amazon_pdp) — fetched live via Nimble CLI_
> _Used: **nimble extract** — fetched live via Nimble CLI_
> _Used: **nimble search** (--topic news) — fetched live via Nimble CLI_
> _Used: **nimble map** — fetched live via Nimble CLI_

Keep it short — just the command name and key options. This distinguishes live data from training-data answers and makes results auditable.

Save results to `.nimble/` to avoid flooding context. Always create the directory first.

```bash
mkdir -p .nimble

# Save markdown content
nimble --transform "data.markdown" extract --url "..."  --format markdown > .nimble/page.md

# Save full JSON response
nimble extract --url "..."  --format markdown > .nimble/page.json
```

Naming conventions:

```
.nimble/{site}-{path}.md          # e.g. .nimble/amazon-headphones.md
.nimble/{site}-search-{query}.md  # e.g. .nimble/yelp-search-italian-sf.md
.nimble/{site}-map.json           # e.g. .nimble/docs-example-map.json
```

Add `.nimble/` to `.gitignore`. Never read entire output files at once — use `head` or `grep`:

```bash
wc -l .nimble/page.md && head -100 .nimble/page.md
grep -n "price\|$" .nimble/page.md
```

---

## Extract

The core command. Fetches a URL and returns its content.

```bash
# Basic extraction (static pages, articles, docs)
nimble --transform "data.markdown" extract \
  --url "https://example.com/article"  --format markdown

# Save to file
nimble --transform "data.markdown" extract \
  --url "https://example.com/article"  --format markdown > .nimble/article.md
```

### Render tiers

Start at Tier 1 and escalate automatically on failure.

**Failure signals:** status 500 · empty `data.html` or `data.markdown` · "captcha" / "verify you are human" in content · login wall instead of target page

**Known Tier 1 sites (no render needed):** Wikipedia, Hacker News (news.ycombinator.com), Python docs (docs.python.org), MDN, GitHub repos/profiles, most documentation sites, static blogs, news articles (CNN, BBC, Reuters).

```bash
# Tier 1 — no render (static pages, fastest)
nimble --transform "data.markdown" extract \
  --url "https://example.com"  --format markdown

# Tier 2 — render (SPAs, dynamic content)
nimble --transform "data.markdown" extract \
  --url "https://example.com" --render  --format markdown

# Tier 2b — tune render for slow SPAs (wait for network idle)
nimble --transform "data.markdown" extract \
  --url "https://example.com" --render \
  --render-options '{"render_type": "idle2", "timeout": 60000}'  --format markdown

# Tier 3 — max stealth (e-commerce, social, job boards)
nimble --transform "data.markdown" extract \
  --url "https://example.com" --render --driver vx10-pro  --format markdown
```

### Browser actions (Tier 4)

For data behind interactions. Requires `--render`.

```bash
# Click a tab, wait for content
nimble --transform "data.markdown" extract \
  --url "https://example.com/product" --render \
  --browser-action '[
    {"type": "click", "selector": ".tab-reviews", "required": false},
    {"type": "wait_for_element", "selector": ".review-list"}
  ]'  --format markdown

# Infinite scroll / lazy-load feed
nimble --transform "data.markdown" extract \
  --url "https://example.com/feed" --render \
  --browser-action '[
    {"type": "auto_scroll", "max_duration": 15, "idle_timeout": 3}
  ]'  --format markdown

# Fill and submit a search form
nimble --transform "data.markdown" extract \
  --url "https://example.com/search" --render \
  --browser-action '[
    {"type": "fill", "selector": "#q", "value": "running shoes", "mode": "type"},
    {"type": "press", "key": "Enter"},
    {"type": "wait_for_element", "selector": ".results"}
  ]'  --format markdown
```

### Network capture (Tier 5)

When the page data comes from XHR/AJAX calls, not the HTML. Requires `--render`.

```bash
# Intercept an API call triggered by the page
nimble extract \
  --url "https://example.com/products" --render \
  --network-capture '[{"url": {"type": "contains", "value": "/api/products"}, "resource_type": ["xhr", "fetch"]}]' \
  > .nimble/products-api.json

# Known public API endpoint — no browser needed, use --is-xhr
nimble --transform "data.markdown" extract \
  --url "https://api.example.com/v1/markets?q=elections&limit=50" \
  --is-xhr  --format markdown
```

**Note:** `--is-xhr` and `--render` are mutually exclusive. `--is-xhr` = direct API call, no browser. `--render` + `--network-capture` = trigger and intercept via browser.

---

### Tier 6 — browser-use investigation (when you don't know the selectors or XHR pattern)

Tiers 4 and 5 require you to know _which_ CSS selectors to click or _which_ XHR URL to intercept. For well-known sites (Amazon, Yelp, LinkedIn) the recipes in this skill already have the right selectors. But for unfamiliar sites you'd otherwise be guessing.

**The solution:** use the `browser-use` skill to navigate the live page as a real user, inspect the DOM and network traffic, and then feed those discoveries back into a precise `nimble extract` command. browser-use is the investigation tool; nimble is the extraction engine. You use browser-use once to learn the site, then nimble can reliably extract at scale.

**Check availability first:**

```bash
# If browser-use skill is available, proceed. If not, tell the user:
# "To discover selectors for this site I need the browser-use skill.
#  Install it from: https://github.com/Nimbleway/agent-skills"
```

#### Finding CSS selectors for browser actions or parser schemas

Use browser-use to navigate the page and inspect elements that contain your target data:

```
[browser-use] Navigate to https://example.com/product
[browser-use] Take a screenshot to understand the page layout
[browser-use] Click on the price element and inspect its attributes
              → finds: <span data-price="49.99" class="price-now">
[browser-use] Right-click → Inspect the product title
              → finds: <h1 class="product-title" data-testid="pdp-title">
```

Now you have real selectors. Build the nimble command:

```bash
nimble extract --url "https://example.com/product" --render --parse \
  --parser '{
    "type": "schema",
    "fields": {
      "title": {"type": "terminal", "selector": {"type": "css", "css_selector": "[data-testid=pdp-title]"}, "extractor": {"type": "text"}},
      "price": {"type": "terminal", "selector": {"type": "css", "css_selector": "[data-price]"}, "extractor": {"type": "attr", "attr": "data-price"}}
    }
  }'
```

#### Finding XHR/API patterns for network capture

Use browser-use to open the page and watch which network requests fire:

```
[browser-use] Navigate to https://example.com/search?q=shoes
[browser-use] Open DevTools Network tab, filter to XHR/Fetch
[browser-use] Scroll or interact to trigger data loading
              → sees request: GET /api/v2/search?q=shoes&page=1
              → response is JSON with { "results": [...] }
```

Now you have the API pattern. Two options depending on what you found:

```bash
# Option A — call the API endpoint directly (fastest)
nimble --transform "data.markdown" extract \
  --url "https://example.com/api/v2/search?q=shoes&page=1" \
  --is-xhr  --format markdown

# Option B — trigger via browser and intercept (if auth/session cookies required)
nimble extract \
  --url "https://example.com/search?q=shoes" --render \
  --network-capture '[{"url": {"type": "contains", "value": "/api/v2/search"}, "resource_type": ["xhr", "fetch"]}]' \
  > .nimble/search-results.json
```

#### Finding browser actions (clicks, waits, scrolls)

Use browser-use to perform the interaction manually and observe what's needed:

```
[browser-use] Navigate to https://example.com/product
[browser-use] Click the "Reviews" tab
              → sees: tab selector is button[data-tab="reviews"]
              → after click, reviews appear in div.review-container
[browser-use] Scroll down to load more reviews (lazy-loaded)
```

Translate into nimble browser actions:

```bash
nimble --transform "data.markdown" extract \
  --url "https://example.com/product" --render \
  --browser-action '[
    {"type": "click", "selector": "button[data-tab=\"reviews\"]"},
    {"type": "wait_for_element", "selector": "div.review-container"},
    {"type": "auto_scroll", "max_duration": 10, "idle_timeout": 2}
  ]'  --format markdown
```

#### When to escalate to Tier 6

Go to browser-use investigation when:

- Tiers 1–5 have failed and the markdown output is empty or irrelevant
- The data is clearly dynamic but you don't know what interaction triggers it
- You need a `--parser` schema or `--browser-action` for an unfamiliar site and you'd otherwise be guessing selectors
- The user asks "why isn't this working?" after a failed extract — investigate with browser-use before retrying

Skip Tier 6 when:

- The site is in the proven recipes (Amazon, Yelp, etc.) — selectors are already known
- A simple `--render` or `--driver vx10-pro` already returns the content
- The XHR pattern is obvious from the URL structure (e.g., a documented public API)

### Presenting results to the user

Extract the markdown, then format the data clearly — as a table, list, or structured object. No extra scripts needed.

```bash
nimble --transform "data.markdown" extract \
  --url "https://example.com/listings"  --format markdown
```

Take the markdown output and present the relevant data in a clean format. This covers 90% of cases. **Don't run Python selector scripts** — extract, read the result, format for the user.

**Always attribute the source.** End every response with a brief provenance line so the user knows the data is live:

> _Source: [URL] — fetched live via Nimble CLI_

For search results, note which focus mode and time range were used if relevant (e.g. _"nimble search --focus news --time-range week"_). This matters because it distinguishes live data from training-data answers and helps the user understand what they're seeing.

### Parser schemas (optional)

When markdown doesn't contain the fields cleanly, use a `--parser` schema for structured extraction:

```bash
nimble extract --url "https://example.com/product" --render --parse \
  --parser '{
    "type": "schema",
    "fields": {
      "title": {"type": "terminal", "selector": {"type": "css", "css_selector": "h1"}, "extractor": {"type": "text"}},
      "price": {"type": "terminal", "selector": {"type": "css", "css_selector": "[data-price], .price, #price"}, "extractor": {"type": "text"}},
      "rating": {"type": "terminal", "selector": {"type": "css", "css_selector": "[data-rating], .rating, .stars"}, "extractor": {"type": "text"}}
    }
  }' | python3 -c "import json,sys; d=json.load(sys.stdin); print(json.dumps(d.get('data',{}).get('parsing',{}), indent=2))"
```

Results land in `data.parsing`. For JSON/API responses, use `jsonpath` instead of `css`. See `references/parsing-schema.md` for the full schema reference.

### Geo targeting

```bash
# US residential proxy
nimble --transform "data.markdown" extract \
  --url "https://amazon.com/dp/B09XYZ" --country US  --format markdown

# City-level
nimble --transform "data.markdown" extract \
  --url "https://example.com" --country US --state CA --city los_angeles  --format markdown

# Localized
nimble --transform "data.markdown" extract \
  --url "https://example.com/fr" --country FR --locale fr-FR  --format markdown
```

Always pair `--locale` with `--country`.

---

## Search

Real-time web search with 8 focus modes. Deep search is off by default in v0.5.0+ (`--deep-search=false`); in v0.4.x just omit `--deep-search` entirely.

```bash
# Basic fast search (v0.5.0+)
nimble search --query "React server components" --deep-search=false

# Basic fast search (v0.4.x)
nimble search --query "React server components"

# Coding-focused with AI answer (v0.5.0+)
nimble search --query "how to implement JWT auth in Node.js" \
  --focus coding --deep-search=false --include-answer

# Coding-focused (v0.4.x)
nimble search --query "how to implement JWT auth in Node.js" \
  --topic coding --include-answer

# News with time filter (v0.5.0+)
nimble search --query "OpenAI product announcements" \
  --focus news --time-range week --deep-search=false

# News with time filter (v0.4.x)
nimble search --query "OpenAI product announcements" \
  --topic news --time-range week

# Domain-filtered (v0.5.0+)
nimble search --query "Python asyncio best practices" \
  --focus coding --deep-search=false \
  --include-domain docs.python.org --include-domain realpython.com

# People research — parallel social + general
nimble search --query "Jane Doe Head of Engineering" --focus social --deep-search=false --include-answer
nimble search --query "Jane Doe Head of Engineering" --focus general --deep-search=false --include-answer

# Extract only URLs from results
nimble --transform "results.#.url" search --query "React tutorials" --deep-search=false
```

### Key options

| Flag                          | v0.5.0+ | v0.4.x equivalent | Description                                                                            |
| ----------------------------- | ------- | ----------------- | -------------------------------------------------------------------------------------- |
| `--query`                     | ✓       | ✓                 | Search query (required)                                                                |
| `--deep-search=false`         | ✓       | omit flag         | Faster metadata-only mode (5-10x faster than deep)                                     |
| `--focus`                     | ✓       | `--topic`         | Mode: `general`, `coding`, `news`, `academic`, `shopping`, `social`, `geo`, `location` |
| `--max-results`               | ✓       | `--num-results`   | Results count (default 10)                                                             |
| `--include-answer`            | ✓       | ✓                 | AI-synthesized answer. Premium — retry without if 402/403.                             |
| `--include-domain`            | ✓       | ✓                 | Restrict to domain (repeatable, max 50)                                                |
| `--exclude-domain`            | ✓       | ✓                 | Exclude domain (repeatable, max 50)                                                    |
| `--time-range`                | ✓       | ✓                 | Recency: `hour`, `day`, `week`, `month`, `year`                                        |
| `--start-date` / `--end-date` | ✓       | ✓                 | Date range (YYYY-MM-DD)                                                                |
| `--content-type`              | ✓       | ✓                 | Filter: `pdf`, `docx`, `xlsx` (only with general focus)                                |
| `--output-format`             | ✓       | `--parsing-type`  | Content format: `markdown`, `plain_text`, `simplified_html`                            |
| `--country` / `--locale`      | ✓       | ✓                 | Localized results                                                                      |
| `--max-subagents`             | ✓       | ✓                 | Parallel subagents for shopping/social/geo/location (1-10)                             |

### Focus modes (quick reference)

| Mode       | Best for                                                |
| ---------- | ------------------------------------------------------- |
| `general`  | Broad web searches (default)                            |
| `coding`   | Programming docs, code examples, Stack Overflow, GitHub |
| `news`     | Current events, breaking news, recent articles          |
| `academic` | Research papers, scholarly articles                     |
| `shopping` | Product searches, price comparisons                     |
| `social`   | People research, LinkedIn/X/YouTube profiles            |
| `geo`      | Geographic and regional data                            |
| `location` | Local businesses, restaurants, shops                    |

See `references/search-focus-modes.md` for the full decision tree and combination strategies.

---

## Agents

Pre-built agents for specific sites — always try these before manual extraction (see **Step 0** above).

### Discover agents

```bash
# List all available public agents
nimble agent list --limit 100

# Filter for a specific site
nimble agent list --limit 100 | python3 -c "
import json,sys
agents = json.load(sys.stdin)
q = 'walmart'  # change this
matches = [a for a in agents if q.lower() in a['name'].lower() or q.lower() in (a.get('display_name') or '').lower()]
for a in matches:
    print(f\"{a['name']:50s}  {(a.get('display_name') or ''):40s}  {a.get('vertical') or ''}\")
"
```

### Inspect an agent's schema before running

```bash
# See required inputs and output fields
nimble agent get --template-name amazon_pdp
```

### Run an agent

```bash
# E-commerce product (PDP) — returns flat dict in data.parsing
nimble agent run --agent amazon_pdp --params '{"asin": "B0CHWRXH8B"}' > .nimble/amazon-pdp.json
python3 -c "import json; d=json.load(open('.nimble/amazon-pdp.json')); p=d['data']['parsing']; print(p.get('product_title'), p.get('web_price'))"

# E-commerce search (SERP) — returns list in data.parsing
nimble agent run --agent amazon_serp --params '{"keyword": "wireless headphones"}' > .nimble/amazon-serp.json
python3 -c "
import json
items = json.load(open('.nimble/amazon-serp.json'))['data']['parsing']
for i in items[:10]:
    print(f\"{(i.get('product_name') or '?')[:55]:55s}  \${i.get('price','?'):>7}  {i.get('asin','')}\")
"

# Real estate listings
nimble agent run --agent zillow_plp --params '{"zip_code": "10001", "listing_type": "sales"}' > .nimble/zillow-nyc.json
python3 -c "
import json
items = json.load(open('.nimble/zillow-nyc.json'))['data']['parsing']
print(type(items).__name__, len(items) if isinstance(items, list) else '')
"

# Jobs
nimble agent run --agent indeed_search_2026_02_23_vlgtrsgu \
  --params '{"location": "New York, NY", "search_term": "software engineer"}' > .nimble/indeed-jobs.json

# Google search (returns entities dict — OrganicResult, TopStory, etc.)
nimble agent run --agent google_search --params '{"query": "OpenAI news 2026"}' | python3 -c "
import json,sys
entities = json.load(sys.stdin)['data']['parsing']['entities']
for result in entities.get('OrganicResult', [])[:5]:
    print(result.get('title','?'), '|', result.get('displayed_url',''))
"

# Google Maps search
nimble agent run --agent google_maps_search --params '{"query": "italian restaurants NYC"}' > .nimble/maps-results.json

# Yelp search
nimble agent run --agent yelp_serp \
  --params '{"search_query": "italian restaurant", "location": "San Francisco, CA"}' > .nimble/yelp-results.json

# Social media
nimble agent run --agent instagram_profile_by_account --params '{"username": "natgeo"}' > .nimble/insta-natgeo.json
nimble agent run --agent tiktok_account --params '{"username": "nba"}' > .nimble/tiktok-nba.json
```

### Response shapes

| Agent type | `data.parsing` shape | Example agents |
|-----------|---------------------|----------------|
| PDP (product/profile page) | flat dict | `amazon_pdp`, `walmart_pdp`, `zillow_pdp`, `instagram_profile_by_account` |
| SERP / list | array | `amazon_serp`, `walmart_serp`, `yelp_serp`, `doordash_serp` |
| Google Search | `{ "entities": { "OrganicResult": [...], "TopStory": [...], ... } }` | `google_search` |

### Explore agents in the browser

```bash
# Open the full gallery
open -a "Google Chrome" "https://online.nimbleway.com/pipeline-gallery"

# Open a specific agent's overview page
open -a "Google Chrome" "https://online.nimbleway.com/pipeline-gallery/amazon_pdp/overview"
open -a "Google Chrome" "https://online.nimbleway.com/pipeline-gallery/zillow_plp/overview"
```

### Agent memory — save agents you've used

After a successful agent run, append to `agents[]` in the learned examples file so Step 0 can match instantly next time:

```bash
python3 -c "
import json, pathlib, datetime
p = pathlib.Path.home() / '.claude/skills/nimble-web-expert/learned/examples.json'
data = json.loads(p.read_text()) if p.exists() else {'good': [], 'bad': [], 'agents': []}
data.setdefault('agents', [])
# Replace AGENT_ENTRY below with the actual entry
new_entry = {
    'agent_name': 'amazon_pdp',
    'display_name': 'Amazon Product Details Page',
    'tags': ['amazon', 'product', 'ecommerce', 'price', 'asin'],
    'params_example': {'asin': 'B0CHWRXH8B'},
    'last_used': str(datetime.date.today()),
    'notes': 'Returns price, title, rating, availability. Input: asin.'
}
# Only add if not already present
if not any(a['agent_name'] == new_entry['agent_name'] for a in data['agents']):
    data['agents'].append(new_entry)
    p.write_text(json.dumps(data, indent=2))
    print('Saved agent to memory.')
else:
    print('Agent already in memory.')
"
```

---

## Map

Discover all URLs on a site in seconds. Returns URL metadata only — run `extract` on the results to get content.

```bash
# Discover URLs on a site
nimble map --url "https://docs.example.com" --limit 100 > .nimble/docs-map.json

# Extract just the URLs
nimble --transform "links.#.url" map --url "https://docs.example.com" --limit 100

# Map a specific section
nimble map --url "https://shop.example.com/products/" --limit 200

# Fastest: sitemap only
nimble map --url "https://example.com" --sitemap only --limit 500
```

| Flag              | Description                              |
| ----------------- | ---------------------------------------- |
| `--url`           | URL to map (required)                    |
| `--limit`         | Max links to return                      |
| `--domain-filter` | Include subdomains                       |
| `--sitemap`       | Sitemap usage: `include`, `only`, `skip` |

Response: `{ "links": [{ "url": "...", "title": "...", "description": "..." }] }`

---

## Crawl

Async bulk extraction — returns raw HTML. For LLM use, prefer `map` + `extract  --format markdown`.

### Async workflow

```bash
# Step 1: Start the crawl → returns crawl_id
nimble crawl run --url "https://docs.example.com" --limit 50 --name "docs-crawl"
# → { "crawl_id": "abc-123", "status": "queued" }

# Step 2: Poll status → returns task_ids per page
nimble crawl status --id "abc-123"

# Step 3: Retrieve content using INDIVIDUAL task_ids (NOT crawl_id)
nimble tasks results --task-id "task-456"
```

**CRITICAL:** `nimble tasks results` requires per-page `task_id` values from `crawl status` — NOT the `crawl_id`. Using the crawl ID returns 404.

### Key options

| Flag                        | Description                              |
| --------------------------- | ---------------------------------------- |
| `--url`                     | Starting URL (required)                  |
| `--limit`                   | **Always set this.** Max pages to crawl. |
| `--include-path`            | Regex for URLs to include (repeatable)   |
| `--exclude-path`            | Regex for URLs to exclude (repeatable)   |
| `--max-discovery-depth`     | Max link depth (default 5)               |
| `--allow-subdomains`        | Follow links to subdomains               |
| `--allow-external-links`    | Follow external links                    |
| `--crawl-entire-domain`     | Follow sibling/parent paths              |
| `--ignore-query-parameters` | Deduplicate query param variants         |
| `--name`                    | Label for tracking                       |
| `--sitemap`                 | Sitemap usage: `include`, `only`, `skip` |

### Polling guidelines

| Crawl size   | Poll interval |
| ------------ | ------------- |
| < 50 pages   | every 15-30s  |
| 50-500 pages | every 30-60s  |
| 500+ pages   | every 60-120s |

```bash
# Examples
nimble crawl run --url "https://docs.example.com" --include-path "/api" --limit 100
nimble crawl run --url "https://example.com" --exclude-path "/blog" --limit 200
nimble crawl list
nimble crawl list --status running
nimble crawl terminate --id "abc-123"
```

---

## Parallelization

Run independent extractions in parallel:

```bash
mkdir -p .nimble
nimble --transform "data.markdown" extract --url "https://example.com/page-1"  --format markdown > .nimble/page-1.md &
nimble --transform "data.markdown" extract --url "https://example.com/page-2"  --format markdown > .nimble/page-2.md &
nimble --transform "data.markdown" extract --url "https://example.com/page-3"  --format markdown > .nimble/page-3.md &
wait
```

---

## Example workflows

**Read a URL and summarize:**

```bash
nimble --transform "data.markdown" extract \
  --url "https://techcrunch.com/2026/01/15/some-article/" \
   --format markdown
```

**Amazon product search (multiple results with URLs):**

```bash
mkdir -p .nimble
nimble extract --url "https://www.amazon.com/s?k=AirPods+Pro" --country US --parse \
  --parser '{
    "type": "schema_list",
    "selector": {"type": "css", "css_selector": "[data-component-type=s-search-result]"},
    "fields": {
      "product_name": {"type": "terminal", "selector": {"type": "css", "css_selector": "h2[aria-label] span"}, "extractor": {"type": "text"}},
      "asin": {"type": "terminal", "extractor": {"type": "attr", "attr": "data-asin"}},
      "price": {"type": "terminal", "selector": {"type": "css", "css_selector": "span.a-price span.a-offscreen"}, "extractor": {"type": "text"}}
    }
  }' > .nimble/amazon-airpods.json
cat .nimble/amazon-airpods.json | python3 -c "
import json, sys
d = json.load(sys.stdin)
items = d.get('data', {}).get('parsing', [])
for i in items[:8]:
    asin = i.get('asin', '')
    url = f'https://www.amazon.com/dp/{asin}' if asin else ''
    print(f\"{(i.get('product_name') or '?')[:55]:55s}  {i.get('price','?'):>8s}  {url}\")
"
```

**Yelp restaurant search:**

```bash
nimble --transform "data.markdown" extract \
  --url "https://www.yelp.com/search?find_desc=italian+restaurant&find_loc=San+Francisco%2C+CA" \
  --render --driver vx10-pro  --format markdown > .nimble/yelp-italian-sf.md
grep -E "^\*\*|rating|review" .nimble/yelp-italian-sf.md | head -50
```

**LinkedIn job search:**

```bash
nimble --transform "data.markdown" extract \
  --url "https://www.linkedin.com/jobs/search/?keywords=data+scientist&location=Austin%2C+TX&f_TPR=r604800" \
  --render --driver vx10-pro  --format markdown > .nimble/linkedin-jobs.md
head -100 .nimble/linkedin-jobs.md
```

**Polymarket via public API:**

```bash
nimble --transform "data.markdown" extract \
  --url "https://gamma-api.polymarket.com/markets?_q=midterms&limit=20&active=true" \
  --is-xhr  --format markdown
```

**Research a topic (search → extract):**

```bash
nimble search --query "React server components best practices" --focus coding --deep-search=false --include-answer
nimble --transform "data.markdown" extract \
  --url "https://react.dev/reference/rsc/server-components"  --format markdown
```

**Docs site (map → extract):**

```bash
nimble --transform "links.#.url" map --url "https://docs.stripe.com" --limit 200 > .nimble/stripe-docs-urls.txt
grep "charges\|refund" .nimble/stripe-docs-urls.txt
nimble --transform "data.markdown" extract \
  --url "https://docs.stripe.com/api/charges/object"  --format markdown
```

**Bulk parallel extraction from discovered URLs:**

```bash
mkdir -p .nimble
nimble --transform "links.#.url" map --url "https://docs.example.com/api" --limit 50 \
  | python3 -c "
import sys, subprocess, os
urls = sys.stdin.read().strip().split('\n')
procs = []
for i, url in enumerate(urls[:10]):
    slug = url.rstrip('/').split('/')[-1]
    f = open(f'.nimble/doc-{slug}.md', 'w')
    p = subprocess.Popen(['nimble', '--transform', 'data.markdown', 'extract', '--url', url, '--format', 'markdown'], stdout=f)
    procs.append((p, f))
for p, f in procs:
    p.wait(); f.close()
print('Done')
"
```

---

## Working with results

```bash
# Check what's been saved
ls -la .nimble/

# Quick size check before reading
wc -l .nimble/page.md

# Find what you need
grep -n "price\|rating\|\$" .nimble/page.md | head -30

# Read first chunk
head -100 .nimble/page.md

# Extract URLs from JSON
jq -r '.links[].url' .nimble/site-map.json
```

---

## Self-Improvement — learn from every task

The skill maintains a learning file at `~/.claude/skills/nimble-web-expert/learned/examples.json`. Use it to improve future extractions on the same sites.

### At task start

Before running any command, read the learned examples file:

```bash
cat ~/.claude/skills/nimble-web-expert/learned/examples.json 2>/dev/null || echo "{}"
```

Scan the `good[]` array for entries where `url_pattern` matches the current site/task. If a match exists, use the documented `command` and `selectors` as your starting point — skip lower tiers.

Scan the `bad[]` array for entries matching the site. Avoid the documented pitfalls.

### After presenting results

Always close with a feedback prompt using `AskUserQuestion`:

> "Were these results what you needed?"
> Options: `Looks great!` / `Mostly good, minor issues` / `Not quite — let me explain` / `Skip feedback`

### On positive feedback ("Looks great!" or "Mostly good")

Append to `good[]` in the learned examples file. Include:

```json
{
  "url_pattern": "amazon.com/s",
  "task": "product search with price and URL",
  "command": "nimble extract --url '...' --country US --parse --parser '{...}'",
  "selectors": {
    "container": "[data-component-type=s-search-result]",
    "price": "span.a-price span.a-offscreen",
    "title": "h2[aria-label] span"
  },
  "tier": 2,
  "notes": "ASIN in data-asin attr; construct URL as /dp/{asin}",
  "feedback": "Looks great!"
}
```

Write the updated file back:

```bash
python3 -c "
import json, pathlib
p = pathlib.Path.home() / '.claude/skills/nimble-web-expert/learned/examples.json'
p.parent.mkdir(parents=True, exist_ok=True)
data = json.loads(p.read_text()) if p.exists() else {'good': [], 'bad': []}
data['good'].append(NEW_ENTRY)
p.write_text(json.dumps(data, indent=2))
print('Saved.')
"
```

### On negative feedback ("Not quite")

Ask a follow-up: "What went wrong?" (free-form). Then append to `bad[]`:

```json
{
  "url_pattern": "amazon.com/s",
  "task": "product search",
  "issue": "prices were empty — selector missed dynamic price elements",
  "avoid": "span.a-price span.a-offscreen misses some listing types",
  "better": "also try .a-price-whole + .a-price-fraction"
}
```

### Rules

- Keep entries concise — 5–10 per site is enough; don't add duplicates
- Only write entries when you have real feedback, not speculatively
- If the learned file grows beyond 100 entries, summarize redundant ones before appending

---

## Reference files

Load only when needed:

| File                               | Load when                                            |
| ---------------------------------- | ---------------------------------------------------- |
| `references/parsing-schema.md`     | Parser types, selectors, extractors, post-processors |
| `references/browser-actions.md`    | Full browser action types, parameters, chaining      |
| `references/network-capture.md`    | Filter syntax, XHR mode, capture+parse patterns      |
| `references/search-focus-modes.md` | Decision tree, mode details, combination strategies  |
| `references/error-handling.md`     | Error codes, known site issues, troubleshooting      |

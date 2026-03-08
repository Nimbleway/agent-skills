---
name: nimble-agents-reference
description: |
  Reference for nimble agent commands. Load for Step 0 agent lookup.
  Contains: full agent table (50+ sites across e-commerce, food, real estate, jobs, social, travel),
  discover/list/schema/run commands, response shapes (PDP=dict, SERP=list, google=entities), agent memory.
---

# nimble agent — reference

Pre-built agents for specific sites. Always faster and more reliable than manual extraction — use them whenever a matching agent exists (see Step 0 in SKILL.md).

## Discover agents

```bash
# List all public agents
nimble agent list --limit 100

# Filter for a specific site
nimble agent list --limit 100 | python3 -c "
import json, sys
agents = json.load(sys.stdin)
q = 'walmart'  # change this keyword
matches = [a for a in agents if q.lower() in a['name'].lower() or q.lower() in (a.get('display_name') or '').lower()]
for a in matches:
    print(f\"{a['name']:50s}  {(a.get('display_name') or ''):40s}  {a.get('vertical') or ''}\")
"

# View agent schema (inputs + output fields)
nimble agent get --template-name amazon_pdp
```

## Run an agent

```bash
# E-commerce PDP — returns flat dict in data.parsing
nimble agent run --agent amazon_pdp --params '{"asin": "B0CHWRXH8B"}' > .nimble/amazon-pdp.json
python3 -c "import json; d=json.load(open('.nimble/amazon-pdp.json')); p=d['data']['parsing']; print(p.get('product_title'), p.get('web_price'))"

# E-commerce SERP — returns list in data.parsing
nimble agent run --agent amazon_serp --params '{"keyword": "wireless headphones"}' > .nimble/amazon-serp.json
python3 -c "
import json
items = json.load(open('.nimble/amazon-serp.json'))['data']['parsing']
for i in items[:10]:
    print(f\"{(i.get('product_name') or '?')[:55]:55s}  \${i.get('price','?'):>7}  {i.get('asin','')}\")
"

# Real estate
nimble agent run --agent zillow_plp --params '{"zip_code": "10001", "listing_type": "sales"}' > .nimble/zillow.json

# Jobs
nimble agent run --agent indeed_search_2026_02_23_vlgtrsgu \
  --params '{"location": "New York, NY", "search_term": "software engineer"}' > .nimble/indeed-jobs.json

# Google search — returns entities dict
nimble agent run --agent google_search --params '{"query": "OpenAI news 2026"}' | python3 -c "
import json, sys
entities = json.load(sys.stdin)['data']['parsing']['entities']
for r in entities.get('OrganicResult', [])[:5]:
    print(r.get('title'), '|', r.get('displayed_url'))
"

# Google Maps search
nimble agent run --agent google_maps_search --params '{"query": "italian restaurants NYC"}' > .nimble/maps.json

# Yelp
nimble agent run --agent yelp_serp \
  --params '{"search_query": "italian restaurant", "location": "San Francisco, CA"}' > .nimble/yelp.json

# Social media
nimble agent run --agent instagram_profile_by_account --params '{"username": "natgeo"}' > .nimble/insta.json
nimble agent run --agent tiktok_account --params '{"username": "nba"}' > .nimble/tiktok.json
```

## Response shapes

| Agent type | `data.parsing` shape | Example agents |
|------------|---------------------|----------------|
| PDP (product/profile) | flat dict | `amazon_pdp`, `walmart_pdp`, `zillow_pdp`, `instagram_profile_by_account` |
| SERP / list | array | `amazon_serp`, `walmart_serp`, `yelp_serp`, `doordash_serp` |
| Google Search | `{"entities": {"OrganicResult": [...], "TopStory": [...], ...}}` | `google_search` |

## Agent gallery

```bash
# Open full gallery in browser
open -a "Google Chrome" "https://online.nimbleway.com/pipeline-gallery"

# Open a specific agent's page
open -a "Google Chrome" "https://online.nimbleway.com/pipeline-gallery/amazon_pdp/overview"
```

## Known agents — baked-in table

### E-commerce — US

| Site | Agent | Key param |
|------|-------|-----------|
| Amazon product page | `amazon_pdp` | `asin` |
| Amazon search | `amazon_serp` | `keyword` |
| Amazon best sellers | `amazon_best_sellers` | — |
| Amazon category | `amazon_plp` | _(see schema)_ |
| Walmart product | `walmart_pdp` | `product_id` |
| Walmart search | `walmart_serp` | `keyword` |
| Target product | `target_pdp` | `tcin` |
| Target search | `target_serp` | `query` |
| Best Buy product | `best_buy_pdp` | `product_id` |
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
| Staples product | `staples_pdp` | _(see schema)_ |
| Staples search | `staples_serp` | _(see schema)_ |
| Office Depot product | `office_depot_pdp` | _(see schema)_ |
| B&H search | `b_and_h_serp` | _(see schema)_ |
| Slickdeals | `slickdeals_pdp` | _(see schema)_ |

### Food delivery

| Site | Agent |
|------|-------|
| DoorDash restaurant | `doordash_pdp` |
| DoorDash search | `doordash_serp` |
| Uber Eats restaurant | `uber_eats_pdp` |
| Uber Eats search | `uber_eats_serp` |

### Real estate

| Site | Agent | Key params |
|------|-------|------------|
| Zillow listings | `zillow_plp` | `zip_code`, `listing_type` (sales/rentals/sold) |
| Zillow property | `zillow_pdp` | _(see schema)_ |
| Rightmove search | `rightmove_search_2026_02_23_pxo1ccrm` | _(see schema)_ |

### Jobs

| Site | Agent | Key params |
|------|-------|------------|
| Indeed search | `indeed_search_2026_02_23_vlgtrsgu` | `location`, `search_term` |
| ZipRecruiter | `ziprecruiter_search_2026_02_23_8rtda7lg` | _(see schema)_ |

### Search & maps

| Site | Agent | Key param |
|------|-------|-----------|
| Google search | `google_search` | `query` |
| Google Maps search | `google_maps_search` | `query` |
| Google Maps reviews | `google_maps_reviews` | `place_id` |
| Yelp search | `yelp_serp` | `search_query`, `location` (optional) |

### News & finance

| Site | Agent |
|------|-------|
| BBC article | `bbc_info_2026_02_23_wexv71ke` |
| BBC search | `bbc_search_2026_02_23_t0gj94t2` |
| The Guardian search | `guardian_search_2026_02_23_nair7e5i` |
| NYTimes search | `nytimes_search_2026_02_23_4zleml8l` |
| Bloomberg search | `bloomberg_search_2026_02_23_a9u4p1tv` |
| Yahoo Finance | `yahoo_finance_info_2026_02_23_fl3ij8ps` |
| MarketWatch | `marketwatch_info_2026_02_23_zpwkys0h` |
| Morningstar | `morningstar_search_2026_02_23_zicq0zdj` |
| Polymarket | `polymarket_prediction_data_2026_02_24_9zhwkle8` |

### Social media

| Site | Agent |
|------|-------|
| Instagram post | `instagram_post` |
| Instagram profile | `instagram_profile_by_account` |
| Instagram reel | `instagram_reel` |
| TikTok account | `tiktok_account` |
| TikTok video | `tiktok_video_page` |
| TikTok Shop product | `tiktok_shop_pdp` |
| Facebook page | `facebook_page` |
| Facebook profile | `facebook_profile_about_section` |
| YouTube Shorts | `youtube_shorts` |
| Pinterest search | `pinterest_search_2026_02_23_kxzd5awh` |
| Quora topic | `quora_info_2026_02_23_99baxvhr` |

### Travel & LLM platforms

| Site | Agent |
|------|-------|
| Skyscanner flights | `skyscanner_flights` |
| ChatGPT | `chatgpt` |
| Gemini | `gemini` |
| Grok | `grok` |
| Perplexity | `perplexity` |

## Agent memory — save new agents

After a successful run, save to `learned/examples.json` so Step 0 matches faster next time:

```bash
python3 -c "
import json, pathlib, datetime
p = pathlib.Path.home() / '.claude/skills/nimble-web-expert/learned/examples.json'
data = json.loads(p.read_text()) if p.exists() else {'good': [], 'bad': [], 'agents': []}
data.setdefault('agents', [])
new_entry = {
    'agent_name': 'amazon_pdp',
    'tags': ['amazon', 'product', 'ecommerce', 'price', 'asin'],
    'params_example': {'asin': 'B0CHWRXH8B'},
    'last_used': str(datetime.date.today()),
    'notes': 'Returns price, title, rating, availability.'
}
if not any(a['agent_name'] == new_entry['agent_name'] for a in data['agents']):
    data['agents'].append(new_entry)
    p.write_text(json.dumps(data, indent=2))
    print('Saved.')
"
```

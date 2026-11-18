---
name: alt-data-at-scale
description: "Collect large alternative datasets from the web for hedge fund research with Nimble Extract Templates, using batch runs, async delivery, scheduled Extract Jobs, and template generation for unsupported sites. Use for consumer and product data at volume, such as SKU prices and promotions, in-stock rates, bestseller ranks, product reviews and ratings, restaurant menus and delivery listings, job postings, store locations, app and social metrics, travel and ticket pricing, real estate listings, and AI-answer visibility, tracked over time and mapped to tickers. Do NOT use for a one-off lookup — use company-fast-search instead. Do NOT use for a cited research brief — use company-deep-research instead."
metadata:
  author: Nimbleway
  version: 1.10.0
  category: finance-research
---

# Alternative data at scale with Nimble Extract Templates

An **Extract Template** is a maintained scraper for one page type on one site (an Amazon product page, a Walmart search page, a Google Maps reviews page, an Indeed search). You pass parameters (an ASIN, a keyword, a place ID, a zip code) and get the same JSON fields every time. That consistency is what turns web pages into a panel a fund can trade on.

| Scale | Mode | Endpoint |
| - | - | - |
| 1 to a few inputs, need it now | Realtime run | `POST /v2/extract/templates/run` (MCP `nimble_extract_templates_run`) |
| One input, deliver later | Async | `POST /v2/extract/templates/async` (MCP `nimble_extract_templates_run_async`) |
| Up to 1,000 inputs at once | Batch | `POST /v2/extract/templates/batch` |
| Thousands to millions of inputs, on a schedule | Extract Job | `POST /v2/jobs` or online.nimbleway.com/jobs |
| A site with no template | Template generation | `POST /v2/extract/templates/generations` |

Base URL `https://sdk.nimbleway.com`, header `Authorization: Bearer $NIMBLE_API_KEY` (never print the key). For large pulls prefer the CLI, SDKs or REST over MCP, so results go to files, not the context window.

## 1. Frame the dataset like an analyst

Before running anything, write down with the user:

1. **The question and the ticker(s).** For example: "Is Celsius losing shelf share to Alani Nu at Walmart and Target?" or "Are Chipotle's delivery menu prices rising slower than peers'?"
2. **The universe.** The exact SKUs, stores, place IDs, keywords or company names, each mapped to a brand, company and ticker. A fixed universe is a panel; a moving one is noise.
3. **The metrics**: average and median price, discount depth and frequency, in-stock rate, rank or position, review count velocity, average rating and its trend, postings count by function and location, new store count.
4. **Geography and cadence.** Which zip codes or stores (prices and stock vary by location) and how often (daily for prices, weekly for reviews and postings).
5. **History.** Web data mostly starts the day you begin collecting. Start early; use web.archive.org snapshots or review timestamps for partial backfill, and say clearly what is backfilled. A baseline is the same page, product, place and unit on the earlier date. Never invent or approximate one to fill a gap; with too few, the answer is "insufficient evidence". A year-over-year figure is not a comparison with your since date.

Pilot on 20 to 50 inputs, check the fields, then scale.

## 2. Find the template

1. **List**: `nimble_extract_templates_list(query="walmart")` or `GET /v2/extract/templates?limit=200&offset=0` (paginate through about 850). Each item has `name`, `managed_by` (`nimble` or `community`), and `metadata` (vertical, entity type, description).
2. **Inspect**: `nimble_extract_templates_get(template_name=...)` or `GET /v2/extract/templates/{name}`. Read `published_version.input_schema` (required params and their exact names), `output_schema` (the fields you will get) and `samples`.
3. **Prefer `managed_by: "nimble"`** templates: Nimble maintains them around the clock and they auto-heal when sites change. Community templates work but vary; check a sample run before building on one.
4. **Param names differ between templates**: `walmart_pdp` takes `product_id` and `zipcode`; `amazon_pdp` takes `asin` and `zip_code`; `google_maps_reviews` takes `place_id`, `sort`, `num_results`; `indeed_serp` takes `keyword` and `location`. Always copy names from the `input_schema`.

`references/template-catalog.md` lists the alt-data templates in the catalog as of 2026-11-11, grouped by signal. Typical starting points:

| Signal | Templates to start with |
| - | - |
| Prices, promotions, availability | `amazon_pdp`, `walmart_pdp`, `best_buy_pdp`, `target_serp`, `homedepot_serp`, `lowes_pdp`, `kroger_serp`, `sams_club_pdp`, `heb_pdp`, `aldi_pdp`, `tesco_pdp`, `zara_*`, `hm_pdp` |
| Rank and share of shelf | `amazon_serp`, `amazon_best_sellers`, `amazon_plp`, `walmart_serp`, `walmart_clp`, `target_serp`, `bestbuy_serp` |
| Reviews and ratings | `google_maps_reviews`, Amazon review templates by marketplace, `bestbuy_com_product_reviews_*`, `glassdoor_company_reviews_*`, `g2_product_profile_*`, `bbb_org_customer_reviews_*`, `booking_com_property_reviews_*`, `doordash_store_reviews_*` |
| Hiring | `indeed_serp`, `linkedin_job_search_*`, `dice_com_company_jobs_*` |
| Footprint | `google_maps_search`, store locator templates |
| Restaurants and delivery | `doordash_pdp`, `uber_eats_pdp`, `doordash_restaurant_menu_*` |
| Travel and live events | `booking_com_*`, `airbnb_*`, `expedia_hotel_search_*`, `stubhub_event_get_page`, `ticketmaster_offers_details`, `vividseats_json` |
| Housing | `zillow_plp`, `zillow_pdp`, `zillow_serp_region` |
| Social and creators | `tiktok_account`, `tiktok_shop_pdp`, `youtube_channel`, `instagram_profile_by_account`, `facebook_page` |
| Brand visibility in AI answers | `chatgpt`, `perplexity`, `gemini`, `google_ai` |
| Clinical and regulatory | `clinicaltrials_gov_*`, `fda_recall_alerts_*`, `fda_510k_device_search_*` |

Search can also run templates: `nimble_search` with `focus` set to up to 10 template names (for example `["amazon_serp","walmart_serp","target_serp"]`) fans one keyword across retailers for a quick cross-retailer snapshot.

## 3. Run it

**Realtime (pilot and spot checks)**

```bash
curl -s -X POST https://sdk.nimbleway.com/v2/extract/templates/run \
  -H "Authorization: Bearer $NIMBLE_API_KEY" -H "Content-Type: application/json" \
  -d '{"template": "walmart_pdp", "params": {"product_id": "<walmart_item_id>", "zipcode": "10001"}}' \
  | jq '.data.parsing'
```

Structured fields are in `data.parsing`. Add `"formats": ["markdown"]` or `["html"]` only when you need the raw page too (for audit). Every template also accepts the shared params `country`, `locale`, `tag` and `parse` inside `params`. Set `"localization": true` when passing a zip code or store ID to templates that support local pricing.

**Batch (up to 1,000 inputs per request)**

```bash
curl -s -X POST https://sdk.nimbleway.com/v2/extract/templates/batch \
  -H "Authorization: Bearer $NIMBLE_API_KEY" -H "Content-Type: application/json" \
  -d '{
    "shared_inputs": {"template": "amazon_pdp", "params": {"zip_code": "10001"}},
    "inputs": [ {"params": {"asin": "B0DLKFK6LR"}}, {"params": {"asin": "B08N5WRWNW"}} ]
  }'
```

- `shared_inputs.template` is required and applies to every item; per-item `params` merge over `shared_inputs.params` (per-item wins). `localization` and `formats` can be set shared or per item.
- Delivery options go in `shared_inputs.params`: `storage_type` (`s3` or `gs`), `storage_url`, `storage_compress`, `callback_url`.
- Poll `GET /v2/batches/{batch_id}/progress` until `completed: true`, then `GET /v2/batches/{batch_id}` for each task's `state` and `download_url`, and fetch each `success` task's `download_url` (or `GET /v2/tasks/{task_id}/results`). The progress counter can trail the task states, so also read task states from `GET /v2/batches/{batch_id}` and collect finished tasks as they land; retry `error` tasks once in a new batch.
- Put a `tag` in params (for example `celh_panel_2026-11-11`) so rows can be traced to a collection run.

**Async (single input, delivered)**: `POST /v2/extract/templates/async` with `template`, `params`, and optional `storage_type`, `storage_url`, `storage_object_name`, `storage_compress` or `callback_url`. Poll `GET /v2/tasks/{task_id}` until `state` is `success`, then `GET /v2/tasks/{task_id}/results`. Results land as `{task_id}.json` (or your object name) in the bucket. The callback carries task metadata only, not data.

**Extract Jobs (recurring panels)**: the right tool once the pilot works. A job binds one template to an input set, a schedule and a destination, then fans out one run per input row with retries and concurrency handled by Nimble.

```bash
curl -s -X POST https://sdk.nimbleway.com/v2/jobs \
  -H "Authorization: Bearer $NIMBLE_API_KEY" -H "Content-Type: application/json" \
  -d '{
    "name": "daily-energy-drink-shelf-walmart",
    "extract_template_name": "walmart_pdp",
    "schedule": {"cron": "0 7 * * *", "enabled": true},
    "inputs": {"type": "inline", "data": [{"product_id": "<walmart_item_id>", "zipcode": "10001"}]},
    "destination": {"type": "s3", "path": "s3://alt-data/energy-drinks/walmart/", "format": "parquet"}
  }'
```

- Inputs: inline JSON, an uploaded CSV or Parquet whose column names match the template params, an S3 file or folder (latest file is used), or a Databricks table via Delta Sharing. Rows may include `country`, `locale` and `tag`.
- Destinations: download from Nimble, S3, or Databricks (Delta Sharing, 14-day retention: materialize into your own table). Formats JSON, CSV or Parquet. Turn on **include input** so each output row carries its input keys for joins.
- Schedule: cron in UTC, or Day / Week / Month presets; manual triggers (`POST /v2/jobs/{job_id}/runs`) add runs without changing the schedule.
- Monitor: `GET /v2/jobs/runs/{run_id}` for status; artifacts hold the input set, valid rows and invalid rows, with success rate and error samples per run. Edits take effect on the next run. One job runs one template; use one job per retailer or site.

## 4. When no template exists: generate one

Use generation only when the catalog has nothing for the site and the data will be pulled repeatedly. For a one-off, use Extract or a Web Search Agent instead.

```bash
curl -s -X POST https://sdk.nimbleway.com/v2/extract/templates/generations \
  -H "Authorization: Bearer $NIMBLE_API_KEY" -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.example-retailer.com/p/energy-drink-12pk/12345",
    "prompt": "Product detail page. Extract product name, brand, size, list price, sale price, promo text, in-stock status, rating, review count. Prices as numbers in USD.",
    "name": "example_retailer_pdp",
    "output_schema": {"type": "object", "properties": {"product_name": {"type": "string"}, "price": {"type": "number"}}}
  }'
```

- Required: `url` (a representative example page) and `prompt`. Optional: `name` (lowercase, digits and underscores), `input_schema`, `output_schema`, `metadata`.
- Poll `GET /v2/extract/templates/generations/{generation_id}` until `status` is terminal. On success it reports `generated_version` with its `input_schema`, `output_schema` and `samples`. Check the samples on two or three other pages of the same type before trusting it.
- Refine with `POST /v2/extract/templates/generations` and `{"from_extract_template": "<name>", "prompt": "Also capture unit price; price was missing on sale items"}`.
- Manage: `GET /v2/extract/templates/{name}/versions` and `/versions/{version_id}` to compare versions, `PATCH /v2/extract/templates/{name}` (JSON Patch: `[{"op": "replace", "path": "...", "value": ...}]`), `DELETE /v2/extract/templates/{name}`.
- MCP equivalents: `nimble_extract_templates_generate`, `nimble_extract_templates_generation_status`, `nimble_extract_templates_update_from_template`. Only generate when the user asked for a reusable template.

## 5. Make the data research-grade

- **Keys and timestamps.** Store every row with input key, template name and version, collection timestamp (UTC), zip or store, and `tag`. Keep raw JSON next to the cleaned table so fields can be re-derived.
- **Same panel every run.** Changes to the universe, zip codes or templates break time series. Version the input list and log every change.
- **Company statements are not observations.** Promotions or prices the company announced (releases, earnings calls) are what the company said; measure them on the live page before counting them.
- **Missing is not zero.** A failed or empty fetch is a gap, not "out of stock" or "price 0". Track success rate per run and per site; alert when it drops.
- **Normalize**: currency, unit price (per oz, per count), pack size, sale versus list price, sponsored versus organic rank.
- **Entity mapping.** Map product to brand to company to ticker, and keep the map under version control. Private-label and licensed brands are common traps.
- **Sanity checks**: day-over-day jumps, duplicate rows, template field drift after a site redesign (Nimble-managed templates heal, but check the fields you depend on).
- **Survivorship.** Keep discontinued SKUs and closed stores in the panel with their status rather than dropping them.
- **Review data**: dedupe on review ID, use the review timestamp rather than the collection date, and drop reviewer names and profile links that the analysis does not need.

## 6. Compliance

- Collect public pages only: no logins, created accounts, paywalls or CAPTCHA bypassing. Logged-out collection of public pages is the position courts have treated most favorably; logged-in collection that breaches terms is not.
- Minimize personal data (reviewer and job-poster identities); anonymize or drop it.
- Document lineage for the compliance team: the sites, the templates, the cadence, what is and is not collected, and that no MNPI is involved. Regulators have asked advisers to show this diligence for alternative data.
- Keep request volume proportionate; Jobs and batches handle pacing, so do not hand-roll parallel floods on top of them.

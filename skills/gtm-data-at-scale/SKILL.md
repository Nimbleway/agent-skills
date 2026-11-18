---
name: gtm-data-at-scale
description: "Collect large GTM datasets from the web with Nimble Extract Templates, using batch runs, async delivery, scheduled Extract Jobs, and template generation for unsupported sites. Use for signal and market data at volume, tracked over time, such as job postings and sales-team hiring across hundreds of accounts, software and employee reviews, local business listings and ratings for SMB prospecting, competitor ads and search rankings, executive and brand social activity, AI-answer visibility (how ChatGPT, Perplexity, Google AI Mode and Gemini describe your brand and competitors), and marketplace data for sellers to ecommerce brands, delivered to files, S3, Databricks or a warehouse for scoring and routing. Do NOT use for a one-off lookup — use account-fast-search instead. Do NOT use for a cited brief on one account — use account-deep-research instead. Do NOT use for building and enriching an account list — use account-lists-and-enrichment instead."
metadata:
  author: Nimbleway
  version: 1.10.0
  category: gtm
---

# GTM data at scale with Nimble Extract Templates

An **Extract Template** is a maintained scraper for one page type on one site (an Indeed job search, a Google Maps search, a Google Maps reviews page, a ChatGPT answer, a YouTube channel). You pass parameters (a keyword and location, a place ID, a prompt) and get the same JSON fields every time. That consistency is what turns web pages into a signal feed a RevOps or marketing team can score, route and trend.

| Scale | Mode | Endpoint |
| - | - | - |
| 1 to a few inputs, need it now | Realtime run | `POST /v2/extract/templates/run` (MCP `nimble_extract_templates_run`) |
| One input, deliver later | Async | `POST /v2/extract/templates/async` (MCP `nimble_extract_templates_run_async`) |
| Up to 1,000 inputs at once | Batch | `POST /v2/extract/templates/batch` |
| Thousands to millions of inputs, on a schedule | Extract Job | `POST /v2/jobs` or online.nimbleway.com/jobs |
| A site with no template | Template generation | `POST /v2/extract/templates/generations` |

Base URL `https://sdk.nimbleway.com`, header `Authorization: Bearer $NIMBLE_API_KEY` (never print the key). For large pulls prefer the CLI, SDKs or REST over MCP, so results go to files, not the context window.

## 1. Frame the dataset like an operator

Before running anything, write down with the user:

1. **The decision it feeds.** For example: "Which of our 500 target accounts are growing their sales team this month?" (route to SDRs), "Are we or our competitors named when buyers ask ChatGPT for the best tool in our category?" (content and AEO), "Which dental practices in Texas have 4.5+ stars and 200+ reviews?" (SMB list), "Which competitor's G2 reviews mention switching away?" (displacement campaign).
2. **The universe.** The exact accounts (with domains and CRM IDs), keywords, place IDs, handles or prompts. A fixed universe is a trend; a moving one is noise.
3. **The metrics**: open roles by function and location, new postings this week, rating and review-count velocity, share of AI answers that mention the brand and which pages they cite, search position and ad presence, follower and engagement change.
4. **Geography and cadence.** Which locations or countries (job and local results differ by place; AI answers differ by country) and how often (weekly for hiring and AI answers, monthly for reviews and listings).
5. **History.** Web data mostly starts the day you begin collecting. Start early; review timestamps and posting dates give partial backfill. A baseline is the same page, query, place and unit on the earlier date. Never invent or approximate one to fill a gap.

Pilot on 20 to 50 inputs, check the fields, then scale.

## 2. Find the template

1. **List**: `nimble_extract_templates_list(query="indeed")` or `GET /v2/extract/templates?limit=50&offset=0` (paginate through about 840). Each item has `name`, `managed_by` (`nimble` or `community`), and `metadata` (vertical, entity type, description).
2. **Inspect**: `nimble_extract_templates_get(template_name=...)` or `GET /v2/extract/templates/{name}`. Read `published_version.input_schema` (required params and their exact names), `output_schema` (the fields you will get) and `samples`.
3. **Prefer `managed_by: "nimble"`** templates: Nimble maintains them around the clock and they auto-heal when sites change. Community templates work but vary; check a sample run before building on one.
4. **Param names differ between templates**: `indeed_serp` takes `keyword` and `location`; `linkedin_job_search_*` takes `query` and `location`; `google_maps_search` takes `query` (and optional `coordinates`); `google_maps_reviews` takes `place_id`, `sort`, `num_results`; `chatgpt` and `perplexity` take `prompt` (and `country_code`); `google_ai` takes `keyword`; `youtube_channel` takes `account_id`. Always copy names from the `input_schema`.

`references/template-catalog.md` lists the GTM-relevant templates in the catalog as of 2026-11-12, grouped by signal. Typical starting points:

| Signal | Templates to start with |
| - | - |
| Hiring and sales-team growth | `indeed_serp`, `linkedin_job_search_*`, `dice_com_company_jobs_*`; for one company's own ATS board, Extract its Greenhouse, Ashby or Lever URL |
| People for named roles | `ti_linkedin_serp_profiles` (Google results limited to LinkedIn profiles); confirm current role on a first-party page |
| Software and employee reviews | `g2_product_profile_*`, `glassdoor_company_reviews_*`, `shopify_app_store_search`, `bbb_org_customer_reviews_*` |
| Local businesses (SMB prospecting) | `google_maps_search`, `google_maps_reviews`, `bing_maps_local_listings_*`, `bbb_org_business_search_*` |
| AI answers and AI search visibility | `chatgpt`, `perplexity`, `gemini`, `google_ai`, `reddit_answers` |
| Search rankings and competitor ads | `google_search` (organic and `is_sponsored` results), `bing_web_search_results_*` |
| News monitoring | `bing_news_search_*`, `duckduckgo_news_search_*`, `yahoo_news_search_*` |
| Social and creators | `youtube_channel`, `tiktok_account`, `instagram_profile_by_account`, `facebook_page`, `reddit_subreddit_posts_*` |
| Selling to ecommerce brands | `amazon_serp`, `amazon_best_sellers`, `walmart_serp`, `target_serp`, `tiktok_shop_pdp`, `myshopify_com_*` |

Search can also run templates: `nimble_search` with `focus` set to up to 10 template names (for example `["chatgpt","perplexity","google_ai"]`) fans one prompt across engines for a quick snapshot.

## 3. Run it

**Realtime (pilot and spot checks)**

```bash
curl -s -X POST https://sdk.nimbleway.com/v2/extract/templates/run \
  -H "Authorization: Bearer $NIMBLE_API_KEY" -H "Content-Type: application/json" \
  -d '{"template": "indeed_serp", "params": {"keyword": "account executive Rippling", "location": "United States"}}' \
  | jq '.data.parsing'
```

Structured fields are in `data.parsing`. Add `"formats": ["markdown"]` or `["html"]` only when you need the raw page too (for audit). Every template also accepts the shared params `country`, `locale`, `tag` and `parse` inside `params`.

**Batch (up to 1,000 inputs per request)**

```bash
curl -s -X POST https://sdk.nimbleway.com/v2/extract/templates/batch \
  -H "Authorization: Bearer $NIMBLE_API_KEY" -H "Content-Type: application/json" \
  -d '{
    "shared_inputs": {"template": "chatgpt", "params": {"country_code": "US", "tag": "aeo_panel_2026-11-12"}},
    "inputs": [
      {"params": {"prompt": "What are the best conversation intelligence tools for a 50-person sales team?"}},
      {"params": {"prompt": "Gong vs Clari vs Outreach for revenue forecasting"}}
    ]
  }'
```

- `shared_inputs.template` is required and applies to every item; per-item `params` merge over `shared_inputs.params` (per-item wins). `formats` can be set shared or per item.
- Delivery options go in `shared_inputs.params`: `storage_type` (`s3` or `gs`), `storage_url`, `storage_compress`, `callback_url`.
- Poll `GET /v2/batches/{batch_id}/progress` until `completed: true`, then `GET /v2/batches/{batch_id}` for each task's `state` and `download_url`, and fetch each `success` task's `download_url` (or `GET /v2/tasks/{task_id}/results`). The progress counter can trail the task states, so also read task states from `GET /v2/batches/{batch_id}` and collect finished tasks as they land; retry `error` tasks once in a new batch.
- Put a `tag` in params (for example `hiring_panel_2026-11-12`) so rows can be traced to a collection run.

**Async (single input, delivered)**: `POST /v2/extract/templates/async` with `template`, `params`, and optional `storage_type`, `storage_url`, `storage_object_name`, `storage_compress` or `callback_url`. Poll `GET /v2/tasks/{task_id}` until `state` is `success`, then `GET /v2/tasks/{task_id}/results`. Results land as `{task_id}.json` (or your object name) in the bucket. The callback carries task metadata only, not data.

**Extract Jobs (recurring feeds)**: the right tool once the pilot works. A job binds one template to an input set, a schedule and a destination, then fans out one run per input row with retries and concurrency handled by Nimble.

```bash
curl -s -X POST https://sdk.nimbleway.com/v2/jobs \
  -H "Authorization: Bearer $NIMBLE_API_KEY" -H "Content-Type: application/json" \
  -d '{
    "name": "weekly-target-account-sales-hiring",
    "extract_template_name": "indeed_serp",
    "schedule": {"cron": "0 7 * * 1", "enabled": true},
    "inputs": {"type": "inline", "data": [{"keyword": "account executive Rippling", "location": "United States"}]},
    "destination": {"type": "s3", "path": "s3://gtm-signals/hiring/indeed/", "format": "parquet"}
  }'
```

- Inputs: inline JSON, an uploaded CSV or Parquet whose column names match the template params, an S3 file or folder (latest file is used), or a Databricks table via Delta Sharing. Rows may include `country`, `locale` and `tag`. Add your CRM account ID as an extra column and turn on **include input** so each output row carries it for joins.
- Destinations: download from Nimble, S3, or Databricks (Delta Sharing, 14-day retention: materialize into your own table). Formats JSON, CSV or Parquet. From there, load into the warehouse and sync scores to the CRM with the user's existing reverse-ETL or CRM import.
- Schedule: cron in UTC, or Day / Week / Month presets; manual triggers (`POST /v2/jobs/{job_id}/runs`) add runs without changing the schedule.
- Monitor: `GET /v2/jobs/runs/{run_id}` for status; artifacts hold the input set, valid rows and invalid rows, with success rate and error samples per run. Edits take effect on the next run. One job runs one template; use one job per site.
- Jobs run Extract Templates, not Web Search Agents. For a scheduled agent job (a weekly trigger watch), run the agent from the user's own scheduler.

## 4. When no template exists: generate one

Use generation only when the catalog has nothing for the site and the data will be pulled repeatedly (a vertical directory, an association's member list, a marketplace's partner directory, a conference's exhibitor pages). For a one-off, use Extract or a Web Search Agent instead.

```bash
curl -s -X POST https://sdk.nimbleway.com/v2/extract/templates/generations \
  -H "Authorization: Bearer $NIMBLE_API_KEY" -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.example-conference.com/2026/exhibitors",
    "prompt": "Exhibitor directory page. Extract every exhibitor: company name, website, booth number, sponsorship tier, category, and the exhibitor profile URL.",
    "name": "example_conference_exhibitors",
    "output_schema": {"type": "array", "items": {"type": "object", "properties": {"company": {"type": "string"}, "website": {"type": "string"}, "tier": {"type": "string"}}}}
  }'
```

- Required: `url` (a representative example page) and `prompt`. Optional: `name` (lowercase, digits and underscores), `input_schema`, `output_schema`, `metadata`.
- Poll `GET /v2/extract/templates/generations/{generation_id}` until `status` is terminal. On success it reports `generated_version` with its `input_schema`, `output_schema` and `samples`. Check the samples on two or three other pages of the same type before trusting it.
- Refine with `POST /v2/extract/templates/generations` and `{"from_extract_template": "<name>", "prompt": "Also capture the booth number; it was missing for sponsors"}`.
- Manage: `GET /v2/extract/templates/{name}/versions` and `/versions/{version_id}` to compare versions, `PATCH /v2/extract/templates/{name}` (JSON Patch: `[{"op": "replace", "path": "...", "value": ...}]`), `DELETE /v2/extract/templates/{name}`.
- MCP equivalents: `nimble_extract_templates_generate`, `nimble_extract_templates_generation_status`, `nimble_extract_templates_update_from_template`. Only generate when the user asked for a reusable template.

## 5. Make the data decision-grade

- **Keys and timestamps.** Store every row with the CRM account ID or domain, template name and version, collection timestamp (UTC), location or country, and `tag`. Keep raw JSON next to the cleaned table so fields can be re-derived.
- **Entity mapping.** Job and review sites name employers their own way ("Rippling People Center Inc.", a subsidiary, a staffing agency posting for a client). Map employer name → domain → CRM account and keep the map under version control. Exclude staffing agencies and reposts unless the user wants them.
- **Same panel every run.** Changes to the account list, keywords, prompts or locations break trends. Version the input list and log every change.
- **Missing is not zero.** A failed or empty fetch is a gap, not "no open roles" or "not mentioned". Track success rate per run and per site; alert when it drops.
- **Dedupe**: job posts on job ID (the same role is often posted in many cities), reviews on review ID, listings on place ID.
- **Use the event's own date**: posting date, review timestamp, answer collection date, not the collection run.
- **AI answers vary.** Sample several phrasings of each buyer prompt, in each country that matters, on a fixed cadence; report mention share and cited sources over time, not one answer.
- **Sanity checks**: week-over-week jumps, duplicate rows, template field drift after a site redesign (Nimble-managed templates heal, but check the fields you depend on).
- **Turn data into actions**: a score per account (for example new sales roles in 30 days, new senior hire, rating drop) and a threshold that routes it to an owner, rather than a raw table.

## 6. Compliance

- Collect public pages only: no logins, created accounts, paywalls or CAPTCHA bypassing.
- **Minimize personal data.** Drop reviewer names, job-poster identities and profile links the analysis does not need; keep business contact details only for businesses (a dental practice's public phone), not for individuals unless the task needs it and the user's privacy rules allow it.
- Outbound use of web data follows the user's own rules: suppression lists, opt-outs, GDPR, CASL and CAN-SPAM decide who is contacted, not the dataset.
- Document lineage for legal or RevOps: the sites, the templates, the cadence, and what is and is not collected.
- Keep request volume proportionate; Jobs and batches handle pacing, so do not hand-roll parallel floods on top of them.

---
name: nimble-databricks-data-products
description: |
  Builds Databricks data products from live web data, end to end: discovers the right Nimble
  web-data agents, scrapes into Delta tables, and produces an AI/BI dashboard and/or a deployed
  Databricks App — a table → dashboard → app workflow, for production data products or quick demos.
  Use whenever a request pairs live or scraped web data WITH a Databricks destination — e.g. "scrape
  Amazon/Walmart prices into a Delta table and build a dashboard", "load Zillow/Instagram/Maps/search
  results into Databricks and build a dashboard or app", "showcase Nimble + Databricks to a prospect".
  Prefer it over nimble-web-expert or competitor-intel when the data lands in Databricks. Do NOT use
  for one-off web fetches or CSV exports with no Databricks destination — use nimble-web-expert
  instead. Do NOT use for competitor or company research briefings — use competitor-intel or
  company-deep-dive instead. Do NOT use for generic Databricks work with no Nimble/web-data angle —
  use the official databricks-* skills instead.
allowed-tools:
  - Bash(databricks:*)
  - Bash(python3:*)
  - Bash(bash:*)
  - Bash(jq:*)
  - Bash(npm:*)
  - Read
  - Write
  - Edit
  - AskUserQuestion
  - Skill
metadata:
  author: Nimbleway
  version: 0.25.0
---

# Nimble on Databricks — data products builder

Turn a natural-language brief like
`pricing analysis on dog products from walmart and amazon` into working Databricks data products:
**discover agents → ingest live web search data into Delta → build dashboard and/or app → deliver links.**
Equally at home for a quick demo or a real, reusable data product.

You are the orchestrator. Databricks mechanics are delegated to the official `databricks-*`
skills (see `references/databricks-skills.md`); this skill owns the **Nimble glue and the gaps**
(agent discovery, ingestion-from-agents, the AI/BI dashboard JSON, branding).

## Golden rules

- **Discover, don't assume.** Read agent names via `nimble_agent_list()`, input params via
  `nimble_agent_describe('<agent>')`, and output fields by probing one call (`to_json(parsing[0])`) —
  never hardcode from memory (Amazon search takes `keyword`, not `query`).
- **Probe before fanning out.** Run one call per source first to learn its localization flag, field
  names, and value formats — sources differ (some return numeric prices, others currency strings).
- **One statement per Statements API call.** Multiple `;`-separated statements in one call are a parse error.
- **Each Bash call is a fresh shell.** Env vars and `cd` don't persist — set them inline. See `references/preflight.md`.
- **Fail fast, then confirm.** Run Phase 0 preflight first; recommend a warehouse + writable schema, then confirm before writing.
- **Always ask the deliverable.** Table / +dashboard / +app is a per-run choice.
- **Branding is always on, neutral.** "Powered by Nimble" + light theme + yellow accent. See `references/branding.md`.
- **Leave artifacts in place.** No teardown.
- **Show your work and the headline.** End with URLs and the one-sentence insight (e.g. the price gap).

## Workflow

Track these as todos so nothing is skipped.

### Phase 0 — Preflight (read-only, fail fast)
Lean on the **`databricks-core`** skill for the generic checks.
1. `databricks current-user me` → confirm auth; capture the username (for the default schema).
2. Find a **RUNNING** SQL warehouse: `databricks warehouses list`. Prefer one already RUNNING; if none, offer to start one.
3. **Integration gate** — confirm these exist:
   `nimble_integration.tools.{nimble_search, nimble_extract, nimble_agent_run, nimble_agent_list, nimble_agent_describe}`.
   Quick check: `databricks functions list nimble_integration tools`.
   **If missing → STOP** and walk the user through `references/install-nimble-integration.md`
   (Nimble cookbook). Do not try to auto-install.
4. **Recommend + confirm** the target: a warehouse and a writable `catalog.schema`
   (default `users.<username>`). Verify writability — some shared catalogs deny `CREATE TABLE`.
   Present the recommendation and let the user confirm or override before writing.

Details + exact commands: `references/preflight.md`.

### Phase 1 — Interpret the brief + clarify (AskUserQuestion)
Parse the brief into: **domain/entity · search terms · sources · analysis goal**.
Then ask (batch into one AskUserQuestion call):
- **Deliverable** — always ask: table / table + dashboard / table + dashboard + app.
- **Sources** — confirm the agents you matched (e.g. Amazon + Walmart SERP).
- **Volume** — default ~8–10 search terms, ~100+ rows/source.

Keep the brief's intent (the "analysis goal") — it picks the Phase 4 template and the headline.

### Phase 2 — Discover agents + map a unified schema
See `references/nimble-agents.md`.
1. `nimble_agent_list()` via SQL, filter by the source/domain keywords.
2. For each chosen agent: `nimble_agent_describe('<name>')` → read its input params (required ones,
   exact names, localization/pagination flags). Output fields come from the §2.5 probe, not here.
3. Design **one unified table** with a `source` column + a normalized core
   (`product_name, price, currency, rating, review_count, brand, url, …`), keeping only fields the
   chosen agents actually emit. Multi-source comparison hinges on the shared columns.

### Phase 3 — Ingest (control table + one set-based call)
See `references/nimble-agents.md` for the full SQL. Drive ingestion from a **control table**, not
per-keyword files — it's reproducible and expandable (add a row, re-run).
0. **Probe ONE call per source first (fail fast).** Before fanning out, run a single
   `nimble_agent_run` per source and check: status, the real field names, the localization flag, and
   whether a price casts cleanly. This catches the Walmart-class surprises (localization, currency-
   string prices, `product_price` vs `price`) in ~40s instead of after a wasted full round. Highest-
   leverage step — see `nimble-agents.md` §2.5.
1. Create a **control (queries) table** `<schema>.<table>_queries` (source, agent, keyword,
   params_json, localization, enabled) and seed one row per (source × term). `params_json` uses each
   agent's **real** param name (from `input_properties`); set **localization per agent** (e.g.
   `amazon_serp` true, `walmart_serp` false).
2. Create the **unified results table** (`source` column + normalized core + `raw VARIANT`).
3. Run **one INSERT** that calls `nimble_agent_run(q.agent, q.params_json, q.localization)` via a
   correlated `LATERAL` join over the control table, with a `/*+ REPARTITION(N) */` hint (N ≈ enabled
   rows, kept modest — high parallelism can trip API rate limits) so the agent calls run in parallel.
   It's one long statement → run it async with `bash scripts/ingest.sh <WH> ingest.sql`.
4. **Reconcile against the control table** (LEFT JOIN): a term that lands no items returns an empty
   result, and a correlated LATERAL drops empty rows — so reconcile to confirm every source is
   covered. If a source shows 0, re-check its localization flag (per-agent) and casts before
   building; see `nimble-agents.md` §6 for the diagnostic order.

### Phase 4 — Build the deliverable(s)
Choose a **template** from the matched agents' `vertical`/`entity_type`:

| Vertical | Dashboard/app shape |
|----------|---------------------|
| Ecommerce (SERP/PDP/CLP) | KPIs; listings & avg price by source/keyword; sponsored share; price-vs-rating scatter; product table with Open links; multi-source → comparison bars + best-effort item-level price gap |
| Social | volume/engagement by account/post; top-content table; like/follower distributions |
| Real Estate | price & price/sqft; listings by location; beds/baths breakdowns |
| Maps / Local | avg rating; review counts; places table |
| LLM / AEO | source/answer presence; share-of-voice; citation table |
| _fallback_ | KPIs + 2 categorical bars + the raw table (works off any `output_schema`) |

**Comparison depth (hybrid):** always build the aggregate/category comparison; *additionally* try
best-effort item-level matching across sources (normalize brand + key tokens). If confident matches
exist, add a "same-product price gap" view; otherwise keep the aggregate comparison and note that
item-level matching wasn't confident.

- **Dashboard** → use `scripts/build_dashboard.py` (compact spec → valid `serialized_dashboard`,
  create + publish). It bakes in every Lakeview gotcha. Read `references/dashboard-cookbook.md` for
  the spec format and recipes.
- **App** → follow `references/app-cookbook.md` (delegates scaffold/deploy to `databricks-apps`;
  adds the Nimble-specific SQL, branding, and the numeric-string / light-mode gotchas).
- **Branding** → `references/branding.md` (always applied).

### Phase 5 — Verify, deliver & share
- Publish the dashboard / confirm the app is `RUNNING`; collect URLs.
- Summarize what was built and the **headline insight** (the comparison takeaway).
- **Offer to share** the dashboard/app link — if a Slack or Notion connector is available, offer to
  post it there (Slack = the link + headline; Notion = a short dated page). Mention once; don't nag.
- **Suggest next steps** with sibling skills, e.g. `competitor-intel` / `company-deep-dive` for
  business signals on the brands surfaced, or `nimble-web-expert` for a one-off deeper pull.
- Offer iterations (more charts, item-level matching, theming, a scheduled refresh job).

## Reference map
- `references/databricks-skills.md` — which official `databricks-*` skill to use per phase.
- `references/install-nimble-integration.md` — setup when the integration gate fails.
- `references/preflight.md` — auth, warehouse, writable-schema discovery (exact commands).
- `references/nimble-agents.md` — discovery, schema mapping, ingestion SQL + gotchas.
- `references/dashboard-cookbook.md` — Lakeview JSON recipes + every gotcha (authoritative).
- `references/app-cookbook.md` — AppKit demo app glue + gotchas.
- `references/branding.md` — "Powered by Nimble", logo, colors.
- `scripts/ingest.sh` — async statement fan-out + poll.
- `scripts/build_dashboard.py` — compact spec → create + publish a dashboard.
- `assets/nimble-logo.png` — the Nimble mark for app branding.

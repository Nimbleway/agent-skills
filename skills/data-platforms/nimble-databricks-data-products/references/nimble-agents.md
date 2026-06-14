# Nimble agents — discover, introspect, ingest

This is the heart of the skill: find the right agents, learn their exact I/O at runtime, and load
their output into a Delta table. **Never hardcode an agent's params or output from memory** — read
them live. (Example trap: Amazon search wants `keyword`, not `query`.)

## 1. Discover agents

> **Agent names in this file (`amazon_serp`, `walmart_serp`, `zillow_*`, …) are illustrative only.**
> The catalog evolves — always discover the actual names at runtime with `nimble_agent_list()` and
> introspect with `nimble_agent_describe`. Never depend on a hardcoded name.

`nimble_agent_list()` returns one row per agent: `name, display_name, description, vertical,
entity_type, domain, managed_by, is_public`. Query it via SQL:

```sql
SELECT name, display_name, vertical, entity_type, domain
FROM nimble_integration.tools.nimble_agent_list()
WHERE lower(domain) LIKE '%amazon%' OR lower(name) LIKE '%amazon%'
ORDER BY name;
```

Match the brief's **sources** (amazon, walmart, zillow, instagram, google_maps, …) against
`name`/`domain`, and pick the `entity_type` that fits the goal:
- **SERP** (search results) → best for "find products by keyword" / assortment / pricing.
- **PDP** (product detail) → deep per-URL detail; needs URLs as input.
- **CLP / best_sellers** → category/ranking pages.

For most "analysis on X from <retailers>" briefs, **`*_serp`** is the right call (keyword in →
many product rows out).

## 2. Introspect the chosen agents — read the INPUTS

Read each chosen agent's input parameters at runtime with `nimble_agent_describe` (one row per
param) — never hardcode them:
```sql
SELECT param_name, required, type, is_localization_param, is_pagination_param, default_value, examples_json
FROM nimble_integration.tools.nimble_agent_describe('amazon_serp')
ORDER BY required DESC;
```
- **The required param is your search term** — e.g. `keyword`, not `query`. Use its exact
  `param_name` when you build `params_json` in §3/§4.
- **`is_localization_param`** flags the localization input (e.g. `zip_code`) and **`is_pagination_param`**
  the pagination input (e.g. `page`). `default_value` / `examples_json` give sane starting values.

Do this for **every** chosen source — param names differ across agents.

> **Output fields come from a probe, not from `describe`.** `nimble_agent_describe` returns inputs
> only (by design — output schemas are large and best seen from a real call). Learn the emitted
> fields by running the agent once and inspecting the payload — see §2.5 (`to_json(parsing[0])`).
> Field names differ across retailers even within a vertical (Amazon emits `price`/`rating`, Walmart
> emits `product_price`/`product_rating`); §4 coalesces the variants into one normalized column.

## 2.5 Probe ONE call per source before fanning out (fail fast)

This is the highest-leverage check in the whole skill. Before seeding the control table and running
all N calls, run **one** `nimble_agent_run` per source and inspect three things — it surfaces the
exact Walmart-class surprises in ~40s instead of after a wasted full round:

```sql
SELECT status,
       to_json(parsing[0]) AS first_item,                       -- see the REAL field names
       parsing[0]:price, parsing[0]:product_price               -- which price field exists?
FROM nimble_integration.tools.nimble_agent_run('walmart_serp', to_json(named_struct('keyword','dog food')), true);
```
Decide three things from the probe, per source:
1. **localization flag** — localization is **per-agent**, not global. If the probe comes back with an
   empty `parsing`, flip the flag and probe again before concluding the term is empty — agents differ
   on whether they expect `true` or `false`.
2. **field names** — they vary by source (e.g. `price` vs `product_price`); note them for the
   coalesce in §4.
3. **value format** — sample a price. Some sources return a plain number; others return a
   currency-formatted string like `"$125.99"` (or an empty string), which a bare
   `CAST(... AS DOUBLE)` rejects with `INVALID_VARIANT_CAST`. Use the defensive cast in §4 so either
   shape works.

## 3. Two tables: a control table + the unified results table

Don't hand-write one SQL file per keyword. Drive everything from a **control (queries) table** so the
demo is set-based, reproducible, and expandable — add a row, re-run, done.

```sql
-- Control table: one row per (source × search term). The single source of truth for what to scrape.
CREATE OR REPLACE TABLE <schema>.<table>_queries (
  source       STRING,   -- 'amazon' | 'walmart' | …
  agent        STRING,   -- the Nimble agent name, e.g. 'amazon_serp'
  keyword      STRING,   -- the search term (for labelling/inspection)
  params_json  STRING,   -- full params for nimble_agent_run, built from the agent's input_properties
  localization BOOLEAN,
  enabled      BOOLEAN
);

INSERT INTO <schema>.<table>_queries VALUES
  -- localization is PER-AGENT (from the §2.5 probe): amazon_serp=true, walmart_serp=false.
  ('amazon','amazon_serp','dog food',  to_json(named_struct('keyword','dog food')),  true,  true),
  ('walmart','walmart_serp','dog food',to_json(named_struct('keyword','dog food')),  false, true),
  ('amazon','amazon_serp','dog toys',  to_json(named_struct('keyword','dog toys')),  true,  true);
  -- … one row per (source × term). params_json uses each agent's REAL param name.

-- Results table: unified, with a source column + normalized core + a raw VARIANT catch-all.
CREATE OR REPLACE TABLE <schema>.<table> (
  source STRING, search_keyword STRING, position INT,
  product_name STRING, brand STRING, price DOUBLE, currency STRING,
  rating DOUBLE, review_count INT, sponsored BOOLEAN,
  product_url STRING, image_url STRING,
  raw VARIANT, ingested_at TIMESTAMP
) COMMENT 'Nimble demo — <brief>. Powered by Nimble.';
```
Adjust the results columns to the vertical (social → `account, post_url, likes, …`; real estate →
`address, price, beds, baths, sqft, …`). Always keep `source`, `raw`, `ingested_at`. Keep sources in
the **same vertical** so one normalized schema fits all of them.

## 4. One set-based ingest (lateral correlated UDTF)

A **single INSERT** runs the agent for every enabled control row and explodes the results — no
per-keyword files. The agent name and params come from the control-table columns via a correlated
`LATERAL` call (verified working on Databricks):

Two rules make this robust across retailers (learned the hard way — see the gotchas after the SQL):
- **Coalesce field-name variants** (`price` vs `product_price`) so one INSERT serves all sources.
- **Defensive numeric casts** — strip non-numerics before casting, because some retailers return
  currency strings (`"$125.99"`) or `""`. Use `try_cast(regexp_replace(...))`, never a bare `CAST`.

```sql
INSERT INTO <schema>.<table>
SELECT /*+ REPARTITION(8) */   -- ≈ number of enabled rows; keep modest (see note below)
  q.source,
  q.keyword AS search_keyword,
  try_cast(v.value:position AS INT),
  CAST(coalesce(v.value:product_name, v.value:title) AS STRING) AS product_name,
  initcap(split(trim(CAST(coalesce(v.value:product_name, v.value:title) AS STRING)), ' ')[0]) AS brand,
  -- defensive numeric cast: strip $, commas, etc. then try_cast (NULL on junk instead of erroring)
  try_cast(regexp_replace(CAST(coalesce(v.value:price, v.value:product_price) AS STRING), '[^0-9.]', '') AS DOUBLE) AS price,
  CAST(coalesce(v.value:currency, '$') AS STRING) AS currency,
  try_cast(regexp_replace(CAST(coalesce(v.value:rating, v.value:product_rating) AS STRING), '[^0-9.]', '') AS DOUBLE) AS rating,
  try_cast(regexp_replace(CAST(coalesce(v.value:review_count, v.value:ratings_count) AS STRING), '[^0-9]', '') AS INT) AS review_count,
  try_cast(v.value:sponsored AS BOOLEAN) AS sponsored,
  CAST(coalesce(v.value:product_url, v.value:url) AS STRING) AS product_url,
  CAST(coalesce(v.value:image_url, v.value:image) AS STRING) AS image_url,
  v.value AS raw,
  current_timestamp()
FROM <schema>.<table>_queries q,
LATERAL nimble_integration.tools.nimble_agent_run(q.agent, q.params_json, q.localization) AS r,
LATERAL variant_explode(r.parsing) AS v
WHERE q.enabled AND r.status = 'success';
```
Adjust the coalesced field names to whatever §2.5 actually showed for your sources — these are
examples, not a fixed list.

Key points:
- **`/*+ REPARTITION(N) */`** spreads the agent calls across N Spark tasks so they run **in
  parallel**. Without it, a tiny control table sits in one partition and the calls run serially
  (N × ~40s). Set **N ≈ the number of enabled rows, and keep it modest** — each task is a live agent
  call, so very high parallelism can trip API rate limits (HTTP 429). A couple dozen is plenty; if
  you have hundreds of terms, batch them across runs rather than firing all at once.
- It's still **one long-running statement**, so submit it **async and poll** — don't use a 50s
  `wait_timeout`. Use the helper: `bash scripts/ingest.sh <WH> ingest.sql`.
- A bare `CAST(v.value:price AS DOUBLE)` throws `INVALID_VARIANT_CAST` the moment a retailer returns
  a formatted string — the `try_cast(regexp_replace(...))` form is harmless on already-numeric data
  (Amazon) and saves a whole wasted round on string-formatted data (Walmart).

To **expand later**: `INSERT INTO <table>_queries VALUES (…)` more rows, then re-run the ingest
(optionally guard with `WHERE q.enabled AND <not already scraped>`). That's the whole point of the
control table — no new files, no edits to the ingest SQL.

## 5. Run it (async, one statement)

```bash
bash scripts/ingest.sh "$WH" ingest.sql      # submits the INSERT async, polls to completion
```

## 6. Verify against the control table — confirm every source is covered

Always **reconcile results against the control table** so you know each source landed data:
1. The UDTF returns an **empty result set** for a term that yields no items (rather than an error row).
2. A correlated inner `LATERAL` **drops any control row that produced no items** — so an empty source
   won't appear in the output unless you reconcile against the control table.

```sql
SELECT q.source, q.keyword, COALESCE(r.n, 0) AS rows
FROM (SELECT source, keyword FROM <schema>.<table>_queries WHERE enabled) q
LEFT JOIN (SELECT source, search_keyword AS keyword, COUNT(*) n
           FROM <schema>.<table> GROUP BY source, search_keyword) r
  USING (source, keyword)
ORDER BY rows;     -- any 0 = that (source,keyword) landed no items
```
**Diagnostic when one source has 0 rows but another is healthy.** Work through these in order before
concluding the term itself is empty:
1. **localization** — the flag is per-agent; flip it for that source and re-run (the §2.5 probe should
   have settled this up front). This is the most common cause.
2. **cast failure** — a bare `CAST` on a currency-string price (`"$125.99"`) aborts the INSERT; switch
   to the defensive `try_cast(regexp_replace(...))` from §4.
3. **field-name mismatch** — the source uses `product_price`/`title` etc.; widen the coalesce.
4. otherwise — use a sibling agent for that source (e.g. a PDP agent over discovered URLs), or proceed
   with the sources that returned data and tell the user which one had no coverage for these terms.

Re-run is cheap: fix the control row (e.g. flip localization) or the cast, then re-run the ingest —
optionally `DELETE FROM <table> WHERE source = '<that source>'` first so you don't double-count.

## Search-term expansion
If the brief names a domain but not terms (e.g. "dog products"), expand to ~8–10 sensible
subcategories (dog food, treats, toys, beds, leashes, collars, crates, harness) and confirm the list
with the user in Phase 1 — then seed the control table with them.

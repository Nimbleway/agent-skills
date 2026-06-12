# Databricks App cookbook (AppKit analytics demo)

Scaffolding/deploy mechanics belong to the official **`databricks-apps`** / **`databricks-app-design`**
skills — follow them. This file adds the **Nimble-specific glue** and the gotchas that cost real time.

Use an app (vs. just a dashboard) when the user wants an interactive, branded, sharable web UI.

## Flow
1. **Manifest** → confirm the `analytics` plugin + its required field:
   `databricks apps manifest` (analytics requires `analytics.sql-warehouse.id`).
2. **Init** (warehouse must be RUNNING):
   ```bash
   databricks apps init --name <app-name> \
     --description "<brief> · Powered by Nimble" \
     --features analytics \
     --set analytics.sql-warehouse.id=<WH> \
     --run none
   ```
   Name ≤26 chars, lowercase/hyphens/numbers.
3. **SQL queries** → put `.sql` files in `config/queries/`. Each is a query key. Use `:param`
   placeholders annotated with `-- @param name TYPE`:
   ```sql
   -- @param keyword STRING
   -- @param source STRING
   SELECT product_name, source, price, rating, review_count, product_url
   FROM users.<me>.<table>
   WHERE (:keyword = '' OR search_keyword = :keyword)
     AND (:source  = 'all' OR source = :source)
   ORDER BY review_count DESC NULLS LAST
   LIMIT 600
   ```
   Keep result sets < 1 MB (LIMIT / aggregate) or the analytics endpoint errors. After writing them:
   `npm run typegen` (needs the warehouse running) → generates `shared/appkit-types/analytics.d.ts`.
   Read those generated types and use the exact field names in the UI.
4. **UI** (`client/src/…`) — build a single Explorer page driven by filters; see the patterns below.
5. **Branding** — see `references/branding.md` (logo into `client/public/`, header + footer).
6. **Validate** → `databricks apps validate` (typecheck + lint + build + smoke test). Fix all.
7. **Deploy** → `databricks apps deploy` → wait for `app_status: RUNNING`; the URL is printed.
   Confirm: `databricks apps get <app-name> -o json | jq '{url, app:.app_status.state}'`.

## UI patterns (AppKit / `@databricks/appkit-ui/react`)
- **Data**: `const { data, loading, error } = useAnalyticsQuery('query_key', params)`.
  **`params` MUST be `useMemo`'d** or the hook refetch-loops:
  `const params = useMemo(() => ({ keyword: sql.string(kw), source: sql.string(src) }), [kw, src])`.
  Import helpers: `import { sql } from '@databricks/appkit-ui/js'`.
- **Charts** auto-fetch via `queryKey`+`parameters`; pick axes with `xKey`/`yKey`:
  `<BarChart queryKey="by_keyword" parameters={p} xKey="keyword" yKey="listings" orientation="horizontal" height={320} />`.
  Available: `BarChart, LineChart, AreaChart, ScatterChart, PieChart, DonutChart, HeatmapChart, RadarChart`.
  (`xKey`/`yKey`, `orientation`, `colors`, `height`, `showLegend` are common props.)
- **Tables**: `DataTable` auto-fetches + filters/sorts/paginates from a queryKey. For a custom
  cell (e.g. an "Open ↗" anchor), build a small table with the `Table…` primitives + a client-side
  search `Input` + sort `Select` over the `useAnalyticsQuery` data.

## Gotchas (these bit us in the POC)
1. **Numbers arrive as strings.** The analytics JSON serializes DOUBLE/BIGINT/INT as strings, even
   though the generated types say `number`. Calling `.toFixed()` or doing arithmetic crashes the page
   (`x.toFixed is not a function`). **Coerce everything**: a `toNum(v)=>{const n=Number(v); return
   Number.isFinite(n)?n:null}` helper, used in every formatter, sort comparator, and `.toFixed()`.
2. **Force light mode** (branding is neutral-light): set `<html lang="en" class="light">` in
   `client/index.html`. AppKit applies dark via a `:root:not(.light)` media query, so the `light`
   class disables it. All components use semantic tokens, so nothing else needs changing.
3. **Update the smoke test.** `tests/smoke.spec.ts` ships asserting the template's home page. After you
   replace the UI, update its selectors to match your page (unique headings, KPI labels, a known
   placeholder). Use real Playwright locators (`getByRole`, `getByText`, `getByPlaceholder`); avoid
   ambiguous `getByText` that matches multiple nodes (add `.first()` or use unique strings). If you
   keep multiple routes, the template's home/heading checks must still pass or `validate` fails.
4. Don't override `@databricks/appkit` versions; don't use custom endpoints for SELECTs (use
   `config/queries/`); don't use `useAnalyticsQuery` for non-warehouse data.

## Minimal query set for an ecommerce comparison demo
`overview_kpis.sql` (params keyword, source) · `by_keyword.sql` · `by_source.sql` (avg price/rating
per source) · `price_vs_rating.sql` · `products.sql` (the table) · `keywords.sql` (filter options).
Mirror the column names from the unified ingest table.

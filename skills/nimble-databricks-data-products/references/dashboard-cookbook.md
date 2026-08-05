# AI/BI (Lakeview) dashboard cookbook — AUTHORITATIVE

There is no official Databricks skill for AI/BI dashboards, so this file + `scripts/build_dashboard.py`
are the source of truth. **Prefer the script** — it bakes in every gotcha below. Hand-rolling the
serialized JSON is the #1 source of broken dashboards.

## TL;DR workflow
1. Write a **compact spec JSON** (datasets + widgets) — see the format in `scripts/build_dashboard.py`'s header.
2. `python3 scripts/build_dashboard.py --spec spec.json` → it creates + publishes and prints the URLs.
3. To revise: edit the spec, rerun with `--dashboard-id <id>` (it PATCHes + republishes).

The script handles: counter top-level-aggregate rule, one-line `queryLines`, full table column
objects, link columns, filter associativity, create/patch/publish, and URL building.

## Spec quick reference (what you write)
```json
{
  "display_name": "🐶 Amazon vs Walmart — Dog Products  ·  Powered by Nimble",
  "warehouse_id": "<WH>",
  "datasets": [{"name": "main", "query": "SELECT * FROM users.me.dog_products_compare"}],
  "widgets": [ /* text, filter, counter, bar, line, area, scatter, pie/donut, table */ ]
}
```
- **pos** `[x, y, w, h]` on a **6-column** grid. Lay rows top-to-bottom.
- Field shorthand: a **string** = a column (categorical dimension); `{"expr":"AVG(\`price\`)"}` = a measure.

## Recipes (per widget)

**Title + branding text** (always include — branding is on):
```json
{"type":"text","md":"# 🐶 Dog Products: Amazon vs Walmart\n_Live web search · **Powered by Nimble**_","pos":[0,0,6,1]}
```

**Global filters** (put a couple near the top; they slice every widget on the SAME dataset):
```json
{"type":"filter","dataset":"main","field":"source","title":"Source","select":"single","pos":[0,1,2,1]}
{"type":"filter","dataset":"main","field":"search_keyword","title":"Keyword","select":"multi","pos":[2,1,2,1]}
```

**KPI counters** (one measure each):
```json
{"type":"counter","dataset":"main","label":"Listings","expr":"COUNT(`product_name`)","pos":[0,2,2,3]}
{"type":"counter","dataset":"main","label":"Avg Price","expr":"AVG(`price`)","format":"currency","pos":[2,2,2,3]}
{"type":"counter","dataset":"main","label":"Avg Rating","expr":"AVG(`rating`)","format":"number","decimals":2,"pos":[4,2,2,3]}
```

**Bars** (grouped; horizontal reads well for many categories):
```json
{"type":"bar","dataset":"main","x":"search_keyword","y":{"expr":"COUNT(`product_name`)"},"orientation":"horizontal","title":"Listings per keyword","pos":[0,5,3,6]}
{"type":"bar","dataset":"main","x":"source","y":{"expr":"AVG(`price`)"},"color":"source","title":"Avg price by source","pos":[3,5,3,6]}
```

**Scatter** (raw points; great for price vs rating):
```json
{"type":"scatter","dataset":"main","x":"price","y":"rating","color":"source","size":"review_count","pos":[0,11,3,7]}
```

**Pie / donut** (share):
```json
{"type":"pie","dataset":"main","color":"source","angle":{"expr":"COUNT(`product_name`)"},"title":"Listings share by source","pos":[3,11,3,7]}
```

**Table with clickable links** (lead with the Open link):
```json
{"type":"table","dataset":"main","title":"Products (sortable / searchable)","pos":[0,18,6,9],
 "columns":[
   {"field":"product_url","title":"Open","link":true},
   {"field":"product_name","title":"Product"},
   {"field":"source","title":"Source"},
   {"field":"search_keyword","title":"Keyword"},
   {"field":"price","title":"Price","kind":"number","number_format":"$0,0.00"},
   {"field":"rating","title":"Rating","kind":"number","number_format":"0.0"},
   {"field":"review_count","title":"Reviews","kind":"integer"},
   {"field":"sponsored","title":"Ad","kind":"boolean"}
 ]}
```

## The gotchas (why the script exists)

1. **Counter expression must be a top-level aggregate.** `AVG(\`price\`)` works; `ROUND(AVG(\`price\`),2)`
   makes AI/BI treat the field as a GROUP BY *dimension* → the tile shows **"No data."** Round via the
   display `format`/`decimals`, never in the SQL expression. (The script warns if it sees a wrapper.)
2. **`queryLines[]` are joined with NO whitespace.** A multi-line dataset query welds tokens
   (`avg_ratingFROM…`) → parse error. Keep each dataset query on **one line** (the script collapses
   whitespace for you).
3. **Tables need the full shape or show "no fields selected."** Required spec-level keys:
   `itemsPerPage, paginationSize, invisibleColumns, withRowNumber, condensed, allowHTMLByDefault`;
   and every column needs `displayName, order, visible, type, displayAs` (+ link/image/boolean
   templates). The script emits all of this.
4. **Clickable URL** = column `displayAs:"link"` + `linkUrlTemplate:"{{ @ }}"` (+ `linkTextTemplate`).
   There is a real `"link"` display type (cached dashboards rarely use it, but it's valid).
5. **Filters only span widgets on the same dataset**, and the filter query needs the magic
   associativity field `COUNT_IF(\`associative_filter_predicate_group\`)`. Keep all filtered widgets
   on one dataset (e.g. `SELECT *`) and let widgets aggregate via `disaggregated:false`.
6. **Pre-aggregated datasets break global filters.** If you must cap a chart (e.g. top-15 brands via a
   separate `GROUP BY … LIMIT 15` dataset), know that the shared filters won't reach it — note that to
   the user, or keep it on the main dataset.
7. **Lifecycle:** create `POST /api/2.0/lakeview/dashboards`; update `PATCH …/{id}` (needs current
   `etag`); make it live `POST …/{id}/published` with `{"embed_credentials":true}`. URL:
   `https://<host>/dashboardsv3/<id>/published`.

## Branding on dashboards
- Prefix `display_name` and the title text widget with the Nimble mark/“Powered by Nimble.”
- Pass `"colors": ["#F2F23B", …]` is not in the compact spec by default; if you want the yellow
  accent as series color 1, add it to a chart's spec via `references/branding.md` guidance (or leave
  default palette — neutral is fine).

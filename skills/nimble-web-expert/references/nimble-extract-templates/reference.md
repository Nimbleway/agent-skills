---
name: nimble-extract-templates-reference
description: |
  Reference for Nimble Extraction Templates — reusable, site-specific structured scrapers.
  Load for Step 0 when a named site has a direct item to look up (by URL or identifier).
  Covers: discover (list), inspect (get → input_schema/output_schema), run/async/batch,
  response shapes, and the no-template→Web Search Agent routing rule. Existing templates only.
---

# nimble extract:templates — reference

An **Extraction Template** is a reusable, preconfigured parser for one specific site: set up
once against that site's structure, then run repeatedly against known items (a URL, an ASIN,
a business ID) without rediscovering anything. Use a template whenever a matching one exists —
it returns clean, structured fields with zero selector work.

**Existing templates only.** Building or publishing new templates is out of scope here. If no
template covers a site, do **not** fall back to a raw `extract` (that pushes parsing onto the
user) and do **not** try to build one — route to a **Web Search Agent** instead
(`references/nimble-agents/reference.md`), which reasons about any site's structure without a
maintained template.

REST/SDK surface: `POST /v2/extract/templates/{run,async,batch}`.

## Table of Contents

- [1. Discover templates](#1-discover-templates)
- [2. Inspect a template (schema)](#2-inspect-a-template-schema)
- [3. Run a template (realtime)](#3-run-a-template-realtime)
- [4. Run async](#4-run-async)
- [5. Run batch](#5-run-batch)
- [Response shapes](#response-shapes)

---

## 1. Discover templates

```bash
# List templates (paginated). No server-side search — filter client-side by
# display_name / name / metadata.domain for the target site.
nimble --client-source nimble-agent-skills extract:templates list --limit 100
```

**Parameters:** `--limit` (int), `--offset` (int).

**List JSON shape** — each item carries the template `name` (the identifier used to run it)
and its published version's schemas:

```json
{
  "items": [
    {
      "id": "…",
      "name": "reddit_post_comments_2026_07_19_8acvxcb0",
      "published_version": {
        "input_schema":  { "type": "object", "required": ["…"], "properties": { … } },
        "output_schema": { "type": "array",  "items": { … } },
        "metadata": { "display_name": "Reddit Post Comments", "domain": "reddit.com",
                      "vertical": "Social Media", "entity_type": "Product Detail Page (PDP)" }
      }
    }
  ]
}
```

Match by `metadata.domain` / `metadata.display_name`; run with the top-level `name`
(NOT the display_name).

---

## 2. Inspect a template (schema)

Always inspect the schema before running — it tells you the required inputs and the exact
output shape.

```bash
nimble --client-source nimble-agent-skills extract:templates get \
  --extract-template-name <template_name>
```

**Parameter:** `--extract-template-name` — the template `name` (required).

Read `input_schema.required` for the params you must supply, and `output_schema` for the
records you'll get back (see [Response shapes](#response-shapes)).

---

## 3. Run a template (realtime)

```bash
nimble --client-source nimble-agent-skills extract:templates run \
  --template <template_name> \
  --params '{"subreddit": "frugal", "post_id": "1ikbpew"}'
```

**Parameters:**

| Parameter        | Type            | Description                                                            |
| ---------------- | --------------- | --------------------------------------------------------------------- |
| `--template`     | string          | Template `name` (required)                                            |
| `--params`       | JSON/YAML map   | Inputs matching the template's `input_schema` (required)              |
| `--format`       | string (repeat) | Extra response content formats to include (all disabled by default)   |
| `--localization` | bool            | Enable zip_code/store_id localization (template-dependent)            |

**`--params` is a mapping, not `key=value`.** Pass a JSON object (`'{"asin":"B0…"}'`) or a
YAML mapping — `--params 'key=value'` is rejected.

---

## 4. Run async

For long jobs, submit and poll instead of blocking:

```bash
nimble --client-source nimble-agent-skills extract:templates async \
  --template <template_name> --params '{…}'
```

Returns a task to poll. States: `pending` → `success` or `error`. Poll status with
`nimble tasks get --task-id <id>` until terminal, then fetch with
`nimble tasks results --task-id <id>` (see `references/nimble-tasks/reference.md`).

---

## 5. Run batch

Up to 1,000 items in one call — one shared template, per-item params:

```bash
nimble --client-source nimble-agent-skills extract:templates batch \
  --template <template_name> \
  --input '{"params": {"asin": "B0CHWRXH8B"}}' \
  --input '{"params": {"asin": "B08N5WRWNW"}}'
```

Returns a `batch_id`. Poll with `nimble batches progress --batch-id <id>`, then
`nimble batches get --batch-id <id>` for task IDs and `nimble tasks results --task-id <id>`
for each. See `references/nimble-tasks/reference.md`.

---

## Response shapes

The CLI response envelope is `{ url, task_id, status, data: { parsing }, metadata,
status_code }` — the parsed records live at **`data.parsing`**, so
`--transform "data.parsing"` extracts them in one shot:

```bash
nimble --client-source nimble-agent-skills --transform "data.parsing" \
  extract:templates run --template amazon_pdp --params '{"asin": "B0CHWRXH8B"}'
```

The shape of `data.parsing` follows the template's `output_schema` — **read it from `get`
before parsing:**

| `output_schema.type` | `data.parsing` shape           | Examples                            |
| -------------------- | ------------------------------ | ----------------------------------- |
| `array`              | list of record objects         | list / SERP-style templates         |
| `object`             | one flat record                | detail / PDP-style templates        |
| `object` w/ entities | `{"entities": {"OrganicResult": [...]}}` | search/maps SERP templates |

If a run comes back empty or clearly wrong, say so plainly — a login wall, a changed page
structure, or malformed params are real outcomes. Re-check the `input_schema`, or route to a
Web Search Agent if the site simply isn't a good fit for a fixed template.

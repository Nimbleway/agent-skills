# Delegation map — official Databricks agent skills

This skill is **not** a Databricks tutorial. For generic Databricks mechanics, use the official
skills and follow their guidance. Repo: <https://github.com/databricks/databricks-agent-skills/tree/main/skills>
(install with `databricks aitools install` if they aren't present locally).

| Phase / need | Official skill | What THIS skill adds on top |
|--------------|----------------|------------------------------|
| Auth, CLI, SQL warehouses, Unity Catalog exploration, running SQL | **`databricks-core`** | the Nimble integration gate; writable-schema selection |
| App scaffold / deploy / bundles | **`databricks-apps`**, **`databricks-app-design`**, **`databricks-dabs`** | Nimble query files, branding, numeric-string + light-mode gotchas (`app-cookbook.md`) |
| Persistent storage (rarely needed for demos) | **`databricks-lakebase`** | n/a — demos are read-only |
| Scheduled refresh of the demo (optional) | **`databricks-jobs`**, **`databricks-pipelines`** | an optional "keep the demo fresh" job over the ingest SQL |
| **AI/BI dashboards** | **— no official skill exists —** | `dashboard-cookbook.md` + `scripts/build_dashboard.py` are the **authority** here |
| Model serving / vector search / serverless migration | `databricks-model-serving`, `databricks-vector-search`, `databricks-serverless-migration` | not core to demos; available if a brief calls for it |

**How to use this in practice:** when a phase needs a generic Databricks operation (e.g. "start a
warehouse", "scaffold an app", "create a bundle"), consult the mapped skill rather than improvising.
Reserve your own effort for the Nimble-specific steps, the dashboard JSON, and branding — that is
where this skill's value lives.

If a mapped skill is not installed, tell the user how to get it (`databricks aitools install`) and
proceed with the inline commands in this skill's references as a fallback.

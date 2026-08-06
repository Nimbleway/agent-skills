# Installing the Nimble × Databricks integration

Use this **only when the Phase 0 integration gate fails** — i.e.
`nimble_integration.tools.{nimble_search, nimble_extract, nimble_agent_run, nimble_agent_list, nimble_agent_describe}`
don't exist. Do not auto-install; walk the user through it (or point them at the cookbook) and stop
until it's done.

Authoritative source: **Nimble cookbook for Databricks** —
<https://github.com/Nimbleway/cookbook/tree/main/databricks>

## What it sets up
Querying live web search data directly from SQL via Nimble APIs/agents, with results landing as governed
Delta tables in Unity Catalog. It creates the `nimble_integration` catalog with a `tools` schema
holding five table functions: `nimble_search`, `nimble_extract`, `nimble_agent_list`,
`nimble_agent_describe`, `nimble_agent_run`.

## Prerequisites (call these out — they matter)
- A **serverless SQL warehouse** with **outbound networking enabled**: turn on the preview
  *"Enable networking for isolated workloads in Serverless SQL Warehouses"* and do a **cold restart**.
  This lets the warehouse make the outbound call to Nimble's API endpoint.
- Permission to create catalogs/schemas and `CREATE FUNCTION`.
- A Nimble API key: <https://online.nimbleway.com/account-settings/api-keys>
- Databricks CLI v0.205+ authenticated (`databricks auth login`).

## Steps (from the cookbook)

```bash
# 1) Store the API key in a secret scope named `nimble`
databricks secrets create-scope nimble
databricks secrets put-secret nimble api_key   # paste token, then Ctrl-D
databricks secrets put-acl nimble users READ

# 2) Identify a serverless warehouse
WH=<your-warehouse-id>            # from: databricks warehouses list

# 3) Deploy catalog + schemas
python3 databricks/helpers/deploy_sql.py --file databricks/01_setup.sql --warehouse "$WH"

# 4) Install the table functions
for f in databricks/tools/*.sql; do
  python3 databricks/helpers/deploy_sql.py --file "$f" --warehouse "$WH"
done
```

(Clone the cookbook repo first so the `databricks/...` paths resolve.)

## Verify
```sql
SELECT count(*) AS n FROM nimble_integration.tools.nimble_search('AI agents news', 5);
SELECT length(content) FROM nimble_integration.tools.nimble_extract('https://www.nimbleway.com');
```
Both should return non-zero. Once verified, return to Phase 0 and continue.

## Optional — register with Genie
The cookbook includes `databricks/helpers/create_genie_space.py` to expose the five functions to a
Genie space. Not required for this skill's dashboard/app demos.

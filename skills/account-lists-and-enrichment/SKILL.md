---
name: account-lists-and-enrichment
description: "Build target account lists and enrich CRM records at scale with Nimble Web Search Agents and the Search API. Use when the user wants an ICP or TAM account list, net-new accounts that match criteria, local businesses in an area, near-misses explained, or wants a whole CSV, spreadsheet or CRM export filled in with firmographics, funding, leadership, decision makers, hiring, tech stack or recent signals, with a source and date per field and rules for writing back to Salesforce or HubSpot. Covers batching, concurrency, verification gates, conflict and precedence rules, and the Search API pipeline when the user wants their own code to own the workflow. Do NOT use for firmographics on a few domains — use account-enrichment instead. Do NOT use for one account's brief or signals — use account-deep-research instead. Do NOT use for a single fact — use account-fast-search instead. Do NOT use for job, review and listing panels tracked over time — use gtm-data-at-scale instead."
metadata:
  author: Nimbleway
  version: 1.10.0
  category: gtm
---

# Account lists and CRM enrichment with Nimble

Two jobs fill most of a pipeline: **find the accounts** that match an ideal customer profile (ICP), and **fill the fields** a rep needs on accounts you already have. Nimble does both two ways:

| | Web Search Agent (Agent API) | Search API pipeline |
| - | - | - |
| Who owns the workflow | Nimble: you give the objective, the rules and the output shape; the agent plans searches, navigates newsrooms, careers boards and registries, cross-checks and returns JSON with per-claim confidence | Your code: you choose each query, its sources and depth, run an LLM step over the results and apply your own rules |
| Best for | Most lists and enrichment: fastest to good results, finds evidence on pages a fixed query list misses | Very large or very cheap runs, strict control of every source, or when results must be reproducible query by query |
| Typical time | Enrichment about 3 to 5 minutes per batch; an ICP list about 7 to 8 minutes per run (both at `high`) | Seconds per search; you pay for your own LLM step |

They find different things. In Nimble's GTM guide, the agent found a company through a Gem-hosted careers board the Search pipeline's fixed ATS list missed, and the Search pipeline found another company's sales roles on Ashby and Lever that the agent did not verify. **For a list that matters, run the agent and a short Search sweep, then merge and verify.**

## 1. Get the agents into the account

These skills use six agents. Check in this order: an agent with the same `agent_name` already in the account (`nimble_agents_list`) → the Nimble gallery (`nimble_agent_templates_list`, then `nimble_agents_create(template=<name>, agent_name=<name>)`) → the bundled spec.

| Agent | Job | Gallery template | Bundled spec |
| - | - | - | - |
| `gtm-icp-discovery` | ICP list where every hard criterion is verified on a cited page, plus near-misses | yes | `account-deep-research/agents/gtm-icp-discovery.json` |
| `account-discovery` | Quick ICP list from a description, each with why it fits and a source | yes | `account-deep-research/agents/account-discovery.json` |
| `business-discovery` | Local businesses by category and place, with address, phone, website, rating, review count | yes | `account-deep-research/agents/business-discovery.json` |
| `gtm-account-enrichment` | CRM-shaped profile from a domain, with conflicts between sources kept | yes | `account-deep-research/agents/gtm-account-enrichment.json` |
| `account-enrichment` | Firmographics on one domain: legal name, HQ, industry, ownership, headcount, funding, leaders, tech stack | yes | `account-deep-research/agents/account-enrichment.json` |
| `decision-maker-identification` | Who holds named roles at an account now | yes | `account-deep-research/agents/decision-maker-identification.json` |

The bundled specs ship in the `account-deep-research` skill of this repo. If only this skill is installed, read them from `https://raw.githubusercontent.com/Nimbleway/agent-skills/main/skills/account-deep-research/agents/<agent_name>.json`. All six are in the **Go-to-market** section of the Nimble gallery, so `nimble_agents_create(template=<name>, agent_name=<name>)` works for each; use the bundled spec only if the gallery does not list one. Create each agent once and reuse it; never one agent per account.

**People at those accounts.** Once the account list is final, `people-research` finds the contacts: `people-discovery` for people who match a role and seniority across the list, `buying-committee-map` for the committee at one target account, and `contact-job-change-monitor` to keep the contact list current.

## 2. Build a list

**Frame the ICP as hard criteria before running anything.** Write down with the user:

1. **Firmographics**: HQ country or region, category in plain words ("builds AI software sold to law firms or in-house legal teams, not a law firm itself"), headcount range, ownership.
2. **Stage and timing**: latest priced round and the date it must be after, or "public", or "PE-backed".
3. **A live signal**: hiring for a function (a quota-carrying sales role in the US), a technology they use, a recent launch, an event they sponsor.
4. **Count and exclusions**: how many, and the domains already in the CRM or already customers (pass them in so they are not returned).

Then run `gtm-icp-discovery` with the criteria as a bulleted list and "Treat every criterion as a hard constraint. List near-misses with the criterion they failed." Use its suggested question as the template. Ask for 15 to 50 rows per run; for a bigger TAM, split by region, sub-category or funding stage and run each scope separately (one run over a whole market truncates). Pass domains already found as `input_data` with "exclude the domains in input_data" so top-up runs find new ones.

**Check the list before you show it:**

- Every row in `companies` has a live `sales_role_url` (or the user's signal), a dated headcount source and `evidence_urls` for each criterion. A row that misses one is a near-miss, not a match.
- **Headcount gate.** Headcount is the field agents infer most. For each row, run one `nimble_search` (`"<company> <domain> employees headcount"`, `search_depth: "lite"`, `max_results: 5`) and drop rows whose only figure is older than a year or outside the range.
- Domains resolve to the named company (open one or two).
- Near-misses are useful: show them with the failed criterion ("HQ is Toronto, not the US"). They are often next quarter's accounts.
- No padding. If fewer companies qualify than asked, the shorter list is the right answer.

**Local and SMB lists** (dentists in Austin, HVAC contractors in three counties): run `business-discovery` per city or county and category, at least 10 rows per run. For thousands of listings or a refresh every month, use the `google_maps_search` Extract Template in `gtm-data-at-scale` instead; it returns stable fields per listing and runs as a batch or a scheduled Job.

## 3. Enrich a list

Send the rows you have in `input_data`, with the fields to fill set to `null`. Your values pass through untouched (`pre_existing` in the trust block); only the blanks are researched.

**Pick the shape.** `gtm-account-enrichment` and `account-enrichment` return one profile per run (an object schema): send one record per run and run several in parallel. To fill a few columns across many rows in one run, create a custom enrichment agent with an **array-root** schema (one output row per input row, input values carried through) as in section 5 of `account-deep-research`.

**Batch size is the lever** for array-root agents. At `high`, about 5 rows with 6 researched fields per run; 10 rows with 2 or 3 fields; 1 to 3 rows at `x-high` for hard fields (financials of private companies, named executives). The hard cap is 20 rows and 200 input cells, but a 10-row, 6-field batch at `high` once ran 21 minutes and researched only half its rows.

```bash
curl -s -X POST https://sdk.nimbleway.com/v2/agents/runs \
  -H "Authorization: Bearer $NIMBLE_API_KEY" -H "Content-Type: application/json" \
  -d '{
    "agent_name": "gtm-account-enrichment",
    "input": "Enrich this CRM account into a current company profile. Resolve it from its domain (eve.legal), not its name.",
    "input_data": {"company_name": "Eve", "domain": "eve.legal", "headquarters": null,
                   "employee_count": null, "last_round": null, "leadership": null, "currently_hiring": null}
  }'
```

Then poll `GET /v2/agents/{agent_id}/runs/{run_id}` while `is_active` and read `GET .../runs/{run_id}/result` (MCP: `nimble_agents_run` → `nimble_agents_run_status`). For more than a few batches, write a small loop rather than calling tools one by one:

- **Concurrency** about 10 runs at a time (account defaults: 30 concurrent agents, 200 runs a day; ask Nimble to raise them for a large backfill).
- **A ledger keyed on the user's identifier** (domain or CRM ID), not on run IDs: which rows came back, which did not. Resubmit missing rows once in a new batch.
- **A stuck threshold**: a run still active after 30 minutes is resubmitted once, not looped.
- **Dedupe after every merge** on the domain.
- Write results to a file (CSV or JSONL), not into the chat. Show the user a sample and the fill rate per field.

For **people**, run `decision-maker-identification` per account with the exact roles ("current CRO, head of RevOps, VP Marketing") after the account list is final. Titles differ by company size; the agent maps "Head of", "VP" and "Director" to the same scope and reports `missing_roles`. Never generate emails or phone numbers from patterns; if the user needs contact data, that comes from their licensed contact provider, matched on name, company and LinkedIn URL.

## 4. Write back to the CRM safely

Most damage happens at write-back, not research. Agree on these rules with the user before touching Salesforce or HubSpot, and keep the raw results file:

- **Never overwrite a value a person entered** unless the user says so. Fill blanks; send conflicts to a review queue.
- **Gate on confidence.** Run with `trust_mode: "full_trust"` (MCP) or read the `trust.claims` block: write `high` confidence fields automatically, queue `medium`, drop `low` and null.
- **Store the source and date with the value** (a `source_url` and `as_of` field, or a note) so reps can see why a field says what it says.
- **Precedence when sources disagree.** For fast-moving fields (headcount, customer count, open roles, titles) the most recent dated value wins. For everything else the most trusted tier wins: the company's own site and ATS boards → press releases and reputable press → everything else → aggregators (Crunchbase, PitchBook, Tracxn). `gtm-account-enrichment` returns `data_conflicts` with every value found; show them rather than silently picking one.
- **Match on domain**, not company name, and normalize to the bare hostname before matching.
- **Dry run first**: write 10 records, have the user check them in the CRM, then the rest.

Enrichment goes stale. Re-run headcount, leadership and hiring every quarter, and buying signals weekly (`gtm-buying-trigger-monitor` in `account-deep-research`).

## 5. The Search API pipeline (when your code owns the workflow)

Use this when the user wants full control, a very large list, or no agent runs. The pattern from Nimble's GTM guide:

**Enrichment, one account:** one focused search pass per attribute group, each with its own sources and depth, then an LLM step that fills a fixed profile and keeps every conflicting value with its source and date, then code-side precedence rules.

| Pass | Parameters |
| - | - |
| Identity and products | `include_domains: [<domain>]`, `search_depth: "standard"`, `max_results: 5` |
| Funding and investors | `search_depth: "standard"`, `max_results: 6` |
| Leadership, HQ, headcount | `search_depth: "standard"`, `max_results: 5` |
| Hiring | `include_domains: ["job-boards.greenhouse.io","jobs.ashbyhq.com","jobs.lever.co", <domain>]`, `search_depth: "lite"`, `max_results: 20` |
| Recent news | `time_range: "year"`, `search_depth: "lite"`, `max_results: 8` |

**List building:** broaden, then narrow. Five or six `lite` discovery queries from different angles (funding stage, buyer type, trade press via `include_domains`, investor portfolios) with `start_date` set to the funding window and `max_results: 10`; dedupe candidates; one `lite` firmographic search per candidate (5 results); a hiring search on ATS boards plus the company's own domain only for candidates that pass; an LLM judges each criterion from the evidence, and code makes the pass/fail decision and records the failed criterion.

**Buying triggers for a watchlist:** three `focus: "news"`, `search_depth: "lite"`, `max_results: 8` queries per account (funding and acquisitions; executive hires; launches, expansions and partnerships) with `start_date` at the window start; an LLM step dates each event by when it happened, types and grades it; code keeps events inside the window, merges duplicate coverage and picks the strongest trigger per account.

Full runnable versions of all three (Search pipeline and agent, with post-processing that guarantees the output shape) are in `Nimbleway/cookbook` under `apps/gtm-account-enrichment-agent`, `apps/gtm-account-discovery-agent` and `apps/gtm-buying-trigger-agent`.

## 6. Rules that apply to every list

- **Public information only.** No logged-in, paywalled or purchased data. No emails or phone numbers constructed from patterns; personal data limited to name, title, company and a public profile URL unless the task needs more.
- **Respect the user's suppression lists**: existing customers, open opportunities, do-not-contact flags and regional privacy rules (GDPR, CASL) decide who goes into an outbound sequence, not the web data.
- **Every value has a source and a date**; a value nobody published is null.
- **No padding**: fewer verified rows beat a list filled to the requested count.
- **Lists are a snapshot.** Say the date the list was built, and re-verify hiring and headcount before a campaign that starts weeks later.

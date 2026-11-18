---
name: company-deep-research
description: "Deep, cited research on a company for hedge fund and investment teams, run by Nimble Web Search Agents. Use when a question needs many sources or a structured, sourced output, such as a fundamental deep dive, catalyst calendar, filing-change diff, forensic red-flag screen, management track record, channel check, customer and supplier map, competitor momentum, government contracts, a borrower credit file, a credit early-warning log, merger deal terms or deal approval tracking. Also covers custom Web Search Agents for requests that fit none of those. Do NOT use for a general company overview — use company-deep-dive instead. Do NOT use for a private-company DD memo — use due-diligence instead. Do NOT use for a quick credit view or counterparty check — use credit-risk instead. Do NOT use for material events at holdings since a date — use portfolio-monitoring instead. Do NOT use for a single fact — use company-fast-search instead. Do NOT use for filings and decks — use filings-media-pdfs instead."
metadata:
  author: Nimbleway
  version: 1.10.0
  category: finance-research
---

# Company deep research with Nimble Web Search Agents

A Web Search Agent takes one research question, plans its own searches, reads dozens of pages in parallel and returns a cited answer, either free text or JSON that matches a schema. This skill runs the 13 hedge fund research agents Nimble published in its agent gallery, and builds a custom agent when a request falls outside them.

## 1. Route before you spend a run

| The request | Use |
| - | - |
| One closed fact ("Who is CRWV's CFO?", "When is NVDA's next earnings date?") | `company-fast-search` (Search with an answer) |
| One known URL or filing | `company-fast-search` (Extract) or `filings-media-pdfs` |
| A named question that needs several sources, a table or verification | **This skill: one agent run** |
| Thousands of product, review or job rows | `alt-data-at-scale` |

Use one run per company and question. Do not research first and then start a run, and do not split one question across several runs. Put every sub-question in the run's `input`.

## 2. Pick the agent

| Agent (`agent_name`) | Use it when the user asks... | Use case |
| - | - | - |
| `hf-fundamental-deep-dive` | for a full underwriting brief tied to a strategy: business, financials, moat, alpha signals, management, risks, catalysts, variant view | research |
| `hf-catalyst-calendar` | what dated events could move the stock (earnings, FDA, trials, lockups, maturities, votes, index changes) | research |
| `hf-filing-changes` | what changed in the latest 10-K or 10-Q against the prior one (new risks, dropped language, moved numbers) | research |
| `hf-forensic-red-flags` | about accounting or governance risk: auditor changes, restatements, related parties, SEC letters, short reports | research |
| `hf-management-track-record` | whether management delivers on guidance and commitments, plus leadership changes and insider trades | research |
| `hf-channel-check` | a specific "what does the web show today versus a past date" question: prices, promotions, stores, hiring, public databases, each measured against an archived baseline | research |
| `hf-customer-supplier-map` | who the company sells to and buys from, with evidence | dataset_building |
| `hf-competitor-momentum` | which rivals (public or private) are gaining ground, as dated signals | dataset_building |
| `hf-government-contracts` | for federal awards, task orders and bid protests, with obligated amounts against ceilings | dataset_building |
| `hf-deal-terms` | for the terms of a merger agreement: consideration, outside date, break fees, regulatory covenants, conditions | research |
| `hf-deal-tracker` | where a pending merger stands with each regulator and court: approvals, lawsuits, votes, rival bids, next dates, and the outside date from the merger agreement | research |
| `hf-credit-profile` | for a credit file on a public or private borrower: capital structure, ratings, lender marks, financials, key terms | research |
| `hf-credit-early-warning` | for stress signals around a borrower since a date: lender actions, debt quotes, lawsuits, liens, WARN notices, adviser hires, each marked active, cured or historical, plus capital structure and liquidity | research |

Each agent's full spec (its skill, output schema, effort and example questions) is in `agents/<agent_name>.json` next to this file. Read the matching file before the first run; its `suggested_questions` show the input format the agent expects.

The three monitors (`hf-deal-tracker`, `hf-credit-early-warning`, `hf-channel-check`) were tightened after live tests and open with a `bottom_line` object: `summary`, `key_risk`, `next_catalyst` and `next_catalyst_date` (plus `stress_level` for credit, from active signals only). If an account copy of one of these agents was created before 2026-11-11, update it from the gallery template or the bundled spec (`nimble_agents_update` or `PATCH /v2/agents/{agent_id}`) so it gets the new skill and schema.

If two agents fit, run the one closest to the user's words. "Is this a short?" is `hf-forensic-red-flags`; "build me the bull and bear case" is `hf-fundamental-deep-dive`. Credit desks start with `hf-credit-profile`, then monitor with `hf-credit-early-warning`. Merger arb starts with `hf-deal-terms`, then monitors with `hf-deal-tracker`.

If none fits, go to section 5 and build a custom agent.

## 3. Get the agent into the account (reuse first)

Check in this order and stop at the first hit:

1. **Already in the account.** `nimble_agents_list` (MCP) or `GET /v2/agents`. Look for an agent named `hf-<name>` or `gallery-hf-<name>`. If found, run it by `agent_id`.
2. **In the gallery.** `nimble_agent_templates_list` (or `GET /v2/agents/templates`). If a template with the same `template_name` exists, create from it: `nimble_agents_create(template="hf-catalyst-calendar", agent_name="hf-catalyst-calendar")`. The gallery copy is maintained by Nimble, so prefer it over the bundled file.
3. **From the bundled spec.** Create the agent from `agents/<agent_name>.json`. Pass its `agent_name`, `display_name`, `description`, `use_case`, `effort`, `skill`, `output_schema` and `suggested_questions` unchanged.

MCP:

```
nimble_agents_create(
  agent_name="hf-catalyst-calendar",
  display_name="Catalyst calendar",
  description=<description>, use_case="research", effort="high",
  skill=<skill>, output_schema=<output_schema>, suggested_questions=<suggested_questions>)
```

REST (any language, `NIMBLE_API_KEY` from the environment, never printed):

```bash
jq '{agent_name, display_name, description, use_case, effort, skill, output_schema, suggested_questions}' \
  agents/hf-catalyst-calendar.json |
curl -s -X POST https://sdk.nimbleway.com/v2/agents \
  -H "Authorization: Bearer $NIMBLE_API_KEY" -H "Content-Type: application/json" -d @-
```

Create each agent once and reuse it. A new agent per question loses the agent's learned context and clutters the account.

## 4. Run it and read the result

Write `input` in the shape of the agent's suggested questions: the company's **legal name, ticker and domain** (two identifiers stop namesake drift), the window or "since" date, and the strategy or question. Keep it short. The agent's skill already holds the method.

```
nimble_agents_run(agent_id=<id>,
  input="Build a catalyst calendar for Rocket Lab (RKLB, rocketlabusa.com) for the next 12 months.")
→ nimble_agents_run_status(run_id=<run_id>, agent_id=<agent_id>) # waits ~45 s per call; call again until it completes
```

REST: `POST /v2/agents/{agent_id}/runs` with `{"input": ...}`, poll `GET /v2/agents/{agent_id}/runs/{run_id}` while `is_active`, then `GET .../runs/{run_id}/result`. Set `trust_mode: "full_trust"` (MCP) when the user wants per-claim confidence and citations.

Timing: `high` runs take about 5 to 15 minutes and can run to 30. Tell the user the run started and roughly how long it takes. Do not start a second run of the same question while one is active.

**Check before you present.** `completed` means finished, not correct:

- Rows or sections returned against what was asked. A thin `checked_no_finding` list on a hard question means the agent stopped early; say so.
- Entity drift: every source is about the right company (ticker, CIK, domain), not a parent, subsidiary or namesake.
- Open two or three citations. Each `source_url` must be the page that states the value, not a search page.
- Dates are event dates, not today's date. A window ("third or fourth quarter of 2027") stays a window: `date` is null and the window is in `date_text` with `date_precision`. Never turn a window into a day.
- Status is current. In `hf-credit-early-warning`, read each signal's `status`: a `cured` signal (see `cured_by`) or a `historical` one is not live stress. A cured exchange-listing deficiency shown as active is the classic error.
- Required fields can come back null. The platform does not enforce the schema at run time, so check the required fields and say which are empty rather than filling them.
- No internal references in text. Strings such as `quote:/pages/...`, `.md#L12` or file paths inside a field are leaks; remove them and cite the `source_url` instead.
- A value whose only source is a paywalled page is unverified; say so.
- Prices name the instrument, the date and the quote type (`price_note`). A fair value disclosed in a filing is not a market quote.
- `checked_no_finding` names the exact registers, dockets or pages searched and the period. A news search that never reached the register is not evidence that nothing exists.
- For `hf-channel-check`, `evidence_direction: insufficient` means too few like-for-like baselines. Report it as insufficient, not as "no", and say how many observations had a baseline.

Present the answer with its citations inline. Lead with the `bottom_line` when the agent returns one, otherwise with what matters for the position (the variant view, the nearest catalyst, the highest-severity flag), and keep analyst opinions labeled as opinions.

**Follow-ups.** For a narrower follow-up on the same subject, run the same agent again with `previous_interaction_id` set to the earlier run's `interaction_id` (REST), or put the earlier answer's key facts into the new `input`. Rerunning monitors such as `hf-credit-early-warning` or `hf-deal-tracker` with a later "since" date produces the change log.

## 5. When nothing fits: build a custom research agent

Create one agent per repeatable question type, not per company. Name it `hf-custom-<topic>` so it is found and reused next time.

1. **Classify `use_case`.** `research` for a brief or a nested answer on one subject; `dataset_building` for a list of entities that meet criteria (all suppliers, all lawsuits, every store opening); `enrichment` for adding fields to rows the user already has (a watchlist or CSV, at most 20 rows and 200 cells per run, practical batch about 5 rows for 6 researched fields).
2. **Write the `skill`** as a playbook, in the style of the bundled specs: where the evidence lives (name the regulators, registries and filing types), what each term means, the pitfalls, and the evidence rules below. Copy the "Citations and evidence" and "What was not found" blocks verbatim from `hf-deal-tracker`, `hf-credit-early-warning` or `hf-channel-check` (the latest versions, which also ban internal references in text and paywalled-only sources); they hold the MNPI and citation rules every investment agent needs.
3. **Write `goals`** (REST only) as 3 to 6 checkable requirements, for example "Every row cites the primary record (filing, docket, regulator page) when one exists".
4. **Design the `output_schema`.** Flat, 5 to 8 described fields per object, `["string","null"]` for anything uncertain, `YYYY-MM-DD` dates, numbers as numbers with the unit in the description, enums for judgments, a `source_url` per value, and a `checked_no_finding` array so absence is reported, not hidden. For a research object, put a `bottom_line` object first (summary, key risk, next catalyst). Dates that may be windows get `date` (null unless exact) plus `date_text` and `date_precision`. Monitoring signals get `status` (active, cured, historical), `cured_by` and `severity_reason`. Keep roles apart in separate fields (a lender is not an owner). Array root for lists. No `format`, `pattern`, `min*`, `max*` or free-form maps.
5. **Set `sources`** when you know them: `allow` tiers (for example SEC EDGAR, the company's IR domain, the relevant regulator), `block` mirrors and scraped-filing sites, and `prioritize` such as "primary records beat press; press beats aggregators".
6. **Effort.** `high` for anything with a schema and for all dataset building (required). `medium` only for a free-text brief. `x-high` for an exhaustive single-site catalog or hard fields one row per run. Never `low` when citations matter.
7. **Test on one company you already know the answer for**, check it against section 4, then fix the skill or schema (not the effort) before running the rest.

One-shot create-and-run (MCP): `nimble_agents_run(agent_name="hf-custom-<topic>", use_case=..., effort="high", skill=..., output_schema=..., input=...)`. An unseen name creates the agent; a known name reuses it.

Example: "Map every data center campus Vertiv's top customers announced in 2026" is `dataset_building`, with a skill that names utility interconnection queues, county permit portals and hyperscaler press rooms, and a schema of `campus, owner, location, mw_capacity, announced_date, vertiv_mentioned, source_url`.

## 6. Rules that apply to every run

- **Public information only.** No paywalled, logged-in, leaked or expert-network content. If only a paywalled headline is public, it can be quoted as "Headline only:".
- **Facts, not forecasts.** A value nobody published is null. Analyst estimates, ratings and targets are reported as views with their source, never as evidence.
- **Primary sources win.** Filings, regulators, courts, government databases and the company's own statements beat press, and press beats aggregators.
- **Point in time.** Every value carries the date it was published or happened, so the user can tell what the market knew and when. A window is not a date, and a cured problem is not a live one.
- **No paywalled-only values.** A paywalled page is never the only source for a value.
- Web Search Agents read public pages. For LinkedIn, Glassdoor or social feeds, use `alt-data-at-scale` (Extract Templates) or `--focus social` search.

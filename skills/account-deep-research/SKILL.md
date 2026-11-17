---
name: account-deep-research
description: "Deep, cited research on an account, a watchlist or a market for sales, SDR/BDR, RevOps and marketing teams, run by Nimble Web Search Agents. Use when a GTM question needs several agents, many sources or a custom structured output, such as buying triggers across a watchlist, a competitive landscape with pricing, brand sentiment, executive or influencer social posts, or a plan that combines brief, signals and contacts. Also use when the request fits no single-template skill: the skill shows how to create and run a custom Web Search Agent. Do NOT use for a pre-meeting brief on one company — use account-brief instead. Do NOT use for who holds a role at one company — use decision-maker-identification instead. Do NOT use for account lists of tens to thousands of rows (ICP, TAM, local businesses) or for enriching domains or a CSV — use account-lists-and-enrichment instead. Do NOT use for a single fact — use account-fast-search instead. Do NOT use for people research — use people-research instead."
metadata:
  author: Nimbleway
  version: 1.10.0
  category: gtm
---

# Account deep research with Nimble Web Search Agents

A Web Search Agent takes one research question, plans its own searches, reads dozens of pages in parallel (company sites, newsrooms, careers pages, ATS boards, the press) and returns a cited answer, either free text or JSON that matches a schema. This skill runs the 12 GTM agents Nimble publishes (nine in its agent gallery, three from its GTM developer guide) and builds a custom agent when a request falls outside them.

## 1. Route before you spend a run

| The request | Use |
| - | - |
| One closed fact ("Who is Gong's CFO?", "Did Clay raise this year?") | `account-fast-search` (Search with an answer) |
| One known URL (a pricing page, a job post, a press release) | `account-fast-search` (Extract) |
| A named account or question that needs several sources, a table or verification | **This skill: one agent run** |
| Tens to thousands of rows to enrich or a list to build and push to a CRM | `account-lists-and-enrichment` |
| Job postings, reviews or listings tracked over time | `gtm-data-at-scale` |

Use one run per account and question. Do not research first and then start a run, and do not split one question across several runs. Put every sub-question in the run's `input`. For a watchlist, put all accounts in one `gtm-buying-trigger-monitor` run rather than one run per account.

## 2. Pick the agent

| Agent (`agent_name`) | Use it when the user asks... | Use case | Source |
| - | - | - | - |
| `account-brief` | to prepare for a meeting or call: what the company does, its priorities and challenges, recent changes, key people, talking points | research | gallery |
| `account-signals` | what changed at one account since a date: funding, hires and departures, launches, layoffs, pricing changes, hiring pushes | research | gallery |
| `gtm-buying-trigger-monitor` | for buying triggers across a watchlist in a window, graded High/Medium/Low for a stated seller, with an outreach angle per account and the rejected events listed | research | gallery (GTM guide) |
| `decision-maker-identification` | who currently holds named roles at an account (CRO, head of RevOps, CTO...), with title, start date, past roles and public profiles | enrichment | gallery |
| `competitive-intelligence` | for a side-by-side of named competitors: published pricing and plans, target customers, differentiators, recent announcements | research | gallery |
| `brand-intelligence` | how a brand or product is being talked about (Reddit, X, LinkedIn, review sites): a sentiment score, themes, incidents | research | gallery |
| `social-media-monitor` | what named people or handles posted in a window, with engagement, and what went viral | dataset_building | gallery |
| `account-enrichment` | for firmographics on one domain: legal name, HQ, industry, ownership, headcount, funding, leaders, tech stack used | enrichment | gallery |
| `gtm-account-enrichment` | to fill a CRM record from a domain: products, target customer, HQ, headcount, funding and investors, leadership, customer count, hiring, recent signals, with conflicts between sources kept | enrichment | gallery (GTM guide) |
| `account-discovery` | for companies matching an ICP description, each with why it fits and a source | dataset_building | gallery |
| `gtm-icp-discovery` | for an ICP list where every hard criterion (HQ, category, size, stage, a live sales posting) is verified on a cited page, plus near-misses with the criterion they failed | dataset_building | gallery (GTM guide) |
| `business-discovery` | for local businesses by category and place (clinics, salons, contractors, restaurants) with address, phone, website, rating and review count | dataset_building | gallery |

Each agent's full spec (its skill, output schema, effort and example questions) is in `agents/<agent_name>.json` next to this file. Read the matching file before the first run; its `suggested_questions` show the input format the agent expects. The specs are snapshots of the gallery templates (2026-11-12). All 12 are in the **Go-to-market** section of the Nimble Web Search Agent gallery, each with a pre-run example answer. The three GTM-guide agents started in Nimble's cookbook (`Nimbleway/cookbook`, `apps/gtm-*-agent`) and were tightened for the gallery: their rules live in the skill and every schema object has non-null required fields.

If two agents fit, run the one closest to the user's words and the shape they need:

- **One account, a quick answer** → the gallery agent (`account-signals`, `account-enrichment`, `account-discovery`), at `medium` effort where its spec says so.
- **A watchlist, CRM-ready fields or a verified list** → the GTM-guide agent (`gtm-buying-trigger-monitor`, `gtm-account-enrichment`, `gtm-icp-discovery`) at `high`.
- "Who should I call?" is `decision-maker-identification`; "prep me for Thursday" is `account-brief`; "is anything happening at X?" is `account-signals`.
- Anything about a specific person (a brief on an attendee, a buying committee, whether a contact changed jobs) goes to `people-research`, which has fast Search patterns and people-focused agents.

For more than a handful of accounts to enrich or a list headed for a CRM, hand off to `account-lists-and-enrichment`, which batches these same agents and applies write-back rules. If none fits, go to section 5 and build a custom agent.

## 3. Get the agent into the account (reuse first)

Check in this order and stop at the first hit:

1. **Already in the account.** `nimble_agents_list` (MCP) or `GET /v2/agents`. Look for an agent with the same `agent_name` (or `gallery-<name>`, `gtm-<name>`). If found, run it by `agent_id`.
2. **In the gallery.** `nimble_agent_templates_list` (or `GET /v2/agents/templates`). If a template with the same `template_name` exists, create from it: `nimble_agents_create(template="account-brief", agent_name="account-brief")`. The gallery copy is maintained by Nimble, so prefer it over the bundled file. If the gallery does not list a template (an older deployment, or a custom agent), go to step 3.
3. **From the bundled spec.** Create the agent from `agents/<agent_name>.json`. Pass its `agent_name`, `display_name`, `description`, `use_case`, `effort`, `skill`, `output_schema` and `suggested_questions` unchanged (omit `output_schema` when it is null: that agent returns free text).

MCP:

```
nimble_agents_create(
  agent_name="gtm-buying-trigger-monitor",
  display_name="GTM Buying Trigger Monitor",
  description=<description>, use_case="research", effort="high",
  skill=<skill>, output_schema=<output_schema>, suggested_questions=<suggested_questions>)
```

REST (any language, `NIMBLE_API_KEY` from the environment, never printed):

```bash
jq '{agent_name, display_name, description, use_case, effort, skill, output_schema, suggested_questions}
    | with_entries(select(.value != null))' \
  agents/gtm-buying-trigger-monitor.json |
curl -s -X POST https://sdk.nimbleway.com/v2/agents \
  -H "Authorization: Bearer $NIMBLE_API_KEY" -H "Content-Type: application/json" -d @-
```

Create each agent once and reuse it. A new agent per account loses the agent's learned context (which sources and retrieval patterns worked) and clutters the account.

## 4. Run it and read the result

Write `input` in the shape of the agent's suggested questions: the company's **name and domain** (the domain stops namesake drift: there are many companies called Eve, Mercury or Clay), the window or "since" date, the roles or criteria, and the seller's context when grading matters ("the seller offers revenue software to B2B SaaS companies"). Keep it short. The agent's skill already holds the method.

```
nimble_agents_run(agent_id=<id>,
  input="Prepare me for a meeting with Gong (gong.io). I sell data infrastructure to revenue teams; the meeting is with their VP of RevOps.")
→ nimble_agents_run_status(run_id=<run_id>, agent_id=<agent_id>) # waits ~45 s per call; call again until it completes
```

REST: `POST /v2/agents/{agent_id}/runs` with `{"input": ...}` (enrichment agents also take `input_data`: the CRM record with the fields to fill set to null), poll `GET /v2/agents/{agent_id}/runs/{run_id}` while `is_active`, then `GET .../runs/{run_id}/result`. Set `trust_mode: "full_trust"` (MCP) when the user wants per-claim confidence and citations, for example before writing to a CRM.

Timing: `medium` runs take about 1 to 3 minutes, `high` about 3 to 8 (a five-account trigger watch took about 4.5 minutes, an ICP list about 7.5), `x-high` can run to 15 or more. Tell the user the run started and roughly how long it takes. Do not start a second run of the same question while one is active.

**Check before you present.** `completed` means finished, not correct:

- Rows or sections returned against what was asked. An empty `events` list or `trigger_count: 0` is a valid answer when nothing happened; a thin list on a busy company (a recent funding round you can find in one search is missing) means the agent stopped early; say so.
- Entity drift: every source is about the right company (domain, HQ city, product), not a namesake, a parent or a former employer's page.
- Open two or three citations. Each `source_url` must be the page that states the value, not a search page or a homepage.
- Event dates, not article dates. "Since 2026-09-21" means the event happened after it; a feature re-covered this month about a 2025 round is excluded. Check the `excluded_events` list where the agent returns one.
- People are current. A title counts only when a dated source in the last year or a current profile shows it; old bio pages and conference speaker pages go stale. Never present an email or phone number that a page did not publish.
- Numbers carry their date and source type: "about 376 employees (LinkedIn, 2026-10)" and "1-10 (Crunchbase)" are a conflict to show, not average.
- Required fields can come back null. The platform does not enforce the schema at run time, so check the required fields and say which are empty rather than filling them.
- No internal references in text. Strings such as `quote:/pages/...`, `.md#L12` or file paths inside a field are leaks; remove them and cite the `source_url` instead.
- Lists are not padded: for `gtm-icp-discovery`, every row in `companies` should have a live `sales_role_url` and evidence for each criterion; a row that misses one belongs in `near_misses`.
- Pricing: a vendor's own pricing page is the only source for its prices; "Not publicly listed" is a correct answer.
- Social: logged-in or blocked platforms (X, LinkedIn feeds) may come back thin. Report a platform the agent could not reach as a coverage gap, not as "no posts".

Present the answer with its citations inline. Lead with what the seller acts on: the strongest trigger and its outreach angle, the two or three talking points for the meeting, the person to contact. Label anything that is a company's own claim (a customer count on its homepage) as the company's claim.

**Follow-ups.** For a narrower follow-up on the same account, run the same agent again with `previous_interaction_id` set to the earlier run's `interaction_id` (REST), or put the earlier answer's key facts into the new `input`. Rerunning `account-signals` or `gtm-buying-trigger-monitor` with a later "since" date produces the change log; schedule it weekly for a watchlist.

## 5. When nothing fits: build a custom research agent

Create one agent per repeatable question type, not per account. Name it `gtm-custom-<topic>` so it is found and reused next time.

1. **Classify `use_case`.** `research` for a brief or a nested answer on one subject (an account, a deal, a market); `dataset_building` for a list of entities that meet criteria (every company exhibiting at a conference, every customer a competitor names, every clinic in a county); `enrichment` for adding fields to rows the user already has (a watchlist or CSV, at most 20 rows and 200 cells per run, practical batch about 5 rows for 6 researched fields).
2. **Write the `skill`** as a playbook, in the style of the bundled specs: where the evidence lives (the company's newsroom, careers page, ATS boards, case studies, integration directories, trade press, registries), what each term means for this seller, the pitfalls, and the evidence rules. Copy the "Citations and evidence" block verbatim from `account-brief` or `gtm-buying-trigger-monitor`; it holds the citation, dating and entity rules every GTM agent needs.
3. **Write `goals`** (REST only; some clients drop them, so also state them in the skill) as 3 to 8 checkable requirements, for example "Return accounts with no qualifying event with trigger_count 0 instead of padding with weak events".
4. **Design the `output_schema`.** Flat, 5 to 8 described fields per object, `["string","null"]` for anything uncertain, `YYYY-MM-DD` dates, numbers as numbers with the unit in the description, enums for judgments (trigger type, strength, fit), a `source_url` per value, and a `missing_fields` or `excluded_events` array so absence and rejections are reported, not hidden. Put the field a rep acts on first (`strongest_trigger`, `outreach_angle`, `why_it_fits`). Array root for lists. No `format`, `pattern`, `min*`, `max*` or free-form maps.
5. **Set `sources`** when you know them: `prioritize` (company newsrooms, ATS boards, trade press for the vertical) and `avoid` (SEO listicles, "top 10" vendor posts, aggregators that re-date old news, job boards as evidence of an event).
6. **Effort.** `high` for anything with a schema and for all dataset building (required). `medium` for a single-account brief or signals check. `x-high` for a multi-vendor comparison or an exhaustive single-site catalog. Never `low` when citations matter.
7. **Test on one account you already know the answer for**, check it against section 4, then fix the skill or schema (not the effort) before running the rest.

One-shot create-and-run (MCP): `nimble_agents_run(agent_name="gtm-custom-<topic>", use_case=..., effort="high", skill=..., output_schema=..., input=...)`. An unseen name creates the agent; a known name reuses it.

Example: "Which of Gong's customers named on its site are hiring RevOps leaders?" is `dataset_building`, with a skill that names Gong's customer stories and logo wall, the customers' own careers pages and ATS boards, and a schema of `company, domain, customer_evidence_url, role_title, role_url, posted_date, location`.

## 6. Rules that apply to every run

- **Public information only.** No logged-in, paywalled or purchased data. Never construct an email address or phone number from a pattern; only publish contact details a page states, and only when the task needs them.
- **Facts, not guesses.** A value nobody published is null. Pains, priorities and intent are reported only when a source shows them, with the source.
- **First-party sources win** for what a company says about itself (product, pricing, leadership, open roles): its own site, newsroom, careers page and filings. Reputable press beats aggregators; aggregators are for discovery and corroboration.
- **Point in time.** Every value carries the date it was published or happened. A headcount, a title or a price without a date is a lead, not a fact.
- **No padding.** Fewer, verified rows beat a list filled to the requested count.
- Web Search Agents read public pages. For LinkedIn, Glassdoor or social feeds, use `gtm-data-at-scale` (Extract Templates) or `--focus social` search.

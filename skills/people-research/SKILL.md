---
name: people-research
description: "Research people for sales and GTM with Nimble: fast, cited answers with the Search API and deeper research with people-focused Web Search Agents. Use when the user wants a list of people who match an ICP (roles, seniority and company criteria), wants to know what someone said or posted recently, wants to check whether contacts or champions changed jobs, needs decision makers found across a list of accounts, wants the buying committee at an account mapped, or wants a person researched before outreach. Covers person disambiguation, verifying that a title is current, query patterns, privacy rules and answer format. Do NOT use for one current title lookup at one company — use decision-maker-identification instead. Do NOT use for researching meeting attendees — use meeting-prep instead. Do NOT use for company-level research — use account-deep-research or account-fast-search instead. Do NOT use for bulk job-posting, review or social panels — use gtm-data-at-scale instead."
metadata:
  author: Nimbleway
  version: 1.10.0
  category: gtm
---

# People research with Nimble

People questions come in two speeds. Start fast, and go deep only when the question needs it.

| Speed | Nimble API | Use it for | Time |
| - | - | - | - |
| **Fast** | **Search** (`nimble_search`, `POST /v2/search`), plus **Extract** for one page | One person or one role: who holds it, since when, where they came from, one recent quote or talk | Seconds |
| **Deep** | **Web Search Agents** (`nimble_agents_*`) | A list of people who match an ICP, a full brief on a person, a buying committee at an account, job-change checks on a contact list, decision makers across accounts | About 1.5 to 10 minutes (a person brief took about 2 minutes, a one-contact job-change check about 1.5) |

Rule of thumb: if three searches answer it, stay fast. If the user wants a brief, a map, a table or many people, run one agent.

## 1. Pin the person first

Write down **full name + company + company domain** (and title or city if known) before searching, and use at least two of them in every query. People research fails on identity more than on search:

- Common names: there are many people called Shane Evans; there is one Shane Evans at Gong.
- Company names that are common words (Gong, Ramp, Clay, Mercury): add the domain or a product word, or the search returns everything else.
- Former employees: bios, speaker pages and profiles from previous jobs stay indexed for years.
- Same title in several units or regions at large companies: say which one the person covers.

## 2. The fast path: Search API

**The loop:**

1. **Find the candidate.** One search for the role or the name, scoped to the company.
2. **Verify the title is current.** A press release announcing an appointment is dated history. Run a second, date-scoped search on the person's name (`time_range: "year"`) and open the newest first-party page. This step is not optional.
3. **Read the page** with Extract when the snippet is not enough (the leadership page, the release, the speaker page).
4. **Answer with the source and its date**, and say what you checked for a later change.

**Worked example (why step 2 matters).** "Who is Gong's CRO?" with `include_answer: true` returns Shane Evans, citing Gong's October 2023 appointment release. A date-scoped search for `"Shane Evans" Gong` in the last year returns Gong's own blog and February 2026 coverage: he is now Gong's **Chief Revenue Architect**. The first answer was true in 2023 and wrong today. (`contact-job-change-monitor` catches the same change: `new_title_same_company`, change date 2026-02-19.)

**Query patterns:**

| Need | Search |
| - | - |
| Who holds a role | `"<Company>" "<Title>"` with `include_answer: true`, then verify (step 2). Or Extract the company's leadership page |
| A cited one-line answer | `include_answer: true` with `time_range: "year"`; check the answer cites a first-party or dated page |
| Find their public profile | `site:linkedin.com/in "<Company>" "<Title>"`, `search_depth: "lite"`, `max_results: 10`: result titles read "Name - Title at Company". A profile seen in search results is a lead; confirm the current role elsewhere when it matters |
| Recent appointment or move | `"<Name>" "<Company>" joins OR appointed OR named`, `time_range: "year"` |
| What they said recently | `"<Name>" "<Company>" podcast OR interview OR webinar OR keynote`, `time_range: "year"`; `include_domains: [<company domain>]` for blog posts they wrote |
| Quotes in press | `"<Name>" "<Company>" said`, or `focus: "news"` with `search_depth: "lite"` and the domain in the query |
| Career history | `"<Name>" "previously" OR "prior to joining"` with the company; appointment releases list past roles |
| Who leads a team that is hiring | Job posts on the company's ATS board often name the team; Extract the board (see `account-fast-search`) |

**Parameter notes (tested):**

- `focus` modes (`news`, `social`, `location` and the rest) only work with `search_depth: "lite"`. For people, plain queries with quotes and the domain usually beat `focus: "social"`, which matches the name loosely (a search for Gong's CRO in `social` returned people whose surname is Gong).
- `time_range` (`day`, `week`, `month`, `year`) or `start_date` / `end_date`: always date-scope "current" and "recent" questions. They cannot be combined.
- `max_results` 5 to 10 is enough; run independent searches in parallel rather than one long query.
- The `ti_linkedin_serp_profiles` Extract Template parses a Google results page limited to `linkedin.com/in` profiles (pass the Google search URL as `url`) into `name`, `title`, `snippet`, `linkedin_url`, which is handy for many roles at once.

**Escalate to an agent** when you have run three searches and are still reconciling pages, when the user wants more than a few facts, or when it is more than two or three people.

## 3. The deep path: people research agents

| Agent (`agent_name`) | Use it when the user asks... | Use case | Source |
| - | - | - | - |
| `people-discovery` | for people who match an ICP for people (roles and seniority, plus company criteria such as industry, size, location or funding), each with why they fit and a page showing the current title | dataset_building | gallery |
| `person-brief` | to research one named person before a meeting or outreach: current role verified with its date, career history, recent public activity, stated priorities, talking points | research | gallery |
| `decision-maker-identification` | who holds named roles at one company now, with title, start date, past roles and public profiles | enrichment | gallery |
| `buying-committee-map` | who at an account would buy, champion, evaluate or block a purchase in a product category, each with why they matter | research | gallery |
| `contact-job-change-monitor` | whether contacts on a list are still in the same role, changed title, or moved employer, with the date (champion tracking, CRM hygiene) | enrichment | gallery |
| `social-media-monitor` | what named people posted in a window, with engagement | dataset_building | gallery |

All six are templates in the **Go-to-market** section of the Nimble Web Search Agent gallery, each with a pre-run example answer. Each spec (skill, output schema, effort, example questions) is also in `agents/<agent_name>.json` next to this file, a snapshot of the gallery template (2026-11-12). `decision-maker-identification` and `social-media-monitor` are shared with account research, so their specs live in `account-deep-research/agents/`. If only this skill is installed, read them from `https://raw.githubusercontent.com/Nimbleway/agent-skills/main/skills/account-deep-research/agents/<agent_name>.json`. Read the matching file before the first run; its `suggested_questions` show the input format.

**Get the agent into the account (reuse first):** an agent with the same `agent_name` already in the account (`nimble_agents_list`) → the Nimble gallery (`nimble_agent_templates_list`, then `nimble_agents_create(template=<name>, agent_name=<name>)`) → the bundled spec, if the gallery does not list it (an older deployment) (pass its `agent_name`, `display_name`, `description`, `use_case`, `effort`, `skill`, `output_schema` and `suggested_questions` unchanged). Create each agent once and reuse it.

**Run it:**

```
nimble_agents_run(agent_id=<id>,
  input="Brief me on Shane Evans at Gong (gong.io) before a call next week. I sell data infrastructure to revenue teams.")
→ nimble_agents_run_status(run_id=<run_id>, agent_id=<agent_id>) # waits ~45 s per call; call again until it completes
```

Put the name, company **and domain**, the roles, and the seller's context ("I sell X to Y") in the input. For `contact-job-change-monitor`, pass the contacts as `input_data` rows (`full_name`, `company`, `domain`, `last_known_title`, optional `profile_url`), about 5 rows per run at `high`. REST: `POST /v2/agents/{agent_id}/runs` with `{"input": ..., "input_data": ...}`, poll `GET /v2/agents/{agent_id}/runs/{run_id}` while `is_active`, then `GET .../runs/{run_id}/result`.

**Check before you present.** `completed` means finished, not correct:

- **Same person:** every source names the right company (and title or city). Drop pages about namesakes.
- **Current, with a date:** each title has an `as_of` within the last 12 months or a page showing it as current. An appointment release alone is not proof of today's title.
- **Moves need evidence:** `moved_company` needs a dated page naming the new employer. "Not on the leadership page" is `cannot_verify`, not a departure.
- **Priorities are quoted, not guessed:** every stated priority or talking point traces to something the person or their company published.
- **Nothing personal:** remove any home address, personal email or phone, family or other sensitive detail that slipped in, and never present a constructed email address.
- **Missing roles are reported:** a role nobody publicly holds belongs in `missing_roles` or `missing_fields`, not filled with a near match.

## 4. Many people, many accounts

- **People who match an ICP:** one `people-discovery` run per scope (a region, a sub-industry or a company-size band), 15 to 50 people per run; split a large market into several scoped runs and pass people already found as `input_data` with "exclude the people in input_data". The company criteria are verified per person, and people at companies that fail one land in `excluded` with the reason.
- **Decision makers across a list of accounts:** one `decision-maker-identification` run per account (it returns one company's people), run in parallel, about 10 at a time. For a thin first pass across hundreds of accounts, the fast path (one `site:linkedin.com/in "<Company>" "<Title>"` search per account and role) is cheaper; then run agents on the accounts that matter.
- **Champion tracking:** run `contact-job-change-monitor` over the contact list monthly in batches of about 5. A champion who moved is a new-logo lead at their new company: route it to `account-brief` for the new employer.
- **Buying committees:** one `buying-committee-map` run per target account, after the account list is final.
- Batching, concurrency, ledgers and CRM write-back rules are the same as for accounts: see `account-lists-and-enrichment`. Never overwrite a contact a rep entered; queue changes for review.

## 5. Privacy rules (apply to every people request)

- **Work-related public information only:** name, title, employer, career history, public talks, posts, articles and quotes. No home address, personal phone or email, family, health, age, religion, politics or other sensitive data.
- **Never construct email addresses or phone numbers** from patterns. Business contact details count only when the person or their company published them for business contact. If the user needs emails, they come from the user's licensed contact provider, matched on name, company and profile URL.
- **Public pages only.** No logged-in views, paywalls or CAPTCHA workarounds; LinkedIn and X are read only as logged-out pages and search results show them.
- **Purpose-bound.** Research people for the business purpose the user stated (a meeting, an account plan). Decline requests to profile someone's private life or to track an individual outside a work context.
- **The user's own rules win:** do-not-contact flags, opt-outs and regional privacy law (GDPR, CCPA, CASL) decide who is contacted, not what the web shows.

## Answer format

Lead with the answer, then the evidence and the freshness check:

> **Answer:** Shane Evans is Gong's Chief Revenue Architect (title since 2026-02-19; Gong announced him as Chief Revenue Officer on 2023-10-19).
> **Sources:** Gong blog, https://gong.io/blog/the-cra-is-the-new-cro-why-i-m-becoming-a-revenue-architect; appointment release, https://gong.io/press/gong-names-shane-evans-as-chief-revenue-officer (2023-10-19).
> **Checked:** Gong's newsroom and press coverage of his name in the last 12 months; no later change found.

For a brief or a map, lead with the bottom line (who matters and the best angle), then the people with a source and date for each.

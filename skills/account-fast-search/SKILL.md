---
name: account-fast-search
description: "Fast, cited web lookups for go-to-market work with Nimble Search, Extract and Extract Templates. Use for quick questions a seller, SDR, RevOps or marketing person asks about an account, a person or a competitor — who holds a role, whether they raised, the latest news, open sales roles on their ATS, what is on their pricing or integrations page, a customer they announced, a G2 rating, an event they're sponsoring — where one to a few searches or known pages answer it in seconds. Covers query writing, source priority, date scoping, entity disambiguation and privacy-safe sourcing. Escalate to account-deep-research when the question needs many sources or a structured multi-part answer."
metadata:
  author: Nimbleway
  version: 1.10.0
  category: gtm
---

# Fast web search for GTM

Nimble gives three fast tools. Pick the cheapest one that answers the question, and answer in seconds rather than minutes.

| Tool | What it does | Use it for |
| - | - | - |
| **Search** (`nimble_search`, `POST /v2/search`) | Live web results across engines; optional cited answer (`include_answer`), full page text (`full_content`) | Finding the page: the press release, the job post, the leadership page, the article. One closed fact. |
| **Extract** (`nimble_extract`, `POST /v2/extract`) | Clean markdown from one known URL, rendered and unblocked when needed | Reading the page you found: a pricing page, a careers page, an ATS board, a customer story, a newsroom post |
| **Extract Template** (`nimble_extract_templates_*`, `POST /v2/extract/templates/run`) | Structured JSON from a supported site (Google Maps, Indeed, LinkedIn job search, Google Search, ChatGPT and Perplexity answers, YouTube, TikTok...) | A known listing, job search, SERP or AI answer on a named site |

**Escalate** to `account-deep-research` when the answer needs more than about three searches or pages, several sources reconciled, a table, or verification across sites (a meeting brief, a trigger check, a competitive comparison). For anything about a specific person beyond one quick fact (a brief, a buying committee, job changes), use `people-research`. For a list of accounts or a CSV to fill, use `account-lists-and-enrichment`. For hundreds of job posts, reviews or listings over time, use `gtm-data-at-scale`.

## The fast loop

1. **Pin the entity.** Write down the company name and its **domain** before searching (plus HQ city or ticker if it helps). Use the domain in every query or as `include_domains`. Watch for namesakes (Eve the legal AI vs. Eve the mattress, Mercury the bank vs. Mercury the insurer), rebrands and former names, parents and subsidiaries, and products whose name differs from the company's. For a person, pin name plus current company.
2. **Decide what kind of source answers it** (see `references/source-map.md`) and aim the query there with `include_domains` or a `site:` operator.
3. **Search narrow.** `max_results` 3 to 5, `search_depth: "lite"` when titles and URLs are enough to pick the page, the default (`standard`) when snippets may hold the answer.
4. **Read the primary page** with Extract when the snippet is not enough or the value matters. Quote the value from the page, not from the snippet.
5. **Answer with the citation and its date**: the value, the URL it was read on, and the date the source published it. Say what you checked and did not find, naming the pages and the period they cover.

Stop at the first first-party or primary source that answers the question. If after three searches you are reconciling conflicting pages, escalate to a Web Search Agent instead of searching more.

## Writing queries

- **Quote exact phrases** a page would contain: `"appointed" "Chief Revenue Officer"`, `"joins as"`, `"Series B"`, `"led by"`, `"acquires"`, `"now available"`, `"partnership"`, `"case study"`.
- **Scope by domain**: the account's own domain for products, pricing, leadership and newsroom; ATS boards for hiring (`job-boards.greenhouse.io`, `boards.greenhouse.io`, `jobs.ashbyhq.com`, `jobs.lever.co`, `apply.workable.com`, `jobs.gem.com`); press wires (`prnewswire.com`, `businesswire.com`, `globenewswire.com`) for announcements; `g2.com`, `capterra.com`, `trustradius.com` for reviews. Up to 50 domains; `exclude_domains` drops listicles, content farms and data-broker pages.
- **Scope by time**: `time_range` (`day`, `week`, `month`, `year`) for "latest" questions, or `start_date` / `end_date` (YYYY-MM-DD) for a window such as "since our last call". They cannot be combined.
- **Pick the focus** (focus modes work only with `search_depth: "lite"`): `focus: "news"` for what happened recently; `focus: "general"` with `content_type: ["pdf"]` (or `presentations`) for case studies, annual reports and investor decks; `focus: "location"` for offices and stores; up to 10 Extract Template names in `focus` to fan one keyword across sites.
- **One question per search.** Run independent searches in parallel rather than one long query.

Patterns that travel across most tasks:

| Need | Query sketch |
| - | - |
| Who holds a role | `"<Company>" "VP of Sales" OR "Chief Revenue Officer"` with the company's domain; then a date-scoped search on the person's name to confirm the title is still current (see `people-research`) |
| A new executive | `"<Company>" <domain> appoints OR "joins as" OR hires CRO OR CMO OR "VP"`, `time_range: "month"` |
| Funding | `"<Company>" <domain> raises Series`, `focus: "news"` with `search_depth: "lite"`, `start_date` set to the window |
| Acquisitions and partnerships | `"<Company>" acquires OR "acquired by" OR partnership`, `focus: "news"` |
| Product launches | `include_domains: [<domain>]` + `launch OR "now available" OR "introducing"`, `time_range: "month"`; or Extract the changelog or blog |
| Hiring (and what they are building) | `"<Company>" jobs` with `include_domains` set to the ATS boards plus their careers domain, `search_depth: "lite"`, `max_results: 20`; Extract the board to count open roles by function |
| Tech stack they use | `"<Company>" "experience with" Salesforce OR HubSpot OR Snowflake` on ATS boards (job posts name tools); vendor case studies naming the account; their integrations page |
| Pricing and packaging | Extract the account's or competitor's `/pricing` page; `web.archive.org/web/<YYYYMMDD>/<url>` for the earlier version |
| Customers they announced | `"<Company>" "case study" OR "customer story" OR "selects"`, or Extract their customers page |
| Reviews and reputation | `"<Product>" reviews` with `include_domains: ["g2.com","capterra.com","trustradius.com"]`; `google_maps_reviews` template for local businesses |
| Events and sponsors | `"<Conference> 2026" sponsors OR exhibitors`, then Extract the sponsor page |
| What AI assistants say about a brand | `chatgpt`, `perplexity`, `google_ai` or `gemini` template with the buyer's prompt |
| Public company priorities | `"<Company>" "earnings call" OR "investor day" 2026`; 10-K and 8-K on sec.gov (`include_domains: ["sec.gov"]`) |

For a single closed fact, set `include_answer: true` (Nimble Answer) and still check that the answer cites a first-party or reputable page.

## Reading pages with Extract

- Pass the exact URL. Default output is markdown, which is what an agent should read.
- If the page comes back empty or truncated, retry with a JS-rendering driver (`vx8`) or a full-browser driver (`vx10`) before giving up; add `wait` (ms) for pages that load data late (many careers pages and ATS embeds do).
- Use `country` (and `locale`) for region-specific pricing.
- A PDF case study, annual report or deck can be parsed to markdown through the REST API or CLI with `file_parsing_options` (`{"mode": "light"}`); the MCP server does not expose that option.
- On sites Nimble maintains a template for, use the template: it returns stable fields instead of page text. Find it with `nimble_extract_templates_list(query="<site>")`, inspect params with `nimble_extract_templates_get`, run with `nimble_extract_templates_run`. Prefer templates `managed_by: "nimble"`; community templates vary in quality.

## Source priority

Use secondary pages to find facts and primary pages to cite them.

1. **The company's own pages**: site, newsroom and blog, leadership page, careers page and ATS board, pricing, docs and changelog, customers page. Authoritative for what the company says about itself; note that customer counts and growth claims are the company's claims.
2. **Official records**: SEC filings for public companies, state and national company registries, court dockets, government contract awards.
3. **Press releases and reputable press**: press wires, business and trade press.
4. **Aggregators and data sites** (Crunchbase, PitchBook, Tracxn, review aggregators): useful for discovery; often stale on headcount, funding totals and titles.
5. **Social posts and forums**: signals and context, not facts on their own. Verify against a first-party page.

When two sources disagree, show both with their dates; for fast-moving values (headcount, open roles, titles) the most recent dated first-party value usually wins.

## Timing and point-in-time

- Date events by when they happened, not when an article was published. Republished or roundup coverage of old news is the most common false "new" signal.
- Titles go stale quickly. A role counts as current only with a dated source in the last year or a page that shows it as current today.
- Job posts come and go. Record the date you saw a posting and its URL; a closed posting is not evidence of current hiring.
- Prices change without announcement. Quote the pricing page with the date you read it; use web.archive.org for the earlier version.
- Check whether something was reversed: an announced partnership that ended, an executive who has since left, a product that was sunset.

## Privacy and compliance guardrails (apply to every lookup)

- **Public information only.** Do not use logged-in, paywalled or purchased data, and do not try to get past logins, paywalls or CAPTCHAs or create accounts to see data.
- **Personal data is minimal.** Name, title, company and a public profile URL are usually enough. Never construct email addresses or phone numbers from patterns, and do not collect home addresses, personal social accounts or sensitive data.
- Respect opt-outs: if the user's own tools mark a person or company as do-not-contact, that wins over anything found on the web.
- Report a vendor's or analyst's claims (market share, "leader in") as attributed claims, not facts.

## Answer format

Lead with the answer, then the evidence:

> **Answer:** Datadog's Chief Revenue Officer is <name>, in the role since <month year>.
> **Source:** Datadog leadership page, https://..., read 2026-11-12; appointment release, https://..., published <date>.
> **Checked, nothing found:** Datadog newsroom and press wires from <date> to today; no later change.

Keep numbers with their units and dates, include every URL, and say how fresh each source is.

See `references/source-map.md` for the full map of GTM research questions to sources and how fast each goes stale.

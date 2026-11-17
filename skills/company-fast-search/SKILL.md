---
name: company-fast-search
description: "Fast, cited web lookups for company investment research with Nimble Search, Extract and Extract Templates. Use for quick questions an analyst or PM asks about a public or private company — a filing pointer, a date, an executive, a deal term, the latest 8-K, today's price or promotion on a retailer page, a recent news check, an IR deck link — where one to a few searches or known pages answer it in seconds. Covers query writing, source priority, date scoping, entity disambiguation and MNPI-safe sourcing. Do NOT use for a full company overview — use company-deep-dive instead. Do NOT use for a question that needs many sources or a structured multi-part answer — use company-deep-research instead."
metadata:
  author: Nimbleway
  version: 1.10.0
  category: finance-research
---

# Fast web search for company investment research

Nimble gives three fast tools. Pick the cheapest one that answers the question, and answer in seconds rather than minutes.

| Tool | What it does | Use it for |
| - | - | - |
| **Search** (`nimble_search`, `POST /v2/search`) | Live web results across engines; optional cited answer (`include_answer`), full page text (`full_content`) | Finding the page: the filing, the release, the deck, the article. One closed fact. |
| **Extract** (`nimble_extract`, `POST /v2/extract`) | Clean markdown from one known URL, rendered and unblocked when needed | Reading the page you found: an 8-K, an IR page, a pricing page, a court docket |
| **Extract Template** (`nimble_extract_templates_*`, `POST /v2/extract/templates/run`) | Structured JSON from a supported site (Amazon, Walmart, Google Maps, app and review sites, job boards...) | A known product, store, listing or SERP on a named site |

**Escalate** to `company-deep-research` when the answer needs more than about three searches or pages, several sources reconciled, a table, or verification across sites. To download a PDF or parse a long filing, use `filings-media-pdfs`. For hundreds of products, reviews or postings, use `alt-data-at-scale`.

## The fast loop

1. **Pin the entity.** Write down legal name, ticker, exchange and primary domain before searching (and SEC CIK when it is a US filer). Use two of them in every query. Watch for namesakes (Block vs H&R Block), share classes, parents and subsidiaries (the debt issuer is often a subsidiary with its own filings), brands that differ from the registrant, and former names after a rename or spin-off.
2. **Decide what kind of source answers it** (see `references/source-map.md`) and aim the query there with `include_domains` or a `site:` operator.
3. **Search narrow.** `max_results` 3 to 5, `search_depth: "lite"` when titles and URLs are enough to pick the page, the default (`standard`) when snippets may hold the answer.
4. **Read the primary page** with Extract when the snippet is not enough or the number matters. Quote the figure from the page, not from the snippet.
5. **Answer with the citation and its date**: the value, the URL it was read on, and the date the source published it. Say what you checked and did not find, naming the exact pages or registers and the period they cover.

Stop at the first primary source that answers the question. If after three searches you are reconciling conflicting pages, escalate to a Web Search Agent instead of searching more.

## Writing queries

- **Quote exact phrases** a document would contain: `"Item 5.02"`, `"going concern"`, `"material weakness"`, `"termination fee"`, `"guidance"`, `"amendment no."`.
- **Name the document type**: `10-K`, `8-K`, `DEF 14A`, `S-4`, `424B4`, `"investor presentation"`, `"earnings call transcript"`, `"press release"`.
- **Scope by domain**: `include_domains: ["sec.gov"]` for filings, the company's IR domain for decks, `["fda.gov","clinicaltrials.gov"]` for biotech, `["courtlistener.com"]` for dockets, `["usaspending.gov","sam.gov"]` for federal contracts. Up to 50 domains; `exclude_domains` drops mirrors, content farms and stock-promo sites.
- **Scope by time**: `time_range` (`day`, `week`, `month`, `year`) for "latest" questions, or `start_date` / `end_date` (YYYY-MM-DD) for a window such as "since the last earnings call" or "as of the deal announcement". They cannot be combined.
- **Pick the focus**: `focus: "news"` for what happened this week; `focus: "general"` with `content_type: ["pdf"]` (or `presentations`, `spreadsheets`) for decks, annual reports and statistical releases; `focus: "shopping"` for product pricing across merchants; `focus: "location"` for stores and sites.
- **One question per search.** Run independent searches in parallel rather than one long query.

Patterns that travel across most tasks:

| Need | Query sketch |
| - | - |
| Latest material event | `"<Company>" 8-K` + `include_domains: ["sec.gov"]`, `time_range: "month"` |
| Officer or director change | `"<Company>" "Item 5.02"` on sec.gov, or `"<Company>" appoints OR resigns CFO` with `focus: "news"` |
| Auditor change or restatement | `"<Company>" "Item 4.01"` / `"Item 4.02"` / `"non-reliance"` |
| IR deck or investor day | `"<Company>" "investor presentation" 2026`, `content_type: ["pdf","presentations"]`, or `include_domains: [<ir domain>]` |
| Merger terms | `"<Target>" "merger agreement" "termination fee"` on sec.gov (DEFM14A, S-4, 8-K Ex. 2.1) |
| Activist stake | `"<Company>" "SC 13D"` or `"<Company>" "open letter" nominate` with `focus: "news"` |
| Debt and covenants | `"<Company>" "credit agreement"` on sec.gov (8-K Ex. 10.x), `"<Company>" indenture "senior notes due"` |
| Distress | `"<Company>" forbearance OR "grace period" OR "restructuring support agreement"`, `"<Company>" "claims agent"` |
| Regulatory event | `site:fda.gov "<Company>" "warning letter"`, `site:clinicaltrials.gov <drug>` |
| Price or promotion today | Extract Template on the retailer (`walmart_pdp`, `amazon_pdp`, `target_serp`...), or Extract on the pricing page |
| Hiring signal | Extract the company's careers page or ATS board (Greenhouse, Lever, Ashby, Workday); `indeed_serp` template for postings |

For a single closed fact, set `include_answer: true` (Nimble Answer) and still check that the answer cites a primary page.

## Reading pages with Extract

- Pass the exact URL. Default output is markdown, which is what an agent should read.
- If the page comes back empty or truncated, retry with a JS-rendering driver (`vx8`) or a full-browser driver (`vx10`) before giving up; add `wait` (ms) for pages that load data late.
- Use `country` (and `locale`) for region-specific prices and availability.
- For PDFs, spreadsheets and decks, use `filings-media-pdfs` (Extract with `file_parsing_options`).
- On sites Nimble maintains a template for, use the template: it returns stable fields instead of page text. Find it with `nimble_extract_templates_list(query="<site>")`, inspect params with `nimble_extract_templates_get`, run with `nimble_extract_templates_run`. Prefer templates `managed_by: "nimble"`; community templates vary in quality.

## Source priority

Use secondary pages to find facts and primary pages to cite them.

1. **Regulatory filings and records**: SEC EDGAR, foreign regulators, courts, government databases (FDA, ClinicalTrials.gov, USAspending, FCC, FERC, state UCC and WARN portals).
2. **The company's own statements**: earnings releases, IR decks, webcast pages, press releases, careers and pricing pages. Primary but promotional; note company-defined metrics.
3. **Original reporting** from reputable outlets and trade press.
4. **Repeated press, aggregators and data sites.** Useful for discovery; often stale or wrong on units, periods and restatements.
5. **Social posts, forums, blogs and short reports.** Signals and allegations, never facts on their own. Verify each claim against a primary record.

When two sources disagree, the primary one wins; report the conflict if it matters.

## Timing and point-in-time

- Filing deadlines set how fresh a source can be: 8-K within 4 business days of most events, Form 4 within 2 business days, Schedule 13D within 5 business days of crossing 5%, 13F up to 45 days after quarter-end (so holdings can be months old).
- Prefer the filing or acceptance date over an article's date, and the fiscal period over the publication date. Note "as reported" versus "restated".
- For "as of" questions, use only pages dated on or before that date, and never fill gaps from model memory. Before concluding, check once for a newer filing, an amendment (`/A`) or a correction.
- A window is not a date. "Expected to close in the third or fourth quarter of 2027" is reported as that window, never as a specific day.
- Check whether a problem is still live. An exchange deficiency notice, covenant breach or going-concern doubt can be cured or withdrawn by a later filing; say "cured on <date>" rather than reporting it as current.

## Compliance guardrails (apply to every lookup)

- **Public information only.** Do not use paywalled, logged-in, leaked or confidential material, or expert-network transcripts: they carry MNPI risk. If only a paywalled headline and opening lines are public, they may be quoted, labeled "Headline only". A paywalled page is never the only source for a value.
- Do not try to get past logins, paywalls or CAPTCHAs, and do not create accounts to see data.
- Avoid collecting personal data that the question does not need.
- Report estimates, price targets and ratings as attributed views, not facts.

## Answer format

Lead with the answer, then the evidence:

> **Answer:** CoreWeave's next earnings date is 2026-11-12 (confirmed).
> **Source:** CoreWeave IR events page, https://..., published 2026-10-22.
> **Checked, nothing found:** EDGAR 8-K filings for CoreWeave from 2026-10-22 to today; none changes the date.

Keep numbers in their units and periods, include every URL, and say how fresh each source is.

See `references/source-map.md` for the full map of research questions to sources and their timing.

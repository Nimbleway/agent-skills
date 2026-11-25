---
name: nimble-search-focus-modes-reference
description: |
  Decision tree for selecting the right --focus mode for nimble search. Load when unsure which focus to use.
  Contains: mode-by-mode guide, example queries per mode, combination strategies, subagent scaling.
---

# Focus Modes Reference

Detailed guide for selecting the right `--focus` for your search query.

## Decision Tree

```
What are you searching for?
|
|-- A person? ................... --focus social  (+ parallel general)
|-- A known company? ............ --focus general (+ news for recent events)
|-- Companies by criteria? ..... focus: "company"
|-- IG/TikTok creators by criteria? focus: "creators"
|-- One exact social account? .. --focus general
|-- Code, docs, or technical? ... --focus coding
|-- Current events or news? ..... --focus news   (+ parallel social for reactions)
|-- Research papers? ............ --focus academic
|-- Products or prices? ......... --focus shopping
|-- A local business or place? .. --focus location
|-- Geographic/regional data? ... --focus geo
|-- General/unsure? ............. --focus general
```

## Focus Selection by Intent

| Query Intent              | Primary Focus | Secondary (parallel) | Why                                                                                                  |
| ------------------------- | ------------- | -------------------- | ---------------------------------------------------------------------------------------------------- |
| Research a **person**     | `social`      | `general`            | Social searches LinkedIn/X/YouTube directly via subagents; general covers blogs, news, company pages |
| Discover **companies by criteria** | `company` | — | Structured company profiles where available |
| Discover **Instagram/TikTok creators by criteria** | `creators` | — | Matching creator profiles |
| Look up **one known social account** | `general` | — | Use the name, handle or site |
| Research a **known company** | `general` | `news` | General for the overview, News for recent developments |
| Find **code/docs**        | `coding`      | —                    | Targets Stack Overflow, GitHub, docs sites                                                           |
| Current **events**        | `news`        | `social`             | News for articles; social for reactions/commentary                                                   |
| Find a **product/price**  | `shopping`    | —                    | Searches e-commerce sites                                                                            |
| Find a **place/business** | `location`    | `geo`                | Local business lookup                                                                                |
| Find **research papers**  | `academic`    | —                    | Targets scholarly sources                                                                            |
| **General/unsure**        | `general`     | —                    | Broad web search (default)                                                                           |

**Always run parallel searches with multiple focus when depth matters.**

Company and Creators searches return matching profiles, not exhaustive lists. These modes apply after choosing Search; they do not replace a Web Search Agent for research, enrichment, or dataset building.

## Mode Details

### general (default)

Standard web search across all sources. Use when no specific mode applies or for broad queries.

- Best for: overviews, general questions, company pages, blogs
- Speed: fastest (1-2s with `--search-depth lite`)

### company

Discover companies by industry, geography or business criteria. Profiles can include name, founding year, headcount, headquarters, revenue and funding when available. Use General for a known company's website or News for recent coverage.

### creators

Discover Instagram or TikTok accounts by niche, geography and follower range. Profiles can include platform, username, follower count, country, content categories and verification status. Narrow niches may return fewer profiles than requested. Use General for a named person's or business's specific account.

### Authenticated MCP examples

```json
{"query":"B2B payment infrastructure companies headquartered in Europe","focus":"company","search_depth":"lite","max_results":2}
```

```json
{"query":"Instagram fitness creators in Brazil with over 100k followers","focus":"creators","search_depth":"standard","max_results":2}
```

Read the profiles from `results[].entities`. For compatibility, see the [Search reference](reference.md#focus-modes).

### coding

Targets programming resources: Stack Overflow, GitHub, official docs, MDN, dev blogs.

- Best for: API references, code examples, debugging, framework docs
- Tip: include the language/framework name in the query for better targeting

### news

Current events and recent articles from news outlets and media sites.

- Best for: breaking news, recent developments, industry updates
- Tip: combine with `--time-range` to control recency (hour, day, week, month)

### academic

Scholarly content: research papers, journals, university publications.

- Best for: scientific research, citations, peer-reviewed studies
- Tip: use specific terminology and author names for better precision

### shopping

E-commerce sites and product listings. Uses subagents for Amazon, Target, etc.

- Best for: product comparisons, pricing, reviews, availability
- Note: uses `--max-subagents` (default 3) for parallel e-commerce searches

### social

Social media platforms: LinkedIn, X/Twitter, YouTube, Reddit, forums. Uses subagents.

- Best for: people research, public profiles, community discussions, opinions
- Note: returns LinkedIn/X/YouTube data directly via subagents — no need to extract those URLs
- Note: uses `--max-subagents` (default 3) for parallel social platform searches

### geo

Geographic and regional information.

- Best for: climate data, regional statistics, geographic features, area-specific info
- Tip: combine with `--country` for localized results

### location

Local business and place-specific queries.

- Best for: restaurants, shops, services in a specific area
- Tip: include the city/area name in the query

## Combination Strategies

For in-depth research, run 2-3 focus modes in parallel to maximize coverage:

| Research Goal        | Parallel Combination          | Query Strategy                                                  |
| -------------------- | ----------------------------- | --------------------------------------------------------------- |
| Person profile       | `social` + `general`          | Name + job title + company                                      |
| Company deep dive    | `general` + `news` + `social` | Company name, then news for recent events, social for sentiment |
| Technical evaluation | `coding` + `general`          | Technology name + use case                                      |
| Market research      | `shopping` + `news`           | Product category + "market" or "trends"                         |
| Local research       | `location` + `general`        | Business type + city name                                       |

## Mode Comparison

| Mode       | Speed  | Subagents | Best Sources      | Use Case           |
| ---------- | ------ | --------- | ----------------- | ------------------ |
| `general`  | Fast   | No        | All web           | Default, overviews |
| `coding`   | Fast   | No        | GitHub, SO, docs  | Programming        |
| `news`     | Fast   | No        | News outlets      | Current events     |
| `academic` | Fast   | No        | Journals, papers  | Research           |
| `shopping` | Medium | Yes (3)   | E-commerce        | Products, prices   |
| `social`   | Medium | Yes (3)   | LinkedIn, X, YT   | People, opinions   |
| `geo`      | Medium | Yes (3)   | Maps, regional    | Geographic data    |
| `location` | Medium | Yes (3)   | Local directories | Local business     |

Modes that use subagents (`shopping`, `social`, `geo`, `location`) are slightly slower but return richer, platform-specific data. Control parallelism with `--max-subagents` (1-10, default 3).

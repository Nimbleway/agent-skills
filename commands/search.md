---
description: Web search (default for all search and research queries)
argument-hint: <query>
---

# Web Search

## Query: $ARGUMENTS

Use the **nimble-web-expert** skill to search for this query.

For a quick shortlist of companies matching business criteria, use `nimble_search` with `focus: "company"`. For Instagram or TikTok creators matching niche, geography or follower criteria, use `focus: "creators"`. Use General to find one known account. Use a Web Search Agent for research or enrichment beyond the returned profiles. See the [focus guide](../skills/nimble-web-expert/references/nimble-search/search-focus-modes.md) for authenticated MCP examples.

For broad web search, run: `nimble search --query "$ARGUMENTS" --search-depth fast`

If a specific focus mode is appropriate (coding, news, academic, shopping, social, geo, location), add `--focus <mode>`. Default is general.

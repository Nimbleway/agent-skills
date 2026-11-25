---
description: Web search (default for all search and research queries)
argument-hint: <query>
---

# Web Search

## Query: $ARGUMENTS

Use the **nimble-web-expert** skill to search for this query.

Run: `nimble search --query "$ARGUMENTS" --search-depth fast`

If a specific focus mode is appropriate (coding, news, academic, shopping, social, geo, location), add `--focus <mode>`. Default is general.

When the request already calls for Search, use `focus: "company"` for company discovery by criteria, or `focus: "creators"` for Instagram/TikTok creator discovery by criteria. Use General to look up one known account. Focus selection does not change when to use a Web Search Agent. See the [focus guide](../skills/nimble-web-expert/references/nimble-search/search-focus-modes.md) for authenticated MCP examples.

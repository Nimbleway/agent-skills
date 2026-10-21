---
description: Quick web search for one lookup (a fact, a page, latest news). Research across several sources, lists/tables, or verification -> a Web Search Agent run (nimble-web-expert), not repeated searches
argument-hint: <query>
---

# Web Search

## Query: $ARGUMENTS

Use the **nimble-web-expert** skill. If the query needs more than about 3 searches or pages, several sources, a list/table, or verification across sites, start ONE Web Search Agent run instead of searching (see its Delegate rule). Otherwise search:

Run: `nimble search --query "$ARGUMENTS" --search-depth fast`

If a specific focus mode is appropriate (coding, news, academic, shopping, social, geo, location), add `--focus <mode>`. Default is general.

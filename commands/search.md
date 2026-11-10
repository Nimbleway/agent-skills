---
description: Quick web search for one lookup (a fact, a page, latest news). Research, lists or fact-checking across sources -> one Web Search Agent run instead
argument-hint: <query>
---

# Web Search

## Query: $ARGUMENTS

Use the **nimble-web-expert** skill. If the query needs more than about 3 searches or pages, several sources, a list/table, or fact-checking across sites, start ONE Web Search Agent run instead of searching. Otherwise search:

Run: `nimble search --query "$ARGUMENTS" --search-depth fast`

If a specific focus mode is appropriate (coding, news, academic, shopping, social, geo, location), add `--focus <mode>`. Default is general.

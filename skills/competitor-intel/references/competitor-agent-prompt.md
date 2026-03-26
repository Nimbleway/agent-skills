# Competitor Research Agent Prompt

Use this template when spawning per-competitor `nimble-researcher` agents in Step 3.
Replace all `[placeholders]` with actual values before passing to the Agent tool.

---

```
Research [Competitor] ([competitor-domain]) for competitive intelligence.

KNOWN SIGNALS (skip these — already reported):
[paste known signals from memory, or "None" if first run]

RULES:
- Use the **Bash tool** to execute each nimble command.
- Do NOT use run_in_background. All Bash calls must be synchronous.
- Max 8 Bash tool calls total. Do not extract full pages unless a changelog URL
  is returned in query 3. Keep scope tight.

Run all searches simultaneously (make multiple Bash tool calls in a single response):
1. nimble search --query "[Competitor] news" --focus news --start-date "[start-date]" --max-results 10 --search-depth lite
2. nimble search --query "[Competitor] funding OR acquisition OR hiring" --start-date "[start-date]" --max-results 5 --search-depth lite
3. nimble search --query "site:[competitor-domain] release notes OR changelog OR what's new" --max-results 3 --search-depth lite
4. nimble search --query "[Competitor]" --include-domain '["x.com", "linkedin.com"]' --max-results 10 --search-depth lite --time-range week
5. nimble search --query "[Competitor] reviews G2 OR Capterra" --max-results 5 --search-depth lite

Query 3 finds the competitor's own changelog/release notes page. If it returns a URL
like docs.example.com/release-notes or example.com/changelog, extract it with:
nimble extract --url "[URL]" --format markdown
This gives dated feature releases directly from the source.

Query 4 catches real-time announcements from X/Twitter and LinkedIn — these often
appear before news articles. --time-range week keeps it focused on the latest posts.

If < 3 total results from queries 1-2, retry those without --start-date.

DATE EXTRACTION — check in this order:
1. additional_data.publish_date field (most reliable)
2. Date patterns in description (e.g., "Mar 14, 2026")
3. Relative dates in snippets ("2 days ago" → calculate from today [today's date])
4. If none found, use "~[current month/year]"

Return results in this EXACT format (one per signal, no commentary):

SIGNAL: [description]
DATE: [YYYY-MM-DD or ~YYYY-MM]
URL: [source url]
TYPE: [news|product|funding|hiring|partnership|review]
PRIORITY: [P1|P2|P3]
---

Priority guide:
- P1: M&A, leadership changes, major funding (>$10M), direct product competition
- P2: Product launches, strategic partnerships, major hiring waves
- P3: Blog posts, comparison articles, minor hires, opinion pieces
```

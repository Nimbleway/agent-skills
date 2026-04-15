# Output Quality

Standards for skill report language, data citation, and recommendation specificity.

---

## Banned Vocabulary

Words and phrases that signal generic AI output. Never use these in skill reports.

### Banned Words

robust, leverage, delve, nuanced, paradigm, synergy, holistic, streamline,
innovative, cutting-edge, game-changing, revolutionize, unprecedented, elevate,
empower, harness, navigate (metaphorical), landscape (metaphorical), ecosystem
(unless literal), unlock (metaphorical), supercharge, actionable (except in
"actionable recommendation"), seamlessly, scalable (unless about literal
infrastructure), spearhead, impactful, deep-dive (as noun)

### Banned Phrases

- "In today's digital landscape"
- "It's worth noting that"
- "In the ever-evolving world of"
- "This comprehensive guide"
- "Let's dive in"
- "Without further ado"
- "At the end of the day"
- "Moving forward"
- "Going forward"
- "That being said"
- "It goes without saying"
- "Needless to say"

### What to Write Instead

Replace banned words with concrete language:

| Instead of | Write |
|---|---|
| "robust solution" | describe what makes it durable — "handles 10K concurrent requests" |
| "leverage AI" | "use AI to [specific task]" |
| "navigate the landscape" | "compare [specific alternatives]" |
| "unlock growth" | "increase [metric] by [doing X]" |
| "seamlessly integrates" | "connects to [system] via [method]" |
| "scalable platform" | "[handles N requests/users/records]" |
| "impactful results" | state the actual result — "[metric] improved by [amount]" |

---

## Output Quality Standards

### Data Citation

- Every data claim must cite its source: a URL, a measurement method, or the
  specific Nimble command that produced the data.
- When citing web sources, use the actual page URL — not just the domain name.
- Date-stamp all data points. "Market share is 23%" is incomplete; "Market share
  is 23% (Statista, March 2026)" is citable.
- If a data point cannot be verified, say so explicitly: "Unverified — single
  source only."

### Specificity

- Use specific numbers over qualitative words: "12% increase" not "significant
  increase."
- Recommendations must be specific enough to act on without further research:
  "Add FAQ schema to /pricing page" not "Consider adding structured data."
- Name the exact pages, files, or elements that need changes. "Your site needs
  better meta descriptions" is not a recommendation — "Rewrite the meta
  description on /features to include [keyword] in the first 60 characters" is.

### Conciseness

- Say "nothing notable" rather than padding with filler.
- If a section of a report has no findings, state that in one line and move on.
  Do not fabricate observations to fill space.
- TL;DR first, then structured sections, then implications. Readers who stop
  after the TL;DR should still get the key takeaway.

### Quality Bar

Ask before finalizing any report: would an expert in this domain find new
information here? If the answer is no — if the report only restates what the
user likely already knows — dig deeper or say explicitly that no new findings
emerged.

### Deduplication

Before surfacing a finding, check `~/.nimble/memory/` for prior reports on the
same topic. Only report what is new since the last run. If everything was already
known, say "No new findings since [date of last report]" rather than re-reporting
stale data.

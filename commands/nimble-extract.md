---
name: nimble-extract
description: Read a single URL as clean markdown via Nimble Extract
argument-hint: <url>
---

# Nimble Extract

## URL: $ARGUMENTS

Use the **nimble-web-expert** skill's Extract Waterfall to read this URL.

Run: `nimble --client-source nimble-agent-skills extract --url "$ARGUMENTS" --format markdown`

If the response is empty, truncated, or clearly JS-rendered content, escalate
through the waterfall tiers documented in
`skills/nimble-web-expert/references/nimble-extract/reference.md` (`--render`,
then a specific driver, then browser actions or network capture) rather than
falling back to `curl`, `WebFetch`, or any other tool.

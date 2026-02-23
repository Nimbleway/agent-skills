# Planning Workflow Reference

Detailed protocol for handling unclear or complex user intents that require
planning before execution.

## When to enter plan mode

**Most requests skip plan mode entirely** — the default route is
discover → get → run → display. Plan mode is the exception.

Enter plan mode only when ALL of these are absent from the request:

- A specific URL, site, or domain
- Clear or inferable data to extract
- A single well-scoped task

Typical plan-mode triggers: "build me a scraping pipeline",
"I need competitive intelligence", "scrape product data" (from where?),
or multi-source requests with unclear structure.

---

## Step 1P-1: Clarify requirements

Use `AskUserQuestion` to resolve the most critical unknowns. Focus on:

- What site(s) to target
- What data fields to extract
- What the output should look like (display, CSV, JSON, etc.)

Do NOT ask more than 2 questions at once. Infer what can be inferred from
the user's message and project context.

---

## Step 1P-2: Explore available agents

Call `nimble_agents_list` with keywords for each target site/domain. For
unfamiliar domains, use `nimble_web_search` to understand what data exists
and how pages are structured before committing to an agent approach.

---

## Step 1P-3: Present a plan

Show a gap analysis table summarizing what exists and what needs generation:

| # | Site / Data Source | Agent | Status |
|---|-------------------|-------|--------|
| 1 | amazon.com products | amazon-product-details | Existing |
| 2 | walmart.com products | — | Generate |
| 3 | bestbuy.com products | — | Generate |

- **Existing** — agent found via `nimble_agents_list`, ready to run.
- **Generate** — no matching agent; a custom agent will be generated.

Confirm the plan with `AskUserQuestion` before executing:

```
question: "Proceed with this plan?"
header: "Confirm"
options:
  - label: "Execute plan (Recommended)"
    description: "Run existing agents and generate missing ones"
  - label: "Adjust"
    description: "Modify the plan before executing"
```

---

## Step 1P-4: Execute

After confirmation:

- **Existing agents** → proceed to Step 2 (agent discovery) in SKILL.md.
- **Agents to generate** → proceed to Step 3C (generate path). Launch
  generations **in parallel** as background tasks — one per session_id.
  Each background task polls independently via
  `nimble_agents_status`. Gather results and proceed when all
  complete.

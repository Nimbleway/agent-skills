# Extraction Template Discovery for Healthcare Providers Enrich

How to find and evaluate Extraction Templates for enriching existing provider records. The Extraction Template catalog
evolves constantly — this skill discovers relevant agents at runtime rather than
relying on a static list.

For general Extraction Template execution rules (invocation, parsing, batch, fallback), see
`nimble-playbook.md`.

---

## Discovery Strategy

### Three search layers

Run these searches during preflight (Step 0) to build a session-specific Extraction Template
inventory. Run all searches simultaneously:

**Layer 1 — Vertical search:**
```bash
nimble extract:templates list --limit 100  # filter items for "healthcare"
```
Returns all agents tagged with the Healthcare vertical (clinical trials, FDA,
regulatory, and any newly added healthcare agents).

**Layer 2 — Session-specific search:**
Search for terms derived from the user's input — their specialty, specific
directories, or data sources they mentioned:
```bash
# If user's list is ophthalmologists:
nimble extract:templates list --limit 50  # filter items for "ophthalmology"
nimble extract:templates list --limit 50  # filter items for "eye"

# If user mentioned specific directories:
nimble extract:templates list --limit 50  # filter items for "healthgrades"
nimble extract:templates list --limit 50  # filter items for "zocdoc"
nimble extract:templates list --limit 50  # filter items for "npi"
```
Adapt search terms to whatever the user provided. Include the specialty, common
directory names for that specialty, and any data sources the user mentioned.

**Layer 3 — General enrichment tools:**
These Extraction Templates are useful across verticals for reputation, verification, and practice
details:
```bash
nimble extract:templates list --limit 50  # filter items for "google_maps"
nimble extract:templates list --limit 50  # filter items for "yelp"
nimble extract:templates list --limit 50  # filter items for "bbb"
nimble extract:templates list --limit 50  # filter items for "review"
```

### Evaluating discovered agents

For each discovered agent, read its `description` and `entity_type` to classify it
into an enrichment category:

| If the agent description mentions... | Assign to category |
|--------------------------------------|-------------------|
| Reviews, ratings, patient feedback, reputation | **Reputation** — practice/provider ratings |
| Clinical trials, FDA, regulatory, compliance, licensing | **Regulatory** — credentials and compliance data |
| Profile, detail page, business info, contact, hours | **Practice details** — supplementary practice info |
| Search, listings, directory, discovery | **Identity** — finding provider web presence |

Validate each relevant agent's params before using it:
```bash
nimble extract:templates get --extract-template-name [agent_name]
```

**Skip agents that don't fit** — not every healthcare-tagged agent is useful for
enrichment. A drug interaction agent, for example, isn't relevant for filling
provider contact info.

---

## Enrichment Phase Mapping

Unlike healthcare-providers-extract (which focuses on discovery and extraction),
this skill focuses on three enrichment categories. Identity search uses
`nimble search` directly — Extraction Templates add value in the enrichment phases.

### Identity (finding provider web presence)

**When:** Always — this is how you find bio pages for providers in the input list.

**Primary tool:** `nimble search` (not Extraction Template-dependent):
```bash
nimble search --query "[name] [credentials] [location] [specialty]" --max-results 5 --search-depth lite
```

**Extraction Template supplement:** If Layer 2 discovery found directory-specific agents (e.g., a
healthcare provider profile agent), use them for providers listed on that directory
to get structured data directly.

### Reputation enrichment

**When:** User requested reviews, ratings, or practice reputation data.

**Search terms for discovery:** `review`, `google_maps`, `yelp`, `bbb`

**How to use:** Run discovered review/rating agents with the provider's practice
name + location. Match results back to the provider record.

**Fallback:**
```bash
nimble search --query "[practice-name] [city] reviews ratings" --max-results 5 --search-depth lite
```

### Regulatory enrichment

**When:** User requested clinical trial activity, FDA data, board certification,
or accreditation status.

**Search terms for discovery:** `healthcare` vertical, `clinicaltrials`, `fda`,
`npi`, `license`, `board`

**How to use:** Run discovered regulatory agents with the provider's name and
credentials. Cross-reference results with existing provider data.

**Fallback:**
```bash
nimble search --query "[provider-name] [credentials] NPI OR license OR board certification" --max-results 5 --search-depth lite
```

### Practice details enrichment

**When:** User wants hours, insurance accepted, staff count, or other practice-level
data.

**Search terms for discovery:** Directory-specific agents found in Layer 2.

**Fallback:**
```bash
nimble search --query "[practice-name] [city] hours insurance" --max-results 5 --search-depth lite
```
Then extract the top result with `nimble extract --url "[url]" --format markdown`.

---

## Scaling Extraction Template Calls

Follow the Scaled Execution pattern from `nimble-playbook.md` — it covers
individual calls, batching, and the confirmation gate for large jobs.

For enrichment, estimate calls as: `[providers] x [enrichment categories requested]`.
A list of 50 providers with reputation + regulatory = ~100 Extraction Template calls = batch tier.

---

## Fallback Chain

If Extraction Template discovery returns nothing useful for a category, fall back to `nimble search`
+ `nimble extract` (the core Nimble tools always work):

1. **Identity fallback:** `nimble search --query "[name] [location] doctor" --max-results 5 --search-depth lite`
2. **Reputation fallback:** `nimble search --query "[practice-name] reviews" --max-results 5 --search-depth lite` + `nimble extract` on results
3. **Regulatory fallback:** `nimble search --query "[name] [credentials] NPI OR license OR board certification" --max-results 5 --search-depth lite`

The skill always produces results even if zero Extraction Templates are found — Extraction Templates accelerate
and enrich, but are never required.

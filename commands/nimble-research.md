---
name: nimble-research
description: Run a Web Search Agent for open-ended, cited research (create-or-reuse)
argument-hint: <question or task>
---

# Nimble Research

## Task: $ARGUMENTS

Use the **nimble-web-expert** skill's Web Search Agents flow — this is for a
finished, cited deliverable (a report, comparison, or enrichment), not a quick
scan. For a raw list of pages instead, use `nimble search` directly.

Follow the reuse-priority chain in
`skills/nimble-web-expert/references/nimble-agents/reference.md`: look for an
existing agent before creating one, then run named create-or-reuse:

If the task restricts domains, build `sources` with the exact Agent API V2
shape below. This applies to MCP tools and CLI `--sources` payloads alike.
`allow` and `block` are arrays of source-group objects; never emit bare domain
or URL strings in either array. `title` and `domains` are required on every
group, `domains` contains hostnames rather than URLs, and `order` is optional.
`prioritize` and `avoid` are guidance strings, not arrays.

```json source-guidance-contract
{
  "allow": [
    {"title": "Official Slack", "domains": ["slack.com"], "order": 0},
    {"title": "Official Microsoft", "domains": ["microsoft.com"], "order": 1}
  ],
  "block": [
    {"title": "Non-official comparison sites", "domains": ["g2.com", "capterra.com"], "order": 0}
  ],
  "prioritize": "Prefer current pricing and product documentation.",
  "avoid": "Avoid search snippets and unsupported secondary summaries."
}
```

Before a create or run that includes `sources`, inspect the final payload and
stop locally if any `allow` or `block` entry is not an object with a non-empty
string `title` and a non-empty string-array `domains`, or if a domain is not a
hostname. A source-shape failure must not consume the one allowed create
attempt. Keep the validated object unchanged and pass its serialized JSON to
the run as `--sources '<validated-source-guidance-json>'` (or as the MCP
tool's `sources` object). Never describe a restriction without also passing it.

Before the run, derive a positive integer source budget from the task. Use an
explicit user-provided limit when present; otherwise use **6**. Append this
verbatim contract to the run input (substituting the integer for `<N>`):

> HARD SOURCE-STOP CONTRACT: Use at most <N> unique web page URLs for this run.
> Count a page when its URL is read, opened, extracted, or cited. Search-result
> snippets do not count unless their target URL is used. Stop discovering or
> reading new pages as soon as <N> unique URLs have been used. Prefer the most
> authoritative pages within the budget. The terminal trust.sources list must
> contain no more than <N> unique canonical URLs. If the task cannot be grounded
> within this budget, return a partial result that says what remains unknown;
> never exceed the budget.

Append this claim-grounding contract to the same run input:

> HARD CLAIM-GROUNDING CONTRACT: Return one Markdown decision table followed by
> a Recommendation section. Every populated factual comparison cell must include
> one or more numbered callouts that exist in terminal trust.claims. Render a cell
> Unknown rather than stating a fact without a mapped callout. Every factual
> reason used by the recommendation must include a mapped callout already used by
> the decision table. Do not add uncited factual prose outside the table. If these
> conditions cannot be met, return only the grounded subset and mark the rest
> Unknown; never infer or present an unmapped claim.

Set client retry policy to `max_retries=0`. If the available transport cannot
guarantee one create attempt with no automatic retry or fallback, stop before
the create. Never issue a replacement create after any terminal result or
audit failure.

Run exactly once:

`nimble --client-source nimble-agent-skills agents run --agent-name <stable-descriptive-name> --use-case research --input "<task plus source-stop and claim-grounding contracts>" --sources '<validated-source-guidance-json>' --effort low`

Omit `--sources` only when the task has no source restriction or guidance.

The response carries `web_search_agent_id` and `id` (`interaction_id`) — keep
both, and pass them as `--agent-id` and `--run-id`; `agents:runs get` and
`agents:runs result` each require both. Poll
`nimble --client-source nimble-agent-skills agents:runs get --agent-id <web_search_agent_id> --run-id <id>`
until finished, then run `mkdir -p .nimble` and fetch
`nimble --client-source nimble-agent-skills agents:runs result --agent-id <web_search_agent_id> --run-id <id> > .nimble/nimble-research-result.json`.
This saves the complete result JSON. Audit the hard postcondition before
presenting it. Use this self-contained standard-library check so the command
does not depend on a host-specific plugin-root variable:

```bash
python3 - <N> .nimble/nimble-research-result.json <<'PY'
import json, sys
from urllib.parse import urlsplit, urlunsplit

budget, path = int(sys.argv[1]), sys.argv[2]
payload = json.load(open(path, encoding="utf-8"))
while isinstance(payload, dict) and not isinstance(payload.get("trust"), dict):
    payload = payload.get("data", payload.get("result"))
trust = payload.get("trust") if isinstance(payload, dict) else None
sources = trust.get("sources") if isinstance(trust, dict) else None
if not isinstance(sources, list):
    raise SystemExit("HOLD_SOURCE_BUDGET_INVALID_RESULT: missing trust.sources")

urls = set()
for source in sources:
    value = source.get("url") if isinstance(source, dict) else None
    parsed = urlsplit(value.strip()) if isinstance(value, str) else None
    if not parsed or parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise SystemExit("HOLD_SOURCE_BUDGET_INVALID_RESULT: invalid source URL")
    scheme, host, port = parsed.scheme.lower(), parsed.hostname.lower(), parsed.port
    netloc = host if port in {None, 80 if scheme == "http" else 443} else f"{host}:{port}"
    source_path = parsed.path or "/"
    urls.add(urlunsplit((scheme, netloc, source_path if source_path == "/" else source_path.rstrip("/"), parsed.query, "")))

observed = len(urls)
if observed > budget:
    raise SystemExit(f"HOLD_SOURCE_BUDGET_EXCEEDED: budget={budget} observed_unique_sources={observed}")
print(f"SOURCE_BUDGET_PASS budget={budget} observed_unique_sources={observed}")
PY
```

The audit counts unique canonical URLs in `trust.sources`; repeated citations
to one canonical URL count once. A non-zero audit exit is a real terminal
`HOLD_SOURCE_BUDGET_EXCEEDED` outcome. Malformed/missing trust metadata is
`HOLD_SOURCE_BUDGET_INVALID_RESULT`; do not bypass the audit. Report the agent
ID, run ID, requested budget, and observed count when available, preserve the
result for inspection, and stop. Do not present an unaudited or over-budget
deliverable as successful and do not create a replacement run. On audit
success, report the terminal result with its per-claim citations and trust
metadata intact — do not summarize away the sourcing.

Then run a second fail-closed audit over the saved result. It must verify that
every populated decision-table cell has a numbered callout present in
`trust.claims`, every claim citation URL exists in `trust.sources`, every
recommendation paragraph has a mapped callout already used by the table, and
there is no extra uncited factual prose. Run this portable audit before showing
the deliverable:

```bash claim-grounding-audit
python3 - .nimble/nimble-research-result.json <<'PY'
import json, re, sys
from urllib.parse import urlsplit, urlunsplit

def canonical(value):
    parsed = urlsplit(value.strip())
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise SystemExit("HOLD_CLAIM_GROUNDING_INVALID_RESULT: invalid source URL")
    scheme, host, port = parsed.scheme.lower(), parsed.hostname.lower(), parsed.port
    netloc = host if port in {None, 80 if scheme == "http" else 443} else f"{host}:{port}"
    path = parsed.path or "/"
    return urlunsplit((scheme, netloc, path if path == "/" else path.rstrip("/"), parsed.query, ""))

payload = json.load(open(sys.argv[1], encoding="utf-8"))
while isinstance(payload, dict) and not (
    isinstance(payload.get("trust"), dict) and payload.get("output") is not None
):
    payload = payload.get("data", payload.get("result"))
if not isinstance(payload, dict):
    raise SystemExit("HOLD_CLAIM_GROUNDING_INVALID_RESULT: missing output/trust")
trust, output = payload["trust"], payload["output"]
text = output.get("content") if isinstance(output, dict) else output
if not isinstance(text, str):
    raise SystemExit("HOLD_CLAIM_GROUNDING_INVALID_RESULT: output is not text")
source_urls = {canonical(source["url"]) for source in trust.get("sources", [])}
trusted = set()
for claim in trust.get("claims", []):
    callout, citations = claim.get("callout"), claim.get("citations")
    if not isinstance(callout, int) or isinstance(callout, bool) or callout < 1 or not citations:
        raise SystemExit("HOLD_CLAIM_GROUNDING_INVALID_RESULT: malformed trust.claims")
    if callout in trusted:
        raise SystemExit("HOLD_CLAIM_GROUNDING_INVALID_RESULT: duplicate trust.claims callout")
    if any(canonical(citation["url"]) not in source_urls for citation in citations):
        raise SystemExit("HOLD_CLAIM_GROUNDING_INVALID_RESULT: claim citation absent from trust.sources")
    trusted.add(callout)

callout_re = re.compile(r"\[(\d+)\]")
unknown = {"unknown", "omitted", "not disclosed"}
refs = lambda value: {int(number) for number in callout_re.findall(value)}
is_unknown = lambda value: re.sub(r"[*_`]", "", value).strip().lower().rstrip(".") in unknown
rows = [line for line in text.splitlines() if line.strip().startswith("|") and "---" not in line]
if len(rows) < 2:
    raise SystemExit("HOLD_CLAIM_GROUNDING_UNMAPPED: missing decision table")
table_refs = set()
for row in rows[1:]:
    cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
    for cell in cells[1:]:
        cell_refs = refs(cell)
        if cell_refs - trusted or (not is_unknown(cell) and not cell_refs):
            raise SystemExit("HOLD_CLAIM_GROUNDING_UNMAPPED: populated or mismatched decision cell")
        table_refs.update(cell_refs)
match = re.search(r"^##\s+Recommendation[^\n]*\n(.*?)(?=^##\s+|\Z)", text, re.M | re.S | re.I)
if not match:
    raise SystemExit("HOLD_CLAIM_GROUNDING_UNMAPPED: missing Recommendation")
for paragraph in [part.strip() for part in re.split(r"\n\s*\n", match.group(1)) if part.strip()]:
    paragraph_refs = refs(paragraph)
    if paragraph_refs - trusted or paragraph_refs - table_refs or not paragraph_refs:
        raise SystemExit("HOLD_CLAIM_GROUNDING_UNMAPPED: recommendation uses an unmapped claim")
scrubbed = re.sub(r"^##\s+Recommendation[^\n]*\n.*?(?=^##\s+|\Z)", "", text, flags=re.M | re.S | re.I)
scrubbed = re.split(r"^Source index:\s*$", scrubbed, flags=re.M | re.I)[0]
for line in scrubbed.splitlines():
    value = line.strip()
    if not value or value.startswith(("#", "|", "---")) or value.lower().startswith("cited from"):
        continue
    if refs(value) - trusted or not refs(value):
        raise SystemExit("HOLD_CLAIM_GROUNDING_UNMAPPED: extra uncited answer claim")
print("CLAIM_GROUNDING_PASS every decision-driving claim maps to trust.claims")
print("RECOMMENDATION_CALLOUTS", *sorted(refs(match.group(1))))
PY
```

`scripts/check-research-claim-grounding.py` regression-tests this contract,
including the preserved failed live result.

A failure is `HOLD_CLAIM_GROUNDING_UNMAPPED`: render the affected cells Unknown
or omit them, do not use them in the recommendation, and do not create a
replacement run. Only report `CLAIM_GROUNDING_PASS` after both source-budget
and claim-grounding audits pass. Include the mapped callout numbers used by the
recommendation in the final visible audit.

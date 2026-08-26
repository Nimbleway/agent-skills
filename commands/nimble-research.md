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

Run exactly once:

`nimble --client-source nimble-agent-skills agents run --agent-name <stable-descriptive-name> --use-case research --input "<task plus source-stop contract>" --sources '<validated-source-guidance-json>' --effort high`

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

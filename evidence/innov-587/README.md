# INNOV-587 exact-commit integration evidence

Evidence captured on 2026-08-19 from commit
`8bc9c811f82a3096d07c211ea0543c73203fea01` on PR #67.

## Cursor IDE

![Cursor exact-commit plugin inventory](cursor-exact-commit.jpeg)

The detached checkout at
`~/.cursor/plugins/local/nimble-8bc9c81` resolved to the commit above. Cursor's
native plugin view discovered the package as `Nimble 8bc9c81` and showed one
MCP server, 15 skills, two subagents, and one command. Cursor plugin-host logs
recorded `loadUserLocalPlugin nimble-8bc9c81` with zero aggregate plugin-load
failures; the redacted excerpt is included in `cursor-plugin-load.log`.

This is a local private installation. Cursor Marketplace submission, review,
listing, acceptance, and publication were not performed and remain separate
open gates.

Reproduce the credential-free packaging checks:

```bash
python3 scripts/check-plugin-manifests.py
bash scripts/check-plugin-structure.sh
bash scripts/tag-release.sh --check
```

Observed results: 162 manifest checks passed, plugin structure passed, and all
22 version references agreed on `1.6.1`.

## Grok Bot hosted MCP

![Grok Bot connected Nimble MCP](grok-mcp-connected.jpeg)

Grok Bot showed a manually added HTTP connector named `nimble`, connected to
`https://mcp.nimbleway.com/mcp`, with 27 of 27 tools enabled. An unauthenticated
credential-free MCP initialization probe returned `401 Unauthorized` and the
server's OAuth protected-resource metadata, as expected. No credential appears
in the screenshots or repository.

The connected account shown in the app had already been authorized by the
account owner. The unauthenticated `401` probe was a separate out-of-band
reachability check and did not establish or modify that authenticated account.

## Grok Bot Web Search Agent / Agent API V2 lifecycle

![Grok Bot Agent API V2 lifecycle](grok-agent-v2-lifecycle.jpeg)

The account owner initiated this live run in Grok Bot. The Bot reported this
tool sequence through the Nimble MCP:

1. `nimble_agents_list`
2. `nimble_agent_templates_list`
3. `nimble_agents_run`
4. poll `nimble_agents_run_status`
5. `nimble_agents_run_result`

The UI preserved agent ID
`wsa_2d3d239e27cb4def9f43eb40e6de2b01` and run ID
`task_run_37f092e4db3841eba1e624328a52efb7` across queued, running, and finished
messages. The terminal response reported ten cited claims, labeled
official/news sources, stable Nimble attribution, and explicit gaps where an
official source did not support a claim.

## Grok skill provenance and remaining gate

![Grok Bot locally created Nimble private skill](grok-private-skill.jpeg)

This is intentionally not claimed as exact-commit canonical-plugin discovery.
Grok Bot displayed three locally created private Nimble skills. The inspected
`Nimble Web Expert` instructions were a local adaptation and not an installed
copy proven to match this repository commit. Placing the exact checkout under
the documented Grok Build user-plugin directory (`~/.grok/plugins/`) did not
make a separate canonical plugin appear in the Grok Bot app's `Yours` view.

Therefore the evidence proves the hosted MCP and Agent API V2 lifecycle in
Grok Bot, but the exact-commit canonical skill/plugin installation gate remains
open. Marketplace submission, acceptance, publication, and activation remain
separate and were not performed.

We did not trigger a failing run to capture its structured error format because
that would require another live, potentially billable Nimble operation. Secret
safety is evidenced only by the absence of credentials from manifests, the
redacted Cursor log excerpt, and screenshots; it is not a claim that every
external runtime log was audited.

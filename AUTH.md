# auth.md

Not an agent? You might be looking for the docs at https://docs.nimbleway.com/.

You are an agent that wants to call the Nimble API on a user's behalf. This document tells you how to obtain a credential and use it safely. Follow the steps in order; do not skip ahead.

Two hosts are relevant:

- Resource server — `https://sdk.nimbleway.com` — the API you will call.
- Dashboard — `https://online.nimbleway.com` — where the user manages their account and keys.

## Current state

Nimble does not support *agentic* registration today: there is no endpoint an agent can call to mint a credential for itself. Concretely, Nimble does not expose `/agent/auth`, claim endpoints, identity-assertion flows (ID-JAG or verified-email), anonymous registration, or a provider-driven `revocation_uri`. If you have an ID-JAG in hand, you cannot exchange it against Nimble today.

Nimble **does** support user OAuth. If you are an MCP client, that is the best path and it involves no API key at all — see the shortcut below. Otherwise the user creates a key in the dashboard and you read it from the environment, per the steps below.

## Shortcut — use Nimble tooling (recommended)

Before doing anything credential-shaped, check whether the user has already wired Nimble into your environment. Each of these handles auth for you, so you never touch the raw key:

1. **Nimble MCP server (best option)** — if you are an MCP client (Claude, Cursor, Codex, etc.), Nimble ships an official server at `https://mcp.nimbleway.com/mcp` exposing search, extract, crawl, map, and agents as tools. It supports **OAuth 2.1 with PKCE**, discoverable from the `WWW-Authenticate` header on a `401`. Where the client supports OAuth there is no API key in the flow at all: the user approves scopes in a browser and the client stores and refreshes the token. Otherwise pass a key as `Authorization: Bearer <key>`. Setup guide: `https://docs.nimbleway.com/integrations/mcp-server/mcp-server`.
2. **Agent Skills** — ready-made skill files for web search, extraction, business research, SEO, and more. Install once, use from any AI coding assistant. Index: `https://docs.nimbleway.com/integrations/agent-skills/plugin-installation`.
3. **Nimble CLI** — if you are running shell commands, prefer `nimble` over hand-rolled `curl`. Install: `npm i -g @nimble-way/nimble-cli`. The CLI reads `NIMBLE_API_KEY` automatically.

If any of these is already configured, use it and stop. Do not ask the user for an API key you do not need.

**If you are an MCP client and the Nimble server is not connected yet, connect it rather than falling through to a key.** On Claude products, `/plugin install nimble` registers the connector, then `/mcp` authenticates in the browser. On other clients, add `https://mcp.nimbleway.com/mcp` to your MCP settings and have the user approve access. Either way there is no API key to create.

Continue to Step 1 only if none of the above is possible, for example the client cannot speak MCP or does not support OAuth.

## Step 1 — Find an existing key

Check in this order. Stop at the first one that exists:

1. `NIMBLE_API_KEY` in your process environment.
2. A `.env` file the user has told you to read.
3. The MCP server's environment, if you are calling through it.

If you find one, go to [Step 3](#step-3--use-the-credential). If none exists, continue to Step 2.

## Step 2 — Help the user create one

Do not ask the user to paste an API key into the conversation. Instead:

**New account:** Direct the user to open `https://online.nimbleway.com/signup` in their browser (open it for them if you can). Tell them to complete the signup form and confirm their email before the dashboard is available, then come back once logged in.

**Existing account:** Direct the user to `https://online.nimbleway.com/login`.

Once logged in, direct the user to `https://online.nimbleway.com/settings/api-keys` and tell them:

> "Click **Create key**, give it a descriptive name like 'agent', then copy it immediately — it's shown only once — and set it as NIMBLE_API_KEY in your environment. Issue a separate key per agent or project so it can be deleted independently."

Wait for the user to confirm the variable is set, then read it from the environment and continue to Step 3.

## Step 3 — Use the credential

Read `NIMBLE_API_KEY` from the environment at the moment of the call. Present it as a bearer token:

```bash
curl -X POST 'https://sdk.nimbleway.com/v2/search' \
  --header "Authorization: Bearer $NIMBLE_API_KEY" \
  --header 'Content-Type: application/json' \
  --data '{
    "query": "latest AI developments",
    "focus": "general",
    "max_results": 5,
    "search_depth": "lite"
  }'
```

**Key safety rules:**
- Do not copy the key into variables you log.
- Do not echo it back to the user.
- Do not include it in commit messages, PR descriptions, error reports, or screenshots.
- When running shell commands, reference `$NIMBLE_API_KEY` — never interpolate the value inline.

If you get a `401` on a previously-working key, drop it and restart at [Step 1](#step-1--find-an-existing-key). Do not stash the credential and retry.

## Errors

| Status | Meaning | What to do |
|---|---|---|
| `401` on first use | Key is malformed, revoked, or for a different environment. | Ask the user to confirm the value in `NIMBLE_API_KEY` is current and active in the dashboard. Do not ask them to paste it. |
| `401` on a previously-working key | Revoked or rotated. | Drop the cached value and ask the user to refresh it from `https://online.nimbleway.com/settings/api-keys`, then set `NIMBLE_API_KEY` again. |
| `403` | Key lacks permission for this resource, or the plan doesn't include it. | Ask the user to confirm the key's account has access to this endpoint in the dashboard. |
| `429` | Rate limited. | Back off and retry. Honor `Retry-After` if present. |

## Revocation

The user revokes keys at `https://online.nimbleway.com/settings/api-keys` (Delete). You will discover revocation as a `401` on a previously-working credential — drop it and re-read from the same source you loaded it from.

Full API reference: https://docs.nimbleway.com/
Integration questions: developers@nimbleway.com

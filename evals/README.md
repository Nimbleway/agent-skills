# nimble-web-expert production evals

Evaluate [`skills/nimble-web-expert`](../skills/nimble-web-expert/) through **Claude Code** and **Codex** CLIs. Results go to a **private** Langfuse dataset: `nimble-web-expert-production`.

Prompts and traces are **not** stored in this public repo — load items from Langfuse.

## Setup

```bash
cd evals
uv sync
cp .env.example .env
# fill LANGFUSE_*
```

Prerequisites on the machine:

- `claude` CLI (Claude Code) signed in
- `codex` CLI signed in (for `--runtime codex|both`)
- Optional for live tool scoring: `npm i -g @nimble-way/nimble-cli` + `NIMBLE_API_KEY`

Codex runs with an isolated `$HOME` (only `nimble-web-expert` under
`.agents/skills/`, empty memory tree) plus a per-run `workdir/.agents/skills/`
symlink, while auth stays on the real `CODEX_HOME` (`~/.codex`). Claude uses a
thin eval-only `--plugin-dir` (only `nimble-web-expert`) and **disallows**
built-in `WebSearch`/`WebFetch`.

Both runtimes receive a **real user prompt**: the production text, prefixed with
a slash-skill invoke so the agent loads the skill the way a human would:

```text
# Claude (eval plugin namespace — args on the same line for --bare expansion)
/nimble-web-expert-eval:nimble-web-expert {original production prompt}

# Codex
/nimble-web-expert

{original production prompt}
```

Skill load is driven by that user turn (not a long `--append-system-prompt`).

## Models (pinned)

| Runtime | Model | Effort |
|---|---|---|
| Claude | `claude-sonnet-5` | `--effort medium` |
| Codex | `gpt-5.6-sol` | `model_reasoning_effort=medium` |

Overrides: `EVAL_CLAUDE_MODEL`, `EVAL_CLAUDE_EFFORT`, `EVAL_CODEX_MODEL`, `EVAL_CODEX_REASONING_EFFORT`.

## Commands

```bash
# Hard smoke gate (must-act IDs): skill must load + at least one `nimble …` tool.
# Default runtime=both, timeout=600s. Fails if Codex uses web_search.
uv run python -m evals.suites.web_expert --smoke
uv run python -m evals.suites.web_expert --smoke --runtime claude
uv run python -m evals.suites.web_expert --smoke --runtime codex

# Dry-load: verify dataset mix without calling CLIs
uv run python -m evals.suites.web_expert \
  --dataset-name=nimble-web-expert-production \
  --dry-load --max-items 50

# Stratified sample (Claude) — uploads experiment traces + scores to Langfuse
uv run python -m evals.suites.web_expert \
  --dataset-name=nimble-web-expert-production \
  --runtime claude --max-items 50

# Codex
uv run python -m evals.suites.web_expert \
  --dataset-name=nimble-web-expert-production \
  --runtime codex --max-items 50

# Extraction Templates only
uv run python -m evals.suites.web_expert \
  --dataset-name=nimble-web-expert-production \
  --tag extraction-templates --runtime both

# Full set + regression gate
uv run python -m evals.suites.web_expert \
  --dataset-name=nimble-web-expert-production \
  --runtime both --check-regression
```

Results/traces land under `~/.nimble/skills-evals/` (not the repo): `results/`, `traces/`.

## Langfuse traces

Each experiment item gets a real observation tree (not a flat JSON blob):

1. **Conversion (default)** — Claude `stream-json` / Codex JSONL → generations +
   tool spans with real input/output (`evals.commons.langfuse_payload`).
2. **Claude OTEL** — off by default (`EVAL_CLAUDE_OTEL=0`). Native OTEL spans
   redact prompts/tool bodies unless content gates are set, which looks empty in
   Langfuse. Set `EVAL_CLAUDE_OTEL=1` to also export OTEL with content gates on
   ([docs](https://langfuse.com/integrations/developer-tools/claude-code)).
3. **Codex plugin** — sets `TRACE_TO_LANGFUSE=true` for the official Stop-hook
   plugin ([docs](https://langfuse.com/integrations/developer-tools/codex));
   evals still convert JSONL directly because `codex exec --ignore-user-config`
   skips plugins.

```bash
cd evals && uv sync --extra dev
uv run pytest tests/test_cli_to_langfuse.py tests/test_nimble_cmd.py -q
```

Unit fixtures under `tests/` must use synthetic stand-ins only (`example.com`,
`acme.com`, `WidgetCo Holdings, LLC`, …). Never copy prompts, legal entity
names, or domains from `nimble-web-expert-production` or from
`~/.nimble/skills-evals/traces/` into the repo — bashlex/payload tests only
need shell shape and JSONL structure.

## Metrics

| Metric | Meaning |
|---|---|
| `first_turn_action` | Headline — dialogue act vs `clarification_policy` (assistant parity) |
| `skill_selection` | `nimble-web-expert` triggered when expected |
| `tool_selection` | Soft match on `nimble search\|extract\|map\|crawl\|agent` |
| `forbidden_tools` | No WSA-create style commands when gold forbids them |
| `response_non_empty` | Final response longer than 10 chars (not an LLM judge) |

Gold is remapped at runtime from assistant `expected_output` (see `evals/commons/gold.py`). Extraction Templates are first-class.

## Related

- Lightweight routing-only eval (no Nimble credits): `python3 scripts/run-routing-eval.py`

## What stays private

| Location | Contents |
|---|---|
| Langfuse project | Production prompts, experiment traces, scores |
| `evals/.env` | API keys (gitignored) |
| `~/.nimble/skills-evals/` | Local results + CLI traces |

Public git may reference dataset items by bare `prod-####` id only — never by
prompt text or real company/domain strings.

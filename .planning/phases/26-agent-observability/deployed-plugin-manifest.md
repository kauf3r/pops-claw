# Observability-Hooks Plugin - Deployed Files

**Deployed to:** EC2 (100.72.143.9)
**Plugin path:** `~/.openclaw/plugins/observability-hooks/`
**DB path:** `/home/ubuntu/clawd/agents/main/observability.db`

## Files Created

| File | Purpose |
|------|---------|
| `package.json` | npm package (@openclaw/observability-hooks v1.0.0, ESM, tsc build) |
| `openclaw.plugin.json` | Plugin manifest (id: observability-hooks) |
| `tsconfig.json` | TypeScript config (ES2022, NodeNext, strict) |
| `src/index.ts` | Plugin entry: registers llm_output + agent_end hooks |
| `src/db.ts` | SQLite via child_process.execSync -- schema, INSERT, cleanup |
| `src/pricing.ts` | Model cost map (Haiku/Sonnet/Opus) + estimateCost() |
| `dist/*.js` | Compiled output (tsc) |

## Schema

### llm_calls
`id, agent_id, session_key, model, provider, input_tokens, output_tokens, cache_read_tokens, cache_write_tokens, estimated_cost_usd, created_at`

### agent_runs
`id, agent_id, session_key, success, error, duration_ms, created_at`

### Indexes
- `idx_llm_agent_time` (agent_id, created_at)
- `idx_llm_model` (model)
- `idx_runs_agent_time` (agent_id, created_at)
- `idx_runs_errors` (agent_id, success)

## Config Changes (openclaw.json)

- `plugins.load.paths`: added `/home/ubuntu/.openclaw/plugins/observability-hooks`
- `plugins.entries.observability-hooks`: `{ "enabled": true }`
- `plugins.installs.observability-hooks`: source=path, version=1.0.0
- `agents.defaults.sandbox.docker.binds`: added `observability.db:/workspace/observability.db:ro`

## Verification (2026-02-18)

- Gateway: active (running)
- llm_calls: 1 row (heartbeat-main-15m, claude-sonnet-4-5, $0.004185)
- agent_runs: 1 row (main, success=1, duration=9295ms)
- Hooks firing on every LLM call and agent run

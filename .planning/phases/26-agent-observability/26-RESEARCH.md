# Phase 26: Agent Observability - Research

**Researched:** 2026-02-18
**Domain:** OpenClaw plugin hooks, LLM usage telemetry, SQLite metrics storage
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Track per-agent token usage (input + output), model distribution (Haiku/Sonnet/Opus), and turn counts for the last 24 hours
- Include estimated cost per agent -- map tokens x model pricing to rough daily dollar cost
- Track error count + most recent error message per agent (not full error log)
- Track rate limit proximity -- monitor rate limit headers from API responses, flag in briefing when approaching thresholds (>80% of limit)
- Track average latency (response time) per agent over 24h
- Use 7-day rolling average as baseline per agent
- Warning flag at 2x rolling average, critical flag at 4x or on repeated errors
- Two severity levels in briefing: warning and critical (critical highlighted differently)
- Flag zero activity -- if an agent that ran every day in the last 7 days has zero activity, surface as a warning
- System is new, no baseline data exists yet -- first week of data collection will establish rolling averages before anomaly detection activates

### Claude's Discretion
- Briefing format and presentation style (follow existing morning briefing patterns)
- Agent granularity -- per-agent totals for all 7 agents, with per-cron breakdown where it adds clarity
- Storage mechanism -- where hook data lands, retention period, DB choice
- Hook implementation details -- which OpenClaw hook events to use, payload structure
- How to handle the cold-start period before 7 days of data exist

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| OBS-01 | `llm_input`/`llm_output` hook payloads configured for agent monitoring | Plugin hook API verified: `llm_input` and `llm_output` are plugin-level events in the `PluginHookHandlerMap`. Must build a plugin (not a HOOK.md discovery hook) to listen to these events. Type definitions confirmed in plugin SDK. |
| OBS-02 | Agent activity summary (token usage, model distribution, turn counts) available to Bob | `llm_output` event provides `usage: { input, output, cacheRead, cacheWrite, total }`, `model`, `provider`, `runId`, `sessionId`. Context provides `agentId`, `sessionKey`. All needed fields are present. Store in SQLite, query from workspace. |
| OBS-03 | Morning briefing includes agent observability section (anomalous usage, errors, rate limit proximity) | Morning briefing is cron `863587f3`, isolated session, model sonnet, delivers to #popsclaw. Add a new section to the cron payload. Bob reads observability.db from /workspace/ and formats the section. Anomaly logic uses SQL over 7-day rolling averages. |
</phase_requirements>

## Summary

OpenClaw v2026.2.17 provides a rich plugin hook system with `llm_input` and `llm_output` events that fire on every LLM call across all agents. These events carry exactly the data needed: token usage (input/output/cache), model identifier, provider, agent ID, session key, and run ID. The `agent_end` event additionally provides `durationMs` for latency tracking and `error` for error tracking.

The critical architectural decision is that `llm_input`/`llm_output` are **plugin-level hooks**, not discovery-based hooks. Discovery-based hooks (HOOK.md + handler.ts in `~/.openclaw/hooks/`) only support command and bootstrap events. To listen to LLM events, we must build an OpenClaw **plugin** -- a small npm package with `openclaw.plugin.json`, a `register(api)` function, and `api.on('llm_output', ...)` / `api.on('agent_end', ...)` handlers. SecureClaw provides a proven reference implementation of this pattern already running on this instance.

**Primary recommendation:** Build a lightweight OpenClaw plugin (`observability-hooks`) that listens to `llm_output` and `agent_end` events, writes metrics to a SQLite database (`observability.db`), and bind-mount that DB into Bob's sandbox at `/workspace/observability.db`. Add a new section to the morning briefing cron that queries this database with SQL. The plugin runs inside the gateway process (host-level, not sandbox), so it has direct filesystem access for writing.

## Standard Stack

### Core

| Component | Version | Purpose | Why Standard |
|-----------|---------|---------|--------------|
| OpenClaw Plugin API | v2026.2.17 | Hook registration for `llm_output`, `agent_end` | Only way to listen to LLM-level events; HOOK.md discovery cannot access these |
| SQLite (better-sqlite3 or node:fs) | Built-in | Metrics storage | Already used for health.db, email.db, coordination.db -- proven pattern on this instance |
| `api.on()` | Plugin SDK | Event handler registration | Standard plugin pattern, used by SecureClaw |

### Supporting

| Component | Version | Purpose | When to Use |
|-----------|---------|---------|-------------|
| Cron JSONL logs | Existing | Historical cron run data | Already captures per-run usage (input_tokens, output_tokens, model, provider, durationMs) in `~/.openclaw/cron/runs/*.jsonl` -- can backfill initial baseline |
| `agent_end` event | Plugin SDK | Latency + error tracking | Fires after each agent run with `durationMs` and `error` fields |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom plugin | HOOK.md discovery hook | Discovery hooks cannot listen to `llm_input`/`llm_output`/`agent_end` events -- not viable |
| SQLite | JSONL append-only log | JSONL is simpler to write but requires scanning entire file for aggregation queries -- SQLite enables rolling averages via SQL |
| New DB file | Extend coordination.db | coordination.db is bind-mounted as rw, could add tables. But observability is a distinct concern -- separate DB is cleaner and avoids coupling |

## Architecture Patterns

### Recommended Project Structure

```
~/.openclaw/plugins/observability-hooks/
  package.json              # npm package with openclaw peer dep
  openclaw.plugin.json      # Plugin manifest (id, name, configSchema)
  src/
    index.ts                # register(api) -- hooks llm_output, agent_end
    db.ts                   # SQLite init, write, query helpers
    pricing.ts              # Model -> $/token mapping
  dist/                     # Compiled JS (tsc)
```

### Pattern 1: Plugin Hook Registration

**What:** Register handlers for `llm_output` and `agent_end` events via the plugin API.
**When to use:** Any time you need to observe LLM calls or agent lifecycle.
**Confidence:** HIGH -- verified from SecureClaw source and plugin SDK type definitions.

```typescript
// Source: SecureClaw src/index.ts + plugin SDK types.d.ts
export default {
  id: 'observability-hooks',
  name: 'Agent Observability',
  version: '1.0.0',

  register(api) {
    // llm_output fires after each LLM response -- carries usage data
    api.on('llm_output', async (event, ctx) => {
      // event: { runId, sessionId, provider, model, assistantTexts, lastAssistant, usage }
      // ctx: { agentId, sessionKey, sessionId, workspaceDir }
      // usage: { input, output, cacheRead, cacheWrite, total }
      await db.recordLlmCall({
        agentId: ctx.agentId,
        sessionKey: ctx.sessionKey,
        model: event.model,
        provider: event.provider,
        inputTokens: event.usage?.input ?? 0,
        outputTokens: event.usage?.output ?? 0,
        cacheReadTokens: event.usage?.cacheRead ?? 0,
        cacheWriteTokens: event.usage?.cacheWrite ?? 0,
        timestamp: new Date().toISOString(),
      });
    });

    // agent_end fires after each agent run -- carries duration and error
    api.on('agent_end', async (event, ctx) => {
      // event: { messages, success, error, durationMs }
      await db.recordAgentRun({
        agentId: ctx.agentId,
        sessionKey: ctx.sessionKey,
        success: event.success,
        error: event.error,
        durationMs: event.durationMs,
        timestamp: new Date().toISOString(),
      });
    });
  }
};
```

### Pattern 2: SQLite Schema for Observability

**What:** Two tables -- `llm_calls` for per-call token data, `agent_runs` for per-run latency/errors.
**When to use:** All metrics storage.

```sql
-- llm_calls: one row per LLM call (llm_output event)
CREATE TABLE IF NOT EXISTS llm_calls (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  agent_id TEXT NOT NULL,
  session_key TEXT,
  model TEXT NOT NULL,
  provider TEXT NOT NULL,
  input_tokens INTEGER DEFAULT 0,
  output_tokens INTEGER DEFAULT 0,
  cache_read_tokens INTEGER DEFAULT 0,
  cache_write_tokens INTEGER DEFAULT 0,
  estimated_cost_usd REAL DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_llm_agent_time ON llm_calls(agent_id, created_at);
CREATE INDEX idx_llm_model ON llm_calls(model);

-- agent_runs: one row per agent run (agent_end event)
CREATE TABLE IF NOT EXISTS agent_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  agent_id TEXT NOT NULL,
  session_key TEXT,
  success INTEGER DEFAULT 1,
  error TEXT,
  duration_ms INTEGER,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_runs_agent_time ON agent_runs(agent_id, created_at);
CREATE INDEX idx_runs_errors ON agent_runs(agent_id, success);
```

### Pattern 3: Morning Briefing Integration

**What:** Add an "Agent Observability" section to the morning briefing cron payload.
**When to use:** OBS-03.

The morning briefing cron (`863587f3`) already has 9 sections. Add section 10 that queries `/workspace/observability.db` using sqlite3 CLI from the sandbox. The observability.db file must be bind-mounted (read-only is sufficient for the briefing).

```
## 10. Agent Observability (OBS-03)
Query /workspace/observability.db for the following:

1. **24h Summary per Agent:**
   SELECT agent_id,
     COUNT(*) as turns,
     SUM(input_tokens) as total_input,
     SUM(output_tokens) as total_output,
     ROUND(SUM(estimated_cost_usd), 4) as cost_usd,
     GROUP_CONCAT(DISTINCT model) as models
   FROM llm_calls
   WHERE created_at >= datetime('now', '-24 hours')
   GROUP BY agent_id ORDER BY cost_usd DESC;

2. **Anomaly Detection:**
   [7-day rolling average comparison SQL]

3. **Errors (last 24h):**
   SELECT agent_id, COUNT(*) as error_count,
     (SELECT error FROM agent_runs r2
      WHERE r2.agent_id = r.agent_id AND r2.success = 0
      ORDER BY r2.created_at DESC LIMIT 1) as last_error
   FROM agent_runs r
   WHERE success = 0 AND created_at >= datetime('now', '-24 hours')
   GROUP BY agent_id;

4. **Latency:**
   SELECT agent_id, ROUND(AVG(duration_ms)/1000.0, 1) as avg_seconds
   FROM agent_runs
   WHERE created_at >= datetime('now', '-24 hours')
   GROUP BY agent_id;

Format with warning/critical indicators. If no data yet (cold start), say
"Observability data collecting -- baselines will be available after 7 days."
```

### Anti-Patterns to Avoid

- **Writing to workspace from plugin directly:** The plugin runs in the gateway process on the host, NOT inside the Docker sandbox. Write to a host path, then bind-mount into the sandbox.
- **Storing metrics in JSONL:** JSONL requires full-file scans for aggregation. SQLite supports indexed queries and rolling averages via SQL window functions.
- **Blocking the hook handler:** `llm_output` and `agent_end` are void hooks that run in parallel. Keep handlers fast -- SQLite INSERT is <1ms. Do NOT do network calls or heavy computation in the handler.
- **Listening to `llm_input` for usage data:** `llm_input` fires BEFORE the LLM call and has no usage data. Use `llm_output` which fires AFTER and includes the `usage` object.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Token cost calculation | Real-time API pricing lookup | Hardcoded pricing map | Pricing changes infrequently; hardcoded map avoids network calls in hot path |
| Rolling average calculation | Custom moving average in JS | SQL window functions | `AVG() OVER (PARTITION BY agent_id ORDER BY date ROWS 6 PRECEDING)` is exact and efficient |
| Hook event interception | Custom event emitter patching | `api.on()` plugin API | Plugin API is the supported way; patching internals will break on update |
| Rate limit monitoring | Custom header parsing | Parse from `llm_output` or cron run metadata | Rate limit data flows through existing cron run JSONL (see `usage` field). For real-time proximity, the gateway already tracks `rate_limit.primary_window.used_percent` internally but does NOT expose it to hooks. |
| Agent ID resolution | Session key parsing | `ctx.agentId` from hook context | Plugin hook context already resolves agent ID |

**Key insight:** The `llm_output` hook does NOT include rate limit headers. Rate limit proximity tracking requires either (a) parsing gateway logs, (b) adding a `before_prompt_build` hook to check the Anthropic rate limit status endpoint, or (c) approximating from token volume vs known plan limits. Recommend option (c) for simplicity -- estimate proximity from cumulative token usage against known tier limits.

## Common Pitfalls

### Pitfall 1: Plugin vs Discovery Hook Confusion
**What goes wrong:** Creating a HOOK.md in `~/.openclaw/hooks/` with `events: ["llm_output"]` -- it will never fire.
**Why it happens:** The hooks documentation lists `llm_input`/`llm_output` as available event types, but these are plugin-level events only. Discovery-based hooks only support `command`, `command:new`, `command:reset`, `command:stop`, `agent:bootstrap`, `gateway:startup`.
**How to avoid:** Build a proper plugin with `openclaw.plugin.json` + `register(api)` + `api.on('llm_output', ...)`.
**Warning signs:** Hook shows as "ready" in `openclaw hooks list` but never fires.

### Pitfall 2: Writing DB Inside Docker Sandbox
**What goes wrong:** Plugin tries to write to `/workspace/observability.db` -- but plugin runs on host, not in sandbox.
**Why it happens:** Confusion between host paths and sandbox paths.
**How to avoid:** Write to a host path (e.g., `~/clawd/agents/main/observability.db` or `~/clawd/observability.db`), then add a bind mount in `openclaw.json` to make it available as `/workspace/observability.db` inside the sandbox.
**Warning signs:** FileNotFoundError or permission denied in plugin logs.

### Pitfall 3: Disk Space on 5.6GB Free
**What goes wrong:** Unbounded metrics accumulation fills the 29GB EBS volume.
**Why it happens:** EC2 is at 81% usage (5.6GB free). Each LLM call row is ~200 bytes. With ~20 crons running at various frequencies plus DM sessions, expect 500-2000 rows/day = ~400KB/day = ~12MB/month. Manageable, but needs retention policy.
**How to avoid:** Add a retention policy: DELETE rows older than 90 days. Run cleanup weekly. 90 days * 2000 rows/day * 200 bytes = ~36MB max.
**Warning signs:** `df -h` showing >90% usage.

### Pitfall 4: Gateway Restart Needed After Plugin Install
**What goes wrong:** Plugin is installed but hooks don't fire.
**Why it happens:** Plugins are loaded at gateway startup. New plugins require a restart.
**How to avoid:** Plan for a gateway restart as a phase step. Use `systemctl --user restart openclaw-gateway.service`.
**Warning signs:** `openclaw hooks list` doesn't show the new plugin hooks.

### Pitfall 5: Agent ID Null for Some Events
**What goes wrong:** `ctx.agentId` is `undefined` for certain session types.
**Why it happens:** The `agentId` in `PluginHookAgentContext` is optional. Some edge cases (probe sessions, ephemeral runs) may not have it.
**How to avoid:** Fall back to parsing `ctx.sessionKey` -- format is `agent:<agentId>:<rest>`. Always handle null gracefully.
**Warning signs:** Rows in observability.db with NULL agent_id.

### Pitfall 6: Cold Start Period for Anomaly Detection
**What goes wrong:** Anomaly detection fires false alarms in the first week because there's no baseline.
**Why it happens:** 7-day rolling average is zero or near-zero with insufficient data.
**How to avoid:** Check row count per agent before running anomaly logic. If < 7 days of data, show "Collecting baseline (day N/7)" instead of anomaly flags.
**Warning signs:** Every agent shows as "critical" in the first briefing.

## Code Examples

### Plugin package.json

```json
{
  "name": "@openclaw/observability-hooks",
  "version": "1.0.0",
  "description": "LLM usage tracking and anomaly detection for agent observability",
  "main": "dist/index.js",
  "type": "module",
  "scripts": {
    "build": "tsc"
  },
  "peerDependencies": {
    "openclaw": "^2026.2.17"
  },
  "openclaw": {
    "type": "extension",
    "extensions": ["./dist/index.js"]
  }
}
```

### Plugin manifest (openclaw.plugin.json)

```json
{
  "id": "observability-hooks",
  "name": "Agent Observability",
  "description": "Tracks LLM usage, latency, and errors across all agents",
  "version": "1.0.0"
}
```

### Cost Estimation Map

```typescript
// Source: https://platform.claude.com/docs/en/about-claude/pricing (Feb 2026)
const COST_PER_MILLION: Record<string, { input: number; output: number }> = {
  'claude-haiku-4-5':  { input: 1.00, output: 5.00 },
  'claude-sonnet-4-5': { input: 3.00, output: 15.00 },
  'claude-opus-4-5':   { input: 5.00, output: 25.00 },
};

function estimateCost(model: string, inputTokens: number, outputTokens: number): number {
  // Normalize model name -- strip provider prefix if present
  const key = model.replace(/^anthropic\//, '');
  const rates = COST_PER_MILLION[key];
  if (!rates) return 0; // Unknown model
  return (inputTokens * rates.input + outputTokens * rates.output) / 1_000_000;
}
```

### Anomaly Detection SQL

```sql
-- 7-day rolling average tokens per agent
WITH daily AS (
  SELECT agent_id,
    DATE(created_at) as day,
    SUM(input_tokens + output_tokens) as daily_tokens,
    COUNT(*) as daily_turns
  FROM llm_calls
  WHERE created_at >= datetime('now', '-8 days')
  GROUP BY agent_id, DATE(created_at)
),
rolling AS (
  SELECT agent_id,
    AVG(daily_tokens) as avg_tokens_7d,
    AVG(daily_turns) as avg_turns_7d,
    COUNT(*) as days_with_data
  FROM daily
  WHERE day < DATE('now')  -- exclude today (incomplete)
  GROUP BY agent_id
),
today AS (
  SELECT agent_id,
    SUM(input_tokens + output_tokens) as today_tokens,
    COUNT(*) as today_turns
  FROM llm_calls
  WHERE created_at >= datetime('now', '-24 hours')
  GROUP BY agent_id
)
SELECT
  COALESCE(t.agent_id, r.agent_id) as agent_id,
  t.today_tokens,
  t.today_turns,
  r.avg_tokens_7d,
  r.avg_turns_7d,
  r.days_with_data,
  CASE
    WHEN r.days_with_data < 7 THEN 'collecting'
    WHEN t.today_tokens IS NULL AND r.avg_turns_7d > 0 THEN 'zero_activity'
    WHEN t.today_tokens > r.avg_tokens_7d * 4 THEN 'critical'
    WHEN t.today_tokens > r.avg_tokens_7d * 2 THEN 'warning'
    ELSE 'ok'
  END as status
FROM rolling r
LEFT JOIN today t ON t.agent_id = r.agent_id;
```

### Bind Mount Addition to openclaw.json

```json
{
  "agents": {
    "defaults": {
      "sandbox": {
        "docker": {
          "binds": [
            "... existing binds ...",
            "/home/ubuntu/clawd/agents/main/observability.db:/workspace/observability.db:ro"
          ]
        }
      }
    }
  }
}
```

### Plugin Registration in openclaw.json

```json
{
  "plugins": {
    "load": {
      "paths": [
        "/home/ubuntu/.openclaw/plugins/secureclaw",
        "/home/ubuntu/.openclaw/plugins/observability-hooks"
      ]
    },
    "entries": {
      "observability-hooks": {
        "enabled": true
      }
    }
  }
}
```

## Verified Event Payloads (from Source)

### llm_output Event

Source: `reply-oSe13ewW.js` line 54096-54111, confirmed by `plugin-sdk/plugins/types.d.ts`

```typescript
type PluginHookLlmOutputEvent = {
  runId: string;          // Unique run identifier
  sessionId: string;      // Session identifier
  provider: string;       // e.g., "anthropic"
  model: string;          // e.g., "claude-sonnet-4-5"
  assistantTexts: string[];
  lastAssistant?: unknown;
  usage?: {
    input?: number;       // Input tokens consumed
    output?: number;      // Output tokens generated
    cacheRead?: number;   // Cache read tokens
    cacheWrite?: number;  // Cache write tokens
    total?: number;       // Total tokens (may include cache)
  };
};
```

Context:
```typescript
type PluginHookAgentContext = {
  agentId?: string;       // e.g., "main", "landos", "ops"
  sessionKey?: string;    // e.g., "agent:main:cron:863587f3:run:..."
  sessionId?: string;
  workspaceDir?: string;
  messageProvider?: string;
};
```

### agent_end Event

Source: `reply-oSe13ewW.js` line 54065-54077

```typescript
type PluginHookAgentEndEvent = {
  messages: unknown[];    // Final message list
  success: boolean;       // Whether the run completed without error
  error?: string;         // Error description if failed
  durationMs?: number;    // Total run duration in milliseconds
};
```

### Rate Limit Data

Source: `reply-oSe13ewW.js` lines with `rate_limit.primary_window`

The gateway internally tracks rate limit windows (`usedPercent`, `resetAt`) from the Anthropic API status endpoint. However, this data is NOT exposed via the `llm_output` hook event. It is used internally for account rotation and cooldown logic.

**Options for rate limit proximity:**
1. **(Recommended)** Estimate from cumulative token volume: track daily tokens against known Anthropic tier limits and calculate approximate proximity.
2. **(Complex)** Periodically call the Anthropic rate limit status API from the plugin at startup or on a timer. The gateway code shows the endpoint returns `{ rate_limit: { primary_window: { used_percent, limit_window_seconds, reset_at }, secondary_window: {...} } }`.
3. **(Not viable)** Parse from hook events -- the data simply isn't there.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Discovery hooks (HOOK.md) | Plugin hook API | v2026.2.x | `llm_input`/`llm_output` only available via plugin API |
| Single hook handler config | Multiple handler system with priority | v2026.2.x | Handlers run in parallel for void hooks, sequential for modifying hooks |
| No LLM hooks | Full LLM lifecycle hooks | v2026.2.17 | `llm_input`, `llm_output`, `agent_end` now available |

## Existing Data Sources

### Cron Run JSONL Logs

Location: `~/.openclaw/cron/runs/<jobId>.jsonl`

Already captures per-cron-run: `model`, `provider`, `usage.input_tokens`, `usage.output_tokens`, `usage.total_tokens`, `durationMs`, `status`. This provides historical data for backfilling initial baselines.

**Limitation:** Only captures cron runs, not DM sessions or ad-hoc interactions. The `usage` field is only present for isolated sessions (not main-session system events). Heartbeats (main session) show no usage data.

### The 7 Agents

| ID | Name | Primary Crons | Expected Activity |
|----|------|---------------|-------------------|
| main | Bob | morning-briefing, evening-recap, anomaly-check, daily-heartbeat, heartbeat-main-15m, email-catchup, meeting-prep-scan, airspace-email-monitor | Highest -- multiple crons + DM sessions |
| landos | Scout | heartbeat-landos-15m | Moderate -- heartbeats + channel messages |
| rangeos | Vector | heartbeat-rangeos-15m, topic-research | Moderate -- heartbeats + research |
| ops | Sentinel | heartbeat-ops-15m, daily-standup, stuck-check, pipeline-report | Moderate -- operational crons |
| quill | Quill | writing-check | Low -- weekly writing tasks |
| sage | Sage | review-check | Low -- review tasks |
| ezra | Ezra | publish-check | Low -- publish tasks |

### Anthropic API Pricing (Feb 2026)

| Model | Input ($/M tokens) | Output ($/M tokens) |
|-------|--------------------|--------------------|
| claude-haiku-4-5 | $1.00 | $5.00 |
| claude-sonnet-4-5 | $3.00 | $15.00 |
| claude-opus-4-5 | $5.00 | $25.00 |

Cache pricing: write = 1.25x input, read = 0.1x input. For rough cost estimates, cache tokens can be ignored initially or counted at input rate.

## Open Questions

1. **Rate limit proximity -- implementation path**
   - What we know: The `llm_output` event does NOT include rate limit headers. The gateway internally parses `rate_limit.primary_window.used_percent` from the Anthropic API but does not expose it to hooks.
   - What's unclear: Whether the Anthropic rate limit status endpoint can be called from a plugin without interfering with the gateway's own rate limit management.
   - Recommendation: Start with option 1 (estimate from token volume vs tier limits). If the user upgrades tiers or wants exact proximity, add periodic API polling later. Flag in the briefing as "estimated" during phase 26. **This is a degraded implementation of the locked decision -- surface to user during planning.**

2. **SQLite from plugin process**
   - What we know: The gateway process runs Node.js on the host. `better-sqlite3` is available if installed. Alternatively, can use `child_process.execSync('sqlite3 ...')` since sqlite3 is on the host.
   - What's unclear: Whether the OpenClaw Node.js process has `better-sqlite3` as a dependency or if we need to install it.
   - Recommendation: Use `child_process.execSync` to call the sqlite3 CLI for writes (simple, no dependency). Or install `better-sqlite3` as a plugin dependency. Check if `sqlite3` binary exists on host (likely yes since it's used for other DBs).

3. **Backfilling baseline from existing cron JSONL**
   - What we know: `~/.openclaw/cron/runs/*.jsonl` contains historical run data with usage for isolated crons. 2.2MB total.
   - What's unclear: How many days of history exist and whether it covers all 7 agents.
   - Recommendation: Write a one-time backfill script that parses existing JSONL files and populates observability.db with historical data. This jumpstarts the 7-day rolling average instead of waiting a full week.

## Implementation Approach (Recommendations for Planner)

### Plan 1: Build the Plugin (OBS-01)
1. Create plugin directory structure at `~/.openclaw/plugins/observability-hooks/`
2. Write `package.json`, `openclaw.plugin.json`, `tsconfig.json`
3. Implement `src/index.ts` with `llm_output` and `agent_end` handlers
4. Implement `src/db.ts` with SQLite schema creation and insert functions
5. Implement `src/pricing.ts` with cost estimation
6. Compile with tsc
7. Register plugin in `openclaw.json` (plugins.load.paths + plugins.entries)
8. Add bind mount for observability.db
9. Restart gateway
10. Verify hooks firing via gateway logs

### Plan 2: Morning Briefing Integration (OBS-03)
1. Add section 10 to morning briefing cron payload
2. SQL queries for: 24h summary, anomaly detection, errors, latency
3. Cold-start handling: show "collecting baseline" for first 7 days
4. Two severity levels: warning (bold) and critical (bold + indicator)

### Plan 3: Baseline Backfill + Validation
1. Parse existing cron JSONL files for historical usage data
2. Populate observability.db with backfilled records
3. Run a manual test: trigger one agent, verify row appears in DB
4. Query anomaly detection SQL to validate logic
5. Add data retention cleanup (DELETE WHERE created_at < datetime('now', '-90 days'))

## Sources

### Primary (HIGH confidence)
- OpenClaw plugin SDK type definitions: `~/.npm-global/lib/node_modules/openclaw/dist/plugin-sdk/plugins/types.d.ts` -- `PluginHookLlmOutputEvent`, `PluginHookAgentEndEvent`, `PluginHookAgentContext`
- OpenClaw source: `reply-oSe13ewW.js` lines 53986-54111 -- `llm_input` and `llm_output` hook invocation with payload structure
- OpenClaw hooks documentation: `~/.openclaw/plugins/secureclaw/node_modules/openclaw/docs/hooks.md` -- hook discovery, HOOK.md format, event types
- SecureClaw plugin source: `~/.openclaw/plugins/secureclaw/src/index.ts` -- `api.on()` registration pattern
- OpenClaw config: `~/.openclaw/openclaw.json` -- current plugin setup, agent list, bind mounts

### Secondary (MEDIUM confidence)
- Anthropic pricing: [platform.claude.com/docs/en/about-claude/pricing](https://platform.claude.com/docs/en/about-claude/pricing) -- current per-token costs
- Cron run JSONL: `~/.openclaw/cron/runs/*.jsonl` -- historical usage data structure verified from actual entries

### Tertiary (LOW confidence)
- Rate limit implementation: Inferred from minified source code grep (`rate_limit.primary_window`) -- may have additional fields or endpoints not visible in minified output

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- plugin SDK types verified, SecureClaw provides working reference implementation
- Architecture: HIGH -- event payloads confirmed from source code, SQLite pattern proven on this instance
- Pitfalls: HIGH -- discovery vs plugin hook distinction verified empirically, disk space measured, cold-start handling explicit in requirements

**Research date:** 2026-02-18
**Valid until:** 2026-03-18 (stable -- plugin API unlikely to change within minor versions)

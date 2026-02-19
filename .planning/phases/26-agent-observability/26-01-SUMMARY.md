---
phase: 26-agent-observability
plan: 01
subsystem: infra
tags: [openclaw-plugin, sqlite, observability, llm-hooks, cost-tracking]

# Dependency graph
requires:
  - phase: 24-security-hardening
    provides: SecureClaw plugin pattern (reference implementation for plugin API)
provides:
  - observability-hooks plugin capturing llm_output and agent_end events
  - observability.db with llm_calls and agent_runs tables
  - per-call cost estimation (Haiku/Sonnet/Opus pricing)
  - bind mount making observability.db readable from sandbox at /workspace/observability.db
affects: [26-02 morning briefing integration, future cost monitoring]

# Tech tracking
tech-stack:
  added: [observability-hooks plugin v1.0.0]
  patterns: [plugin hook handlers for llm_output/agent_end, SQLite via child_process.execSync, model cost estimation]

key-files:
  created:
    - ~/.openclaw/plugins/observability-hooks/src/index.ts
    - ~/.openclaw/plugins/observability-hooks/src/db.ts
    - ~/.openclaw/plugins/observability-hooks/src/pricing.ts
    - ~/clawd/agents/main/observability.db
  modified:
    - ~/.openclaw/openclaw.json

key-decisions:
  - "Used child_process.execSync for SQLite writes (no npm dependency needed, sqlite3 CLI available on host)"
  - "Plugin manifest requires configSchema field (discovered during gateway startup validation)"
  - "Plugin installs entry needed in openclaw.json alongside load.paths and entries (matching SecureClaw pattern)"

patterns-established:
  - "OpenClaw plugin manifest: must include configSchema (even empty object) or gateway rejects config"
  - "Plugin registration: requires load.paths + entries + installs entries in openclaw.json"

requirements-completed: [OBS-01, OBS-02]

# Metrics
duration: 8min
completed: 2026-02-18
---

# Phase 26 Plan 01: Observability Hooks Summary

**OpenClaw plugin capturing per-call LLM usage (tokens, model, cost) and agent lifecycle (duration, errors) to SQLite, verified with live heartbeat data**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-18T23:49:51Z
- **Completed:** 2026-02-18T23:57:40Z
- **Tasks:** 2
- **Files modified:** 8 (6 plugin source + 1 config + 1 database)

## Accomplishments
- Built observability-hooks plugin with llm_output and agent_end hook handlers
- SQLite database (observability.db) with llm_calls and agent_runs tables, 4 indexes for query performance
- Model cost estimation covering claude-haiku-4-5, claude-sonnet-4-5, claude-opus-4-5 with fuzzy matching
- Plugin registered, gateway stable, hooks verified firing with real heartbeat cron data (1 LLM call, 1 agent run)
- Bind mount provides read-only sandbox access at /workspace/observability.db

## Task Commits

Each task was committed atomically:

1. **Task 1: Create observability-hooks plugin source files** - `8889d18` (feat)
2. **Task 2: Register plugin, add bind mount, restart gateway, verify hooks** - `35b51d4` (feat)

**Plan metadata:** `c5d8f9b` (docs: complete plan)

## Files Created/Modified
- `~/.openclaw/plugins/observability-hooks/package.json` - npm package definition (ESM, tsc build)
- `~/.openclaw/plugins/observability-hooks/openclaw.plugin.json` - Plugin manifest with configSchema
- `~/.openclaw/plugins/observability-hooks/tsconfig.json` - TypeScript config (ES2022, NodeNext)
- `~/.openclaw/plugins/observability-hooks/src/index.ts` - Hook handlers for llm_output and agent_end
- `~/.openclaw/plugins/observability-hooks/src/db.ts` - SQLite schema, INSERT functions, 90-day cleanup
- `~/.openclaw/plugins/observability-hooks/src/pricing.ts` - Model cost map with fuzzy name resolution
- `~/.openclaw/openclaw.json` - Added plugin paths, entries, installs, bind mount
- `~/clawd/agents/main/observability.db` - SQLite database with llm_calls + agent_runs tables

## Decisions Made
- Used `child_process.execSync('sqlite3 ...')` for database writes -- no npm runtime dependencies needed, proven pattern on this host
- Added `configSchema` to plugin manifest -- OpenClaw v2026.2.17 requires it (gateway crashes without it)
- Added `plugins.installs` entry alongside `load.paths` and `entries` -- all three are needed for plugin discovery
- Database at `~/clawd/agents/main/observability.db` alongside email.db -- consistent bind-mount location

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed missing configSchema in plugin manifest**
- **Found during:** Task 2 (gateway restart)
- **Issue:** Gateway crashed with "plugin manifest requires configSchema" -- OpenClaw validates plugin manifests at startup
- **Fix:** Added configSchema with enabled (boolean) and retentionDays (number) properties
- **Files modified:** ~/.openclaw/plugins/observability-hooks/openclaw.plugin.json
- **Verification:** Gateway starts successfully after fix
- **Committed in:** 35b51d4 (Task 2 commit)

**2. [Rule 1 - Bug] Fixed missing plugins.installs entry**
- **Found during:** Task 2 (gateway restart)
- **Issue:** Gateway reported "plugins.entries.observability-hooks: plugin not found" despite load.paths being set
- **Fix:** Added installs entry with source=path, matching SecureClaw's registration pattern
- **Files modified:** ~/.openclaw/openclaw.json
- **Verification:** Gateway loads plugin successfully, "[observability-hooks] Database initialized" in logs
- **Committed in:** 35b51d4 (Task 2 commit)

**3. [Rule 1 - Bug] Fixed shell-escaped exclamation mark in pricing.ts**
- **Found during:** Task 1 (TypeScript compilation)
- **Issue:** Heredoc over SSH escaped `!` to `\!` in `if (!key)`, causing TS compilation error
- **Fix:** Replaced `\!` with `!` via sed
- **Files modified:** ~/.openclaw/plugins/observability-hooks/src/pricing.ts
- **Verification:** TypeScript compiles without errors
- **Committed in:** 8889d18 (Task 1 commit)

---

**Total deviations:** 3 auto-fixed (3 bugs)
**Impact on plan:** All auto-fixes necessary for correct operation. No scope creep.

## Issues Encountered
- Shell heredoc escaping of `!` character required using SCP for complex TypeScript files instead of inline heredocs
- Gateway crash-restart loop during plugin manifest fix (resolved within 30 seconds, auto-restart caught it)

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- observability.db collecting data from all agent activity going forward
- Ready for Plan 02: morning briefing integration (query observability.db for 24h summary, anomalies, errors)
- Cold-start period: 7 days of data needed before anomaly detection baselines are meaningful
- Databases on instance: health.db, coordination.db, content.db, email.db, observability.db

## Self-Check: PASSED

- 26-01-SUMMARY.md: FOUND
- deployed-plugin-manifest.md: FOUND
- Commit 8889d18: FOUND
- Commit 35b51d4: FOUND

---
*Phase: 26-agent-observability*
*Completed: 2026-02-18*

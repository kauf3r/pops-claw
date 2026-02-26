---
phase: 42-cli-tools-dashboard
plan: 02
subsystem: api
tags: [nextjs, typescript, api-routes, cron, health-check, swr]

# Dependency graph
requires:
  - phase: 42-cli-tools-dashboard (plan 01)
    provides: tools-health.json cached on EC2 filesystem
provides:
  - GET /api/tools endpoint merging tools-health.json + jobs.json
  - POST /api/tools/refresh endpoint (fire-and-forget script trigger)
  - Shared TypeScript interfaces for tools health data (ToolsHealth, CliTool, PluginTool, ScriptTool, CronEntry, HealthStatus)
affects: [42-cli-tools-dashboard plan 03 (UI page)]

# Tech tracking
tech-stack:
  added: []
  patterns: [filesystem-json-cache-merge, fire-and-forget-spawn, typed-api-response]

key-files:
  created:
    - src/lib/types/tools.ts
    - src/app/api/tools/route.ts
    - src/app/api/tools/refresh/route.ts
  modified: []

key-decisions:
  - "Fixed jobs.json parsing to handle { version, jobs: [...] } wrapper (not plain array)"
  - "Cron health uses state.lastRunAtMs not empty lastRun field"
  - "Graceful degradation: empty cron array if jobs.json unreadable"

patterns-established:
  - "Typed API response: shared interfaces in src/lib/types/ imported by both API routes and future UI"
  - "Fire-and-forget spawn: detached child process with unref() for long-running scripts"

requirements-completed: [TOOLS-01]

# Metrics
duration: 5min
completed: 2026-02-26
---

# Phase 42 Plan 02: API Routes Summary

**TypeScript interfaces and two API routes for /tools page: GET merges tools-health.json + cron jobs.json, POST triggers health-check script fire-and-forget**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-26T19:09:18Z
- **Completed:** 2026-02-26T19:13:58Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Created shared TypeScript interfaces (ToolsHealth, CliTool, PluginTool, ScriptTool, CronEntry, HealthStatus) in src/lib/types/tools.ts
- GET /api/tools merges tools-health.json (cli/plugins/scripts) with jobs.json (cron section), computes health status per cron job
- POST /api/tools/refresh spawns health-check script detached and returns 202 immediately
- Verified: 5 CLI tools, 2 plugins, 3 scripts, 24 cron jobs returned; bd is red; 22/24 cron jobs have lastRunAt

## Task Commits

Each task was committed atomically:

1. **Task 1: Create TypeScript interfaces and GET /api/tools route** - `f1ab597` (feat)
2. **Task 2: Create POST /api/tools/refresh route, build, and verify endpoints** - `d4868c6` (feat)

## Files Created/Modified
- `src/lib/types/tools.ts` - Shared TypeScript interfaces for all tools health data
- `src/app/api/tools/route.ts` - GET endpoint merging tools-health.json + jobs.json with cron health computation
- `src/app/api/tools/refresh/route.ts` - POST endpoint spawning health-check script fire-and-forget (202)

## Decisions Made
- Fixed jobs.json parsing to handle `{ version, jobs: [...] }` wrapper instead of treating as plain array (plan assumed array, actual data has wrapper)
- Used `spawn` with `detached: true` + `unref()` for fire-and-forget (not `execFile` which would block)
- Cron health computed from `state.lastRunAtMs` per research findings (not empty `lastRun` field)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed jobs.json parsing for { version, jobs } wrapper**
- **Found during:** Task 1 (GET /api/tools route)
- **Issue:** Plan code treated jobs.json as a plain array (`const jobs: RawCronJob[] = JSON.parse(rawJobs)`), but actual jobs.json is `{ version: 1, jobs: [...] }`
- **Fix:** Changed to `const parsed = JSON.parse(rawJobs); const jobs: RawCronJob[] = parsed.jobs ?? parsed;` to handle both formats
- **Files modified:** src/app/api/tools/route.ts
- **Verification:** GET /api/tools returns 24 cron entries with correct data
- **Committed in:** f1ab597 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Essential for correctness. Without this fix, cron section would have been empty or errored.

## Issues Encountered
- `npx tsc --noEmit` without `--skipLibCheck` shows pre-existing Next.js type noise from node_modules. Using `--skipLibCheck` confirms our code compiles cleanly. This is a known Next.js 14 + TypeScript issue, not related to our changes.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- API routes are live and serving typed data at GET /api/tools and POST /api/tools/refresh
- Plan 03 (UI page) can build against these endpoints with useSWR("/api/tools")
- TypeScript interfaces are importable via `@/lib/types/tools`
- No blockers for Plan 03

---
*Phase: 42-cli-tools-dashboard*
*Completed: 2026-02-26*

---
phase: 30-dashboard-metrics
plan: 01
subsystem: api, dashboard
tags: [swr, better-sqlite3, next-api-routes, status-card, activity-feed, cron-parser]

# Dependency graph
requires:
  - phase: 29-02
    provides: getDb singleton factory, WAL read-only connections, db-paths registry, SWR installed
provides:
  - 4 query modules (agents, crons, metrics, activity) reading from SQLite + JSON
  - 4 API routes under /api/dashboard/* returning live subsystem data
  - SWR global config with 30s polling via SWRConfig in providers.tsx
  - StatusCard reusable component (headline + colored dot + detail)
  - Constants file with agent registry, email quotas, activity types
affects: [30-02-dashboard-page, 31-agent-board]

# Tech tracking
tech-stack:
  added: []
  patterns: [query-module-per-subsystem, cross-db-merge-in-js, force-dynamic-api-routes, global-swr-polling]

key-files:
  created:
    - src/lib/constants.ts
    - src/lib/queries/agents.ts
    - src/lib/queries/crons.ts
    - src/lib/queries/metrics.ts
    - src/lib/queries/activity.ts
    - src/app/api/dashboard/agents/route.ts
    - src/app/api/dashboard/crons/route.ts
    - src/app/api/dashboard/metrics/route.ts
    - src/app/api/dashboard/activity/route.ts
    - src/components/dashboard/status-card.tsx
  modified:
    - src/app/providers.tsx

key-decisions:
  - "Query modules per subsystem (not one mega route) for independent error handling and parallel SWR fetches"
  - "Activity feed merges coordination.db + observability.db + email.db in JS (no ATTACH -- read-only mode)"
  - "Agents with no data show as idle (not down) to avoid false alarms for sage/ezra"
  - "Cron success rate uses current snapshot (lastStatus=ok / total with status) since no historical logging exists"

patterns-established:
  - "Query module pattern: each file exports typed functions that handle null DBs gracefully"
  - "API route pattern: force-dynamic + try/catch with typed fallback response on error"
  - "StatusCard pattern: headline number + colored dot (ok/warn/error) + one-line detail"

requirements-completed: [DASH-01, DASH-02, DASH-03, PIPE-01, PIPE-02]

# Metrics
duration: 4min
completed: 2026-02-21
---

# Phase 30 Plan 01: Dashboard Data Layer Summary

**4 API routes serving live agent health, cron success, pipeline/email metrics, and cross-DB activity feed with SWR 30s global polling and reusable StatusCard component**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-21T07:09:14Z
- **Completed:** 2026-02-21T07:13:10Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments
- Built 4 query modules querying coordination.db, observability.db, email.db, content.db, and cron jobs.json with full null/empty DB handling
- Created 4 API routes returning live data: agents (4/7 alive), crons (20/20, 100% success), metrics (zeros expected), activity (119+ entries)
- Configured SWR globally with 30-second polling, error-aware fetcher, focus revalidation, and 5s dedup
- Built StatusCard component matching locked design: headline number, colored dot indicator, one-line detail

## Task Commits

Each task was committed atomically:

1. **Task 1: Create query modules and constants** - `98fcf26` (feat)
2. **Task 2: Create API routes, SWR config, and StatusCard** - `f8af6ba` (feat)

## Files Created/Modified
- `src/lib/constants.ts` - Agent registry (7 agents), email quotas, activity colors, shared types
- `src/lib/queries/agents.ts` - Cross-DB agent health from coordination + observability
- `src/lib/queries/crons.ts` - Cron summary from jobs.json with success rate calculation
- `src/lib/queries/metrics.ts` - Content pipeline counts + email metrics from SQLite
- `src/lib/queries/activity.ts` - Cross-DB activity feed merge with pagination (50/page)
- `src/app/api/dashboard/agents/route.ts` - Agent health endpoint
- `src/app/api/dashboard/crons/route.ts` - Cron summary endpoint
- `src/app/api/dashboard/metrics/route.ts` - Pipeline + email metrics endpoint
- `src/app/api/dashboard/activity/route.ts` - Paginated activity feed endpoint
- `src/app/providers.tsx` - SWRConfig with 30s polling, error-aware fetcher
- `src/components/dashboard/status-card.tsx` - Reusable status card with headline + dot + detail

## Decisions Made
- Query modules per subsystem (not one mega route) for independent error handling and parallel SWR fetches
- Activity feed merges coordination.db + observability.db + email.db in JS since better-sqlite3 read-only cannot ATTACH
- Agents with no data (sage, ezra) show as "idle" not "down" to avoid false alarms
- Cron success rate uses current snapshot (lastStatus=ok count / total with any status) since no historical logging exists

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required. All 4 API endpoints are live at http://100.72.143.9:3001/api/dashboard/*.

## Next Phase Readiness
- All 4 API routes return correctly shaped JSON, verified with curl
- StatusCard component ready for composition in Plan 02 dashboard page
- SWR global config active -- any `useSWR` hook in child components gets 30s polling automatically
- Plan 02 can now compose the dashboard UI purely from these building blocks

## Self-Check: PASSED

- 30-01-SUMMARY.md: FOUND
- Commit 98fcf26 (Task 1): FOUND on EC2
- Commit f8af6ba (Task 2): FOUND on EC2
- STATE.md updated: Phase 30, plan 02
- ROADMAP.md updated: Phase 30 shows 1/2 plans complete

---
*Phase: 30-dashboard-metrics*
*Completed: 2026-02-21*

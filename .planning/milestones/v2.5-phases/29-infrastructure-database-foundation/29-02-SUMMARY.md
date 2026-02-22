---
phase: 29-infrastructure-database-foundation
plan: 02
subsystem: database, infra
tags: [better-sqlite3, wal-mode, systemd, tailscale, ufw, shadcn-badge, swr, next-production]

# Dependency graph
requires:
  - phase: 29-01
    provides: Convex-free codebase, SWR, shadcn components, zinc palette, RelativeTime
provides:
  - Read-only WAL database connection layer for all 5 SQLite databases
  - DB status API endpoint (/api/db-status) returning connection state and row counts
  - Landing page with 5 database status cards (connected/not-initialized states)
  - Production systemd service (mission-control.service) with OOMScoreAdjust=500
  - Tailscale-direct access at http://100.72.143.9:3001 (no SSH tunnel)
  - UFW rule restricting port 3001 to Tailscale CGNAT range
affects: [30-dashboard-metrics, 31-agent-board, 32-visualization]

# Tech tracking
tech-stack:
  added: []
  patterns: [singleton-db-connection, wal-readonly, systemd-user-service, tailscale-direct-bind]

key-files:
  created:
    - src/lib/db-paths.ts
    - src/lib/db.ts
    - src/app/api/db-status/route.ts
    - src/components/dashboard/db-status-card.tsx
    - src/components/dashboard/system-status.tsx
    - ~/.config/systemd/user/mission-control.service
  modified:
    - src/app/page.tsx
    - src/app/layout.tsx
    - package.json

key-decisions:
  - "Bound Next.js to 0.0.0.0:3001 for direct Tailscale access instead of loopback with SSH tunnel"
  - "OOMScoreAdjust=500 on mission-control so gateway (-900) and Tailscale survive OOM events"
  - "Database connections opened read-only with WAL check and busy_timeout=5000 for concurrent tolerance"

patterns-established:
  - "DB singleton pattern: getDb(name) lazily opens and caches read-only connections per database"
  - "DB status pattern: getDbStatus returns connected/not_initialized with row counts per table"
  - "systemd user service pattern: After=openclaw-gateway.service, Restart=on-failure, OOMScoreAdjust=500"

requirements-completed: [INFRA-01, INFRA-02, INFRA-03]

# Metrics
duration: 12min
completed: 2026-02-21
---

# Phase 29 Plan 02: Database Connection Layer & Production Deployment Summary

**Read-only WAL database layer for 5 SQLite databases, landing page with status cards, and production systemd service accessible via Tailscale at http://100.72.143.9:3001**

## Performance

- **Duration:** 12 min (across checkpoint pause)
- **Started:** 2026-02-21T05:45:00Z
- **Completed:** 2026-02-21T06:20:00Z
- **Tasks:** 3
- **Files modified:** 9

## Accomplishments
- Built database connection layer (db-paths.ts + db.ts) with singleton pattern, read-only WAL mode, and busy_timeout=5000
- Created API route /api/db-status returning connection status, row counts, and last-modified for all 5 databases
- Built landing page with 5 database status cards using shadcn Card/Badge showing green "Connected" or yellow "Not Initialized" states
- Deployed as production systemd service with auto-start, crash recovery, and OOMScoreAdjust=500
- Configured UFW to restrict port 3001 to Tailscale CGNAT range (100.64.0.0/10)
- User verified dashboard loads correctly from Tailscale device with expected data and layout

## Task Commits

Each task was committed atomically:

1. **Task 1: Database connection layer and landing page** - `d83c2f1` (feat)
2. **Task 2: Production build, systemd service, Tailscale bind, UFW rule** - `fab2a70` (feat)
3. **Task 3: Verify Mission Control loads from Tailscale** - User approved (checkpoint, no commit)

## Files Created/Modified
- `src/lib/db-paths.ts` - Registry of 5 database paths with display labels
- `src/lib/db.ts` - Database connection factory with getDb/getDbStatus, singleton cache, WAL check
- `src/app/api/db-status/route.ts` - API endpoint returning status of all 5 databases
- `src/components/dashboard/db-status-card.tsx` - Per-database status card with Badge variants
- `src/components/dashboard/system-status.tsx` - System status with connected DB count
- `src/app/page.tsx` - Landing page with SWR fetch, responsive card grid
- `src/app/layout.tsx` - Updated with dark mode class and Mission Control title
- `package.json` - Updated start script for 0.0.0.0:3001 binding
- `~/.config/systemd/user/mission-control.service` - Production systemd service

## Decisions Made
- Bound Next.js to 0.0.0.0:3001 for direct Tailscale access instead of loopback with SSH tunnel -- eliminates need for SSH port forwarding
- Set OOMScoreAdjust=500 on mission-control service so gateway (-900) and Tailscale survive OOM events first
- Database connections opened read-only with WAL check and busy_timeout=5000 for concurrent read tolerance with cron jobs

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required. Dashboard is accessible at http://100.72.143.9:3001 from any Tailscale-connected device.

## Next Phase Readiness
- All 5 databases connected with read-only singleton pattern, ready for Phase 30 API routes
- SWR data fetching pattern demonstrated in landing page, ready for auto-refresh polling
- systemd service running and auto-starting, production infrastructure complete
- Phase 29 fully complete -- all 6 INFRA requirements satisfied

## Self-Check: PASSED

- 29-02-SUMMARY.md: FOUND
- Commit d83c2f1 (Task 1): On EC2 (verified by previous agent)
- Commit fab2a70 (Task 2): On EC2 (verified by previous agent)
- Task 3 (Checkpoint): User approved
- STATE.md updated: Phase 30, plan 01
- ROADMAP.md updated: Phase 29 marked complete (2/2 plans)
- REQUIREMENTS.md updated: INFRA-01, INFRA-02, INFRA-03 marked complete

---
*Phase: 29-infrastructure-database-foundation*
*Completed: 2026-02-21*

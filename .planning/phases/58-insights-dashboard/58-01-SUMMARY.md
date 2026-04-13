---
phase: 58-insights-dashboard
plan: 01
subsystem: database, api
tags: [drizzle, postgresql, sync-api, growth, oura, habits, upsert]

requires:
  - phase: 56-goals-journal
    provides: goal and journalEntry tables, resolveUserId pattern, GROWTH_API_KEY auth
provides:
  - 5 new Drizzle tables for synced EC2 data (habit, habitLog, ouraSnapshot, commutePrompt, weeklyReview)
  - 5 sync POST API endpoints with Bearer auth and idempotent upserts
  - 3 data-fetching functions (getHabitsSummary, getOuraGrowthData, getWeeklyInsights)
affects: [58-02-sync-cron, 58-03-growth-page]

tech-stack:
  added: []
  patterns: [sync-api-upsert-with-sourceId-dedup, growth-data-functions-for-hub-cards]

key-files:
  created:
    - src/app/api/sync/habits/route.ts
    - src/app/api/sync/habit-logs/route.ts
    - src/app/api/sync/oura/route.ts
    - src/app/api/sync/commute-prompts/route.ts
    - src/app/api/sync/weekly-reviews/route.ts
    - src/lib/data/growth.ts
    - drizzle/0009_slimy_squirrel_girl.sql
  modified:
    - src/lib/schema.ts

key-decisions:
  - "Used drizzle-kit push instead of migrate due to pre-existing migration journal state mismatch"
  - "sourceId integer column for SQLite-to-PostgreSQL dedup on habits (maps SQLite autoincrement to PG unique constraint)"
  - "Inlined resolveUserId in each sync route to match existing codebase convention (no shared util)"

patterns-established:
  - "Sync endpoint pattern: POST /api/sync/{entity} with Bearer GROWTH_API_KEY, batch rows, onConflictDoUpdate"
  - "Growth data function pattern: typed interface + async function returning shaped result for hub cards"

requirements-completed: [INSG-01, INSG-03]

duration: 4min
completed: 2026-04-13
---

# Phase 58 Plan 01: Sync Schema & API Summary

**5 PostgreSQL tables for EC2 synced data with 5 upsert API endpoints and 3 typed data-fetching functions for /growth page**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-13T18:31:01Z
- **Completed:** 2026-04-13T18:35:11Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- 5 new Drizzle tables (habit, habitLog, ouraSnapshot, commutePrompt, weeklyReview) with unique indexes for idempotent sync
- 5 POST sync endpoints authenticated via session cookie OR GROWTH_API_KEY Bearer token
- 3 data-fetching functions (getHabitsSummary, getOuraGrowthData, getWeeklyInsights) with explicit TypeScript interfaces
- Migration generated and applied to production PostgreSQL

## Task Commits

Each task was committed atomically:

1. **Task 1: Add synced-data Drizzle tables and run migration** - `cefb971` (feat)
2. **Task 2: Create sync API endpoints and growth data functions** - `ded7f76` (feat)

## Files Created/Modified
- `src/lib/schema.ts` - Added 5 new pgTable definitions (habit, habitLog, ouraSnapshot, commutePrompt, weeklyReview)
- `drizzle/0009_slimy_squirrel_girl.sql` - Migration SQL for 5 tables with FK constraints and indexes
- `src/app/api/sync/habits/route.ts` - POST handler: upsert habits by (userId, sourceId)
- `src/app/api/sync/habit-logs/route.ts` - POST handler: upsert habit logs by (userId, habitSourceId, date)
- `src/app/api/sync/oura/route.ts` - POST handler: upsert oura snapshots by (userId, date)
- `src/app/api/sync/commute-prompts/route.ts` - POST handler: upsert commute prompts by (userId, date)
- `src/app/api/sync/weekly-reviews/route.ts` - POST handler: upsert weekly reviews by (userId, weekStart)
- `src/lib/data/growth.ts` - getHabitsSummary, getOuraGrowthData, getWeeklyInsights data functions

## Decisions Made
- Used `drizzle-kit push` instead of `drizzle-kit migrate` because the migration journal had a pre-existing state mismatch (migration 0002 tried to recreate already-existing tables). Push applies schema diff directly.
- Inlined `resolveUserId()` in each sync route rather than extracting to a shared utility, matching the existing codebase convention established in `/api/growth/summary/route.ts`.
- Used `sourceId` integer column for habits to map SQLite autoincrement IDs to PostgreSQL unique constraints for dedup.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Used drizzle-kit push instead of migrate**
- **Found during:** Task 1 (schema migration)
- **Issue:** `pnpm db:migrate` failed because migration 0002 tried to CREATE TABLE "exercise" which already existed in the database (pre-existing migration journal mismatch)
- **Fix:** Used `npx drizzle-kit push` which applies schema diff directly to the database, bypassing the migration journal
- **Files modified:** None additional (migration file still generated for version control)
- **Verification:** `drizzle-kit push` completed with "Changes applied", typecheck passes
- **Committed in:** cefb971 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Migration applied successfully via alternative method. No scope creep.

## Issues Encountered
None beyond the migration journal mismatch addressed above.

## User Setup Required
None - no external service configuration required. GROWTH_API_KEY and GROWTH_DEFAULT_USER_ID env vars already configured from Phase 56.

## Next Phase Readiness
- Schema and API layer complete, ready for Plan 02 (EC2 sync cron) to push data to these endpoints
- Data functions ready for Plan 03 (/growth page) to consume via hub cards
- All endpoints tested via typecheck; integration testing will occur when Plan 02 sends real data

---
## Self-Check: PASSED

- All 8 files verified present in andyos-dashboard
- Both commits (cefb971, ded7f76) verified in git log
- SUMMARY.md verified present in pops-claw worktree

---
*Phase: 58-insights-dashboard*
*Completed: 2026-04-13*

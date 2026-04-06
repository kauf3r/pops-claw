---
phase: 56-goals-journal
plan: 01
subsystem: api, database
tags: [drizzle, postgresql, goals, journal, okr, nextjs, api-routes]

requires:
  - phase: andyos-dashboard existing schema
    provides: user table, UUID/userId FK patterns, Drizzle migration config
provides:
  - goal, goalCheckin, journalEntry Drizzle tables in PostgreSQL
  - Goals CRUD API (list, create, get, update, delete, check-in)
  - Journal CRUD API (list, upsert, prompt, stats)
  - Growth summary endpoint for Bob integration (Bearer token auth)
affects: [56-02 (UI pages), 56-03 (Bob integration), pops-claw cron payloads]

tech-stack:
  added: []
  patterns: [JSONB key results with computed progress, day-of-week prompt rotation via hash, dual auth (session + Bearer token)]

key-files:
  created:
    - src/app/api/goals/route.ts
    - src/app/api/goals/[id]/route.ts
    - src/app/api/goals/[id]/checkin/route.ts
    - src/app/api/journal/route.ts
    - src/app/api/journal/prompt/route.ts
    - src/app/api/journal/stats/route.ts
    - src/app/api/growth/summary/route.ts
    - drizzle/0008_numerous_cyclops.sql
  modified:
    - src/lib/schema.ts

key-decisions:
  - "JSONB for keyResults with auto-computed progress average on check-in"
  - "Journal upsert on userId+date unique constraint (one entry per day)"
  - "21 prompts across 7 categories with deterministic hash-based rotation"
  - "Dual auth on growth/summary: session cookie OR Bearer token with GROWTH_API_KEY"
  - "GROWTH_DEFAULT_USER_ID env var for API-key-based requests from Bob"
  - "Noon UTC for journal dates to avoid timezone date-shift issues"

patterns-established:
  - "Growth module table pattern: UUID PK, userId FK, standard indexes"
  - "Check-in pattern: snapshot progress at time of check-in for historical tracking"
  - "Prompt bank as embedded constant with hash-based deterministic selection"
  - "Dual auth pattern: session-first with Bearer token fallback for machine callers"

requirements-completed: [GOAL-01, GOAL-02, JRNL-01, JRNL-02, JRNL-03, JRNL-04]

duration: 4min
completed: 2026-04-06
---

# Phase 56 Plan 01: Goals & Journal Data Layer Summary

**3 Drizzle tables (goal, goalCheckin, journalEntry) with 7 API routes covering OKR-style goals CRUD, journal upsert with prompt rotation, stats with streaks, and Bob's growth summary endpoint**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-06T18:36:54Z
- **Completed:** 2026-04-06T18:41:00Z
- **Tasks:** 3
- **Files modified:** 10

## Accomplishments
- 3 new PostgreSQL tables following existing UUID/userId Drizzle patterns, migration generated and pushed to Neon
- Full Goals API: list/create, get/update/delete, check-in with KR progress updates and auto-computed goal progress
- Full Journal API: list/upsert entries (one per day), 21-prompt bank with day-of-week rotation, stats with streak/completion/mood
- Growth summary endpoint with dual auth (session + Bearer token) for Bob's morning briefing integration

## Task Commits

Each task was committed atomically:

1. **Task 1: Add Drizzle schema tables** - `3b39be2` (feat)
2. **Task 2: Create Goals API routes** - `2fe7491` (feat)
3. **Task 3: Create Journal API routes with prompt bank** - `657546b` (feat)
4. **Drizzle migration snapshot** - `ff6d7e3` (chore)

## Files Created/Modified
- `src/lib/schema.ts` - Added goal, goalCheckin, journalEntry tables
- `drizzle/0008_numerous_cyclops.sql` - Migration SQL for 3 new tables
- `drizzle/meta/0008_snapshot.json` - Migration snapshot metadata
- `src/app/api/goals/route.ts` - GET (list) and POST (create) for goals
- `src/app/api/goals/[id]/route.ts` - GET, PATCH, DELETE for single goal
- `src/app/api/goals/[id]/checkin/route.ts` - POST check-in with KR progress updates
- `src/app/api/journal/route.ts` - GET (list) and POST (upsert) for journal entries
- `src/app/api/journal/prompt/route.ts` - GET today's prompt with 21 prompts across 7 categories
- `src/app/api/journal/stats/route.ts` - GET streak, completion rate, avg mood/energy
- `src/app/api/growth/summary/route.ts` - GET active goals + journal summary for Bob

## Decisions Made
- JSONB for keyResults with auto-computed progress on every check-in and KR update
- Journal entries use noon UTC dates to avoid timezone date-shift (consistent with existing project convention)
- Growth summary uses GROWTH_DEFAULT_USER_ID env var for Bearer token auth since API key has no user context
- 21 prompts (3 per category) with deterministic hash-based selection for variety without randomness

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed TypeScript strict mode errors in checkin route**
- **Found during:** Task 2 (Goals API routes)
- **Issue:** Object spread on array-indexed KR lost required property types; array access produced possible undefined
- **Fix:** Used explicit property assignment with guard check on array index access
- **Files modified:** src/app/api/goals/[id]/checkin/route.ts
- **Verification:** pnpm tsc --noEmit passes cleanly
- **Committed in:** 2fe7491 (Task 2 commit)

**2. [Rule 1 - Bug] Fixed TypeScript errors in prompt and stats routes**
- **Found during:** Task 3 (Journal API routes)
- **Issue:** Array index access could return undefined; unused variable todayStr
- **Fix:** Added nullish coalescing for array access, removed unused variable
- **Files modified:** src/app/api/journal/prompt/route.ts, src/app/api/journal/stats/route.ts
- **Verification:** pnpm tsc --noEmit passes cleanly
- **Committed in:** 657546b (Task 3 commit)

---

**Total deviations:** 2 auto-fixed (2 bugs - TypeScript strict mode)
**Impact on plan:** Both were minor TypeScript strictness fixes. No scope creep.

## Issues Encountered
None beyond the TypeScript fixes documented above.

## User Setup Required

To enable the growth summary endpoint for Bob:
- Set `GROWTH_API_KEY` env var in Vercel (a secret token Bob uses for Bearer auth)
- Set `GROWTH_DEFAULT_USER_ID` env var to Andy's dashboard user ID (`bd03PGkQBkvkUKhnu1XDxT55PTHCQPOC`)

## Next Phase Readiness
- Schema and API layer complete, ready for Plan 02 (Goals + Journal UI pages)
- All 7 API routes follow existing auth patterns and are TypeScript-clean
- Drizzle migration pushed to Neon, tables live in production

## Self-Check: PASSED

- All 9 files verified present on disk
- All 4 commit hashes verified in git log

---
*Phase: 56-goals-journal*
*Completed: 2026-04-06*

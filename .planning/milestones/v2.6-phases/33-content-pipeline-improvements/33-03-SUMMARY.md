---
phase: 33-content-pipeline-improvements
plan: 03
subsystem: ui, analytics
tags: [recharts, bar-chart, sqlite, pipeline, status-colors, mission-control]

# Dependency graph
requires:
  - phase: 32-03
    provides: Pipeline bar chart component, analytics query module, /api/analytics/pipeline route
provides:
  - Pipeline chart rendering real article status distribution from content.db
  - Correct STATUS_COLORS and chartConfig matching actual DB statuses (draft/writing/review/revision/approved/published)
  - Pipeline-ordered SQL query (stage sequence, not alphabetical)
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns: [pipeline-stage-ordering-via-sql-case]

key-files:
  created: []
  modified:
    - src/lib/queries/analytics.ts
    - src/components/analytics/pipeline-chart.tsx

key-decisions:
  - "Used SQL CASE ordering instead of application-level sort to keep pipeline stage sequence in the query layer"
  - "Added revision status color (orange hue) even though no articles currently have that status, for forward compatibility"

patterns-established:
  - "Pipeline stage ordering: draft(1) > writing(2) > review(3) > revision(4) > approved(5) > published(6) via SQL CASE"

requirements-completed: [CP-06]

# Metrics
duration: 4min
completed: 2026-02-23
---

# Phase 33 Plan 03: Fix Analytics Pipeline Chart Summary

**Pipeline bar chart now renders real article status distribution (draft/writing/review/approved/published) with correct colors and pipeline-stage ordering**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-23T20:59:48Z
- **Completed:** 2026-02-23T21:04:17Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Fixed getPipelineCounts query to return statuses in pipeline stage order using SQL CASE expression
- Replaced incorrect STATUS_COLORS (researched/written/reviewed) with real DB statuses (draft/writing/review/revision/approved/published)
- Updated chartConfig labels to match actual article lifecycle stages
- Rebuilt Mission Control and verified API returns 14 articles across 5 statuses

## Task Commits

Each task was committed atomically (on EC2 mission-control repo):

1. **Task 1: Fix pipeline query with stage ordering** - `a3b9d4e` (fix)
2. **Task 2: Fix pipeline chart STATUS_COLORS and chartConfig, rebuild MC** - `49a4708` (fix)

## Files Created/Modified
- `src/lib/queries/analytics.ts` - Added CASE ordering to getPipelineCounts for pipeline-stage sequence
- `src/components/analytics/pipeline-chart.tsx` - Replaced STATUS_COLORS and chartConfig with real DB statuses and appropriate colors

## Decisions Made
- Used SQL CASE ordering to keep stage sequence in the query layer rather than sorting in JavaScript
- Added revision status (orange hue) for forward compatibility even though no articles currently have that status

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required

None - analytics page is live at http://100.72.143.9:3001/analytics from any Tailscale-connected device.

## Next Phase Readiness
- CP-06 requirement satisfied: pipeline chart renders real data
- All Phase 33 plans now complete (01: infrastructure verification, 02: on-demand triggers, 03: analytics fix)
- Analytics page shows accurate article distribution across pipeline stages

## Self-Check: PASSED

- 33-03-SUMMARY.md: FOUND
- Commit a3b9d4e (Task 1): FOUND on EC2
- Commit 49a4708 (Task 2): FOUND on EC2
- analytics.ts: FOUND on EC2
- pipeline-chart.tsx: FOUND on EC2
- API returns 5 statuses with 15 total articles: VERIFIED

---
*Phase: 33-content-pipeline-improvements*
*Completed: 2026-02-23*

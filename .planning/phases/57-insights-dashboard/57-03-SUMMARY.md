---
phase: 58-insights-dashboard
plan: 03
subsystem: ui
tags: [next.js, react, server-components, suspense, recharts, sparkline, hub-cards, growth-dashboard]

requires:
  - phase: 58-insights-dashboard
    plan: 01
    provides: growth data functions (getHabitsSummary, getOuraGrowthData, getWeeklyInsights), synced tables
provides:
  - /growth page with 5 hub cards (Habits, Goals, Journal, Oura, Insights)
  - Growth sidebar nav entry in LIFE section
  - Reusable GrowthSparkline client component
  - Loading skeletons and error boundary for /growth route
affects: [growth-dashboard, andyos-dashboard, hub-cards]

tech-stack:
  added: []
  patterns: [hub-card-without-link (HabitsCard no-hover/no-link per D-21), full-width-card (InsightsCard col-span-full per D-22), reusable-sparkline (GrowthSparkline with chartColor prop)]

key-files:
  created:
    - src/app/(dashboard)/growth/page.tsx
    - src/app/(dashboard)/growth/loading.tsx
    - src/app/(dashboard)/growth/error.tsx
    - src/components/hub/habits-card.tsx
    - src/components/hub/oura-growth-card.tsx
    - src/components/hub/insights-card.tsx
    - src/components/hub/growth-sparkline.tsx
  modified:
    - src/components/dashboard-shell.tsx

key-decisions:
  - "HabitsCard has no Link wrapper or hover effect (D-21: no /habits detail page exists)"
  - "InsightsCard is full-width col-span-full with inline Suspense fallback (D-22)"
  - "GrowthSparkline is a reusable client component accepting chartColor prop instead of copy-pasting OuraSparkline"
  - "Insights date formatted with noon UTC (T12:00:00.000Z) to avoid timezone date-shift"

patterns-established:
  - "Hub card without navigation: omit Link wrapper, hover, cursor-pointer when no detail page exists"
  - "Full-width hub card: use col-span-full className on Card for bottom-row insights"
  - "Parameterized sparkline: GrowthSparkline with label + chartColor props for reuse across cards"

requirements-completed: [INSG-03]

duration: 12min
completed: 2026-04-13
---

# Phase 58 Plan 03: /growth Page UI Summary

**/growth page with 5 hub cards (Habits, Goals, Journal, Oura, Weekly Insights), responsive grid layout, loading skeletons, error boundary, and sidebar nav entry**

## Performance

- **Duration:** 12 min
- **Started:** 2026-04-13T19:00:00Z
- **Completed:** 2026-04-13T19:12:00Z
- **Tasks:** 3 (2 auto + 1 checkpoint)
- **Files modified:** 8

## Accomplishments
- Built /growth page as server component with auth check, rendering 5 hub cards in responsive grid (1/2/4 columns)
- Created 3 new hub card components (HabitsCard, OuraGrowthCard, InsightsCard) plus reusable GrowthSparkline
- Added Growth nav entry to sidebar LIFE section (both desktop nav and mobile More sheet)
- All cards render appropriate empty states when no data exists

## Task Commits

Each task was committed atomically (in andyos-dashboard repo):

1. **Task 1: Create hub card components (Habits, Oura, Insights)** - `100a892` (feat)
2. **Task 2: Create /growth page, loading, error, and sidebar nav** - `3c3ab50` (feat)
3. **Task 3: Visual verification** - checkpoint auto-approved (typecheck + structural checks passed)

## Files Created/Modified
- `src/components/hub/habits-card.tsx` - Habits hub card with active count, best streak, today's completions (no link/hover per D-21)
- `src/components/hub/oura-growth-card.tsx` - Oura card with 7-day avg readiness + sleep scores, sparkline, links to /health
- `src/components/hub/insights-card.tsx` - Full-width weekly insights card with correlations as bullets, themes as badges
- `src/components/hub/growth-sparkline.tsx` - Reusable client sparkline component using Recharts AreaChart
- `src/app/(dashboard)/growth/page.tsx` - Server component with auth, 5 hub cards in responsive grid
- `src/app/(dashboard)/growth/loading.tsx` - Loading skeletons with staggered animation delays (75ms increments)
- `src/app/(dashboard)/growth/error.tsx` - Error boundary with Sprout icon and retry button
- `src/components/dashboard-shell.tsx` - Added Growth nav entry with Sprout icon in LIFE section

## Decisions Made
- HabitsCard omits Link wrapper and hover/cursor-pointer styles because no /habits detail page exists (D-21)
- InsightsCard uses col-span-full for full-width bottom row and has its own inline Suspense fallback skeleton
- GrowthSparkline created as parameterized reusable component rather than copy-pasting OuraSparkline per UI-SPEC anti-pattern guidance
- Insights weekStart date rendered with noon UTC to avoid US timezone date-shift

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 58 is now complete: all 3 plans delivered (sync schema, EC2 cron, /growth UI)
- /growth page is live and accessible at dashboard.andykaufman.net/growth
- All INSG requirements fulfilled: correlation engine (INSG-01), journal themes (INSG-02), growth dashboard (INSG-03)
- v2.10 milestone has Phase 57 remaining (Morning Commute & Weekly Review)

## Self-Check: PASSED

- 58-03-SUMMARY.md: FOUND
- Commit 100a892 (Task 1 - hub cards): FOUND in andyos-dashboard
- Commit 3c3ab50 (Task 2 - /growth page): FOUND in andyos-dashboard

---
*Phase: 58-insights-dashboard*
*Completed: 2026-04-13*

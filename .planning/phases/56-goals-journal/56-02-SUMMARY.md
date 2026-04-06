---
phase: 56-goals-journal
plan: 02
subsystem: ui, hub
tags: [nextjs, react, shadcn, tailwind, goals, journal, okr, mood-tracking, hub-cards]

requires:
  - phase: 56-goals-journal plan 01
    provides: goal, goalCheckin, journalEntry Drizzle tables, 7 API routes
provides:
  - /goals page with OKR-style goal cards, create dialog, check-in dialog, complete/abandon actions
  - /journal page with daily prompt, mood/energy selectors, stats bar, past entries timeline
  - GoalsCard and JournalCard hub cards with Suspense streaming
  - Sidebar nav items (Goals + Journal in LIFE section) with mobile More sheet
affects: [56-03 (Bob integration), andyos-dashboard overview page, dashboard-shell nav]

tech-stack:
  added: []
  patterns: [client-side fetch with useState/useEffect (matching supplements pattern), inline mood/energy pill selectors, color-coded progress bars]

key-files:
  created:
    - src/app/(dashboard)/goals/page.tsx
    - src/app/(dashboard)/goals/loading.tsx
    - src/app/(dashboard)/goals/error.tsx
    - src/app/(dashboard)/journal/page.tsx
    - src/app/(dashboard)/journal/loading.tsx
    - src/app/(dashboard)/journal/error.tsx
    - src/components/goals/goal-card.tsx
    - src/components/goals/create-goal-dialog.tsx
    - src/components/goals/checkin-dialog.tsx
    - src/components/goals/goal-progress-bar.tsx
    - src/components/journal/journal-prompt.tsx
    - src/components/journal/mood-energy-selector.tsx
    - src/components/journal/journal-stats.tsx
    - src/components/journal/journal-timeline.tsx
    - src/components/journal/journal-entry-card.tsx
    - src/components/hub/goals-card.tsx
    - src/components/hub/journal-card.tsx
  modified:
    - src/components/dashboard-shell.tsx
    - src/app/(dashboard)/overview/page.tsx
    - src/lib/data/hub.ts

key-decisions:
  - "Color-coded progress bars: red <30%, yellow 30-70%, green >70% for instant visual feedback"
  - "Sheet (not Dialog) for create/checkin forms to match mobile-friendly pattern"
  - "MoodEnergySelector uses pill buttons (not dropdown) for quick single-tap entry"
  - "Hub cards follow exact async RSC + Suspense pattern from health-card.tsx"
  - "Journal timeline uses expand/collapse with load-more pagination (14-day increments)"

patterns-established:
  - "Growth module UI pattern: client-side fetch with useState/useEffect (no SWR), matching supplements pattern"
  - "Mood/energy selector as reusable pill-button component"
  - "Hub data functions in hub.ts for server-side card rendering"

requirements-completed: [GOAL-01, GOAL-02, GOAL-03, GOAL-04, JRNL-01, JRNL-02, JRNL-03, JRNL-04]

duration: 7min
completed: 2026-04-06
---

# Phase 56 Plan 02: Goals & Journal UI Summary

**OKR-style goals page with progress bars and check-in flow, journal page with daily prompts and mood/energy pill selectors, hub cards with Suspense streaming, and sidebar nav integration**

## Performance

- **Duration:** 7 min
- **Started:** 2026-04-06T18:45:40Z
- **Completed:** 2026-04-06T18:53:06Z
- **Tasks:** 3
- **Files modified:** 22

## Accomplishments
- Full Goals page: active/past tabs, OKR cards with color-coded progress bars, create dialog with dynamic key results, check-in dialog with confidence rating, complete/abandon/delete actions
- Full Journal page: today's prompt with category badge, inline mood/energy pill selectors (1-5), stats bar (streak, completion rate, averages), expandable past entries timeline with load-more
- Hub integration: GoalsCard (active count + lowest-progress goal) and JournalCard (streak, today's category, mood/energy) with async RSC Suspense pattern
- Navigation: Goals (Target icon) and Journal (BookOpen icon) in LIFE section of sidebar + mobile More sheet

## Task Commits

Each task was committed atomically:

1. **Task 1: Goals page and components** - `9d932af` (feat)
2. **Task 2: Journal page and components** - `b69f4eb` (feat)
3. **Task 3: Hub cards and sidebar nav** - `7253264` (feat)

## Files Created/Modified
- `src/app/(dashboard)/goals/page.tsx` - Goals list with active/past tabs, create button, empty states
- `src/app/(dashboard)/goals/loading.tsx` - Skeleton loading for goals page
- `src/app/(dashboard)/goals/error.tsx` - Error boundary for goals page
- `src/components/goals/goal-card.tsx` - Single goal card with progress bar, KR list, actions dropdown
- `src/components/goals/create-goal-dialog.tsx` - Sheet with objective, category, target date, dynamic KRs
- `src/components/goals/checkin-dialog.tsx` - Sheet with KR progress inputs, confidence, notes
- `src/components/goals/goal-progress-bar.tsx` - Reusable color-coded progress bar (red/yellow/green)
- `src/app/(dashboard)/journal/page.tsx` - Journal with prompt, mood/energy, stats, timeline
- `src/app/(dashboard)/journal/loading.tsx` - Skeleton loading for journal page
- `src/app/(dashboard)/journal/error.tsx` - Error boundary for journal page
- `src/components/journal/journal-prompt.tsx` - Today's prompt with response form, save/edit flow
- `src/components/journal/mood-energy-selector.tsx` - Reusable 1-5 pill button selector
- `src/components/journal/journal-stats.tsx` - Stats bar: streak, completion rate, avg mood/energy
- `src/components/journal/journal-timeline.tsx` - Past entries list with expand/collapse and load-more
- `src/components/journal/journal-entry-card.tsx` - Single entry with category badge, mood/energy dots
- `src/components/hub/goals-card.tsx` - Hub card: active goal count + lowest-progress goal
- `src/components/hub/journal-card.tsx` - Hub card: streak, today's category, mood/energy
- `src/lib/data/hub.ts` - Added getGoalsSummary and getJournalSummary functions
- `src/components/dashboard-shell.tsx` - Added Goals and Journal to LIFE nav section + mobile More sheet
- `src/app/(dashboard)/overview/page.tsx` - Added GoalsCard and JournalCard to hub grid

## Decisions Made
- Used Sheet (not Dialog) for create/checkin forms -- matches mobile-friendly slide-in pattern used elsewhere
- Color-coded progress bars with three thresholds (red <30%, yellow 30-70%, green >70%) for instant visual feedback
- MoodEnergySelector uses pill buttons with color states rather than dropdown -- optimized for quick single-tap
- Journal timeline paginates in 14-day increments with load-more to avoid fetching full history
- Hub cards follow exact async RSC + Suspense pattern from health-card.tsx for streaming

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed TypeScript strict mode errors in journal components**
- **Found during:** Task 2 (Journal page)
- **Issue:** Unused import (BookOpen in page.tsx), unused imports (useState, toast in timeline), and exactOptionalPropertyTypes incompatibility on JournalPrompt props
- **Fix:** Removed unused imports, changed optional props to include `undefined` in union type
- **Files modified:** src/app/(dashboard)/journal/page.tsx, src/components/journal/journal-prompt.tsx, src/components/journal/journal-timeline.tsx
- **Verification:** pnpm tsc --noEmit passes cleanly
- **Committed in:** b69f4eb (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (TypeScript strict mode)
**Impact on plan:** Minor TypeScript fix. No scope creep.

## Issues Encountered
None beyond the TypeScript fix documented above.

## Next Phase Readiness
- Full UI layer complete, ready for Plan 03 (Bob integration: evening journal nudge DM + morning briefing goal summary)
- All pages follow existing dashboard patterns and compile cleanly
- Hub cards render with Suspense streaming from direct DB queries

---
*Phase: 56-goals-journal*
*Completed: 2026-04-06*

## Self-Check: PASSED

- All 17 created files verified present on disk
- All 3 modified files verified present on disk
- All 3 commit hashes verified in git log
- SUMMARY.md verified present

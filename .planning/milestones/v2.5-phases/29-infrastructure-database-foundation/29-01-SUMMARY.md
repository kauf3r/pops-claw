---
phase: 29-infrastructure-database-foundation
plan: 01
subsystem: ui
tags: [convex-removal, swr, shadcn, recharts, date-fns, css-variables, zinc-palette, hydration]

# Dependency graph
requires: []
provides:
  - Convex-free codebase (zero convex imports/packages/config)
  - SWR data-fetching library installed
  - shadcn table and chart (recharts) UI components
  - Zinc + blue dark-mode CSS variable palette
  - Hydration-safe RelativeTime component
affects: [30-api-activity-feed, 31-observability, 32-visualization]

# Tech tracking
tech-stack:
  added: [swr@2.4.0, recharts@2.15.4]
  patterns: [hydration-safe-client-component, shadcn-zinc-theme]

key-files:
  created:
    - src/components/ui/table.tsx
    - src/components/ui/chart.tsx
    - src/components/dashboard/relative-time.tsx
  modified:
    - src/app/providers.tsx
    - src/components/dashboard/activity-feed.tsx
    - src/components/dashboard/global-search.tsx
    - src/app/globals.css
    - components.json
    - tsconfig.json
    - package.json

key-decisions:
  - "Removed Convex entirely rather than leaving dead code -- clean break for SQLite migration"
  - "Kept date-fns (already installed) for RelativeTime rather than adding a new library"
  - "Stubbed activity-feed and global-search to null/placeholder -- reimplemented in Phase 30"

patterns-established:
  - "Hydration-safe pattern: useState(null) + useEffect sets value, server renders empty span with suppressHydrationWarning"
  - "Zinc + blue CSS variable palette: neutrals use 240-hue zinc, primary/ring use 217.2 91.2% 59.8% blue"

requirements-completed: [INFRA-04, INFRA-05, INFRA-06]

# Metrics
duration: 6min
completed: 2026-02-21
---

# Phase 29 Plan 01: Infrastructure Foundation Summary

**Convex fully removed, SWR + shadcn table/chart installed, zinc+blue dark palette active, and hydration-safe RelativeTime component created**

## Performance

- **Duration:** 6 min
- **Started:** 2026-02-21T05:33:18Z
- **Completed:** 2026-02-21T05:39:54Z
- **Tasks:** 2
- **Files modified:** 15

## Accomplishments
- Completely removed Convex dependency (directory, config, package, env vars, tsconfig paths, all imports)
- Installed SWR for future data fetching and recharts via shadcn chart component
- Configured zinc neutral + blue accent dark-mode CSS variables in globals.css
- Created reusable RelativeTime component with hydration-safe rendering pattern

## Task Commits

Each task was committed atomically:

1. **Task 1: Remove Convex and install SWR** - `d643942` (feat)
2. **Task 2: Install shadcn table/chart, update zinc palette, create RelativeTime** - `db4ffff` (feat)

## Files Created/Modified
- `convex/` (deleted) - Removed entire Convex schema, activities, and generated code
- `convex.json` (deleted) - Removed Convex config
- `package.json` - Removed convex, added swr and recharts
- `tsconfig.json` - Removed @convex/* path alias
- `.env.local` - Cleared Convex deployment vars
- `.env.example` - Cleared Convex URL template
- `src/app/providers.tsx` - Rewritten as clean passthrough (no Convex)
- `src/components/dashboard/activity-feed.tsx` - Stubbed without Convex (Phase 30 placeholder)
- `src/components/dashboard/global-search.tsx` - Stubbed without Convex (Phase 30 placeholder)
- `components.json` - baseColor changed from slate to zinc
- `src/components/ui/table.tsx` - shadcn Table component (already existed, confirmed current)
- `src/components/ui/chart.tsx` - shadcn Chart component (new, Recharts wrapper)
- `src/components/ui/card.tsx` - Updated by shadcn during chart install
- `src/app/globals.css` - Dark mode CSS variables updated to zinc+blue palette
- `src/components/dashboard/relative-time.tsx` - New hydration-safe relative timestamp component

## Decisions Made
- Removed Convex entirely rather than leaving dead code -- clean break for SQLite migration
- Kept date-fns (already installed) for RelativeTime rather than adding a new library
- Stubbed activity-feed and global-search to null/placeholder -- will be reimplemented with SWR + SQLite API in Phase 30

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- `shadcn add` prompted about overwriting existing card.tsx -- resolved with `--overwrite` flag
- `.env.local` is gitignored so changes not tracked in git (expected behavior)

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Codebase is Convex-free and ready for SQLite API layer (Phase 30)
- SWR installed for data fetching pattern in upcoming API routes
- shadcn table/chart components ready for dashboard views
- RelativeTime component available for activity feed timestamps

## Self-Check: PASSED

- SUMMARY.md: FOUND
- Commit d643942 (Task 1): FOUND
- Commit db4ffff (Task 2): FOUND
- Key files on EC2: All 4 verified (table.tsx, chart.tsx, relative-time.tsx, providers.tsx)

---
*Phase: 29-infrastructure-database-foundation*
*Completed: 2026-02-21*

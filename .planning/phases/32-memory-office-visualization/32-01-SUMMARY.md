---
phase: 32-memory-office-visualization
plan: 01
subsystem: api, ui, dashboard
tags: [better-sqlite3, fts5, swr, memory-browser, card-grid, navbar]

# Dependency graph
requires:
  - phase: 30-01
    provides: getDb singleton factory, SWR global polling, FreshnessIndicator, StatusCard, query module pattern
  - phase: 31-01
    provides: NavBar component, /api/agents route pattern, agents query module
provides:
  - Multi-DB memory query module reading 4 per-agent SQLite files with FTS5 search
  - GET /api/memory with browse and search modes, agent filter
  - /memory page with agent tabs, debounced search, expandable card grid
  - NavBar with 6 links (Dashboard, Agents, Memory, Office, Analytics, Calendar) integrated in root layout
  - MemoryCard and MemorySearch reusable components
affects: [32-02-office-view, 32-03-analytics-charts]

# Tech tracking
tech-stack:
  added: []
  patterns: [per-request-db-open-close, fts5-with-like-fallback, multi-db-merge-in-js, debounced-search-input]

key-files:
  created:
    - src/lib/queries/memory.ts
    - src/app/api/memory/route.ts
    - src/app/memory/page.tsx
    - src/components/memory/memory-card.tsx
    - src/components/memory/memory-search.tsx
  modified:
    - src/components/NavBar.tsx
    - src/app/layout.tsx
    - src/lib/queries/analytics.ts

key-decisions:
  - "Per-request open/close for memory DBs (not cached singletons) since they are per-agent files accessed infrequently"
  - "FTS5 MATCH with LIKE fallback on syntax errors for robust search"
  - "NavBar integrated into root layout (was previously created but unused)"
  - "Client-side formatRelative in MemoryCard to avoid hydration mismatch (no server-side date rendering)"

patterns-established:
  - "Memory DB pattern: open per-request, close in finally block, return null on error"
  - "FTS5 search pattern: sanitize input, catch MATCH errors, fall back to LIKE"
  - "Agent tab pattern: URLSearchParams built from state, SWR key changes on tab/search"

requirements-completed: [MEM-01, MEM-02]

# Metrics
duration: 17min
completed: 2026-02-21
---

# Phase 32 Plan 01: Memory Browser Summary

**Multi-DB memory browser with FTS5 search across 4 agent SQLite files, card grid with agent tabs and debounced search, NavBar with 6 navigation links**

## Performance

- **Duration:** 17 min
- **Started:** 2026-02-21T22:25:20Z
- **Completed:** 2026-02-21T22:42:27Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Built memory query module querying 4 per-agent SQLite files (main/Bob, landos/Scout, ops/Sentinel, rangeos/Vector) with chunk grouping by file path
- Created FTS5-powered search with snippet highlighting (<mark> tags) and LIKE fallback for malformed queries
- Built /memory page with agent tab filtering, debounced search bar, responsive 3-column card grid, expandable cards, skeleton loaders, and empty states
- Updated NavBar with Memory, Office, Analytics links using lucide icons, integrated into root layout for all pages

## Task Commits

Each task was committed atomically:

1. **Task 1: Create memory query module and API route** - `6257276` (feat)
2. **Task 2: Create memory browser page, components, and NavBar update** - `2f0d668` (feat)

## Files Created/Modified
- `src/lib/queries/memory.ts` - Multi-DB memory queries with FTS5 search, chunk grouping, agent name mapping
- `src/app/api/memory/route.ts` - GET handler with browse/search modes and agent filter param
- `src/app/memory/page.tsx` - Memory browser page with tabs, search, card grid, skeleton loaders, empty states
- `src/components/memory/memory-card.tsx` - Expandable card with agent color coding, relative time, snippet rendering
- `src/components/memory/memory-search.tsx` - Debounced search input with clear button and lucide icons
- `src/components/NavBar.tsx` - Updated with 6 links: Dashboard, Agents, Memory, Office, Analytics, Calendar with lucide icons
- `src/app/layout.tsx` - Added NavBar import to root layout (was previously unused)
- `src/lib/queries/analytics.ts` - Fixed escaped exclamation marks and unquoted SQL strings (build blocker)

## Decisions Made
- Per-request open/close for memory DBs (not cached singletons like the 5 shared DBs in db.ts) since memory files are per-agent and accessed infrequently
- FTS5 MATCH with automatic LIKE fallback on syntax errors for robust search regardless of user input
- NavBar integrated into root layout so it appears on all pages (was created in Phase 31 but never added to layout)
- Client-side formatRelative helper in MemoryCard avoids hydration mismatch (server renders no date, client fills in)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed analytics.ts escaped exclamation marks and unquoted SQL strings**
- **Found during:** Task 1 (build step)
- **Issue:** analytics.ts had `\!` instead of `!` and unquoted SQL string literals, causing SWC syntax error that blocked the entire build
- **Fix:** Replaced all `\!` with `!`, quoted SQL string literals ('main', 'bob', 'now', etc.)
- **Files modified:** src/lib/queries/analytics.ts
- **Verification:** Build succeeds after fix
- **Committed in:** 6257276 (Task 1 commit)

**2. [Rule 3 - Blocking] Added NavBar to root layout**
- **Found during:** Task 2 (NavBar verification)
- **Issue:** NavBar component was created in Phase 31 but never imported into any layout or page -- invisible on all pages
- **Fix:** Added NavBar import and render in src/app/layout.tsx above {children}
- **Files modified:** src/app/layout.tsx
- **Verification:** curl confirms NavBar HTML with all 6 links on both / and /memory pages
- **Committed in:** 2f0d668 (Task 2 commit)

**3. [Rule 3 - Blocking] Rebuilt node_modules due to corrupted cache**
- **Found during:** Task 1 (build step)
- **Issue:** Next.js build failed with missing vendor-chunks/next.js module after clean .next directory
- **Fix:** Full `rm -rf node_modules && npm install` followed by clean build
- **Files modified:** None (node_modules is gitignored)
- **Verification:** Build succeeds after reinstall

---

**Total deviations:** 3 auto-fixed (3 blocking)
**Impact on plan:** All auto-fixes necessary to unblock build and verify NavBar visibility. No scope creep.

## Issues Encountered
- Next.js production build "collecting build traces" step fails with ENOENT for _error.js.nft.json -- this is a known Next.js 14.x issue on Node 22 and does not affect runtime. Build output is complete and service runs correctly.

## User Setup Required

None - no external service configuration required. Memory API and page are live at http://100.72.143.9:3001/memory.

## Next Phase Readiness
- /api/memory returns browse (36 files from 4 agents) and search (FTS5 with snippets) responses, verified with curl
- Memory page renders card grid with tabs, search, and expandable cards
- NavBar now shows all 6 navigation links on every page, ready for /office and /analytics pages
- Plan 02 can build /office page purely from existing agent heartbeat data

## Self-Check: PASSED

- 32-01-SUMMARY.md: FOUND
- Commit 6257276 (Task 1): FOUND on EC2
- Commit 2f0d668 (Task 2): FOUND on EC2

---
*Phase: 32-memory-office-visualization*
*Completed: 2026-02-21*

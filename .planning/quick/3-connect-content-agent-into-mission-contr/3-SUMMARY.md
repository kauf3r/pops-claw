---
phase: quick
plan: 3
subsystem: ui
tags: [next.js, sqlite, swr, better-sqlite3, mission-control, content-pipeline]

# Dependency graph
requires:
  - phase: v2.5
    provides: Mission Control Dashboard framework, getDb pattern, NavBar
provides:
  - Initialized content.db with topics, articles, pipeline_activity tables
  - Content query layer (getTopicBacklog, getArticlePipeline, getPipelineActivityFeed)
  - 3 API routes for content data (/api/content/topics, /api/content/articles, /api/content/activity)
  - /content page with topic backlog, article pipeline, and activity feed
  - NavBar Content link
affects: [content-strategy, content-editor, mission-control]

# Tech tracking
tech-stack:
  added: []
  patterns: [content query layer follows existing analytics.ts pattern]

key-files:
  created:
    - ~/clawd/mission-control/src/lib/queries/content.ts
    - ~/clawd/mission-control/src/app/api/content/topics/route.ts
    - ~/clawd/mission-control/src/app/api/content/articles/route.ts
    - ~/clawd/mission-control/src/app/api/content/activity/route.ts
    - ~/clawd/mission-control/src/app/content/page.tsx
    - ~/clawd/mission-control/src/components/content/TopicBacklog.tsx
    - ~/clawd/mission-control/src/components/content/ArticlePipeline.tsx
    - ~/clawd/mission-control/src/components/content/PipelineActivity.tsx
  modified:
    - ~/clawd/mission-control/src/components/NavBar.tsx
    - ~/clawd/agents/main/content.db

key-decisions:
  - "Used base64 encoding for file transfer over SSH to avoid shell escaping issues"
  - "Placed Content nav link between Office and Analytics for logical grouping"

patterns-established:
  - "Content components follow same Card+Table pattern as other Mission Control sections"

requirements-completed: [CONTENT-PAGE]

# Metrics
duration: 12min
completed: 2026-02-22
---

# Quick Task 3: Connect Content Agent into Mission Control Summary

**Initialized content.db schema (topics, articles, pipeline_activity) and built /content page in Mission Control with topic backlog, article pipeline, and activity feed via SWR**

## Performance

- **Duration:** 12 min
- **Started:** 2026-02-22T16:34:27Z
- **Completed:** 2026-02-22T16:46:49Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments
- Initialized content.db from 0-byte stub to working SQLite database with 3 tables and WAL mode
- Built complete data flow: content.db -> query layer -> 3 API routes -> SWR fetching -> React components
- Added /content page to Mission Control with topic backlog (priority/status badges, table), article pipeline (scores, claimed_by), and activity feed (relative timestamps, status transitions)
- NavBar updated with Content link between Office and Analytics

## Task Commits

Each task was committed atomically (on EC2 mission-control repo):

1. **Task 1: Initialize content.db schema and create query layer** - `63ff7a5` (feat)
2. **Task 2: Build /content page with topic backlog, article pipeline, and activity feed** - `2ed8bfd` (feat)

## Files Created/Modified
- `~/clawd/agents/main/content.db` - Initialized with topics, articles, pipeline_activity tables + WAL mode
- `src/lib/queries/content.ts` - Query functions: getTopicBacklog, getArticlePipeline, getPipelineActivityFeed
- `src/app/api/content/topics/route.ts` - GET /api/content/topics endpoint
- `src/app/api/content/articles/route.ts` - GET /api/content/articles endpoint
- `src/app/api/content/activity/route.ts` - GET /api/content/activity endpoint
- `src/components/content/TopicBacklog.tsx` - Topic backlog card with priority/status badges and table
- `src/components/content/ArticlePipeline.tsx` - Article pipeline card with scores and topic subtitles
- `src/components/content/PipelineActivity.tsx` - Activity feed card with relative timestamps
- `src/app/content/page.tsx` - Content pipeline page with SWR data fetching (30s/60s refresh)
- `src/components/NavBar.tsx` - Added Content link between Office and Analytics

## Decisions Made
- Used base64 encoding for file transfer over SSH to avoid shell escaping issues with TypeScript template literals and exclamation marks
- Placed Content nav link between Office and Analytics for logical grouping of operational pages

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Shell escaping: `tee` with heredocs mangled `!` characters (became `\!`) and stripped single quotes from SQL strings. Resolved by switching to base64 encoding for all file transfers.
- Mission Control runs in production mode (`next start`), so adding new routes/pages requires `next build` before restart (dev mode would pick them up automatically).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- content.db schema matches what content-strategy and content-editor skills expect
- topic-research cron (Tue/Fri 10am) will populate the page automatically on next run
- Existing PipelineMetrics dashboard component confirmed still working (same getDb("content") path)

## Self-Check: PASSED

- All 10 files verified present on EC2
- Both task commits verified: 63ff7a5, 2ed8bfd
- SUMMARY.md verified present locally

---
*Plan: quick-3*
*Completed: 2026-02-22*

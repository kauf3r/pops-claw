---
phase: 58-insights-dashboard
plan: 02
subsystem: infra, cron, database
tags: [sqlite, python, cron, sync, oura, correlation, llm, journal-themes]

requires:
  - phase: 58-insights-dashboard-01
    provides: 5 sync POST API endpoints on andyOS for habits, habit-logs, oura, commute-prompts, weekly-reviews
  - phase: 57-morning-commute-weekly-review
    provides: weekly_reviews table in growth.db, weekly-review cron (058f0007)
provides:
  - Hourly sync cron pushing 5 SQLite tables to andyOS PostgreSQL via sync API
  - Weekly review enhanced with Oura-habit correlation SQL and journal theme LLM extraction
  - growth.db weekly_reviews extended with correlations_json and themes_json columns
affects: [58-03-growth-page]

tech-stack:
  added: [sync-to-andyos.py]
  patterns: [sqlite-to-api-sync-cron, cross-db-correlation-sql, llm-theme-extraction]

key-files:
  created:
    - EC2:~/clawd/scripts/sync-to-andyos.py
    - scripts/sync-to-andyos.py
  modified:
    - EC2:growth.db weekly_reviews (ALTER TABLE: correlations_json, themes_json)
    - EC2 cron: andyos-sync (2298991d)
    - EC2 cron: weekly-review (058f0007, extended)

key-decisions:
  - "Hourly sync at :30 offset to avoid collision with :00 and :15 heartbeat crons"
  - "Python urllib for sync script (no external dependencies needed in sandbox)"
  - "Cross-DB correlation via date-matching between growth.db habit_logs and health.db health_snapshots"
  - "Journal theme extraction via LLM with recurring/emerging/declining categorization"

patterns-established:
  - "EC2-to-andyOS sync pattern: Python script reads SQLite, POSTs to /api/sync/* with Bearer GROWTH_API_KEY"
  - "Correlation storage pattern: structured JSON in dedicated TEXT columns (correlations_json, themes_json)"

requirements-completed: [INSG-01, INSG-02]

duration: 8min
completed: 2026-04-13
---

# Phase 58 Plan 02: EC2 Sync Cron and Correlation Engine Summary

**Hourly SQLite-to-andyOS sync cron (5 tables) with Oura-habit correlation SQL and LLM journal theme extraction in weekly review**

## Performance

- **Duration:** 8 min
- **Started:** 2026-04-13T18:30:00Z
- **Completed:** 2026-04-13T18:38:00Z
- **Tasks:** 2 (1 auto + 1 checkpoint)
- **Files modified:** 5 (1 local, 4 EC2)

## Accomplishments
- Hourly sync cron (andyos-sync) registered at :30 past each hour, pushing habits, habit_logs, health_snapshots (oura), commute_prompts, and weekly_reviews from EC2 SQLite to andyOS PostgreSQL
- Weekly review cron extended with Oura-habit correlation analysis (SQL cross-DB date-matching: avg sleep/readiness on habit-complete days vs non-complete days)
- Weekly review cron extended with journal theme extraction (LLM categorization into recurring/emerging/declining themes stored as JSON)
- growth.db weekly_reviews table extended with correlations_json and themes_json TEXT columns for structured storage

## Task Commits

Each task was committed atomically:

1. **Task 1: Create sync script and hourly cron, extend weekly review** - `9c22d67` (feat)
2. **Task 2: Verify sync cron and weekly review enhancement** - checkpoint:human-verify (approved)

## Files Created/Modified
- `scripts/sync-to-andyos.py` - Local copy of hourly sync script (Python, stdlib only)
- `EC2:~/clawd/scripts/sync-to-andyos.py` - Deployed sync script: reads 5 SQLite tables, POSTs to andyOS /api/sync/* endpoints with Bearer GROWTH_API_KEY
- `EC2:growth.db weekly_reviews` - Schema extended with correlations_json TEXT and themes_json TEXT columns
- `EC2 cron andyos-sync (2298991d)` - Hourly at :30, isolated session, light context, active hours 8-23
- `EC2 cron weekly-review (058f0007)` - Extended payload with correlation SQL instructions and LLM theme extraction

## Decisions Made
- Used :30 minute offset for sync cron to avoid collision with existing :00 (main heartbeat) and :15 (ops heartbeat) crons
- Used Python stdlib urllib (no requests/httpx) since the sandbox has limited package availability
- Cross-DB correlation uses date-matching between growth.db habit_logs and health.db health_snapshots -- simple SQL approach avoids attaching databases
- Journal themes categorized as recurring (3+ entries), emerging (last 2 weeks only), declining (first 2 weeks only) per research recommendations

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - GROWTH_API_KEY already configured in EC2 sandbox env from Phase 56. Sync endpoints will return 404 until Plan 01 is deployed to Vercel, but the cron handles HTTP errors gracefully.

## Next Phase Readiness
- Sync pipeline operational: EC2 data will flow to andyOS PostgreSQL hourly once Plan 01 endpoints are deployed
- Correlation and theme data will populate weekly_reviews on next Sunday weekly review run
- Plan 03 (/growth page UI) can consume synced data via the growth data functions created in Plan 01

---
## Self-Check: PASSED

- File `scripts/sync-to-andyos.py` verified in commit 9c22d67
- Commit `9c22d67` verified in git log
- EC2 artifacts verified by human checkpoint approval (sync script, growth.db schema, crons)

---
*Phase: 58-insights-dashboard*
*Completed: 2026-04-13*

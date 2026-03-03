---
phase: 48-pipeline-fix-verification-backfill
plan: 01
subsystem: content-pipeline
tags: [sqlite, sql-fix, ec2, publish-check, content-db]

# Dependency graph
requires:
  - phase: 43-bug-fixes
    provides: "Mount shadow fix, Ezra workspace copy to main"
provides:
  - "PUBLISH_SESSION.md query handles NULL and empty-string wp_post_id"
  - "Ghost 0-byte content.db at agents/main deleted permanently"
  - "content.db data clean (no empty-string wp_post_id values)"
affects: [48-02, content-pipeline-cron]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Defensive SQL: (col IS NULL OR col = '') for nullable text columns"]

key-files:
  created: []
  modified:
    - "~/clawd/agents/main/PUBLISH_SESSION.md (EC2)"
    - "~/clawd/agents/ezra/PUBLISH_SESSION.md (EC2)"
    - "~/clawd/content.db (EC2, data cleanup)"

key-decisions:
  - "Fixed both main AND ezra PUBLISH_SESSION.md copies for consistency"
  - "Ran data cleanup UPDATE even though 0 rows affected (belt and suspenders)"

patterns-established:
  - "Defensive NULL-or-empty-string pattern for SQLite text columns"

requirements-completed: [BUG-01]

# Metrics
duration: 2min
completed: 2026-03-03
---

# Phase 48 Plan 01: EC2 Pipeline Fix Summary

**Fixed PUBLISH_SESSION.md SQL query to handle both NULL and empty-string wp_post_id, deleted ghost 0-byte content.db at agents/main path**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-03T02:21:43Z
- **Completed:** 2026-03-03T02:23:53Z
- **Tasks:** 2
- **Files modified:** 3 (on EC2: 2 PUBLISH_SESSION.md files + 1 ghost file deleted)

## Accomplishments
- PUBLISH_SESSION.md query in both main and ezra workspaces now uses `(wp_post_id IS NULL OR wp_post_id = '')` instead of `wp_post_id IS NULL`
- Verified 0 articles have empty-string wp_post_id in content.db (data was already clean)
- Deleted ghost 0-byte content.db at ~/clawd/agents/main/ -- confirmed it does not reappear after gateway restart
- Gateway service confirmed active after restart

## Task Commits

All changes were EC2-side (SSH operations). No local repo file changes per task -- this is a planning/docs repo.

1. **Task 1: Fix PUBLISH_SESSION.md SQL query and clean content.db data** - EC2 SSH operation (sed + sqlite3)
2. **Task 2: Delete ghost content.db file and verify it stays deleted** - EC2 SSH operation (rm + systemctl restart)

**Plan metadata:** (will be committed with this SUMMARY.md)

## Files Created/Modified
- `~/clawd/agents/main/PUBLISH_SESSION.md` (EC2) - Fixed SQL query pattern for publish-check cron
- `~/clawd/agents/ezra/PUBLISH_SESSION.md` (EC2) - Same fix applied to ezra's copy for consistency
- `~/clawd/agents/main/content.db` (EC2) - Deleted ghost 0-byte file permanently

## Decisions Made
- **Fixed ezra's copy too:** Plan only specified main workspace, but ezra's PUBLISH_SESSION.md had the same vulnerable query. Fixed both for consistency (deviation Rule 2).
- **Data cleanup returned 0 rows:** The `UPDATE articles SET wp_post_id = NULL WHERE wp_post_id = ''` affected 0 rows -- data was already clean. Ran anyway for verification certainty.
- **Bind-mount config confirmed correct:** Docker binds point to `~/clawd/content.db:/workspace/content.db:rw` (not the agents/main path), confirming ghost file will not be recreated.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Fixed ezra PUBLISH_SESSION.md copy**
- **Found during:** Task 1 (SQL query fix)
- **Issue:** Plan only specified fixing main workspace copy, but ezra's PUBLISH_SESSION.md had the identical vulnerable query
- **Fix:** Applied same sed replacement to ~/clawd/agents/ezra/PUBLISH_SESSION.md
- **Files modified:** ~/clawd/agents/ezra/PUBLISH_SESSION.md (EC2)
- **Verification:** grep confirmed `(wp_post_id IS NULL OR wp_post_id = '')` in both files
- **Committed in:** EC2 SSH operation (no local commit)

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** Minimal -- fixed the same bug in a second copy of the same file. No scope creep.

## Issues Encountered
None -- all operations succeeded on first attempt.

## User Setup Required
None - no external service configuration required.

## Verification Results

All 4 verification checks passed:

1. `grep "wp_post_id IS NULL OR wp_post_id = ''" ~/clawd/agents/main/PUBLISH_SESSION.md` -- MATCH found
2. `sqlite3 ~/clawd/content.db "SELECT COUNT(*) FROM articles WHERE wp_post_id = '';"` -- returned 0
3. `ls ~/clawd/agents/main/content.db` -- "No such file or directory" (ghost gone)
4. `systemctl --user is-active openclaw-gateway` -- "active"

## Next Phase Readiness
- BUG-01 fully resolved -- publish-check cron will now find articles with either NULL or empty-string wp_post_id
- Ready for 48-02 (verification backfill for phases 43-45 + REQUIREMENTS.md update)

## Self-Check: PASSED

- FOUND: 48-01-SUMMARY.md
- FOUND: commit d08e97b
- EC2 verified: SQL query fixed, ghost file gone, gateway active

---
*Phase: 48-pipeline-fix-verification-backfill*
*Completed: 2026-03-03*

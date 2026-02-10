---
phase: 18-pipeline-monitoring
plan: 02
subsystem: ops
tags: [sqlite, cron, monitoring, sentinel, stuck-detection, slack-alerts]

# Dependency graph
requires:
  - phase: 18-01
    provides: "Sentinel ops agent pattern (PIPELINE_REPORT.md + cron targeting ops)"
  - phase: 12-01
    provides: "content.db schema with topics, articles, social_posts tables"
provides:
  - "STUCK_DETECTION.md reference doc with SQL queries for 4 stuck-item categories"
  - "Daily stuck-check cron job targeting Sentinel (ops) at 9 AM PT"
  - "Silent-skip alerting pattern (no noise when pipeline is healthy)"
affects: [ops, content-pipeline]

# Tech tracking
tech-stack:
  added: []
  patterns: ["stuck-detection with age thresholds", "silent-skip alerting (no-news-is-good-news)"]

key-files:
  created:
    - /home/ubuntu/clawd/agents/ops/STUCK_DETECTION.md
  modified:
    - /home/ubuntu/.openclaw/cron/jobs.json

key-decisions:
  - "Age thresholds: researching >3d, writing >5d, review >3d, revision >5d, approved >7d, social draft >7d"
  - "Alerts to #content-pipeline (not #ops) so content agents see bottlenecks directly"
  - "Silent-skip pattern: no Slack post when nothing is stuck"

patterns-established:
  - "Stuck detection via SQL age threshold queries in reference doc"
  - "Silent-skip alerting: only post when action needed, zero noise otherwise"

# Metrics
duration: 2min
completed: 2026-02-10
---

# Phase 18 Plan 02: Stuck Detection Summary

**Daily stuck-item detection via Sentinel ops agent with SQL age-threshold queries across topics, articles, and social posts, alerting #content-pipeline only when bottlenecks found**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-10T01:10:16Z
- **Completed:** 2026-02-10T01:12:52Z
- **Tasks:** 2
- **Files modified:** 2 (on EC2) + 1 local (plan frontmatter fix)

## Accomplishments
- Deployed STUCK_DETECTION.md to Sentinel with SQL queries covering 4 stuck-item categories (topics, articles, social posts, social drafts)
- Created stuck-check cron job firing daily at 9 AM PT targeting ops agent with sonnet model
- Implemented silent-skip pattern: no alert noise when pipeline is healthy
- All queries use embedded-mode host paths (no /workspace/ sandbox paths)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create STUCK_DETECTION.md reference doc** - `11f478c` (feat)
2. **Task 2: Create daily stuck-check cron job** - EC2-only deployment (cron add + jobs.json patch + gateway restart)

**Plan metadata:** [pending] (docs: complete stuck-detection plan)

## Files Created/Modified
- `/home/ubuntu/clawd/agents/ops/STUCK_DETECTION.md` - Reference doc with SQL queries for 4 stuck-item categories, age thresholds, alert format, and silent-skip instructions
- `/home/ubuntu/.openclaw/cron/jobs.json` - Added stuck-check cron entry (sessionTarget=ops, kind=agentTurn, model=sonnet, daily 9 AM PT)

## Decisions Made
- Age thresholds calibrated to pipeline cadence: topics have shorter thresholds (3-5 days) since research should be quick; articles allow longer (5-7 days) for quality writing/review
- Alerts go to #content-pipeline (C0ADWCMU5F0) not #ops, because content agents need to see and act on bottlenecks
- Silent-skip pattern avoids alert fatigue: healthy pipeline = no message
- Schedule at 9 AM PT (17:00 UTC) runs after content agent crons have processed, surfacing issues same day

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- jobs.json structure is `{version, jobs: [...]}` not a flat array -- adjusted patching script accordingly (minor, not a deviation)
- CLI `grep "workspace"` verification found the warning line "never /workspace/ paths" -- acceptable since it's an instruction to avoid sandbox paths, not an actual path reference

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 18 complete: both pipeline monitoring plans deployed (weekly report + daily stuck detection)
- Sentinel now has two monitoring responsibilities: weekly pipeline summary (Sunday 8 AM) and daily stuck check (daily 9 AM)
- Total cron jobs: 18 (stuck-check added)

## Self-Check: PASSED

- FOUND: /home/ubuntu/clawd/agents/ops/STUCK_DETECTION.md (EC2)
- FOUND: stuck-check cron job (EC2)
- FOUND: commit 11f478c (Task 1)
- FOUND: 18-02-SUMMARY.md (local)

---
*Phase: 18-pipeline-monitoring*
*Completed: 2026-02-10*

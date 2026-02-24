---
phase: 33-content-pipeline-improvements
plan: 02
subsystem: content-pipeline
tags: [sqlite, openclaw, cron, bob, workspace-protocol, content-triggers]

# Dependency graph
requires:
  - phase: 12-content-db-agent-setup
    provides: content.db schema with topics, articles, social_posts, pipeline_activity tables
provides:
  - CONTENT_TRIGGERS.md workspace protocol doc for Bob enabling on-demand content creation, research directives, and social post retrieval
affects: [content-pipeline, bob-workspace, cron-triggers]

# Tech tracking
tech-stack:
  added: []
  patterns: [workspace-protocol-doc-pattern, priority-based-topic-queue, on-demand-content-via-sqlite-insert]

key-files:
  created:
    - "~/clawd/agents/main/CONTENT_TRIGGERS.md"
  modified: []

key-decisions:
  - "Bob inserts topics via sqlite3 rather than triggering cron directly -- openclaw binary not available in Docker sandbox"
  - "openclaw cron run IS safe (tested successfully) but not accessible from sandbox -- documented as host-only command"
  - "Priority 1 used for on-demand topics to ensure they are processed before lower-priority backlog items"

patterns-established:
  - "Workspace protocol doc pattern: standing instructions in /workspace/ for Bob DM command handling"
  - "On-demand content trigger: sqlite3 INSERT with priority 1 into content.db topics table"
  - "Social post retrieval: SQL JOIN query against social_posts + articles tables"

requirements-completed: [CP-03, CP-04, CP-05]

# Metrics
duration: 7min
completed: 2026-02-23
---

# Phase 33 Plan 02: On-Demand Content Triggers Summary

**CONTENT_TRIGGERS.md workspace protocol doc enabling Bob to handle "write about X", "research topics about X", and "get social posts for X" DM commands via sqlite3 inserts and queries against content.db**

## Performance

- **Duration:** 7 min
- **Started:** 2026-02-23T20:59:43Z
- **Completed:** 2026-02-23T21:06:53Z
- **Tasks:** 2
- **Files modified:** 1 (created on EC2)

## Accomplishments
- Created CONTENT_TRIGGERS.md (186 lines, 7187 bytes) in Bob's workspace at ~/clawd/agents/main/
- Captured all 6 content pipeline cron job IDs with schedules and agents
- Tested `openclaw cron run` safety -- command works but times out at CLI level; underlying session runs successfully (confirmed via cron runs log showing article written)
- Documented that openclaw binary is NOT bind-mounted into Docker sandbox, so Bob cannot trigger crons directly
- Verified SQL INSERT pattern works against live content.db (inserted test topic, confirmed, cleaned up)
- Verified social post retrieval query returns 3 existing posts (linkedin, twitter, instagram)
- Protocol doc includes pipeline status check queries for "what's in the pipeline?" requests

## Task Commits

Each task was committed atomically:

1. **Task 1: Capture cron IDs and test immediate triggering safety** - Remote work on EC2 (CONTENT_TRIGGERS.md created)
2. **Task 2: Verify Bob can read the protocol doc and test SQL patterns** - Remote verification (SQL patterns validated)

**Plan metadata:** (pending -- will be committed with SUMMARY.md)

_Note: All artifacts are on EC2 (~/clawd/agents/main/CONTENT_TRIGGERS.md). No local repo files were modified by the tasks themselves._

## Files Created/Modified
- `~/clawd/agents/main/CONTENT_TRIGGERS.md` (EC2) - Workspace protocol doc for on-demand content triggers, research directives, social post retrieval, and pipeline status checks

## Decisions Made
- **openclaw cron run safety:** Tested by triggering writing-check manually. The CLI reports "gateway timeout" after 60-120s, but the cron runs log confirms the session ran successfully (Quill wrote a 2,008-word article about drone ROI). The timeout is cosmetic -- the CLI cannot wait for multi-minute agent sessions.
- **Bob cannot trigger crons directly:** The openclaw binary is not bind-mounted into the Docker sandbox (checked agents.defaults.sandbox.docker.binds in openclaw.json). Bob can only insert topics via sqlite3 and let scheduled crons pick them up.
- **Priority 1 for on-demand topics:** Ensures Quill/Vector process user-requested content before lower-priority backlog items.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Corrected `openclaw cron run` syntax**
- **Found during:** Task 1
- **Issue:** Plan specified `openclaw cron run --id <uuid>` but the actual CLI syntax uses a positional argument: `openclaw cron run <id>`
- **Fix:** Tested with correct syntax `openclaw cron run writing-check`; documented correct positional syntax in CONTENT_TRIGGERS.md
- **Verification:** Command successfully triggered a writing session (confirmed via cron runs log)

**2. [Rule 2 - Missing Critical] Added pipeline status check section**
- **Found during:** Task 1
- **Issue:** Users often ask "what's in the pipeline?" -- this common query was not in the plan but is essential for a complete protocol doc
- **Fix:** Added "Pipeline Status Check" section with queries for topic/article counts by status and active articles list
- **Verification:** Queries match the actual content.db schema

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 missing critical)
**Impact on plan:** Both auto-fixes improved correctness and completeness. No scope creep.

## Issues Encountered
- The `openclaw cron run` CLI timeout is a known limitation -- agent sessions take 3-7 minutes but the CLI max timeout is 120s. The session runs fine asynchronously.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Bob now has workspace instructions for on-demand content triggers
- Protocol doc pattern established for future DM command handling
- Social post retrieval ready for use immediately
- Content pipeline can be monitored via status check queries

## Self-Check: PASSED

- FOUND: ~/clawd/agents/main/CONTENT_TRIGGERS.md (EC2)
- FOUND: 33-02-SUMMARY.md (local)

---
*Phase: 33-content-pipeline-improvements*
*Completed: 2026-02-23*

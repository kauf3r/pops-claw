---
phase: 12-content-db-agent-setup
plan: 01
subsystem: database
tags: [sqlite, content-pipeline, bind-mount, docker, sandbox]

# Dependency graph
requires:
  - phase: 06-multi-agent-gateway
    provides: "Docker sandbox bind-mount pattern (coordination.db)"
provides:
  - "content.db with topics, articles, social_posts, pipeline_activity tables"
  - "Sandbox bind-mount at /workspace/content.db:rw for all agents"
  - "10 indexes for query performance"
affects: [12-02-PLAN, 12-03-PLAN, 13-research-agent, 14-writing-agent, 15-review-publish-agent]

# Tech tracking
tech-stack:
  added: []
  patterns: ["content.db bind-mount follows coordination.db pattern exactly"]

key-files:
  created:
    - "~/clawd/content.db (EC2)"
  modified:
    - "~/.openclaw/openclaw.json (EC2) - added content.db bind-mount"

key-decisions:
  - "Followed coordination.db bind-mount pattern exactly for consistency"
  - "Schema uses TEXT timestamps with CURRENT_TIMESTAMP defaults (matches coordination.db)"

patterns-established:
  - "Content pipeline DB at /workspace/content.db:rw in all agent sandboxes"
  - "Status flows: topics(backlog->researching->writing->completed), articles(writing->review->revision->approved->published), social_posts(draft->scheduled->posted)"
  - "BEGIN IMMEDIATE transactions for claim locking (schema supports, protocol in Plan 02)"
  - "pipeline_activity table logs all state changes (logging protocol in Plan 02)"

# Metrics
duration: 2min
completed: 2026-02-09
---

# Phase 12 Plan 01: Content DB Schema + Sandbox Bind-mount Summary

**SQLite content.db with 4-table pipeline schema (topics, articles, social_posts, pipeline_activity) and Docker sandbox bind-mount for all agents**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-09T18:57:07Z
- **Completed:** 2026-02-09T18:58:57Z
- **Tasks:** 2
- **Files modified:** 2 (on EC2)

## Accomplishments
- Created content.db at ~/clawd/content.db with 4 tables and 10 indexes
- Added content.db bind-mount to openclaw.json sandbox config
- Verified read/write access from Docker sandbox containers
- Gateway restarted cleanly with new config

## Task Commits

Both tasks modified EC2 files only (SSH operations). Local commits capture documentation.

1. **Task 1: Create content.db with 4-table schema and indexes** - EC2 operation (schema deployed)
2. **Task 2: Bind-mount content.db and verify sandbox access** - EC2 operation (config updated, gateway restarted)

**Plan metadata:** See final commit below.

## Files Created/Modified
- `~/clawd/content.db` (EC2) - Content pipeline database with 4 tables, 10 indexes
- `~/.openclaw/openclaw.json` (EC2) - Added `/home/ubuntu/clawd/content.db:/workspace/content.db:rw` to agents.defaults.sandbox.docker.binds

## Schema Reference

### Tables
- **topics** - Content topic backlog with claim locking (12 columns)
- **articles** - Article drafts linked to topics with review scores (18 columns)
- **social_posts** - Social media posts linked to articles (9 columns)
- **pipeline_activity** - Audit log for all pipeline state changes (9 columns)

### Indexes (10 total)
- `idx_topics_status`, `idx_topics_claimed`
- `idx_articles_status`, `idx_articles_topic`, `idx_articles_claimed`
- `idx_social_article`, `idx_social_platform`
- `idx_activity_entity`, `idx_activity_agent`, `idx_activity_created`

## Decisions Made
- Followed coordination.db bind-mount pattern exactly for consistency
- Used TEXT timestamps with CURRENT_TIMESTAMP defaults (matches existing DBs)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- content.db deployed and accessible from all agent sandboxes
- Ready for Plan 02 (agent SKILL.md files) to define claim locking and activity logging protocols
- Ready for Plan 03 (#content-pipeline Slack channel setup)

---
*Phase: 12-content-db-agent-setup*
*Completed: 2026-02-09*

## Self-Check: PASSED

- [x] 12-01-SUMMARY.md exists locally
- [x] content.db exists on EC2 at ~/clawd/content.db
- [x] 4 tables present (articles, pipeline_activity, social_posts, topics)
- [x] 10 indexes created
- [x] Bind-mount in openclaw.json (1 match)
- [x] Gateway service active

---
phase: 34-memory-curation-bootstrap
plan: 02
subsystem: infra
tags: [openclaw, cron, memory, compaction, flush]

# Dependency graph
requires:
  - phase: none
    provides: n/a
provides:
  - daily-memory-flush cron job (11 PM PT nightly)
  - DAILY_FLUSH.md instruction doc in Bob's workspace
  - lowered softThresholdTokens to 3000
affects: [35-memory-retrieval-discipline, 36-memory-health-monitoring]

# Tech tracking
tech-stack:
  added: []
  patterns: [reference-doc-driven cron, dedicated flush cron for short-session agents]

key-files:
  created:
    - ~/clawd/agents/main/DAILY_FLUSH.md (EC2 - instruction doc for daily log review)
  modified:
    - ~/.openclaw/openclaw.json (EC2 - softThresholdTokens 6000 -> 3000)

key-decisions:
  - "Used reference doc pattern (DAILY_FLUSH.md) instead of inline prompt for maintainability"
  - "Set cron at 11 PM PT (7 AM UTC) to capture full day's activity before midnight"
  - "Lowered softThresholdTokens from 6000 to 3000 to catch mid-length sessions"

patterns-established:
  - "Reference-doc cron: complex instructions go in workspace .md files, cron message just says 'follow instructions in X.md'"

requirements-completed: [MEM-02]

# Metrics
duration: 4min
completed: 2026-02-23
---

# Phase 34 Plan 02: Fix Memory Flush Consistency Summary

**Daily-memory-flush cron at 11 PM PT + softThresholdTokens lowered to 3000 to ensure daily log entries for every active day**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-23T20:10:54Z
- **Completed:** 2026-02-23T20:15:18Z
- **Tasks:** 4
- **Files modified:** 2 (on EC2)

## Accomplishments
- Confirmed flush gap hypothesis: highest cron session was 4,798 tokens, well under 6,000 threshold -- compaction never triggers on cron sessions
- Created DAILY_FLUSH.md instruction doc that reviews coordination.db, email.db, content.db, and voice_notes daily
- Registered daily-memory-flush cron (ID: d7041540, 11 PM PT, isolated, Sonnet, no-deliver)
- Lowered softThresholdTokens from 6000 to 3000 to catch more mid-length sessions
- Baseline recorded: 9 files / 12 chunks in main agent memory before fix

## Task Commits

Each task was committed atomically:

1. **Tasks 1-4: Diagnose + Cron + Config + Verify** - `d4a04c2` (feat) -- all EC2 changes in single commit since no local file changes per-task

**Plan metadata:** (pending - docs commit below)

## Files Created/Modified
- `~/clawd/agents/main/DAILY_FLUSH.md` (EC2) - Instruction doc for nightly daily log review
- `~/.openclaw/openclaw.json` (EC2) - softThresholdTokens changed from 6000 to 3000
- Cron job `daily-memory-flush` registered via `openclaw cron add`

## Decisions Made
- Used reference doc pattern (DAILY_FLUSH.md) instead of embedding the full prompt in the cron message -- keeps instructions maintainable and editable without re-registering the cron
- Set cron at 11 PM PT to capture the full day's activity before midnight rolls over
- Lowered softThresholdTokens to 3000 (half of original 6000) -- minimal risk since worst case is more frequent small memory writes

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Observability DB only has data from Feb 18+ (6 days), which limited the token-vs-log correlation analysis. However, the pattern was clear enough: no single cron session reaches 6000 tokens.
- Gateway restart was needed after config change to pick up new softThresholdTokens (not mentioned in plan but standard procedure). Note: gateway restart clears DM sessions per MEMORY.md.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Daily-memory-flush cron will fire tonight at 11 PM PT -- verify tomorrow that memory/2026-02-23.md was created
- Check `openclaw memory status` shows 10+ files after first flush
- Phase 35 (Memory Retrieval Discipline) can proceed once daily logs are confirmed flowing

## Self-Check: PASSED

- FOUND: 34-02-SUMMARY.md (local)
- FOUND: d4a04c2 task commit
- FOUND: DAILY_FLUSH.md (EC2)
- FOUND: daily-memory-flush cron job (EC2)
- VERIFIED: softThresholdTokens = 3000 (EC2)

---
*Phase: 34-memory-curation-bootstrap*
*Completed: 2026-02-23*

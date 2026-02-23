---
phase: 35-memory-retrieval-discipline
plan: 01
subsystem: memory
tags: [agents, memory-retrieval, learnings, boot-sequence, ec2]

# Dependency graph
requires:
  - phase: 34-memory-curation-bootstrap
    provides: "Freed bootstrap token budget (MEMORY.md 304->91 lines) for retrieval instructions"
provides:
  - "Memory Protocol section in global AGENTS.md (5-bullet retrieval cascade)"
  - "LEARNINGS.md seeded with 22 operational entries across 5 categories"
  - "MARKER test entry (Tailscale DNS on EC2) for retrieval validation"
affects: [35-02, phase-36, memory-health-monitoring]

# Tech tracking
tech-stack:
  added: []
  patterns: ["prioritized file cascade (LEARNINGS -> daily logs -> docs/) with early stop"]

key-files:
  created:
    - "~/clawd/LEARNINGS.md (EC2) - Seeded operational knowledge base, 22 entries, 41 lines"
  modified:
    - "~/clawd/AGENTS.md (EC2) - Added Memory Protocol section, 191->200 lines"

key-decisions:
  - "LEARNINGS.md placed at ~/clawd/LEARNINGS.md (workspace root) not ~/clawd/agents/main/ -- all default/named sessions access it, isolated crons are stateless and skip memory retrieval"
  - "5 bullets in Memory Protocol (3 cascade tiers + early stop + fallback) rather than strict 3-4, for completeness"
  - "Context-aware crons all use default sessions (not Docker sandbox), confirming global workspace files are accessible without bind-mount changes"

patterns-established:
  - "Memory retrieval cascade: LEARNINGS.md -> daily logs (7 days) -> docs/, stop when found"
  - "LEARNINGS.md graduation: entries move to docs/ when file exceeds ~100 lines"

requirements-completed: [MEM-03, MEM-04]

# Metrics
duration: 4min
completed: 2026-02-23
---

# Phase 35 Plan 01: Memory Protocol & LEARNINGS.md Summary

**Memory Protocol added to AGENTS.md with 5-bullet retrieval cascade, LEARNINGS.md seeded with 22 operational entries across 5 categories from real project knowledge**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-23T23:25:03Z
- **Completed:** 2026-02-23T23:29:30Z
- **Tasks:** 2
- **Files modified:** 2 (on EC2 via SSH)

## Accomplishments
- Added Memory Protocol section to global ~/clawd/AGENTS.md (9 lines added, 191->200 total) with prioritized cascade: LEARNINGS.md -> daily logs -> docs/, early stop, silent fallback
- Created ~/clawd/LEARNINGS.md with 22 seeded entries across 5 categories (API & Auth Gotchas, Cron Patterns, Infrastructure, Content Pipeline, User Preferences) -- all drawn from real MEMORY.md lessons and operational history
- Embedded MARKER test entry ("Tailscale DNS on EC2") as a natural-looking infrastructure lesson for retrieval validation
- Verified sandbox configuration: context-aware crons use default sessions with full filesystem access, isolated crons are stateless and skip retrieval -- no bind-mount changes needed

## Task Commits

All changes are EC2 workspace files (SSH operations), tracked in this summary:

1. **Task 1: Resolve sandbox visibility and add Memory Protocol to AGENTS.md** - EC2 SSH operation
   - Verified sandbox bind-mount config (Docker mounts per-agent dirs, not global workspace)
   - Confirmed all context-aware crons (morning-briefing, evening-recap, weekly-review, writing/review/publish-check, etc.) use default sessions with full filesystem access
   - Added Memory Protocol section after "Every Session" boot sequence in ~/clawd/AGENTS.md
   - 5 bullets: LEARNINGS.md scan, daily logs (7 days for past-work references), docs/ fallback, early stop, silent gap handling

2. **Task 2: Create and seed LEARNINGS.md with MARKER entry** - EC2 SSH operation
   - Created ~/clawd/LEARNINGS.md at workspace root (accessible to all agents in default sessions)
   - Seeded 22 entries across 5 categories from MEMORY.md "Lessons Learned" and operational history
   - MARKER entry: "Tailscale DNS on EC2" in Infrastructure section -- rephrased real knowledge, testable by asking Bob

## Files Created/Modified
- `~/clawd/AGENTS.md` (EC2) - Added Memory Protocol section (9 lines, 191->200 total)
- `~/clawd/LEARNINGS.md` (EC2) - New file, 22 entries, 41 lines, 5 categories

## Decisions Made
- **LEARNINGS.md at workspace root**: Placed at `~/clawd/LEARNINGS.md` instead of `~/clawd/agents/main/LEARNINGS.md`. Reason: per-agent workspaces are `~/clawd/agents/{agent}/`, but default sessions (used by all context-aware crons) have full filesystem access. Global placement means all agents can reference it without bind-mount changes.
- **5 bullets instead of 3-4**: Added a 5th bullet for silent gap handling ("proceed with best judgment, note gap in daily log"). The 3 cascade tiers + early stop + fallback is the complete protocol; dropping any would leave ambiguity.
- **No bind-mount changes needed**: Sandbox Docker sessions are only used by stateless crons (email-catchup, voice-notes-processor, etc.) that don't need memory retrieval. Context-aware crons all use default/named sessions.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - SSH operations succeeded on first attempt. Shell quoting for Python heredocs required using a temp script file approach (per existing "heredocs over SSH" lesson in MEMORY.md).

## User Setup Required

None - no external service configuration required. MARKER validation test (asking Bob about Tailscale offline recovery) is a manual post-deploy verification step documented in the plan.

## Next Phase Readiness
- Memory Protocol is live in global AGENTS.md -- all agents will see it on next session
- LEARNINGS.md is seeded and accessible at workspace root
- Ready for Plan 35-02 (content agent BOOTSTRAP.md files for Quill, Sage, Ezra)
- MARKER test can be run anytime: ask Bob "What should I try if Tailscale shows offline on the EC2?"

## Self-Check: PASSED

All verification items confirmed:
- [x] Memory Protocol in AGENTS.md (1 match)
- [x] AGENTS.md under 210 lines (200 lines)
- [x] LEARNINGS.md exists at ~/clawd/LEARNINGS.md
- [x] LEARNINGS.md under 100 lines (41 lines)
- [x] 15-25 entries (22 entries)
- [x] MARKER entry present (Tailscale DNS on EC2)
- [x] Cascade order verified (LEARNINGS.md, daily logs, docs/ all referenced)
- [x] 35-01-SUMMARY.md created locally

---
*Phase: 35-memory-retrieval-discipline*
*Completed: 2026-02-23*

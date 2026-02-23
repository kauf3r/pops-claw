---
phase: 34-memory-curation-bootstrap
plan: 01
subsystem: memory
tags: [memory, observability, token-optimization, ec2]

# Dependency graph
requires:
  - phase: none
    provides: first phase of v2.6
provides:
  - Curated MEMORY.md (91 lines, under 150 budget)
  - Reference docs directory ~/clawd/docs/ (8 files)
  - Token consumption baseline and post-curation measurement
affects: [35-memory-retrieval-discipline, 36-memory-health-monitoring]

# Tech tracking
tech-stack:
  added: []
  patterns: [memory-curation-to-docs-dir, token-baseline-measurement]

key-files:
  created:
    - ~/clawd/docs/INSIGHT_UP.md
    - ~/clawd/docs/SAFETY_DOC_GEN.md
    - ~/clawd/docs/CA66_GENERATOR.md
    - ~/clawd/docs/CLAUDE_LIFE_OS.md
    - ~/clawd/docs/VOICE_MEMORY_APP.md
    - ~/clawd/docs/READICCULUS.md
    - ~/clawd/docs/NEGOTIATION.md
    - ~/clawd/docs/CANVA.md
  modified:
    - ~/clawd/MEMORY.md

key-decisions:
  - "MEMORY.md cut to 91 lines (below 120-140 target) -- leaves room for organic growth without hitting 150"
  - "Included Reference Docs index section in MEMORY.md so Bob knows where moved content lives"
  - "Backed up original MEMORY.md as MEMORY.md.bak-20260223 before overwrite"

patterns-established:
  - "Reference docs in ~/clawd/docs/ -- not indexed, retrievable on demand"
  - "Token baseline measurement via observability.db before/after changes"

requirements-completed: [MEM-01]

# Metrics
duration: 7min
completed: 2026-02-23
---

# Phase 34 Plan 01: Curate MEMORY.md Under Budget Summary

**MEMORY.md trimmed from 304 to 91 lines, 8 reference docs moved to ~/clawd/docs/, 25% reduction in avg session input tokens**

## Performance

- **Duration:** 7 min
- **Started:** 2026-02-23T20:10:51Z
- **Completed:** 2026-02-23T20:18:05Z
- **Tasks:** 5
- **Files modified:** 9 (1 modified + 8 created on EC2)

## Accomplishments
- Baselined 7-day token consumption: 1,611 calls, avg 86K total input, $15.97 cost
- Created 8 reference doc files in ~/clawd/docs/ from sections moved out of MEMORY.md
- Rewrote MEMORY.md from 304 lines to 91 lines (70% reduction)
- Deleted stale sections: session logs (Jan 25+29), skills created, birthday
- Reindexed memory: 9/9 files, 12 chunks, clean, no dirty state
- Post-curation main session avg total input dropped from 82,630 to 62,064 tokens (~25% reduction)

## Task Commits

All 5 tasks were EC2 SSH operations with a single local commit:

1. **Task 1: Baseline Token Consumption** - `2411ca0` (feat)
2. **Task 2: Create docs/ and Move Reference Material** - `2411ca0` (feat)
3. **Task 3: Curate MEMORY.md** - `2411ca0` (feat)
4. **Task 4: Reindex Memory and Verify** - `2411ca0` (feat)
5. **Task 5: Measure Post-Curation Token Consumption** - `2411ca0` (feat)

## Files Created/Modified
- `~/clawd/MEMORY.md` - Curated from 304 to 91 lines (operational essentials only)
- `~/clawd/docs/INSIGHT_UP.md` - UAV solutions website reference
- `~/clawd/docs/SAFETY_DOC_GEN.md` - Mission safety briefing generator reference
- `~/clawd/docs/CA66_GENERATOR.md` - Airport agreement generator reference
- `~/clawd/docs/CLAUDE_LIFE_OS.md` - Personal knowledge base reference
- `~/clawd/docs/VOICE_MEMORY_APP.md` - Voice analysis platform reference
- `~/clawd/docs/READICCULUS.md` - Event project reference
- `~/clawd/docs/NEGOTIATION.md` - Compensation strategy reference
- `~/clawd/docs/CANVA.md` - Canva integration reference

## Token Consumption Data

### Pre-Curation Baseline (7-day, main agent)

| Metric | Value |
|--------|-------|
| Total calls | 1,611 |
| Avg total input (main session) | 82,630 tokens |
| Peak total input (main session) | 701,192 tokens |
| Avg cache read | 86,009 tokens |
| 7-day cost | $15.97 |

### Post-Curation (fresh session after restart)

| Metric | Value |
|--------|-------|
| Prompt tokens (test call) | 36,539 |
| System prompt chars | 25,641 (projectContext: 9,976) |
| Avg total input (main session) | 62,064 tokens |
| Peak total input (main session) | 176,089 tokens |
| Reduction | ~25% avg input per call |

### Memory Index (post-curation)

| Agent | Files | Chunks | Status |
|-------|-------|--------|--------|
| main | 9/9 | 12 | Clean |
| landos | 14/14 | 29 | Clean |
| rangeos | 12/12 | 71 | Clean |
| ops | 12/12 | 50 | Clean |

## Decisions Made
- Cut MEMORY.md to 91 lines (below 120-140 target) to leave room for organic growth
- Added "Reference Docs" section to MEMORY.md pointing to ~/clawd/docs/ so Bob can find moved content
- Backed up original as MEMORY.md.bak-20260223

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- `observability.db` exists at multiple paths; the one with actual data is `~/clawd/agents/main/observability.db` (not `~/.openclaw/agents/main/observability.db` which is 0 bytes)
- `openclaw send` command does not exist; used `openclaw agent --agent main --message` instead for test session

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- MEMORY.md is under budget (91 lines), ready for Phase 35 retrieval discipline additions
- Token baseline documented for future comparison
- Memory index clean, no blockers

## Self-Check: PASSED

- All 9 EC2 files verified (8 docs + MEMORY.md)
- MEMORY.md line count: 91 (under 150 budget)
- Commit 2411ca0 verified in git log
- 34-01-SUMMARY.md exists locally

---
*Phase: 34-memory-curation-bootstrap*
*Completed: 2026-02-23*

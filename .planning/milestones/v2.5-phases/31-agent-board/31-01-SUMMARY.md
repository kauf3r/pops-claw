---
phase: 31-agent-board
plan: 01
subsystem: api, dashboard
tags: [better-sqlite3, next-api-routes, agent-monitoring, token-aggregation]

# Dependency graph
requires:
  - phase: 30-01
    provides: getDb singleton factory, AGENTS constant, query module pattern, force-dynamic API route pattern
provides:
  - getAgentBoardData() returning AgentBoardSummary with 7 agents, 5-min/30-min status thresholds
  - GET /api/agents endpoint returning per-agent heartbeat, token, and error data
  - formatTokens, MODEL_LABELS, formatModelBreakdown token formatting utilities
  - NavBar updated with Agents link
affects: [31-02-agent-board-page]

# Tech tracking
tech-stack:
  added: []
  patterns: [cross-db-agent-query-with-alias, input-output-only-token-aggregation, status-threshold-5min-30min]

key-files:
  created:
    - src/app/api/agents/route.ts
  modified:
    - src/lib/queries/agents.ts
    - src/lib/utils.ts
    - src/components/NavBar.tsx

key-decisions:
  - "Use input+output tokens only (not cache) for headline token counts -- cache tokens are 100x larger and not actionable for workload monitoring"
  - "Query both 'main' and 'bob' agent_ids for main agent across all databases (coordination and observability)"
  - "Separate /api/agents route rather than extending existing /api/dashboard/agents to avoid changing Phase 30 contract"

patterns-established:
  - "Agent ID aliasing: main agent queries use IN ('main', 'bob') for both coordination.db and observability.db"
  - "Token formatting: formatTokens (12.4k/1.2M) and formatModelBreakdown (H: 8k . S: 3k) as shared utilities"

requirements-completed: [AGNT-01, AGNT-02, AGNT-03, AGNT-04]

# Metrics
duration: 5min
completed: 2026-02-21
---

# Phase 31 Plan 01: Agent Board Data Layer Summary

**Per-agent query module with 5-min/30-min status thresholds, 24h input+output token aggregation by model, cross-DB heartbeat merging, and /api/agents endpoint returning 7 agents**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-21T16:55:28Z
- **Completed:** 2026-02-21T17:00:50Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Built getAgentBoardData() querying coordination.db and observability.db with bob/main alias handling across all queries
- Created /api/agents returning 7 agents with status, 24h token usage by model, and error counts
- Added formatTokens, MODEL_LABELS, and formatModelBreakdown utilities for compact token display
- Updated NavBar with Agents link between Dashboard and Calendar

## Task Commits

Each task was committed atomically:

1. **Task 1: Create agent board query module and token formatting utilities** - `31588e3` (feat)
2. **Task 2: Create /api/agents route and add Agents link to NavBar** - `0e37460` (feat)

## Files Created/Modified
- `src/lib/queries/agents.ts` - Added getAgentBoardData() alongside existing getAgentHealth(), with 5-min/30-min thresholds and bob/main aliasing
- `src/lib/utils.ts` - Added formatTokens, MODEL_LABELS, formatModelBreakdown for compact token display
- `src/app/api/agents/route.ts` - GET handler returning AgentBoardSummary with force-dynamic pattern
- `src/components/NavBar.tsx` - Added Agents link between Dashboard and Calendar

## Decisions Made
- Used input+output tokens only (not cache) for headline token counts. Cache tokens (cache_read + cache_write) are 100x larger than input+output and represent context reuse, not new generation. Main/Bob 24h: input+output = ~460k vs cache = ~52M.
- Query both "main" and "bob" agent_ids for the main agent in ALL queries (lastSeen, tokens, errors) -- not just coordination.db. The observability.db may also have entries under either ID.
- Created separate /api/agents route rather than extending /api/dashboard/agents to keep Phase 30 contract stable.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required. API endpoint live at http://100.72.143.9:3001/api/agents.

## Next Phase Readiness
- /api/agents returns correctly shaped JSON with all 7 agents, verified with curl
- Token formatting utilities ready for use in agent card components
- NavBar already shows Agents link (will route to /agents page built in Plan 02)
- Plan 02 can build the /agents page purely from this data layer

## Self-Check: PASSED

- 31-01-SUMMARY.md: FOUND
- Commit 31588e3 (Task 1): FOUND on EC2
- Commit 0e37460 (Task 2): FOUND on EC2

---
*Phase: 31-agent-board*
*Completed: 2026-02-21*

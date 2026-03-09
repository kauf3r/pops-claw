# Phase 53: Retrieval Protocol & Flush Scheduling - Context

**Gathered:** 2026-03-08
**Status:** Ready for planning
**Source:** Auto-generated from ROADMAP.md and REQUIREMENTS.md

<domain>
## Phase Boundary

Add search-before-acting retrieval protocol to AGENTS.md so Bob checks memory before answering recurring topics. Reschedule daily memory flush cron to 23:00 UTC (end of day PT) for better session summaries. No MEMORY.md changes (Phase 52), no health monitoring (Phase 54).

</domain>

<decisions>
## Implementation Decisions

### Retrieval Protocol
- Add to existing AGENTS.md (append new section, preserve Operator Mindset)
- Specific trigger categories: preferences, history, project context
- Include example queries for each trigger category
- Consequence clause: "If unsure about user preference, search memory first"

### Flush Scheduling
- Current flush happens during compaction (threshold-based, not time-based)
- Need a dedicated cron job at 23:00 UTC to trigger daily flush
- Use openclaw cron system for scheduling
- Preserve existing compaction-triggered flush as backup

### Claude's Discretion
- Exact wording of retrieval protocol triggers
- How to add cron via openclaw CLI vs direct config edit
- Whether to add LEARNINGS.md stub or defer entirely

</decisions>

<deferred>
## Deferred Ideas

- LEARNINGS.md content seeding — can create stub but Phase 53 scope is protocol only
- Multi-agent retrieval protocols — Bob only for v2.9
- Automated memory quality scoring — Phase 54

</deferred>

---

*Phase: 53-retrieval-protocol-flush-scheduling*
*Context gathered: 2026-03-08*

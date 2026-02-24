# Phase 36: Memory Health Monitoring - Context

**Gathered:** 2026-02-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Add a memory health panel to Mission Control's /memory page showing per-agent memory system health at a glance. Covers chunk counts, line budget usage, last-updated timestamps, and flush frequency trends. Uses existing 30s SWR polling — no new infrastructure.

</domain>

<decisions>
## Implementation Decisions

### Panel layout & placement
- Lives on the existing /memory page as a new section/tab — memory health belongs alongside memory content
- Card-per-agent grid layout — one compact card per agent, scannable like Linear's board view
- Health status indicator leads each card — problems visible instantly before reading details

### Health indicators
- Colored dot + text label: green "Healthy" / yellow "Warning" / red "Critical"
- Warning threshold: MEMORY.md over 160 lines (80% of 200-line budget)
- Critical threshold: MEMORY.md over 190 lines (95% of 200-line budget)
- Separate "stale" badge if no memory flush in 3+ days — independent from the main health dot (staleness is a different concern than budget usage)

### Budget visualization
- Horizontal progress bar showing fill level, with "142/200 lines" fraction text
- Bar color shifts green→yellow→red at the 80%/95% thresholds
- Chunk count shown as secondary text below the progress bar ("12 chunks")
- Last-updated timestamp in relative format ("Updated 3h ago") with exact datetime on hover/tooltip

### Trend display
- Mini sparkline: 7-bar chart showing flushes per day over the last 7 days
- A "flush" = any MEMORY.md git commit (simple, directly observable, no new instrumentation)
- Read-only — no click-to-expand or drill-down. The sparkline tells the story.

### Claude's Discretion
- Exact card dimensions and spacing
- Sparkline rendering approach (SVG, canvas, or CSS)
- How to collect git commit data (API endpoint design)
- Card grid responsive breakpoints
- Empty state if an agent has no memory files

</decisions>

<specifics>
## Specific Ideas

- Cards should feel like Linear's issue cards — clean, compact, scannable
- Health dot is the fastest signal — you should be able to tell if anything needs attention in under 2 seconds
- The progress bar is the actionable detail — "how close to budget am I?"
- Sparkline shows activity patterns — is this agent's memory being maintained or neglected?

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 36-memory-health-monitoring*
*Context gathered: 2026-02-23*

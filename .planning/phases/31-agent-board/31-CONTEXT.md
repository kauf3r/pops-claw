# Phase 31: Agent Board - Context

**Gathered:** 2026-02-21
**Status:** Ready for planning

<domain>
## Phase Boundary

A dedicated /agents page showing health, workload, and resource usage of all 7 agents (Andy, Scout, Vector, Sentinel, Quill, Sage, Ezra) at a glance. Data comes from coordination.db (heartbeats) and observability.db (tokens, models, errors). No agent management or control actions — view-only monitoring.

</domain>

<decisions>
## Implementation Decisions

### Card layout & grid
- Uniform grid: all 7 cards same size, no hero/featured card
- Responsive columns: 4 on desktop (2 rows), 2 on tablet, 1 on mobile
- All info visible on each card — no expand/collapse, no hover-to-reveal
- Subtle bordered cards with rounded corners
- Status color as thick left border accent (Linear-style)
- Page header: "Agents" title with fleet summary subtitle ("5 active · 1 stale · 1 down")

### Status presentation
- Green = active (seen in last 5 min), Yellow = stale (5-30 min), Red = down (30+ min)
- Relative timestamps ("2m ago", "1h ago") with absolute timestamp on hover tooltip
- Color + text label ("Active" / "Stale" / "Down") for accessibility

### Token & error display
- Total 24h token count as single number (e.g., "12.4k tokens")
- Model breakdown line below: "H: 8k · S: 3k · O: 1.4k" — compact, no charts
- Error count as badge/pill: gray when 0, red when non-zero
- "Last 24 hours" label at page level, not repeated per card

### Agent identity & ordering
- Sort by status priority: Down → Stale → Active, then alphabetical within group
- Agent name shown prominently, role/system as subtitle (e.g., "Scout — landos")
- Uniform card styling — only left border color varies by status, no per-agent accent colors

### Claude's Discretion
- Exact spacing, typography, and card dimensions
- Loading state design
- How to handle agents with no data yet (never seen)
- Dark/neutral background treatment

</decisions>

<specifics>
## Specific Ideas

- Left border accent inspired by Linear's sidebar items — status color as the primary visual signal
- Problems surface to the top via status-priority sorting — you see what needs attention first
- Fleet summary in header gives instant "are we healthy?" answer before scanning individual cards

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 31-agent-board*
*Context gathered: 2026-02-21*

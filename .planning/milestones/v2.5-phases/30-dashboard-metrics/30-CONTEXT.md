# Phase 30: Dashboard & Metrics - Context

**Gathered:** 2026-02-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Landing page that answers "is everything OK?" at a glance. Status cards for all major subsystems (agents, crons, content pipeline, email), a live activity feed replacing the Convex-based feed, pipeline and email metrics, all auto-refreshing via SWR. No new subsystem integrations — reads from existing SQLite databases.

</domain>

<decisions>
## Implementation Decisions

### Status card design
- 4-card grid layout: Agent Health, Cron Success, Content Pipeline, Email Quota
- Each card shows a single headline number with colored dot indicator (green/yellow/red)
- One-line detail beneath the headline number (e.g., "7/7 agents alive", "98% success rate")
- Clean and not busy — no inline breakdowns or expandable sections

### Activity feed style
- Flat chronological list, newest first
- Each entry is one line: icon + timestamp + description
- Color-coded by type: agent=blue, cron=purple, email=green, content=orange
- No grouping by time or type, no nesting — clean log view
- Replaces the existing Convex-based activity feed

### Metrics presentation
- Content pipeline: 4 count badges (researched / written / reviewed / published)
- Email: sent/received/bounced counts + quota usage bar
- Numbers only — no charts, no sparklines
- Simple and scannable

### Refresh & staleness
- Subtle "Updated X seconds ago" text in page header
- Color changes on staleness: normal → yellow after 60s → red after 120s
- No manual refresh button — SWR polling handles everything at 30s intervals
- Auto-refresh is invisible when working normally

### Claude's Discretion
- Exact card dimensions and spacing
- Activity feed pagination approach (infinite scroll vs load more vs fixed window)
- Icon choices for activity types
- Empty state design for each section
- Error state handling when a database is unreachable

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches. The overall vibe is "ops dashboard" — clean, information-dense but not cluttered, like a simplified Datadog or Linear status page.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 30-dashboard-metrics*
*Context gathered: 2026-02-20*

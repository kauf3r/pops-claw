# Phase 32: Memory, Office & Visualization - Context

**Gathered:** 2026-02-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Three new dashboard pages: a memory browser for viewing agent memories, a virtual office showing agent avatars and status, and an analytics page with Recharts visualizations for tokens, content, email, and crons. All pages integrate into existing Mission Control sidebar navigation.

</domain>

<decisions>
## Implementation Decisions

### Memory Browser (/memory)
- Card grid layout — each memory as a card with agent name, timestamp, and 2-3 line content preview (truncated with ellipsis, click to expand)
- Agent filtering via tabs across top — "All" tab + one tab per agent for quick switching
- Search bar at top filters cards live — type to search across all agents' memories, works with active agent tab filter, highlights matching text in cards
- Cards should feel scannable like Notion's database view

### Office View (/office)
- Top-down office floorplan — bird's-eye view with desks arranged in an office layout, isometric-lite feel
- Illustrated character avatars — unique cartoon/illustrated avatar per agent giving each personality
- Activity status: animated green pulse when working, gray/dim when idle. Small badge shows current task type (e.g., "writing", "researching") based on recent heartbeat/action data
- Idle threshold: 5 minutes without heartbeat/action = idle

### Chart Design (/analytics)
- All 4 chart types on one dedicated /analytics page:
  - Token usage: area charts per agent
  - Content pipeline: bar chart by status
  - Email volume: line chart over time
  - Cron success/failure: donut chart
- Color palette: pull from existing Tailwind theme, each agent gets a distinct color
- Default time range: last 7 days with range picker buttons (24h / 7d / 30d)
- Interactivity: hover tooltips showing exact values + time range buttons. No zoom/pan — clean and useful without overbuilding
- Powered by Recharts

### Page Layout & Navigation
- Add Memory, Office, and Analytics as new items in existing sidebar nav
- Nav order: Dashboard, Agents, Memory, Office, Analytics, Calendar
- Consistent page structure: page title, optional subtitle/description, then content area — same header pattern as existing dashboard pages
- Skeleton loaders while data fetches — gray placeholder shapes matching content layout

### Claude's Discretion
- Exact card spacing and typography for memory grid
- Office floorplan desk arrangement and spacing
- Specific Recharts configuration and chart sizing
- Skeleton loader shape details per page
- Empty state messaging

</decisions>

<specifics>
## Specific Ideas

- Memory cards should feel like Notion's database view — scannable, clean
- Office should be fun to look at — the isometric floorplan with illustrated characters makes agent status playful, not just functional
- Charts should be practical, not flashy — tooltips and time range buttons are enough interactivity

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 32-memory-office-visualization*
*Context gathered: 2026-02-21*

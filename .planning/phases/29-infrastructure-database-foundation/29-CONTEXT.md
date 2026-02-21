# Phase 29: Infrastructure & Database Foundation - Context

**Gathered:** 2026-02-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the foundational layer for Mission Control — 5 SQLite database connections (WAL, read-only), Convex removal, shadcn/ui component library, systemd production service, and direct Tailscale access without SSH tunneling. No dashboard content beyond DB connection status cards.

</domain>

<decisions>
## Implementation Decisions

### Dashboard look & feel
- Dark mode by default, with system preference override
- shadcn/ui "zinc" neutral palette with blue accents for primary actions
- No custom branding beyond "Mission Control" in the header — utility-focused aesthetic

### Landing page skeleton
- Minimal shell: header with "Mission Control" title, grid of 5 database connection status cards
- Each card shows DB name, connection status (connected/not initialized), row counts if available
- "System Status" section showing service uptime
- This foundation gets replaced by real dashboard content in Phase 30; DB status cards remain useful as health indicators

### Database error states
- Inline, per-card: yellow "Not Initialized" badge when DB file doesn't exist, with muted explanation ("Database file not found at expected path")
- No full-page warnings — partial availability is expected
- Connected DBs show green badge + last-modified timestamp

### Service & resource limits
- Port 3001, bind to 0.0.0.0 (Tailscale interface)
- `OOMScoreAdjust=500` — gateway and Tailscale survive, dashboard gets killed first
- `NODE_ENV=production` with `next start` (not dev server) for lower memory footprint
- UFW rule: allow 3001 from 100.64.0.0/10 only (Tailscale CGNAT range)

### Claude's Discretion
- Exact shadcn component versions and configuration
- Database singleton implementation pattern
- RelativeTime component approach (date-fns vs custom)
- systemd service file structure and restart policy details

</decisions>

<specifics>
## Specific Ideas

- DB status cards as long-term health indicators, not just Phase 29 placeholders
- Production mode (`next start`) over dev server to respect 2GB RAM constraint on t3.small

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 29-infrastructure-database-foundation*
*Context gathered: 2026-02-20*

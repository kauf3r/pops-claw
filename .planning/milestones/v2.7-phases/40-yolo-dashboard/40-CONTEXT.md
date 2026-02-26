# Phase 40: YOLO Dashboard - Context

**Gathered:** 2026-02-24
**Status:** Ready for planning

<domain>
## Phase Boundary

A new Mission Control page at `/yolo` that displays YOLO build history as interactive cards with status badges, self-scores, descriptions, and tech stack tags. Includes status filtering and auto-refresh via SWR.

</domain>

<decisions>
## Implementation Decisions

### Card design
- Card-based grid layout matching existing Mission Control patterns (shadcn Card component)
- Each card shows: build name, date, status badge (color-coded), self-score (1-5 as filled/empty dots or stars), description snippet, tech stack as small tags, duration, lines of code
- Left border accent per status, matching AgentCard pattern: success=emerald, partial=amber, failed=rose, building/testing=blue, idea=secondary
- Status badge uses existing Badge variants: success, warning, error, secondary
- Cards sorted newest-first by date (default)

### Page layout & filtering
- Standard Mission Control layout: `min-h-screen px-6 py-10`, `max-w-7xl mx-auto`
- Filter bar at top with pill-style buttons: All / Success / Partial / Failed (active state uses `bg-secondary text-foreground`)
- Responsive grid: 1 column mobile, 2 columns md, 3 columns lg
- Add "YOLO" to NavBar links array (with Zap or Rocket icon from lucide-react)

### Status color mapping
- `success` → emerald (Badge variant: success)
- `partial` → amber (Badge variant: warning)
- `failed` → rose (Badge variant: error)
- `building` / `testing` → blue (Badge variant: default/primary)
- `idea` → secondary/muted (Badge variant: secondary)

### Data fetching
- SWR with global 30s refreshInterval (matches existing config, satisfies SC-3)
- API route at `/api/yolo/builds` using better-sqlite3 readonly against yolo.db
- Register yolo.db path in db-paths.ts pointing to `~/clawd/yolo-dev/yolo.db`

### Empty & loading states
- Loading: card skeleton placeholders (3 gray shimmer cards)
- Empty: centered message "No builds yet" with muted text — simple, no illustration needed

### Build detail depth
- Cards show summary at a glance (name, status, score, tech stack tags, date)
- Description truncated to 2 lines on card, no expand/detail view needed for this phase
- build_log and error_log are NOT displayed (too verbose for dashboard cards)

### Claude's Discretion
- Exact card spacing and typography within Mission Control conventions
- Skeleton animation style
- Icon choice for navbar (Zap, Rocket, or similar)
- Whether to show duration as "Xm Ys" or "X min"
- Score visualization (dots, stars, or numeric badge)

</decisions>

<specifics>
## Specific Ideas

- Match the existing dark theme aesthetic — cards should feel consistent with Agent cards and Status cards
- Tech stack tags should be small, pill-shaped, muted color (like secondary badges)
- Self-score is 1-5 — keep it compact, not prominent (small badge or dots)
- Filter should feel like tab navigation, not a dropdown

</specifics>

<deferred>
## Deferred Ideas

- Build detail/expand view with full logs — future phase
- Search by name or tech stack — future phase
- Build comparison (side by side) — future phase
- Triggering new builds from the dashboard — separate capability

</deferred>

---

*Phase: 40-yolo-dashboard*
*Context gathered: 2026-02-24*

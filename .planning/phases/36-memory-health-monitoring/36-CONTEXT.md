# Phase 36: Memory Health Monitoring - Context

**Gathered:** 2026-02-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Add a memory health panel to Mission Control's /memory page showing per-agent memory system health at a glance. Covers chunk counts, line budget usage, last-updated timestamps, and flush frequency trends. Uses existing 30s SWR polling — no new infrastructure.

</domain>

<decisions>
## Implementation Decisions

### Health thresholds
- Warning at 160 lines (80% of 200-line budget), critical at 190 lines (95%)
- Colored dot + text label: green "Healthy" / yellow "Warning" / red "Critical"
- Staleness badge: 3+ days with no memory flush — same threshold for all agents (content agents included)
- Staleness is independent from budget health (separate concern, separate badge)

### Agent scope & empty states
- Show all 7 agents: Bob, Scout, Sentinel, Vector, Quill, Sage, Ezra
- Agents without memory files (currently Quill, Sage, Ezra) show gray "No Memory" card — visible but clearly inactive
- No overall summary bar — with 7 cards, the dots themselves are the summary

### Data sources
- MEMORY.md line count: read file directly from disk (`~/clawd/agents/{agent_id}/MEMORY.md`)
- Sparkline flush data: shell out to `git log` on demand per agent — simple, accurate, no new state
- A "flush" = any MEMORY.md git commit (directly observable)
- If MEMORY.md doesn't exist for an agent, show "No Memory" state

### Panel placement & page integration
- Health section sits at top of /memory page, above the existing browse grid
- "Memory Health" as a subtle section heading — just enough to separate from browse below
- Existing page title/subtitle unchanged ("Memory" / "Browse agent memories and conversations")
- New `/api/memory/health` endpoint — separate from existing `/api/memory` browse/search endpoint
- Uses same 30s SWR polling via global provider config

### Budget visualization
- Horizontal progress bar showing fill level with "142/200 lines" fraction text
- Bar color shifts green→yellow→red at the 80%/95% thresholds
- Chunk count as small secondary gray text below progress bar ("12 chunks")
- Last-updated timestamp in relative format ("Updated 3h ago") with exact datetime on hover

### Card layout & density
- Card-per-agent grid: 4 cols (lg), 3 cols (md), 2 cols (sm) — denser than browse grid since health cards are compact
- Agent identified by display name (Bob, Scout, etc.) + agent color dot from chart-constants.ts
- Mini sparkline: 7-bar chart showing flushes per day over last 7 days — read-only, no drill-down
- Sparkline hidden on mobile to keep cards compact — health dot + progress bar + last-updated are the essentials

### Claude's Discretion
- Exact card dimensions and spacing
- Sparkline rendering approach (SVG, canvas, or CSS)
- git log command construction and parsing
- Card grid responsive breakpoints (exact pixel values)
- Skeleton loader design during health data fetch
- How to handle git repos that don't exist for an agent

</decisions>

<specifics>
## Specific Ideas

- Cards should feel like Linear's issue cards — clean, compact, scannable
- Health dot is the fastest signal — you should be able to tell if anything needs attention in under 2 seconds
- The progress bar is the actionable detail — "how close to budget am I?"
- Sparkline shows activity patterns — is this agent's memory being maintained or neglected?
- Consistent with existing Mission Control patterns: agent colors from chart-constants.ts, FreshnessIndicator, skeleton loaders

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 36-memory-health-monitoring*
*Context gathered: 2026-02-23*

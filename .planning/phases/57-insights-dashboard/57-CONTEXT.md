# Phase 58: Insights & Dashboard - Context

**Gathered:** 2026-04-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Bob surfaces cross-domain patterns from accumulated data (Oura ↔ habits ↔ mood correlations, recurring journal themes) and the andyOS Dashboard gets a /growth page displaying habit charts, journal entries, goal progress, and Oura correlations. An hourly sync cron pushes EC2 data to andyOS PostgreSQL, establishing the pattern for future Mission Control → andyOS unification.

After this phase: User sees a unified growth hub on dashboard.andykaufman.net with habit streaks, goal progress, journal trends, Oura metrics, and weekly insights. Bob's weekly review includes Oura↔habit correlations and journal theme analysis. EC2 data flows to andyOS hourly via sync cron.

</domain>

<decisions>
## Implementation Decisions

### Dashboard Location
- **D-01:** /growth page built on **andyOS Dashboard** (Vercel/PostgreSQL at dashboard.andykaufman.net), NOT Mission Control
- **D-02:** Goals and journal data already in andyOS PostgreSQL — no migration needed for those
- **D-03:** Mission Control pages (agents, yolo, tools) stay on EC2 for now — migration deferred to future phase/milestone
- **D-04:** This phase establishes the EC2→andyOS sync pattern that future MC migration will reuse

### Data Sync (EC2 → andyOS)
- **D-05:** Hourly sync cron on EC2 pushes data to andyOS API endpoints
- **D-06:** Sync targets: habits + habit_logs (growth.db), Oura snapshots (health.db), commute_prompts (growth.db), weekly_reviews (growth.db)
- **D-07:** andyOS stores synced data in PostgreSQL tables (mirrored schema)
- **D-08:** All /growth queries hit local PostgreSQL — no cross-network calls at page load
- **D-09:** Sync API endpoints on andyOS authenticated via API key (same pattern as /api/growth/summary)

### Correlation Engine
- **D-10:** SQL date-matching joins — avg sleep score on habit-complete days vs not, mood vs HRV/readiness, etc.
- **D-11:** No stats libraries or LLM analysis for correlations — keep it simple, understandable
- **D-12:** Correlation insights generated weekly via existing Sunday 8am weekly review cron
- **D-13:** Bob includes correlations in weekly review Slack DM (extends Phase 57 weekly review)

### Journal Theme Extraction
- **D-14:** LLM summarization — Bob sends last 4 weeks of journal entries to Claude for theme extraction
- **D-15:** Themes categorized as: recurring, emerging, declining
- **D-16:** Theme analysis bundled into weekly review cron (not separate cron)
- **D-17:** Theme results stored in weekly_reviews record for dashboard display

### /growth Page Design
- **D-18:** Hub-style card grid layout — each domain as a card (Habits, Goals, Journal, Oura, Insights)
- **D-19:** Each card shows key metric + sparkline/mini chart (Recharts)
- **D-20:** Cards link to existing detail pages (/goals, /journal) — /growth is the overview hub
- **D-21:** Habits card shows summary only (streaks, consistency, today's status) — no separate /habits page
- **D-22:** Full-width "Weekly Insights" card at bottom with latest correlation and theme data
- **D-23:** Chart library: Recharts (already in andyOS stack)
- **D-24:** Follow existing andyOS patterns: shadcn cards, Suspense loading, SWR auto-refresh

### Weekly Review Enhancement
- **D-25:** Extend Phase 57 weekly review cron to include: Oura↔habit correlations (SQL), journal themes (LLM), and store results in growth.db weekly_reviews
- **D-26:** Sync cron pushes weekly_reviews to andyOS for dashboard display

### Claude's Discretion
- Exact PostgreSQL schema for synced tables (mirror SQLite structure)
- Sync cron implementation details (Python script vs shell script)
- API endpoint design for sync (batch vs per-table)
- Sparkline chart config and card sizing
- Error/loading/empty states for /growth cards
- SWR refresh interval for /growth page
- Exact correlation query SQL

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Growth system (pops-claw EC2)
- `.planning/phases/55-platform-prep-habit-tracking/55-CONTEXT.md` — growth.db schema, habit tracking design, bind-mount pattern
- `.planning/phases/56-goals-journal/56-CONTEXT.md` — andyOS goals/journal architecture, API routes, Drizzle schema
- `.planning/phases/57-commute-weekly-review/57-CONTEXT.md` — weekly review cron design, Oura correlation approach, voice note linking

### Requirements
- `.planning/REQUIREMENTS.md` §Insights & Dashboard — INSG-01 (Oura correlations), INSG-02 (journal themes), INSG-03 (/growth page)

### andyOS Dashboard (separate repo)
- andyOS Dashboard codebase at ~/Desktop/Projects/andyos-dashboard/ — existing Drizzle schema, API routes, page patterns, Recharts usage

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- andyOS `/api/growth/summary` endpoint — already serves goal + journal summary to Bob
- andyOS Drizzle schema — goal, goalCheckin, journalEntry tables already exist
- andyOS Recharts integration — used in existing analytics pages
- andyOS shadcn card components — established pattern for hub cards
- EC2 weekly-review cron — Phase 57 already includes Oura data queries

### Established Patterns
- andyOS Suspense + SWR for data loading
- andyOS API key auth for Bob-facing endpoints (/api/growth/summary uses GROWTH_API_KEY)
- EC2 cron → Python script → SQLite pattern (habit-manager.py, process-voice-notes.py)
- EC2 bind-mounted databases for sandbox access

### Integration Points
- New sync cron on EC2 → new /api/sync/* endpoints on andyOS
- Extended weekly-review cron payload (add correlations + themes sections)
- New /growth page in andyOS sidebar navigation (LIFE section)
- growth.db weekly_reviews table stores correlation + theme results

</code_context>

<specifics>
## Specific Ideas

- Hub card layout: 2x2 grid (Habits, Goals, Journal, Oura) + full-width insights card below
- Insights card shows latest weekly review highlights: correlation bullets + theme list
- Oura card: 7-day sleep score sparkline + avg readiness badge
- Habits card: active count, best streak, today's completion status
- Goals card: active count, lowest-progress goal name + bar
- Journal card: streak days, avg mood/energy this week
- Correlation example: "Sleep 84 on habit days vs 71 — readiness ↑ mood"
- Theme example: "Recurring: work-life balance (8 of 12 entries). Emerging: fitness motivation"
- User wants andyOS to become the unified hub — this phase is the first step in that direction

</specifics>

<deferred>
## Deferred Ideas

- Mission Control → andyOS migration (agents, yolo, tools pages) — capture as Phase 59 or new milestone
- /habits detail page with calendar heatmap and per-habit history — future phase
- Real-time sync (webhook-based instead of polling) — future optimization
- Monthly/quarterly personal retrospective report (ADV-03) — v2 requirements
- Adaptive prompt difficulty (ADV-01) — v2 requirements

</deferred>

---

*Phase: 58-insights-dashboard*
*Context gathered: 2026-04-12*

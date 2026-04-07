# Phase 56: Goals & Journal - Context

**Gathered:** 2026-03-26
**Status:** Ready for planning
**Source:** Requirements + andyOS Dashboard codebase analysis

<domain>
## Phase Boundary

This phase delivers OKR-style goal tracking and daily journaling as new modules in the **andyOS Dashboard** (Next.js/PostgreSQL/Vercel at dashboard.andykaufman.net). Bob (pops-claw) gets a lightweight nudge layer — evening journal prompt DM that links to the dashboard, and morning briefing goal summaries pulled from an andyOS API.

After this phase: User can create goals with key results in the dashboard, track progress visually, write journal entries with mood/energy, see goals and journal on the hub. Bob sends an 8pm journal nudge and includes goal summary in morning briefings.

## Cross-Repo Scope

| Repo | What gets built |
|------|----------------|
| **andyos-dashboard** | Drizzle schema (goal, goalCheckin, journalEntry), API routes, /goals page, /journal page, hub cards |
| **pops-claw** (EC2) | Protocol doc update for Bob nudges, cron payload modifications |

</domain>

<decisions>
## Implementation Decisions

### Database (andyOS PostgreSQL via Drizzle)
- New tables: `goal`, `goal_checkin`, `journal_entry` — all with userId FK to user table
- goal.keyResults stored as JSONB: `[{text, targetPct, currentPct}]`
- goal.status: active, completed, abandoned
- journal_entry has date (unique per user per day), prompt, response, mood (1-5), energy (1-5), category
- All tables follow existing pattern: UUID PK, userId FK, indexes on userId + date

### Goals Page (/goals)
- List view of active goals with visual progress bars (Recharts or native CSS)
- Create goal form: objective, 1-3 key results, optional category + target date
- Goal detail: KR progress sliders/inputs, check-in history, complete/abandon actions
- Categories: health, career, learning, financial, personal
- Matches existing dashboard style: shadcn cards, same layout patterns as /projects

### Journal Page (/journal)
- Today's prompt at top (based on day-of-week rotation)
- Rich text area for response entry
- Mood (1-5) and energy (1-5) inline selectors (not separate step)
- Past entries timeline below, most recent first
- Stats: completion rate, streaks, average mood/energy
- Day-of-week prompt categories: Mon=gratitude, Tue=challenges, Wed=learning, Thu=goals, Fri=wins, Sat=freeform, Sun=reflection

### Hub Cards
- Goals hub card: shows active goal count + lowest-progress goal (links to /goals)
- Journal hub card: shows today's prompt + streak count (links to /journal)
- Follow existing Suspense pattern from health-card.tsx

### Nav Integration
- Add "Goals" and "Journal" to the LIFE section in sidebar nav
- Icons: Target (goals), BookOpen (journal) from lucide-react

### API Routes
- /api/goals — CRUD for goals
- /api/goals/[id]/checkin — progress check-ins
- /api/journal — CRUD for journal entries
- /api/journal/prompt — get today's prompt
- /api/journal/stats — completion rate, streaks, mood trends
- /api/growth/summary — public-ish endpoint for Bob to pull goal + journal summary (API key auth)

### Bob Integration (pops-claw, lightweight)
- Evening journal nudge: cron at 8pm PT, DM says "Time for your evening reflection" with dashboard link
- Morning briefing: cron payload adds "Goals" section that calls andyOS /api/growth/summary
- No Python scripts needed — all data lives in PostgreSQL
- Protocol doc: GROWTH_DASHBOARD.md replaces GOAL_TRACKER.md + JOURNAL_PROTOCOL.md

### Prompt Bank
- 21+ prompts across 7 categories, stored as constant in journal API route
- Same rotation as before: hash(date) % prompts.length for deterministic variety

### Claude's Discretion
- Exact Recharts config for goal progress visualization
- Journal entry form layout specifics
- Hub card data display format
- growth/summary API response shape
- Error/loading/empty states

</decisions>

<specifics>
## Specific Ideas

- Goal progress bars: thin colored bars under each goal card, color shifts green as progress increases
- Journal mood selector: 5 emoji-style buttons (not a dropdown) — quick single-tap
- Hub goals card: "3 active goals — Read 12 Books (25%)" linking to /goals
- Hub journal card: "Streak: 5 days — Today: Gratitude" linking to /journal
- /api/growth/summary returns: {goals: [{title, progress, targetDate}], journal: {streak, lastMood, lastEnergy}}
- Bob's DM: "Evening reflection time. Today's prompt (gratitude): What's one thing you're grateful for? → dashboard.andykaufman.net/journal"

</specifics>

<deferred>
## Deferred Ideas

- Morning commute audio prompts — Phase 57
- Weekly growth review with Oura correlation — Phase 57
- Oura x mood x habit correlations — Phase 58
- Mission Control /growth page — Phase 58
- Bob journal response capture via DM (alternate entry path) — backlog
- Journal prompt push notifications — backlog

</deferred>

---

*Phase: 56-goals-journal*
*Context gathered: 2026-03-26 via requirements + andyOS codebase analysis*

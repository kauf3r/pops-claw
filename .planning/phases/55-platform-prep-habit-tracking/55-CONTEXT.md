# Phase 55: Platform Prep & Habit Tracking - Context

**Gathered:** 2026-03-16
**Status:** Ready for planning
**Source:** Research + Requirements (best-practice defaults)

<domain>
## Phase Boundary

This phase delivers the foundation for all v2.10 self-improvement features plus the complete habit tracking system. It includes upgrading OpenClaw to v2026.3.13, creating growth.db with the full schema for all 4 phases, deploying the GROWTH_COMPANION.md workspace protocol doc, and building complete habit CRUD with streaks, accountability nudges, and morning briefing integration.

After this phase: User can create habits via Slack DM, log completions daily, see streaks and consistency in morning briefing, and get nudged in evening recap for unlogged habits.

</domain>

<decisions>
## Implementation Decisions

### Database
- Database name: growth.db (not selfimprove.db)
- Full schema upfront: habits, habit_logs, goals, goal_checkins, journal_entries, commute_prompts, weekly_reviews — all tables created in Phase 55 even though later phases use them. Avoids schema migrations.
- Location on EC2: ~/clawd/growth.db (same pattern as content.db, email.db)
- Bind-mount in openclaw.json: agents.defaults.sandbox.docker.binds
- WAL mode for Mission Control reads (later phase)

### OpenClaw Upgrade
- Target: v2026.3.13 (from v2026.3.11)
- Run `openclaw backup create` after upgrade (new CLI feature)
- Verify OPENCLAW_TZ behavior (log-only or cron-affecting?)
- Run `openclaw doctor --fix` after upgrade
- Single gateway restart for upgrade + bind-mount + cron changes

### Protocol Doc Pattern
- GROWTH_COMPANION.md in ~/clawd/agents/main/ (same as CONTENT_TRIGGERS.md, VOICE_NOTES_PROTOCOL.md)
- Handles: habit create/list/log/pause/archive commands via DM
- Includes: Python script references for DB CRUD operations
- Does NOT handle: goals, journal, commute prompts (separate protocol docs in later phases)

### Habit Tracking Design
- Streak forgiveness: 1 grace day (missing 1 day doesn't break streak, missing 2 does)
- Consistency rate: completions / (days since created - paused days) * 100
- Habit frequency: daily by default, support weekly option
- Logging: natural language ("done meditation", "skipped gym - sick")
- Skip reasons: stored in habit_logs for pattern detection (Phase 58)
- Accountability nudge: piggyback on existing evening-recap cron payload, not new cron
- Briefing section: new Section 12 in morning briefing (after YOLO in Section 11)

### Cron Strategy
- NO new standalone crons for habits — bundle into existing evening-recap and morning-briefing
- Modify evening-recap session instruction to include habit nudge section
- Modify morning-briefing session instruction to include habit summary section
- Single gateway restart covers all changes

### Python Scripts
- ~/scripts/habit-manager.py — CRUD operations on growth.db habits/habit_logs tables
- Bind-mounted to sandbox for Bob to execute
- Pattern: same as process-voice-notes.py, weekly-oura-summary.py

### Claude's Discretion
- Exact habit_logs table schema (columns, types)
- Python script error handling approach
- Exact wording of accountability nudge
- Morning briefing section formatting
- Natural language parsing strategy for habit logging

</decisions>

<specifics>
## Specific Ideas

- Habit create example: "Bob, add habit: meditate 10min daily"
- Habit log example: "done meditation" or "skipped gym - feeling sick"
- Briefing output example: "Habits: meditation (12-day streak, 94%), gym (3/5 this week, 60%), reading (new)"
- Evening nudge example: "You haven't logged meditation or gym today. Done, skipped, or remind me later?"
- growth.db tables needed for Phase 55: habits (id, name, frequency, created_at, status, grace_days), habit_logs (id, habit_id, date, status, skip_reason, logged_at)
- Tables for future phases (create empty now): goals, goal_checkins, journal_entries, commute_prompts, weekly_reviews

</specifics>

<deferred>
## Deferred Ideas

- Goal tracking — Phase 56
- Journal prompts — Phase 56
- Morning commute prompts — Phase 57
- Weekly growth review — Phase 57
- Oura correlations — Phase 58
- Mission Control /growth page — Phase 58
- Adaptive prompt difficulty — v2 (deferred)

</deferred>

---

*Phase: 55-platform-prep-habit-tracking*
*Context gathered: 2026-03-16 via research best-practice defaults*

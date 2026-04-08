# Phase 57: Morning Commute & Weekly Review - Context

**Gathered:** 2026-04-08
**Status:** Ready for planning
**Source:** Requirements CMTE-01–04, WKLY-01–04 + infrastructure audit

<domain>
## Phase Boundary

This phase adds two features to Bob (pops-claw EC2): context-aware morning commute prompts with voice note responses, and structured weekly growth reviews correlating Oura health data with habit/journal patterns. All data lives in growth.db (already has `commute_prompts` and `weekly_reviews` tables). The andyOS Dashboard (goals/journal) is read-only from Bob's perspective — Bob fetches summaries via API.

After this phase: Bob sends a personalized commute prompt before the user leaves for work, accepts voice note responses via the existing pipeline, and generates a comprehensive weekly growth review every Sunday with Oura health correlations.

## What Already Exists

### Infrastructure (ready to use)
| Component | Location | Status |
|-----------|----------|--------|
| growth.db | ~/clawd/db/growth.db (bind-mounted) | Has `commute_prompts` + `weekly_reviews` tables, both empty |
| Voice notes pipeline | voice-notes-processor cron (every 2h) | Running OK, processes Google Drive voice notes |
| coordination.db | voice_notes table | Active, tracks transcriptions |
| Oura health data | health.db health_snapshots | 62 days (Feb 6 – Apr 8), syncs daily |
| Habit system | growth.db habits + habit_logs | 1 active habit, 0 logs |
| Goals (andyOS) | /api/growth/summary | 0 goals yet — API deployed, GROWTH_API_KEY on EC2 |
| Journal (andyOS) | /api/growth/summary | 0 entries yet — API deployed |
| Weekly review cron | weekly-review (Sunday 8am PT) | Already exists and running OK |
| Weekly goal check-in cron | weekly-goal-checkin (Sunday 9am PT) | Exists, idle |
| GROWTH_COMPANION.md | ~/clawd/agents/main/ | Habit commands protocol |
| GROWTH_DASHBOARD.md | ~/clawd/agents/main/ | Goals/journal nudge protocol |

### Data Availability Note
- Habit logs: 0 entries (habit created but not logged yet)
- Journal entries: 0 (Phase 56 UI deployed Apr 6, not yet used)
- Goals: 0 (not yet created)
- Oura: 62 days of sleep/readiness/HRV/activity — sufficient for weekly correlation
- Voice notes: pipeline exists, processes every 2h

Phase 57 should work gracefully with sparse data — show what's available, omit what isn't, improve as data accumulates.

</domain>

<decisions>
## Implementation Decisions

### Morning Commute Prompt
- **Trigger:** New cron, ~7:15am PT (before 7:30 departure), weekdays only
- **Delivery:** Slack DM to Andy
- **Context sources:** (1) Calendar — today's events via gog, (2) Oura — last night's sleep score + readiness from health.db, (3) Active goals — from andyOS /api/growth/summary, (4) Recent journal themes — last 3 entries from andyOS or growth.db
- **Prompt style:** Brief, thought-provoking question tied to the day's context. Not generic — reference specific meetings, sleep quality, or active goals
- **Response path:** User responds via voice note (Google Drive → voice-notes-processor → transcription). Bob matches response to today's commute_prompts row by date
- **Storage:** growth.db commute_prompts table (already exists with all needed columns)
- **Protocol doc:** Add "Morning Commute" section to GROWTH_COMPANION.md

### Weekly Growth Review
- **Trigger:** Enhance existing weekly-review cron (Sunday 8am PT) — don't create a new one
- **Delivery:** Slack DM, structured format
- **Content sections:**
  1. **Wins** — goals with progress increases this week, habits completed, journal highlights
  2. **Challenges** — missed habits, goals with no progress, low mood/energy days
  3. **Energy Patterns** — Oura sleep/readiness/HRV trends for the week, correlate with habit completion (e.g., "You completed all habits on days when sleep score > 80")
  4. **Habit Summary** — weekly completion rates, streak status
  5. **Goal Progress** — week-over-week delta from andyOS API
  6. **Reflection Prompt** — one question to think about for next week
- **Storage:** growth.db weekly_reviews table (already exists)
- **Data queries:**
  - health.db: 7-day sleep_score, readiness_score, hrv_balance, resting_hr
  - growth.db: habit_logs for the week, commute_prompts responses
  - andyOS API: goal summary (progress %)
  - andyOS API: journal stats + recent entries (mood/energy trends)
- **Graceful degradation:** Each section checks data availability — if no habits logged, say "No habit data this week." Don't error out.

### Voice Note → Commute Response Linking
- Voice notes pipeline already transcribes to coordination.db voice_notes
- New: voice-notes-processor should check if today has an unresponded commute_prompt in growth.db
- If user sends voice note on a day with an open commute prompt, link them:
  - Update commute_prompts.response_text with transcription
  - Set commute_prompts.response_source = 'voice'
  - Set commute_prompts.responded_at
- Matching logic: same date (date-level, not time), most recent unresponded prompt

### Configurable Commute Time
- Store in GROWTH_COMPANION.md as a setting Bob reads: `commute_prompt_time: 07:15`
- Cron runs at fixed time, but protocol doc makes it easy to adjust
- Skip weekends and holidays (just weekdays for now)

### What NOT to Build
- No voice input (out of scope per PROJECT.md)
- No Google Drive integration changes — voice notes pipeline already works
- No dashboard UI for commute/reviews — that's Phase 58
- No ML/NLP analysis of journal themes — simple keyword extraction or last-3-entries summary
- Don't modify existing weekly-review cron payload significantly — extend it with growth data sections

</decisions>

<questions>
## Open Questions (answered with best-practice defaults)

1. **Commute time configurable per day?** → No, single time for now (7:15am PT weekdays). Can adjust in protocol doc.
2. **Should commute prompt skip if no calendar events?** → No, still send — use sleep data or goals as context instead.
3. **Weekly review length?** → Target 20-30 lines. Concise, scannable, not an essay.
4. **Merge with existing weekly-goal-checkin?** → No, keep separate. Weekly review is broader (habits + Oura + journal), goal check-in is goal-specific. Review at 8am, goal check-in at 9am.
5. **Store weekly review as Markdown in growth.db?** → Yes, text columns for each section. Keep it queryable.
</questions>

<scope>
## Plan Breakdown

### Plan 57-01: Morning Commute Prompt System
- Commute prompt generation logic (context assembly from calendar, Oura, goals, journal)
- New cron: commute-prompt (7:15am PT weekdays)
- Protocol doc update (GROWTH_COMPANION.md commute section)
- growth.db commute_prompts writes
- Voice note → commute response linking in voice-notes-processor

### Plan 57-02: Weekly Growth Review
- Enhanced weekly-review cron payload with growth data sections
- Oura correlation logic (sleep vs. habit completion, readiness trends)
- Protocol doc (GROWTH_COMPANION.md weekly review section)
- growth.db weekly_reviews writes
- Graceful degradation for sparse data

### Plan 57-03: Integration & Verification
- End-to-end test: commute prompt delivery + voice note response linking
- End-to-end test: weekly review with real Oura + growth data
- Verify graceful degradation with empty/sparse data
- Update morning briefing to mention commute prompt status if needed
</scope>

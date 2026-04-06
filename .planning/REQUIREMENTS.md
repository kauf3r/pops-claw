# Requirements: Pops-Claw v2.10 Self-Improvement Companion

**Defined:** 2026-03-16
**Core Value:** Bob becomes a self-improvement companion -- tracking habits, prompting reflection, monitoring goals, and correlating health data -- while keeping proactive interactions under the fatigue threshold.

## v2.10 Requirements

### Platform Prep

- [ ] **PLAT-01**: OpenClaw upgraded to v2026.3.13 with backup CLI, OPENCLAW_TZ, and compaction fix verified
- [ ] **PLAT-02**: growth.db created with full schema (habits, habit_logs, goals, goal_checkins, journal_entries, commute_prompts, weekly_reviews) and bind-mounted to sandbox
- [ ] **PLAT-03**: GROWTH_COMPANION.md workspace protocol doc deployed, Bob recognizes self-improvement DM commands

### Habit Tracking

- [ ] **HABIT-01**: User can create, list, pause, and archive habits via Slack DM to Bob
- [ ] **HABIT-02**: User can log habit completion via Slack DM (e.g., "done meditation", "skipped gym -- sick")
- [ ] **HABIT-03**: Bob tracks streaks with 1-day forgiveness and displays consistency rate (%) alongside streak count
- [ ] **HABIT-04**: Bob sends accountability nudge in evening recap if habits not logged today
- [ ] **HABIT-05**: Morning briefing includes habit summary section (active habits, streaks, consistency, what's due today)

### Goals

- [x] **GOAL-01**: User can create OKR-style goals via Slack DM (objective + 1-3 key results with measurable targets)
- [x] **GOAL-02**: User can check in on goal progress via Slack DM, Bob updates key result progress
- [ ] **GOAL-03**: Bob prompts weekly goal check-in (bundled with weekly growth review)
- [ ] **GOAL-04**: Morning briefing includes active goals with progress bars

### Journal

- [x] **JRNL-01**: Bob sends daily journal prompt via Slack DM with day-of-week topic rotation
- [x] **JRNL-02**: User can respond to journal prompt via DM, Bob extracts and stores mood/energy ratings (1-5)
- [x] **JRNL-03**: Journal prompt bank of 20+ diverse prompts covering reflection, gratitude, challenges, aspirations
- [x] **JRNL-04**: Bob stores journal entries in growth.db with date, prompt, response, mood, energy fields

### Morning Commute Prompts

- [ ] **CMTE-01**: Bob delivers personalized morning commute prompt before departure (configurable time)
- [ ] **CMTE-02**: Commute prompt incorporates context from calendar, sleep data, active goals, recent journal themes
- [ ] **CMTE-03**: User responds via voice notes (existing Google Drive pipeline), Bob associates response with prompt
- [ ] **CMTE-04**: Bob extracts key insights from voice note responses and stores in growth.db

### Weekly Growth Review

- [ ] **WKLY-01**: Bob generates structured weekly growth review (wins, challenges, energy patterns, habit/goal progress)
- [ ] **WKLY-02**: Weekly review includes Oura-correlated energy patterns (sleep quality vs. habit completion, readiness trends)
- [ ] **WKLY-03**: Weekly review delivered via Slack DM on Sunday morning
- [ ] **WKLY-04**: Review stored in growth.db for longitudinal tracking

### Insights & Dashboard

- [ ] **INSG-01**: Bob correlates Oura health data with habit completion and mood patterns (requires 4+ weeks data)
- [ ] **INSG-02**: Bob surfaces recurring journal themes across entries (requires 4+ weeks data)
- [ ] **INSG-03**: Mission Control /growth page displays habit charts, journal entries, goal progress, and Oura correlations

## v2 Requirements (Deferred)

### Advanced Features
- **ADV-01**: Adaptive prompt difficulty based on journaling depth over time
- **ADV-02**: Social accountability (share streaks/goals with accountability partner)
- **ADV-03**: Monthly/quarterly personal retrospective report
- **ADV-04**: Integration with fitness tracking beyond Oura (Apple Health, workout logs)

## Out of Scope

| Feature | Reason |
|---------|--------|
| ClawhHub habit/self-improvement skills | Conflict with established workspace protocol doc pattern |
| Gamification (badges, points, levels) | 67% abandonment by week 4 per research |
| New agent for self-improvement | Bob (main agent) handles it -- no coordination overhead |
| Real-time habit reminders | Notification fatigue risk -- bundle into existing briefing/recap only |
| Voice input as primary logging | Voice pipeline has 28-note backlog + OpenAI quota issues -- text-first, voice supplemental |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PLAT-01 | Phase 55 | Pending |
| PLAT-02 | Phase 55 | Pending |
| PLAT-03 | Phase 55 | Pending |
| HABIT-01 | Phase 55 | Pending |
| HABIT-02 | Phase 55 | Pending |
| HABIT-03 | Phase 55 | Pending |
| HABIT-04 | Phase 55 | Pending |
| HABIT-05 | Phase 55 | Pending |
| GOAL-01 | Phase 56 | Complete |
| GOAL-02 | Phase 56 | Complete |
| GOAL-03 | Phase 56 | Pending |
| GOAL-04 | Phase 56 | Pending |
| JRNL-01 | Phase 56 | Complete |
| JRNL-02 | Phase 56 | Complete |
| JRNL-03 | Phase 56 | Complete |
| JRNL-04 | Phase 56 | Complete |
| CMTE-01 | Phase 57 | Pending |
| CMTE-02 | Phase 57 | Pending |
| CMTE-03 | Phase 57 | Pending |
| CMTE-04 | Phase 57 | Pending |
| WKLY-01 | Phase 57 | Pending |
| WKLY-02 | Phase 57 | Pending |
| WKLY-03 | Phase 57 | Pending |
| WKLY-04 | Phase 57 | Pending |
| INSG-01 | Phase 58 | Pending |
| INSG-02 | Phase 58 | Pending |
| INSG-03 | Phase 58 | Pending |

**Coverage:**
- v2.10 requirements: 27 total
- Mapped to phases: 27
- Unmapped: 0

---
*Requirements defined: 2026-03-16*
*Last updated: 2026-03-16 -- traceability updated with phase mappings*

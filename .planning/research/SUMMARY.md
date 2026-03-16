# Research Summary: v2.10 Self-Improvement Companion

**Domain:** AI-powered personal self-improvement (habit tracking, journaling, weekly reviews, goal tracking, morning commute prompts)
**Researched:** 2026-03-16
**Overall confidence:** HIGH for architecture and patterns (reuses proven stack), MEDIUM for ClawhHub ecosystem assessment and OpenClaw upgrade behavior

## Executive Summary

v2.10 builds self-improvement features onto Bob's existing infrastructure using the same patterns proven across 9 milestones: workspace protocol documents define agent behavior, cron jobs drive proactive interaction, SQLite stores structured data, and Python scripts handle database operations inside the Docker sandbox. The entire feature set requires one new database (growth.db), five workspace protocol documents, four to five new cron jobs, and two to three Python scripts. No new agents, no new runtimes, no new external services.

The ClawhHub marketplace has several self-improvement skills (habit-flow-skill by tralves, task-tracker by kesslerio, self-improvement by navendugoyal19), but none are worth installing. They introduce their own data models, dependency trees, and cron management that conflict with the established patterns in this deployment. Custom workspace protocol docs + SQLite + crons are the right approach.

OpenClaw has released v2026.3.12 and v2026.3.13 since the current v2026.3.11. The upgrade is recommended before feature work begins. Key gains: `openclaw backup create` (config safety net), Docker `OPENCLAW_TZ` timezone override (cleaner cron scheduling), and a compaction token counting fix (prevents over-aggressive context pruning). The upgrade is low-risk -- incremental releases with no breaking changes.

The biggest risk is not technical -- it is behavioral. Self-improvement tools have a 92% failure rate within 60 days. The mitigation is phased rollout: ship one feature (habit tracking), use it for 14 days, then add the next. Never launch all 5 features simultaneously.

## Key Findings

**Stack:** Zero new infrastructure. One new SQLite database (growth.db), five workspace protocol docs, 4-5 cron jobs, 2-3 Python scripts. Upgrade OpenClaw to v2026.3.13. No ClawhHub skills to install.

**Architecture:** Same proven patterns -- workspace protocol docs for behavior, cron for proactive nudges, Python scripts for DB CRUD, Slack DM for interaction. Voice notes pipeline extended (not rebuilt) for commute journal responses. Single new database (growth.db) keeps data separated from coordination.db.

**Critical pitfall:** The self-improvement system itself becoming another obligation. Phased rollout with 14-day usage gates between features is the primary mitigation. Secondary: streak fragility (use consistency rates, not pure streaks), notification fatigue (max 4 proactive DMs/day, bundle into existing briefing).

## Implications for Roadmap

Based on research, suggested phase structure:

1. **Platform Prep + Habit Foundation** - OpenClaw upgrade to v2026.3.13, growth.db creation with full schema, HABIT_TRACKER.md protocol doc, habit logging via Slack DM, habit-accountability cron, morning briefing integration
   - Addresses: Table stakes (habit logging, streak tracking, accountability nudge)
   - Avoids: Docker stub pitfall (DB created before bind-mount), gateway restart disruption (single restart for all changes), OpenClaw version lag (upgrade first)

2. **Goals + Journal** - GOAL_TRACKER.md and JOURNAL_PROTOCOL.md protocol docs, goal creation/check-in via Slack DM, journal-prompt cron with day-of-week rotation, mood/energy logging
   - Addresses: Goal tracking, journal prompts, mood logging
   - Avoids: Insufficient data pitfall (habits have 1+ weeks of data before goals/journal layer on)

3. **Morning Commute + Weekly Review** - COMMUTE_PROMPTS.md and WEEKLY_REVIEW.md protocol docs, morning-reflection-prompt cron, weekly-review cron extension, weekly-oura-summary.py script, voice-to-journal pipeline
   - Addresses: Morning commute prompts, weekly review with Oura correlation
   - Avoids: Voice note attribution ambiguity (manual confirmation, not auto-attribution), weekly review data gaps (2+ weeks of data available)

4. **Insights + Polish** (optional, gated on actual usage) - Journal theme surfacing, Oura-correlated habit insights, adaptive prompt difficulty, Mission Control /growth dashboard page
   - Addresses: Differentiator features
   - Avoids: Over-engineering (only build if core features are being used regularly for 14+ days)

**Phase ordering rationale:**
- Phase 1 first because habits are the highest-frequency interaction and the foundation for all other features. Growth.db schema is designed upfront to support all phases, avoiding schema migrations later. OpenClaw upgrade batched here to get backup CLI and timezone support before feature work.
- Phase 2 after Phase 1 because goals and journal entries build on the same DB and protocol doc patterns. Having habits working proves the pattern before expanding. Journal prompt data accumulation clock starts here (4 weeks needed for pattern detection).
- Phase 3 after Phase 2 because morning prompts need journal infrastructure (Phase 2), and weekly reviews need 2+ weeks of habit + journal data to be meaningful. Voice-to-journal pipeline has the most complex flow and needs the most testing.
- Phase 4 is optional and gated on actual usage evidence. Oura correlation needs 4+ weeks of habit data. Theme surfacing needs 4+ weeks of journal entries. Mission Control page is view-only and not critical for functionality.

**Research flags for phases:**
- Phase 1: Standard patterns, unlikely to need deeper research. Docker TZ behavior after upgrade should be verified.
- Phase 2: Standard patterns. Journal prompt bank (20-30 prompts) needs content creation, not research.
- Phase 3: Voice-to-journal attribution needs design validation. Test keyword-prefix approach vs. manual confirmation in first week.
- Phase 4: Oura correlation analysis is analytically complex. May need phase-specific research on what correlations are meaningful.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Zero new dependencies. Same DB, same scripts, same cron patterns as 9 previous milestones. OpenClaw upgrade well-documented |
| Features | HIGH | Table stakes well-defined. Differentiators clearly bounded. Anti-features explicitly listed. Behavioral research on habit app abandonment informs design |
| Architecture | HIGH | Extends proven workspace protocol + cron + SQLite + Python pattern. All 5 workspace protocol docs follow established CONTENT_TRIGGERS.md / VOICE_NOTES_PROTOCOL.md model |
| Pitfalls | HIGH | Most pitfalls are variants of known issues (Docker stubs, token bloat, timezone confusion, gateway restart). Behavioral pitfalls (streak fragility, notification fatigue, prompt staleness) well-documented in research literature |
| OpenClaw upgrade | MEDIUM | Release notes are clear but compaction behavior change in v2026.3.13 needs post-upgrade monitoring |
| ClawhHub skills | MEDIUM | Assessed from SKILL.md files and community reviews. Not tested on this deployment. Recommendation is to install none |
| Voice-to-journal pipeline | MEDIUM | Conceptually sound but attribution logic needs real-world testing. Existing voice notes pipeline is confirmed working (process-voice-notes.py runs, Whisper tiny model on EC2 CPU) |

## Gaps to Address

- **Docker OPENCLAW_TZ behavior verification:** Does the v2026.3.13 timezone env var affect cron execution times, or only log timestamps? Needs testing after upgrade.
- **health.db schema inspection:** Need to SSH into EC2 and inspect actual health.db table structure to ensure weekly-oura-summary.py queries are valid.
- **Workspace token budget:** Need to measure current workspace file token load before adding 5 new docs. If already near budget, some existing docs may need pruning.
- **Journal prompt content:** 20-30 diverse prompts needed. Content creation task, not research.
- **Streak forgiveness UX:** "1 grace day" is the recommended default. Design needs user input on per-habit forgiveness rules.
- **Database naming decision:** Research files use both "growth.db" (STACK.md) and "selfimprove.db" (ARCHITECTURE.md). Roadmap should settle on one name. Recommendation: "growth.db" (shorter, clearer).

---

*Research summary for: pops-claw v2.10 Self-Improvement Companion*
*Researched: 2026-03-16*
*Replaces: v2.9 Memory System Overhaul SUMMARY.md*

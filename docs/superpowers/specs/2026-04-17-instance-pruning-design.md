# Instance Pruning: Signal Over Noise

**Date:** 2026-04-17
**Approach:** Prune Now, Redesign on M1 (Approach C)
**North star:** Daily usefulness — Bob pushes fewer things, but everything he pushes matters.

## Context

After 58 phases and 10 milestones, Bob has accumulated 30+ crons, 7 agents, and ~15-20 daily Slack pushes. User feedback: only 6 of 14 daily touchpoints actually change behavior or decisions. The rest is noise that gets skimmed or ignored.

Hardware migration from EC2 t3.small to MacBook Pro M1 is planned. This spec covers Phase 1 (prune on EC2). Phase 2 (redesign on M1) is captured as vision notes only.

### What lands (keep)

1. Morning briefing (7am)
2. Commute prompt (7:15am weekdays)
3. AI builders digest (7:30am)
4. Research scan (Tue/Fri)
5. YOLO Dev (overnight)
6. Weekly review + goal check-in (Sun)

### What doesn't land (cut or reduce)

- Meeting prep, email handling (3x), AirSpace email (2h), journal nudge, evening recap, anomaly check
- Entire content pipeline (3 agents, 6 crons)
- Boss report digest: **keep** (user override)

## Phase 1: Prune (EC2, immediate)

### 1A. Pause — Content Pipeline (3 agents, 6 crons)

| Agent | Role | Action |
|-------|------|--------|
| Quill | SEO writer | Pause (disable crons, keep config) |
| Sage | Content editor | Pause (disable crons, keep config) |
| Ezra | WordPress publisher | Pause (disable crons, keep config) |

| Cron | Schedule | Action |
|------|----------|--------|
| topic-research | Tue/Fri 9am | Pause |
| writing-check | Daily | Pause |
| review-check | 2x/day | Pause |
| publish-check | Daily | Pause |
| pipeline-report | Weekly | Pause |
| stuck-check | Daily | Pause |

Content pipeline produced articles but never became a daily-useful touchpoint. Paused for reactivation — agents stay in config, crons commented out (not deleted), content.db and all articles preserved intact. Skills remain installed.

### 1B. Kill — Noisy Daily Touchpoints (4 crons)

| Cron | Schedule | Why kill |
|------|----------|---------|
| meeting-prep | 8am + 1pm | Not changing behavior |
| journal-nudge | 8pm PT | Evening prompts not sticking |
| evening-recap | End of day | Not landing |
| anomaly-check | 2x/day | Infrastructure noise |

### 1C. Reduce — Frequency Downgrades (5 crons)

| Cron | Before | After | Rationale |
|------|--------|-------|-----------|
| email-handler | 3x/day (8, 12, 18) | 1x/day (8am) | Morning catch, rest on-demand |
| airspace-email-monitor | Every 2h M-F 8-6 | 1x/day (8am) | Bundle with email handler |
| rangeos heartbeat | Every 4h | Disable | Content role gone, UAS via cron only |
| ops heartbeat | Every 2h | Every 4h | Infra monitoring doesn't need 2h |
| andyos-sync | Every 4h | Every 6h | Dashboard freshness is fine at 6h |

### 1D. Untouched — The Keepers (12 items)

| Touchpoint | Schedule | Role |
|------------|----------|------|
| morning-briefing | 7am PT | Core daily value |
| commute-prompt | 7:15am weekdays | Core daily value |
| ai-builders-digest | 7:30am PT | Core daily value |
| boss-report-digest | 2x/day (7:33am/9:33pm) | User override: keep |
| research-scan | Tue/Fri 9am | Core knowledge pipeline |
| research-dive | Weekdays 2pm | Feeds research scan |
| yolo-dev-overnight | Nightly | Core creative pipeline |
| weekly-review | Sun 8am PT | Core weekly reflection |
| weekly-goal-checkin | Sun 9am PT | Core weekly reflection |
| main heartbeat | Hourly (haiku) | Bob DM responsiveness |
| db-health-check | Sun 3am | Safety net |
| daily-memory-flush | 23:00 UTC | Memory system |
| memory-health-alert | 08:00 UTC | Safety net |

## Impact

| Metric | Before | After |
|--------|--------|-------|
| Active agents | 7 | 4 (main, ops, rangeos-reduced, landos-paused) |
| Active crons | ~30 | ~17 |
| Daily Slack pushes | ~15-20 | ~7-8 |
| Est. token spend | ~$80-100/mo | ~$50-70/mo |
| Cron containers/day | ~40+ | ~20 |

Primary win is signal-to-noise, not cost. Every push Bob makes should be something worth reading.

## Implementation

All changes are OpenClaw config edits in `~/.openclaw/openclaw.json` + crontab modifications on EC2. No code changes. No database changes. Content.db and all historical data preserved.

Steps:
1. Disable Quill, Sage, Ezra agents in config (remove from agents list or set enabled: false)
2. Remove 10 killed cron entries from openclaw.json crons section
3. Update 5 reduced cron schedules
4. Disable rangeos heartbeat
5. Restart gateway to pick up changes
6. Verify remaining crons fire correctly over 24h

Rollback: Restore `openclaw.json` from the backup taken before changes.

## Phase 2: M1 Vision (future, not designed)

Captured for migration planning. Not actionable until hardware is ready.

- **Morning OS** — Merge briefing + commute + AI builders into one cohesive morning flow
- **QMD/gbrain revival** — M1's 8-16GB RAM makes vector search + embeddings viable
- **Simplified agent model** — Possibly just Bob + Ops, capabilities via skills not agents
- **Local-first** — No EC2 cost, no SSH, no Tailscale dependency for basics
- **On-demand over scheduled** — New capabilities default to "ask Bob" not "add a cron"

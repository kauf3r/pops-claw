---
phase: 22-domain-warmup-hardening
plan: 01
subsystem: email
tags: [resend, dmarc, spf, dkim, quota, cron, sqlite, warmup]

# Dependency graph
requires:
  - phase: 19-outbound-email-foundation
    provides: "Resend API integration, email-config.json, resend-email skill, email-template.html"
  - phase: 21-inbound-email-processing
    provides: "email.db with email_conversations table, inbound processing pipeline, delivery status tracking, n8n webhook relay"
provides:
  - "WARMUP.md 5-step domain warmup checklist for Bob"
  - "Quota enforcement with daily 80/95 and monthly 2700 thresholds in SKILL.md Section 9"
  - "Monthly send tracking in email-config.json (monthly_send_count, monthly_send_month)"
  - "email-catchup cron polling Resend every 30 min for missed webhooks"
  - "Email health metrics in morning briefing (bounce/complaint rates, volume stats, threshold alerts)"
affects: [morning-briefing, resend-email-skill, email-monitoring]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Quota threshold enforcement with daily/monthly counters in JSON config"
    - "Webhook downtime fallback via polling cron with dedup against existing DB"
    - "Low-volume statistical guard: absolute numbers below minimum sample size thresholds"

key-files:
  created:
    - "/home/ubuntu/clawd/agents/main/WARMUP.md"
  modified:
    - "/home/ubuntu/.openclaw/skills/resend-email/SKILL.md"
    - "/home/ubuntu/clawd/agents/main/email-config.json"
    - "/home/ubuntu/.openclaw/cron/jobs.json"

key-decisions:
  - "Added quota checks as Check 0 (before existing rate limits) in SKILL.md Section 9 -- runs before every outbound email"
  - "Monthly counter reset uses same pattern as daily counter (compare stored month vs current month)"
  - "email-catchup cron at :15/:45 to avoid collision with existing :00/:30 crons"
  - "Email health added to morning briefing (not separate cron) -- Bob already reads email-config.json during briefing"
  - "Low-volume guards: bounce rate only meaningful at 10+ outbound, complaint rate at 20+ outbound"

patterns-established:
  - "Quota threshold pattern: JSON config counter + pre-send check + hard-block + notification"
  - "Catch-up cron pattern: API poll + DB dedup + silent-when-healthy + notify-on-recovery"

requirements-completed: []

# Metrics
duration: 9min
completed: 2026-02-17
---

# Phase 22 Plan 01: Domain Warmup & Hardening Summary

**WARMUP.md checklist, daily 80/95 + monthly 2700 quota enforcement in SKILL.md, email-catchup cron polling Resend every 30min, and morning briefing email health metrics with bounce/complaint threshold alerts**

## Performance

- **Duration:** 9 min
- **Started:** 2026-02-17T19:17:04Z
- **Completed:** 2026-02-17T19:26:09Z
- **Tasks:** 3
- **Files modified:** 4 (on EC2)

## Accomplishments
- Deployed 5-step WARMUP.md checklist (DNS verify, auth headers, inbox placement, 2-week monitor, DMARC escalation) to Bob's workspace
- Enhanced SKILL.md Section 9 with daily quota thresholds (80 warning, 95 hard-block) and monthly tracking (2700 warning/block) -- counters increment on every send, reset on day/month boundary
- Added monthly_send_count and monthly_send_month fields to email-config.json (preserving all existing fields)
- Created email-catchup cron job (isolated/sonnet/agentTurn/silent) running every 30 min at :15/:45 to recover missed webhook deliveries via Resend Received Emails API with email.db dedup
- Added Section 9: Email Health Check to morning briefing with bounce rate, complaint rate, volume stats, and threshold-based alerting (bounce >2% at 10+ volume, complaint >0.08% at 20+ volume)
- Total cron jobs now at 20 (19 existing + email-catchup)

## Task Commits

All tasks deployed to EC2 via SSH (remote deployment -- no local code changes per task):

1. **Task 1: Create WARMUP.md + update SKILL.md + update email-config.json** - EC2 deployment
2. **Task 2: Create email-catchup cron job** - EC2 deployment + gateway restart
3. **Task 3: Add email health monitoring to morning briefing** - EC2 deployment + gateway restart

**Plan metadata:** committed with SUMMARY.md + STATE.md

## Files Created/Modified
- `/home/ubuntu/clawd/agents/main/WARMUP.md` (created) - 5-step domain warmup checklist for Bob
- `/home/ubuntu/.openclaw/skills/resend-email/SKILL.md` (modified) - Section 9 rewritten with quota enforcement (Check 0: daily/monthly thresholds before Check 1/2 rate limits)
- `/home/ubuntu/clawd/agents/main/email-config.json` (modified) - Added monthly_send_count (0) and monthly_send_month ("2026-02")
- `/home/ubuntu/.openclaw/cron/jobs.json` (modified) - Added email-catchup job + Section 9 Email Health Check to morning briefing

## Decisions Made
- Renamed Section 9 from "Rate Limiting (Outbound Replies)" to "Rate Limiting and Quota Enforcement (Outbound)" to reflect expanded scope
- Quota checks run as Check 0 (highest priority, before per-sender and hard-cap checks)
- Monthly hard-block allows critical alerts to proceed (only non-critical sends blocked at 2700)
- Catch-up cron uses 120s timeout (ample for 1 API call + 100 dedup checks + processing)
- Email health in morning briefing uses /workspace/ paths (isolated session runs in Docker sandbox)
- DKIM selector names use `resend._domainkey`, `resend2._domainkey`, `resend3._domainkey` in WARMUP.md (standard Resend convention)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Gateway websocket CLI commands failed intermittently after restart (Slack socket mode pong timeouts). Resolved by waiting ~60 seconds for gateway warmup. All cron jobs and skills verified functional after stabilization.

## User Setup Required

None - no external service configuration required. All changes deployed to existing EC2 infrastructure.

## Next Phase Readiness
- WARMUP.md is ready for Bob to begin working through Steps 1-4
- Andy should monitor for 2 weeks and then manually escalate DMARC (Step 5)
- All email health monitoring is automated -- no further setup needed
- Phase 22 is the final phase of v2.2 Resend Email Integration milestone

## Self-Check: PASSED

- FOUND: 22-01-SUMMARY.md (local)
- FOUND: WARMUP.md (EC2)
- FOUND: SKILL.md (EC2)
- FOUND: monthly fields in email-config.json (EC2)
- FOUND: email-catchup in jobs.json (EC2)
- FOUND: Email Health in morning briefing (EC2)

---
*Phase: 22-domain-warmup-hardening*
*Completed: 2026-02-17*

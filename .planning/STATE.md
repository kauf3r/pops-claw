# Project State: Proactive Daily Companion

## Current Position

Phase: 20-inbound-email-infrastructure
Plan: 20-01 complete (1/2)
Status: In Progress
Milestone: v2.2 Resend Email Integration
Last activity: 2026-02-16 — Plan 20-01 complete (gateway bind change, hooks endpoint, Caddy webhook route)

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-16)

**Core value:** Proactive daily companion with autonomous content marketing pipeline at $0 incremental cost.
**Current focus:** v2.2 Resend Email Integration — give Bob dedicated email send/receive via Resend API

## Blockers

(None yet)

## Accumulated Context

### Key Architecture Decisions (v2.0)

- Bind-mount pattern for sandbox tools (read-only FS)
- Reference doc pattern for cron instructions
- SQLite for all persistent data (health.db + coordination.db)
- Vision-native receipt extraction (no external OCR)
- Embedded mode for cron (host paths, not /workspace/)

### Key Architecture Decisions (v2.1)

- SQLite (not Notion) as coordination layer — real transactions, no race conditions
- 1 shared Slack channel #content-pipeline (not 3 separate)
- No idle heartbeats for content agents — cron-only workers
- Human approval gate before WordPress publish
- content.db bind-mounted to all agents (like coordination.db pattern)
- Start slow: 1-2 articles/week
- Content agents inherit all defaults — no per-agent overrides
- PRODUCT_CONTEXT.md pattern for domain guardrails + pipeline protocols
- Multi-agent shared channel: first-match routing for DMs, cron bypasses via sessionTarget
- Content agent cron pattern: sessionTarget=agent-name, kind=agentTurn, model=sonnet, no delivery config
- Cron tz field with local time expression (not raw UTC) for DST-safe scheduling
- WordPress REST API auth via Application Passwords (Basic auth over HTTPS, no OAuth needed)
- WordPress draft-only publishing with human approval gate (WP-05) — Ezra never sets status to "publish"
- Dual-purpose publish-check cron: creates new WP drafts AND confirms human-published articles via REST API polling
- Copy-only social promotion: generate platform copy (LinkedIn, X/Twitter, Instagram), human posts manually
- Skill chaining in session reference docs: PUBLISH_SESSION.md invokes social-promoter skill after publication confirmation
- Ops reporting pattern: reference doc with SQL queries + cron trigger + embedded mode host paths
- Stuck detection pattern: SQL age-threshold queries + silent-skip alerting (no noise when healthy) + alerts to #content-pipeline (not #ops)

### Open Items

- SE-04: Gmail OAuth scope reduction (2 excess scopes, deferred)
- DP E2E: Receipt scanning human verification pending
- GV-03: No Govee sensors bound (all 11 devices are lights)
- UQ-1: LinkedIn Company Page vs personal posting
- UQ-2: Instagram Facebook Business account status
- UQ-3: WordPress existing UAS categories
- UQ-4: content.db scope — RESOLVED: bind-mounted to all agents via defaults (Plan 12-01)

## Notes

- EC2 access via Tailscale: 100.72.143.9
- OpenClaw version: v2026.2.6-3
- Memory: builtin (sqlite-vec 1536-dim + FTS5, 12 chunks indexed)
- Gateway token: rotated 2026-02-07
- Config: ~/.openclaw/openclaw.json
- Cron: ~/.openclaw/cron/jobs.json
- health.db: ~/clawd/agents/main/health.db (/workspace/health.db in sandbox)
- coordination.db: ~/clawd/coordination.db bind-mounted to /workspace/coordination.db:rw
- content.db (v2.1): ~/clawd/content.db bind-mounted to /workspace/content.db:rw
- Content agents: quill (Quill), sage (Sage), ezra (Ezra) — workspaces at ~/clawd/agents/{quill,sage,ezra}/
- PRODUCT_CONTEXT.md deployed to all 4 content agent workspaces: quill, sage, ezra, rangeos (CP-04, CP-05, CP-06)
- content-strategy skill: ~/.openclaw/skills/content-strategy/SKILL.md (ready, all agents)
- TOPIC_RESEARCH.md: ~/clawd/agents/rangeos/TOPIC_RESEARCH.md (research session reference doc)
- topic-research cron: Tue+Fri 10 AM PT, sessionTarget=rangeos, agentTurn, sonnet, 300s timeout
- writing-check cron: daily 11 AM PT, sessionTarget=quill, agentTurn, sonnet, 600s timeout
- review-check cron: 2x/day 10 AM + 3 PM PT, sessionTarget=sage, agentTurn, sonnet, 600s timeout
- seo-writer skill: ~/.openclaw/skills/seo-writer/SKILL.md (ready, all agents)
- content-editor skill: ~/.openclaw/skills/content-editor/SKILL.md (ready, all agents)
- WRITING_SESSION.md: ~/clawd/agents/quill/WRITING_SESSION.md (writing session reference doc)
- REVIEW_SESSION.md: ~/clawd/agents/sage/REVIEW_SESSION.md (review session reference doc)
- #content-pipeline Slack channel: C0ADWCMU5F0, bound to quill/sage/ezra
- Exec-approvals allowlist: gh, sqlite3, curl, gog pre-approved for all agents
- v1 milestone archived in .planning/archive/v1-multi-agent-setup/
- v2 milestone archived in .planning/milestones/
- WordPress: airspaceintegration.com, WP_SITE_URL + WP_USERNAME + WP_APP_PASSWORD in sandbox env
- wordpress-publisher skill: ~/.openclaw/skills/wordpress-publisher/SKILL.md (ready, all agents)
- PUBLISH_SESSION.md: ~/clawd/agents/ezra/PUBLISH_SESSION.md (publishing session reference doc)
- publish-check cron: daily 2 PM PT, sessionTarget=ezra, agentTurn, sonnet, 600s timeout
- social-promoter skill: ~/.openclaw/skills/social-promoter/SKILL.md (ready, all agents)
- PUBLISH_SESSION.md: updated with Step 5 (social promotion) and Step 6 (summary incl social post count)
- Total cron jobs: 19 (airspace-email-monitor added 2026-02-11)
- PIPELINE_REPORT.md: ~/clawd/agents/ops/PIPELINE_REPORT.md (weekly report reference doc)
- pipeline-report cron: Sunday 8 AM PT, sessionTarget=ops, agentTurn, sonnet, 120s timeout
- STUCK_DETECTION.md: ~/clawd/agents/ops/STUCK_DETECTION.md (daily stuck detection reference doc)
- stuck-check cron: daily 9 AM PT, sessionTarget=ops, agentTurn, sonnet, 120s timeout
- gog accounts: theandykaufman@gmail.com + Kaufman@AirSpaceIntegration.com (OAuth, client: pops-claw)
- airspace-email-monitor cron: every 30 min M-F 8-6 PT, isolated, agentTurn, sonnet, silent delivery
- Morning briefing updated with AirSpace email section (2b) between Email and Health
- Morning briefing updated with AirSpace calendar section (1b) between Calendar and Email
- Evening recap Tomorrow Preview includes AirSpace calendar with [ASI] prefix
- Weekly review Upcoming Week includes AirSpace calendar with conflict flagging
- MEETING_PREP.md scans both personal + AirSpace calendars (dual-calendar stop condition)
- resend-email skill: ~/.openclaw/skills/resend-email/SKILL.md (ready, all agents)
- email-template.html: ~/clawd/agents/main/email-template.html (/workspace/email-template.html in sandbox)
- email-config.json: ~/clawd/agents/main/email-config.json (/workspace/email-config.json in sandbox)
- Morning briefing Section 8: Email Briefing (sends via Resend API after Slack delivery)
- Gateway bind: tailnet (100.72.143.9:18789, changed from loopback in Phase 20-01)
- Hooks endpoint: http://100.72.143.9:18789/hooks/agent (token: 982cbc4b...)
- VPS (165.22.139.214): Tailscale IP 100.105.251.99, Caddy+n8n in Docker
- Webhook URL: https://n8n.andykaufman.net/webhooks/resend (Resend IP-restricted)

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 1 | Add Gmail monitoring for Kaufman@AirSpaceIntegration.com with important email highlights | 2026-02-11 | f8190d2 | [1-add-gmail-monitoring-for-kaufman-airspac](./quick/1-add-gmail-monitoring-for-kaufman-airspac/) |
| 2 | Add AirSpace calendar to morning briefing, evening recap, weekly review, and meeting prep | 2026-02-11 | 67d516e | [2-add-airspace-calendar-to-morning-briefin](./quick/2-add-airspace-calendar-to-morning-briefin/) |

---
### Key Architecture Decisions (v2.2)

- Resend API for outbound email (free tier: 100/day, 3000/month)
- Email from: bob@mail.andykaufman.net (subdomain isolation)
- RESEND_API_KEY injected via sandbox env (same pattern as Oura, Govee)
- DMARC p=none initially (permissive for testing)
- No parent DMARC on andykaufman.net
- HTML template with inline CSS palette comment block for agent reference
- Alert email soft cap: 5/day via config counter, daily reset at morning briefing
- Dual-delivery briefing: single cron sends to Slack then email (Section 8)
- resend-email skill: 7 sections covering curl pattern, composition, alerts, quotas
- email-config.json tracks recipients + daily_send_count + alert_count_today
- Morning briefing cron uses agentTurn (not systemEvent) with isolated session
- Gateway bind: tailnet (100.72.143.9:18789) instead of loopback -- enables VPS webhook relay
- Hooks token (982cbc4b...) shared between gmail hooks and inbound email hooks (single dedicated token, separate from gateway auth)
- SSH tunnel dashboard: `ssh -L 3000:100.72.143.9:18789` (must use Tailscale IP after bind change)
- VPS Tailscale IP: 100.105.251.99 (same tailnet as EC2)
- Caddy Docker: n8n_caddy container, Caddyfile at /home/officernd/n8n-production/Caddyfile
- Webhook URL: https://n8n.andykaufman.net/webhooks/resend (Caddy routes to n8n:5678 with Resend IP restriction)

---
*Last updated: 2026-02-16 — Plan 20-01 complete (endpoint infrastructure)*

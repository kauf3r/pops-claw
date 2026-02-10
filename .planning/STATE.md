# Project State: Proactive Daily Companion

## Current Position

Phase: —
Plan: —
Status: MILESTONE COMPLETE
Milestone: v2.1 Content Marketing Pipeline (shipped 2026-02-09)
Last activity: 2026-02-09 — v2.1 milestone archived

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-09)

**Core value:** Proactive daily companion with autonomous content marketing pipeline at $0 incremental cost.
**Current focus:** v2.1 shipped — planning next milestone

## Blockers

- ~~**Phase 12 human checkpoint:** Create #content-pipeline Slack channel~~ RESOLVED (C0ADWCMU5F0)
- ~~**Phase 16 human checkpoint:** Generate WordPress Application Password~~ RESOLVED (App Password configured)
- ~~**Phase 17 human checkpoint:** LinkedIn developer app + OAuth flow~~ NOT NEEDED (copy-only approach, no API)

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
- Total cron jobs: 18 (stuck-check added for Sentinel ops)
- PIPELINE_REPORT.md: ~/clawd/agents/ops/PIPELINE_REPORT.md (weekly report reference doc)
- pipeline-report cron: Sunday 8 AM PT, sessionTarget=ops, agentTurn, sonnet, 120s timeout
- STUCK_DETECTION.md: ~/clawd/agents/ops/STUCK_DETECTION.md (daily stuck detection reference doc)
- stuck-check cron: daily 9 AM PT, sessionTarget=ops, agentTurn, sonnet, 120s timeout

---
*Last updated: 2026-02-09 — v2.1 Content Marketing Pipeline milestone archived*

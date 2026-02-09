# Pops-Claw: Proactive Daily Companion

## What This Is

A proactive AI companion (Bob) running on OpenClaw v2026.2.6-3, deployed on AWS EC2 with Tailscale-only access. Bob delivers daily briefings with health/calendar/email/weather/tasks/devices/GitHub data, controls smart home devices, reviews PRs, tracks expenses, and coordinates a 4-agent multi-agent system — all proactively, before being asked.

## Core Value

Bob delivers a genuinely useful morning briefing, knows your health data, manages home devices, reviews code, and coordinates a multi-agent system — all for ~$0 incremental cost on existing Claude Pro 200.

## Requirements

### Validated

- ✓ OpenClaw v2026.2.6-3 deployed with security hardening — v2.0
- ✓ SQLite hybrid memory (builtin sqlite-vec+FTS5, 12 chunks) — v2.0
- ✓ Oura Ring health data integration (sleep, readiness, HRV, HR) — v2.0
- ✓ 7-section morning briefing (calendar, email, health, weather, tasks, Govee, GitHub) — v2.0
- ✓ Evening recap + weekly review automation — v2.0
- ✓ Model routing (Haiku/Sonnet/Opus) with session capping — v2.0
- ✓ GitHub CLI + SQLite CLI in Docker sandbox via bind-mounts — v2.0
- ✓ Govee smart home control (11 lights, room grouping) — v2.0
- ✓ Wyze scale data via Gmail parsing — v2.0
- ✓ 4-agent system (Andy, Scout, Vector, Sentinel) with coordination DB — v2.0
- ✓ Domain Slack channels (#land-ops, #range-ops, #ops) with routing — v2.0
- ✓ Heartbeat crons (4 agents, staggered) + daily standup — v2.0
- ✓ Proactive patterns (pre-meeting prep, anomaly alerts, reminders) — v2.0
- ✓ Agentic coding workflow (PR review, GitHub activity in briefing) — v2.0
- ✓ Receipt scanning + monthly expense summaries — v2.0
- ✓ Slack Socket Mode integration — v1.0
- ✓ Gmail/Calendar via gog CLI — v1.0
- ✓ Browser automation with Chromium — v1.0
- ✓ Cron/scheduled tasks operational — v1.0
- ✓ Tailscale-only secure access — v1.0

### Active

(None — start next milestone to define)

### Out of Scope

- Voice input (evaluate at day 60)
- Additional agents beyond 4
- Public API exposure
- EC2 instance upgrade
- Offline mode — real-time connectivity is core

## Context

**Shipped v2.0** with 9,347 lines across 83 files in 10 days.

**Tech stack:** OpenClaw v2026.2.6-3, AWS EC2 Ubuntu, Tailscale, Docker sandbox, SQLite (health.db + coordination.db), Slack Socket Mode, Gmail/Calendar via gog CLI, Chromium browser automation.

**Infrastructure:**
- AWS EC2 Ubuntu, Tailscale IP: 100.72.143.9
- Gateway port: 18789 (loopback only)
- Workspace: ~/clawd/ on EC2
- Config: ~/.openclaw/openclaw.json
- Service: openclaw-gateway.service (systemd user)

**Skills deployed:** oura, govee (includes Wyze), coding-assistant, receipt-scanner

**Cron jobs:** morning-briefing (7 AM PT), evening-recap (7 PM PT), weekly-review (Sun 8 AM PT), meeting-prep-scan (*/15), anomaly-check (2x daily), daily-standup (8 AM EST), monthly-expense-summary (1st of month), 4 heartbeats (15min)

**Agent Roster:**
| Agent ID | Name | Domain | Heartbeat Offset |
|----------|------|--------|------------------|
| main | Andy | Coordinator | :00 |
| landos | Scout | Land Investing | :02 |
| rangeos | Vector | UAS Operations | :04 |
| ops | Sentinel | Infra + Coding | :06 |

**Cost Model:** Claude Pro 200 ($200/mo flat) — no per-token API costs. Model routing for rate limits, not cost.

## Constraints

- **Platform**: OpenClaw on existing AWS EC2
- **Database**: SQLite (coordination + health + receipts)
- **Security**: Tailscale-only, no public exposure
- **Budget**: $0 incremental (except optional Superwhisper $8/mo)
- **Rate Limits**: Haiku for heartbeats to avoid hitting Sonnet/Opus limits

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 4 agents (Andy, Scout, Vector, Sentinel) | Match actual domains | ✓ Good — all 4 heartbeating |
| SQLite over Convex | Already exists, simpler | ✓ Good — health.db + coordination.db |
| Wyze via Gmail parsing (not SDK) | No official API | ✓ Good — works reliably |
| Haiku for heartbeats | Rate limit management | ✓ Good — reduces Sonnet/Opus usage |
| Sentinel covers infra + coding | Natural fit | ✓ Good — standup aggregation |
| Bind-mount over setupCommand | Sandbox FS is read-only | ✓ Good — gh+sqlite3 working |
| "builtin" memory backend | "sqlite-hybrid" not valid config value | ✓ Good — same sqlite-vec+FTS5 |
| Reference doc pattern for crons | Keep systemEvent messages concise | ✓ Good — MEETING_PREP.md, STANDUP.md, etc. |
| Vision-native receipt extraction | No external OCR API needed | ✓ Good — Claude vision handles it |
| Gmail scope reduction deferred | Re-auth disruption not worth it | ⚠️ Revisit — 2 excess scopes remain |

---
*Last updated: 2026-02-09 after v2.0 milestone*

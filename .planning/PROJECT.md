# Pops-Claw: Proactive Daily Companion

## What This Is

Transform Bob (OpenClaw) from a reactive assistant into a proactive daily companion with health awareness, coding assistance, multi-agent orchestration, and cost-efficient operation. Built on existing OpenClaw v2026.2.3-1 deployment on AWS EC2.

## Core Value

Bob delivers a genuinely useful morning briefing, knows your health data, manages home devices, reviews code, and coordinates a multi-agent system — all for ~$0 incremental cost on existing Claude Pro 200.

## Requirements

### Validated

- OpenClaw v2026.2.3-1 deployed on AWS EC2 — existing
- Slack Socket Mode integration — existing
- Gmail/Calendar via gog CLI — existing
- Browser automation with Chromium — existing
- Cron/scheduled tasks operational — existing
- Tailscale-only secure access — existing
- Multi-agent workspace (Phase 1 of v1 milestone) — complete

### Active

- [ ] Update to v2026.2.6 (Opus 4.6, token dashboard, safety scanner)
- [ ] SQLite hybrid memory system enabled
- [ ] Oura Ring health data integration
- [ ] Rich morning briefing (calendar + email + health + weather + tasks)
- [ ] Rate limit management via model routing
- [ ] Security hardening (discovery, dmScope, token rotation)
- [ ] MCP servers (GitHub, SQLite, Brave Search, Filesystem)
- [ ] Govee device integration (sensors + lights)
- [ ] Wyze scale via Gmail parsing
- [ ] Multi-agent gateway config (4 agents)
- [ ] Multi-agent Slack channels
- [ ] Multi-agent heartbeats and standups
- [ ] Proactive agent patterns (pre-meeting prep, anomaly alerts)
- [ ] Agentic coding workflow skill
- [ ] Document/receipt processing skill

### Out of Scope

- Voice input (evaluate at day 60)
- Additional agents beyond 4
- Public API exposure
- EC2 instance upgrade

## Context

**Infrastructure:**
- AWS EC2 Ubuntu, Tailscale IP: 100.72.143.9
- Gateway port: 18789 (loopback only)
- Workspace: ~/clawd/ on EC2
- Config: ~/.openclaw/openclaw.json
- Service: openclaw-gateway.service (systemd user)

**Cost Model:**
- Claude Pro 200 ($200/mo flat, existing) — no per-token API costs
- Model routing for rate limits, not cost
- All new integrations: $0-8/mo incremental

**Agent Roster:**
| Agent ID | Name | Domain | Heartbeat Offset |
|----------|------|--------|------------------|
| main | Andy | Coordinator | :00 |
| landos | Scout | Land Investing | :02 |
| rangeos | Vector | UAS Operations | :04 |
| ops | Sentinel | Infra + Coding | :06 |

## Constraints

- **Platform**: OpenClaw on existing AWS EC2
- **Database**: SQLite (coordination + health + receipts)
- **Security**: Tailscale-only, no public exposure
- **Budget**: $0 incremental (except optional Superwhisper $8/mo)
- **Rate Limits**: Haiku for heartbeats to avoid hitting Sonnet/Opus limits

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| 4 agents (Andy, Scout, Vector, Sentinel) | Match actual domains |
| SQLite over Convex | Already exists, simpler |
| Wyze via Gmail parsing (not SDK) | Official API doesn't exist, SDK may break |
| Haiku for heartbeats | Rate limit management, not cost |
| Sentinel covers infra + coding | Natural fit, infrastructure-adjacent |

---
*Last updated: 2026-02-07 — v2 milestone*

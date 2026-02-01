# Mission Control: Multi-Agent System

## What This Is

A coordinated multi-agent AI system built on OpenClaw that automates Andy Kaufman's land investing (LandOS) and UAS test range (RangeOS) operations. Four specialized agents work together with staggered heartbeats, shared memory, and domain-specific Slack channels to handle everything from market analysis to flight operations.

## Core Value

Agents operate autonomously within their domains, coordinating through structured handoffs, so Andy can focus on high-level decisions while the system handles routine monitoring, analysis, and coordination.

## Requirements

### Validated

- Existing single-agent OpenClaw deployment on AWS EC2 — existing
- Slack Socket Mode integration working — existing
- Gmail/Calendar via gog CLI — existing
- Browser automation with Chromium — existing
- Cron/scheduled tasks operational — existing
- Tailscale-only secure access — existing

### Active

- [ ] Multi-agent workspace structure (SOUL.md, HEARTBEAT.md per agent)
- [ ] Shared AGENTS.md operating manual
- [ ] Gateway configuration for 4 agent routes with staggered heartbeats
- [ ] SQLite coordination tables (agent_tasks, agent_messages, agent_activity)
- [ ] Domain Slack channels (#land-ops, #range-ops, #ops)
- [ ] Daily standup automation (Sentinel agent, 8 AM)
- [ ] Cross-agent memory architecture (WORKING.md, per-agent memory/)

### Out of Scope

- Convex database — SQLite sufficient for coordination, avoid new service complexity
- Additional agents beyond 4 — start simple, expand later if needed
- Real-time Pub/Sub notifications — polling via heartbeats is adequate
- Public API exposure — Tailscale-only access maintained

## Context

**Infrastructure:**
- AWS EC2 Ubuntu instance with systemd service
- Tailscale IP: 100.72.143.9
- Gateway port: 18789 (loopback only)
- Workspace: ~/clawd/ on EC2

**Source Article:**
Mission Control architecture by Bhanu Teja P - demonstrates 10 agents with SOUL files, staggered heartbeats, shared Convex database, and daily standups.

**Existing Integration:**
- pops-claw project at /Users/andykaufman/Desktop/Projects/pops-claw
- claude-life-os provides LLM-context files and pipeline database
- Beads issue tracking in use

**Agent Roster:**
| Agent ID | Name | Domain | Heartbeat Offset |
|----------|------|--------|------------------|
| main | Andy | Coordinator | :00 |
| landos | Scout | Land Investing | :02 |
| rangeos | Vector | UAS Operations | :04 |
| ops | Sentinel | Infrastructure | :06 |

## Constraints

- **Platform**: OpenClaw on existing AWS EC2 instance
- **Database**: SQLite (extend pipeline.db) — no new services
- **Security**: Tailscale-only access, no public exposure
- **Resources**: Start with t3.micro, upgrade only if needed

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 4 agents (not 10) | Match actual domains (land, UAS, ops, coordinator) | — Pending |
| SQLite over Convex | Already exists, simpler, no new service | — Pending |
| Domain Slack channels | Clear separation, easier routing | — Pending |
| 15-min heartbeats with 2-min offset | Prevents concurrent API calls, maintains responsiveness | — Pending |

---
*Last updated: 2026-02-01 after initialization*

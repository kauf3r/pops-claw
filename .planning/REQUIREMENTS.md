# Requirements: Mission Control Multi-Agent System

## v1 Requirements

### Workspace (WS)

- [ ] **WS-01**: Agent directories created on EC2 (~/clawd/agents/{main,landos,rangeos,ops}/)
- [ ] **WS-02**: Shared directory created (~/clawd/shared/)
- [ ] **WS-03**: SOUL.md persona file for Andy (main) agent
- [ ] **WS-04**: SOUL.md persona file for Scout (landos) agent
- [ ] **WS-05**: SOUL.md persona file for Vector (rangeos) agent
- [ ] **WS-06**: SOUL.md persona file for Sentinel (ops) agent
- [ ] **WS-07**: HEARTBEAT.md task file for each agent (4 files)
- [ ] **WS-08**: Shared AGENTS.md operating manual in ~/clawd/shared/
- [ ] **WS-09**: Memory directories per agent (~/clawd/agents/{agent}/memory/)
- [ ] **WS-10**: Shared memory directory (~/clawd/shared/memory/)
- [ ] **WS-11**: WORKING.md active context file in shared memory

### Gateway (GW)

- [ ] **GW-01**: Backup existing clawdbot.json before modifications
- [ ] **GW-02**: Add agent routes to clawdbot.json (4 agents)
- [ ] **GW-03**: Configure staggered heartbeat schedules (15min, 2min offset)
- [ ] **GW-04**: Map Slack channels to agents (#clawdbot→main, #land-ops→landos, #range-ops→rangeos, #ops→ops)
- [ ] **GW-05**: Restart gateway and verify all agents load

### Database (DB)

- [ ] **DB-01**: Create agent_tasks table with id, agent_id, title, status, priority, beads_issue_id, timestamps
- [ ] **DB-02**: Create agent_messages table with from_agent, to_agent, message_type, subject, body, read_at
- [ ] **DB-03**: Create agent_activity table with agent_id, activity_type, summary, created_at
- [ ] **DB-04**: Create indexes for efficient queries
- [ ] **DB-05**: Verify database accessible from all agent workspaces

### Slack (SL)

- [ ] **SL-01**: Create #land-ops Slack channel
- [ ] **SL-02**: Create #range-ops Slack channel
- [ ] **SL-03**: Create #ops Slack channel
- [ ] **SL-04**: Invite bot to all new channels
- [ ] **SL-05**: Test message routing to each agent

### Automation (AU)

- [ ] **AU-01**: Add heartbeat-main cron job (every 15min, offset :00)
- [ ] **AU-02**: Add heartbeat-landos cron job (every 15min, offset :02)
- [ ] **AU-03**: Add heartbeat-rangeos cron job (every 15min, offset :04)
- [ ] **AU-04**: Add heartbeat-ops cron job (every 15min, offset :06)
- [ ] **AU-05**: Add daily-standup cron job (8 AM EST / 13:00 UTC, ops agent)
- [ ] **AU-06**: Verify heartbeat execution logs

### Verification (VF)

- [ ] **VF-01**: Send test message to each Slack channel, verify correct agent responds
- [ ] **VF-02**: Wait one heartbeat cycle (15min), verify all 4 agents execute
- [ ] **VF-03**: Trigger manual standup, verify aggregation works
- [ ] **VF-04**: Verify agent_activity table populated with heartbeat records

## v2 Requirements (Deferred)

- Additional agents (marketing, research, etc.)
- Real-time Pub/Sub notifications
- Advanced memory consolidation (auto-summarization)
- Cross-agent task dependencies

## Out of Scope

- Convex database — SQLite sufficient, avoid new service complexity
- Public API exposure — Tailscale-only access maintained
- EC2 instance upgrade — monitor first, upgrade only if needed
- Additional messaging platforms — Slack only for v1

## Traceability

| REQ-ID | Phase | Status |
|--------|-------|--------|
| WS-01 to WS-11 | Phase 1 | Pending |
| GW-01 to GW-05 | Phase 2 | Pending |
| DB-01 to DB-05 | Phase 2 | Pending |
| SL-01 to SL-05 | Phase 3 | Pending |
| AU-01 to AU-06 | Phase 4 | Pending |
| VF-01 to VF-04 | Phase 4 | Pending |

---
*26 requirements across 6 categories*

# Roadmap: Mission Control Multi-Agent System

## Overview

| Phases | Requirements | Target |
|--------|--------------|--------|
| 4 | 26 | Multi-agent OpenClaw on EC2 |

## Phases

### Phase 1: Workspace Setup

**Goal:** Create the directory structure and agent persona files on EC2

**Requirements:** WS-01 to WS-11 (11 requirements)

**Success Criteria:**
1. All 4 agent directories exist with correct permissions
2. Each agent has SOUL.md and HEARTBEAT.md files
3. Shared AGENTS.md is readable by all agents
4. WORKING.md exists in shared memory

**Deliverables:**
- ~/clawd/agents/{main,landos,rangeos,ops}/
- ~/clawd/shared/AGENTS.md
- SOUL.md and HEARTBEAT.md per agent
- Memory directories initialized

---

### Phase 2: Gateway & Database

**Goal:** Configure multi-agent routing and create coordination database

**Requirements:** GW-01 to GW-05, DB-01 to DB-05 (10 requirements)

**Success Criteria:**
1. clawdbot.json backed up and updated with 4 agent routes
2. Gateway restarts successfully with new config
3. All 3 coordination tables created with indexes
4. Database accessible from agent workspace

**Deliverables:**
- Updated ~/.clawdbot/clawdbot.json
- SQLite tables: agent_tasks, agent_messages, agent_activity
- Verified gateway restart

---

### Phase 3: Slack Integration

**Goal:** Create domain channels and configure bot routing

**Requirements:** SL-01 to SL-05 (5 requirements)

**Success Criteria:**
1. Three new Slack channels exist (#land-ops, #range-ops, #ops)
2. Bot is member of all channels
3. Messages in each channel route to correct agent
4. Test messages receive appropriate responses

**Deliverables:**
- #land-ops channel (Scout)
- #range-ops channel (Vector)
- #ops channel (Sentinel)
- Verified routing

**Note:** Slack channel creation is manual via Slack UI

---

### Phase 4: Automation & Verification

**Goal:** Configure heartbeat cron jobs, daily standup, and verify full system

**Requirements:** AU-01 to AU-06, VF-01 to VF-04 (10 requirements)

**Success Criteria:**
1. All 4 heartbeat jobs in cron config
2. Daily standup job triggers at 8 AM EST
3. One full heartbeat cycle completes (15 min)
4. agent_activity table shows records from all agents
5. Standup aggregates data correctly

**Deliverables:**
- Updated ~/.clawdbot/cron/jobs.json
- Verified heartbeat execution
- Verified standup generation
- System operational

---

## Requirement Mapping

| Phase | Requirements | Count |
|-------|--------------|-------|
| 1 | WS-01 to WS-11 | 11 |
| 2 | GW-01 to GW-05, DB-01 to DB-05 | 10 |
| 3 | SL-01 to SL-05 | 5 |
| 4 | AU-01 to AU-06, VF-01 to VF-04 | 10 |
| **Total** | | **26** |

## Dependencies

```
Phase 1 (Workspace)
    │
    ▼
Phase 2 (Gateway + Database)
    │
    ├──────────────┐
    ▼              ▼
Phase 3         Phase 4
(Slack)      (Automation)
    │              │
    └──────┬───────┘
           ▼
      Verification
```

Phase 3 and Phase 4 can run in parallel after Phase 2 completes.

---
*Created: 2026-02-01*

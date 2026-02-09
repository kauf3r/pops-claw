# Roadmap: Proactive Daily Companion

## Overview

| Phases | Requirements | Target |
|--------|--------------|--------|
| 11 | 70 | Proactive Bob with health, coding, multi-agent |

## Phases

### Phase 1: Update, Memory & Security ✓ (2026-02-07)

**Goal:** Update OpenClaw to v2026.2.6, enable hybrid memory, harden security

**Requirements:** UF-01 to UF-05, ME-01 to ME-03, SE-01 to SE-04 (12 requirements)

**Plans:** 2 plans

Plans:
- [x] 01-01-PLAN.md -- Update OpenClaw to v2026.2.6, run safety scanner and ClawdStrike audit
- [x] 01-02-PLAN.md — Configure sqlite-hybrid memory and apply security hardening (2026-02-07)

**Success Criteria:**
1. OpenClaw v2026.2.6 running, gateway healthy
2. Safety scanner passes on ClawdStrike skill
3. Memory system active (sqlite-hybrid backend)
4. Discovery disabled, dmScope set, token rotated

**Deliverables:**
- Updated ~/.openclaw/openclaw.json (memory + security)
- Verified v2026.2.6 features (token dashboard, session capping)

---

### Phase 2: Oura Ring Integration ✓ (2026-02-08)

**Goal:** Pull health data from Oura Ring API into Bob's daily workflow

**Requirements:** HE-01 to HE-05 (5 requirements)

**Plans:** 1 plan

Plans:
- [x] 02-01-PLAN.md — Create Oura skill, configure API access, set up health snapshot storage (2026-02-08)

**Success Criteria:**
1. Oura skill created and functional
2. Sleep score, readiness, HRV, resting HR accessible
3. Daily health snapshots stored in SQLite
4. Health data available for briefing consumption

**Deliverables:**
- ~/.openclaw/skills/oura/SKILL.md
- OURA_ACCESS_TOKEN in .env
- Health snapshot storage

---

### Phase 3: Daily Briefing & Rate Limits ✓ (2026-02-08)

**Goal:** Rich morning briefing, evening recap, weekly review, and model routing

**Requirements:** BR-01 to BR-08, RL-01 to RL-04 (12 requirements)

**Plans:** 3 plans

Plans:
- [x] 03-01-PLAN.md -- Model routing (Haiku/Sonnet/Opus aliases), session history capping, heartbeat model assignment (2026-02-08)
- [x] 03-02-PLAN.md -- Expand morning briefing to 5 sections (calendar, email, health, weather, tasks), merge email digest (2026-02-08)
- [x] 03-03-PLAN.md -- Create evening recap and weekly review cron jobs (2026-02-08)

**Success Criteria:**
1. Morning briefing fires at 7 AM PT with all 5 sections
2. Evening recap fires at 7 PM PT
3. Weekly review fires Sunday 8 AM PT
4. Model routing configured (Haiku/Sonnet/Opus)
5. Session history capping enabled

**Deliverables:**
- Updated ~/.openclaw/cron/jobs.json
- Model routing in openclaw.json

---

### Phase 4: MCP Servers ✓ (2026-02-08)

**Goal:** Make coding and data tools accessible from Bob's Docker sandbox (gh, sqlite3, web search, filesystem)

**Requirements:** MC-01 to MC-06 (6 requirements)

**Plans:** 1 plan

Plans:
- [x] 04-01-PLAN.md -- Bind-mount gh+sqlite3 into sandbox, inject GitHub auth, enable elevated exec, verify all tools (2026-02-08)

**Success Criteria:**
1. GitHub CLI operational from sandbox (can list repos, PRs)
2. SQLite CLI operational from sandbox (can query databases)
3. Brave Search operational via built-in web_search tool
4. Filesystem operational via built-in read/write/edit/exec tools

**Deliverables:**
- Updated ~/.openclaw/openclaw.json (bind-mounts, GITHUB_TOKEN, elevated exec)
- GITHUB_TOKEN in .env

---

### Phase 5: Govee & Wyze Integrations ✓ (2026-02-08)

**Goal:** Device data (temp, humidity, lights, weight) accessible to Bob

**Requirements:** GV-01 to GV-06, WY-01 to WY-03 (9 requirements)

**Plans:** 2 plans

Plans:
- [x] 05-01-PLAN.md -- Govee skill (API config, sensor reading, light control, anomaly detection, SQLite storage) (2026-02-08)
- [x] 05-02-PLAN.md -- Briefing integration (Govee section in morning briefing, Wyze email parsing, weight trend in weekly review) (2026-02-08)

**Success Criteria:**
1. Govee skill reads sensor data
2. Govee skill controls lights
3. Govee data in morning briefing
4. Wyze emails parsed for weight data
5. Weight trend in weekly summary

**Deliverables:**
- ~/.openclaw/skills/govee/SKILL.md
- GOVEE_API_KEY in .env
- Wyze email parsing via existing Gmail integration

---

### Phase 6: Multi-Agent Gateway ✓ (2026-02-08)

**Goal:** Configure 4-agent routing in OpenClaw gateway with coordination DB

**Requirements:** MA-01 to MA-06 (6 requirements)

**Plans:** 2 plans

Plans:
- [x] 06-01-PLAN.md -- Backup config, verify multi-agent infrastructure, fix coordination DB access and agent HEARTBEAT.md SQL (2026-02-08)
- [x] 06-02-PLAN.md -- Restart gateway, verify all 4 agents load and route Slack messages correctly (2026-02-08)

**Success Criteria:**
1. openclaw.json backed up and updated with 4 agent routes
2. Gateway restarts with new config
3. All 3 coordination tables created with indexes
4. Database accessible from agent workspace

**Deliverables:**
- Updated ~/.openclaw/openclaw.json
- SQLite tables: agent_tasks, agent_messages, agent_activity

---

### Phase 7: Multi-Agent Slack Channels ✓ (2026-02-09)

**Goal:** Create domain Slack channels and verify bot routing

**Requirements:** MS-01 to MS-05 (5 requirements)

**Plans:** 1 plan

Plans:
- [x] 07-01-PLAN.md -- Create domain channels, invite bot, verify message routing to correct agents (2026-02-09)

**Success Criteria:**
1. Three channels exist (#land-ops, #range-ops, #ops)
2. Bot is member of all channels
3. Messages route to correct agent

**Deliverables:**
- Slack channels created and verified

**Note:** Channel creation is manual via Slack UI

---

### Phase 8: Multi-Agent Automation ✓ (2026-02-09)

**Goal:** Heartbeat crons, daily standup, full system verification

**Requirements:** AA-01 to AA-04 (4 requirements)

**Plans:** 2 plans

Plans:
- [x] 08-01-PLAN.md -- Verify heartbeat stagger offsets, create daily standup cron + STANDUP.md for Sentinel (2026-02-09)
- [x] 08-02-PLAN.md -- Verify full heartbeat cycle and standup posting to #ops (2026-02-09)

**Success Criteria:**
1. All 4 heartbeat jobs in cron config
2. Daily standup triggers at 8 AM EST
3. One full heartbeat cycle completes
4. Standup posted to #ops with all agent summaries

**Deliverables:**
- Updated ~/.openclaw/cron/jobs.json
- Verified heartbeat execution

---

### Phase 9: Proactive Agent Patterns ✓ (2026-02-08)

**Goal:** Bob acts before being asked — pre-meeting prep, anomaly alerts, reminders

**Requirements:** PP-01 to PP-03 (3 requirements)

**Plans:** 3 plans

Plans:
- [x] 09-01-PLAN.md — Calendar-driven proactive patterns: pre-meeting prep cron (every 15min) + context-aware reminders (2026-02-08)
- [x] 09-02-PLAN.md — Anomaly alerts: health metric deviations (Oura) + Govee environment thresholds (2026-02-08)
- [x] 09-03-PLAN.md — End-to-end verification of all proactive patterns with human checkpoint (2026-02-08)

**Success Criteria:**
1. Pre-meeting context sent 15min before events
2. Anomaly alerts fire on metric deviations
3. Context-aware reminders from calendar + memory

**Deliverables:**
- Cron jobs (meeting-prep-scan, anomaly-check) and reference docs (MEETING_PREP.md, ANOMALY_ALERTS.md)

---

### Phase 10: Agentic Coding Workflow

**Goal:** Bob can review PRs, create issues, and assist with coding via Slack

**Requirements:** CW-01 to CW-04 (4 requirements)

**Plans:** 2 plans

Plans:
- [ ] 10-01-PLAN.md -- Create coding-assistant SKILL.md and add open PR count to morning briefing
- [ ] 10-02-PLAN.md -- End-to-end verification of PR review command and briefing GitHub section via Slack

**Success Criteria:**
1. coding-assistant skill operational
2. "Review PR #N" command works via Slack
3. Open PR count in daily briefing

**Deliverables:**
- ~/.openclaw/skills/coding-assistant/SKILL.md

---

### Phase 11: Document Processing

**Goal:** Receipt scanning, expense tracking, monthly summaries

**Requirements:** DP-01 to DP-04 (4 requirements)

**Success Criteria:**
1. Photo -> structured receipt data extraction
2. Receipts stored in SQLite
3. Monthly expense summary generated

**Deliverables:**
- ~/.openclaw/skills/receipt-scanner/SKILL.md
- SQLite receipts table

---

## Requirement Mapping

| Phase | Requirements | Count |
|-------|--------------|-------|
| 1 | UF-01-05, ME-01-03, SE-01-04 | 12 |
| 2 | HE-01-05 | 5 |
| 3 | BR-01-08, RL-01-04 | 12 |
| 4 | MC-01-06 | 6 |
| 5 | GV-01-06, WY-01-03 | 9 |
| 6 | MA-01-06 | 6 |
| 7 | MS-01-05 | 5 |
| 8 | AA-01-04 | 4 |
| 9 | PP-01-03 | 3 |
| 10 | CW-01-04 | 4 |
| 11 | DP-01-04 | 4 |
| **Total** | | **70** |

## Dependencies

```
Phase 1 (Update/Memory/Security)
    |
    +-----------.-------------+
    v           v              v
Phase 2      Phase 3       Phase 4
(Oura)    (Briefing)     (MCP)
    |          |              |
    +----+-----+              |
         v                    |
    Phase 5 <-----------------+
  (Govee/Wyze)
         |
         v
    Phase 6
  (Multi-Agent GW)
         |
    +----+----+
    v         v
Phase 7    Phase 8
(Slack)  (Automation)
    |         |
    +----+----+
         v
    Phase 9
  (Proactive)
         |
    +----+----+
    v         v
Phase 10   Phase 11
(Coding)  (Receipts)
```

Phases 2, 3, 4 can run in parallel after Phase 1.
Phases 7, 8 can run in parallel after Phase 6.
Phases 10, 11 can run in parallel after Phase 9.

---
*Created: 2026-02-07 -- v2 milestone*

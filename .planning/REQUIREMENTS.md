# Requirements: Proactive Daily Companion

## v2 Requirements

### Update & Foundation (UF)

- [ ] **UF-01**: Update OpenClaw to v2026.2.6 via npm install -g
- [ ] **UF-02**: Run openclaw doctor --fix post-update
- [ ] **UF-03**: Restart gateway service, verify new features load
- [ ] **UF-04**: Run safety scanner on ClawdStrike skill
- [ ] **UF-05**: Re-run ClawdStrike audit post-update

### Memory (ME)

- [ ] **ME-01**: Set memory.backend = "sqlite-hybrid" in openclaw.json
- [ ] **ME-02**: Verify SQLite hybrid memory operational (70% vector + 30% BM25)
- [ ] **ME-03**: Confirm ~/clawd/agents/main/memory/ used as Markdown source

### Security (SE)

- [ ] **SE-01**: Set discovery.wideArea.enabled = false
- [ ] **SE-02**: Set session.dmScope explicitly
- [ ] **SE-03**: Rotate gateway auth token
- [ ] **SE-04**: Review Gmail OAuth scopes — reduce to minimum

### Health — Oura (HE)

- [ ] **HE-01**: Create ~/.openclaw/skills/oura/SKILL.md
- [ ] **HE-02**: Add OURA_ACCESS_TOKEN to ~/.openclaw/.env
- [ ] **HE-03**: Skill pulls sleep score, readiness, HRV, resting HR, activity
- [ ] **HE-04**: Store daily health snapshots in SQLite
- [ ] **HE-05**: Feed Oura data into morning briefing

### Briefing (BR)

- [ ] **BR-01**: Morning briefing cron at 15:00 UTC (7 AM PT) via Slack DM
- [ ] **BR-02**: Briefing section: Calendar — today's events with prep notes
- [ ] **BR-03**: Briefing section: Email — unread summary grouped by priority
- [ ] **BR-04**: Briefing section: Health — Oura sleep/readiness/HRV
- [ ] **BR-05**: Briefing section: Weather — current + forecast
- [ ] **BR-06**: Briefing section: Tasks — open items from memory
- [ ] **BR-07**: Evening recap cron at 03:00 UTC (7 PM PT)
- [ ] **BR-08**: Weekly review cron Sunday 16:00 UTC (8 AM PT)

### Rate Limits (RL)

- [ ] **RL-01**: Configure model routing: Haiku for heartbeats/acks
- [ ] **RL-02**: Configure model routing: Sonnet for briefings/analysis
- [ ] **RL-03**: Configure model routing: Opus for coding/complex reasoning
- [ ] **RL-04**: Enable session history capping

### MCP Servers (MC)

- [ ] **MC-01**: Install GitHub MCP (@modelcontextprotocol/server-github)
- [ ] **MC-02**: Install SQLite MCP (@modelcontextprotocol/server-sqlite)
- [ ] **MC-03**: Install Brave Search MCP (@modelcontextprotocol/server-brave-search)
- [ ] **MC-04**: Install Filesystem MCP for EC2
- [ ] **MC-05**: Configure all in ~/.openclaw/mcp_config.json
- [ ] **MC-06**: Add GITHUB_TOKEN to ~/.openclaw/.env

### Devices — Govee (GV)

- [ ] **GV-01**: Create ~/.openclaw/skills/govee/SKILL.md
- [ ] **GV-02**: Add GOVEE_API_KEY to ~/.openclaw/.env
- [ ] **GV-03**: Read temp/humidity from Govee sensors
- [ ] **GV-04**: Control lights (on/off, brightness, color)
- [ ] **GV-05**: Add Govee data to morning briefing
- [ ] **GV-06**: Anomaly alerts (temp drop, etc.)

### Devices — Wyze (WY)

- [ ] **WY-01**: Set up Gmail filter for Wyze weigh-in notifications
- [ ] **WY-02**: Parse weight data from Wyze emails
- [ ] **WY-03**: Add weight trend to weekly health summary

### Multi-Agent Gateway (MA)

- [ ] **MA-01**: Back up openclaw.json
- [ ] **MA-02**: Add 4 agent routes (main/Andy, landos/Scout, rangeos/Vector, ops/Sentinel)
- [ ] **MA-03**: Create SQLite coordination tables (agent_tasks, agent_messages, agent_activity)
- [ ] **MA-04**: Configure staggered heartbeat schedules (15min, 2min offsets)
- [ ] **MA-05**: Map Slack channels to agents
- [ ] **MA-06**: Restart gateway, verify all agents load

### Multi-Agent Slack (MS)

- [ ] **MS-01**: Create #land-ops Slack channel
- [ ] **MS-02**: Create #range-ops Slack channel
- [ ] **MS-03**: Create #ops Slack channel
- [ ] **MS-04**: Invite bot to all channels
- [ ] **MS-05**: Test message routing per channel

### Multi-Agent Automation (AA)

- [ ] **AA-01**: Add heartbeat crons (4 agents, :00/:02/:04/:06 offsets)
- [ ] **AA-02**: Add daily standup cron (13:00 UTC, Sentinel aggregates)
- [ ] **AA-03**: Verify full heartbeat cycle (15min)
- [ ] **AA-04**: Verify standup posted to #ops

### Proactive Patterns (PP)

- [ ] **PP-01**: Pre-meeting prep: 15min before events, send context via Slack
- [ ] **PP-02**: Anomaly alerts: health metric deviations, Govee temp drops
- [ ] **PP-03**: Context-aware reminders from calendar + memory

### Coding Workflow (CW)

- [ ] **CW-01**: Create ~/.openclaw/skills/coding-assistant/SKILL.md
- [ ] **CW-02**: Combine GitHub MCP + browser + filesystem for code review
- [ ] **CW-03**: Add open PR count to daily briefing
- [ ] **CW-04**: Slack command: "review PR #N" triggers diff review

### Document Processing (DP)

- [ ] **DP-01**: Create ~/.openclaw/skills/receipt-scanner/SKILL.md
- [ ] **DP-02**: Slack workflow: photo → extract merchant, amount, date, category
- [ ] **DP-03**: Store receipts in SQLite via MCP
- [ ] **DP-04**: Monthly expense summary cron

## Traceability

| REQ-ID | Phase | Count |
|--------|-------|-------|
| UF-01 to UF-05 | Phase 1 | 5 |
| ME-01 to ME-03 | Phase 1 | 3 |
| SE-01 to SE-04 | Phase 1 | 4 |
| HE-01 to HE-05 | Phase 2 | 5 |
| BR-01 to BR-08 | Phase 3 | 8 |
| RL-01 to RL-04 | Phase 3 | 4 |
| MC-01 to MC-06 | Phase 4 | 6 |
| GV-01 to GV-06 | Phase 5 | 6 |
| WY-01 to WY-03 | Phase 5 | 3 |
| MA-01 to MA-06 | Phase 6 | 6 |
| MS-01 to MS-05 | Phase 7 | 5 |
| AA-01 to AA-04 | Phase 8 | 4 |
| PP-01 to PP-03 | Phase 9 | 3 |
| CW-01 to CW-04 | Phase 10 | 4 |
| DP-01 to DP-04 | Phase 11 | 4 |
| **Total** | | **70** |

---
*70 requirements across 15 categories*

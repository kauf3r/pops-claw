# Best Uses for Mission Control

Your multi-agent setup with Gmail integration is now operational. Here's how to get the most out of it.

## Current Capabilities

| Agent | Channel | Domain |
|-------|---------|--------|
| Andy (main) | #popsclaw | General tasks, email digest |
| Scout (landos) | #land-ops | Land investing |
| Vector (rangeos) | #range-ops | UAS/drone operations |
| Sentinel (ops) | #ops | Infrastructure, monitoring |

## Daily Workflows

### Morning Routine (Automatic)
- **7:00 AM** - Daily standup runs
- **7:15 AM** - Email digest posts to #popsclaw

### Quick Commands

Message any agent in their channel:

| Command | What it does |
|---------|--------------|
| "status" | Agent reports health, pending tasks |
| "check coordination.db" | Shows inter-agent messages |
| "summarize yesterday" | Pulls from agent_activity table |

## Email Integration

### What Happens When Email Arrives
1. Gmail sends notification to Pub/Sub
2. Agent receives in ~5 seconds
3. Posts notification to #popsclaw

### Routing Ideas
Add rules to route emails to specific agents:

```
# In hook config, match by subject/sender:
"land" OR "acres" → Scout (#land-ops)
"drone" OR "flight" → Vector (#range-ops)
"server" OR "alert" → Sentinel (#ops)
```

## Inter-Agent Communication

Agents can collaborate via `coordination.db`:

### Leave a Message
Tell any agent:
> "Leave a message for Vector: Check airspace for tomorrow's test flight"

The message goes to `agent_messages` table. Vector picks it up on next heartbeat.

### Handoff a Task
> "Hand this research off to Scout for land analysis"

Scout receives context and continues the work.

## Best Use Cases by Agent

### Andy (Main)
- Email triage and summaries
- General questions
- Coordinating other agents
- Daily planning

### Scout (Land Ops)
- Land deal analysis
- Market research
- Due diligence checklists
- Comparable sales lookup

### Vector (Range Ops)
- Flight planning
- Airspace checks
- Equipment inventory
- Test scheduling

### Sentinel (Ops)
- System monitoring
- Weekly rollups
- Infrastructure alerts
- Cron job management

## Power User Tips

### 1. Batch Processing
Send multiple tasks to an agent:
> "Process these 5 parcels: [list]. For each, get acreage, county, and zoning."

### 2. Scheduled Reports
Add cron jobs for recurring reports:
- Weekly land deal summary (Scout)
- Monthly flight logs (Vector)
- Infrastructure health report (Sentinel)

### 3. Cross-Agent Research
> "Scout, research this parcel and have Vector check if it's suitable for drone operations"

### 4. Context Persistence
Each agent maintains conversation history. Reference previous work:
> "Remember the Johnson County parcel from last week? What was the asking price?"

## Configuration Reference

| Service | Location |
|---------|----------|
| Gateway | `~/.clawdbot/clawdbot.json` |
| Cron jobs | `~/.clawdbot/cron/jobs.json` |
| Agent workspaces | `~/clawd/agents/{id}/` |
| Coordination DB | `~/clawd/coordination.db` |
| Scripts | `~/clawd/scripts/` |

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `https://ip-172-31-7-127.tail26c537.ts.net/` | Gateway |
| `https://ip-172-31-7-127.tail26c537.ts.net:8443/` | Gmail Pub/Sub |

## Next Steps to Consider

1. **Email routing rules** - Auto-route by content to specialized agents
2. **Calendar integration** - Add Google Calendar for scheduling
3. **Slack slash commands** - `/status`, `/digest`, `/handoff`
4. **Weekly reports** - Automated summaries every Friday
5. **Browser automation** - Research tasks with web access

---
*Last updated: 2026-02-01*

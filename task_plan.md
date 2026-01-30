# Task Plan: pops-claw - Personal OpenClaw Deployment

## Goal
Secure the existing OpenClaw (Clawdbot) EC2 instance and enable full capabilities: Email/Calendar automation, Browser control, Cron/scheduled tasks, and Messaging integrations.

## Current Phase
Phase 1

## Architecture (Current)
```
EC2 Ubuntu Host
├── Gateway (port 18789)
├── ~/.clawdbot/clawdbot.json
├── ~/clawd/ (workspace)
└── Docker Sandbox
    ├── Claude Agent (Bob)
    ├── agent-browser + Chromium
    └── Tools (npm, node)
```

## Phases

### Phase 1: Security Audit & Hardening
- [ ] Audit current security posture (exposed ports, auth, credentials)
- [ ] Configure EC2 security groups (restrict 18789 to trusted IPs)
- [ ] Set up SSL/TLS for gateway
- [ ] Review credential storage in clawdbot.json
- [ ] Configure firewall (ufw)
- **Status:** in_progress

### Phase 2: Email/Calendar Integration (Gmail)
- [ ] Set up Gmail Pub/Sub for real-time notifications
- [ ] Configure OAuth 2.0 credentials
- [ ] Enable calendar read/write access
- [ ] Test email summarization and calendar management
- **Status:** pending

### Phase 3: Browser Control & Automation
- [ ] Verify agent-browser + Chromium working
- [ ] Decide network mode (none vs bridge)
- [ ] Configure browser profiles if needed
- [ ] Test web automation capabilities
- **Status:** pending

### Phase 4: Cron/Scheduled Tasks
- [ ] Enable cron + wakeups feature
- [ ] Configure webhooks
- [ ] Set up recurring automations
- [ ] Test heartbeat functionality
- **Status:** pending

### Phase 5: Additional Messaging Integrations
- [ ] Review current Slack Socket Mode setup
- [ ] Add WhatsApp/Telegram if desired
- [ ] Configure notification preferences
- **Status:** pending

### Phase 6: Production Hardening
- [ ] Set up monitoring/alerting
- [ ] Configure log rotation
- [ ] Document recovery procedures
- [ ] Final security review
- **Status:** pending

## Key Questions
1. ~~What IP addresses should have access to port 18789?~~ → **Tailscale only (100.72.143.9)**
2. ~~Do you have a domain for SSL certificate?~~ → **Not needed, Tailscale encrypts**
3. Which Google account for Gmail/Calendar integration?
4. What's acceptable network exposure for browser (none vs bridge)?

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| Keep Docker sandbox | Isolation for security |
| Slack Socket Mode | Already working, maintain |
| Tailscale-only access | Zero public attack surface, WireGuard encryption |

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
|       | 1       |            |

## Notes
- OpenClaw = rebranded Clawdbot (trademark issue with Anthropic)
- Port 18789 currently exposed - priority security concern
- Browser network mode affects web access capability

# Task Plan: pops-claw - Personal OpenClaw Deployment

## Goal
Secure the existing OpenClaw (Clawdbot) EC2 instance and enable full capabilities: Email/Calendar automation, Browser control, Cron/scheduled tasks, and Messaging integrations.

## Current Phase
ALL PHASES COMPLETE

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
- [x] Audit current security posture (exposed ports, auth, credentials)
- [x] Configure EC2 security groups (restrict 18789 to trusted IPs) → Already secure (loopback-only)
- [x] Set up SSL/TLS for gateway → Not needed (Tailscale WireGuard encrypts)
- [x] Review credential storage in clawdbot.json → 600 perms, token auth
- [x] Configure firewall (ufw) → Already active, deny-default
- **Status:** ✅ complete

### Phase 2: Email/Calendar Integration (Gmail)
- [x] Set up Gmail Pub/Sub for real-time notifications
- [x] Configure OAuth 2.0 credentials
- [x] Enable calendar read/write access
- [x] Test email summarization and calendar management
- **Status:** ✅ complete (per commit 08cb660)

### Phase 3: Browser Control & Automation
- [x] Verify agent-browser + Chromium working
- [x] Decide network mode (none vs bridge) → `bridge` for web access
- [x] Configure browser profiles if needed → Default is fine
- [x] Test web automation capabilities
- **Status:** ✅ complete

### Phase 4: Cron/Scheduled Tasks
- [x] Enable cron + wakeups feature → Enabled by default (no config key needed)
- [x] Configure webhooks → Hooks already configured (Gmail webhook active)
- [x] Set up recurring automations → Added "daily-heartbeat" (09:00 UTC daily)
- [x] Test heartbeat functionality → Test job fired successfully at 18:21 UTC
- **Status:** ✅ complete

### Phase 5: Additional Messaging Integrations
- [x] Review current Slack Socket Mode setup → Working, Socket Mode connected
- [x] Assess available integrations → 28 plugins available (Telegram, WhatsApp, Signal, Discord, etc.)
- [x] Configure notification preferences → ackReactionScope: group-mentions
- [x] Test Slack end-to-end → DM send successful
- **Status:** ✅ complete

### Phase 6: Production Hardening
- [x] Set up monitoring/alerting → health-check.sh (cron every 5 min)
- [x] Configure log rotation → /etc/logrotate.d/clawdbot (7 days, compress)
- [x] Document recovery procedures → ~/clawd/RECOVERY.md on EC2
- [x] Final security review → `clawdbot doctor` + `security audit --deep`
- **Status:** ✅ complete

## Key Questions
1. ~~What IP addresses should have access to port 18789?~~ → **Tailscale only (100.72.143.9)**
2. ~~Do you have a domain for SSL certificate?~~ → **Not needed, Tailscale encrypts**
3. Which Google account for Gmail/Calendar integration?
4. ~~What's acceptable network exposure for browser (none vs bridge)?~~ → **bridge (enables web automation)**

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| Keep Docker sandbox | Isolation for security |
| Slack Socket Mode | Already working, maintain |
| Tailscale-only access | Zero public attack surface, WireGuard encryption |
| Docker network=bridge | Required for web automation; acceptable tradeoff |

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
|       | 1       |            |

## Notes
- OpenClaw = rebranded Clawdbot (trademark issue with Anthropic)
- ~~Port 18789 currently exposed~~ → Gateway binds to loopback only, not exposed
- Browser network mode affects web access capability (currently `none` = isolated)
- Public IP 3.145.170.88 exists but ports blocked by SG/UFW

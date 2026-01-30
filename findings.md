# Findings & Decisions

## Requirements
- Secure existing OpenClaw EC2 instance
- Enable Email/Calendar automation (Gmail integration)
- Enable Browser control (web automation)
- Enable Cron/scheduled tasks (heartbeat, webhooks)
- Maintain existing Slack integration
- Production-ready security posture

## Research Findings

### OpenClaw Capabilities (from web research)
- Runs locally on user's infrastructure (EC2 in this case)
- Connects to WhatsApp, Telegram, Discord, Slack, Teams
- Browser control via dedicated Chromium instance
- Gmail Pub/Sub for real-time email notifications
- Cron + wakeups for scheduled tasks
- Webhooks for external triggers
- Skills platform (bundled, managed, workspace skills)
- Memory persistence across sessions
- "Heartbeat" for proactive actions

### Security Considerations (from research)
- Prompt injection remains unsolved industry-wide
- Exposed admin interfaces are a risk
- Credentials stored in local config files
- 34 security-related commits hardened codebase
- Recommended: strong models + security best practices
- Suitable for advanced users who understand risks

### Current Architecture (from user)
```
Host (Ubuntu EC2)
├── Gateway: port 18789
├── Config: ~/.clawdbot/clawdbot.json
├── Workspace: ~/clawd/
└── Docker Sandbox
    ├── Agent: Bob (Claude)
    ├── Browser: agent-browser + Chromium
    └── Tools: npm, node, etc.
```

External connections:
- Slack (Socket Mode) - working
- Anthropic API - working
- Internet - conditional (network=none|bridge)

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| **Tailscale-only access** | Block public 18789, access via 100.72.143.9 |
| No SSL needed | Tailscale provides WireGuard E2E encryption |
| Use Docker network=bridge for browser | Enable web automation capabilities |
| Gmail OAuth 2.0 | Secure auth for email/calendar |
| Keep Docker sandbox isolation | Security boundary for agent |

## User Environment
- Tailscale IP: 100.72.143.9
- Access method: SSH via Tailscale

## Phase 1 Security Audit (2026-01-30)

### Network Exposure

| Check | Finding | Status |
|-------|---------|--------|
| Gateway binding | `loopback` only (127.0.0.1) | ✅ Secure |
| Port 18789 external | Not reachable from internet | ✅ Secure |
| Port 22 external | Not reachable from internet | ✅ Secure |
| UFW firewall | Active, deny incoming by default | ✅ Secure |
| UFW SSH rule | Only allows 100.64.0.0/10 (Tailscale) | ✅ Secure |
| iptables INPUT | Policy DROP | ✅ Secure |
| Public IP exists | 3.145.170.88 (but blocked by SG/UFW) | ⚠️ OK |

### Credentials & Config

| Check | Finding | Status |
|-------|---------|--------|
| ~/.clawdbot/ perms | 700 (owner only) | ✅ Secure |
| clawdbot.json perms | 600 (owner only) | ✅ Secure |
| .env perms | 600 (owner only) | ✅ Secure |
| credentials/ perms | 700, files 600 | ✅ Secure |
| Gateway auth | Token-based (`mode: token`) | ✅ Secure |

### Docker Sandbox

| Check | Finding | Status |
|-------|---------|--------|
| Container running | `clawdbot-sbx-agent-main-main-20ceb99b` | ✅ Running |
| Network mode | `none` (no network access) | ⚠️ Note |
| Image | `clawdbot-sandbox:with-browser` | ✅ OK |

### Services Running

- `docker.service` - Docker daemon
- `tailscaled.service` - Tailscale agent

### Environment Variables (.env)

```
BRAVE_SEARCH_API_KEY=***
NANO_BANANA_API_KEY=***
OPENAI_API_KEY=***
```

### Gateway Config

```json
{
  "port": 18789,
  "mode": "local",
  "bind": "loopback",
  "auth": { "mode": "token", "token": "***" },
  "tailscale": { "mode": "off" }
}
```

### Summary

**Overall: SECURE** - No immediate vulnerabilities found.

Action items:
- [ ] Verify EC2 Security Group in AWS Console (cannot check via CLI)
- [ ] Consider removing public IP if not needed
- [ ] Change Docker network to `bridge` when ready for browser automation (Phase 3)

## Phase 2 Email/Calendar Integration (2026-01-30)

### Configuration

| Component | Value |
|-----------|-------|
| Google Account | andy@andykaufman.net |
| GCP Project | pops-claw |
| OAuth Client | Desktop app (client_secret.json) |
| gog CLI | v0.9.0 installed |
| Keyring | file-based (GOG_KEYRING_PASSWORD in .env) |
| Scopes | gmail.modify, gmail.settings.*, calendar |

### Files Modified

| File | Change |
|------|--------|
| ~/.clawdbot/clawdbot.json | Added hooks.gmail config |
| ~/.clawdbot/.env | Added GOG_KEYRING_PASSWORD |
| ~/.config/gogcli/client_secret.json | OAuth credentials |
| ~/.config/gogcli/config.json | keyring=file |

### Capabilities Enabled

- ✅ Read emails (gog gmail search)
- ✅ Send emails (gog gmail send)
- ✅ List calendars (gog calendar calendars)
- ✅ Read calendar events (gog calendar events)
- ✅ Create calendar events (gog calendar events create)

### Limitations

| Issue | Workaround |
|-------|------------|
| Pub/Sub IAM blocked by org policy | Use cron polling instead of push notifications |
| Real-time email notifications | Poll via cron (Phase 4) or on-demand queries |

## Issues Encountered
| Issue | Resolution |
|-------|------------|
| AWS CLI not configured | Cannot verify SG from instance - use AWS Console |
| gog auth --manual stdin issues | Use ssh -t for TTY allocation |
| Pub/Sub IAM org policy | Skip push, use pull/polling approach |
| gog keyring on headless server | Switch to file backend with GOG_KEYRING_PASSWORD |

## Resources
- OpenClaw GitHub: https://github.com/openclaw/openclaw
- OpenClaw docs: https://openclaw.ai/
- AWS EC2 Security Groups docs
- Gmail API OAuth setup

## Visual/Browser Findings
- User provided architecture diagram showing gateway, Docker, and external connections
- Network mode toggle (none vs bridge) controls browser internet access

---
*Update this file after every 2 view/browser/search operations*

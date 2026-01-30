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

## Issues Encountered
| Issue | Resolution |
|-------|------------|
|       |            |

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

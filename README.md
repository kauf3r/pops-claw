# pops-claw 🦞

Personal OpenClaw (Clawdbot) deployment on AWS EC2 with Tailscale access.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  🖥️ Host Machine (Ubuntu EC2)                                   │
│  ┌─────────────────┐  ┌──────────────┐  ┌─────────────────────┐ │
│  │ 🦞 Gateway      │  │ Config       │  │ Workspace           │ │
│  │ port 18789      │  │ ~/.clawdbot/ │  │ ~/clawd/            │ │
│  └────────┬────────┘  └──────────────┘  └──────────┬──────────┘ │
│           │                                         │           │
│           ▼                                         ▼           │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  🐳 Docker Sandbox                                          ││
│  │  ┌──────────────┐  ┌───────────────┐  ┌──────────────────┐ ││
│  │  │ 🤖 Bob       │  │ 🌐 Browser    │  │ 🔧 Tools         │ ││
│  │  │ (Claude)     │  │ + Chromium    │  │ npm, node, etc.  │ ││
│  │  └──────────────┘  └───────────────┘  └──────────────────┘ ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
    ┌──────────┐       ┌─────────────┐      ┌──────────┐
    │ 💬 Slack │       │ 🧠 Anthropic│      │ 🌍 Web   │
    │ Socket   │       │ API         │      │ (bridge) │
    └──────────┘       └─────────────┘      └──────────┘
```

## Access

- **Tailscale IP:** `[tailscale-ip]`
- **Gateway:** `http://[tailscale-ip]:18789`
- **No public access** - Tailscale only

## Capabilities

| Feature | Status | Notes |
|---------|--------|-------|
| Slack integration | ✅ Working | Socket Mode |
| Email/Calendar | 🔲 Planned | Gmail Pub/Sub |
| Browser control | 🔲 Planned | Chromium in Docker |
| Cron/Webhooks | 🔲 Planned | Scheduled tasks |

## Security

- Access restricted to Tailscale network
- Traffic encrypted via WireGuard (Tailscale)
- Agent runs in Docker sandbox
- Credentials in `~/.clawdbot/clawdbot.json`

## Setup

See [task_plan.md](task_plan.md) for implementation phases.

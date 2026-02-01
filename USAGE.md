# OpenClaw (Bob) - Usage Guide

## Quick Access

```bash
# SSH to server
ssh pops-claw

# Or explicitly
ssh -i ~/.ssh/clawdbot-key.pem ubuntu@100.72.143.9
```

**Web UI:** http://100.72.143.9:18789 (Tailscale only)

---

## Architecture

```
Your Mac (Tailscale) ──────► EC2 Ubuntu (100.72.143.9)
                              ├── Gateway :18789 (loopback)
                              ├── ~/.clawdbot/clawdbot.json
                              ├── ~/clawd/ (workspace)
                              └── Docker Sandbox
                                  ├── Agent "Bob" (Claude)
                                  ├── Chromium Browser
                                  └── Node.js tools
```

---

## Interacting with Bob

### Via Slack
DM the bot directly or mention in #clawdbot channel.

### Via Web UI
1. Connect to Tailscale
2. Open http://100.72.143.9:18789
3. Chat in the web interface

### Via CLI (on EC2)
```bash
ssh pops-claw
source ~/.nvm/nvm.sh
npx clawdbot chat "What can you help me with?"
```

---

## Capabilities

| Feature | Status | Notes |
|---------|--------|-------|
| Slack messaging | ✅ | Socket Mode, DM + channels |
| Gmail read/send | ✅ | OAuth via gog CLI |
| Calendar access | ✅ | Read/write events |
| Web browsing | ✅ | Chromium in Docker |
| Scheduled tasks | ✅ | Cron jobs configured |
| File operations | ✅ | ~/clawd/ workspace |

---

## Common Tasks

### Check Status
```bash
ssh pops-claw "systemctl --user status clawdbot-gateway"
```

### View Logs
```bash
# Live logs
ssh pops-claw "journalctl --user -u clawdbot-gateway -f"

# Today's log file
ssh pops-claw "tail -100 /tmp/clawdbot/clawdbot-\$(date +%Y-%m-%d).log"
```

### Restart Gateway
```bash
ssh pops-claw "systemctl --user restart clawdbot-gateway"
```

### Run Health Check
```bash
ssh pops-claw "~/clawd/scripts/health-check.sh"
```

### Run Doctor
```bash
ssh pops-claw "source ~/.nvm/nvm.sh && npx clawdbot doctor"
```

---

## Gmail/Calendar

### Read Recent Emails
```bash
ssh pops-claw "source ~/.nvm/nvm.sh && gog gmail search --query 'newer_than:1d' --max 5"
```

### Send Email
```bash
ssh pops-claw "source ~/.nvm/nvm.sh && gog gmail send --to someone@example.com --subject 'Test' --body 'Hello'"
```

### List Calendars
```bash
ssh pops-claw "source ~/.nvm/nvm.sh && gog calendar calendars"
```

### View Today's Events
```bash
ssh pops-claw "source ~/.nvm/nvm.sh && gog calendar events --timeMin \$(date -I) --timeMax \$(date -I -d '+1 day')"
```

---

## Scheduled Jobs

### List Jobs
```bash
ssh pops-claw "cat ~/.clawdbot/cron/jobs.json | jq '.[] | {name, schedule: .schedule.expr, enabled}'"
```

### Current Jobs
| Job | Schedule | Purpose |
|-----|----------|---------|
| daily-heartbeat | 09:00 UTC daily | Health check prompt |
| short-ribs-reminder | Jan 25 @ 22:00 | Yearly reminder |

### Add New Job
Edit `~/.clawdbot/cron/jobs.json` or use the web UI.

---

## Adding Messaging Channels

### Telegram
```bash
ssh pops-claw
source ~/.nvm/nvm.sh
npx clawdbot channels add --channel telegram --token "YOUR_BOT_TOKEN"
```

### Discord
```bash
npx clawdbot channels add --channel discord --token "YOUR_BOT_TOKEN"
```

### WhatsApp (requires QR scan)
```bash
npx clawdbot channels add --channel whatsapp
# Follow QR code instructions
```

---

## Troubleshooting

### Gateway Not Responding
```bash
ssh pops-claw
systemctl --user status clawdbot-gateway
systemctl --user restart clawdbot-gateway
```

### Slack Bot Offline
```bash
ssh pops-claw "source ~/.nvm/nvm.sh && npx clawdbot channels status"
# If disconnected, restart gateway
```

### Auth Token Expired
```bash
ssh pops-claw
source ~/.nvm/nvm.sh
npx clawdbot doctor
# If token expired, run: claude setup-token
```

### Disk Space Low
```bash
ssh pops-claw "df -h / && docker system prune -f"
```

---

## Config Files

| File | Purpose |
|------|---------|
| `~/.clawdbot/clawdbot.json` | Main config (Slack, hooks, agents) |
| `~/.clawdbot/.env` | API keys (Brave, OpenAI) |
| `~/.clawdbot/credentials/` | Auth tokens |
| `~/.clawdbot/cron/jobs.json` | Scheduled jobs |
| `~/.config/gogcli/` | Gmail OAuth config |

### Edit Config
```bash
ssh pops-claw "nano ~/.clawdbot/clawdbot.json"
# After editing:
ssh pops-claw "systemctl --user restart clawdbot-gateway"
```

---

## Backup

### Manual Backup
```bash
ssh pops-claw "tar -czf ~/clawd/backup-\$(date +%Y%m%d).tar.gz ~/.clawdbot/clawdbot.json ~/.clawdbot/.env ~/.clawdbot/credentials ~/.clawdbot/cron/jobs.json"
```

### Download Backup
```bash
scp pops-claw:~/clawd/backup-*.tar.gz ~/Desktop/
```

---

## Security Notes

- **No public access**: Gateway binds to localhost only
- **Tailscale required**: All access via 100.72.143.9
- **UFW active**: Default deny, SSH only from Tailscale
- **Docker sandboxed**: Agent runs in isolated container
- **Config protected**: 600 permissions on sensitive files

---

## Key URLs

| Resource | URL |
|----------|-----|
| Web UI | http://100.72.143.9:18789 |
| EC2 Console | AWS Console → EC2 |
| Tailscale Admin | https://login.tailscale.com/admin |
| GCP Console | https://console.cloud.google.com (project: pops-claw) |

---

## Recovery

Full recovery procedures: `ssh pops-claw "cat ~/clawd/RECOVERY.md"`

### Quick Recovery
```bash
# 1. Check if running
ssh pops-claw "systemctl --user status clawdbot-gateway"

# 2. Start if stopped
ssh pops-claw "systemctl --user start clawdbot-gateway"

# 3. Check logs if failing
ssh pops-claw "journalctl --user -u clawdbot-gateway -n 50"

# 4. Run doctor for diagnostics
ssh pops-claw "source ~/.nvm/nvm.sh && npx clawdbot doctor --fix"
```

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
- [x] Change Docker network to `bridge` when ready for browser automation (Phase 3) ✅ Done

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

## Phase 3 Browser Control (2026-01-30)

### Browser Stack

| Component | Version | Location |
|-----------|---------|----------|
| Chromium | 145.0.7632.6 | /root/.cache/ms-playwright/chromium-1208 |
| agent-browser | 0.8.5 | Global npm package |
| Playwright | (via agent-browser) | /root/.npm/_npx/*/playwright-core |
| Docker image | clawdbot-sandbox:with-browser | 1.69GB |

### Network Mode Change

| Setting | Before | After |
|---------|--------|-------|
| `agents.defaults.sandbox.docker.network` | `none` | `bridge` |

**Tradeoff:**
- `none` = complete isolation, no internet (more secure, no web automation)
- `bridge` = standard Docker NAT, can access internet (less secure, enables web automation)

**Decision:** Use `bridge` because web automation is a core use case. Container still sandboxed from host.

### Test Results

```bash
# With network: none
$ docker run --network=none ... node browser-test.js
Browser test FAILED: page.goto: net::ERR_INTERNET_DISCONNECTED

# With network: bridge
$ docker run --network=bridge ... node browser-test.js
Page title: Example Domain
H1 content: Example Domain
Browser test PASSED!

# agent-browser CLI test
$ npx agent-browser open https://example.com && npx agent-browser snapshot -c
✓ Example Domain
  https://example.com/
  - heading "Example Domain" [ref=e1] [level=1]
  - paragraph: This domain is for use in documentation examples...
  - link "Learn more" [ref=e2]
```

### Files Modified

| File | Change |
|------|--------|
| ~/.clawdbot/clawdbot.json | `docker.network`: `none` → `bridge` |

### Remaining Considerations

- Browser has full internet access when container spawns
- Consider adding iptables rules inside container if need to restrict destinations
- Existing container was stopped; new sessions will use bridge network

## Phase 4 Cron/Scheduled Tasks (2026-01-30)

### Architecture Discovery

The cron feature is **enabled by default** in Clawdbot. No config key is needed in clawdbot.json.

| Component | Location |
|-----------|----------|
| Jobs store | ~/.clawdbot/cron/jobs.json |
| Run logs | ~/.clawdbot/cron/runs/{jobId}.jsonl |
| Service module | cron/service/ops.js |

### Job Schema

```json
{
  "id": "unique-job-id",
  "agentId": "main",
  "name": "job-name",
  "enabled": true,
  "createdAtMs": 1769797100000,
  "updatedAtMs": 1769797100000,
  "schedule": {
    "expr": "0 9 * * *",
    "kind": "cron"
  },
  "sessionTarget": "main",
  "wakeMode": "next-heartbeat",
  "payload": {
    "kind": "systemEvent",
    "text": "Message to deliver"
  },
  "state": {
    "nextRunAtMs": 1769850000000,
    "lastRunAtMs": 1769797260003,
    "lastStatus": "ok",
    "lastDurationMs": 22
  }
}
```

### Configured Jobs

| Job ID | Name | Schedule | Description |
|--------|------|----------|-------------|
| 32564f8e-... | short-ribs-reminder | 0 22 25 1 * | Yearly (Jan 25 @ 22:00 UTC) |
| heartbeat-daily-001 | daily-heartbeat | 0 9 * * * | Daily health check (09:00 UTC) |

### Webhooks

Webhooks configured in `hooks` section of clawdbot.json:
- Gmail hook: `/hooks/gmail` - triggers agent on new emails
- Internal hooks: boot-md, session-memory, command-logger

### Test Results

| Test | Time | Result |
|------|------|--------|
| Cron service start | 18:18:56 UTC | jobs:3, nextWakeAtMs set |
| Test job fire | 18:21:00 UTC | status:ok, durationMs:22 |
| Logs written | 18:21:00 UTC | runs/test-immediate-001.jsonl created |

### Notes

- Cron expressions use standard 5-field format (minute, hour, day, month, weekday)
- Jobs survive gateway restart (persisted to disk)
- `wakeMode: "next-heartbeat"` = delivers on next agent heartbeat
- `wakeMode: "now"` = immediately wakes agent
- Run logs stored as JSON Lines (.jsonl) per job

## Phase 5 Messaging Integrations (2026-01-30)

### Current Setup

| Channel | Mode | Status |
|---------|------|--------|
| Slack | Socket Mode | ✅ Running, connected |

### Slack Configuration

```json
{
  "mode": "socket",
  "enabled": true,
  "botToken": "xoxb-...",
  "appToken": "xapp-...",
  "groupPolicy": "allowlist",
  "dm": {
    "policy": "allowlist",
    "allowFrom": ["U0CUJ5CAF"]
  },
  "channels": {
    "#clawdbot": { "allow": true }
  }
}
```

### Slack Capabilities

| Feature | Support |
|---------|---------|
| Chat types | direct, channel, thread |
| Reactions | ✅ |
| Threads | ✅ |
| Media | ✅ |
| Native commands | ✅ |
| Actions | send, broadcast, react, read, edit, delete, pin/unpin |

### Available Messaging Plugins (28 total)

| Plugin | ID | Status | Requirements |
|--------|-----|--------|--------------|
| **Slack** | slack | ✅ loaded | Bot + App tokens |
| **Telegram** | telegram | disabled | Bot token from @BotFather |
| **WhatsApp** | whatsapp | disabled | Auth session (QR scan) |
| **Signal** | signal | disabled | signal-cli + phone number |
| **Discord** | discord | disabled | Bot token |
| **iMessage** | imessage | disabled | macOS + Messages.app |
| **Google Chat** | googlechat | disabled | Workspace app |
| **MS Teams** | msteams | disabled | Azure bot registration |
| **Matrix** | matrix | disabled | Homeserver + access token |
| **Mattermost** | mattermost | disabled | Bot account |
| **Nextcloud Talk** | nextcloud-talk | disabled | Nextcloud instance |
| **BlueBubbles** | bluebubbles | disabled | BlueBubbles server |
| **LINE** | line | disabled | LINE bot credentials |
| **Nostr** | nostr | disabled | Private key (NIP-04 DMs) |
| **Zalo** | zalo | disabled | Zalo OA credentials |
| **Tlon/Urbit** | tlon | disabled | Ship + login code |

### Adding New Channels

To enable a messaging channel:

```bash
# Example: Add Telegram
clawdbot channels add --channel telegram --token "YOUR_BOT_TOKEN"

# Example: Add Discord
clawdbot channels add --channel discord --token "YOUR_BOT_TOKEN"

# Example: Add WhatsApp (requires QR scan)
clawdbot channels add --channel whatsapp
```

After adding, enable the plugin:
```bash
clawdbot config set plugins.entries.telegram.enabled true
```

### Notification Preferences

Current `messages` config:
```json
{
  "ackReactionScope": "group-mentions"
}
```

Options:
- `ackReactionScope`: Controls when bot acknowledges with reactions
  - `"all"` - React to all messages
  - `"group-mentions"` - Only react when mentioned in groups
  - `"dm-only"` - Only react in DMs

### Test Results

| Test | Command | Result |
|------|---------|--------|
| Channel status | `clawdbot channels status` | Slack: enabled, running |
| DM send | `clawdbot message send --channel slack --target U0CUJ5CAF --message "test"` | ✅ Message ID returned |

### Recommendations

1. **Current setup is sufficient** - Slack Socket Mode working well
2. **Telegram** - Easy to add if needed (just bot token)
3. **Signal** - Requires signal-cli daemon; more complex setup
4. **WhatsApp** - Requires WhatsApp Web session; unofficial integration
5. **Discord** - Straightforward if you have a Discord server

### Known Limitations

- WhatsApp integration is unofficial (uses WhatsApp Web protocol)
- Signal requires maintaining signal-cli daemon
- iMessage only works on macOS
- Some plugins (Zalo, LINE) may have regional restrictions

## Phase 6 Production Hardening (2026-01-30)

### Monitoring Assessment

| Component | Status | Notes |
|-----------|--------|-------|
| CloudWatch Agent | Not installed | Not needed for single instance |
| Prometheus/Grafana | Not installed | Overkill for personal use |
| systemd user service | ✅ Enabled | Auto-restart on failure |
| Custom health check | ✅ Created | Cron every 5 min |

### Logging

| Log Location | Purpose | Retention |
|--------------|---------|-----------|
| /tmp/clawdbot/clawdbot-YYYY-MM-DD.log | Gateway runtime logs | 7 days (logrotate) |
| ~/.clawdbot/logs/commands.log | Command history | Manual |
| ~/.clawdbot/cron/runs/*.jsonl | Cron job execution | Manual |
| journalctl --user -u clawdbot-gateway | systemd logs | Per journald config |

### Health Monitoring

Created `/home/ubuntu/clawd/scripts/health-check.sh`:
- Checks gateway process (systemd)
- Checks disk space (alert >85%)
- Checks memory (alert <200MB available)
- Logs to ~/clawd/scripts/health.log
- Runs via crontab every 5 minutes

### Recovery Procedures

Created `/home/ubuntu/clawd/RECOVERY.md` on EC2 with:
- Quick reference commands
- Scenario-based recovery steps
- Config backup procedures
- Emergency contact info

### Security Audit Results

```
clawdbot security audit --deep
Summary: 0 critical · 1 warn · 2 info

WARN: gateway.trusted_proxies_missing
  → Not an issue since gateway binds to loopback only

INFO: config.secrets.hooks_token_in_config
  → Acceptable since config perms are 600
```

### Final Security Checklist

| Check | Status |
|-------|--------|
| UFW firewall active | ✅ deny incoming, SSH Tailscale-only |
| Gateway binds loopback | ✅ 127.0.0.1:18789 |
| Config file perms | ✅ 600 (clawdbot.json, .env) |
| Credentials dir perms | ✅ 700 |
| Docker network | ⚠️ bridge (required for web automation) |
| systemd auto-restart | ✅ Restart=always, RestartSec=5 |
| Log rotation | ✅ 7 days, compressed |
| Health monitoring | ✅ cron every 5 min |

### Outstanding Items

| Item | Priority | Notes |
|------|----------|-------|
| Claude CLI token refresh | Medium | Expires in 8h, run `claude setup-token` |
| EC2 Security Group verification | Low | Cannot verify from instance, use AWS Console |
| Consider removing public IP | Low | Currently blocked by SG/UFW anyway |

## Version Update: v2026.1.24-3 → v2026.2.3-1 (2026-02-06)

### Migration Summary

| Component | Before | After |
|-----------|--------|-------|
| Package | `clawdbot` | `openclaw` |
| Binary | `clawdbot` | `openclaw` |
| State dir | `~/.clawdbot/` | `~/.openclaw/` (symlinked from old) |
| Config | `~/.clawdbot/clawdbot.json` | `~/.openclaw/openclaw.json` |
| Service | `clawdbot-gateway.service` | `openclaw-gateway.service` |
| Entrypoint | `dist/entry.js` | `dist/index.js` |
| Auth | `anthropic:claude-cli` | `anthropic:manual` (setup-token) |
| Logs | `/tmp/clawdbot/` | `/tmp/openclaw/` |
| Public IP | 3.145.170.88 | Changed after stop/start (check AWS Console) |

### Service File Changes

Added `EnvironmentFile=/home/ubuntu/.openclaw/.env` to load API keys and `GOG_KEYRING_PASSWORD` automatically.

### Update Procedure (for future reference)

```bash
# 1. Backup
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.bak

# 2. Update
npm install -g openclaw@latest

# 3. Migrate
openclaw doctor --fix

# 4. Update service entrypoint if needed
# Check: openclaw doctor (will flag mismatches)
# Fix: sed -i 's|old-entry|new-entry|' ~/.config/systemd/user/openclaw-gateway.service

# 5. Restart
systemctl --user daemon-reload && systemctl --user restart openclaw-gateway.service

# 6. Verify
journalctl --user -u openclaw-gateway.service --since '1 min ago' | tail -20
```

## Resources
- OpenClaw GitHub: https://github.com/openclaw/openclaw
- OpenClaw docs: https://openclaw.ai/
- OpenClaw Updating Guide: https://docs.openclaw.ai/install/updating
- AWS EC2 Security Groups docs
- Gmail API OAuth setup

## Visual/Browser Findings
- User provided architecture diagram showing gateway, Docker, and external connections
- Network mode toggle (none vs bridge) controls browser internet access

---
*Update this file after every 2 view/browser/search operations*

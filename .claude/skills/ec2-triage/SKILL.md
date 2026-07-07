---
name: ec2-triage
description: Diagnose and fix pops-claw EC2 infrastructure problems — gateway down, crons failing, disk/log bloat, Docker sandbox errors, tailscaled instability, stale data. Use when asked to "run an ops check", "triage the server", "Bob is down", "crons are failing", "check EC2 health", or when any Slack alert from Bob reports an agent/cron failure.
---

# EC2 Triage — pops-claw

Structured diagnosis for the OpenClaw deployment at `ubuntu@100.72.143.9` (Tailscale-only, key `~/.ssh/clawdbot-key.pem`). Most incidents here have happened before — check the symptom table before investigating from scratch.

## Step 1 — Run the health check

Run the `/ops` command (`.claude/commands/ops.md`) — it executes 10 checks in ONE SSH connection (disk, Docker, cron failures, log sizes, zombies, Tailscale, gog OAuth age, memory, uptime, gateway) and defines the OK/WARN/ALERT thresholds. Use its compound-SSH script verbatim; do not reinvent it.

Notes baked into `/ops` that you must respect:
- Cron sandbox containers (`openclaw-sbx-agent-*-cron-*`) are WARN only at **"Up 3 hours"+** — Docker rounds up, and `container-cleanup.sh` reaps ≥2h containers hourly.
- gog refresh tokens are permanent (app is published); the age threshold is informational.

If SSH itself fails: Tailscale on the Mac may be down (`/Applications/Tailscale.app/Contents/MacOS/Tailscale status`), the instance may be stopped (AWS console), or — if it worked minutes ago — tailscaled on the host may be restart-looping (it IS your SSH transport). Wait 2 minutes and retry before escalating.

## Step 2 — Match symptoms to known root causes

| Symptom | Known cause | Reference |
|---|---|---|
| ALL isolated crons fail, `main` sessions fine; "Duplicate mount point: /tmp" | Explicit bind to a path OpenClaw now auto-mounts (upgrade regression) | `docs/solutions/runtime-errors/docker-duplicate-mount-point-tmp.md` |
| Syslog >500MB, disk climbing, thousands of tailscaled lines, months-old `client_time` timestamps | systemd `WatchdogSec` drop-in SIGABRTing tailscaled (~66s cycle), logtail backlog replay | `docs/solutions/runtime-errors/tailscaled-watchdog-sigabrt-flood.md` |
| A DB file is 0 bytes inside the sandbox but healthy on host | Docker mount shadowing (never fully resolved); workaround: host-side query | `docs/solutions/integration-issues/content-db-zero-bytes-in-docker-sandbox.md` |
| Cron runs "successfully" but consumer sees stale data | Script writing to `~/clawd/agents/main/*.db` instead of canonical `~/clawd/db/*.db` — happened to health.db AND observability.db | `findings.md` ("Oura Health Sync — Stale Data Fix", "Token Optimization Pass") |
| Boot warning: gmail-watcher `invalidArgument: Invalid topicName` | `hooks.gmail.topic` pointed at stale GCP project `rock-range-485422-h3`; push is now disabled by design — do NOT re-enable without the documented path | `progress.md` (Session 2026-05-25) |
| Slack delivery silently fails from a cron | Payload uses bare channel name instead of `channel:ID` format | Phase 33-04 fix, CLAUDE.md Mistake #8 |
| Multiple isolated jobs fail simultaneously, main jobs succeed | Docker container creation issue (mounts/image/network) — inspect `journalctl --user -u openclaw-gateway` for daemon errors | duplicate-mount doc, Prevention section |

Useful direct probes:

```bash
SSH="ssh -i ~/.ssh/clawdbot-key.pem -o ConnectTimeout=10 ubuntu@100.72.143.9"
$SSH 'journalctl --user -u openclaw-gateway -n 100 --no-pager'
$SSH 'journalctl -u tailscaled --since "24 hours ago" | grep -c "Started tailscaled"'  # expect 0-1, not 800+
$SSH 'sudo tail -50000 /var/log/syslog | awk "{print \$5}" | sort | uniq -c | sort -rn | head'  # syslog top talkers
$SSH 'ls -l /etc/systemd/system/tailscaled.service.d/ 2>/dev/null'  # drop-ins (watchdog.conf must NOT exist)
```

## Step 3 — Fix under the rules

1. Back up any config before touching it: `cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.bak-$(date +%Y%m%d-%H%M%S)`. Config edits follow the `openclaw-config-edit` skill.
2. Destructive actions (deleting data, disabling services, pruning beyond dangling images) → stop and ask Andy first, with a recommended default.
3. Restart the gateway only once per batch of changes: `systemctl --user restart openclaw-gateway`.
4. Verify the ORIGINAL symptom is gone with fresh command output (next cron run, journal clean, file size stable) — not just that the service restarted.

## Step 4 — Write it down (mandatory)

- Append a dated session entry to `progress.md`: symptom, root cause, changes (with backup path), verification output.
- If it was a real diagnosis (not a known repeat), write `docs/solutions/{runtime-errors|integration-issues}/<slug>.md` with the existing frontmatter format (title, category, component, severity, date_solved, status, tags) and Symptom / Investigation / Root Cause / Solution / Prevention sections — copy the shape of the tailscaled doc.
- Commit on a branch, PR to main (never direct push).

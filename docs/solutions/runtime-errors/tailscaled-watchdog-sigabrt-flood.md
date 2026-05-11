---
title: "Tailscaled SIGABRT loop floods syslog to 1.2GB"
category: runtime-errors
component: ec2-infrastructure
severity: high
date_solved: 2026-05-11
status: resolved
tags: [tailscale, systemd, watchdog, syslog, ec2, logrotate, sigabrt]
related_beads: []
affected_agents: [all]
---

# Tailscaled SIGABRT loop floods syslog to 1.2GB

## Symptom

`/ops` health check flagged log size ALERT — `/var/log/syslog` at 524M and `/var/log/syslog.1` at 686M (1.2GB combined). Root partition at 63%, memory available at 652MiB (WARN). No app errors, no cron failures, no Docker issues — just two enormous syslog files growing fast.

A focused investigation showed `tailscaled` was authoring almost all of it:
- 378K `derp-2` messages in the full syslog
- 96K `cloudinfo.GetPublicIPs: AWS:` entries
- Thousands of `wg: [cC9Ln] - Handshake did not complete after N seconds, retrying`
- Recent samples had `client_time` timestamps from **2026-02-12** but log timestamps from 2026-05-11 — months-old logtail buffer being replayed live

SSH to the host timed out mid-investigation because `tailscaled` (the SSH transport) was actively restarting.

## Investigation Steps

1. **Top-talker analysis** — `sudo tail -50000 /var/log/syslog | awk '{print $5}' | sort | uniq -c | sort -rn | head` showed `tailscaled` dominating message counts.
2. **Restart counter** — `journalctl -u tailscaled --since "24 hours ago" | grep -c "Started\|Stopping\|killed"` returned **843** — ~35 restarts/hour, one every ~100s.
3. **Process check (mid-investigation)** — `tailscale status` returned "doesn't appear to be running" briefly, confirming live restart cycle.
4. **Stale timestamp clue** — recent syslog entries carried `client_time` JSON fields from `2026-02-12`. This was the logtail upload buffer flushing 3 months of backlog on every restart.
5. **Exit reason** — `journalctl -u tailscaled` showed clockwork:
   ```
   18:08:14  systemd: Killing process (tailscaled) with signal SIGABRT
   18:08:14  systemd: Main process exited, code=exited, status=2/INVALIDARGUMENT
   18:09:20  ... (66s later, same pattern)
   18:10:27  ... (67s later)
   18:11:34  ... (67s later)
   ```
   Exit status `2/INVALIDARGUMENT` from SIGABRT = systemd watchdog kill signature.
6. **Watchdog config inspection** —
   ```
   $ sudo cat /etc/systemd/system/tailscaled.service.d/watchdog.conf
   [Service]
   Restart=always
   RestartSec=5
   WatchdogSec=60
   ```
   And `systemctl show tailscaled` confirmed `WatchdogUSec=1min`.
7. **Eliminated alternatives** —
   - Not OOM: memory peak 20.1MB, `OOMScoreAdjust=-900` already protective.
   - Not the unreachable peer `[cC9Ln]`: handshake retries were a symptom of the restart cycle, not the cause.
   - Not Tailscale upstream bug: stock unit file does NOT enable `WatchdogSec`.

## Root Cause

**Tailscale 1.96.4 does not emit `sd_notify WATCHDOG=1` pings on the default code path.** The `WatchdogSec=60` drop-in told systemd to expect a ping every 60s; when none arrived, systemd SIGABRTed the process. Result: ~1440 restarts/day.

Each restart:
1. New process inherits the unfinished logtail upload buffer.
2. `log.tailscale.com` upload is partially blocked/backlogged.
3. Process exits before draining → buffer persists in `/var/lib/tailscale/`.
4. Next restart re-attempts the flush → spills entries to syslog instead.
5. Syslog grows by tens of MB per cycle.

Compounding: the drop-in was labeled "protection" in project memory (`MEMORY.md` line 21: "watchdog overrides on tailscaled/sshd") which masked the bug as a feature for an unknown duration.

## Solution

Remove the watchdog drop-in. Keep the OOM protection drop-in (`oom.conf`) unchanged — that is the real protection.

```bash
# 1. Back up the broken drop-in
sudo cp /etc/systemd/system/tailscaled.service.d/watchdog.conf \
        ~/tailscaled-watchdog.conf.bak

# 2. Remove the drop-in
sudo rm /etc/systemd/system/tailscaled.service.d/watchdog.conf

# 3. Apply and restart
sudo systemctl daemon-reload
sudo systemctl restart tailscaled

# 4. Verify watchdog disabled
sudo systemctl show tailscaled --property=WatchdogUSec
# Expected: WatchdogUSec=0

# 5. Manual syslog rotation (logrotate size threshold won't trip for huge files)
sudo journalctl --rotate
sudo journalctl --vacuum-size=200M
sudo mv /var/log/syslog /var/log/syslog.manual-rotate.$(date +%Y%m%d-%H%M%S)
sudo kill -HUP $(pidof rsyslogd)
sudo gzip /var/log/syslog.manual-rotate.* /var/log/syslog.1
```

**Post-fix verification:**
- `tailscaled` PID held for 24+ minutes (vs ~60s before)
- `WatchdogUSec=0`, `Restart=on-failure`
- Memory: 21.9 MB (healthy)
- Disk: 63% → 59% (~1.5GB reclaimed)
- Available memory: 652Mi → 768Mi
- Active syslog: 524M → 298 bytes

## Prevention

### Never re-add `WatchdogSec` to tailscaled

Tailscale's stock packaging deliberately omits systemd watchdog because the daemon does not implement watchdog ping on standard paths. Any drop-in that adds `WatchdogSec` will SIGABRT the process on schedule.

If a future upgrade adds watchdog support, Tailscale will ship it in the stock unit — don't reintroduce it via a custom drop-in.

### Keep the OOM drop-in

`/etc/systemd/system/tailscaled.service.d/oom.conf` with `OOMScoreAdjust=-900` is the correct protective layer for the 2GB t3.small instance. Do not remove this.

### sshd / ssh.service drop-ins — DO NOT TOUCH

`/etc/systemd/system/ssh.service.d/watchdog.conf` exists but only sets `Restart=always` + `RestartSec=5` — no `WatchdogSec`. Effective `WatchdogUSec=0`. The drop-in is misnamed but harmless. Leave it.

`sshd.service` has no drop-in directory and defaults to `WatchdogUSec=infinity` (disabled). No action needed.

### Diagnostic one-liner for syslog floods

When `/ops` flags log size ALERT, first identify the talker:

```bash
sudo tail -50000 /var/log/syslog | awk '{print $5}' | sort | uniq -c | sort -rn | head -10
```

If `tailscaled` dominates, check:
1. Are recent entries' `client_time` fields stale (months old)? → logtail backlog
2. `journalctl -u tailscaled | grep -c "Killing process"` over 24h → systemd watchdog
3. `systemctl show tailscaled --property=WatchdogUSec` → should be `0`

### Monitor for recurrence

Add to `/ops` script (or a cron sentinel): alert if `tailscaled` restart count >5/day. Stock behavior is zero unplanned restarts.

```bash
RESTARTS=$(sudo journalctl -u tailscaled --since "24 hours ago" | grep -c "Started tailscaled")
[ "$RESTARTS" -gt 5 ] && echo "ALERT: tailscaled restarted $RESTARTS times in 24h"
```

## Cross-References

- Memory: `~/.claude/projects/-Users-andykaufman-Desktop-Projects-pops-claw/memory/lesson_tailscaled_watchdog_flood.md`
- Memory (corrected): `MEMORY.md` line 21 — was "watchdog overrides on both" (misleading), now describes the drop-in as removed.
- Related: prior `/ops` runs flagged "syslog bloat" in lessons learned but never traced to root cause.
- Backup file on EC2: `~/tailscaled-watchdog.conf.bak`

## Indicators This Is Happening Again

- `/ops` ALERTs on Log Sizes
- `tailscaled` Memory column in `systemctl status` resets to a fresh value frequently
- SSH timeouts to EC2 mid-session (Tailscale transport flapping)
- `journalctl -u tailscaled` shows `SIGABRT` + `status=2/INVALIDARGUMENT` in clockwork intervals
- Syslog lines contain `client_time` timestamps significantly older than the line's own timestamp

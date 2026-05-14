---
title: "Docker 'Duplicate mount point: /tmp' blocks all isolated cron jobs"
category: runtime-errors
component: openclaw-sandbox
severity: high
date_solved: 2026-03-22
status: resolved
tags: [docker, bind-mount, openclaw, sandbox, cron, tmp]
related_beads: []
affected_agents: [landos, rangeos, ops, quill, sage, ezra]
---

# Docker "Duplicate mount point: /tmp" blocks all isolated cron jobs

## Symptom

All cron jobs running in `isolated` (Docker sandbox) mode fail immediately with:

```
Error response from daemon: Duplicate mount point: /tmp
```

Slack DM from Bob: `:warning: Agent failed before reply: Error response from daemon: Duplicate mount point: /tmp`

Affected: every cron job with `target: isolated` — heartbeats (landos, rangeos, ops), email-handler, voice-notes-processor, daily-standup, writing-check, publish-check, review-check, daily-memory-flush. Only `target: main` jobs (which bypass Docker) continued working.

Model fallback cascade also visible in logs — haiku fails, falls back to opus, then sonnet, all hitting the same Docker error.

## Investigation Steps

1. **Checked Slack DM** — Bob reported the error at 10:03 AM PT
2. **Checked journalctl** — `lane task error` entries on every isolated cron run, all with "Duplicate mount point: /tmp"
3. **Checked openclaw.json** — Found explicit bind: `"/home/ubuntu/clawd/sandbox-tmp:/tmp:rw"` in `agents.defaults.sandbox.docker.binds`
4. **Identified conflict** — OpenClaw v2026.3.11+ auto-mounts `/tmp` as a tmpfs inside containers. The explicit bind creates a second `/tmp` mount, which Docker rejects.
5. **Confirmed `main` sessions unaffected** — `heartbeat-main-15m` and `morning-briefing` ran fine because they execute on the host, not in Docker.

## Root Cause

**OpenClaw version upgrade introduced automatic `/tmp` tmpfs mount in Docker containers.** The explicit bind mount `sandbox-tmp:/tmp:rw` (added in an earlier phase to provide writable tmp space) now conflicts with the built-in mount, causing Docker to reject container creation with "Duplicate mount point."

The `dangerouslyAllowReservedContainerTargets: true` flag allowed the bind to target `/tmp`, but it can't override OpenClaw's own internal mount.

## Solution

Removed the explicit `/tmp` bind from `openclaw.json`:

```python
# Fix applied via Python on EC2
import json
with open("/home/ubuntu/.openclaw/openclaw.json") as f:
    cfg = json.load(f)
binds = cfg["agents"]["defaults"]["sandbox"]["docker"]["binds"]
binds = [b for b in binds if ":/tmp:" not in b]
cfg["agents"]["defaults"]["sandbox"]["docker"]["binds"] = binds
with open("/home/ubuntu/.openclaw/openclaw.json", "w") as f:
    json.dump(cfg, f, indent=2)
```

Then restarted the gateway:
```bash
systemctl --user restart openclaw-gateway.service
```

Verified: `heartbeat-ops-15m` ran successfully on next schedule — no `/tmp` error. Container started normally with OpenClaw's built-in `/tmp` tmpfs.

## Prevention

- **After OpenClaw upgrades**: Check `journalctl --user -u openclaw-gateway.service` for Docker mount errors within the first hour. New versions may change container mount behavior.
- **Don't bind to reserved Docker paths** (`/tmp`, `/dev`, `/proc`, `/sys`) unless absolutely necessary — upstream may start managing these internally.
- **Monitor isolated cron health**: If multiple isolated jobs fail simultaneously while `main` jobs succeed, suspect Docker container creation issues (mounts, image, network).
- **The `dangerouslyAllow*` flags are a smell**: They exist because the mount targets reserved paths. When OpenClaw starts managing those paths itself, conflicts are inevitable.

## Cross-References

- Phase 55 MEMORY.md: sandbox-tmp reference removed
- Existing solution: [content-db-zero-bytes-in-docker-sandbox](../integration-issues/content-db-zero-bytes-in-docker-sandbox.md) — related Docker mount ordering issue
- openclaw.json `agents.defaults.sandbox.docker.binds` — 16 binds remaining after fix

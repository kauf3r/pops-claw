---
phase: 24-critical-security-update
plan: 01
subsystem: infra
tags: [openclaw, npm, systemd, security-update, cve-patch, ec2, tailscale]

# Dependency graph
requires:
  - phase: 01-update-memory-security
    provides: "Previous update procedure pattern and EC2 infrastructure"
provides:
  - OpenClaw v2026.2.17 running on EC2 (CVE-2026-25253 patched)
  - Pre-update backup at ~/backups/pre-v2026.2.17/ for instant rollback
  - Gateway active on tailnet (100.72.143.9:18789)
  - gog OAuth tokens verified intact (both accounts)
  - Config migrated to v2026.2.17 schema (dmPolicy aliases)
affects: [24-02-PLAN, phase-25, phase-28]

# Tech tracking
tech-stack:
  added: [openclaw@2026.2.17]
  patterns: [npm-global-update, systemd-user-service, doctor-fix-cycle, pre-update-backup]

key-files:
  created:
    - /home/ubuntu/backups/pre-v2026.2.17/openclaw (entry point backup)
    - /home/ubuntu/backups/pre-v2026.2.17/openclaw.json (config snapshot)
    - /home/ubuntu/backups/pre-v2026.2.17/gog-keyring/ (OAuth token backup)
    - /home/ubuntu/backups/pre-v2026.2.17/doctor-output.txt (pre-update baseline)
    - /home/ubuntu/backups/pre-v2026.2.17/security-audit.txt (pre-update baseline)
    - /home/ubuntu/backups/pre-v2026.2.17/verified-bundle.json (ClawdStrike baseline)
  modified:
    - /home/ubuntu/.npm-global/lib/node_modules/openclaw/ (npm update v2026.2.6-3 -> v2026.2.17)
    - /home/ubuntu/.openclaw/openclaw.json (doctor migration: dmPolicy aliases, contextPruning/heartbeat reorg)
    - /home/ubuntu/.config/systemd/user/openclaw-gateway.service (version string + token alignment)

key-decisions:
  - "Aligned CLAWDBOT_GATEWAY_TOKEN in service file with gateway.auth.token from config (doctor flagged mismatch)"
  - "Config schema migration accepted: dm.policy -> dmPolicy, dm.allowFrom -> allowFrom (v2026.2.14+ format)"
  - "Rollback via npm install -g openclaw@2026.2.6-3 (not binary copy, since openclaw is a Node.js package)"

patterns-established:
  - "Pre-update backup: binary + config + gog keyring + doctor output + security audit + ClawdStrike bundle"
  - "Token alignment: verify CLAWDBOT_GATEWAY_TOKEN matches gateway.auth.token after doctor --fix"

requirements-completed: [SEC-01]

# Metrics
duration: 8min
completed: 2026-02-18
---

# Phase 24 Plan 01: OpenClaw Update Summary

**OpenClaw updated from v2026.2.6-3 to v2026.2.17 on EC2 patching CVE-2026-25253 (CVSS 8.8 RCE), with full pre-update backup, config schema migration, and gateway token alignment**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-18T05:25:17Z
- **Completed:** 2026-02-18T05:32:48Z
- **Tasks:** 2
- **Files modified:** 9 (6 created on EC2, 3 modified on EC2)

## Accomplishments
- Captured complete pre-update baseline: doctor output, security audit, ClawdStrike bundle, config, gog keyring, entry point
- Updated OpenClaw from v2026.2.6-3 to v2026.2.17 via npm (CVE-2026-25253 patched)
- Doctor auto-migrated config schema: `channels.slack.dm.policy/allowFrom` to `dmPolicy/allowFrom` format, reorganized `contextPruning` and `heartbeat` to agent defaults
- Aligned gateway auth token in systemd service file with config (doctor flagged mismatch)
- Verified gateway active on tailnet 100.72.143.9:18789, health OK, no errors in logs
- Verified gog OAuth tokens intact for both accounts (personal + AirSpace)

## Task Commits

This plan was executed entirely on EC2 via SSH -- no local repository files were created or modified. All changes are infrastructure-level on the remote host.

1. **Task 1: Capture pre-update security baseline and create full backup** - No local commit (EC2-only: created ~/backups/pre-v2026.2.17/ with 6 files)
2. **Task 2: Update OpenClaw to v2026.2.17 and verify gateway + connectivity** - No local commit (EC2-only: npm update, doctor --fix, service file update, restart)

## Files Created/Modified

**On EC2 (created):**
- `/home/ubuntu/backups/pre-v2026.2.17/openclaw` - Entry point script backup (796B)
- `/home/ubuntu/backups/pre-v2026.2.17/openclaw.json` - Config snapshot (9,771B)
- `/home/ubuntu/backups/pre-v2026.2.17/gog-keyring/` - OAuth token backup (2 token files)
- `/home/ubuntu/backups/pre-v2026.2.17/doctor-output.txt` - Pre-update doctor baseline (4,236B)
- `/home/ubuntu/backups/pre-v2026.2.17/security-audit.txt` - Pre-update security audit (1,523B)
- `/home/ubuntu/backups/pre-v2026.2.17/verified-bundle.json` - ClawdStrike baseline (38,342B)

**On EC2 (modified):**
- `/home/ubuntu/.npm-global/lib/node_modules/openclaw/` - npm package updated to v2026.2.17
- `/home/ubuntu/.openclaw/openclaw.json` - Doctor migrated dmPolicy aliases, reorganized contextPruning/heartbeat
- `/home/ubuntu/.config/systemd/user/openclaw-gateway.service` - Version string v2026.2.17, token aligned with config

## Decisions Made
- **Token alignment**: Doctor flagged CLAWDBOT_GATEWAY_TOKEN in service file did not match `gateway.auth.token` in config. Updated service file to use the config token value. This may explain intermittent auth issues that existed before the update.
- **Config migration accepted**: Doctor migrated `dm.policy`/`dm.allowFrom` to new aliases (`dmPolicy`/`allowFrom`). These are the v2026.2.14+ config format. The migration is purely structural, no behavioral change.
- **Rollback strategy**: The "binary backup" is actually the npm entry point script (796B). True rollback is `npm install -g openclaw@2026.2.6-3` + restore config from backup. Config backup is the critical rollback artifact.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Gateway auth token mismatch in service file**
- **Found during:** Task 2 (doctor --fix output)
- **Issue:** `CLAWDBOT_GATEWAY_TOKEN` in systemd service file (`ac12cdd0...`) did not match `gateway.auth.token` in openclaw.json (`tQnJMk...`). Doctor flagged this as "service token is missing."
- **Fix:** Updated service file to use the config token value for consistency
- **Files modified:** `/home/ubuntu/.config/systemd/user/openclaw-gateway.service`
- **Verification:** Gateway started successfully with health OK, no auth errors in logs
- **Committed in:** N/A (EC2-only change)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Token alignment was necessary for correct gateway authentication. No scope creep.

## Issues Encountered
- `gog auth list` over SSH fails without `GOG_KEYRING_PASSWORD` exported (the env var is in `.env` but `source` doesn't work with non-export format). Gateway service loads it via `EnvironmentFile` so gog works correctly at runtime. Verification required `export $(grep GOG_KEYRING_PASSWORD ~/.openclaw/.env)` workaround.
- Pre-update security audit showed 1 critical (camofox-browser plugin dangerous code patterns) + gateway probe timeout. Both are pre-existing findings, not related to the update.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- OpenClaw v2026.2.17 is running with CVE-2026-25253 patched
- Gateway is healthy on tailnet with correct auth token alignment
- Platform is ready for SecureClaw plugin installation (Plan 24-02)
- DM sessions were cleared by gateway restart -- user should DM Bob to re-establish session before relying on cron delivery
- Pre-existing doctor warnings (deprecated auth profile, legacy session keys) remain Phase 28 scope

## Self-Check: PASSED

- SUMMARY.md: FOUND
- EC2 backup files (6/6): ALL FOUND
- OpenClaw version: 2026.2.17 (correct)
- Gateway status: active (correct)

---
*Phase: 24-critical-security-update*
*Completed: 2026-02-18*

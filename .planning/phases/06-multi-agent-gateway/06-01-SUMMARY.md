---
phase: 06-multi-agent-gateway
plan: 01
subsystem: infra
tags: [multi-agent, sqlite, coordination-db, docker, bind-mount, openclaw]

# Dependency graph
requires:
  - phase: 01-workspace-setup
    provides: "OpenClaw v2026.2.6-3 on EC2 with 4-agent config"
provides:
  - "Verified 4-agent gateway config with backup"
  - "Coordination DB schema validated (3 tables, 6 indexes)"
  - "HEARTBEAT.md schema reference in all 4 agent workspaces"
  - "Coordination DB accessible from Docker sandbox via bind-mount"
  - "Debian 12-compatible sqlite3 binary for sandbox"
affects: [07-multi-agent-slack-channels, 08-multi-agent-automation]

# Tech tracking
tech-stack:
  added: [sqlite3-compat (Debian 12 build for sandbox)]
  patterns: [coordination-db-bind-mount, schema-reference-in-agent-docs]

key-files:
  created:
    - "~/clawd/sqlite3-compat (Debian 12-compatible sqlite3 binary)"
  modified:
    - "~/.openclaw/openclaw.json (bind-mounts for coordination.db + sqlite3-compat)"
    - "~/clawd/agents/main/HEARTBEAT.md (schema reference added)"
    - "~/clawd/agents/landos/HEARTBEAT.md (schema reference + DB path fixed)"
    - "~/clawd/agents/rangeos/HEARTBEAT.md (schema reference added)"
    - "~/clawd/agents/ops/HEARTBEAT.md (schema reference added)"

key-decisions:
  - "Replaced symlinks with bind-mount for coordination.db (Docker can't resolve symlinks outside mount)"
  - "Built Debian 12-compatible sqlite3 from sandbox apt-get (host binary glibc 2.39 vs sandbox 2.36)"
  - "Schema reference section added to all HEARTBEAT.md files (prevents column name guessing)"

patterns-established:
  - "Coordination DB bind-mount: /home/ubuntu/clawd/coordination.db:/workspace/coordination.db:rw"
  - "Sandbox-compatible binaries: extract from matching Debian image, store in ~/clawd/"

# Metrics
duration: 5min
completed: 2026-02-08
---

# Phase 6 Plan 1: Multi-Agent Gateway Verification Summary

**Validated 4-agent gateway config, fixed coordination DB sandbox access (symlink->bind-mount), added schema reference to all HEARTBEAT.md files**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-08T21:43:49Z
- **Completed:** 2026-02-08T21:49:12Z
- **Tasks:** 2
- **Files modified:** 6 (all on EC2, no local repo files)

## Accomplishments
- Timestamped backup of openclaw.json created (20260208)
- Verified all 4 agent routes (main/Bob, landos/Scout, rangeos/Vector, ops/Sentinel), 4 Slack bindings, 4 channel allowlists, 5 heartbeat crons (4 staggered + 1 daily)
- Coordination DB verified: 3 tables (agent_tasks, agent_messages, agent_activity) with 6 indexes and 4 triggers
- All 4 HEARTBEAT.md files updated with explicit schema reference (body, not message)
- Fixed Scout (landos) HEARTBEAT.md referencing wrong DB path (mission-control.db -> coordination.db)
- Resolved Docker symlink problem: removed workspace symlinks, added direct bind-mount
- Built Debian 12-compatible sqlite3 binary to fix glibc version mismatch (host 2.39 vs sandbox 2.36)
- Confirmed coordination DB queries succeed from inside agent sandbox

## Task Commits

All work was remote EC2 operations via SSH -- no local repository files were created or modified by these tasks. Per-task local commits were not applicable.

1. **Task 1: Backup openclaw.json and verify 4-agent gateway config** - Remote only (backup + verification on EC2)
2. **Task 2: Verify coordination DB schema and fix agent HEARTBEAT.md SQL** - Remote only (schema fixes + bind-mount config on EC2)

**Plan metadata:** See final commit below.

## Files Created/Modified (on EC2)
- `~/.openclaw/openclaw.json.bak-20260208` - Timestamped config backup
- `~/.openclaw/openclaw.json` - Updated bind-mounts (coordination.db + sqlite3-compat)
- `~/clawd/sqlite3-compat` - Debian 12-compatible sqlite3 binary for sandbox
- `~/clawd/agents/main/HEARTBEAT.md` - Added coordination DB schema reference
- `~/clawd/agents/landos/HEARTBEAT.md` - Added schema reference, fixed DB path
- `~/clawd/agents/rangeos/HEARTBEAT.md` - Added coordination DB schema reference
- `~/clawd/agents/ops/HEARTBEAT.md` - Added coordination DB schema reference

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Replace symlinks with bind-mount for coordination.db | Docker can't resolve symlinks pointing outside the workspace mount boundary |
| Build Debian 12-compatible sqlite3 binary | Host sqlite3 (Ubuntu 24.04, glibc 2.39) crashes in sandbox (Debian 12, glibc 2.36) |
| Add schema reference to all HEARTBEAT.md | Prevents agents from guessing column names (body vs message mismatch) |
| Fix landos DB path reference | Was referencing non-existent mission-control.db |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed landos HEARTBEAT.md wrong DB path**
- **Found during:** Task 2 (HEARTBEAT.md review)
- **Issue:** Scout's HEARTBEAT.md referenced `/home/ubuntu/clawd/shared/mission-control.db` which doesn't exist; should be coordination.db
- **Fix:** Changed DB path to `/workspace/coordination.db`
- **Files modified:** ~/clawd/agents/landos/HEARTBEAT.md
- **Verification:** grep confirms correct path

**2. [Rule 3 - Blocking] Removed symlinks, added bind-mount for coordination.db**
- **Found during:** Task 2 (sandbox access test)
- **Issue:** Docker can't resolve symlinks pointing to paths outside the bind-mount; `coordination.db -> /home/ubuntu/clawd/coordination.db` fails inside container since /home/ubuntu/clawd/ is not mounted
- **Fix:** Removed all 4 workspace symlinks; added `/home/ubuntu/clawd/coordination.db:/workspace/coordination.db:rw` bind-mount to openclaw.json
- **Files modified:** ~/.openclaw/openclaw.json, removed symlinks in 4 agent dirs
- **Verification:** `docker run ... sqlite3 /workspace/coordination.db "SELECT count(*) FROM agent_messages"` returns 1

**3. [Rule 3 - Blocking] Replaced host sqlite3 with Debian 12-compatible binary**
- **Found during:** Task 2 (sandbox access test, after bind-mount fix)
- **Issue:** Host sqlite3 binary (Ubuntu 24.04) requires glibc 2.38+ symbols (`GLIBC_2.38` for libm.so.6) not available in sandbox image (Debian 12, glibc 2.36). Also `sqlite3_stmt_explain` symbol missing from sandbox's older libsqlite3.
- **Fix:** Installed sqlite3 inside sandbox image via `docker run ... apt-get install sqlite3`, extracted binary to `~/clawd/sqlite3-compat`, updated bind-mount from `/usr/bin/sqlite3` to `~/clawd/sqlite3-compat:/usr/bin/sqlite3:ro`
- **Files modified:** ~/.openclaw/openclaw.json, ~/clawd/sqlite3-compat (new)
- **Verification:** `docker run ... sqlite3 /workspace/coordination.db ".tables"` returns all 3 tables

---

**Total deviations:** 3 auto-fixed (1 bug, 2 blocking)
**Impact on plan:** All fixes necessary for sandbox DB access. Plan anticipated the symlink issue and provided fallback path. sqlite3 glibc mismatch was discovered and fixed as blocking issue. No scope creep.

## Issues Encountered
- Docker symlink resolution: Anticipated by the plan (noted "symlink WILL NOT resolve in sandbox"). Plan provided the bind-mount fallback path.
- sqlite3 glibc mismatch: Not anticipated. The host OS (Ubuntu 24.04) has a newer glibc than the sandbox image (Debian 12). Previously worked per memory notes, suggesting the sandbox image may have been rebuilt since last test. Resolved by extracting a matching binary from the sandbox image's own package manager.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- All 4 agents verified with correct config, crons, and Slack bindings
- Coordination DB accessible from all agent sandboxes via bind-mount
- HEARTBEAT.md files have explicit schema reference preventing column name confusion
- Ready for Phase 6 Plan 2 (multi-agent coordination patterns)

## Self-Check: PASSED

- FOUND: 06-01-SUMMARY.md (local)
- FOUND: ~/.openclaw/openclaw.json.bak-20260208 (EC2)
- FOUND: ~/clawd/sqlite3-compat (EC2)
- FOUND: main HEARTBEAT.md schema reference (EC2)
- FOUND: landos HEARTBEAT.md schema reference (EC2)
- FOUND: rangeos HEARTBEAT.md schema reference (EC2)
- FOUND: ops HEARTBEAT.md schema reference (EC2)
- FOUND: coordination.db bind-mount in openclaw.json (EC2)

Note: No per-task local commits -- all work was remote EC2 operations via SSH.

---
*Phase: 06-multi-agent-gateway*
*Completed: 2026-02-08*

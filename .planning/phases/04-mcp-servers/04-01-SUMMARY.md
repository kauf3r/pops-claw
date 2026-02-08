---
phase: 04-mcp-servers
plan: 01
subsystem: infra
tags: [gh, sqlite3, docker, sandbox, bind-mount, elevated-exec]

requires:
  - phase: 01-update-memory-security
    provides: "OpenClaw v2026.2.6 running, gateway service, sandbox config"
  - phase: 02-oura-ring
    provides: "health.db in workspace for sqlite3 testing"
provides:
  - "gh CLI accessible from sandbox via bind-mount"
  - "sqlite3 CLI accessible from sandbox via bind-mount"
  - "GITHUB_TOKEN injected into sandbox env"
  - "Elevated exec enabled as host-tool fallback"
  - "Web search and filesystem tools confirmed working"
affects: [05-govee-wyze, 10-coding-workflow]

tech-stack:
  added: [gh-cli-in-sandbox, sqlite3-in-sandbox, elevated-exec]
  patterns: [bind-mount-host-binaries, sandbox-env-injection]

key-files:
  created:
    - .planning/phases/04-mcp-servers/04-01-config-changes.md
  modified:
    - /home/ubuntu/.openclaw/openclaw.json
    - /home/ubuntu/.openclaw/.env

key-decisions:
  - "Bind-mount over setupCommand: sandbox has read-only FS, apt-get fails"
  - "gh is statically linked — simple binary mount works"
  - "sqlite3 is dynamic but all deps (libsqlite3, libreadline, libz, libtinfo) already in image"
  - "Elevated exec restricted to Andy's Slack ID (U0CUJ5CAF)"

patterns-established:
  - "Bind-mount pattern: mount host binaries into sandbox at same path with :ro"
  - "Belt-and-suspenders auth: both GITHUB_TOKEN env var AND gh config dir mounted"

duration: ~25min
completed: 2026-02-08
---

# Phase 4, Plan 01: MCP Servers Summary

**gh and sqlite3 bind-mounted into sandbox, GitHub auth injected, elevated exec enabled — all 4 tool categories verified via Slack**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-02-08T19:04Z
- **Completed:** 2026-02-08T19:15Z
- **Tasks:** 2
- **Files modified:** 3 (openclaw.json, .env, config-changes.md)

## Accomplishments
- GitHub CLI operational from sandbox (can list repos, PRs)
- SQLite CLI operational from sandbox (can query health.db)
- Brave Search confirmed working via built-in web_search tool
- Filesystem access confirmed working via built-in read/write/edit/exec tools
- Elevated exec enabled as fallback for host commands
- All 5 verification tests passed via Slack DM

## Task Commits

1. **Task 1: Install gh and sqlite3 in sandbox and inject GitHub auth** - `6740e55` (feat)
2. **Task 1 fix: bind-mount instead of setupCommand** - `a55f117` (fix)
3. **Task 2: Human verification via Slack** - all 5 tests passed

## Files Created/Modified
- `/home/ubuntu/.openclaw/openclaw.json` - Added sandbox bind-mounts, GITHUB_TOKEN env, elevated exec, gh config mount
- `/home/ubuntu/.openclaw/.env` - Added GITHUB_TOKEN for gateway process
- `.planning/phases/04-mcp-servers/04-01-config-changes.md` - Documents all changes applied

## Decisions Made
- Bind-mount host binaries instead of setupCommand (sandbox FS is read-only)
- gh statically linked = simple mount; sqlite3 dynamic but deps pre-exist in image
- Elevated exec as fallback, restricted to Andy's Slack user ID
- Belt-and-suspenders GitHub auth: both env var AND config dir mounted

## Deviations from Plan

### Auto-fixed Issues

**1. [Blocking] setupCommand fails on read-only filesystem**
- **Found during:** Task 1 (sandbox container creation)
- **Issue:** `apt-get update` fails with "Read-only file system" for `/var/lib/apt/lists/partial`
- **Fix:** Removed setupCommand entirely, bind-mounted `/usr/bin/gh` and `/usr/bin/sqlite3` from host
- **Files modified:** ~/.openclaw/openclaw.json
- **Verification:** Gateway restarted, all 5 Slack tests passed
- **Committed in:** a55f117

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Essential pivot. Bind-mount is actually cleaner than setupCommand — no install delay on container creation.

## Issues Encountered
- setupCommand with apt-get is incompatible with read-only sandbox filesystem. Bind-mount pattern is the correct approach for adding host binaries to sandbox.

## User Setup Required
None - GITHUB_TOKEN already present on host from prior `gh auth login`.

## Next Phase Readiness
- All MCP tool categories working: GitHub, SQLite, web search, filesystem
- Phase 5 (Govee & Wyze) unblocked — can use sqlite3 for sensor data storage
- Phase 10 (Coding Workflow) unblocked — gh CLI available for PR reviews

---
*Phase: 04-mcp-servers*
*Completed: 2026-02-08*

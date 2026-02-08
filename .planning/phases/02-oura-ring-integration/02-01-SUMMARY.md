---
phase: 02-oura-ring-integration
plan: 01
subsystem: health
tags: [oura, health-data, sqlite, api-integration, skill]

requires:
  - phase: 01-update-memory-security
    provides: "OpenClaw v2026.2.6 with memory backend and gateway service"
provides:
  - "Oura Ring skill for Bob (sleep, readiness, HRV, activity)"
  - "health_snapshots SQLite table with daily health data"
  - "OURA_ACCESS_TOKEN configured in sandbox env"
affects: [daily-briefing, proactive-patterns]

tech-stack:
  added: [oura-api-v2, sqlite3]
  patterns: [sandbox-env-injection, workspace-path-convention]

key-files:
  created:
    - /home/ubuntu/.openclaw/skills/oura/SKILL.md
    - /home/ubuntu/clawd/agents/main/health.db
  modified:
    - /home/ubuntu/.openclaw/.env
    - /home/ubuntu/.openclaw/openclaw.json

key-decisions:
  - "API base URL is api.ouraring.com (not cloud.ouraring.com as docs suggest)"
  - "health.db in agent workspace (/workspace/health.db inside sandbox)"
  - "OURA_ACCESS_TOKEN injected via openclaw.json sandbox.docker.env"
  - "Used CURRENT_TIMESTAMP for SQLite default (not datetime('now'))"

patterns-established:
  - "Sandbox env injection: API tokens go in openclaw.json agents.defaults.sandbox.docker.env"
  - "Workspace paths: SKILL.md uses /workspace/ paths, files stored in agent workspace dir"
  - "API smoke-test: verify endpoints with curl before writing SKILL.md"

duration: 45min
completed: 2026-02-08
---

# Phase 2 Plan 1: Oura Ring Integration Summary

**Oura Ring skill with API access to sleep/readiness/activity/HR data, SQLite health snapshots, and sandbox-aware configuration**

## Performance

- **Duration:** ~45 min (including sandbox debugging)
- **Started:** 2026-02-08T05:45:00Z
- **Completed:** 2026-02-08T06:30:00Z
- **Tasks:** 3 (2 auto + 1 human-verify)
- **Files modified:** 4

## Accomplishments
- Oura Ring SKILL.md (241 lines) deployed with full API docs for sleep, readiness, activity, heart rate
- health_snapshots SQLite table created with 14 columns
- Real Oura data pulled and stored: sleep=74, readiness=74, resting_hr=60 (2026-02-07)
- Morning briefing query template included in skill

## Task Commits

1. **Task 1: Add OURA_ACCESS_TOKEN and create health_snapshots table** - `889eb09` (feat)
2. **Task 2: Create Oura Ring SKILL.md** - `649e608` (feat)
3. **Task 3: Human verification** - Approved after end-to-end test via Slack

## Files Created/Modified
- `~/.openclaw/skills/oura/SKILL.md` - Full Oura API skill with 7 sections
- `~/clawd/agents/main/health.db` - SQLite DB with health_snapshots table
- `~/.openclaw/.env` - Added OURA_ACCESS_TOKEN
- `~/.openclaw/openclaw.json` - Added OURA_ACCESS_TOKEN to sandbox docker env

## Decisions Made
- API base URL is `api.ouraring.com` not `cloud.ouraring.com` (docs outdated)
- health.db stored in agent workspace for sandbox accessibility
- Token injected via openclaw.json sandbox env (not just .env)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Wrong API base URL**
- **Found during:** Task 2 verification (API smoke test)
- **Issue:** Plan specified `cloud.ouraring.com/v2/usercollection` — returns 404
- **Fix:** Changed all URLs to `api.ouraring.com/v2/usercollection`
- **Files modified:** SKILL.md
- **Verification:** curl returns 200 with real data

**2. [Rule 3 - Blocking] Sandbox env var missing**
- **Found during:** Task 3 (Bob couldn't access OURA_ACCESS_TOKEN)
- **Issue:** `.env` loaded by gateway only; Docker sandbox has separate env
- **Fix:** Added OURA_ACCESS_TOKEN to `agents.defaults.sandbox.docker.env` in openclaw.json
- **Files modified:** openclaw.json
- **Verification:** Bob confirmed token access after restart

**3. [Rule 3 - Blocking] health.db path inaccessible from sandbox**
- **Found during:** Task 3 (Bob couldn't read health.db)
- **Issue:** DB at `~/clawd/health.db` is outside sandbox workspace mount
- **Fix:** Moved to `~/clawd/agents/main/health.db`, updated SKILL.md paths to `/workspace/health.db`
- **Files modified:** health.db (moved), SKILL.md (paths updated)
- **Verification:** Bob stored real data at `/workspace/health.db`

**4. [Rule 1 - Bug] SQLite default expression**
- **Found during:** Task 1 (table creation)
- **Issue:** `datetime('now')` not valid as column default; used `CURRENT_TIMESTAMP`
- **Files modified:** Table DDL
- **Verification:** Table created successfully

---

**Total deviations:** 4 auto-fixed (2 blocking, 2 bugs)
**Impact on plan:** All fixes necessary for end-to-end functionality. Established sandbox-aware patterns for future skill plans.

## Issues Encountered
- Initial token provided (050567) was not a valid Oura PAT — required user to generate real token from cloud.ouraring.com
- Bob's existing Slack session didn't pick up new skill until gateway restart + different channel

## User Setup Required
None — OURA_ACCESS_TOKEN configured during execution.

## Next Phase Readiness
- Health data accessible for Phase 3 (Daily Briefing) morning briefing consumption
- Pattern established for sandbox env injection (needed by Phase 5 Govee, Phase 10 Coding)
- Phase complete, ready for transition

---
*Phase: 02-oura-ring-integration*
*Completed: 2026-02-08*

---
phase: 28-platform-cleanup
plan: 01
subsystem: infra
tags: [openclaw-doctor, auth-profiles, session-keys, config-migration]

# Dependency graph
requires:
  - phase: 24-critical-security-update
    provides: "v2026.2.17 gateway with modern config format"
provides:
  - "Zero-warning openclaw doctor output on EC2"
  - "Deprecated anthropic:claude-cli auth profile removed"
  - "Legacy session key (bare 'main') removed from sessions.json"
  - "dmPolicy/allowFrom config migration verified complete"
affects: [28-platform-cleanup]

# Tech tracking
tech-stack:
  added: []
  patterns: ["doctor fix-then-verify loop", "manual session key cleanup when doctor --fix insufficient"]

key-files:
  created: []
  modified:
    - "EC2: ~/.openclaw/openclaw.json (removed deprecated auth profile)"
    - "EC2: ~/.openclaw/agents/main/sessions/sessions.json (removed legacy 'main' key)"

key-decisions:
  - "Removed deprecated anthropic:claude-cli profile directly from config instead of running interactive setup-token (profile was redundant -- anthropic:manual and anthropic:clawdbot already present)"
  - "Manually removed legacy bare 'main' session key from sessions.json after doctor --fix failed to canonicalize it"
  - "Accepted tailnet gateway binding security notice as known false positive (SC-GW-001, documented Phase 24-02)"

patterns-established:
  - "doctor --fix only modifies openclaw.json, not session state files -- manual cleanup needed for session key canonicalization"

requirements-completed: [CLN-02, CLN-03, CLN-04]

# Metrics
duration: 7min
completed: 2026-02-20
---

# Phase 28 Plan 01: Doctor Warnings & Config Verification Summary

**Deprecated auth profile removed, legacy session key canonicalized, dmPolicy/allowFrom migration verified -- zero actionable doctor warnings**

## Performance

- **Duration:** 7 min
- **Started:** 2026-02-20T00:07:39Z
- **Completed:** 2026-02-20T00:14:50Z
- **Tasks:** 2
- **Files modified:** 2 (on EC2)

## Accomplishments

- Resolved deprecated `anthropic:claude-cli` auth profile warning by removing the redundant OAuth-mode profile from openclaw.json (two token-mode profiles remain: `anthropic:clawdbot` and `anthropic:manual`)
- Resolved legacy session key warning by removing stale bare `main` key from sessions.json (the canonical `agent:main:main` key was already present with current data)
- Verified dmPolicy/allowFrom config migration is complete (3 modern keys, 0 legacy keys) -- confirms Phase 24-01 migration stuck
- Gateway verified active and running after all changes

## Task Commits

Both tasks were EC2-only operations (no local file changes). All changes documented in this SUMMARY.

1. **Task 1: Fix doctor warnings** - EC2 changes only (openclaw.json + sessions.json)
2. **Task 2: Verify dmPolicy/allowFrom config migration** - Verification only, no changes needed

**Plan metadata:** committed with SUMMARY.md + STATE.md + ROADMAP.md + REQUIREMENTS.md

## Files Created/Modified

- `EC2: ~/.openclaw/openclaw.json` - Removed deprecated `anthropic:claude-cli` auth profile (mode: oauth)
- `EC2: ~/.openclaw/agents/main/sessions/sessions.json` - Removed legacy bare `main` session key (stale, 0 messages, Feb 13 timestamp)
- `EC2: ~/.openclaw/agents/main/sessions/sessions.json.bak` - Backup before session key removal

## Decisions Made

1. **Removed auth profile instead of running setup-token:** The deprecated `anthropic:claude-cli` (mode: oauth) was redundant -- `anthropic:manual` (mode: token) and `anthropic:clawdbot` (mode: token) already exist and are the active profiles. Running the interactive `setup-token` command was unnecessary.

2. **Manual session key removal:** `openclaw doctor --fix` detected the legacy `main` session key but did not modify sessions.json (it only writes to openclaw.json). Tried with gateway running and stopped -- same behavior. Manually removed the stale key with a Python script after creating a backup.

3. **Tailnet security notice accepted:** The "Gateway bound to tailnet" security info in doctor output is the known false positive (SC-GW-001) from Phase 24-02. Not a warning to fix.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Manual session key canonicalization instead of doctor --fix**
- **Found during:** Task 1 (Step 3 -- legacy session keys)
- **Issue:** `openclaw doctor --fix` detected legacy session keys but did not modify sessions.json. The command only modified openclaw.json timestamps. Tested with gateway running and stopped -- same result.
- **Fix:** Identified the single legacy key (bare `main`, 0 messages, stale Feb 13 timestamp) via Python analysis. Created backup, removed the key manually, verified doctor no longer reports the warning.
- **Files modified:** EC2: ~/.openclaw/agents/main/sessions/sessions.json
- **Verification:** `openclaw doctor` output shows no "Legacy state detected" section
- **Impact:** None -- the removed key had 0 messages and a stale timestamp. The canonical `agent:main:main` key was already present.

---

**Total deviations:** 1 auto-fixed (1 blocking -- doctor --fix insufficient for session state)
**Impact on plan:** Minimal. Same outcome achieved through manual cleanup instead of doctor --fix.

## Issues Encountered

- `doctor --fix` applies config-level fixes to openclaw.json but does not modify session state files (sessions.json). This is a pattern to document: session key canonicalization requires manual intervention or gateway-level migration.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Doctor baseline is clean -- ready for Plan 28-02 (OAuth scope trimming + gateway.remote.url documentation)
- Gateway is running and healthy
- All 3 requirements for this plan (CLN-02, CLN-03, CLN-04) resolved/verified

## Self-Check: PASSED

- SUMMARY.md: FOUND at .planning/phases/28-platform-cleanup/28-01-SUMMARY.md
- EC2 doctor: zero actionable warnings (verified via SSH)
- EC2 gateway: active (running)
- No local git commits for individual tasks (EC2-only operations)

---
*Phase: 28-platform-cleanup*
*Completed: 2026-02-20*

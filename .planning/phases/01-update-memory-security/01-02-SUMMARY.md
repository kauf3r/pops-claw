---
phase: 01-update-memory-security
plan: 02
subsystem: infra
tags: [openclaw, memory, sqlite-vec, fts5, security, gateway-token, oauth]

# Dependency graph
requires:
  - phase: 01-01
    provides: OpenClaw v2026.2.6-3 running on EC2
provides:
  - Memory system active (builtin sqlite-vec + FTS5)
  - Security hardening (discovery off, dmScope=main, token rotated)
  - Gmail OAuth scope audit documented
affects: [phase-2, phase-3, phase-4, phase-5]

# Tech tracking
tech-stack:
  added: [sqlite-vec, fts5, text-embedding-3-small]
  patterns: [builtin-memory-backend, openai-embedding-batches, token-rotation]

key-files:
  created: []
  modified:
    - /home/ubuntu/.openclaw/openclaw.json (memory + security + token)
    - progress.md (OAuth scope findings)

key-decisions:
  - "sqlite-hybrid is not a valid config value — builtin backend IS sqlite-hybrid internally (sqlite-vec + FTS5)"
  - "session.dmScope set to 'main' (most restrictive valid option; 'direct' from plan doesn't exist)"
  - "Gmail OAuth has 2 excess scopes (gmail.settings.basic, gmail.settings.sharing) — defer reduction to future re-auth"

patterns-established:
  - "Memory config: builtin backend auto-configures sqlite-vec (1536-dim) + FTS5"
  - "Token rotation: python3 secrets.token_urlsafe(32) + jq update + service restart"

# Metrics
duration: 15min
completed: 2026-02-07
---

# Phase 1 Plan 2: Memory & Security Summary

**Builtin memory backend active (sqlite-vec 1536-dim + FTS5, 12 chunks indexed), security hardened (discovery off, dmScope=main, gateway token rotated), Gmail OAuth scopes audited**

## Performance

- **Duration:** 15 min
- **Started:** 2026-02-07T22:45:00Z
- **Completed:** 2026-02-07T23:00:00Z
- **Tasks:** 3 (2 auto + 1 checkpoint)
- **Files modified:** 2 (on EC2) + 1 (local)

## Accomplishments

- Memory system operational: builtin backend with sqlite-vec (1536-dim, OpenAI text-embedding-3-small) + FTS5 full-text search, 12 chunks indexed
- Security hardening applied: discovery.wideArea.enabled=false, session.dmScope=main
- Gateway auth token rotated (secrets.token_urlsafe(32)) and verified operational
- Gmail OAuth scopes audited: 7 scopes, 2 excess identified for future cleanup
- Human verification passed: Bob responding on Slack with new token

## Task Commits

Each task was committed atomically:

1. **Task 1: Configure memory and security settings** - `a82e1d5` (feat)
2. **Task 2: Rotate gateway token and review OAuth scopes** - `fca9d2e` (feat)
3. **Task 3: Human verification checkpoint** - passed (no commit needed)

**Plan metadata:** (this commit)

## Files Created/Modified

- `/home/ubuntu/.openclaw/openclaw.json` - Memory backend, security settings, rotated token
- `/home/ubuntu/.openclaw/openclaw.json.bak-20260207` - Pre-change backup
- `progress.md` - Gmail OAuth scope findings

## Decisions Made

- **builtin IS sqlite-hybrid**: Plan specified `memory.backend: "sqlite-hybrid"` but that's not a valid schema value. The `builtin` backend already uses sqlite-vec + FTS5 internally — same hybrid search, just different config key.
- **dmScope=main**: Plan specified `"direct"` but that doesn't exist in the schema. Used `"main"` which is the most restrictive valid option.
- **Gmail scope reduction deferred**: 2 excess scopes found (gmail.settings.basic, gmail.settings.sharing). Reduction requires re-auth with `gog auth add --manual` — not worth disrupting working auth now.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Invalid config values from plan**
- **Found during:** Task 1 (memory configuration)
- **Issue:** `memory.backend: "sqlite-hybrid"`, `vectorWeight`, `bm25Weight`, `markdownSource` are not valid openclaw.json keys
- **Fix:** Used `"builtin"` which provides identical sqlite-vec + FTS5 hybrid search
- **Files modified:** /home/ubuntu/.openclaw/openclaw.json
- **Verification:** `openclaw health` shows Vector ready + FTS ready
- **Committed in:** a82e1d5

**2. [Rule 1 - Bug] Invalid dmScope value from plan**
- **Found during:** Task 1 (security settings)
- **Issue:** `session.dmScope: "direct"` not in schema (valid: main, per-peer, per-channel-peer, per-account-channel-peer)
- **Fix:** Used `"main"` (most restrictive)
- **Verification:** Config validated with python3 json.tool
- **Committed in:** a82e1d5

**3. [Rule 3 - Blocking] qmd backend unavailable**
- **Found during:** Task 1 (attempted qmd backend)
- **Issue:** qmd CLI is npm placeholder v0.0.0, not functional
- **Fix:** Reverted to builtin backend
- **Committed in:** a82e1d5

---

**Total deviations:** 3 auto-fixed (2 bug, 1 blocking)
**Impact on plan:** Plan had incorrect config schema values. All deviations resolved to equivalent-or-better settings. No scope creep.

## Issues Encountered

None beyond the deviations above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 1 complete — all requirements addressed
- Memory system active and indexing (12 chunks, embeddings via OpenAI)
- Security posture improved (discovery off, dmScope restricted, token fresh)
- Gmail OAuth working (excess scopes documented for future cleanup)
- Ready for Phases 2, 3, 4 (can run in parallel per roadmap)

## Self-Check: PASSED

- FOUND: 01-02-SUMMARY.md
- FOUND: a82e1d5 (Task 1 commit)
- FOUND: fca9d2e (Task 2 commit)

---
*Phase: 01-update-memory-security*
*Completed: 2026-02-07*
